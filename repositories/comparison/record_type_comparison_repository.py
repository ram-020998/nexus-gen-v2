"""
Record Type Comparison Repository

Provides data access for Record Type comparison results.
Stores detailed differences including fields, relationships, views,
and actions.
"""

import json
from typing import Optional, Dict, Any, List
from models import RecordTypeComparison
from repositories.base_repository import BaseRepository


class RecordTypeComparisonRepository(
    BaseRepository[RecordTypeComparison]
):
    """
    Repository for RecordTypeComparison entities.

    Manages comparison results for Record Type objects, storing detailed
    differences between versions including fields, relationships, views,
    and actions.

    Key Methods:
        - create_comparison: Create comparison with all difference data
        - get_by_change_id: Get comparison by change ID
        - update_comparison: Update existing comparison
    """

    def __init__(self):
        """Initialize repository with RecordTypeComparison model."""
        super().__init__(RecordTypeComparison)

    def create_comparison(
        self,
        change_id: int,
        fields_changed: Optional[List[Dict[str, Any]]] = None,
        relationships_changed: Optional[List[Dict[str, Any]]] = None,
        views_changed: Optional[List[Dict[str, Any]]] = None,
        actions_changed: Optional[List[Dict[str, Any]]] = None
    ) -> RecordTypeComparison:
        """
        Create record type comparison with difference data.

        Args:
            change_id: Reference to changes table
            fields_changed: List of field changes (added/removed/modified)
            relationships_changed: List of relationship changes
            views_changed: List of view changes
            actions_changed: List of action changes

        Returns:
            Created RecordTypeComparison object

        Example:
            >>> comparison = repo.create_comparison(
            ...     change_id=42,
            ...     fields_changed=[
            ...         {
            ...             "change_type": "ADDED",
            ...             "field_name": "newField",
            ...             "field_type": "Text",
            ...             "is_required": True
            ...         },
            ...         {
            ...             "change_type": "MODIFIED",
            ...             "field_name": "existingField",
            ...             "old_type": "Text",
            ...             "new_type": "Number"
            ...         }
            ...     ],
            ...     relationships_changed=[
            ...         {
            ...             "change_type": "ADDED",
            ...             "relationship_name": "relatedRecords",
            ...             "relationship_type": "ONE_TO_MANY",
            ...             "target_record_type": "OtherRecord"
            ...         }
            ...     ]
            ... )
        """
        comparison = RecordTypeComparison(
            change_id=change_id,
            fields_changed=json.dumps(fields_changed)
            if fields_changed else None,
            relationships_changed=json.dumps(relationships_changed)
            if relationships_changed else None,
            views_changed=json.dumps(views_changed)
            if views_changed else None,
            actions_changed=json.dumps(actions_changed)
            if actions_changed else None
        )

        self.db.session.add(comparison)
        self.db.session.flush()
        return comparison

    def get_by_change_id(
        self,
        change_id: int
    ) -> Optional[RecordTypeComparison]:
        """
        Get record type comparison by change ID.

        Args:
            change_id: Change ID

        Returns:
            RecordTypeComparison or None if not found
        """
        return self.find_one(change_id=change_id)

    def update_comparison(
        self,
        change_id: int,
        fields_changed: Optional[List[Dict[str, Any]]] = None,
        relationships_changed: Optional[List[Dict[str, Any]]] = None,
        views_changed: Optional[List[Dict[str, Any]]] = None,
        actions_changed: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[RecordTypeComparison]:
        """
        Update existing record type comparison.

        Args:
            change_id: Change ID
            fields_changed: List of field changes
            relationships_changed: List of relationship changes
            views_changed: List of view changes
            actions_changed: List of action changes

        Returns:
            Updated RecordTypeComparison or None if not found
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison:
            return None

        if fields_changed is not None:
            comparison.fields_changed = json.dumps(fields_changed)
        if relationships_changed is not None:
            comparison.relationships_changed = (
                json.dumps(relationships_changed)
            )
        if views_changed is not None:
            comparison.views_changed = json.dumps(views_changed)
        if actions_changed is not None:
            comparison.actions_changed = json.dumps(actions_changed)

        self.db.session.flush()
        return comparison

    def get_fields_changed(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get field changes for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of field changes or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.fields_changed:
            return None
        return json.loads(comparison.fields_changed)

    def get_relationships_changed(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get relationship changes for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of relationship changes or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.relationships_changed:
            return None
        return json.loads(comparison.relationships_changed)

    def get_views_changed(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get view changes for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of view changes or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.views_changed:
            return None
        return json.loads(comparison.views_changed)

    def get_actions_changed(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get action changes for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of action changes or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.actions_changed:
            return None
        return json.loads(comparison.actions_changed)
