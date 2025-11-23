"""
Comparison Request Manager Service.

This module manages the lifecycle of comparison requests, including
creation, status updates, and result storage.
"""

from typing import Optional

from core.base_service import BaseService
from repositories.comparison_repository import ComparisonRepository
from models import ComparisonRequest


class ComparisonRequestManager(BaseService):
    """
    Manages comparison request lifecycle.
    
    This service handles the creation, updating, and storage of comparison
    requests throughout their lifecycle from initial creation through
    completion or error states.
    
    Example:
        >>> manager = ComparisonRequestManager()
        >>> request = manager.create_request('OldApp', 'NewApp')
        >>> manager.update_status(request.id, 'completed')
    """
    
    def _initialize_dependencies(self):
        """Initialize repository dependencies."""
        self.comparison_repo = self._get_repository(ComparisonRepository)
    
    def create_request(
        self,
        old_app_name: str,
        new_app_name: str
    ) -> ComparisonRequest:
        """
        Create new comparison request.
        
        Generates a unique reference ID and creates a new comparison
        request in the database with 'processing' status.
        
        Args:
            old_app_name: Name of the old application version
            new_app_name: Name of the new application version
            
        Returns:
            ComparisonRequest: Newly created comparison request
            
        Example:
            >>> request = manager.create_request(
            ...     'SourceSelectionv2.4.0',
            ...     'SourceSelectionv2.6.0'
            ... )
        """
        # Generate reference ID
        count = self.comparison_repo.count() + 1
        reference_id = f"CMP_{count:03d}"
        
        return self.comparison_repo.create(
            reference_id=reference_id,
            old_app_name=old_app_name,
            new_app_name=new_app_name,
            status='processing'
        )
    
    def update_status(
        self,
        request_id: int,
        status: str,
        error_msg: Optional[str] = None
    ) -> Optional[ComparisonRequest]:
        """
        Update request status.
        
        Updates the status of a comparison request and optionally
        records an error message.
        
        Args:
            request_id: ID of the comparison request
            status: New status ('processing', 'completed', 'error')
            error_msg: Optional error message for failed requests
            
        Returns:
            Optional[ComparisonRequest]: Updated request if found,
                None otherwise
                
        Example:
            >>> manager.update_status(1, 'completed')
            >>> manager.update_status(2, 'error', 'Analysis failed')
        """
        return self.comparison_repo.update_status(
            request_id,
            status,
            error_msg
        )
    
    def save_results(
        self,
        request_id: int,
        old_blueprint: dict,
        new_blueprint: dict,
        comparison: dict,
        processing_time: int
    ) -> Optional[ComparisonRequest]:
        """
        Save analysis results.
        
        Stores the complete analysis results including blueprints,
        comparison data, and processing time. Updates status to 'completed'.
        
        Args:
            request_id: ID of the comparison request
            old_blueprint: Blueprint dictionary for old version
            new_blueprint: Blueprint dictionary for new version
            comparison: Comparison results dictionary
            processing_time: Processing time in seconds
            
        Returns:
            Optional[ComparisonRequest]: Updated request if found,
                None otherwise
                
        Example:
            >>> manager.save_results(
            ...     request_id=1,
            ...     old_blueprint={'objects': [...]},
            ...     new_blueprint={'objects': [...]},
            ...     comparison={'changes': [...]},
            ...     processing_time=45
            ... )
        """
        import json
        
        request = self.comparison_repo.get_by_id(request_id)
        if request:
            # Update blueprints
            self.comparison_repo.update_blueprints(
                request_id,
                json.dumps(old_blueprint),
                json.dumps(new_blueprint)
            )
            
            # Update results
            self.comparison_repo.update_results(
                request_id,
                json.dumps(comparison),
                processing_time
            )
            
            # Update status to completed
            return self.comparison_repo.update_status(
                request_id,
                'completed'
            )
        
        return None
    
    def get_request(self, request_id: int) -> Optional[ComparisonRequest]:
        """
        Get comparison request by ID.
        
        Args:
            request_id: ID of the comparison request
            
        Returns:
            Optional[ComparisonRequest]: Request if found, None otherwise
            
        Example:
            >>> request = manager.get_request(1)
        """
        return self.comparison_repo.get_by_id(request_id)
    
    def get_all_requests(self) -> list:
        """
        Get all comparison requests.
        
        Returns requests ordered by creation date (most recent first).
        
        Returns:
            list: List of all comparison requests
            
        Example:
            >>> requests = manager.get_all_requests()
        """
        return self.comparison_repo.get_recent(limit=1000)
