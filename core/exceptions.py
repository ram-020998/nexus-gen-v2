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


class TransientException(NexusGenException):
    """
    Exception for transient failures that can be retried.
    
    Raised when an operation fails due to temporary conditions like
    network issues, database locks, or resource constraints.
    """
    pass


class XMLParsingException(ValidationException):
    """
    Exception for XML parsing errors.
    
    Raised when XML content is malformed or cannot be parsed.
    """
    def __init__(self, message: str, object_uuid: str = None, 
                 object_type: str = None):
        super().__init__(message)
        self.object_uuid = object_uuid
        self.object_type = object_type


class DatabaseTransactionException(RepositoryException):
    """
    Exception for database transaction errors.
    
    Raised when database transactions fail and need to be rolled back.
    """
    pass


class ConcurrencyException(NexusGenException):
    """
    Exception for concurrent access conflicts.
    
    Raised when multiple requests conflict with each other.
    """
    pass


class ResourceConstraintException(NexusGenException):
    """
    Exception for resource constraint issues.
    
    Raised when system resources (memory, disk, connections) are exhausted.
    """
    pass


class ThreeWayMergeException(ServiceException):
    """
    Exception for three-way merge workflow errors.
    
    Raised when the three-way merge workflow encounters errors during
    package extraction, comparison, classification, or guidance generation.
    """
    pass
