"""
Data models for Appian objects
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

@dataclass
class AppianObject:
    """Base class for all Appian objects"""
    uuid: str
    name: str
    object_type: str
    description: str = ""

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
