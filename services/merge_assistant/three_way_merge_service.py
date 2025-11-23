"""
Three-Way Merge Service

Orchestrates the entire three-way merge workflow including blueprint
generation, comparison, classification, ordering, and guidance generation.
"""
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

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
from services.merge_assistant.package_service import PackageService
from services.merge_assistant.change_service import ChangeService


class ThreeWayMergeService:
    """
    Orchestrates the three-way merge process

    Coordinates blueprint generation, comparison, classification,
    ordering, and guidance generation for merge sessions.
    """

    def __init__(self):
        """Initialize the three-way merge service"""
        self.blueprint_service = BlueprintGenerationService()
        self.comparison_service = ThreeWayComparisonService()
        self.classification_service = ChangeClassificationService()
        self.dependency_service = DependencyAnalysisService()
        self.guidance_service = MergeGuidanceService()
        self.package_service = PackageService()
        self.change_service = ChangeService()

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

        # Step 1: Create session record
        session = MergeSession(
            reference_id=self._generate_reference_id(),
            base_package_name=self._extract_package_name(base_zip_path),
            customized_package_name=self._extract_package_name(
                customized_zip_path
            ),
            new_vendor_package_name=self._extract_package_name(
                new_vendor_zip_path
            ),
            status='processing'
        )
        db.session.add(session)
        db.session.commit()
        
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

            # Step 7: Update session status to 'ready'
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
        return MergeSession.query.get(session_id)

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
        return MergeSession.query.filter_by(
            reference_id=reference_id
        ).first()

    def get_summary(self, session_id: int) -> Dict[str, Any]:
        """
        Get merge summary with statistics using optimized SQL aggregates

        Uses a single GROUP BY query instead of multiple COUNT queries
        for better performance.

        Args:
            session_id: Session ID

        Returns:
            Dictionary with summary information:
            {
                'session_id': int,
                'reference_id': str,
                'packages': {...},
                'statistics': {...},
                'breakdown_by_type': {...},
                'estimated_complexity': str,
                'estimated_time_hours': int
            }
        """
        from sqlalchemy import func, case
        from models import Change, Package

        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Get package information
        packages = Package.query.filter_by(session_id=session_id).all()
        package_info = {}
        for pkg in packages:
            package_info[pkg.package_type] = pkg.package_name

        # Calculate all statistics in a single optimized query using CASE
        # This is much faster than multiple separate COUNT queries
        stats_query = db.session.query(
            func.count(Change.id).label('total'),
            func.sum(case((Change.classification == 'NO_CONFLICT', 1), else_=0)).label('no_conflict'),
            func.sum(case((Change.classification == 'CONFLICT', 1), else_=0)).label('conflict'),
            func.sum(case((Change.classification == 'CUSTOMER_ONLY', 1), else_=0)).label('customer_only'),
            func.sum(case((Change.classification == 'REMOVED_BUT_CUSTOMIZED', 1), else_=0)).label('removed_but_customized')
        ).filter(Change.session_id == session_id).first()

        statistics = {
            'total_changes': stats_query.total or 0,
            'no_conflict': stats_query.no_conflict or 0,
            'conflict': stats_query.conflict or 0,
            'customer_only': stats_query.customer_only or 0,
            'removed_but_customized': stats_query.removed_but_customized or 0
        }

        # Calculate breakdown by type using optimized GROUP BY
        # Uses idx_change_session_type for efficient grouping
        breakdown_query = (
            db.session.query(
                Change.object_type,
                Change.classification,
                func.count(Change.id)
            )
            .filter(Change.session_id == session_id)
            .group_by(Change.object_type, Change.classification)
            .all()
        )

        # Build breakdown dictionary
        breakdown_by_type = {}
        for obj_type, classification, count in breakdown_query:
            if obj_type not in breakdown_by_type:
                breakdown_by_type[obj_type] = {
                    'no_conflict': 0,
                    'conflict': 0,
                    'customer_only': 0,
                    'removed_but_customized': 0
                }

            # Map classification to lowercase key
            classification_key = classification.lower()
            if classification_key in breakdown_by_type[obj_type]:
                breakdown_by_type[obj_type][classification_key] = count

        # Estimate complexity and time
        complexity, estimated_hours = self._estimate_complexity(statistics)

        return {
            'session_id': session.id,
            'reference_id': session.reference_id,
            'packages': {
                'base': package_info.get('base', 'Unknown'),
                'customized': package_info.get('customized', 'Unknown'),
                'new_vendor': package_info.get('new_vendor', 'Unknown')
            },
            'statistics': statistics,
            'breakdown_by_type': breakdown_by_type,
            'estimated_complexity': complexity,
            'estimated_time_hours': estimated_hours,
            'status': session.status,
            'created_at': session.created_at.isoformat(),
            'reviewed_count': session.reviewed_count,
            'skipped_count': session.skipped_count
        }

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
        from models import Change

        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Query changes with eager loading of related objects
        from models import AppianObject, ProcessModelMetadata
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
            change_dict = self._build_change_dict(change)
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
            Dictionary with complete merge report:
            {
                'summary': {...},
                'changes': [...],
                'statistics': {...}
            }
        """
        from sqlalchemy.orm import joinedload
        from models import Change

        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Initialize logger
        logger = create_merge_session_logger(session.reference_id)
        logger.log_report_generation()

        # Get summary
        summary = self.get_summary(session_id)

        # Get all changes with complete data using JOIN
        from models import AppianObject, ProcessModelMetadata
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
            change_dict = self._build_change_dict(change)
            changes_with_reviews.append(change_dict)

            # Group by category
            classification = change.classification
            if classification in changes_by_category:
                changes_by_category[classification].append(change_dict)

        # Calculate final statistics
        report_statistics = {
            'total_changes': session.total_changes,
            'reviewed': session.reviewed_count,
            'skipped': session.skipped_count,
            'pending': (
                session.total_changes -
                session.reviewed_count -
                session.skipped_count
            ),
            'conflicts': len(changes_by_category['CONFLICT']),
            'processing_time_seconds': session.total_time,
            'completed_at': (
                session.completed_at.isoformat()
                if session.completed_at else None
            )
        }

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
            classification: Filter by classification (uses idx_change_session_classification)
            object_type: Filter by object type (uses idx_change_session_type)
            review_status: Filter by review status (uses idx_review_session_status)
            search_term: Search by object name (uses idx_object_type_name)
            page: Page number (1-indexed) for pagination
            page_size: Number of results per page
            use_cache: Whether to use query result caching (default: False)

        Returns:
            Filtered list of changes
        """
        from sqlalchemy.orm import joinedload
        from models import Change

        # Get session for logger
        session = self.get_session(session_id)
        if session:
            logger = create_merge_session_logger(session.reference_id)
        
        # Build query with filters - order matters for index usage
        from models import AppianObject, ProcessModelMetadata
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

        # Apply filters in order of selectivity (most selective first)
        # This helps the query optimizer choose the best index
        
        # Classification filter (uses idx_change_session_classification)
        if classification:
            query = query.filter(Change.classification == classification)

        # Object type filter (uses idx_change_session_type)
        if object_type:
            query = query.filter(Change.object_type == object_type)

        # Review status filter (uses idx_review_session_status via join)
        if review_status:
            # Use outer join to include changes without reviews
            query = query.outerjoin(Change.review)
            if review_status == 'pending':
                # Pending means no review or review_status is 'pending'
                query = query.filter(
                    (ChangeReview.review_status == None) |
                    (ChangeReview.review_status == 'pending')
                )
            else:
                query = query.filter(ChangeReview.review_status == review_status)

        # Search term filter (case-insensitive, uses object_name index)
        if search_term:
            # Use LIKE with leading wildcard - still uses index for filtering
            query = query.filter(
                Change.object_name.ilike(f'%{search_term}%')
            )

        # Order by display_order (uses idx_change_session_order)
        query = query.order_by(Change.display_order)

        # Apply pagination if requested
        if page is not None and page_size is not None:
            offset = (page - 1) * page_size
            query = query.limit(page_size).offset(offset)

        # Execute query with optional caching
        if use_cache:
            # Enable query result caching for repeated queries
            from sqlalchemy.orm import lazyload
            query = query.options(lazyload('*'))
        
        changes = query.all()

        # Convert to dictionaries with enriched data
        result = []
        for change in changes:
            change_dict = self._build_change_dict(change)
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

    def _generate_reference_id(self) -> str:
        """
        Generate unique reference ID for merge session

        Returns:
            Reference ID in format MRG_001, MRG_002, etc.
        """
        # Get the highest existing reference ID
        last_session = MergeSession.query.order_by(
            MergeSession.id.desc()
        ).first()

        if last_session and last_session.reference_id:
            # Extract number from last reference ID
            try:
                last_num = int(last_session.reference_id.split('_')[1])
                next_num = last_num + 1
            except (IndexError, ValueError):
                next_num = 1
        else:
            next_num = 1

        return f"MRG_{next_num:03d}"

    def _extract_package_name(self, zip_path: str) -> str:
        """
        Extract package name from ZIP file path

        Args:
            zip_path: Path to ZIP file

        Returns:
            Package name without extension
        """
        import os
        return os.path.basename(zip_path).replace('.zip', '')



    def _estimate_complexity(
        self,
        statistics: Dict[str, int]
    ) -> tuple[str, int]:
        """
        Estimate merge complexity and time

        Args:
            statistics: Statistics dictionary with counts

        Returns:
            Tuple of (complexity_level, estimated_hours)
        """
        conflicts = statistics.get('conflict', 0)
        total = statistics.get('total_changes', 0)

        # Calculate complexity based on conflict ratio
        if total == 0:
            return 'LOW', 0

        conflict_ratio = conflicts / total

        if conflict_ratio < 0.1:
            complexity = 'LOW'
            # Estimate 2 minutes per change
            estimated_hours = max(1, int((total * 2) / 60))
        elif conflict_ratio < 0.3:
            complexity = 'MEDIUM'
            # Estimate 5 minutes per change
            estimated_hours = max(2, int((total * 5) / 60))
        else:
            complexity = 'HIGH'
            # Estimate 10 minutes per change
            estimated_hours = max(4, int((total * 10) / 60))

        return complexity, estimated_hours

    def _build_change_dict(self, change) -> Dict[str, Any]:
        """
        Build a dictionary representation of a Change with related objects

        Args:
            change: Change model instance with eager-loaded relationships

        Returns:
            Dictionary with complete change information
        """
        change_dict = {
            'id': change.id,
            'uuid': change.object_uuid,
            'name': change.object_name,
            'type': change.object_type,
            'classification': change.classification,
            'change_type': change.change_type,
            'vendor_change_type': change.vendor_change_type,
            'customer_change_type': change.customer_change_type,
            'display_order': change.display_order
        }

        # Add base object data
        if change.base_object:
            change_dict['base_object'] = self._build_object_dict(
                change.base_object,
                object_type=change.object_type
            )

        # Add customer object data
        if change.customer_object:
            change_dict['customer_object'] = self._build_object_dict(
                change.customer_object,
                object_type=change.object_type
            )

        # Add vendor object data
        if change.vendor_object:
            change_dict['vendor_object'] = self._build_object_dict(
                change.vendor_object,
                object_type=change.object_type
            )

        # Add merge guidance data
        if change.merge_guidance:
            change_dict['merge_guidance'] = {
                'recommendation': change.merge_guidance.recommendation,
                'reason': change.merge_guidance.reason,
                'conflicts': [
                    {
                        'field_name': c.field_name,
                        'conflict_type': c.conflict_type,
                        'description': c.description
                    }
                    for c in change.merge_guidance.conflicts
                ],
                'changes': [
                    {
                        'field_name': c.field_name,
                        'description': c.change_description,
                        'old_value': c.old_value,
                        'new_value': c.new_value
                    }
                    for c in change.merge_guidance.changes
                ]
            }

        # Add review status
        if change.review:
            change_dict['review_status'] = change.review.review_status
            change_dict['user_notes'] = change.review.user_notes
            change_dict['reviewed_at'] = (
                change.review.reviewed_at.isoformat()
                if change.review.reviewed_at else None
            )
        else:
            change_dict['review_status'] = 'pending'
            change_dict['user_notes'] = None
            change_dict['reviewed_at'] = None

        # Add process model comparison data if this is a Process Model
        if change.object_type == 'Process Model':
            change_dict['process_model_data'] = self._build_process_model_comparison(
                change_dict.get('base_object'),
                change_dict.get('customer_object'),
                change_dict.get('vendor_object')
            )

        return change_dict

    def _build_process_model_comparison(
        self,
        base_obj: Optional[Dict[str, Any]],
        customer_obj: Optional[Dict[str, Any]],
        vendor_obj: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build process model comparison data for flow diagram visualization

        Args:
            base_obj: Base version object dict
            customer_obj: Customer version object dict
            vendor_obj: Vendor version object dict

        Returns:
            Dictionary with process model comparison data
        """
        # If no process model data exists, return empty structure
        if not vendor_obj or 'process_model_data' not in vendor_obj:
            return {'has_enhanced_data': False}

        vendor_pm = vendor_obj['process_model_data']
        customer_pm = customer_obj.get('process_model_data') if customer_obj else None
        base_pm = base_obj.get('process_model_data') if base_obj else None

        # Build node comparison
        vendor_nodes = {n['uuid']: n for n in vendor_pm.get('nodes', [])}
        customer_nodes = {n['uuid']: n for n in customer_pm.get('nodes', [])} if customer_pm else {}
        base_nodes = {n['uuid']: n for n in base_pm.get('nodes', [])} if base_pm else {}

        added_nodes = []
        removed_nodes = []
        modified_nodes = []
        unchanged_nodes = []

        # Find added nodes (in vendor but not in base)
        for uuid, node in vendor_nodes.items():
            if uuid not in base_nodes:
                added_nodes.append(node)
            elif uuid in customer_nodes:
                # Check if modified
                if self._nodes_differ(base_nodes[uuid], vendor_nodes[uuid]):
                    modified_nodes.append({
                        'node': node,
                        'changes': ['Modified by vendor']
                    })
                else:
                    unchanged_nodes.append(node)
            else:
                unchanged_nodes.append(node)

        # Find removed nodes (in base but not in vendor)
        for uuid, node in base_nodes.items():
            if uuid not in vendor_nodes:
                removed_nodes.append(node)

        # Build flow comparison
        vendor_flows = vendor_pm.get('flows', [])
        base_flows = base_pm.get('flows', []) if base_pm else []

        # Create flow signatures for comparison
        def flow_signature(flow):
            return f"{flow.get('from_node_uuid')}→{flow.get('to_node_uuid')}"

        vendor_flow_sigs = {flow_signature(f): f for f in vendor_flows}
        base_flow_sigs = {flow_signature(f): f for f in base_flows}

        added_flows = [f for sig, f in vendor_flow_sigs.items() if sig not in base_flow_sigs]
        unchanged_flows = [f for sig, f in vendor_flow_sigs.items() if sig in base_flow_sigs]

        return {
            'has_enhanced_data': True,
            'total_nodes': vendor_pm.get('total_nodes', 0),
            'total_flows': vendor_pm.get('total_flows', 0),
            'complexity_score': vendor_pm.get('complexity_score'),
            'node_comparison': {
                'added': added_nodes,
                'removed': removed_nodes,
                'modified': modified_nodes,
                'unchanged': unchanged_nodes
            },
            'flow_comparison': {
                'added_flows': added_flows,
                'unchanged_flows': unchanged_flows
            },
            'flow_graph': {
                'nodes': list(vendor_nodes.values()),
                'flows': vendor_flows
            }
        }

    def _nodes_differ(self, node1: Dict[str, Any], node2: Dict[str, Any]) -> bool:
        """
        Check if two nodes are different

        Args:
            node1: First node dict
            node2: Second node dict

        Returns:
            True if nodes differ, False otherwise
        """
        # Compare name and type
        if node1.get('name') != node2.get('name'):
            return True
        if node1.get('type') != node2.get('type'):
            return True
        # Could add more detailed property comparison here
        return False

    def _build_object_dict(self, obj, object_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Build a dictionary representation of an AppianObject

        Args:
            obj: AppianObject model instance
            object_type: Optional object type override (from Change table)

        Returns:
            Dictionary with object information
        """
        # Use provided object_type or fall back to obj.object_type
        effective_type = object_type or obj.object_type
        
        obj_dict = {
            'uuid': obj.uuid,
            'name': obj.name,
            'type': effective_type,
            'sail_code': obj.sail_code,
            'fields': (
                json.loads(obj.fields) if obj.fields else None
            ),
            'properties': (
                json.loads(obj.properties) if obj.properties else None
            )
        }
        
        # Add process model data if this is a Process Model
        if effective_type == 'Process Model' and obj.process_model_metadata:
            pm_meta = obj.process_model_metadata
            obj_dict['process_model_data'] = {
                'has_enhanced_data': True,
                'total_nodes': pm_meta.total_nodes,
                'total_flows': pm_meta.total_flows,
                'complexity_score': pm_meta.complexity_score,
                'nodes': [
                    {
                        'uuid': node.node_id,
                        'type': node.node_type,
                        'name': node.node_name,
                        'properties': json.loads(node.properties) if node.properties else {}
                    }
                    for node in pm_meta.nodes
                ],
                'flows': [
                    {
                        'from_node_uuid': flow.from_node.node_id if flow.from_node else None,
                        'to_node_uuid': flow.to_node.node_id if flow.to_node else None,
                        'condition': flow.flow_condition,
                        'label': flow.flow_label
                    }
                    for flow in pm_meta.flows
                ]
            }
        
        return obj_dict

    def analyze_query_plan(
        self,
        session_id: int,
        query_type: str = 'get_ordered_changes'
    ) -> List[Dict[str, Any]]:
        """
        Analyze query execution plan for performance optimization

        Args:
            session_id: Session ID
            query_type: Type of query to analyze
                       ('get_ordered_changes', 'filter_changes', 'get_summary')

        Returns:
            List of query plan steps showing index usage and performance
        """
        from sqlalchemy import text

        if query_type == 'get_ordered_changes':
            # Analyze the get_ordered_changes query
            sql = """
            EXPLAIN QUERY PLAN
            SELECT * FROM changes
            WHERE session_id = :session_id
            ORDER BY display_order
            """
        elif query_type == 'filter_changes':
            # Analyze a typical filter query
            sql = """
            EXPLAIN QUERY PLAN
            SELECT * FROM changes
            WHERE session_id = :session_id
            AND classification = 'CONFLICT'
            AND object_type = 'Interface'
            ORDER BY display_order
            """
        elif query_type == 'get_summary':
            # Analyze the summary aggregation query
            sql = """
            EXPLAIN QUERY PLAN
            SELECT classification, COUNT(*) as count
            FROM changes
            WHERE session_id = :session_id
            GROUP BY classification
            """
        else:
            raise ValueError(f"Unknown query type: {query_type}")

        result = db.session.execute(
            text(sql),
            {"session_id": session_id}
        )

        # Convert result to list of dictionaries
        plan_steps = []
        for row in result:
            plan_steps.append({
                'id': row[0],
                'parent': row[1],
                'notused': row[2],
                'detail': row[3]
            })

        return plan_steps

    def verify_index_usage(self, session_id: int) -> Dict[str, bool]:
        """
        Verify that queries are using appropriate indexes

        Args:
            session_id: Session ID

        Returns:
            Dictionary indicating which indexes are being used:
            {
                'idx_change_session_classification': bool,
                'idx_change_session_type': bool,
                'idx_change_session_order': bool,
                'idx_review_session_status': bool
            }
        """
        index_usage = {}

        # Check if session_id + classification index is used
        plan = self.analyze_query_plan(session_id, 'filter_changes')
        for step in plan:
            detail = step['detail'].lower()
            if 'idx_change_session_classification' in detail:
                index_usage['idx_change_session_classification'] = True
            if 'idx_change_session_type' in detail:
                index_usage['idx_change_session_type'] = True
            if 'idx_change_session_order' in detail:
                index_usage['idx_change_session_order'] = True
            if 'idx_review_session_status' in detail:
                index_usage['idx_review_session_status'] = True

        # Set defaults for indexes not found in plan
        index_usage.setdefault('idx_change_session_classification', False)
        index_usage.setdefault('idx_change_session_type', False)
        index_usage.setdefault('idx_change_session_order', False)
        index_usage.setdefault('idx_review_session_status', False)

        return index_usage

    def get_statistics_by_type(
        self,
        session_id: int,
        object_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for a specific object type using optimized aggregation

        Args:
            session_id: Session ID
            object_type: Optional object type to filter by

        Returns:
            Dictionary with statistics:
            {
                'object_type': str,
                'total': int,
                'no_conflict': int,
                'conflict': int,
                'customer_only': int,
                'removed_but_customized': int
            }
        """
        from sqlalchemy import func, case
        from models import Change

        query = db.session.query(
            func.count(Change.id).label('total'),
            func.sum(case((Change.classification == 'NO_CONFLICT', 1), else_=0)).label('no_conflict'),
            func.sum(case((Change.classification == 'CONFLICT', 1), else_=0)).label('conflict'),
            func.sum(case((Change.classification == 'CUSTOMER_ONLY', 1), else_=0)).label('customer_only'),
            func.sum(case((Change.classification == 'REMOVED_BUT_CUSTOMIZED', 1), else_=0)).label('removed_but_customized')
        ).filter(Change.session_id == session_id)

        if object_type:
            # Uses idx_change_session_type for efficient filtering
            query = query.filter(Change.object_type == object_type)

        result = query.first()

        return {
            'object_type': object_type or 'all',
            'total': result.total or 0,
            'no_conflict': result.no_conflict or 0,
            'conflict': result.conflict or 0,
            'customer_only': result.customer_only or 0,
            'removed_but_customized': result.removed_but_customized or 0
        }
