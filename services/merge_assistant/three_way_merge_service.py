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

            # Store blueprints
            session.base_blueprint = json.dumps(base_result)
            session.customized_blueprint = json.dumps(customized_result)
            session.new_vendor_blueprint = json.dumps(new_vendor_result)
            db.session.commit()

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

            # Store comparison results
            session.vendor_changes = json.dumps(vendor_changes)
            session.customer_changes = json.dumps(customer_changes)
            db.session.commit()

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

            # Store classification results
            session.classification_results = json.dumps(
                classification_results
            )
            db.session.commit()

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

            # Store ordered changes
            session.ordered_changes = json.dumps(ordered_changes)
            session.total_changes = len(ordered_changes)
            db.session.commit()

            # Create ChangeReview records for each change
            for idx, change in enumerate(ordered_changes):
                review = ChangeReview(
                    session_id=session.id,
                    object_uuid=change['uuid'],
                    object_name=change.get('name', 'Unknown'),
                    object_type=change.get('type', 'Unknown'),
                    classification=change.get('classification', 'UNKNOWN'),
                    review_status='pending'
                )
                db.session.add(review)

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
        Get merge summary with statistics

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
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Parse classification results
        classification_results = json.loads(
            session.classification_results
        )

        # Calculate statistics
        statistics = {
            'total_changes': session.total_changes,
            'no_conflict': len(
                classification_results.get('NO_CONFLICT', [])
            ),
            'conflict': len(classification_results.get('CONFLICT', [])),
            'customer_only': len(
                classification_results.get('CUSTOMER_ONLY', [])
            ),
            'removed_but_customized': len(
                classification_results.get('REMOVED_BUT_CUSTOMIZED', [])
            )
        }

        # Calculate breakdown by type
        breakdown_by_type = self._calculate_breakdown_by_type(
            classification_results
        )

        # Estimate complexity and time
        complexity, estimated_hours = self._estimate_complexity(statistics)

        return {
            'session_id': session.id,
            'reference_id': session.reference_id,
            'packages': {
                'base': session.base_package_name,
                'customized': session.customized_package_name,
                'new_vendor': session.new_vendor_package_name
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

    def get_ordered_changes(self, session_id: int) -> List[Dict[str, Any]]:
        """
        Get smart-ordered list of changes

        Args:
            session_id: Session ID

        Returns:
            List of change objects in smart order
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if not session.ordered_changes:
            return []

        return json.loads(session.ordered_changes)

    def update_progress(
        self,
        session_id: int,
        change_index: int,
        review_status: str,
        notes: Optional[str] = None
    ) -> None:
        """
        Update user progress on a specific change

        Args:
            session_id: Session ID
            change_index: Index of the change in ordered list
            review_status: 'reviewed' or 'skipped'
            notes: Optional user notes

        Raises:
            ValueError: If session not found or invalid parameters
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Initialize logger
        logger = create_merge_session_logger(session.reference_id)

        # Get ordered changes
        ordered_changes = json.loads(session.ordered_changes)

        if change_index < 0 or change_index >= len(ordered_changes):
            raise ValueError(
                f"Invalid change index: {change_index}. "
                f"Must be between 0 and {len(ordered_changes) - 1}"
            )

        # Get the change
        change = ordered_changes[change_index]
        object_uuid = change['uuid']

        # Find or create ChangeReview record
        review = ChangeReview.query.filter_by(
            session_id=session_id,
            object_uuid=object_uuid
        ).first()

        if not review:
            # Create new review record
            review = ChangeReview(
                session_id=session_id,
                object_uuid=object_uuid,
                object_name=change.get('name', 'Unknown'),
                object_type=change.get('type', 'Unknown'),
                classification=change.get('classification', 'UNKNOWN')
            )
            db.session.add(review)

        # Update review
        review.review_status = review_status
        review.user_notes = notes
        review.reviewed_at = datetime.utcnow()

        # Update session progress
        session.current_change_index = change_index

        # Commit the review first so it's included in the count
        db.session.commit()

        # Update counts by querying all reviews with each status
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
            change.get('name', 'Unknown'),
            change.get('type', 'Unknown'),
            change.get('classification', 'UNKNOWN')
        )

        # Check if workflow is complete
        if change_index == len(ordered_changes) - 1:
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
            logger.log_workflow_complete(
                session.reviewed_count,
                session.skipped_count
            )

        db.session.commit()

    def generate_report(self, session_id: int) -> Dict[str, Any]:
        """
        Generate final merge report

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
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Initialize logger
        logger = create_merge_session_logger(session.reference_id)
        logger.log_report_generation()

        # Get summary
        summary = self.get_summary(session_id)

        # Get ordered changes
        ordered_changes = json.loads(session.ordered_changes)

        # Get all review records
        reviews = ChangeReview.query.filter_by(
            session_id=session_id
        ).all()

        # Build review lookup
        review_lookup = {
            review.object_uuid: review for review in reviews
        }

        # Add review information to changes
        changes_with_reviews = []
        for change in ordered_changes:
            uuid = change['uuid']
            review = review_lookup.get(uuid)

            change_with_review = change.copy()
            if review:
                change_with_review['review_status'] = review.review_status
                change_with_review['user_notes'] = review.user_notes
                change_with_review['reviewed_at'] = (
                    review.reviewed_at.isoformat()
                    if review.reviewed_at else None
                )
            else:
                change_with_review['review_status'] = 'pending'
                change_with_review['user_notes'] = None
                change_with_review['reviewed_at'] = None

            changes_with_reviews.append(change_with_review)

        # Group changes by category
        changes_by_category = {
            'NO_CONFLICT': [],
            'CONFLICT': [],
            'CUSTOMER_ONLY': [],
            'REMOVED_BUT_CUSTOMIZED': []
        }

        for change in changes_with_reviews:
            classification = change.get('classification', 'UNKNOWN')
            if classification in changes_by_category:
                changes_by_category[classification].append(change)

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
        search_term: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter changes based on criteria

        Args:
            session_id: Session ID
            classification: Filter by classification
            object_type: Filter by object type
            review_status: Filter by review status
            search_term: Search by object name

        Returns:
            Filtered list of changes
        """
        # Get session for logger
        session = self.get_session(session_id)
        if session:
            logger = create_merge_session_logger(session.reference_id)
        
        # Get ordered changes
        ordered_changes = self.get_ordered_changes(session_id)

        # Get review records
        reviews = ChangeReview.query.filter_by(
            session_id=session_id
        ).all()
        review_lookup = {
            review.object_uuid: review for review in reviews
        }

        # Apply filters
        filtered = []
        for change in ordered_changes:
            # Classification filter
            if (classification and
                    change.get('classification') != classification):
                continue

            # Object type filter
            if object_type and change.get('type') != object_type:
                continue

            # Review status filter
            if review_status:
                review = review_lookup.get(change['uuid'])
                if not review or review.review_status != review_status:
                    continue

            # Search term filter
            if search_term:
                name = change.get('name', '').lower()
                if search_term.lower() not in name:
                    continue

            # Add review information
            review = review_lookup.get(change['uuid'])
            if review:
                change['review_status'] = review.review_status
                change['user_notes'] = review.user_notes
            else:
                change['review_status'] = 'pending'
                change['user_notes'] = None

            filtered.append(change)
        
        # Log filter application
        if session:
            logger.log_filter_applied(
                classification=classification,
                object_type=object_type,
                review_status=review_status,
                search_term=search_term,
                result_count=len(filtered)
            )

        return filtered

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

    def _calculate_breakdown_by_type(
        self,
        classification_results: Dict[str, List[Dict]]
    ) -> Dict[str, Dict[str, int]]:
        """
        Calculate breakdown by object type for each category

        Args:
            classification_results: Classification results dictionary

        Returns:
            Dictionary with breakdown:
            {
                'interfaces': {'no_conflict': 10, 'conflict': 5, ...},
                'process_models': {...},
                ...
            }
        """
        breakdown = {}

        for category, changes in classification_results.items():
            for change in changes:
                obj_type = change.get('type', 'Unknown')

                if obj_type not in breakdown:
                    breakdown[obj_type] = {
                        'no_conflict': 0,
                        'conflict': 0,
                        'customer_only': 0,
                        'removed_but_customized': 0
                    }

                # Map category to lowercase key
                category_key = category.lower()
                if category_key in breakdown[obj_type]:
                    breakdown[obj_type][category_key] += 1

        return breakdown

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
