"""
Three Way Merge Orchestrator

Coordinates the complete three-way merge workflow by orchestrating all
sub-services (extraction, delta, customer, classification, guidance).
"""

import logging
import time
from typing import Dict, Any, List, Optional

from core.base_service import BaseService
from core.logger import LoggerConfig, get_merge_logger
from models import db, MergeSession, Package, Change
from repositories.change_repository import ChangeRepository
from services.package_extraction_service import PackageExtractionService
from services.delta_comparison_service import DeltaComparisonService
from services.customer_comparison_service import CustomerComparisonService
from services.classification_service import ClassificationService
from services.merge_guidance_service import MergeGuidanceService
from services.comparison_persistence_service import (
    ComparisonPersistenceService
)
from domain.enums import SessionStatus


class ThreeWayMergeOrchestrator(BaseService):
    """
    Orchestrator for the complete three-way merge workflow.
    
    This service coordinates all sub-services to execute the 8-step workflow:
    1. Create session record
    2. Extract all three packages (transactional)
    3. Perform delta comparison (A→C)
    4. Perform customer comparison (delta vs B)
    5. Classify changes (apply 7 rules)
    6. Generate merge guidance
    7. Update session status to 'ready'
    8. Return session with reference_id and total_changes
    
    Key Design Principles:
    - Transactional: All operations in a single transaction
    - Rollback on error: Any failure rolls back entire session
    - Status tracking: Session status updated at each step
    - Error handling: Comprehensive error handling with logging
    - Idempotent: Can be retried safely
    
    Example:
        >>> orchestrator = ThreeWayMergeOrchestrator()
        >>> session = orchestrator.create_merge_session(
        ...     base_zip_path="/path/to/base.zip",
        ...     customized_zip_path="/path/to/customized.zip",
        ...     new_vendor_zip_path="/path/to/new_vendor.zip"
        ... )
        >>> print(f"Session {session.reference_id} created with "
        ...       f"{session.total_changes} changes")
    """
    
    def __init__(self, container=None):
        """Initialize orchestrator with dependencies."""
        super().__init__(container)
        self.logger = get_merge_logger()
    
    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.package_extraction_service = self._get_service(
            PackageExtractionService
        )
        self.delta_comparison_service = self._get_service(
            DeltaComparisonService
        )
        self.customer_comparison_service = self._get_service(
            CustomerComparisonService
        )
        self.classification_service = self._get_service(
            ClassificationService
        )
        self.merge_guidance_service = self._get_service(
            MergeGuidanceService
        )
        self.comparison_persistence_service = self._get_service(
            ComparisonPersistenceService
        )
        self.change_repository = self._get_repository(ChangeRepository)
    
    def create_merge_session(
        self,
        base_zip_path: str,
        customized_zip_path: str,
        new_vendor_zip_path: str
    ) -> MergeSession:
        """
        Create and process a new merge session.
        
        This is the main entry point for the three-way merge workflow.
        It executes all 8 steps in a single transaction.
        
        Workflow:
        1. Create session record with status='PROCESSING'
        2. Extract Package A (Base)
        3. Extract Package B (Customized)
        4. Extract Package C (New Vendor)
        5. Perform delta comparison (A→C)
        6. Perform customer comparison (delta vs B)
        7. Classify changes (apply 7 rules)
        8. Generate merge guidance
        9. Update session status to 'READY'
        10. Commit transaction
        
        If any step fails:
        - Log error
        - Update session status to 'ERROR'
        - Rollback transaction
        - Raise exception
        
        Args:
            base_zip_path: Path to Package A (Base Version) ZIP file
            customized_zip_path: Path to Package B (Customer Version) ZIP file
            new_vendor_zip_path: Path to Package C (New Vendor Version) ZIP file
            
        Returns:
            MergeSession: Created session with reference_id and total_changes
            
        Raises:
            ThreeWayMergeException: If any step fails
            
        Example:
            >>> orchestrator = ThreeWayMergeOrchestrator()
            >>> session = orchestrator.create_merge_session(
            ...     base_zip_path="applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip",
            ...     customized_zip_path="applicationArtifacts/Three Way Testing Files/V2/Test Application Customer Version.zip",
            ...     new_vendor_zip_path="applicationArtifacts/Three Way Testing Files/V2/Test Application Vendor New Version.zip"
            ... )
            >>> print(f"Session {session.reference_id}: {session.status}")
            >>> print(f"Total changes: {session.total_changes}")
        """
        session = None
        workflow_start_time = time.time()
        
        try:
            # Log workflow start
            LoggerConfig.log_separator(self.logger)
            self.logger.info("THREE-WAY MERGE WORKFLOW STARTING")
            LoggerConfig.log_separator(self.logger)
            
            LoggerConfig.log_function_entry(
                self.logger,
                'create_merge_session',
                base_zip_path=base_zip_path,
                customized_zip_path=customized_zip_path,
                new_vendor_zip_path=new_vendor_zip_path
            )
            
            # Step 1: Create session record
            step_start = time.time()
            LoggerConfig.log_step(self.logger, 1, 8, "Creating merge session record")
            
            session = self._create_session()
            
            step_duration = time.time() - step_start
            self.logger.info(
                f"✓ Session created: {session.reference_id} (id={session.id}) "
                f"in {step_duration:.2f}s"
            )
            
            # Step 2: Extract Package A (Base)
            step_start = time.time()
            LoggerConfig.log_step(self.logger, 2, 8, "Extracting Package A (Base Version)")
            self.logger.debug(f"Package A path: {base_zip_path}")
            
            package_a = self.package_extraction_service.extract_package(
                session_id=session.id,
                zip_path=base_zip_path,
                package_type='base'
            )
            
            step_duration = time.time() - step_start
            self.logger.info(
                f"✓ Package A extracted: {package_a.total_objects} objects "
                f"in {step_duration:.2f}s"
            )
            
            # Step 3: Extract Package B (Customized)
            step_start = time.time()
            LoggerConfig.log_step(self.logger, 3, 8, "Extracting Package B (Customer Version)")
            self.logger.debug(f"Package B path: {customized_zip_path}")
            
            package_b = self.package_extraction_service.extract_package(
                session_id=session.id,
                zip_path=customized_zip_path,
                package_type='customized'
            )
            
            step_duration = time.time() - step_start
            self.logger.info(
                f"✓ Package B extracted: {package_b.total_objects} objects "
                f"in {step_duration:.2f}s"
            )
            
            # Step 4: Extract Package C (New Vendor)
            step_start = time.time()
            LoggerConfig.log_step(self.logger, 4, 8, "Extracting Package C (New Vendor Version)")
            self.logger.debug(f"Package C path: {new_vendor_zip_path}")
            
            package_c = self.package_extraction_service.extract_package(
                session_id=session.id,
                zip_path=new_vendor_zip_path,
                package_type='new_vendor'
            )
            
            step_duration = time.time() - step_start
            self.logger.info(
                f"✓ Package C extracted: {package_c.total_objects} objects "
                f"in {step_duration:.2f}s"
            )
            
            # Step 5: Perform delta comparison (A→C)
            step_start = time.time()
            LoggerConfig.log_step(self.logger, 5, 8, "Performing delta comparison (A→C)")
            self.logger.debug(
                f"Comparing base package (id={package_a.id}) with "
                f"new vendor package (id={package_c.id})"
            )
            
            delta_changes = self.delta_comparison_service.compare(
                session_id=session.id,
                base_package_id=package_a.id,
                new_vendor_package_id=package_c.id
            )
            
            step_duration = time.time() - step_start
            self.logger.info(
                f"✓ Delta comparison complete: {len(delta_changes)} changes detected "
                f"in {step_duration:.2f}s"
            )
            
            # Step 6: Perform customer comparison (delta vs B)
            step_start = time.time()
            LoggerConfig.log_step(self.logger, 6, 8, "Performing customer comparison (delta vs B)")
            self.logger.debug(
                f"Analyzing customer modifications in package B (id={package_b.id})"
            )
            
            customer_modifications = (
                self.customer_comparison_service.compare(
                    base_package_id=package_a.id,
                    customer_package_id=package_b.id,
                    delta_changes=delta_changes
                )
            )
            
            step_duration = time.time() - step_start
            self.logger.info(
                f"✓ Customer comparison complete: {len(customer_modifications)} objects analyzed "
                f"in {step_duration:.2f}s"
            )
            
            # Step 7: Classify changes (apply 7 rules)
            step_start = time.time()
            LoggerConfig.log_step(self.logger, 7, 8, "Classifying changes (applying 7 classification rules)")
            self.logger.debug("Applying classification rules 10a-10g")
            
            classified_changes = self.classification_service.classify(
                session_id=session.id,
                delta_changes=delta_changes,
                customer_modifications=customer_modifications
            )
            
            step_duration = time.time() - step_start
            self.logger.info(
                f"✓ Classification complete: {len(classified_changes)} changes classified "
                f"in {step_duration:.2f}s"
            )
            
            # Log classification breakdown
            classification_counts = {}
            for change in classified_changes:
                classification_counts[change.classification] = \
                    classification_counts.get(change.classification, 0) + 1
            
            self.logger.info("Classification breakdown:")
            # Sort by classification name instead of value to avoid comparison issues
            for classification, count in sorted(classification_counts.items(), key=lambda x: x[0].name):
                self.logger.info(f"  - {classification.value}: {count}")
            
            # Step 8: Persist detailed comparisons
            step_start = time.time()
            LoggerConfig.log_step(
                self.logger, 8, 9,
                "Persisting detailed object comparisons"
            )
            
            comparison_counts = (
                self.comparison_persistence_service.persist_all_comparisons(
                    session_id=session.id,
                    base_package_id=package_a.id,
                    customer_package_id=package_b.id,
                    new_vendor_package_id=package_c.id
                )
            )
            
            step_duration = time.time() - step_start
            self.logger.info(
                f"✓ Comparison persistence complete: {comparison_counts} "
                f"in {step_duration:.2f}s"
            )
            
            # Step 9: Generate merge guidance
            step_start = time.time()
            LoggerConfig.log_step(self.logger, 9, 9, "Generating merge guidance")
            
            changes = self.change_repository.get_by_session(session.id)
            self.logger.debug(
                f"Retrieved {len(changes)} changes for guidance generation"
            )
            
            guidance_records = self.merge_guidance_service.generate_guidance(
                session_id=session.id,
                changes=changes
            )
            
            step_duration = time.time() - step_start
            self.logger.info(
                f"✓ Guidance generation complete: "
                f"{len(guidance_records)} guidance records "
                f"in {step_duration:.2f}s"
            )
            
            # Update session with total changes and status
            session.total_changes = len(classified_changes)
            session.status = SessionStatus.READY.value
            db.session.flush()
            
            # Commit transaction
            self.logger.debug("Committing database transaction")
            db.session.commit()
            self.logger.debug("Transaction committed successfully")
            
            # Calculate total workflow duration
            workflow_duration = time.time() - workflow_start_time
            
            # Log workflow completion
            LoggerConfig.log_separator(self.logger)
            self.logger.info("THREE-WAY MERGE WORKFLOW COMPLETED SUCCESSFULLY")
            LoggerConfig.log_separator(self.logger)
            
            self.logger.info(f"Session Reference ID: {session.reference_id}")
            self.logger.info(f"Session Status: {session.status}")
            self.logger.info(f"Total Changes: {session.total_changes}")
            
            LoggerConfig.log_performance(
                self.logger,
                'Three-Way Merge Workflow',
                workflow_duration,
                session_id=session.id,
                reference_id=session.reference_id,
                total_changes=session.total_changes,
                package_a_objects=package_a.total_objects,
                package_b_objects=package_b.total_objects,
                package_c_objects=package_c.total_objects
            )
            
            LoggerConfig.log_separator(self.logger)
            
            LoggerConfig.log_function_exit(
                self.logger,
                'create_merge_session',
                result=f"Session {session.reference_id} with {session.total_changes} changes"
            )
            
            return session
            
        except Exception as e:
            workflow_duration = time.time() - workflow_start_time
            
            LoggerConfig.log_separator(self.logger, char="-")
            self.logger.error("THREE-WAY MERGE WORKFLOW FAILED")
            LoggerConfig.log_separator(self.logger, char="-")
            
            LoggerConfig.log_error_with_context(
                self.logger,
                e,
                'Three-way merge workflow',
                session_id=session.id if session else None,
                reference_id=session.reference_id if session else None,
                base_zip_path=base_zip_path,
                customized_zip_path=customized_zip_path,
                new_vendor_zip_path=new_vendor_zip_path,
                workflow_duration=f"{workflow_duration:.2f}s"
            )
            
            # Update session status to ERROR if session was created
            if session:
                try:
                    self.logger.debug(f"Updating session {session.reference_id} status to ERROR")
                    session.status = SessionStatus.ERROR.value
                    db.session.commit()
                    self.logger.info(f"Session {session.reference_id} marked as ERROR")
                except Exception as commit_error:
                    self.logger.error(
                        f"Failed to update session status: {commit_error}",
                        exc_info=True
                    )
            
            # Rollback transaction
            self.logger.debug("Rolling back database transaction")
            db.session.rollback()
            self.logger.debug("Transaction rolled back")
            
            LoggerConfig.log_separator(self.logger, char="-")
            
            # Re-raise as ThreeWayMergeException
            raise ThreeWayMergeException(
                f"Failed to create merge session: {e}"
            ) from e
    
    def _create_session(self) -> MergeSession:
        """
        Create a new merge session record.
        
        Generates a unique reference_id in format: MRG_XXX
        where XXX is a sequential 3-digit number (001, 002, etc.).
        
        Returns:
            MergeSession: Created session with status='PROCESSING'
            
        Example:
            >>> session = orchestrator._create_session()
            >>> print(session.reference_id)  # MRG_001
        """
        # Generate unique reference_id
        reference_id = self._generate_reference_id()
        
        # Create session
        session = MergeSession(
            reference_id=reference_id,
            status=SessionStatus.PROCESSING.value,
            total_changes=0
        )
        
        db.session.add(session)
        db.session.flush()
        
        return session
    
    def _generate_reference_id(self) -> str:
        """
        Generate unique reference ID for merge session.
        
        Format: MRG_XXX where XXX is a sequential 3-digit number (001, 002, etc.).
        
        Returns:
            str: Unique reference ID
            
        Example:
            >>> ref_id = orchestrator._generate_reference_id()
            >>> print(ref_id)  # MRG_001
        """
        # Get the last session to determine next sequence number
        last_session = MergeSession.query.order_by(MergeSession.id.desc()).first()
        
        if last_session and last_session.reference_id.startswith('MRG_'):
            # Extract sequence number from last reference_id
            try:
                last_seq = int(last_session.reference_id.split('_')[1])
                next_seq = last_seq + 1
            except (IndexError, ValueError):
                # If parsing fails, start from 1
                next_seq = 1
        else:
            # First session or migrating from old format
            next_seq = 1
        
        return f"MRG_{next_seq:03d}"
    
    def get_session_status(self, reference_id: str) -> Dict[str, Any]:
        """
        Get current status of merge session.
        
        Returns comprehensive status information including:
        - Session metadata (reference_id, status, created_at)
        - Package information (filenames, object counts)
        - Statistics (total changes, by classification)
        - Progress information
        
        Args:
            reference_id: Session reference ID (e.g., MRG_001)
            
        Returns:
            Dict with session status information
            
        Raises:
            ValueError: If session not found
            
        Example:
            >>> status = orchestrator.get_session_status("MRG_001")
            >>> print(f"Status: {status['status']}")
            >>> print(f"Total changes: {status['total_changes']}")
            >>> print(f"Conflicts: {status['statistics']['CONFLICT']}")
        """
        # Find session
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()
        
        if not session:
            raise ValueError(f"Session not found: {reference_id}")
        
        # Get packages
        packages = db.session.query(Package).filter_by(
            session_id=session.id
        ).all()
        
        package_info = {
            pkg.package_type: {
                'filename': pkg.filename,
                'total_objects': pkg.total_objects
            }
            for pkg in packages
        }
        
        # Get statistics
        classification_stats = self._get_session_statistics(session.id)
        
        # Get statistics by object type
        from sqlalchemy import func
        from models import ObjectLookup
        
        object_type_results = db.session.query(
            ObjectLookup.object_type,
            func.count(Change.id).label('count')
        ).join(
            Change, Change.object_id == ObjectLookup.id
        ).filter(
            Change.session_id == session.id
        ).group_by(
            ObjectLookup.object_type
        ).all()
        
        # Build by_object_type dict
        by_object_type = {}
        for obj_type, count in object_type_results:
            by_object_type[obj_type] = count
        
        return {
            'reference_id': session.reference_id,
            'status': session.status,
            'total_changes': session.total_changes,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'packages': package_info,
            'statistics': {
                'total_changes': session.total_changes,
                'by_classification': classification_stats,
                'by_object_type': by_object_type
            }
        }
    
    def _get_session_statistics(self, session_id: int) -> Dict[str, int]:
        """
        Get statistics for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with statistics by classification
            
        Example:
            >>> stats = orchestrator._get_session_statistics(1)
            >>> print(stats)
            {
                'NO_CONFLICT': 10,
                'CONFLICT': 5,
                'NEW': 3,
                'DELETED': 2
            }
        """
        from sqlalchemy import func
        
        # Query changes grouped by classification
        results = db.session.query(
            Change.classification,
            func.count(Change.id).label('count')
        ).filter(
            Change.session_id == session_id
        ).group_by(
            Change.classification
        ).all()
        
        # Convert to dict
        statistics = {
            'NO_CONFLICT': 0,
            'CONFLICT': 0,
            'NEW': 0,
            'DELETED': 0
        }
        
        for classification, count in results:
            statistics[classification] = count
        
        return statistics
    
    def get_working_set(
        self,
        reference_id: str,
        classification_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get working set of changes for review.
        
        Returns changes with object details for user review.
        Can optionally filter by classification.
        
        Args:
            reference_id: Session reference ID
            classification_filter: Optional list of classifications to filter
                                  (e.g., ['CONFLICT', 'NEW'])
            
        Returns:
            List of dicts with change and object information
            
        Raises:
            ValueError: If session not found
            
        Example:
            >>> # Get all changes
            >>> changes = orchestrator.get_working_set("MRG_001")
            >>> print(f"Total changes: {len(changes)}")
            
            >>> # Get only conflicts
            >>> conflicts = orchestrator.get_working_set(
            ...     "MRG_001",
            ...     classification_filter=['CONFLICT']
            ... )
            >>> print(f"Conflicts: {len(conflicts)}")
        """
        # Find session
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()
        
        if not session:
            raise ValueError(f"Session not found: {reference_id}")
        
        # Build query
        query = db.session.query(Change).filter(
            Change.session_id == session.id
        )
        
        # Apply classification filter if provided
        if classification_filter:
            query = query.filter(
                Change.classification.in_(classification_filter)
            )
        
        # Order by display_order
        query = query.order_by(Change.display_order)
        
        # Execute query
        changes = query.all()
        
        # Convert to dicts with object information
        working_set = []
        
        for change in changes:
            # Get object details
            obj = change.object
            
            change_dict = {
                'change_id': change.id,
                'display_order': change.display_order,
                'classification': change.classification,
                'vendor_change_type': change.vendor_change_type,
                'customer_change_type': change.customer_change_type,
                'object': {
                    'id': obj.id,
                    'uuid': obj.uuid,
                    'name': obj.name,
                    'object_type': obj.object_type,
                    'description': obj.description
                }
            }
            
            working_set.append(change_dict)
        
        return working_set
    
    def delete_session(self, reference_id: str) -> None:
        """
        Delete a merge session and all related data.
        
        This will cascade delete:
        - Packages
        - Package object mappings
        - Object versions
        - Delta comparison results
        - Changes
        
        Note: Objects in object_lookup are NOT deleted (they may be
        referenced by other sessions).
        
        Args:
            reference_id: Session reference ID
            
        Raises:
            ValueError: If session not found
            
        Example:
            >>> orchestrator.delete_session("MRG_001")
        """
        # Find session
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()
        
        if not session:
            raise ValueError(f"Session not found: {reference_id}")
        
        self.logger.info(f"Deleting session {reference_id}")
        
        # Delete session (cascades to all related data)
        db.session.delete(session)
        db.session.commit()
        
        self.logger.info(f"Session {reference_id} deleted")
    
    def retry_failed_session(
        self,
        reference_id: str,
        base_zip_path: str,
        customized_zip_path: str,
        new_vendor_zip_path: str
    ) -> MergeSession:
        """
        Retry a failed session.
        
        This deletes the failed session and creates a new one with the
        same packages.
        
        Args:
            reference_id: Failed session reference ID
            base_zip_path: Path to Package A ZIP file
            customized_zip_path: Path to Package B ZIP file
            new_vendor_zip_path: Path to Package C ZIP file
            
        Returns:
            MergeSession: New session
            
        Example:
            >>> session = orchestrator.retry_failed_session(
            ...     reference_id="MRG_001",
            ...     base_zip_path="/path/to/base.zip",
            ...     customized_zip_path="/path/to/customized.zip",
            ...     new_vendor_zip_path="/path/to/new_vendor.zip"
            ... )
        """
        self.logger.info(f"Retrying failed session {reference_id}")
        
        # Delete failed session
        try:
            self.delete_session(reference_id)
        except ValueError:
            # Session doesn't exist, that's fine
            pass
        
        # Create new session
        return self.create_merge_session(
            base_zip_path=base_zip_path,
            customized_zip_path=customized_zip_path,
            new_vendor_zip_path=new_vendor_zip_path
        )


class ThreeWayMergeException(Exception):
    """Exception raised when three-way merge workflow fails."""
    pass
