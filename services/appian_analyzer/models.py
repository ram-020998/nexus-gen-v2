"""
Data models for Appian objects
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


@dataclass
class VersionInfo:
    """Version history entry"""
    version_uuid: str
    timestamp: datetime
    author: str
    description: str = ""


class ImportChangeStatus(Enum):
    """Object change classification for version comparison"""
    NEW = "NEW"  # Object only in new version
    CHANGED = "CHANGED"  # Legitimate update
    CONFLICT_DETECTED = "CONFLICT_DETECTED"  # Version conflict
    NOT_CHANGED = "NOT_CHANGED"  # Identical versions
    NOT_CHANGED_NEW_VUUID = "NOT_CHANGED_NEW_VUUID"  # Same content
    REMOVED = "REMOVED"  # Object only in old version
    UNKNOWN = "UNKNOWN"  # Missing version info


@dataclass
class AppianObject:
    """Enhanced base class for all Appian objects"""
    uuid: str
    name: str
    object_type: str
    description: str = ""

    # New fields for enhanced extraction
    raw_xml: str = ""  # Complete raw XML content
    version_uuid: str = ""  # Current version UUID
    version_history: List[VersionInfo] = field(
        default_factory=list
    )  # Version lineage
    raw_xml_data: Dict[str, Any] = field(
        default_factory=dict
    )  # All XML elements
    diff_hash: str = ""  # Content-based hash


@dataclass
class Site(AppianObject):
    """Site object model"""
    pages: List[Dict[str, Any]] = None
    security: Dict[str, Any] = None

    def __post_init__(self):
        if self.pages is None:
            self.pages = []
        if self.security is None:
            self.security = {"roles": []}


@dataclass
class RecordType(AppianObject):
    """Record Type object model"""
    fields: List[Dict[str, Any]] = None
    relationships: List[Dict[str, Any]] = None
    actions: List[Dict[str, Any]] = None
    views: List[Dict[str, Any]] = None
    security: Dict[str, Any] = None

    def __post_init__(self):
        if self.fields is None:
            self.fields = []
        if self.relationships is None:
            self.relationships = []
        if self.actions is None:
            self.actions = []
        if self.views is None:
            self.views = []
        if self.security is None:
            self.security = {"roles": []}


@dataclass
class ProcessModel(AppianObject):
    """Process Model object model"""
    variables: List[Dict[str, Any]] = None
    nodes: List[Dict[str, Any]] = None
    flows: List[Dict[str, Any]] = None
    interfaces: List[Dict[str, Any]] = None
    rules: List[Dict[str, Any]] = None
    business_logic: str = ""
    security: Dict[str, Any] = None

    def __post_init__(self):
        if self.variables is None:
            self.variables = []
        if self.nodes is None:
            self.nodes = []
        if self.flows is None:
            self.flows = []
        if self.interfaces is None:
            self.interfaces = []
        if self.rules is None:
            self.rules = []
        if self.security is None:
            self.security = {"roles": []}


@dataclass
class SimpleObject(AppianObject):
    """Simple object for interfaces, rules, constants, etc."""
    sail_code: str = ""
    security: Dict[str, Any] = None

    def __post_init__(self):
        if self.security is None:
            self.security = {"roles": []}


@dataclass
class Blueprint:
    """Main blueprint container"""
    metadata: Dict[str, Any]
    sites: List[Site]
    record_types: List[RecordType]
    process_models: List[ProcessModel]
    interfaces: List[SimpleObject]
    rules: List[SimpleObject]
    data_types: List[SimpleObject]
    integrations: List[SimpleObject]
    security_groups: List[SimpleObject]
    constants: List[SimpleObject]
    summary: Dict[str, Any]


@dataclass
class ComparisonResult:
    """Result of object comparison"""
    status: ImportChangeStatus
    obj: AppianObject
    old_obj: Optional[AppianObject] = None  # Store old object for comparison
    version_info: Dict[str, Any] = None
    content_diff: Optional[str] = None
    diagnostics: List[str] = field(default_factory=list)


@dataclass
class EnhancedComparisonReport:
    """Comprehensive comparison report"""
    summary: Dict[str, Any]
    changes_by_status: Dict[ImportChangeStatus, List[ComparisonResult]]
    changes_by_category: Dict[str, Dict[str, int]]
    detailed_changes: List[ComparisonResult]
    impact_assessment: Dict[str, Any]
    diagnostics: List[str] = field(default_factory=list)
