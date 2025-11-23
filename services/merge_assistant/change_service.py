"""
Change Service - Backward compatibility wrapper

This module maintains the original import path while delegating to the
new refactored implementation in services.merge.change_service.

The service has been refactored to use dependency injection and the
repository pattern. This wrapper ensures existing code continues to work.
"""

# Import the refactored service
from services.merge.change_service import ChangeService

# Export for backward compatibility
__all__ = ['ChangeService']
