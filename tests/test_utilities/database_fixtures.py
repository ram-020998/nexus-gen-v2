"""
Database Fixture Utilities for Testing

Provides utilities for setting up package data in the database for tests,
replacing the need for mock blueprints.

This module supports the database-only workflow by:
1. Creating Package records with test data
2. Creating AppianObject records
3. Creating ObjectLookup entries
4. Creating object-specific records with package_id
5. Creating Change records for comparison tests
6. Providing query helpers for test assertions
"""
from typing import List, Optional, Tuple
from datetime import datetime
import json

from models import (
    db, Package, ObjectLookup, Change,
    Interface, ExpressionRule, ProcessModel, RecordType, CDT,
    Integration, WebAPI, Site, Group, Constant, ConnectedSystem,
    UnknownObject, DataStore
)


class DatabaseFixtureBuilder:
    """
    Builder for creating database fixtures for tests.
    
    Replaces mock blueprint creation with actual database records.
    """
    
    def __init__(self, session_id: Optional[int] = None):
        """
        Initialize the fixture builder.
        
        Args:
            session_id: Optional merge session ID to associate packages with
        """
        self.session_id = session_id
        self.packages = {}  # package_type -> package_id
        self.objects = {}  # package_id -> list of object_ids
    
    def create_package(
        self,
        package_type: str,
        filename: str,
        total_objects: int = 0
    ) -> int:
        """
        Create a Package record in the database.
        
        Args:
            package_type: 'base', 'customized', or 'new_vendor'
            filename: Package filename
            total_objects: Number of objects in package
            
        Returns:
            Package ID
        """
        package = Package(
            session_id=self.session_id,
            package_type=package_type,
            filename=filename,
            total_objects=total_objects
        )
        db.session.add(package)
        db.session.flush()
        
        self.packages[package_type] = package.id
        self.objects[package.id] = []
        
        return package.id
    
    def create_object_lookup(
        self,
        uuid: str,
        name: str,
        object_type: str,
        description: Optional[str] = None
    ) -> int:
        """
        Create an ObjectLookup record in the database.
        
        Args:
            uuid: Object UUID
            name: Object name
            object_type: Type of object (Interface, Expression Rule, etc.)
            description: Optional description
            
        Returns:
            ObjectLookup ID
        """
        from repositories import ObjectLookupRepository
        
        repo = ObjectLookupRepository()
        obj_lookup = repo.find_or_create(
            uuid=uuid,
            name=name,
            object_type=object_type,
            description=description
        )
        db.session.flush()
        
        return obj_lookup.id
    

    
    def create_interface_with_package(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        sail_code: Optional[str] = None,
        description: Optional[str] = None
    ) -> Interface:
        """
        Create an Interface record with package_id.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
            uuid: Interface UUID
            name: Interface name
            version_uuid: Optional version UUID
            sail_code: Optional SAIL code
            description: Optional description
            
        Returns:
            Interface object
        """
        interface = Interface(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid or f"{uuid}_v1",
            sail_code=sail_code,
            description=description
        )
        db.session.add(interface)
        db.session.flush()
        return interface
    
    def create_expression_rule_with_package(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        sail_code: Optional[str] = None,
        output_type: Optional[str] = None,
        description: Optional[str] = None
    ) -> ExpressionRule:
        """
        Create an ExpressionRule record with package_id.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
            uuid: Expression rule UUID
            name: Expression rule name
            version_uuid: Optional version UUID
            sail_code: Optional SAIL code
            output_type: Optional output type
            description: Optional description
            
        Returns:
            ExpressionRule object
        """
        rule = ExpressionRule(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid or f"{uuid}_v1",
            sail_code=sail_code,
            output_type=output_type,
            description=description
        )
        db.session.add(rule)
        db.session.flush()
        return rule
    
    def create_process_model_with_package(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        total_nodes: int = 0,
        total_flows: int = 0,
        complexity_score: Optional[float] = None
    ) -> ProcessModel:
        """
        Create a ProcessModel record with package_id.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
            uuid: Process model UUID
            name: Process model name
            version_uuid: Optional version UUID
            total_nodes: Total number of nodes
            total_flows: Total number of flows
            complexity_score: Optional complexity score
            
        Returns:
            ProcessModel object
        """
        pm = ProcessModel(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid or f"{uuid}_v1",
            total_nodes=total_nodes,
            total_flows=total_flows,
            complexity_score=complexity_score
        )
        db.session.add(pm)
        db.session.flush()
        return pm
    
    def create_record_type_with_package(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> RecordType:
        """
        Create a RecordType record with package_id.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
            uuid: Record type UUID
            name: Record type name
            version_uuid: Optional version UUID
            source_type: Optional source type
            
        Returns:
            RecordType object
        """
        rt = RecordType(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid or f"{uuid}_v1",
            source_type=source_type
        )
        db.session.add(rt)
        db.session.flush()
        return rt
    
    def create_cdt_with_package(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        namespace: Optional[str] = None
    ) -> CDT:
        """
        Create a CDT record with package_id.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
            uuid: CDT UUID
            name: CDT name
            version_uuid: Optional version UUID
            namespace: Optional namespace
            
        Returns:
            CDT object
        """
        cdt = CDT(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid or f"{uuid}_v1",
            namespace=namespace
        )
        db.session.add(cdt)
        db.session.flush()
        return cdt
    
    def create_integration_with_package(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> Integration:
        """
        Create an Integration record with package_id.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
            uuid: Integration UUID
            name: Integration name
            version_uuid: Optional version UUID
            endpoint: Optional endpoint
            
        Returns:
            Integration object
        """
        integration = Integration(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid or f"{uuid}_v1",
            endpoint=endpoint
        )
        db.session.add(integration)
        db.session.flush()
        return integration
    
    def create_web_api_with_package(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        endpoint: Optional[str] = None
    ) -> WebAPI:
        """
        Create a WebAPI record with package_id.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
            uuid: Web API UUID
            name: Web API name
            version_uuid: Optional version UUID
            endpoint: Optional endpoint
            
        Returns:
            WebAPI object
        """
        web_api = WebAPI(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid or f"{uuid}_v1",
            endpoint=endpoint
        )
        db.session.add(web_api)
        db.session.flush()
        return web_api
    
    def create_site_with_package(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None
    ) -> Site:
        """
        Create a Site record with package_id.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
            uuid: Site UUID
            name: Site name
            version_uuid: Optional version UUID
            
        Returns:
            Site object
        """
        site = Site(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid or f"{uuid}_v1"
        )
        db.session.add(site)
        db.session.flush()
        return site
    
    def create_group_with_package(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None
    ) -> Group:
        """
        Create a Group record with package_id.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
            uuid: Group UUID
            name: Group name
            version_uuid: Optional version UUID
            
        Returns:
            Group object
        """
        group = Group(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid or f"{uuid}_v1"
        )
        db.session.add(group)
        db.session.flush()
        return group
    
    def create_constant_with_package(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        constant_value: Optional[str] = None
    ) -> Constant:
        """
        Create a Constant record with package_id.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
            uuid: Constant UUID
            name: Constant name
            version_uuid: Optional version UUID
            constant_value: Optional constant value
            
        Returns:
            Constant object
        """
        constant = Constant(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid or f"{uuid}_v1",
            constant_value=constant_value
        )
        db.session.add(constant)
        db.session.flush()
        return constant
    
    def create_connected_system_with_package(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        system_type: Optional[str] = None
    ) -> ConnectedSystem:
        """
        Create a ConnectedSystem record with package_id.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
            uuid: Connected system UUID
            name: Connected system name
            version_uuid: Optional version UUID
            system_type: Optional system type
            
        Returns:
            ConnectedSystem object
        """
        cs = ConnectedSystem(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid or f"{uuid}_v1",
            system_type=system_type
        )
        db.session.add(cs)
        db.session.flush()
        return cs
    
    def create_unknown_object_with_package(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        raw_xml: Optional[str] = None
    ) -> UnknownObject:
        """
        Create an UnknownObject record with package_id.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
            uuid: Unknown object UUID
            name: Unknown object name
            version_uuid: Optional version UUID
            raw_xml: Optional raw XML
            
        Returns:
            UnknownObject object
        """
        unknown = UnknownObject(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid or f"{uuid}_v1",
            raw_xml=raw_xml
        )
        db.session.add(unknown)
        db.session.flush()
        return unknown
    
    def create_data_store_with_package(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None
    ) -> DataStore:
        """
        Create a DataStore record with package_id.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
            uuid: Data store UUID
            name: Data store name
            version_uuid: Optional version UUID
            
        Returns:
            DataStore object
        """
        ds = DataStore(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid or f"{uuid}_v1"
        )
        db.session.add(ds)
        db.session.flush()
        return ds
    
    def commit(self):
        """Commit all changes to the database."""
        db.session.commit()
    
    def get_package_id(self, package_type: str) -> Optional[int]:
        """
        Get package ID by type.
        
        Args:
            package_type: 'base', 'customized', or 'new_vendor'
            
        Returns:
            Package ID or None
        """
        return self.packages.get(package_type)
    
    def get_object_ids(self, package_id: int) -> List[int]:
        """
        Get all object IDs for a package.
        
        Args:
            package_id: Package ID
            
        Returns:
            List of AppianObject IDs
        """
        return self.objects.get(package_id, [])


class ChangeFixtureBuilder:
    """
    Builder for creating Change records for comparison tests.
    """
    
    def __init__(self, session_id: int):
        """
        Initialize the change fixture builder.
        
        Args:
            session_id: Merge session ID
        """
        self.session_id = session_id
        self.changes = []
    
    def create_change(
        self,
        uuid: str,
        name: str,
        object_type: str,
        classification: str,
        change_type: str = 'MODIFIED',
        base_object_id: Optional[int] = None,
        customer_object_id: Optional[int] = None,
        vendor_object_id: Optional[int] = None
    ) -> int:
        """
        Create a Change record.
        
        Args:
            uuid: Object UUID
            name: Object name
            object_type: Type of object
            classification: NO_CONFLICT, CONFLICT, etc.
            change_type: ADDED, MODIFIED, REMOVED
            base_object_id: Optional base version object ID
            customer_object_id: Optional customer version object ID
            vendor_object_id: Optional vendor version object ID
            
        Returns:
            Change ID
        """
        # Calculate display order
        display_order = len(self.changes)
        
        change = Change(
            session_id=self.session_id,
            object_uuid=uuid,
            object_name=name,
            object_type=object_type,
            classification=classification,
            change_type=change_type,
            base_object_id=base_object_id,
            customer_object_id=customer_object_id,
            vendor_object_id=vendor_object_id,
            display_order=display_order
        )
        db.session.add(change)
        db.session.flush()
        
        self.changes.append(change.id)
        
        return change.id
    
    def commit(self):
        """Commit all changes to the database."""
        db.session.commit()
    
    def get_change_ids(self) -> List[int]:
        """
        Get all created change IDs.
        
        Returns:
            List of Change IDs
        """
        return self.changes


class DatabaseQueryHelper:
    """
    Helper for querying database in tests.
    
    Provides convenient methods for test assertions.
    """
    
    @staticmethod
    def get_package_by_type(
        session_id: int,
        package_type: str
    ) -> Optional[Package]:
        """
        Get package by session and type.
        
        Args:
            session_id: Merge session ID
            package_type: 'base', 'customized', or 'new_vendor'
            
        Returns:
            Package or None
        """
        return db.session.query(Package).filter_by(
            session_id=session_id,
            package_type=package_type
        ).first()
    
    @staticmethod
    def get_interfaces_by_package(package_id: int) -> List[Interface]:
        """
        Get all interfaces in a package.
        
        Args:
            package_id: Package ID
            
        Returns:
            List of Interface records
        """
        return db.session.query(Interface).filter_by(
            package_id=package_id
        ).all()
    
    @staticmethod
    def get_interface_by_uuid(
        package_id: int,
        uuid: str
    ) -> Optional[Interface]:
        """
        Get interface by UUID within a package.
        
        Args:
            package_id: Package ID
            uuid: Object UUID
            
        Returns:
            Interface or None
        """
        return db.session.query(Interface).filter_by(
            package_id=package_id,
            uuid=uuid
        ).first()
    
    @staticmethod
    def get_object_count_by_type(
        package_id: int,
        object_type: str
    ) -> int:
        """
        Get count of objects by type in a package.
        
        Args:
            package_id: Package ID
            object_type: Type of object
            
        Returns:
            Count of objects
        """
        return db.session.query(ObjectLookup).filter_by(
            package_id=package_id,
            object_type=object_type
        ).count()
    
    @staticmethod
    def get_changes_by_classification(
        session_id: int,
        classification: str
    ) -> List[Change]:
        """
        Get changes by classification.
        
        Args:
            session_id: Merge session ID
            classification: Classification type
            
        Returns:
            List of Change records
        """
        return db.session.query(Change).filter_by(
            session_id=session_id,
            classification=classification
        ).all()
    
    @staticmethod
    def get_total_changes(session_id: int) -> int:
        """
        Get total number of changes in a session.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Count of changes
        """
        return db.session.query(Change).filter_by(
            session_id=session_id
        ).count()


def create_test_packages(
    session_id: int,
    num_objects: int = 5
) -> Tuple[int, int, int]:
    """
    Create a complete set of test packages with objects.
    
    This is a convenience function for quickly setting up test data.
    
    Args:
        session_id: Merge session ID
        num_objects: Number of objects to create in each package
        
    Returns:
        Tuple of (base_package_id, customized_package_id,
        new_vendor_package_id)
    """
    builder = DatabaseFixtureBuilder(session_id)
    
    # Create packages
    base_id = builder.create_package('base', 'TestBase_v1.0')
    cust_id = builder.create_package('customized', 'TestCustomized_v1.0')
    vendor_id = builder.create_package('new_vendor', 'TestVendor_v2.0')
    
    # Create objects in each package
    for i in range(num_objects):
        uuid = f"_a-test-uuid-{i:03d}"
        name = f"TestObject{i}"
        
        # Create object_lookup entry (once)
        obj_lookup_id = builder.create_object_lookup(
            uuid=uuid,
            name=name,
            object_type='Interface'
        )
        
        # Base version
        builder.create_interface_with_package(
            object_id=obj_lookup_id,
            package_id=base_id,
            uuid=uuid,
            name=name,
            sail_code=f"/* Base SAIL code for {name} */"
        )
        
        # Customized version (same as base for most)
        builder.create_interface_with_package(
            object_id=obj_lookup_id,
            package_id=cust_id,
            uuid=uuid,
            name=name,
            sail_code=f"/* Base SAIL code for {name} */"
        )
        
        # Vendor version (modified)
        builder.create_interface_with_package(
            object_id=obj_lookup_id,
            package_id=vendor_id,
            uuid=uuid,
            name=name,
            sail_code=f"/* Modified SAIL code for {name} in v2.0 */"
        )
    
    builder.commit()
    
    return (base_id, cust_id, vendor_id)


def create_test_object_with_package(
    object_type: str,
    package_id: int,
    uuid: str,
    name: str,
    **kwargs
) -> Tuple[int, object]:
    """
    Create a test object with package_id in both object_lookup and
    object-specific table.
    
    This is a convenience function for creating test objects with proper
    package_id.
    
    Args:
        object_type: Type of object (Interface, Expression Rule, etc.)
        package_id: Package ID
        uuid: Object UUID
        name: Object name
        **kwargs: Additional object-specific parameters
        
    Returns:
        Tuple of (object_lookup_id, object_specific_record)
    """
    from repositories import ObjectLookupRepository
    
    # Create object_lookup entry
    obj_lookup_repo = ObjectLookupRepository()
    obj_lookup = obj_lookup_repo.find_or_create(
        uuid=uuid,
        name=name,
        object_type=object_type
    )
    db.session.flush()
    
    # Create object-specific record with package_id
    builder = DatabaseFixtureBuilder()
    
    if object_type == 'Interface':
        obj = builder.create_interface_with_package(
            object_id=obj_lookup.id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            **kwargs
        )
    elif object_type == 'Expression Rule':
        obj = builder.create_expression_rule_with_package(
            object_id=obj_lookup.id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            **kwargs
        )
    elif object_type == 'Process Model':
        obj = builder.create_process_model_with_package(
            object_id=obj_lookup.id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            **kwargs
        )
    elif object_type == 'Record Type':
        obj = builder.create_record_type_with_package(
            object_id=obj_lookup.id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            **kwargs
        )
    elif object_type == 'CDT':
        obj = builder.create_cdt_with_package(
            object_id=obj_lookup.id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            **kwargs
        )
    elif object_type == 'Integration':
        obj = builder.create_integration_with_package(
            object_id=obj_lookup.id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            **kwargs
        )
    elif object_type == 'Web API':
        obj = builder.create_web_api_with_package(
            object_id=obj_lookup.id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            **kwargs
        )
    elif object_type == 'Site':
        obj = builder.create_site_with_package(
            object_id=obj_lookup.id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            **kwargs
        )
    elif object_type == 'Group':
        obj = builder.create_group_with_package(
            object_id=obj_lookup.id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            **kwargs
        )
    elif object_type == 'Constant':
        obj = builder.create_constant_with_package(
            object_id=obj_lookup.id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            **kwargs
        )
    elif object_type == 'Connected System':
        obj = builder.create_connected_system_with_package(
            object_id=obj_lookup.id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            **kwargs
        )
    elif object_type == 'Unknown':
        obj = builder.create_unknown_object_with_package(
            object_id=obj_lookup.id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            **kwargs
        )
    elif object_type == 'Data Store':
        obj = builder.create_data_store_with_package(
            object_id=obj_lookup.id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            **kwargs
        )
    else:
        raise ValueError(f"Unsupported object type: {object_type}")
    
    db.session.flush()
    return (obj_lookup.id, obj)
