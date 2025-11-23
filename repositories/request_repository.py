"""
Request repository for managing Request model data access.

This module provides data access methods for the Request model,
which handles breakdown, verify, and create actions.
"""

from typing import List, Optional
from datetime import datetime
from core.base_repository import BaseRepository
from models import Request


class RequestRepository(BaseRepository[Request]):
    """
    Repository for Request model operations.

    Provides data access methods for managing requests including
    breakdown, verify, and create actions with their associated
    metadata and processing results.

    Example:
        >>> repo = RequestRepository()
        >>> request = repo.create(
        ...     action_type='breakdown',
        ...     filename='document.txt',
        ...     status='processing'
        ... )
        >>> recent = repo.get_recent_by_action('breakdown', limit=5)
    """

    def __init__(self):
        """Initialize RequestRepository with Request model."""
        super().__init__(Request)

    def get_recent_by_action(
        self,
        action_type: str,
        limit: int = 10
    ) -> List[Request]:
        """
        Get recent requests by action type.

        Args:
            action_type: Type of action ('breakdown', 'verify', 'create')
            limit: Maximum number of requests to return

        Returns:
            List[Request]: List of recent requests ordered by creation date

        Example:
            >>> requests = repo.get_recent_by_action('breakdown', limit=5)
        """
        return (self.model_class.query
                .filter_by(action_type=action_type)
                .order_by(self.model_class.created_at.desc())
                .limit(limit)
                .all())

    def get_by_reference_id(self, reference_id: str) -> Optional[Request]:
        """
        Get request by reference ID.

        Args:
            reference_id: Reference ID (e.g., 'RQ_ND_001')

        Returns:
            Optional[Request]: Request if found, None otherwise

        Example:
            >>> request = repo.get_by_reference_id('RQ_ND_001')
        """
        return self.find_one(reference_id=reference_id)

    def update_status(
        self,
        request_id: int,
        status: str,
        output_data: Optional[str] = None
    ) -> Optional[Request]:
        """
        Update request status and optionally set output data.

        Args:
            request_id: ID of the request to update
            status: New status ('processing', 'completed', 'error')
            output_data: Optional final output data

        Returns:
            Optional[Request]: Updated request if found, None otherwise

        Example:
            >>> request = repo.update_status(
            ...     request_id=1,
            ...     status='completed',
            ...     output_data='{"result": "success"}'
            ... )
        """
        request = self.get_by_id(request_id)
        if request:
            request.status = status
            if output_data:
                request.final_output = output_data
            request.updated_at = datetime.utcnow()
            self.update(request)
        return request

    def get_by_status(self, status: str) -> List[Request]:
        """
        Get all requests with a specific status.

        Args:
            status: Status to filter by ('processing', 'completed', 'error')

        Returns:
            List[Request]: List of requests with the specified status

        Example:
            >>> processing = repo.get_by_status('processing')
        """
        return self.filter_by(status=status)

    def get_recent(self, limit: int = 10) -> List[Request]:
        """
        Get most recent requests across all action types.

        Args:
            limit: Maximum number of requests to return

        Returns:
            List[Request]: List of recent requests ordered by creation date

        Example:
            >>> recent = repo.get_recent(limit=20)
        """
        return (self.model_class.query
                .order_by(self.model_class.created_at.desc())
                .limit(limit)
                .all())

    def get_by_agent_name(self, agent_name: str) -> List[Request]:
        """
        Get all requests processed by a specific agent.

        Args:
            agent_name: Name of the agent (e.g., 'breakdown-agent')

        Returns:
            List[Request]: List of requests processed by the agent

        Example:
            >>> requests = repo.get_by_agent_name('breakdown-agent')
        """
        return self.filter_by(agent_name=agent_name)

    def get_failed_requests(self) -> List[Request]:
        """
        Get all requests with error status.

        Returns:
            List[Request]: List of failed requests

        Example:
            >>> failed = repo.get_failed_requests()
        """
        return self.get_by_status('error')

    def get_completed_requests(self) -> List[Request]:
        """
        Get all completed requests.

        Returns:
            List[Request]: List of completed requests

        Example:
            >>> completed = repo.get_completed_requests()
        """
        return self.get_by_status('completed')

    def get_processing_requests(self) -> List[Request]:
        """
        Get all requests currently being processed.

        Returns:
            List[Request]: List of requests in processing state

        Example:
            >>> processing = repo.get_processing_requests()
        """
        return self.get_by_status('processing')

    def count_by_action_type(self, action_type: str) -> int:
        """
        Count requests by action type.

        Args:
            action_type: Type of action to count

        Returns:
            int: Number of requests with the specified action type

        Example:
            >>> count = repo.count_by_action_type('breakdown')
        """
        return self.count(action_type=action_type)

    def count_by_status(self, status: str) -> int:
        """
        Count requests by status.

        Args:
            status: Status to count

        Returns:
            int: Number of requests with the specified status

        Example:
            >>> count = repo.count_by_status('completed')
        """
        return self.count(status=status)
