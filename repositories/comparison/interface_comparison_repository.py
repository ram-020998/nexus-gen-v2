"""
Interface Comparison Repository

Provides data access for Interface comparison results.
Stores detailed differences including SAIL code diffs, parameter changes,
and security changes.
"""

import json
from typing import Optional, Dict, Any, List
from models import InterfaceComparison
from repositories.base_repository import BaseRepository


class InterfaceComparisonRepository(BaseRepository[InterfaceComparison]):
    """
    Repository for InterfaceComparison entities.

    Manages comparison results for Interface objects, storing detailed
    differences between versions including SAIL code, parameters, and
    security settings.

    Key Methods:
        - create_comparison: Create comparison with all difference data
        - get_by_change_id: Get comparison by change ID
        - update_comparison: Update existing comparison
    """

    def __init__(self):
        """Initialize repository with InterfaceComparison model."""
        super().__init__(InterfaceComparison)

    def create_comparison(
        self,
        change_id: int,
        sail_code_diff: Optional[str] = None,
        parameters_added: Optional[List[Dict[str, Any]]] = None,
        parameters_removed: Optional[List[Dict[str, Any]]] = None,
        parameters_modified: Optional[List[Dict[str, Any]]] = None,
        security_changes: Optional[List[Dict[str, Any]]] = None
    ) -> InterfaceComparison:
        """
        Create interface comparison with difference data.

        Args:
            change_id: Reference to changes table
            sail_code_diff: SAIL code differences (text diff)
            parameters_added: List of added parameters
            parameters_removed: List of removed parameters
            parameters_modified: List of modified parameters
            security_changes: List of security setting changes

        Returns:
            Created InterfaceComparison object

        Example:
            >>> comparison = repo.create_comparison(
            ...     change_id=42,
            ...     sail_code_diff="- old code\\n+ new code",
            ...     parameters_added=[
            ...         {
            ...             "parameter_name": "newParam",
            ...             "parameter_type": "Text",
            ...             "is_required": True
            ...         }
            ...     ],
            ...     parameters_modified=[
            ...         {
            ...             "parameter_name": "existingParam",
            ...             "old_type": "Text",
            ...             "new_type": "Number",
            ...             "old_required": False,
            ...             "new_required": True
            ...         }
            ...     ]
            ... )
        """
        comparison = InterfaceComparison(
            change_id=change_id,
            sail_code_diff=sail_code_diff,
            parameters_added=json.dumps(parameters_added)
            if parameters_added else None,
            parameters_removed=json.dumps(parameters_removed)
            if parameters_removed else None,
            parameters_modified=json.dumps(parameters_modified)
            if parameters_modified else None,
            security_changes=json.dumps(security_changes)
            if security_changes else None
        )

        self.db.session.add(comparison)
        self.db.session.flush()
        return comparison

    def get_by_change_id(
        self,
        change_id: int
    ) -> Optional[InterfaceComparison]:
        """
        Get interface comparison by change ID.

        Args:
            change_id: Change ID

        Returns:
            InterfaceComparison or None if not found
        """
        return self.find_one(change_id=change_id)

    def update_comparison(
        self,
        change_id: int,
        sail_code_diff: Optional[str] = None,
        parameters_added: Optional[List[Dict[str, Any]]] = None,
        parameters_removed: Optional[List[Dict[str, Any]]] = None,
        parameters_modified: Optional[List[Dict[str, Any]]] = None,
        security_changes: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[InterfaceComparison]:
        """
        Update existing interface comparison.

        Args:
            change_id: Change ID
            sail_code_diff: SAIL code differences
            parameters_added: List of added parameters
            parameters_removed: List of removed parameters
            parameters_modified: List of modified parameters
            security_changes: List of security setting changes

        Returns:
            Updated InterfaceComparison or None if not found
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison:
            return None

        if sail_code_diff is not None:
            comparison.sail_code_diff = sail_code_diff
        if parameters_added is not None:
            comparison.parameters_added = json.dumps(parameters_added)
        if parameters_removed is not None:
            comparison.parameters_removed = json.dumps(parameters_removed)
        if parameters_modified is not None:
            comparison.parameters_modified = json.dumps(parameters_modified)
        if security_changes is not None:
            comparison.security_changes = json.dumps(security_changes)

        self.db.session.flush()
        return comparison

    def get_parameters_added(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get added parameters for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of added parameters or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.parameters_added:
            return None
        return json.loads(comparison.parameters_added)

    def get_parameters_removed(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get removed parameters for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of removed parameters or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.parameters_removed:
            return None
        return json.loads(comparison.parameters_removed)

    def get_parameters_modified(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get modified parameters for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of modified parameters or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.parameters_modified:
            return None
        return json.loads(comparison.parameters_modified)

    def get_security_changes(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get security changes for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of security changes or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.security_changes:
            return None
        return json.loads(comparison.security_changes)
