"""
Comparison repository for managing ComparisonRequest model data access.

This module provides data access methods for the ComparisonRequest model,
which handles Appian application version comparison operations.
"""

from typing import List, Optional
from datetime import datetime
from core.base_repository import BaseRepository
from models import ComparisonRequest


class ComparisonRepository(BaseRepository[ComparisonRequest]):
    """
    Repository for ComparisonRequest model operations.

    Provides data access methods for managing comparison requests
    between different versions of Appian applications, including
    blueprint storage and comparison results.

    Example:
        >>> repo = ComparisonRepository()
        >>> comparison = repo.create(
        ...     reference_id='CMP_001',
        ...     old_app_name='SourceSelectionv2.4.0',
        ...     new_app_name='SourceSelectionv2.6.0',
        ...     status='processing'
        ... )
        >>> recent = repo.get_recent(limit=5)
    """

    def __init__(self):
        """Initialize ComparisonRepository with ComparisonRequest model."""
        super().__init__(ComparisonRequest)

    def get_by_reference_id(
        self,
        reference_id: str
    ) -> Optional[ComparisonRequest]:
        """
        Get comparison request by reference ID.

        Args:
            reference_id: Reference ID (e.g., 'CMP_001')

        Returns:
            Optional[ComparisonRequest]: Comparison if found, None otherwise

        Example:
            >>> comparison = repo.get_by_reference_id('CMP_001')
        """
        return self.find_one(reference_id=reference_id)

    def get_recent(self, limit: int = 10) -> List[ComparisonRequest]:
        """
        Get most recent comparison requests.

        Args:
            limit: Maximum number of comparisons to return

        Returns:
            List[ComparisonRequest]: List of recent comparisons ordered
                by creation date

        Example:
            >>> recent = repo.get_recent(limit=20)
        """
        return (self.model_class.query
                .order_by(self.model_class.created_at.desc())
                .limit(limit)
                .all())

    def get_by_status(self, status: str) -> List[ComparisonRequest]:
        """
        Get all comparison requests with a specific status.

        Args:
            status: Status to filter by ('processing', 'completed', 'error')

        Returns:
            List[ComparisonRequest]: List of comparisons with the
                specified status

        Example:
            >>> processing = repo.get_by_status('processing')
        """
        return self.filter_by(status=status)

    def update_status(
        self,
        comparison_id: int,
        status: str,
        error_log: Optional[str] = None
    ) -> Optional[ComparisonRequest]:
        """
        Update comparison request status.

        Args:
            comparison_id: ID of the comparison to update
            status: New status ('processing', 'completed', 'error')
            error_log: Optional error log message

        Returns:
            Optional[ComparisonRequest]: Updated comparison if found,
                None otherwise

        Example:
            >>> comparison = repo.update_status(
            ...     comparison_id=1,
            ...     status='completed'
            ... )
        """
        comparison = self.get_by_id(comparison_id)
        if comparison:
            comparison.status = status
            if error_log:
                comparison.error_log = error_log
            comparison.updated_at = datetime.utcnow()
            self.update(comparison)
        return comparison

    def update_blueprints(
        self,
        comparison_id: int,
        old_blueprint: str,
        new_blueprint: str
    ) -> Optional[ComparisonRequest]:
        """
        Update comparison request with blueprint data.

        Args:
            comparison_id: ID of the comparison to update
            old_blueprint: JSON string of old application blueprint
            new_blueprint: JSON string of new application blueprint

        Returns:
            Optional[ComparisonRequest]: Updated comparison if found,
                None otherwise

        Example:
            >>> comparison = repo.update_blueprints(
            ...     comparison_id=1,
            ...     old_blueprint='{"objects": [...]}',
            ...     new_blueprint='{"objects": [...]}'
            ... )
        """
        comparison = self.get_by_id(comparison_id)
        if comparison:
            comparison.old_app_blueprint = old_blueprint
            comparison.new_app_blueprint = new_blueprint
            comparison.updated_at = datetime.utcnow()
            self.update(comparison)
        return comparison

    def update_results(
        self,
        comparison_id: int,
        comparison_results: str,
        total_time: Optional[int] = None
    ) -> Optional[ComparisonRequest]:
        """
        Update comparison request with results.

        Args:
            comparison_id: ID of the comparison to update
            comparison_results: JSON string of comparison results
            total_time: Optional processing time in seconds

        Returns:
            Optional[ComparisonRequest]: Updated comparison if found,
                None otherwise

        Example:
            >>> comparison = repo.update_results(
            ...     comparison_id=1,
            ...     comparison_results='{"changes": [...]}',
            ...     total_time=45
            ... )
        """
        comparison = self.get_by_id(comparison_id)
        if comparison:
            comparison.comparison_results = comparison_results
            if total_time is not None:
                comparison.total_time = total_time
            comparison.updated_at = datetime.utcnow()
            self.update(comparison)
        return comparison

    def get_by_app_names(
        self,
        old_app_name: str,
        new_app_name: str
    ) -> List[ComparisonRequest]:
        """
        Get comparisons by application names.

        Args:
            old_app_name: Name of the old application version
            new_app_name: Name of the new application version

        Returns:
            List[ComparisonRequest]: List of comparisons matching
                the application names

        Example:
            >>> comparisons = repo.get_by_app_names(
            ...     'SourceSelectionv2.4.0',
            ...     'SourceSelectionv2.6.0'
            ... )
        """
        return (self.model_class.query
                .filter_by(
                    old_app_name=old_app_name,
                    new_app_name=new_app_name
                )
                .all())

    def get_completed_comparisons(self) -> List[ComparisonRequest]:
        """
        Get all completed comparison requests.

        Returns:
            List[ComparisonRequest]: List of completed comparisons

        Example:
            >>> completed = repo.get_completed_comparisons()
        """
        return self.get_by_status('completed')

    def get_failed_comparisons(self) -> List[ComparisonRequest]:
        """
        Get all failed comparison requests.

        Returns:
            List[ComparisonRequest]: List of failed comparisons

        Example:
            >>> failed = repo.get_failed_comparisons()
        """
        return self.get_by_status('error')

    def get_processing_comparisons(self) -> List[ComparisonRequest]:
        """
        Get all comparison requests currently being processed.

        Returns:
            List[ComparisonRequest]: List of comparisons in
                processing state

        Example:
            >>> processing = repo.get_processing_comparisons()
        """
        return self.get_by_status('processing')

    def count_by_status(self, status: str) -> int:
        """
        Count comparison requests by status.

        Args:
            status: Status to count

        Returns:
            int: Number of comparisons with the specified status

        Example:
            >>> count = repo.count_by_status('completed')
        """
        return self.count(status=status)

    def get_comparisons_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[ComparisonRequest]:
        """
        Get comparisons within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List[ComparisonRequest]: List of comparisons created
                within the date range

        Example:
            >>> from datetime import datetime, timedelta
            >>> end = datetime.utcnow()
            >>> start = end - timedelta(days=7)
            >>> recent = repo.get_comparisons_by_date_range(start, end)
        """
        return (self.model_class.query
                .filter(self.model_class.created_at >= start_date)
                .filter(self.model_class.created_at <= end_date)
                .order_by(self.model_class.created_at.desc())
                .all())
