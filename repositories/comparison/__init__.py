"""
Comparison Repositories

Provides data access for comparison result entities.
Stores detailed differences for object-specific comparisons.
"""

from repositories.comparison.interface_comparison_repository import (
    InterfaceComparisonRepository
)
from repositories.comparison.process_model_comparison_repository import (
    ProcessModelComparisonRepository
)
from repositories.comparison.record_type_comparison_repository import (
    RecordTypeComparisonRepository
)

__all__ = [
    'InterfaceComparisonRepository',
    'ProcessModelComparisonRepository',
    'RecordTypeComparisonRepository',
]
