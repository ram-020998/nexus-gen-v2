"""
Session Statistics Service

Provides statistical analysis and metrics for merge sessions.
Calculates complexity, estimates review time, and tracks progress.
"""

import logging
from typing import Dict, Any

from core.base_service import BaseService
from core.cache import SessionCache
from models import db, MergeSession, Change


class SessionStatisticsService(BaseService):
    """
    Service for calculating session statistics and metrics.

    Provides methods for:
    - Calculating estimated complexity (Low, Medium, High)
    - Estimating review time in hours
    - Getting progress metrics
    - Caching statistics for performance

    Statistics are cached for 5 minutes and invalidated on change updates.

    Example:
        >>> service = SessionStatisticsService()
        >>> complexity = service.calculate_complexity(1)
        >>> print(f"Complexity: {complexity}")
        >>> time = service.estimate_review_time(1)
        >>> print(f"Estimated time: {time} hours")
        >>> metrics = service.get_progress_metrics(1)
        >>> print(f"Progress: {metrics['progress_percent']}%")
    """

    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)
        self.cache = SessionCache()

    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        pass

    def calculate_complexity(self, session_id: int) -> str:
        """
        Calculate estimated complexity (Low, Medium, High).

        Complexity is based on:
        - Number of conflicts (high weight)
        - Total number of changes
        - Object types involved (Process Models are more complex)
        - Mix of change types

        Scoring:
        - Low: < 10 changes, few conflicts, simple objects
        - Medium: 10-30 changes, some conflicts, mixed objects
        - High: > 30 changes, many conflicts, complex objects

        Args:
            session_id: Merge session ID

        Returns:
            Complexity level: 'Low', 'Medium', or 'High'

        Raises:
            ValueError: If session not found

        Example:
            >>> complexity = service.calculate_complexity(1)
            >>> assert complexity in ['Low', 'Medium', 'High']
        """
        # Get session
        session = db.session.query(MergeSession).filter_by(
            id=session_id
        ).first()

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Get change statistics
        total_changes = session.total_changes

        # Count conflicts
        conflict_count = db.session.query(Change).filter_by(
            session_id=session_id,
            classification='CONFLICT'
        ).count()

        # Calculate complexity score
        score = 0

        # Factor 1: Total changes (0-40 points)
        if total_changes <= 5:
            score += 10
        elif total_changes <= 15:
            score += 20
        elif total_changes <= 30:
            score += 30
        else:
            score += 40

        # Factor 2: Conflict ratio (0-40 points)
        if total_changes > 0:
            conflict_ratio = conflict_count / total_changes
            if conflict_ratio <= 0.1:
                score += 10
            elif conflict_ratio <= 0.3:
                score += 20
            elif conflict_ratio <= 0.5:
                score += 30
            else:
                score += 40

        # Factor 3: Complex object types (0-20 points)
        # Process models and record types are more complex
        complex_objects = db.session.query(Change).filter(
            Change.session_id == session_id
        ).join(
            Change.object
        ).filter(
            db.or_(
                Change.object.has(object_type='process_model'),
                Change.object.has(object_type='record_type')
            )
        ).count()  # noqa: E501

        if complex_objects > 0:
            complex_ratio = (
                complex_objects / total_changes
                if total_changes > 0
                else 0
            )
            if complex_ratio <= 0.2:
                score += 5
            elif complex_ratio <= 0.5:
                score += 10
            else:
                score += 20

        # Determine complexity level
        if score <= 30:
            complexity = 'Low'
        elif score <= 60:
            complexity = 'Medium'
        else:
            complexity = 'High'

        self.logger.info(
            f"Session {session_id} complexity: {complexity} (score: {score})"
        )

        return complexity

    def estimate_review_time(self, session_id: int) -> float:
        """
        Estimate review time in hours.

        Time estimation is based on:
        - Total changes (base time per change)
        - Conflict count (conflicts take longer)
        - Object complexity (complex objects take longer)
        - Historical data (if available)

        Base estimates:
        - Simple change: 5 minutes
        - Conflict: 15 minutes
        - Process model: +5 minutes
        - Record type: +3 minutes

        Args:
            session_id: Merge session ID

        Returns:
            Estimated review time in hours (rounded to 1 decimal)

        Raises:
            ValueError: If session not found

        Example:
            >>> time = service.estimate_review_time(1)
            >>> print(f"Estimated time: {time} hours")
        """
        # Get session
        session = db.session.query(MergeSession).filter_by(
            id=session_id
        ).first()

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        total_changes = session.total_changes

        if total_changes == 0:
            return 0.0

        # Base time per change (5 minutes)
        base_time_minutes = total_changes * 5

        # Additional time for conflicts (10 extra minutes per conflict)
        conflict_count = db.session.query(Change).filter_by(
            session_id=session_id,
            classification='CONFLICT'
        ).count()
        conflict_time_minutes = conflict_count * 10

        # Additional time for complex objects
        process_model_count = db.session.query(Change).filter(
            Change.session_id == session_id
        ).join(
            Change.object
        ).filter(
            Change.object.has(object_type='process_model')
        ).count()

        record_type_count = db.session.query(Change).filter(
            Change.session_id == session_id
        ).join(
            Change.object
        ).filter(
            Change.object.has(object_type='record_type')
        ).count()

        complex_time_minutes = (
            (process_model_count * 5) + (record_type_count * 3)
        )

        # Total time in minutes
        total_minutes = (
            base_time_minutes + conflict_time_minutes + complex_time_minutes
        )

        # Convert to hours and round to 1 decimal
        total_hours = round(total_minutes / 60, 1)

        self.logger.info(
            f"Session {session_id} estimated time: {total_hours} hours "
            f"({total_changes} changes, {conflict_count} conflicts)"
        )

        return total_hours

    def get_progress_metrics(self, session_id: int) -> Dict[str, Any]:
        """
        Get progress metrics for a session.

        Returns comprehensive progress information including:
        - Total changes
        - Reviewed count
        - Skipped count
        - Pending count
        - Progress percentage
        - Breakdown by classification
        - Breakdown by object type

        Results are cached for 5 minutes for performance.

        Args:
            session_id: Merge session ID

        Returns:
            Dict containing:
            - total_changes: Total number of changes
            - reviewed_count: Number reviewed
            - skipped_count: Number skipped
            - pending_count: Number pending
            - progress_percent: Percentage complete (0-100)
            - by_classification: Dict of counts by classification
            - by_object_type: Dict of counts by object type
            - by_status: Dict of counts by status

        Raises:
            ValueError: If session not found

        Example:
            >>> metrics = service.get_progress_metrics(1)
            >>> print(f"Progress: {metrics['progress_percent']}%")
            >>> print(f"Reviewed: {metrics['reviewed_count']}")
            >>> print(f"Conflicts: {metrics['by_classification']['CONFLICT']}")
        """
        # Try to get from cache
        cached_metrics = self.cache.get_statistics(session_id)
        if cached_metrics is not None:
            self.logger.debug(f"Cache hit for session {session_id} statistics")
            return cached_metrics

        # Get session
        session = db.session.query(MergeSession).filter_by(
            id=session_id
        ).first()

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Basic counts
        total_changes = session.total_changes
        reviewed_count = session.reviewed_count
        skipped_count = session.skipped_count
        pending_count = total_changes - reviewed_count - skipped_count

        # Calculate progress percentage
        completed_count = reviewed_count + skipped_count
        progress_percent = (
            round((completed_count / total_changes * 100), 2)
            if total_changes > 0
            else 0
        )

        # Breakdown by classification
        classification_results = db.session.query(
            Change.classification,
            db.func.count(Change.id)
        ).filter_by(
            session_id=session_id
        ).group_by(
            Change.classification
        ).all()

        by_classification = {
            classification: count
            for classification, count in classification_results
        }

        # Ensure all classifications are present
        for classification in ['NO_CONFLICT', 'CONFLICT', 'NEW', 'DELETED']:
            if classification not in by_classification:
                by_classification[classification] = 0

        # Breakdown by object type
        from sqlalchemy import func
        from models import ObjectLookup

        object_type_results = db.session.query(
            ObjectLookup.object_type,
            func.count(Change.id)
        ).join(
            Change,
            Change.object_id == ObjectLookup.id
        ).filter(
            Change.session_id == session_id
        ).group_by(
            ObjectLookup.object_type
        ).all()  # noqa: E501

        by_object_type = {
            object_type: count
            for object_type, count in object_type_results
        }

        # Breakdown by status
        status_results = db.session.query(
            Change.status,
            db.func.count(Change.id)
        ).filter_by(
            session_id=session_id
        ).group_by(
            Change.status
        ).all()

        by_status = {
            status: count
            for status, count in status_results
        }

        # Ensure all statuses are present
        for status in ['pending', 'reviewed', 'skipped']:
            if status not in by_status:
                by_status[status] = 0

        # Build metrics dict
        metrics = {
            'total_changes': total_changes,
            'reviewed_count': reviewed_count,
            'skipped_count': skipped_count,
            'pending_count': pending_count,
            'progress_percent': progress_percent,
            'by_classification': by_classification,
            'by_object_type': by_object_type,
            'by_status': by_status
        }

        # Cache for 5 minutes
        self.cache.set_statistics(session_id, metrics, ttl=300)

        self.logger.info(
            f"Session {session_id} progress: {progress_percent}% "
            f"({reviewed_count} reviewed, {skipped_count} skipped, "
            f"{pending_count} pending)"
        )

        return metrics

    def invalidate_cache(self, session_id: int) -> None:
        """
        Invalidate cached statistics for a session.

        Should be called when changes are updated (reviewed, skipped, etc.)
        to ensure fresh statistics are calculated.

        Args:
            session_id: Merge session ID

        Example:
            >>> service.invalidate_cache(1)
        """
        self.cache.invalidate_statistics(session_id)
        self.logger.debug(f"Invalidated cache for session {session_id}")
