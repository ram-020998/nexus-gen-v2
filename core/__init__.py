"""
Core infrastructure module for NexusGen application.

This module provides base classes and utilities for implementing
clean, modular, object-oriented design patterns throughout the application.
"""

from core.base_service import BaseService
from core.base_repository import BaseRepository
from core.dependency_container import DependencyContainer
from core.exceptions import (
    NexusGenException,
    ServiceException,
    RepositoryException,
    ValidationException
)

__all__ = [
    'BaseService',
    'BaseRepository',
    'DependencyContainer',
    'NexusGenException',
    'ServiceException',
    'RepositoryException',
    'ValidationException'
]
