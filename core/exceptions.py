"""
Custom exception hierarchy for NexusGen application.

This module defines a hierarchy of exceptions that can be used throughout
the application for better error handling and debugging.
"""


class NexusGenException(Exception):
    """
    Base exception for NexusGen application.
    
    All custom exceptions in the application should inherit from this class.
    """
    pass


class ServiceException(NexusGenException):
    """
    Base exception for service layer errors.
    
    Raised when business logic operations fail or encounter errors.
    """
    pass


class RepositoryException(NexusGenException):
    """
    Base exception for repository layer errors.
    
    Raised when database operations fail or encounter errors.
    """
    pass


class ValidationException(ServiceException):
    """
    Exception for validation errors in service layer.
    
    Raised when input validation fails or data does not meet requirements.
    """
    pass
