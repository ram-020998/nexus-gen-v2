"""
Migration Service for Three-Way Merge Assistant

This service handles migrating existing MergeSession data from the old JSON-based
schema to the new normalized relational schema.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from models import (
    db, MergeSession, Package, AppianObject, Change, ChangeReview,
    MergeGuidance, MergeConflict, MergeChange, ObjectDependency,
    PackageObjectTypeCount, ProcessModelMetadata, ProcessModelNode, ProcessModelFlow
)
from services.merge_assistant.package_service import PackageService
from services.merge_assistant.change_service import ChangeService
from services.merge_assistant.logger import get_logger


class MigrationError(Exception):
    """Raised when migration fails"""
    pass


class MigrationService:
    """Service for migrating MergeSession data from JSON to normalized schema"""
    
    def __init__(self):
        self.logger = get_logger()
        self.package_service = PackageService()
        self.change_service = ChangeService()
    
    def migrate_session(self, session_id: int) -> bool:
        """
        Migrate a single session from old to new schema
        
        Steps:
        1. Load MergeSession record
        2. Parse JSON blobs
        3. Create Package records
        4. Create AppianObject records
        5. Create Change records
        6. Update ChangeReview records
        7. Verify data integrity
        8. Clear old JSON columns
        
        Args:
            session_id: ID of the session to migrate
            
        Returns:
            True if migration successful, False otherwise
            
        Raises:
            MigrationError: If migration fails
        """
        self.logger.info(f"Starting migration for session {session_id}")
        
        try:
            # Load session
            session = MergeSession.query.get(session_id)
            if not session:
                raise MigrationError(f"Session {session_id} not found")
            
            # Check if already migrated
            if session.packages:
                self.logger.info(f"Session {session_id} already migrated, skipping")
                return True
            
            # Start transaction
            try:
                # Parse JSON blobs
                self.logger.info(f"Parsing JSON data for session {session_id}")
                base_blueprint = self._parse_json(session.base_blueprint, "base_blueprint")
                customized_blueprint = self._parse_json(session.customized_blueprint, "customized_blueprint")
                new_vendor_blueprint = self._parse_json(session.new_vendor_blueprint, "new_vendor_blueprint")
                vendor_changes = self._parse_json(session.vendor_changes, "vendor_changes")
                customer_changes = self._parse_json(session.customer_changes, "customer_changes")
                classification_results = self._parse_json(session.classification_results, "classification_results")
                ordered_changes = self._parse_json(session.ordered_changes, "ordered_changes")
                
                # Migrate blueprints to Package and AppianObject records
                self.logger.info(f"Migrating blueprints for session {session_id}")
                base_package = self._migrate_blueprint(
                    session_id, 'base', session.base_package_name, base_blueprint
                )
                customized_package = self._migrate_blueprint(
                    session_id, 'customized', session.customized_package_name, customized_blueprint
                )
                new_vendor_package = self._migrate_blueprint(
                    session_id, 'new_vendor', session.new_vendor_package_name, new_vendor_blueprint
                )
                
                # Migrate comparison results to Change records
                self.logger.info(f"Migrating changes for session {session_id}")
                self._migrate_changes(
                    session_id,
                    ordered_changes,
                    classification_results
                )
                
                # Update existing ChangeReview records to link to Change records
                self.logger.info(f"Updating change reviews for session {session_id}")
                self._update_change_reviews(session_id)
                
                # Flush to ensure all changes are visible for verification
                db.session.flush()
                
                # Verify migration
                self.logger.info(f"Verifying migration for session {session_id}")
                verification = self.verify_migration(session_id)
                if not all(verification.values()):
                    raise MigrationError(f"Migration verification failed: {verification}")
                
                # Clear old JSON columns (optional - can be done later)
                # self._clear_json_columns(session)
                
                # Commit transaction
                db.session.commit()
                
                self.logger.info(f"Successfully migrated session {session_id}")
                return True
                
            except Exception as e:
                db.session.rollback()
                self.logger.error(f"Error migrating session {session_id}: {str(e)}", exc_info=True)
                raise MigrationError(f"Failed to migrate session {session_id}: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Migration failed for session {session_id}: {str(e)}", exc_info=True)
            raise
    
    def verify_migration(self, session_id: int) -> Dict[str, bool]:
        """
        Verify migration correctness
        
        Checks:
        - Package count = 3
        - Object count matches blueprint metadata
        - Change count matches ordered_changes length
        - Review count matches changes count
        - All foreign keys valid
        
        Args:
            session_id: ID of the session to verify
            
        Returns:
            Dictionary with verification results
        """
        self.logger.info(f"Verifying migration for session {session_id}")
        
        results = {
            'package_count': False,
            'object_count': False,
            'change_count': False,
            'review_count': False,
            'foreign_keys': False
        }
        
        try:
            session = MergeSession.query.get(session_id)
            if not session:
                self.logger.error(f"Session {session_id} not found")
                return results
            
            # Check package count
            package_count = Package.query.filter_by(session_id=session_id).count()
            results['package_count'] = package_count == 3
            if not results['package_count']:
                self.logger.warning(f"Package count mismatch: expected 3, got {package_count}")
            
            # Check object count
            packages = Package.query.filter_by(session_id=session_id).all()
            total_expected_objects = sum(p.total_objects for p in packages)
            total_actual_objects = sum(
                AppianObject.query.filter_by(package_id=p.id).count()
                for p in packages
            )
            results['object_count'] = total_expected_objects == total_actual_objects
            if not results['object_count']:
                self.logger.warning(
                    f"Object count mismatch: expected {total_expected_objects}, "
                    f"got {total_actual_objects}"
                )
            
            # Check change count
            change_count = Change.query.filter_by(session_id=session_id).count()
            expected_change_count = session.total_changes
            results['change_count'] = change_count == expected_change_count
            if not results['change_count']:
                self.logger.warning(
                    f"Change count mismatch: expected {expected_change_count}, "
                    f"got {change_count}"
                )
            
            # Check review count
            review_count = ChangeReview.query.filter_by(session_id=session_id).count()
            results['review_count'] = review_count == change_count
            if not results['review_count']:
                self.logger.warning(
                    f"Review count mismatch: expected {change_count}, "
                    f"got {review_count}"
                )
            
            # Check foreign keys
            results['foreign_keys'] = self._verify_foreign_keys(session_id)
            
            self.logger.info(f"Verification results for session {session_id}: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error verifying session {session_id}: {str(e)}", exc_info=True)
            return results
    
    def _parse_json(self, json_str: Optional[str], field_name: str) -> Any:
        """Parse JSON string, handling None and empty strings"""
        if not json_str:
            self.logger.warning(f"Empty or None JSON for {field_name}")
            return None
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON for {field_name}: {str(e)}")
            raise MigrationError(f"Invalid JSON in {field_name}: {str(e)}")
    
    def _migrate_blueprint(
        self,
        session_id: int,
        package_type: str,
        package_name: str,
        blueprint: Dict[str, Any]
    ) -> Package:
        """
        Migrate a blueprint to Package and AppianObject records
        
        Args:
            session_id: Session ID
            package_type: 'base', 'customized', or 'new_vendor'
            package_name: Name of the package
            blueprint: Blueprint dictionary
            
        Returns:
            Created Package record
        """
        if not blueprint:
            raise MigrationError(f"Blueprint is None for {package_type}")
        
        # Ensure package_name is in blueprint metadata
        if 'blueprint' not in blueprint:
            blueprint['blueprint'] = {}
        if 'metadata' not in blueprint['blueprint']:
            blueprint['blueprint']['metadata'] = {}
        if 'package_name' not in blueprint['blueprint']['metadata']:
            blueprint['blueprint']['metadata']['package_name'] = package_name
        
        # Use PackageService to create package and all related data
        package = self.package_service.create_package_with_all_data(
            session_id=session_id,
            package_type=package_type,
            blueprint_result=blueprint
        )
        
        self.logger.info(
            f"Migrated {package_type} package: {package.total_objects} objects"
        )
        
        return package
    
    def _migrate_changes(
        self,
        session_id: int,
        ordered_changes: List[Dict[str, Any]],
        classification_results: Dict[str, List[Dict]]
    ):
        """
        Migrate comparison results to Change records
        
        Args:
            session_id: Session ID
            ordered_changes: List of ordered changes
            classification_results: Classification results by category
        """
        if not ordered_changes:
            self.logger.warning(f"No ordered changes for session {session_id}")
            return
        
        # Use ChangeService to create changes
        self.change_service.create_changes_from_comparison(
            session_id=session_id,
            classification_results=classification_results,
            ordered_changes=ordered_changes
        )
        
        self.logger.info(f"Migrated {len(ordered_changes)} changes")
    
    def _update_change_reviews(self, session_id: int):
        """
        Update existing ChangeReview records to link to Change records
        
        Args:
            session_id: Session ID
        """
        # Get all reviews for this session
        reviews = ChangeReview.query.filter_by(session_id=session_id).all()
        
        for review in reviews:
            # Find corresponding Change record by object_uuid
            change = Change.query.filter_by(
                session_id=session_id,
                object_uuid=review.object_uuid
            ).first()
            
            if change:
                review.change_id = change.id
            else:
                self.logger.warning(
                    f"No Change found for review {review.id} "
                    f"(object_uuid={review.object_uuid})"
                )
        
        db.session.flush()
        self.logger.info(f"Updated {len(reviews)} change reviews")
    
    def _verify_foreign_keys(self, session_id: int) -> bool:
        """
        Verify all foreign keys are valid
        
        Args:
            session_id: Session ID
            
        Returns:
            True if all foreign keys valid
        """
        try:
            # Check Change foreign keys
            changes = Change.query.filter_by(session_id=session_id).all()
            for change in changes:
                # At least one object reference should exist
                if change.base_object_id:
                    obj = AppianObject.query.get(change.base_object_id)
                    if not obj:
                        self.logger.error(
                            f"Invalid base_object_id {change.base_object_id} "
                            f"for change {change.id}"
                        )
                        return False
                
                if change.customer_object_id:
                    obj = AppianObject.query.get(change.customer_object_id)
                    if not obj:
                        self.logger.error(
                            f"Invalid customer_object_id {change.customer_object_id} "
                            f"for change {change.id}"
                        )
                        return False
                
                if change.vendor_object_id:
                    obj = AppianObject.query.get(change.vendor_object_id)
                    if not obj:
                        self.logger.error(
                            f"Invalid vendor_object_id {change.vendor_object_id} "
                            f"for change {change.id}"
                        )
                        return False
            
            # Check ChangeReview foreign keys
            reviews = ChangeReview.query.filter_by(session_id=session_id).all()
            for review in reviews:
                if review.change_id:
                    change = Change.query.get(review.change_id)
                    if not change:
                        self.logger.error(
                            f"Invalid change_id {review.change_id} "
                            f"for review {review.id}"
                        )
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying foreign keys: {str(e)}", exc_info=True)
            return False
    
    def _clear_json_columns(self, session: MergeSession):
        """
        Clear old JSON columns after successful migration
        
        Args:
            session: MergeSession to clear
        """
        session.base_blueprint = None
        session.customized_blueprint = None
        session.new_vendor_blueprint = None
        session.vendor_changes = None
        session.customer_changes = None
        session.classification_results = None
        session.ordered_changes = None
        
        db.session.flush()
        self.logger.info(f"Cleared JSON columns for session {session.id}")
    
    def migrate_all_sessions(self, skip_errors: bool = True) -> Dict[str, Any]:
        """
        Migrate all sessions in the database
        
        Args:
            skip_errors: If True, continue on errors; if False, stop on first error
            
        Returns:
            Dictionary with migration statistics
        """
        self.logger.info("Starting migration of all sessions")
        
        stats = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        # Get all sessions
        sessions = MergeSession.query.all()
        stats['total'] = len(sessions)
        
        for session in sessions:
            try:
                # Check if already migrated
                if session.packages:
                    self.logger.info(f"Session {session.id} already migrated, skipping")
                    stats['skipped'] += 1
                    continue
                
                # Migrate session
                success = self.migrate_session(session.id)
                if success:
                    stats['successful'] += 1
                else:
                    stats['failed'] += 1
                    
            except Exception as e:
                stats['failed'] += 1
                error_msg = f"Session {session.id}: {str(e)}"
                stats['errors'].append(error_msg)
                self.logger.error(f"Failed to migrate session {session.id}: {str(e)}")
                
                if not skip_errors:
                    raise
        
        self.logger.info(f"Migration complete: {stats}")
        return stats
