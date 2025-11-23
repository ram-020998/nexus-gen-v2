"""
Three-Way Merge Service

Orchestrates the entire three-way merge workflow including blueprint
generation, comparison, classification, ordering, and guidance generation.

Refactored to use dependency injection and repository pattern.
"""
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.base_service import BaseService
from repositories.merge_session_repository import MergeSessionRepository
from repositories.change_repository import ChangeRepository
from repositories.package_repository import PackageRepository
from models import db, MergeSession, ChangeReview
from services.merge_assistant.logger import create_merge_session_logger
from services.merge_assistant.blueprint_generation_service import (
    BlueprintGenerationService,
    BlueprintGenerationError
)
from services.merge_assistant.three_way_comparison_service import (
    ThreeWayComparisonService
)
from services.merge_assistant.change_classification_service import (
    ChangeClassificationService
)
from services.merge_assistant.dependency_analysis_service import (
    DependencyAnalysisService
)
from services.merge_assistant.merge_guidance_service import (
    MergeGuidanceService
)
from services.merge.package_service import PackageService
from services.merge.change_service import ChangeService

# Import extracted helper classes
from services.merge.change_data_builder import ChangeDataBuilder
from services.merge.merge_statistics_calculator import MergeStatisticsCalculator
from services.merge.merge_session_utilities import MergeSessionUtilities


class ThreeWayMergeService(BaseService):
    """
    Orchestrates the three-way merge process

    Coordinates blueprint generation, comparison, classification,
    ordering, and guidance generation for merge sessions.
    """

    def _initialize_dependencies(self):
        """Initialize service and repository dependencies"""
        # Initialize repositories
        self.merge_session_repo = self._get_repository(MergeSessionRepository)
        self.change_repo = self._get_repository(ChangeRepository)
        self.package_repo = self._get_repository(PackageRepository)
        
        # Initialize services
        self.blueprint_service = BlueprintGenerationService()
        self.comparison_service = ThreeWayComparisonService()
        self.classification_service = ChangeClassificationService()
        self.dependency_service = DependencyAnalysisService()
        self.guidance_service = MergeGuidanceService()
        self.package_service = self._get_service(PackageService)
        self.change_service = self._get_service(ChangeService)
        
        # Initialize helper classes
        self.data_builder = ChangeDataBuilder()
        self.statistics_calculator = MergeStatisticsCalculator()
        self.utilities = MergeSessionUtilities()

    def create_session(
        self,
        base_zip_path: str,
        customized_zip_path: str,
        new_vendor_zip_path: str
    ) -> MergeSession:
        """
        Create a new merge session and initiate analysis

        Steps:
        1. Create session record
        2. Generate blueprints for A, B, C
        3. Perform comparisons (A→B, A→C)
        4. Classify changes
        5. Order changes intelligently
        6. Generate merge guidance
        7. Update session status to 'ready'

        Args:
            base_zip_path: Path to base package (A)
            customized_zip_path: Path to customized package (B)
            new_vendor_zip_path: Path to new vendor package (C)

        Returns:
            MergeSession object

        Raises:
            BlueprintGenerationError: If blueprint generation fails
            Exception: For other errors during processing
        """
        start_time = time.time()

        # Step 1: Create session record using repository
        session = self.merge_session_repo.create(
            reference_id=self.utilities.generate_reference_id(),
            base_package_name=self.utilities.extract_package_name(base_zip_path),
            customized_package_name=self.utilities.extract_package_name(customized_zip_path),
            new_vendor_package_name=self.utilities.extract_package_name(new_vendor_zip_path),
            status='processing'
        )
        
        # Initialize logger for this session
        logger = create_merge_session_logger(session.reference_id)
        logger.log_upload(
            session.base_package_name,
            session.customized_package_name,
            session.new_vendor_package_name
        )

        try:
            # Step 2: Generate blueprints for A, B, C
            logger.log_stage('Blueprint Generation', {'packages': 3})
            blueprint_start = time.time()
            
            base_result, customized_result, new_vendor_result = (
                self.blueprint_service.generate_all_blueprints(
                    base_zip_path,
                    customized_zip_path,
                    new_vendor_zip_path,
                    logger=logger
                )
            )
            
            blueprint_time = time.time() - blueprint_start
            logger.info(
                f"All blueprints generated in {blueprint_time:.2f}s"
            )

            # Normalize blueprints into Package and AppianObject tables
            logger.log_stage('Blueprint Normalization', {'packages': 3})
            normalization_start = time.time()
            
            self.package_service.create_package_with_all_data(
                session.id,
                'base',
                base_result
            )
            
            self.package_service.create_package_with_all_data(
                session.id,
                'customized',
                customized_result
            )
            
            self.package_service.create_package_with_all_data(
                session.id,
                'new_vendor',
                new_vendor_result
            )
            
            normalization_time = time.time() - normalization_start
            logger.info(
                f"Blueprint normalization completed in "
                f"{normalization_time:.2f}s"
            )

            # Step 3: Perform comparisons (A→B, A→C)
            comparison_start = time.time()
            
            vendor_changes, customer_changes = (
                self.comparison_service.perform_three_way_comparison(
                    base_result,
                    customized_result,
                    new_vendor_result,
                    logger=logger
                )
            )
            
            comparison_time = time.time() - comparison_start
            logger.info(
                f"Three-way comparison completed in {comparison_time:.2f}s"
            )

            # Step 4: Classify changes
            logger.log_classification_start()
            classification_start = time.time()
            
            classification_results = (
                self.classification_service.classify_changes(
                    vendor_changes,
                    customer_changes,
                    logger=logger
                )
            )
            
            classification_time = time.time() - classification_start
            logger.log_classification_complete(
                len(classification_results.get('NO_CONFLICT', [])),
                len(classification_results.get('CONFLICT', [])),
                len(classification_results.get('CUSTOMER_ONLY', [])),
                len(classification_results.get('REMOVED_BUT_CUSTOMIZED', []))
            )
            logger.info(
                f"Classification completed in {classification_time:.2f}s"
            )

            # Step 5: Order changes intelligently
            logger.log_ordering_start()
            ordering_start = time.time()
            
            # Build dependency graph from new vendor blueprint
            # (most complete version)
            dependency_graph = (
                self.dependency_service.build_dependency_graph(
                    new_vendor_result,
                    logger=logger
                )
            )

            ordered_changes = self.dependency_service.order_changes(
                classification_results,
                dependency_graph,
                logger=logger
            )
            
            ordering_time = time.time() - ordering_start
            logger.log_ordering_complete(len(ordered_changes))
            logger.info(
                f"Change ordering completed in {ordering_time:.2f}s"
            )

            # Step 6: Generate merge guidance for each change
            logger.log_guidance_generation_start()
            guidance_start = time.time()
            
            # Get object lookups for guidance generation
            base_lookup = base_result['object_lookup']
            customized_lookup = customized_result['object_lookup']
            new_vendor_lookup = new_vendor_result['object_lookup']

            for change in ordered_changes:
                uuid = change['uuid']

                # Get objects from each version
                base_obj = base_lookup.get(uuid)
                customer_obj = customized_lookup.get(uuid)
                vendor_obj = new_vendor_lookup.get(uuid)

                # Add three-way objects to change for template display
                change['base_object'] = base_obj
                change['customer_object'] = customer_obj
                change['vendor_object'] = vendor_obj

                # Generate guidance
                guidance = self.guidance_service.generate_guidance(
                    change,
                    base_obj,
                    customer_obj,
                    vendor_obj
                )

                # Add guidance to change object
                change['merge_guidance'] = guidance

                # Add dependency information
                # Note: Pass ordered_changes and object_lookup after the loop
                # to get enriched dependency information with names and review status
                change['dependencies'] = {
                    'parents': [],
                    'children': []
                }
            
            guidance_time = time.time() - guidance_start
            logger.log_guidance_generation_complete(len(ordered_changes))
            logger.info(
                f"Guidance generation completed in {guidance_time:.2f}s"
            )

            # Step 7: Enrich dependencies with names and review status
            # Use the most complete object lookup (prefer vendor, then customer, then base)
            combined_lookup = {}
            combined_lookup.update(base_lookup)
            combined_lookup.update(customized_lookup)
            combined_lookup.update(new_vendor_lookup)

            for change in ordered_changes:
                uuid = change['uuid']
                deps = self.dependency_service.get_dependencies(
                    uuid,
                    dependency_graph,
                    ordered_changes,
                    combined_lookup
                )
                change['dependencies'] = deps

            # Normalize changes into Change and ChangeReview tables
            logger.log_stage('Change Normalization', {'changes': len(ordered_changes)})
            change_normalization_start = time.time()
            
            created_changes = self.change_service.create_changes_from_comparison(
                session.id,
                classification_results,
                ordered_changes
            )
            
            change_normalization_time = time.time() - change_normalization_start
            logger.info(
                f"Change normalization completed in {change_normalization_time:.2f}s"
            )
            
            # Update session with total changes count
            session.total_changes = len(created_changes)
            db.session.commit()

            # Step 8: Update session status to 'ready'
            session.status = 'ready'
            total_time = int(time.time() - start_time)
            session.total_time = total_time
            db.session.commit()
            
            logger.log_session_ready(total_time)

            return session

        except BlueprintGenerationError as e:
            # Blueprint generation failed
            logger.log_error(
                'blueprint_generation',
                str(e),
                {'session_id': session.reference_id}
            )
            session.status = 'error'
            session.error_log = json.dumps({
                'phase': 'blueprint_generation',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            db.session.commit()
            raise

        except Exception as e:
            # Other errors
            logger.log_error(
                'processing',
                str(e),
                {'session_id': session.reference_id}
            )
            session.status = 'error'
            session.error_log = json.dumps({
                'phase': 'processing',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            db.session.commit()
            raise

    def get_session(self, session_id: int) -> Optional[MergeSession]:
        """
        Retrieve session by ID

        Args:
            session_id: Session ID

        Returns:
            MergeSession object or None if not found
        """
        return self.merge_session_repo.get_by_id(session_id)

    def get_session_by_reference_id(
        self,
        reference_id: str
    ) -> Optional[MergeSession]:
        """
        Retrieve session by reference ID

        Args:
            reference_id: Reference ID (e.g., MRG_001)

        Returns:
            MergeSession object or None if not found
        """
        return self.merge_session_repo.get_by_reference_id(reference_id)

    def get_summary(self, session_id: int) -> Dict[str, Any]:
        """
        Get merge summary with statistics using optimized SQL aggregates

        Uses a single GROUP BY query instead of multiple COUNT queries
        for better performance.

        Args:
            session_id: Session ID

        Returns:
            Dictionary with summary information
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        return self.statistics_calculator.calculate_summary(session_id, session)

    def get_ordered_changes(
        self,
        session_id: int,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get smart-ordered list of changes using SQL JOIN with optional pagination

        Args:
            session_id: Session ID
            page: Page number (1-indexed) for pagination, None for all results
            page_size: Number of results per page, None for all results

        Returns:
            List of change objects in smart order with enriched data
        """
        from sqlalchemy.orm import joinedload
        from models import Change, AppianObject, ProcessModelMetadata

        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Query changes with eager loading of related objects
        query = db.session.query(Change)\
            .options(
                joinedload(Change.base_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.nodes),
                joinedload(Change.base_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.flows),
                joinedload(Change.customer_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.nodes),
                joinedload(Change.customer_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.flows),
                joinedload(Change.vendor_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.nodes),
                joinedload(Change.vendor_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.flows),
                joinedload(Change.merge_guidance),
                joinedload(Change.review)
            )\
            .filter(Change.session_id == session_id)\
            .order_by(Change.display_order)

        # Apply pagination if requested
        if page is not None and page_size is not None:
            offset = (page - 1) * page_size
            query = query.limit(page_size).offset(offset)

        changes = query.all()

        # Convert to dictionaries with enriched data
        result = []
        for change in changes:
            change_dict = self.data_builder.build_change_dict(change)
            result.append(change_dict)

        return result

    def update_progress(
        self,
        session_id: int,
        change_index: int,
        review_status: str,
        notes: Optional[str] = None
    ) -> None:
        """
        Update user progress on a specific change using normalized tables

        Args:
            session_id: Session ID
            change_index: Index of the change in ordered list
            review_status: 'reviewed' or 'skipped'
            notes: Optional user notes

        Raises:
            ValueError: If session not found or invalid parameters
        """
        from models import Change

        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Initialize logger
        logger = create_merge_session_logger(session.reference_id)

        # Get the change by display_order
        change = Change.query.filter_by(
            session_id=session_id,
            display_order=change_index
        ).first()

        if not change:
            raise ValueError(
                f"Change not found at index {change_index} "
                f"for session {session_id}"
            )

        # Find or create ChangeReview record
        review = ChangeReview.query.filter_by(
            session_id=session_id,
            change_id=change.id
        ).first()

        if not review:
            # Create new review record
            review = ChangeReview(
                session_id=session_id,
                change_id=change.id,
                review_status=review_status,
                user_notes=notes,
                reviewed_at=datetime.utcnow()
            )
            db.session.add(review)
        else:
            # Update existing review
            review.review_status = review_status
            review.user_notes = notes
            review.reviewed_at = datetime.utcnow()

        # Update session progress
        session.current_change_index = change_index

        # Commit the review first so it's included in the count
        db.session.commit()

        # Update counts using SQL queries
        session.reviewed_count = ChangeReview.query.filter_by(
            session_id=session_id,
            review_status='reviewed'
        ).count()
        session.skipped_count = ChangeReview.query.filter_by(
            session_id=session_id,
            review_status='skipped'
        ).count()

        # Log user action
        logger.log_user_action(
            review_status,
            change_index,
            change.object_name,
            change.object_type,
            change.classification
        )

        # Check if workflow is complete (all changes reviewed or skipped)
        total_reviewed = session.reviewed_count + session.skipped_count
        if total_reviewed >= session.total_changes:
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
            logger.log_workflow_complete(
                session.reviewed_count,
                session.skipped_count
            )

        db.session.commit()

    def generate_report(self, session_id: int) -> Dict[str, Any]:
        """
        Generate final merge report using JOIN queries

        Args:
            session_id: Session ID

        Returns:
            Dictionary with complete merge report
        """
        from sqlalchemy.orm import joinedload
        from models import Change, AppianObject, ProcessModelMetadata

        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Initialize logger
        logger = create_merge_session_logger(session.reference_id)
        logger.log_report_generation()

        # Get summary
        summary = self.get_summary(session_id)

        # Get all changes with complete data using JOIN
        changes = db.session.query(Change)\
            .options(
                joinedload(Change.base_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.nodes),
                joinedload(Change.base_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.flows),
                joinedload(Change.customer_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.nodes),
                joinedload(Change.customer_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.flows),
                joinedload(Change.vendor_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.nodes),
                joinedload(Change.vendor_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.flows),
                joinedload(Change.merge_guidance),
                joinedload(Change.review)
            )\
            .filter(Change.session_id == session_id)\
            .order_by(Change.display_order)\
            .all()

        # Convert to dictionaries with complete information
        changes_with_reviews = []
        changes_by_category = {
            'NO_CONFLICT': [],
            'CONFLICT': [],
            'CUSTOMER_ONLY': [],
            'REMOVED_BUT_CUSTOMIZED': []
        }

        for change in changes:
            change_dict = self.data_builder.build_change_dict(change)
            changes_with_reviews.append(change_dict)

            # Group by category
            classification = change.classification
            if classification in changes_by_category:
                changes_by_category[classification].append(change_dict)

        # Calculate final statistics
        report_statistics = self.statistics_calculator.calculate_report_statistics(
            session,
            changes_by_category
        )

        return {
            'summary': summary,
            'changes': changes_with_reviews,
            'changes_by_category': changes_by_category,
            'statistics': report_statistics,
            'session': {
                'reference_id': session.reference_id,
                'base_package_name': session.base_package_name,
                'customized_package_name': session.customized_package_name,
                'new_vendor_package_name': session.new_vendor_package_name,
                'status': session.status,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat()
            }
        }

    def filter_changes(
        self,
        session_id: int,
        classification: Optional[str] = None,
        object_type: Optional[str] = None,
        review_status: Optional[str] = None,
        search_term: Optional[str] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        use_cache: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Filter changes using SQL WHERE clauses with optimized indexed queries

        Args:
            session_id: Session ID
            classification: Filter by classification
            object_type: Filter by object type
            review_status: Filter by review status
            search_term: Search by object name
            page: Page number (1-indexed) for pagination
            page_size: Number of results per page
            use_cache: Whether to use query result caching

        Returns:
            Filtered list of changes
        """
        from sqlalchemy.orm import joinedload
        from models import Change, AppianObject, ProcessModelMetadata

        # Get session for logger
        session = self.get_session(session_id)
        if session:
            logger = create_merge_session_logger(session.reference_id)
        
        # Build query with filters
        query = db.session.query(Change)\
            .options(
                joinedload(Change.base_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.nodes),
                joinedload(Change.base_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.flows),
                joinedload(Change.customer_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.nodes),
                joinedload(Change.customer_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.flows),
                joinedload(Change.vendor_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.nodes),
                joinedload(Change.vendor_object).joinedload(AppianObject.process_model_metadata).joinedload(ProcessModelMetadata.flows),
                joinedload(Change.merge_guidance),
                joinedload(Change.review)
            )\
            .filter(Change.session_id == session_id)

        # Apply filters
        if classification:
            query = query.filter(Change.classification == classification)

        if object_type:
            query = query.filter(Change.object_type == object_type)

        if review_status:
            query = query.outerjoin(Change.review)
            if review_status == 'pending':
                query = query.filter(
                    (ChangeReview.review_status == None) |
                    (ChangeReview.review_status == 'pending')
                )
            else:
                query = query.filter(ChangeReview.review_status == review_status)

        if search_term:
            query = query.filter(
                Change.object_name.ilike(f'%{search_term}%')
            )

        # Order by display_order
        query = query.order_by(Change.display_order)

        # Apply pagination if requested
        if page is not None and page_size is not None:
            offset = (page - 1) * page_size
            query = query.limit(page_size).offset(offset)

        # Execute query
        if use_cache:
            from sqlalchemy.orm import lazyload
            query = query.options(lazyload('*'))
        
        changes = query.all()

        # Convert to dictionaries with enriched data
        result = []
        for change in changes:
            change_dict = self.data_builder.build_change_dict(change)
            result.append(change_dict)

        # Log filter application
        if session:
            logger.log_filter_applied(
                classification=classification,
                object_type=object_type,
                review_status=review_status,
                search_term=search_term,
                result_count=len(result)
            )

        return result


# Backward compatibility: Expose extracted classes
__all__ = [
    'ThreeWayMergeService',
    'ChangeDataBuilder',
    'MergeStatisticsCalculator',
    'MergeSessionUtilities'
]
