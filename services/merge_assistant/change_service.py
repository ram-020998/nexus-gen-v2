"""
Change Service for normalizing comparison data into database tables.

This service handles the extraction and normalization of comparison results,
classification data, and merge guidance into the Change, MergeGuidance,
MergeConflict, MergeChange, and ChangeReview tables.
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from models import (
    db, Change, MergeGuidance, MergeConflict, MergeChange,
    ChangeReview, AppianObject, Package
)

logger = logging.getLogger(__name__)


class ChangeService:
    """Service for managing Change and related records."""

    def __init__(self):
        """Initialize the ChangeService."""
        pass

    def create_changes_from_comparison(
        self,
        session_id: int,
        classification_results: Dict[str, List[Dict]],
        ordered_changes: List[Dict[str, Any]]
    ) -> List[Change]:
        """
        Create Change records from comparison results.

        This method orchestrates the complete normalization of comparison data:
        1. Iterate through ordered_changes
        2. Look up object IDs from AppianObject table
        3. Create Change records with proper foreign keys
        4. Set display_order for maintaining order
        5. Create MergeGuidance records
        6. Create ChangeReview records

        Args:
            session_id: ID of the merge session
            classification_results: Dictionary of classified changes by category
            ordered_changes: List of changes in smart order

        Returns:
            List of created Change records

        Raises:
            ValueError: If data structure is invalid
            Exception: If database operation fails
        """
        try:
            logger.info(
                f"Creating changes for session {session_id}, "
                f"total changes: {len(ordered_changes)}"
            )

            changes = []
            
            # Process each change in order
            for index, change_data in enumerate(ordered_changes):
                # Create the Change record
                change = self._create_change_record(
                    session_id,
                    change_data,
                    index
                )
                
                if change:
                    changes.append(change)
                    
                    # Create merge guidance if present
                    if 'merge_guidance' in change_data:
                        self._create_merge_guidance(
                            change,
                            change_data['merge_guidance']
                        )
                    
                    # Create change review record
                    self._create_change_review(change)

            # Commit all changes
            db.session.commit()

            logger.info(
                f"Successfully created {len(changes)} Change records "
                f"for session {session_id}"
            )

            return changes

        except Exception as e:
            # Rollback on any error
            db.session.rollback()
            logger.error(
                f"Error creating changes from comparison: {str(e)}",
                exc_info=True
            )
            raise

    def _create_change_record(
        self,
        session_id: int,
        change_data: Dict[str, Any],
        display_order: int
    ) -> Optional[Change]:
        """
        Create a single Change record with foreign keys to objects.

        Args:
            session_id: ID of the merge session
            change_data: Dictionary containing change information
            display_order: Order index for this change

        Returns:
            Created Change record or None if object lookup fails

        Raises:
            Exception: If change creation fails
        """
        try:
            # Extract basic change information
            object_uuid = change_data.get('uuid', '')
            object_name = change_data.get('name', '')
            object_type = change_data.get('type', '')
            classification = change_data.get('classification', '')
            change_type = change_data.get('change_type')
            
            # Extract vendor and customer change types
            vendor_change_type = change_data.get('vendor_change_type')
            customer_change_type = change_data.get('customer_change_type')

            # Look up object IDs from AppianObject table
            base_object_id = self._get_object_id(
                session_id,
                'base',
                object_uuid
            )
            customer_object_id = self._get_object_id(
                session_id,
                'customized',
                object_uuid
            )
            vendor_object_id = self._get_object_id(
                session_id,
                'new_vendor',
                object_uuid
            )

            # Create Change record
            change = Change(
                session_id=session_id,
                object_uuid=object_uuid,
                object_name=object_name,
                object_type=object_type,
                classification=classification,
                change_type=change_type,
                vendor_change_type=vendor_change_type,
                customer_change_type=customer_change_type,
                base_object_id=base_object_id,
                customer_object_id=customer_object_id,
                vendor_object_id=vendor_object_id,
                display_order=display_order
            )

            db.session.add(change)
            db.session.flush()  # Get change ID

            logger.debug(
                f"Created Change {change.id} for object {object_name} "
                f"(classification: {classification})"
            )

            return change

        except Exception as e:
            logger.error(
                f"Error creating change record: {str(e)}",
                exc_info=True
            )
            raise

    def _get_object_id(
        self,
        session_id: int,
        package_type: str,
        object_uuid: str
    ) -> Optional[int]:
        """
        Look up AppianObject ID by package type and UUID.

        Args:
            session_id: ID of the merge session
            package_type: Type of package ('base', 'customized', 'new_vendor')
            object_uuid: UUID of the object

        Returns:
            AppianObject ID or None if not found
        """
        try:
            # Get package ID for this session and type
            package = Package.query.filter_by(
                session_id=session_id,
                package_type=package_type
            ).first()

            if not package:
                logger.warning(
                    f"Package not found for session {session_id}, "
                    f"type {package_type}"
                )
                return None

            # Get object ID
            appian_obj = AppianObject.query.filter_by(
                package_id=package.id,
                uuid=object_uuid
            ).first()

            if appian_obj:
                return appian_obj.id
            else:
                logger.debug(
                    f"Object {object_uuid} not found in package {package.id}"
                )
                return None

        except Exception as e:
            logger.error(
                f"Error looking up object ID: {str(e)}",
                exc_info=True
            )
            return None

    def _create_merge_guidance(
        self,
        change: Change,
        guidance_data: Dict[str, Any]
    ) -> MergeGuidance:
        """
        Create MergeGuidance and related records for a change.

        Args:
            change: Change record to associate guidance with
            guidance_data: Dictionary containing guidance information

        Returns:
            Created MergeGuidance record

        Raises:
            Exception: If guidance creation fails
        """
        try:
            # Extract guidance information
            recommendation = guidance_data.get('recommendation', '')
            reason = guidance_data.get('reason', '')

            # Create MergeGuidance record
            guidance = MergeGuidance(
                change_id=change.id,
                recommendation=recommendation,
                reason=reason
            )

            db.session.add(guidance)
            db.session.flush()  # Get guidance ID

            # Create MergeConflict records if present
            conflicts = guidance_data.get('conflicts', [])
            for conflict_data in conflicts:
                self._create_merge_conflict(guidance, conflict_data)

            # Create MergeChange records if present
            changes = guidance_data.get('changes', [])
            for change_data in changes:
                self._create_merge_change(guidance, change_data)

            logger.debug(
                f"Created MergeGuidance {guidance.id} for change {change.id} "
                f"with {len(conflicts)} conflicts and {len(changes)} changes"
            )

            return guidance

        except Exception as e:
            logger.error(
                f"Error creating merge guidance: {str(e)}",
                exc_info=True
            )
            raise

    def _create_merge_conflict(
        self,
        guidance: MergeGuidance,
        conflict_data: Dict[str, Any]
    ) -> MergeConflict:
        """
        Create a MergeConflict record.

        Args:
            guidance: MergeGuidance record to associate conflict with
            conflict_data: Dictionary containing conflict information

        Returns:
            Created MergeConflict record

        Raises:
            Exception: If conflict creation fails
        """
        try:
            conflict = MergeConflict(
                guidance_id=guidance.id,
                field_name=conflict_data.get('field_name'),
                conflict_type=conflict_data.get('conflict_type'),
                description=conflict_data.get('description')
            )

            db.session.add(conflict)
            db.session.flush()

            return conflict

        except Exception as e:
            logger.error(
                f"Error creating merge conflict: {str(e)}",
                exc_info=True
            )
            raise

    def _create_merge_change(
        self,
        guidance: MergeGuidance,
        change_data: Dict[str, Any]
    ) -> MergeChange:
        """
        Create a MergeChange record.

        Args:
            guidance: MergeGuidance record to associate change with
            change_data: Dictionary containing change information

        Returns:
            Created MergeChange record

        Raises:
            Exception: If change creation fails
        """
        try:
            merge_change = MergeChange(
                guidance_id=guidance.id,
                field_name=change_data.get('field_name'),
                change_description=change_data.get('description'),
                old_value=change_data.get('old_value'),
                new_value=change_data.get('new_value')
            )

            db.session.add(merge_change)
            db.session.flush()

            return merge_change

        except Exception as e:
            logger.error(
                f"Error creating merge change: {str(e)}",
                exc_info=True
            )
            raise

    def _create_change_review(
        self,
        change: Change
    ) -> ChangeReview:
        """
        Create a ChangeReview record linked to Change.

        Args:
            change: Change record to create review for

        Returns:
            Created ChangeReview record

        Raises:
            Exception: If review creation fails
        """
        try:
            review = ChangeReview(
                session_id=change.session_id,
                change_id=change.id,
                review_status='pending'
            )

            db.session.add(review)
            db.session.flush()

            logger.debug(
                f"Created ChangeReview {review.id} for change {change.id}"
            )

            return review

        except Exception as e:
            logger.error(
                f"Error creating change review: {str(e)}",
                exc_info=True
            )
            raise

    def get_change_with_objects(
        self,
        change_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get change with all related objects using JOIN.

        Returns complete change information without JSON parsing.

        Args:
            change_id: ID of the change

        Returns:
            Dictionary with complete change information or None if not found
        """
        try:
            from sqlalchemy.orm import joinedload

            # Query with eager loading
            change = db.session.query(Change)\
                .options(
                    joinedload(Change.base_object),
                    joinedload(Change.customer_object),
                    joinedload(Change.vendor_object),
                    joinedload(Change.merge_guidance),
                    joinedload(Change.review)
                )\
                .filter(Change.id == change_id)\
                .first()

            if not change:
                return None

            # Build result dictionary
            result = change.to_dict()
            
            # Add related objects
            if change.base_object:
                result['base_object'] = change.base_object.to_dict()
            if change.customer_object:
                result['customer_object'] = change.customer_object.to_dict()
            if change.vendor_object:
                result['vendor_object'] = change.vendor_object.to_dict()
            if change.merge_guidance:
                result['merge_guidance'] = change.merge_guidance.to_dict()
            if change.review:
                result['review'] = change.review.to_dict()

            return result

        except Exception as e:
            logger.error(
                f"Error getting change with objects: {str(e)}",
                exc_info=True
            )
            return None
