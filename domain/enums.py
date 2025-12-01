"""
Domain enums for three-way merge functionality.

These enums define the core types and states used throughout the merge process.
"""

from enum import Enum


class PackageType(Enum):
    """
    Type of Appian package in the three-way merge.

    - BASE: Vendor Base Version (Package A) - original vendor package
            before customizations
    - CUSTOMIZED: Customer Customized Version (Package B) - package with
                  customer modifications
    - NEW_VENDOR: Vendor New Version (Package C) - latest vendor package
                  with updates
    """
    BASE = 'base'
    CUSTOMIZED = 'customized'
    NEW_VENDOR = 'new_vendor'


class ChangeCategory(Enum):
    """
    Category of change identified in delta comparison (A→C).

    - NEW: Object exists in Package C but not in Package A
    - MODIFIED: Object exists in both packages but has differences
    - DEPRECATED: Object exists in Package A but not in Package C
    """
    NEW = 'NEW'
    MODIFIED = 'MODIFIED'
    DEPRECATED = 'DEPRECATED'


class Classification(Enum):
    """
    Classification of a change after analyzing vendor delta and customer
    modifications.

    - NO_CONFLICT: Change can be auto-merged
                   (vendor changed, customer didn't)
    - CONFLICT: Manual review required
                (both vendor and customer changed)
    - NEW: New object from vendor (not in base)
    - DELETED: Object removed by customer but modified by vendor
    """
    NO_CONFLICT = 'NO_CONFLICT'
    CONFLICT = 'CONFLICT'
    NEW = 'NEW'
    DELETED = 'DELETED'


class ChangeType(Enum):
    """
    Type of change made to an object.

    - ADDED: Object was added
    - MODIFIED: Object was modified
    - REMOVED: Object was removed
    """
    ADDED = 'ADDED'
    MODIFIED = 'MODIFIED'
    REMOVED = 'REMOVED'


class SessionStatus(Enum):
    """
    Status of a merge session.

    - PROCESSING: Session is being created and packages are being
                  extracted
    - READY: Session is ready for user review
    - IN_PROGRESS: User is actively reviewing changes
    - COMPLETED: User has completed the review
    - ERROR: An error occurred during processing
    """
    PROCESSING = 'processing'
    READY = 'ready'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    ERROR = 'error'
