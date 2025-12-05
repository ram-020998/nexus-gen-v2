"""
Dependency injection container for NexusGen application.

This module provides a simple dependency injection container that manages
service and repository instances, supporting singleton patterns and
lazy initialization.
"""

from typing import Dict, Type, Any, Optional


class DependencyContainer:
    """
    Simple dependency injection container.
    
    Manages service and repository instances with singleton pattern support.
    Provides lazy initialization and type-safe dependency resolution.
    
    Example:
        >>> container = DependencyContainer.get_instance()
        >>> container.register_service(MyService)
        >>> service = container.get_service(MyService)
    """
    
    _instance: Optional['DependencyContainer'] = None
    
    def __init__(self):
        """
        Initialize the dependency container.
        
        Note: Use get_instance() instead of direct instantiation to ensure
        singleton behavior.
        """
        self._services: Dict[Type, Any] = {}
        self._repositories: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
    
    @classmethod
    def get_instance(cls) -> 'DependencyContainer':
        """
        Get singleton instance of the dependency container.
        
        Returns:
            DependencyContainer: The singleton container instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance.
        
        Useful for testing to ensure clean state between tests.
        """
        cls._instance = None
    
    def register_service(self, service_class: Type, instance: Any = None) -> None:
        """
        Register a service class or instance.
        
        Args:
            service_class: The service class type to register
            instance: Optional pre-instantiated service instance.
                     If None, class will be instantiated on
                     first access.
        """
        if instance:
            self._services[service_class] = instance
        else:
            self._services[service_class] = service_class
    
    def register_repository(self, repo_class: Type, instance: Any = None) -> None:
        """
        Register a repository class or instance.
        
        Args:
            repo_class: The repository class type to register
            instance: Optional pre-instantiated repository instance.
                     If None, class will be instantiated on
                     first access.
        """
        if instance:
            self._repositories[repo_class] = instance
        else:
            self._repositories[repo_class] = repo_class
    
    def get_service(self, service_class: Type) -> Any:
        """
        Get service instance (singleton pattern).
        
        If the service hasn't been instantiated yet, it will be created
        and cached for future requests.
        
        Args:
            service_class: The service class type to retrieve
            
        Returns:
            Any: The service instance
        """
        if service_class not in self._singletons:
            service = self._services.get(service_class, service_class)
            if isinstance(service, type):
                service = service(self)
            self._singletons[service_class] = service
        return self._singletons[service_class]
    
    def get_repository(self, repo_class: Type) -> Any:
        """
        Get repository instance (singleton pattern).
        
        If the repository hasn't been instantiated yet, it will be created
        and cached for future requests.
        
        Args:
            repo_class: The repository class type to retrieve
            
        Returns:
            Any: The repository instance
        """
        if repo_class not in self._singletons:
            repo = self._repositories.get(repo_class, repo_class)
            if isinstance(repo, type):
                repo = repo()
            self._singletons[repo_class] = repo
        return self._singletons[repo_class]
    
    def clear_singletons(self) -> None:
        """
        Clear all cached singleton instances.
        
        Useful for testing or when you need to force re-initialization
        of services and repositories.
        """
        self._singletons.clear()
