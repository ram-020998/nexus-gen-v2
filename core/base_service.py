"""
Base service class for business logic layer.

This module provides a base service class that supports dependency injection
and provides common functionality for all services.
"""

from abc import ABC
from typing import Optional, Type, Any
from core.dependency_container import DependencyContainer


class BaseService(ABC):
    """
    Base class for all services providing common functionality.
    
    This class provides dependency injection support and common utilities
    that can be used by all service implementations. Services should inherit
    from this class and override _initialize_dependencies() to inject
    specific dependencies.
    
    Example:
        >>> class UserService(BaseService):
        ...     def _initialize_dependencies(self):
        ...         self.user_repo = self._get_repository(UserRepository)
        ...         self.email_service = self._get_service(EmailService)
        ...     
        ...     def create_user(self, name: str, email: str) -> User:
        ...         user = self.user_repo.create(name=name, email=email)
        ...         self.email_service.send_welcome_email(user)
        ...         return user
    """
    
    def __init__(self, container: Optional[DependencyContainer] = None):
        """
        Initialize service with dependency container.
        
        Args:
            container: Dependency injection container. If None, uses the
                      singleton instance.
        """
        self._container = container or DependencyContainer.get_instance()
        self._initialize_dependencies()
    
    def _initialize_dependencies(self) -> None:
        """
        Initialize service dependencies.
        
        Override this method in subclasses to inject specific dependencies
        using _get_repository() and _get_service().
        
        Example:
            >>> def _initialize_dependencies(self):
            ...     self.user_repo = self._get_repository(UserRepository)
            ...     self.auth_service = self._get_service(AuthService)
        """
        pass
    
    def _get_repository(self, repository_class: Type[Any]) -> Any:
        """
        Get repository instance from container.
        
        Args:
            repository_class: The repository class type to retrieve
            
        Returns:
            Any: The repository instance
            
        Example:
            >>> user_repo = self._get_repository(UserRepository)
        """
        return self._container.get_repository(repository_class)
    
    def _get_service(self, service_class: Type[Any]) -> Any:
        """
        Get service instance from container.
        
        Args:
            service_class: The service class type to retrieve
            
        Returns:
            Any: The service instance
            
        Example:
            >>> email_service = self._get_service(EmailService)
        """
        return self._container.get_service(service_class)
