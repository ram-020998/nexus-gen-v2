"""
Test for Task 18: Verify database fixtures work with package_id.

This test verifies that the updated database fixtures correctly create
objects with package_id.
"""
import pytest
from tests.base_test import BaseTestCase
from tests.test_utilities.database_fixtures import (
    DatabaseFixtureBuilder,
    create_test_object_with_package,
    create_test_packages
)
from models import db, Package, ObjectLookup, Interface, MergeSession
from repositories import ObjectLookupRepository


class TestTask18Fixtures(BaseTestCase):
    """Test database fixtures with package_id support."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a merge session
        self.session = MergeSession(
            reference_id='MS_TEST001',
            status='in_progress'
        )
        db.session.add(self.session)
        db.session.flush()
    
    def test_create_interface_with_package(self):
        """Test creating an interface with package_id using fixtures."""
        # Create a package
        package = Package(
            session_id=self.session.id,
            package_type='base',
            filename='test_package.zip',
            total_objects=0
        )
        db.session.add(package)
        db.session.flush()
        
        # Create object_lookup
        obj_lookup_repo = ObjectLookupRepository()
        obj_lookup = obj_lookup_repo.find_or_create(
            uuid='test-interface-uuid',
            name='Test Interface',
            object_type='Interface'
        )
        db.session.flush()
        
        # Create interface with package_id using fixture
        builder = DatabaseFixtureBuilder()
        interface = builder.create_interface_with_package(
            object_id=obj_lookup.id,
            package_id=package.id,
            uuid='test-interface-uuid',
            name='Test Interface',
            version_uuid='v1',
            sail_code='a!localVariables()',
            description='Test interface'
        )
        db.session.commit()
        
        # Verify
        self.assertIsNotNone(interface)
        self.assertEqual(interface.object_id, obj_lookup.id)
        self.assertEqual(interface.package_id, package.id)
        self.assertEqual(interface.uuid, 'test-interface-uuid')
        self.assertEqual(interface.name, 'Test Interface')
        self.assertEqual(interface.version_uuid, 'v1')
        self.assertEqual(interface.sail_code, 'a!localVariables()')
        
        # Verify we can query by object_id and package_id
        retrieved = Interface.query.filter_by(
            object_id=obj_lookup.id,
            package_id=package.id
        ).first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, interface.id)
    
    def test_create_test_object_with_package_convenience_function(self):
        """Test the convenience function for creating objects with package_id."""
        # Create a package
        package = Package(
            session_id=self.session.id,
            package_type='customized',
            filename='test_package_2.zip',
            total_objects=0
        )
        db.session.add(package)
        db.session.flush()
        
        # Use convenience function
        obj_lookup_id, interface = create_test_object_with_package(
            object_type='Interface',
            package_id=package.id,
            uuid='test-interface-2',
            name='Test Interface 2',
            version_uuid='v2',
            sail_code='a!textField()',
            description='Another test interface'
        )
        db.session.commit()
        
        # Verify object_lookup was created
        obj_lookup = ObjectLookup.query.get(obj_lookup_id)
        self.assertIsNotNone(obj_lookup)
        self.assertEqual(obj_lookup.uuid, 'test-interface-2')
        self.assertEqual(obj_lookup.name, 'Test Interface 2')
        self.assertEqual(obj_lookup.object_type, 'Interface')
        
        # Verify interface was created with package_id
        self.assertIsNotNone(interface)
        self.assertEqual(interface.object_id, obj_lookup_id)
        self.assertEqual(interface.package_id, package.id)
        self.assertEqual(interface.uuid, 'test-interface-2')
        self.assertEqual(interface.version_uuid, 'v2')
    
    def test_create_multiple_object_types_with_package(self):
        """Test creating different object types with package_id."""
        # Create a package
        package = Package(
            session_id=self.session.id,
            package_type='new_vendor',
            filename='test_package_3.zip',
            total_objects=0
        )
        db.session.add(package)
        db.session.flush()
        
        # Create different object types
        obj_types = [
            ('Interface', {'sail_code': 'a!localVariables()'}),
            ('Expression Rule', {'sail_code': 'rule!test()', 'output_type': 'Text'}),
            ('Process Model', {'total_nodes': 5, 'total_flows': 4}),
            ('Record Type', {'source_type': 'database'}),
            ('CDT', {'namespace': 'com.example'}),
            ('Integration', {'endpoint': 'https://api.example.com'}),
            ('Web API', {'endpoint': '/api/test'}),
            ('Site', {}),
            ('Group', {}),
            ('Constant', {'constant_value': '100'}),
            ('Connected System', {'system_type': 'HTTP'}),
            ('Data Store', {}),
        ]
        
        for i, (obj_type, kwargs) in enumerate(obj_types):
            obj_lookup_id, obj = create_test_object_with_package(
                object_type=obj_type,
                package_id=package.id,
                uuid=f'test-{obj_type.lower().replace(" ", "-")}-{i}',
                name=f'Test {obj_type} {i}',
                **kwargs
            )
            db.session.flush()
            
            # Verify object was created with package_id
            self.assertIsNotNone(obj)
            self.assertEqual(obj.object_id, obj_lookup_id)
            self.assertEqual(obj.package_id, package.id)
        
        db.session.commit()
    
    def test_create_test_packages_function(self):
        """Test the create_test_packages convenience function."""
        # Create test packages with objects
        base_id, cust_id, vendor_id = create_test_packages(
            session_id=self.session.id,
            num_objects=3
        )
        
        # Verify packages were created
        base_pkg = Package.query.get(base_id)
        cust_pkg = Package.query.get(cust_id)
        vendor_pkg = Package.query.get(vendor_id)
        
        self.assertIsNotNone(base_pkg)
        self.assertIsNotNone(cust_pkg)
        self.assertIsNotNone(vendor_pkg)
        
        self.assertEqual(base_pkg.package_type, 'base')
        self.assertEqual(cust_pkg.package_type, 'customized')
        self.assertEqual(vendor_pkg.package_type, 'new_vendor')
        
        # Verify interfaces were created with package_id
        base_interfaces = Interface.query.filter_by(package_id=base_id).all()
        cust_interfaces = Interface.query.filter_by(package_id=cust_id).all()
        vendor_interfaces = Interface.query.filter_by(package_id=vendor_id).all()
        
        self.assertEqual(len(base_interfaces), 3)
        self.assertEqual(len(cust_interfaces), 3)
        self.assertEqual(len(vendor_interfaces), 3)
        
        # Verify each interface has correct package_id
        for interface in base_interfaces:
            self.assertEqual(interface.package_id, base_id)
        
        for interface in cust_interfaces:
            self.assertEqual(interface.package_id, cust_id)
        
        for interface in vendor_interfaces:
            self.assertEqual(interface.package_id, vendor_id)
        
        # Verify object_lookup entries exist (should be 3 unique objects)
        obj_lookups = ObjectLookup.query.all()
        self.assertEqual(len(obj_lookups), 3)
    
    def test_unique_constraint_on_object_package(self):
        """Test that unique constraint prevents duplicate (object_id, package_id)."""
        # Create a package
        package = Package(
            session_id=self.session.id,
            package_type='base',
            filename='test_package.zip',
            total_objects=0
        )
        db.session.add(package)
        db.session.flush()
        
        # Create first interface
        obj_lookup_id, interface1 = create_test_object_with_package(
            object_type='Interface',
            package_id=package.id,
            uuid='test-duplicate',
            name='Test Duplicate',
            sail_code='a!localVariables()'
        )
        db.session.commit()
        
        # Attempt to create duplicate (same object_id + package_id)
        from sqlalchemy.exc import IntegrityError
        
        builder = DatabaseFixtureBuilder()
        
        with self.assertRaises(IntegrityError):
            interface2 = builder.create_interface_with_package(
                object_id=obj_lookup_id,
                package_id=package.id,
                uuid='test-duplicate',
                name='Test Duplicate',
                sail_code='a!localVariables()'
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
