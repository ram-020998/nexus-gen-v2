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
class DeltaChange:
    """
    Represents a change identified in the delta comparison (A→C).

    This captures what changed in the vendor package between the base
    version and the new version.

    Attributes:
        object_id: Database ID of the object in object_lookup
        change_category: Type of change (NEW, MODIFIED, DEPRECATED)
        version_changed: Whether the version UUID changed
        content_changed: Whether the content changed (when version is same)
    """
    object_id: int
    change_category: ChangeCategory
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


@dataclass
class CustomerModification:
    """
    Represents customer modifications to an object.

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
class ClassifiedChange:
    """
    Represents a classified change ready for the working set.

    This is the result of applying classification rules to a delta change
    combined with customer modification data.

    Attributes:
        object_id: Database ID of the object in object_lookup
        classification: Classification result
                       (NO_CONFLICT, CONFLICT, NEW, DELETED)
        vendor_change_type: Type of vendor change
                           (ADDED, MODIFIED, REMOVED)
        customer_change_type: Type of customer change (optional)
        display_order: Order for presenting changes to user
    """
    object_id: int
    classification: Classification
    vendor_change_type: ChangeType
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
        if not isinstance(self.vendor_change_type, ChangeType):
            raise ValueError(
                "vendor_change_type must be a ChangeType enum"
            )
        if (self.customer_change_type is not None and
                not isinstance(self.customer_change_type, ChangeType)):
            raise ValueError(
                "customer_change_type must be a ChangeType enum or None"
            )
        if self.display_order < 0:
            raise ValueError("display_order must be non-negative")
