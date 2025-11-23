"""
Merge services package

This package contains refactored merge assistant services following
the repository pattern with dependency injection.
"""

from services.merge.package_service import PackageService
from services.merge.change_service import ChangeService
from services.merge.three_way_merge_service import ThreeWayMergeService

__all__ = [
    'PackageService',
    'ChangeService',
    'ThreeWayMergeService'
]
