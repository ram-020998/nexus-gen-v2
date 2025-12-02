"""
Change Action Service

Provides action functionality for changes in a merge session.
Handles user actions like marking as reviewed, skipping, saving notes,
and undo.
"""

import logging
from datetime import datetime
from typing import Optional

from core.base_service import BaseService
from models import db, MergeSession, Change
from repositories.change_repository import ChangeRepository


class ChangeActionService(BaseService):
    """
    Service for handling user actions on changes.

    Provides methods for:
    - Marking changes as reviewed
    - Skipping changes
    - Saving notes
    - Undoing actions

    All actions update both the change record and the session counters
    to maintain consistency.

    Example:
        >>> service = ChangeActionService()
        >>> change = service.mark_as_reviewed("MRG_001", 42, "user123")
        >>> print(f"Change {change.id} marked as reviewed")
    """

    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)
        self._statistics_service = None

    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.change_repository = self._get_repository(ChangeRepository)

    def _get_statistics_service(self):
        """Lazy load statistics service to avoid circular dependency."""
        if self._statistics_service is None:
            from services.session_statistics_service import (
                SessionStatisticsService
            )
            self._statistics_service = SessionStatisticsService(
                self._container
            )
        return self._statistics_service

    def mark_as_reviewed(
        self,
        reference_id: str,
        change_id: int,
        user_id: Optional[str] = None
    ) -> Change:
        """
        Mark a change as reviewed.

        Updates the change status to 'reviewed', sets the reviewed_at
        timestamp, optionally sets reviewed_by, and increments the
        session's reviewed_count.

        Args:
            reference_id: Session reference ID (e.g., MRG_001)
            change_id: Change ID
            user_id: Optional user ID who reviewed the change

        Returns:
            Updated Change object

        Raises:
            ValueError: If session or change not found

        Example:
            >>> change = service.mark_as_reviewed("MRG_001", 42, "user123")
            >>> assert change.status == 'reviewed'
            >>> assert change.reviewed_at is not None
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

        # Only increment counter if status is changing from pending
        if change.status == 'pending':
            session.reviewed_count += 1

        # Update change
        change.status = 'reviewed'
        change.reviewed_at = datetime.utcnow()
        if user_id:
            change.reviewed_by = user_id

        # Update session status to in_progress if it's the first action
        if session.status == 'ready':
            session.status = 'in_progress'

        # Update session timestamp
        session.updated_at = datetime.utcnow()

        # Commit changes
        db.session.commit()

        # Invalidate statistics cache
        self._get_statistics_service().invalidate_cache(session.id)

        self.logger.info(
            f"Change {change_id} marked as reviewed in session {reference_id}"
        )

        return change

    def skip_change(
        self,
        reference_id: str,
        change_id: int
    ) -> Change:
        """
        Mark a change as skipped.

        Updates the change status to 'skipped' and increments the
        session's skipped_count.

        Args:
            reference_id: Session reference ID (e.g., MRG_001)
            change_id: Change ID

        Returns:
            Updated Change object

        Raises:
            ValueError: If session or change not found

        Example:
            >>> change = service.skip_change("MRG_001", 42)
            >>> assert change.status == 'skipped'
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

        # Only increment counter if status is changing from pending
        if change.status == 'pending':
            session.skipped_count += 1

        # Update change
        change.status = 'skipped'

        # Update session status to in_progress if it's the first action
        if session.status == 'ready':
            session.status = 'in_progress'

        # Update session timestamp
        session.updated_at = datetime.utcnow()

        # Commit changes
        db.session.commit()

        # Invalidate statistics cache
        self._get_statistics_service().invalidate_cache(session.id)

        self.logger.info(
            f"Change {change_id} skipped in session {reference_id}"
        )

        return change

    def save_notes(
        self,
        reference_id: str,
        change_id: int,
        notes: str
    ) -> Change:
        """
        Save user notes for a change.

        Updates the change's notes field with the provided text.

        Args:
            reference_id: Session reference ID (e.g., MRG_001)
            change_id: Change ID
            notes: Notes text to save

        Returns:
            Updated Change object

        Raises:
            ValueError: If session or change not found

        Example:
            >>> change = service.save_notes(
            ...     "MRG_001",
            ...     42,
            ...     "This change requires manual merge"
            ... )
            >>> assert change.notes == "This change requires manual merge"
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

        # Update notes
        change.notes = notes

        # Update session timestamp
        session.updated_at = datetime.utcnow()

        # Commit changes
        db.session.commit()

        self.logger.info(
            f"Notes saved for change {change_id} in session {reference_id}"
        )

        return change

    def undo_action(
        self,
        reference_id: str,
        change_id: int
    ) -> Change:
        """
        Undo review/skip action on a change.

        Resets the change status to 'pending', clears reviewed_at,
        and decrements the appropriate session counter.

        Args:
            reference_id: Session reference ID (e.g., MRG_001)
            change_id: Change ID

        Returns:
            Updated Change object

        Raises:
            ValueError: If session or change not found

        Example:
            >>> change = service.undo_action("MRG_001", 42)
            >>> assert change.status == 'pending'
            >>> assert change.reviewed_at is None
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

        # Decrement appropriate counter
        if change.status == 'reviewed':
            session.reviewed_count = max(0, session.reviewed_count - 1)
        elif change.status == 'skipped':
            session.skipped_count = max(0, session.skipped_count - 1)

        # Reset change to pending
        change.status = 'pending'
        change.reviewed_at = None

        # Update session timestamp
        session.updated_at = datetime.utcnow()

        # Commit changes
        db.session.commit()

        # Invalidate statistics cache
        self._get_statistics_service().invalidate_cache(session.id)

        self.logger.info(
            f"Action undone for change {change_id} in session {reference_id}"
        )

        return change

    def complete_session(self, reference_id: str) -> MergeSession:
        """
        Mark a merge session as completed.

        Updates the session status to 'completed' if all changes have been
        reviewed or skipped.

        Args:
            reference_id: Session reference ID (e.g., MRG_001)

        Returns:
            Updated MergeSession object

        Raises:
            ValueError: If session not found or has pending changes

        Example:
            >>> session = service.complete_session("MRG_001")
            >>> assert session.status == 'completed'
        """
        # Find session
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()

        if not session:
            raise ValueError(f"Session not found: {reference_id}")

        # Check if all changes are reviewed or skipped
        pending_count = db.session.query(Change).filter_by(
            session_id=session.id,
            status='pending'
        ).count()

        if pending_count > 0:
            raise ValueError(
                f"Cannot complete session: {pending_count} changes are still pending"
            )

        # Update session status
        session.status = 'completed'
        session.updated_at = datetime.utcnow()

        # Commit changes
        db.session.commit()

        # Invalidate statistics cache
        self._get_statistics_service().invalidate_cache(session.id)

        self.logger.info(
            f"Session {reference_id} marked as completed"
        )

        return session
