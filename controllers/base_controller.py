"""
Base Controller - Common functionality for all controllers

Provides shared utilities for response formatting, error handling,
and service access across all Flask controllers.
"""

from flask import jsonify, flash, redirect, url_for, render_template
from typing import Any, Dict, Optional, Tuple, Union
from functools import wraps
from pathlib import Path
import traceback

from core.dependency_container import DependencyContainer


class BaseController:
    """
    Base controller class providing common functionality for all controllers.
    
    This class provides helper methods for:
    - Response formatting (JSON, HTML, redirects)
    - Error handling (exceptions, validation, logging)
    - Service access (dependency injection)
    - File validation
    - Flash messaging
    
    Controllers should inherit from this class to access shared functionality.
    
    Example:
        >>> class MyController(BaseController):
        ...     def __init__(self):
        ...         super().__init__()
        ...         self.my_service = self.get_service(MyService)
    """
    
    def __init__(self, container: Optional[DependencyContainer] = None):
        """
        Initialize base controller with dependency container.
        
        Args:
            container: Optional dependency injection container.
                      If None, uses singleton instance.
        """
        self._container = container or DependencyContainer.get_instance()
    
    # ========================================================================
    # Service Access Methods
    # ========================================================================
    
    def get_service(self, service_class: type) -> Any:
        """
        Get service instance from dependency container.
        
        Args:
            service_class: The service class to retrieve
            
        Returns:
            Service instance
            
        Example:
            >>> request_service = self.get_service(RequestService)
        """
        return self._container.get_service(service_class)
    
    def get_repository(self, repo_class: type) -> Any:
        """
        Get repository instance from dependency container.
        
        Args:
            repo_class: The repository class to retrieve
            
        Returns:
            Repository instance
            
        Example:
            >>> request_repo = self.get_repository(RequestRepository)
        """
        return self._container.get_repository(repo_class)
    
    # ========================================================================
    # Response Formatting Methods
    # ========================================================================
    
    def json_response(
        self,
        data: Any = None,
        success: bool = True,
        message: Optional[str] = None,
        status_code: int = 200,
        **kwargs
    ) -> Tuple[Dict[str, Any], int]:
        """
        Create standardized JSON response.
        
        Args:
            data: Response data (optional)
            success: Success flag
            message: Optional message
            status_code: HTTP status code
            **kwargs: Additional fields to include in response
            
        Returns:
            Tuple of (response_dict, status_code)
            
        Example:
            >>> return self.json_response(
            ...     data={'id': 123},
            ...     message='Created successfully',
            ...     status_code=201
            ... )
        """
        response = {
            'success': success,
            **kwargs
        }
        
        if message:
            response['message'] = message
        
        if data is not None:
            response['data'] = data
        
        return jsonify(response), status_code
    
    def json_success(
        self,
        data: Any = None,
        message: Optional[str] = None,
        status_code: int = 200,
        **kwargs
    ) -> Tuple[Dict[str, Any], int]:
        """
        Create success JSON response.
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code (default 200)
            **kwargs: Additional fields
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return self.json_response(
            data=data,
            success=True,
            message=message,
            status_code=status_code,
            **kwargs
        )
    
    def json_error(
        self,
        error: Union[str, Exception],
        status_code: int = 500,
        **kwargs
    ) -> Tuple[Dict[str, Any], int]:
        """
        Create error JSON response.
        
        Args:
            error: Error message or exception
            status_code: HTTP status code (default 500)
            **kwargs: Additional fields
            
        Returns:
            Tuple of (response_dict, status_code)
            
        Example:
            >>> return self.json_error('Invalid input', status_code=400)
        """
        error_message = str(error)
        
        return self.json_response(
            success=False,
            message=error_message,
            error=error_message,
            status_code=status_code,
            **kwargs
        )
    
    def render(
        self,
        template: str,
        **context
    ) -> str:
        """
        Render template with context.
        
        Args:
            template: Template path
            **context: Template context variables
            
        Returns:
            Rendered HTML string
            
        Example:
            >>> return self.render('users/list.html', users=users)
        """
        return render_template(template, **context)
    
    def redirect_to(
        self,
        endpoint: str,
        **values
    ) -> Any:
        """
        Redirect to endpoint.
        
        Args:
            endpoint: Flask endpoint name
            **values: URL parameters
            
        Returns:
            Flask redirect response
            
        Example:
            >>> return self.redirect_to('users.list')
            >>> return self.redirect_to('users.detail', user_id=123)
        """
        return redirect(url_for(endpoint, **values))
    
    # ========================================================================
    # Flash Messaging Methods
    # ========================================================================
    
    def flash_success(self, message: str) -> None:
        """
        Flash success message.
        
        Args:
            message: Success message to display
        """
        flash(message, 'success')
    
    def flash_error(self, message: str) -> None:
        """
        Flash error message.
        
        Args:
            message: Error message to display
        """
        flash(message, 'error')
    
    def flash_warning(self, message: str) -> None:
        """
        Flash warning message.
        
        Args:
            message: Warning message to display
        """
        flash(message, 'warning')
    
    def flash_info(self, message: str) -> None:
        """
        Flash info message.
        
        Args:
            message: Info message to display
        """
        flash(message, 'info')
    
    # ========================================================================
    # Error Handling Methods
    # ========================================================================
    
    def handle_error(
        self,
        error: Exception,
        user_message: Optional[str] = None,
        log_error: bool = True,
        return_json: bool = False
    ) -> Union[Tuple[Dict[str, Any], int], Any]:
        """
        Handle exception with logging and user-friendly response.
        
        Args:
            error: The exception that occurred
            user_message: Optional user-friendly message
            log_error: Whether to log the error (default True)
            return_json: Whether to return JSON response (default False)
            
        Returns:
            JSON error response or redirect to referrer
            
        Example:
            >>> try:
            ...     risky_operation()
            ... except Exception as e:
            ...     return self.handle_error(
            ...         e,
            ...         user_message='Operation failed',
            ...         return_json=True
            ...     )
        """
        # Log error if requested
        if log_error:
            error_details = traceback.format_exc()
            print(f"❌ ERROR: {str(error)}")
            print(f"   Details: {error_details}")
        
        # Determine message to show user
        message = user_message or str(error)
        
        # Return appropriate response
        if return_json:
            return self.json_error(message)
        else:
            self.flash_error(message)
            return redirect(url_for('dashboard'))
    
    def validate_required_fields(
        self,
        data: Dict[str, Any],
        required_fields: list,
        return_json: bool = True
    ) -> Optional[Tuple[Dict[str, Any], int]]:
        """
        Validate that required fields are present in data.
        
        Args:
            data: Dictionary to validate
            required_fields: List of required field names
            return_json: Whether to return JSON error (default True)
            
        Returns:
            None if valid, error response if invalid
            
        Example:
            >>> error = self.validate_required_fields(
            ...     request.get_json(), ['name', 'email']
            ... )
            >>> if error:
            ...     return error
        """
        missing_fields = [
            field for field in required_fields
            if field not in data or not data[field]
        ]
        
        if missing_fields:
            message = f"Missing required fields: {', '.join(missing_fields)}"
            if return_json:
                return self.json_error(message, status_code=400)
            else:
                self.flash_error(message)
                return redirect(url_for('dashboard'))
        
        return None
    
    # ========================================================================
    # File Handling Methods
    # ========================================================================
    
    def validate_file_extension(
        self,
        filename: str,
        allowed_extensions: set
    ) -> bool:
        """
        Validate file extension.
        
        Args:
            filename: Name of file to validate
            allowed_extensions: Set of allowed extensions (e.g., {'zip', 'pdf'})
            
        Returns:
            True if valid, False otherwise
            
        Example:
            >>> valid = self.validate_file_extension(
            ...     file.filename, {'zip'}
            ... )
            >>> if not valid:
            ...     return self.json_error('Invalid file type')
        """
        return (
            '.' in filename and
            filename.rsplit('.', 1)[1].lower() in allowed_extensions
        )
    
    def validate_file_size(
        self,
        file_size: int,
        max_size_mb: int = 100
    ) -> bool:
        """
        Validate file size.
        
        Args:
            file_size: Size of file in bytes
            max_size_mb: Maximum allowed size in megabytes
            
        Returns:
            True if valid, False otherwise
            
        Example:
            >>> if not self.validate_file_size(file.content_length, max_size_mb=50):
            ...     return self.json_error('File too large')
        """
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes
    
    def ensure_directory_exists(self, directory: Union[str, Path]) -> Path:
        """
        Ensure directory exists, create if necessary.
        
        Args:
            directory: Directory path
            
        Returns:
            Path object for the directory
            
        Example:
            >>> upload_dir = self.ensure_directory_exists('uploads/temp')
        """
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    # ========================================================================
    # Decorator Methods
    # ========================================================================
    
    @staticmethod
    def handle_exceptions(
        user_message: str = "An error occurred",
        return_json: bool = True
    ):
        """
        Decorator to handle exceptions in route handlers.
        
        Args:
            user_message: Message to show user on error
            return_json: Whether to return JSON response
            
        Returns:
            Decorated function
            
        Example:
            >>> @handle_exceptions("Failed to process request")
            ... def my_route():
            ...     # route logic
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Log error
                    print(f"❌ ERROR in {func.__name__}: {str(e)}")
                    print(f"   Details: {traceback.format_exc()}")
                    
                    # Return error response
                    if return_json:
                        return jsonify({
                            'success': False,
                            'error': user_message,
                            'details': str(e)
                        }), 500
                    else:
                        flash(user_message, 'error')
                        return redirect(url_for('dashboard'))
            
            return wrapper
        return decorator
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def is_ajax_request(self, request_obj) -> bool:
        """
        Check if request is AJAX/JSON request.
        
        Args:
            request_obj: Flask request object
            
        Returns:
            True if AJAX request, False otherwise
            
        Example:
            >>> if self.is_ajax_request(request):
            ...     return self.json_response(data)
            ... else:
            ...     return self.render('template.html')
        """
        return (
            request_obj.is_json or
            request_obj.headers.get('X-Requested-With') == 'XMLHttpRequest'
        )
    
    def get_pagination_params(
        self,
        request_obj,
        default_page: int = 1,
        default_per_page: int = 10
    ) -> Tuple[int, int]:
        """
        Extract pagination parameters from request.
        
        Args:
            request_obj: Flask request object
            default_page: Default page number
            default_per_page: Default items per page
            
        Returns:
            Tuple of (page, per_page)
            
        Example:
            >>> page, per_page = self.get_pagination_params(request)
            >>> items = repository.get_paginated(page, per_page)
        """
        try:
            page = int(request_obj.args.get('page', default_page))
            per_page = int(request_obj.args.get('per_page', default_per_page))
            
            # Ensure positive values
            page = max(1, page)
            per_page = max(1, min(100, per_page))  # Cap at 100
            
            return page, per_page
        except (ValueError, TypeError):
            return default_page, default_per_page
