"""
Domain entities for three-way merge functionality.

These dataclasses represent core domain concepts and are used to pass data
between services without coupling to database models.
"""

from dataclasses import dataclass
from typing import Optional
from domain.enums import ChangeCategory, Classification, ChangeType


@dataclass
class ObjectIdentity:
    """
    Represents the identity of an Appian object.

    This is the minimal information needed to uniquely identify an object
    across packages without referencing database IDs.

    Attributes:
        uuid: Universally unique identifier for the object
        name: Human-readable name of the object
        object_type: Type of Appian object
                    (e.g., 'Interface', 'Process Model')
        description: Optional description of the object
    """
    uuid: str
    name: str
    object_type: str
    description: Optional[str] = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.uuid:
            raise ValueError("uuid is required")
        if not self.name:
            raise ValueError("name is required")
        if not self.object_type:
            raise ValueError("object_type is required")


@dataclass
class VendorChange:
    """
    Represents a change in the vendor package (Set D: A→C).
    
    This represents what the vendor changed from the base version
    to the new vendor version.

    Attributes:
        object_id: Database ID of the object in object_lookup
        change_category: Type of change (NEW, MODIFIED, DEPRECATED)
        change_type: Type of change (ADDED, MODIFIED, REMOVED)
        version_changed: Whether the version UUID changed
        content_changed: Whether the content changed
    """
    object_id: int
    change_category: ChangeCategory
    change_type: ChangeType
    version_changed: bool
    content_changed: bool

    def __post_init__(self):
        """Validate fields."""
        if self.object_id <= 0:
            raise ValueError("object_id must be positive")
        if not isinstance(self.change_category, ChangeCategory):
            raise ValueError(
                "change_category must be a ChangeCategory enum"
            )
        if not isinstance(self.change_type, ChangeType):
            raise ValueError(
                "change_type must be a ChangeType enum"
            )


@dataclass
class DeltaChange:
    """
    Legacy alias for VendorChange for backward compatibility.
    
    Represents a change identified in the delta comparison (A→C).

    This captures what changed in the vendor package between the base
    version and the new version.

    Attributes:
        object_id: Database ID of the object in object_lookup
        change_category: Type of change (NEW, MODIFIED, DEPRECATED)
        change_type: Type of change (ADDED, MODIFIED, REMOVED)
        version_changed: Whether the version UUID changed
        content_changed: Whether the content changed (when version is same)
    """
    object_id: int
    change_category: ChangeCategory
    change_type: ChangeType
    version_changed: bool
    content_changed: bool

    def __post_init__(self):
        """Validate fields."""
        if self.object_id <= 0:
            raise ValueError("object_id must be positive")
        if not isinstance(self.change_category, ChangeCategory):
            raise ValueError(
                "change_category must be a ChangeCategory enum"
            )
        if not isinstance(self.change_type, ChangeType):
            raise ValueError(
                "change_type must be a ChangeType enum"
            )


@dataclass
class CustomerChange:
    """
    Represents a change in the customer package (Set E: A→B).
    
    This represents what the customer changed from the base version
    to their customized version.

    Attributes:
        object_id: Database ID of the object in object_lookup
        change_category: Type of change (NEW, MODIFIED, DEPRECATED)
        change_type: Type of change (ADDED, MODIFIED, REMOVED)
        version_changed: Whether the version UUID changed
        content_changed: Whether the content changed
    """
    object_id: int
    change_category: ChangeCategory
    change_type: ChangeType
    version_changed: bool
    content_changed: bool

    def __post_init__(self):
        """Validate fields."""
        if self.object_id <= 0:
            raise ValueError("object_id must be positive")
        if not isinstance(self.change_category, ChangeCategory):
            raise ValueError(
                "change_category must be a ChangeCategory enum"
            )
        if not isinstance(self.change_type, ChangeType):
            raise ValueError(
                "change_type must be a ChangeType enum"
            )


@dataclass
class CustomerModification:
    """
    Legacy entity for customer modifications (deprecated).

    This captures whether and how the customer modified an object
    that appears in the vendor delta.

    Attributes:
        object_id: Database ID of the object in object_lookup
        exists_in_customer: Whether the object exists in customer package
        customer_modified: Whether customer modified the object (vs base)
        version_changed: Whether customer changed the version UUID
        content_changed: Whether customer changed the content
    """
    object_id: int
    exists_in_customer: bool
    customer_modified: bool
    version_changed: bool
    content_changed: bool

    def __post_init__(self):
        """Validate fields."""
        if self.object_id <= 0:
            raise ValueError("object_id must be positive")


@dataclass
class MergeAnalysis:
    """
    Represents the merge analysis result for an object.
    
    This combines vendor and customer changes to determine
    if there's a conflict.

    Attributes:
        object_id: Database ID of the object in object_lookup
        in_vendor_changes: Object in Set D
        in_customer_changes: Object in Set E
        vendor_change: VendorChange entity (if in Set D)
        customer_change: CustomerChange entity (if in Set E)
        classification: Classification result
    """
    object_id: int
    in_vendor_changes: bool
    in_customer_changes: bool
    vendor_change: Optional['VendorChange']
    customer_change: Optional['CustomerChange']
    classification: Classification
    
    @property
    def is_conflict(self) -> bool:
        """Check if this is a conflict (object in both D and E)."""
        return self.in_vendor_changes and self.in_customer_changes
    
    @property
    def is_vendor_only(self) -> bool:
        """Check if this is a vendor-only change (in D, not in E)."""
        return self.in_vendor_changes and not self.in_customer_changes
    
    @property
    def is_customer_only(self) -> bool:
        """Check if this is a customer-only change (in E, not in D)."""
        return not self.in_vendor_changes and self.in_customer_changes

    def __post_init__(self):
        """Validate fields."""
        if self.object_id <= 0:
            raise ValueError("object_id must be positive")
        if not isinstance(self.classification, Classification):
            raise ValueError(
                "classification must be a Classification enum"
            )


@dataclass
class ClassifiedChange:
    """
    Represents a classified change ready for the working set.

    This is the result of applying classification rules to a delta change
    combined with customer modification data.

    Attributes:
        object_id: Database ID of the object in object_lookup
        classification: Classification result
                       (NO_CONFLICT, CONFLICT, NEW, DELETED)
        vendor_change_type: Type of vendor change (optional)
        customer_change_type: Type of customer change (optional)
        display_order: Order for presenting changes to user
    """
    object_id: int
    classification: Classification
    vendor_change_type: Optional[ChangeType]
    customer_change_type: Optional[ChangeType]
    display_order: int

    def __post_init__(self):
        """Validate fields."""
        if self.object_id <= 0:
            raise ValueError("object_id must be positive")
        if not isinstance(self.classification, Classification):
            raise ValueError(
                "classification must be a Classification enum"
            )
        if (self.vendor_change_type is not None and
                not isinstance(self.vendor_change_type, ChangeType)):
            raise ValueError(
                "vendor_change_type must be a ChangeType enum or None"
            )
        if (self.customer_change_type is not None and
                not isinstance(self.customer_change_type, ChangeType)):
            raise ValueError(
                "customer_change_type must be a ChangeType enum or None"
            )
        if self.display_order < 0:
            raise ValueError("display_order must be non-negative")
