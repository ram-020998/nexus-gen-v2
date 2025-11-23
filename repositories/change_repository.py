"""
Change repository for managing Change model data access.

This module provides data access methods for the Change model,
which stores individual change records from three-way comparisons.
"""

from typing import List, Optional
from core.base_repository import BaseRepository
from models import Change


class ChangeRepository(BaseRepository[Change]):
    """
    Repository for Change model operations.

    Provides data access methods for managing changes identified during
    three-way merge comparisons, including classification, filtering,
    and ordering.

    Example:
        >>> repo = ChangeRepository()
        >>> change = repo.create(
        ...     session_id=1,
        ...     object_uuid='_a-0001ed6e-54f1-8000-9df6-011c48011c48',
        ...     object_name='MyInterface',
        ...     object_type='Interface',
        ...     classification='CONFLICT',
        ...     display_order=0
        ... )
        >>> conflicts = repo.get_by_classification(1, 'CONFLICT')
    """

    def __init__(self):
        """Initialize ChangeRepository with Change model."""
        super().__init__(Change)

    def get_by_session_id(self, session_id: int) -> List[Change]:
        """
        Get all changes for a specific session.

        Args:
            session_id: ID of the merge session

        Returns:
            List[Change]: List of changes ordered by display_order

        Example:
            >>> changes = repo.get_by_session_id(session_id=1)
        """
        return (self.model_class.query
                .filter_by(session_id=session_id)
                .order_by(self.model_class.display_order.asc())
                .all())

    def get_by_classification(
        self,
        session_id: int,
        classification: str
    ) -> List[Change]:
        """
        Get changes by classification type.

        Args:
            session_id: ID of the merge session
            classification: Classification type ('NO_CONFLICT', 'CONFLICT',
                'CUSTOMER_ONLY', 'REMOVED_BUT_CUSTOMIZED')

        Returns:
            List[Change]: List of changes with the specified classification

        Example:
            >>> conflicts = repo.get_by_classification(1, 'CONFLICT')
            >>> no_conflicts = repo.get_by_classification(1, 'NO_CONFLICT')
        """
        return (self.model_class.query
                .filter_by(
                    session_id=session_id,
                    classification=classification
                )
                .order_by(self.model_class.display_order.asc())
                .all())

    def get_by_object_type(
        self,
        session_id: int,
        object_type: str
    ) -> List[Change]:
        """
        Get changes by object type.

        Args:
            session_id: ID of the merge session
            object_type: Type of object (e.g., 'Interface', 'Process Model')

        Returns:
            List[Change]: List of changes for the specified object type

        Example:
            >>> interfaces = repo.get_by_object_type(1, 'Interface')
        """
        return (self.model_class.query
                .filter_by(session_id=session_id, object_type=object_type)
                .order_by(self.model_class.display_order.asc())
                .all())

    def get_by_uuid(
        self,
        session_id: int,
        object_uuid: str
    ) -> Optional[Change]:
        """
        Get a change by object UUID.

        Args:
            session_id: ID of the merge session
            object_uuid: UUID of the object

        Returns:
            Optional[Change]: Change if found, None otherwise

        Example:
            >>> change = repo.get_by_uuid(
            ...     1,
            ...     '_a-0001ed6e-54f1-8000-9df6-011c48011c48'
            ... )
        """
        return self.find_one(session_id=session_id, object_uuid=object_uuid)

    def get_conflicts(self, session_id: int) -> List[Change]:
        """
        Get all conflicting changes for a session.

        Args:
            session_id: ID of the merge session

        Returns:
            List[Change]: List of changes with CONFLICT classification

        Example:
            >>> conflicts = repo.get_conflicts(session_id=1)
        """
        return self.get_by_classification(session_id, 'CONFLICT')

    def get_no_conflicts(self, session_id: int) -> List[Change]:
        """
        Get all non-conflicting changes for a session.

        Args:
            session_id: ID of the merge session

        Returns:
            List[Change]: List of changes with NO_CONFLICT classification

        Example:
            >>> no_conflicts = repo.get_no_conflicts(session_id=1)
        """
        return self.get_by_classification(session_id, 'NO_CONFLICT')

    def get_customer_only_changes(self, session_id: int) -> List[Change]:
        """
        Get all customer-only changes for a session.

        Args:
            session_id: ID of the merge session

        Returns:
            List[Change]: List of changes with CUSTOMER_ONLY classification

        Example:
            >>> customer_only = repo.get_customer_only_changes(session_id=1)
        """
        return self.get_by_classification(session_id, 'CUSTOMER_ONLY')

    def get_removed_but_customized(self, session_id: int) -> List[Change]:
        """
        Get all removed but customized changes for a session.

        Args:
            session_id: ID of the merge session

        Returns:
            List[Change]: List of changes with REMOVED_BUT_CUSTOMIZED
                classification

        Example:
            >>> removed = repo.get_removed_but_customized(session_id=1)
        """
        return self.get_by_classification(session_id, 'REMOVED_BUT_CUSTOMIZED')

    def count_by_classification(
        self,
        session_id: int,
        classification: str
    ) -> int:
        """
        Count changes by classification.

        Args:
            session_id: ID of the merge session
            classification: Classification type to count

        Returns:
            int: Number of changes with the specified classification

        Example:
            >>> conflict_count = repo.count_by_classification(1, 'CONFLICT')
        """
        return self.count(session_id=session_id, classification=classification)

    def count_by_object_type(
        self,
        session_id: int,
        object_type: str
    ) -> int:
        """
        Count changes by object type.

        Args:
            session_id: ID of the merge session
            object_type: Type of object to count

        Returns:
            int: Number of changes for the specified object type

        Example:
            >>> interface_count = repo.count_by_object_type(1, 'Interface')
        """
        return self.count(session_id=session_id, object_type=object_type)

    def get_classification_summary(
        self,
        session_id: int
    ) -> dict[str, int]:
        """
        Get summary of changes by classification.

        Args:
            session_id: ID of the merge session

        Returns:
            dict: Dictionary mapping classification to count

        Example:
            >>> summary = repo.get_classification_summary(session_id=1)
            >>> # Returns: {'CONFLICT': 10, 'NO_CONFLICT': 50, ...}
        """
        classifications = [
            'NO_CONFLICT',
            'CONFLICT',
            'CUSTOMER_ONLY',
            'REMOVED_BUT_CUSTOMIZED'
        ]
        return {
            cls: self.count_by_classification(session_id, cls)
            for cls in classifications
        }

    def get_object_type_summary(
        self,
        session_id: int
    ) -> dict[str, int]:
        """
        Get summary of changes by object type.

        Args:
            session_id: ID of the merge session

        Returns:
            dict: Dictionary mapping object type to count

        Example:
            >>> summary = repo.get_object_type_summary(session_id=1)
            >>> # Returns: {'Interface': 25, 'Process Model': 10, ...}
        """
        changes = self.get_by_session_id(session_id)
        summary: dict[str, int] = {}
        for change in changes:
            obj_type = change.object_type
            summary[obj_type] = summary.get(obj_type, 0) + 1
        return summary

    def get_by_display_order_range(
        self,
        session_id: int,
        start_order: int,
        end_order: int
    ) -> List[Change]:
        """
        Get changes within a display order range.

        Args:
            session_id: ID of the merge session
            start_order: Starting display order (inclusive)
            end_order: Ending display order (inclusive)

        Returns:
            List[Change]: List of changes in the specified range

        Example:
            >>> changes = repo.get_by_display_order_range(1, 0, 9)
        """
        return (self.model_class.query
                .filter_by(session_id=session_id)
                .filter(self.model_class.display_order >= start_order)
                .filter(self.model_class.display_order <= end_order)
                .order_by(self.model_class.display_order.asc())
                .all())

    def get_paginated(
        self,
        session_id: int,
        page: int = 1,
        per_page: int = 10
    ) -> tuple[List[Change], int]:
        """
        Get paginated changes for a session.

        Args:
            session_id: ID of the merge session
            page: Page number (1-indexed)
            per_page: Number of changes per page

        Returns:
            tuple: (list of changes, total count)

        Example:
            >>> changes, total = repo.get_paginated(1, page=2, per_page=10)
        """
        query = (self.model_class.query
                 .filter_by(session_id=session_id)
                 .order_by(self.model_class.display_order.asc()))

        total = query.count()
        changes = query.offset((page - 1) * per_page).limit(per_page).all()

        return (changes, total)

    def delete_by_session(self, session_id: int) -> int:
        """
        Delete all changes for a session.

        Args:
            session_id: ID of the merge session

        Returns:
            int: Number of changes deleted

        Example:
            >>> deleted = repo.delete_by_session(session_id=1)
        """
        changes = self.get_by_session_id(session_id)
        count = len(changes)
        for change in changes:
            self.db.session.delete(change)
        self.db.session.commit()
        return count

    def get_changes_with_guidance(
        self,
        session_id: int
    ) -> List[Change]:
        """
        Get all changes that have merge guidance.

        Args:
            session_id: ID of the merge session

        Returns:
            List[Change]: List of changes with merge guidance

        Example:
            >>> guided = repo.get_changes_with_guidance(session_id=1)
        """
        return (self.model_class.query
                .filter_by(session_id=session_id)
                .filter(self.model_class.merge_guidance.isnot(None))
                .order_by(self.model_class.display_order.asc())
                .all())

    def get_changes_with_reviews(
        self,
        session_id: int
    ) -> List[Change]:
        """
        Get all changes that have been reviewed.

        Args:
            session_id: ID of the merge session

        Returns:
            List[Change]: List of changes with reviews

        Example:
            >>> reviewed = repo.get_changes_with_reviews(session_id=1)
        """
        return (self.model_class.query
                .filter_by(session_id=session_id)
                .filter(self.model_class.review.isnot(None))
                .order_by(self.model_class.display_order.asc())
                .all())
