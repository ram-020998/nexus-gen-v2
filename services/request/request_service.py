"""
Request Service - Manage breakdown/verify/create requests

This is the refactored class-based implementation with dependency injection.
"""
from typing import Optional, List
from core.base_service import BaseService
from repositories.request_repository import RequestRepository
from services.data_source_factory import DataSourceFactory
from models import Request


class RequestService(BaseService):
    """
    Service for managing requests with dependency injection

    Handles creation, retrieval, and status updates for
    breakdown/verify/create requests.
    Integrates with Bedrock RAG service for AI-powered processing.
    """

    def _initialize_dependencies(self):
        """Initialize service dependencies"""
        self.request_repo = self._get_repository(RequestRepository)
        self.bedrock_service = DataSourceFactory.create_rag_service()

    def create_request(self, action_type: str, filename: str = None,
                       input_text: str = None) -> Request:
        """
        Create a new request

        Args:
            action_type: Type of action (breakdown, verify, create)
            filename: Optional filename for file-based requests
            input_text: Optional input text for text-based requests

        Returns:
            Created Request instance
        """
        return self.request_repo.create(
            action_type=action_type,
            filename=filename,
            input_text=input_text,
            status='processing'
        )

    def update_request_status(self, request_id: int, status: str,
                              output_data: str = None) -> Optional[Request]:
        """
        Update request status and output

        Args:
            request_id: ID of the request to update
            status: New status value
            output_data: Optional output data to store

        Returns:
            Updated Request instance or None if not found
        """
        return self.request_repo.update_status(
            request_id, status, output_data
        )

    def get_request(self, request_id: int) -> Optional[Request]:
        """
        Get request by ID

        Args:
            request_id: ID of the request to retrieve

        Returns:
            Request instance or None if not found
        """
        return self.request_repo.get_by_id(request_id)

    def get_recent_requests(self, action_type: str = None,
                            limit: int = 10) -> List[Request]:
        """
        Get recent requests, optionally filtered by action type

        Args:
            action_type: Optional action type filter
            limit: Maximum number of requests to return

        Returns:
            List of Request instances
        """
        if action_type:
            return self.request_repo.get_recent_by_action(action_type, limit)
        return self.request_repo.get_all()[:limit]

    def process_with_bedrock(self, request: Request,
                             query_text: str) -> dict:
        """
        Process request with Bedrock RAG service

        Args:
            request: Request instance to process
            query_text: Query text for Bedrock service

        Returns:
            Bedrock service response as dictionary
        """
        # Query Bedrock service
        bedrock_response = self.bedrock_service.query(
            request.action_type, query_text
        )

        # Update request with Bedrock data
        request.rag_query = query_text
        request.rag_response = str(bedrock_response)
        self.request_repo.update(request)

        return bedrock_response
