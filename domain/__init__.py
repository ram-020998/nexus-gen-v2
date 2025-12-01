"""
Domain layer for three-way merge functionality.

This package contains domain models, enums, entities, and strategies
that represent the core business logic independent of infrastructure concerns.
"""

from domain.enums import (
    PackageType,
    ChangeCategory,
    Classification,
    ChangeType,
    SessionStatus
)

from domain.entities import (
    ObjectIdentity,
    DeltaChange,
    CustomerModification,
    ClassifiedChange
)

from domain.comparison_strategies import (
    VersionComparisonStrategy,
    ContentComparisonStrategy
)

__all__ = [
    'PackageType',
    'ChangeCategory',
    'Classification',
    'ChangeType',
    'SessionStatus',
    'ObjectIdentity',
    'DeltaChange',
    'CustomerModification',
    'ClassifiedChange',
    'VersionComparisonStrategy',
    'ContentComparisonStrategy',
]
