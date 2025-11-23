"""
Merge session repository for managing MergeSession model data access.

This module provides data access methods for the MergeSession model,
which handles three-way merge sessions for Appian applications.
"""

from typing import List, Optional
from datetime import datetime
from core.base_repository import BaseRepository
from models import MergeSession


class MergeSessionRepository(BaseRepository[MergeSession]):
    """
    Repository for MergeSession model operations.

    Provides data access methods for managing three-way merge sessions,
    including session creation, status tracking, and progress management.

    Example:
        >>> repo = MergeSessionRepository()
        >>> session = repo.create(
        ...     reference_id='MRG_001',
        ...     base_package_name='AppV1.0',
        ...     customized_package_name='AppV1.0_Custom',
        ...     new_vendor_package_name='AppV2.0',
        ...     status='processing'
        ... )
        >>> recent = repo.get_recent(limit=5)
    """

    def __init__(self):
        """Initialize MergeSessionRepository with MergeSession model."""
        super().__init__(MergeSession)

    def get_by_reference_id(
        self,
        reference_id: str
    ) -> Optional[MergeSession]:
        """
        Get merge session by reference ID.

        Args:
            reference_id: Reference ID (e.g., 'MRG_001')

        Returns:
            Optional[MergeSession]: Session if found, None otherwise

        Example:
            >>> session = repo.get_by_reference_id('MRG_001')
        """
        return self.find_one(reference_id=reference_id)

    def get_recent(self, limit: int = 10) -> List[MergeSession]:
        """
        Get most recent merge sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List[MergeSession]: List of recent sessions ordered
                by creation date

        Example:
            >>> recent = repo.get_recent(limit=20)
        """
        return (self.model_class.query
                .order_by(self.model_class.created_at.desc())
                .limit(limit)
                .all())

    def get_by_status(self, status: str) -> List[MergeSession]:
        """
        Get all merge sessions with a specific status.

        Args:
            status: Status to filter by ('processing', 'ready',
                'in_progress', 'completed', 'error')

        Returns:
            List[MergeSession]: List of sessions with the specified status

        Example:
            >>> processing = repo.get_by_status('processing')
        """
        return self.filter_by(status=status)

    def update_status(
        self,
        session_id: int,
        status: str,
        error_log: Optional[str] = None
    ) -> Optional[MergeSession]:
        """
        Update merge session status.

        Args:
            session_id: ID of the session to update
            status: New status ('processing', 'ready', 'in_progress',
                'completed', 'error')
            error_log: Optional error log message

        Returns:
            Optional[MergeSession]: Updated session if found, None otherwise

        Example:
            >>> session = repo.update_status(
            ...     session_id=1,
            ...     status='completed'
            ... )
        """
        session = self.get_by_id(session_id)
        if session:
            session.status = status
            if error_log:
                session.error_log = error_log
            session.updated_at = datetime.utcnow()
            if status == 'completed':
                session.completed_at = datetime.utcnow()
            self.update(session)
        return session

    def update_progress(
        self,
        session_id: int,
        current_change_index: Optional[int] = None,
        reviewed_count: Optional[int] = None,
        skipped_count: Optional[int] = None
    ) -> Optional[MergeSession]:
        """
        Update merge session progress.

        Args:
            session_id: ID of the session to update
            current_change_index: Current change being reviewed
            reviewed_count: Number of changes reviewed
            skipped_count: Number of changes skipped

        Returns:
            Optional[MergeSession]: Updated session if found, None otherwise

        Example:
            >>> session = repo.update_progress(
            ...     session_id=1,
            ...     current_change_index=5,
            ...     reviewed_count=3,
            ...     skipped_count=2
            ... )
        """
        session = self.get_by_id(session_id)
        if session:
            if current_change_index is not None:
                session.current_change_index = current_change_index
            if reviewed_count is not None:
                session.reviewed_count = reviewed_count
            if skipped_count is not None:
                session.skipped_count = skipped_count
            session.updated_at = datetime.utcnow()
            self.update(session)
        return session

    def increment_reviewed(
        self,
        session_id: int
    ) -> Optional[MergeSession]:
        """
        Increment the reviewed count for a session.

        Args:
            session_id: ID of the session to update

        Returns:
            Optional[MergeSession]: Updated session if found, None otherwise

        Example:
            >>> session = repo.increment_reviewed(session_id=1)
        """
        session = self.get_by_id(session_id)
        if session:
            session.reviewed_count += 1
            session.updated_at = datetime.utcnow()
            self.update(session)
        return session

    def increment_skipped(
        self,
        session_id: int
    ) -> Optional[MergeSession]:
        """
        Increment the skipped count for a session.

        Args:
            session_id: ID of the session to update

        Returns:
            Optional[MergeSession]: Updated session if found, None otherwise

        Example:
            >>> session = repo.increment_skipped(session_id=1)
        """
        session = self.get_by_id(session_id)
        if session:
            session.skipped_count += 1
            session.updated_at = datetime.utcnow()
            self.update(session)
        return session

    def set_total_changes(
        self,
        session_id: int,
        total_changes: int
    ) -> Optional[MergeSession]:
        """
        Set the total number of changes for a session.

        Args:
            session_id: ID of the session to update
            total_changes: Total number of changes

        Returns:
            Optional[MergeSession]: Updated session if found, None otherwise

        Example:
            >>> session = repo.set_total_changes(
            ...     session_id=1,
            ...     total_changes=150
            ... )
        """
        session = self.get_by_id(session_id)
        if session:
            session.total_changes = total_changes
            session.updated_at = datetime.utcnow()
            self.update(session)
        return session

    def complete_session(
        self,
        session_id: int,
        total_time: Optional[int] = None
    ) -> Optional[MergeSession]:
        """
        Mark a session as completed.

        Args:
            session_id: ID of the session to complete
            total_time: Optional total processing time in seconds

        Returns:
            Optional[MergeSession]: Updated session if found, None otherwise

        Example:
            >>> session = repo.complete_session(
            ...     session_id=1,
            ...     total_time=3600
            ... )
        """
        session = self.get_by_id(session_id)
        if session:
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
            if total_time is not None:
                session.total_time = total_time
            session.updated_at = datetime.utcnow()
            self.update(session)
        return session

    def get_active_sessions(self) -> List[MergeSession]:
        """
        Get all active merge sessions (not completed or errored).

        Returns:
            List[MergeSession]: List of active sessions

        Example:
            >>> active = repo.get_active_sessions()
        """
        return (self.model_class.query
                .filter(self.model_class.status.in_(
                    ['processing', 'ready', 'in_progress']
                ))
                .order_by(self.model_class.created_at.desc())
                .all())

    def get_completed_sessions(self) -> List[MergeSession]:
        """
        Get all completed merge sessions.

        Returns:
            List[MergeSession]: List of completed sessions

        Example:
            >>> completed = repo.get_completed_sessions()
        """
        return self.get_by_status('completed')

    def get_failed_sessions(self) -> List[MergeSession]:
        """
        Get all failed merge sessions.

        Returns:
            List[MergeSession]: List of failed sessions

        Example:
            >>> failed = repo.get_failed_sessions()
        """
        return self.get_by_status('error')

    def get_sessions_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[MergeSession]:
        """
        Get merge sessions within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            List[MergeSession]: List of sessions created
                within the date range

        Example:
            >>> from datetime import datetime, timedelta
            >>> end = datetime.utcnow()
            >>> start = end - timedelta(days=7)
            >>> recent = repo.get_sessions_by_date_range(start, end)
        """
        return (self.model_class.query
                .filter(self.model_class.created_at >= start_date)
                .filter(self.model_class.created_at <= end_date)
                .order_by(self.model_class.created_at.desc())
                .all())

    def get_progress_percentage(
        self,
        session_id: int
    ) -> Optional[float]:
        """
        Calculate progress percentage for a session.

        Args:
            session_id: ID of the session

        Returns:
            Optional[float]: Progress percentage (0-100) if session found,
                None otherwise

        Example:
            >>> progress = repo.get_progress_percentage(session_id=1)
            >>> print(f"Progress: {progress:.1f}%")
        """
        session = self.get_by_id(session_id)
        if session and session.total_changes > 0:
            completed = session.reviewed_count + session.skipped_count
            return (completed / session.total_changes) * 100
        return None

    def count_by_status(self, status: str) -> int:
        """
        Count merge sessions by status.

        Args:
            status: Status to count

        Returns:
            int: Number of sessions with the specified status

        Example:
            >>> count = repo.count_by_status('completed')
        """
        return self.count(status=status)
