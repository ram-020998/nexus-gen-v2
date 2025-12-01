"""
Change Navigation Service

Provides navigation functionality for changes in a merge session.
Handles sequential navigation, position tracking, and change details.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import joinedload

from core.base_service import BaseService
from models import (
    db, MergeSession, Change, Package, ObjectVersion
)
from repositories.change_repository import ChangeRepository


class ChangeNavigationService(BaseService):
    """
    Service for navigating through changes in a merge session.
    
    Provides methods for:
    - Getting detailed change information
    - Sequential navigation (next/previous)
    - Position tracking (e.g., "Change 1 of 6")
    - Progress calculation
    - Object version retrieval from all three packages
    
    Example:
        >>> service = ChangeNavigationService()
        >>> detail = service.get_change_detail("MS_A1B2C3", 42)
        >>> print(f"Change {detail['position']} - {detail['object']['name']}")
        >>> print(f"Progress: {detail['progress_percent']}%")
    """
    
    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.change_repository = self._get_repository(ChangeRepository)
    
    def get_change_detail(
        self,
        reference_id: str,
        change_id: int
    ) -> Dict[str, Any]:
        """
        Get detailed information for a specific change.
        
        Returns comprehensive information including:
        - Change details (classification, change types, status, notes)
        - Object details (name, type, UUID, description)
        - Session information (reference_id, status, counts)
        - Navigation (previous/next change IDs)
        - Position (e.g., "1 of 6")
        - Progress percentage
        - Object versions from all three packages
        
        Args:
            reference_id: Session reference ID (e.g., MS_A1B2C3)
            change_id: Change ID
            
        Returns:
            Dict containing all change detail information
            
        Raises:
            ValueError: If session or change not found
            
        Example:
            >>> detail = service.get_change_detail("MS_A1B2C3", 42)
            >>> print(f"Object: {detail['object']['name']}")
            >>> print(f"Classification: {detail['change']['classification']}")
            >>> print(f"Position: {detail['position']}")
            >>> print(f"Progress: {detail['progress_percent']}%")
        """
        # Find session
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()
        
        if not session:
            raise ValueError(f"Session not found: {reference_id}")
        
        # Find change with eager loading
        change = db.session.query(Change).options(
            joinedload(Change.object)
        ).filter_by(
            id=change_id,
            session_id=session.id
        ).first()
        
        if not change:
            raise ValueError(
                f"Change {change_id} not found in session {reference_id}"
            )
        
        # Get navigation
        next_change_id = self.get_next_change(reference_id, change_id)
        previous_change_id = self.get_previous_change(reference_id, change_id)
        
        # Get position
        current_position, total_changes = self.get_change_position(
            reference_id,
            change_id
        )
        
        # Calculate progress percentage
        progress_percent = (
            (current_position / total_changes * 100)
            if total_changes > 0
            else 0
        )
        
        # Get object versions from all three packages
        versions = self.get_object_versions(
            session.id,
            change.object_id
        )
        
        # Build response
        return {
            'change': {
                'id': change.id,
                'classification': change.classification,
                'vendor_change_type': change.vendor_change_type,
                'customer_change_type': change.customer_change_type,
                'display_order': change.display_order,
                'status': change.status,
                'notes': change.notes,
                'reviewed_at': (
                    change.reviewed_at.isoformat()
                    if change.reviewed_at
                    else None
                ),
                'reviewed_by': change.reviewed_by
            },
            'object': {
                'id': change.object.id,
                'uuid': change.object.uuid,
                'name': change.object.name,
                'object_type': change.object.object_type,
                'description': change.object.description
            },
            'session': {
                'id': session.id,
                'reference_id': session.reference_id,
                'status': session.status,
                'total_changes': session.total_changes,
                'reviewed_count': session.reviewed_count,
                'skipped_count': session.skipped_count
            },
            'navigation': {
                'next_change_id': next_change_id,
                'previous_change_id': previous_change_id,
                'has_next': next_change_id is not None,
                'has_previous': previous_change_id is not None
            },
            'position': f"{current_position} of {total_changes}",
            'current_position': current_position,
            'total_changes': total_changes,
            'progress_percent': round(progress_percent, 2),
            'versions': versions
        }
    
    def get_next_change(
        self,
        reference_id: str,
        current_change_id: int
    ) -> Optional[int]:
        """
        Get ID of next change in sequence.
        
        Returns the change with the next higher display_order.
        Returns None if current change is the last one.
        
        Args:
            reference_id: Session reference ID
            current_change_id: Current change ID
            
        Returns:
            Next change ID or None if at end
            
        Example:
            >>> next_id = service.get_next_change("MS_A1B2C3", 42)
            >>> if next_id:
            ...     print(f"Next change: {next_id}")
            ... else:
            ...     print("This is the last change")
        """
        # Find session
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()
        
        if not session:
            raise ValueError(f"Session not found: {reference_id}")
        
        # Find current change
        current_change = db.session.query(Change).filter_by(
            id=current_change_id,
            session_id=session.id
        ).first()
        
        if not current_change:
            raise ValueError(
                f"Change {current_change_id} not found in "
                f"session {reference_id}"
            )
        
        # Find next change by display_order
        next_change = db.session.query(Change).filter(
            Change.session_id == session.id,
            Change.display_order > current_change.display_order
        ).order_by(
            Change.display_order
        ).first()
        
        return next_change.id if next_change else None
    
    def get_previous_change(
        self,
        reference_id: str,
        current_change_id: int
    ) -> Optional[int]:
        """
        Get ID of previous change in sequence.
        
        Returns the change with the next lower display_order.
        Returns None if current change is the first one.
        
        Args:
            reference_id: Session reference ID
            current_change_id: Current change ID
            
        Returns:
            Previous change ID or None if at beginning
            
        Example:
            >>> prev_id = service.get_previous_change("MS_A1B2C3", 42)
            >>> if prev_id:
            ...     print(f"Previous change: {prev_id}")
            ... else:
            ...     print("This is the first change")
        """
        # Find session
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()
        
        if not session:
            raise ValueError(f"Session not found: {reference_id}")
        
        # Find current change
        current_change = db.session.query(Change).filter_by(
            id=current_change_id,
            session_id=session.id
        ).first()
        
        if not current_change:
            raise ValueError(
                f"Change {current_change_id} not found in "
                f"session {reference_id}"
            )
        
        # Find previous change by display_order
        previous_change = db.session.query(Change).filter(
            Change.session_id == session.id,
            Change.display_order < current_change.display_order
        ).order_by(
            Change.display_order.desc()
        ).first()
        
        return previous_change.id if previous_change else None
    
    def get_change_position(
        self,
        reference_id: str,
        change_id: int
    ) -> Tuple[int, int]:
        """
        Get position of change in workflow.
        
        Returns the 1-based position of the change in the sequence
        and the total number of changes.
        
        Args:
            reference_id: Session reference ID
            change_id: Change ID
            
        Returns:
            Tuple of (current_position, total_changes)
            e.g., (1, 6) means "Change 1 of 6"
            
        Raises:
            ValueError: If session or change not found
            
        Example:
            >>> position, total = service.get_change_position(
            ...     "MS_A1B2C3",
            ...     42
            ... )
            >>> print(f"Change {position} of {total}")
        """
        # Find session
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()
        
        if not session:
            raise ValueError(f"Session not found: {reference_id}")
        
        # Find change
        change = db.session.query(Change).filter_by(
            id=change_id,
            session_id=session.id
        ).first()
        
        if not change:
            raise ValueError(
                f"Change {change_id} not found in session {reference_id}"
            )
        
        # Count changes with lower display_order
        position = db.session.query(Change).filter(
            Change.session_id == session.id,
            Change.display_order <= change.display_order
        ).count()
        
        # Total changes
        total_changes = session.total_changes
        
        return position, total_changes
    
    def get_object_versions(
        self,
        session_id: int,
        object_id: int
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Retrieve object versions from all three packages.
        
        Queries the ObjectVersion table for the given object across
        all three packages (base, customized, new_vendor) and returns
        version data including SAIL code.
        
        Args:
            session_id: Merge session ID
            object_id: Object ID from object_lookup
            
        Returns:
            Dict with keys 'base', 'customized', 'new_vendor'
            Each value is either a dict with version data or None
            if the object doesn't exist in that package
            
        Example:
            >>> versions = service.get_object_versions(1, 42)
            >>> if versions['new_vendor']:
            ...     print(versions['new_vendor']['sail_code'])
        """
        # Get all packages for this session
        packages = db.session.query(Package).filter_by(
            session_id=session_id
        ).all()
        
        # Create package_type to package_id mapping
        package_map = {pkg.package_type: pkg.id for pkg in packages}
        
        # Initialize result
        result = {
            'base': None,
            'customized': None,
            'new_vendor': None
        }
        
        # Query object versions for each package
        for package_type in ['base', 'customized', 'new_vendor']:
            package_id = package_map.get(package_type)
            
            if not package_id:
                continue
            
            version = db.session.query(ObjectVersion).filter_by(
                object_id=object_id,
                package_id=package_id
            ).first()
            
            if version:
                result[package_type] = {
                    'id': version.id,
                    'version_uuid': version.version_uuid,
                    'sail_code': version.sail_code,
                    'fields': version.fields,
                    'properties': version.properties,
                    'raw_xml': version.raw_xml
                }
        
        return result
