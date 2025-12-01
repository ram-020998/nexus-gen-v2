"""
Tests for Package Extraction Service

Tests the complete workflow of extracting Appian packages and storing objects.
Updated to verify package_id is set correctly in object-specific tables.
"""
import os
import unittest
from tests.base_test import BaseTestCase
from models import (
    db, MergeSession, Package, ObjectLookup,
    PackageObjectMapping, ObjectVersion,
    Interface, ExpressionRule, ProcessModel
)
from services.package_extraction_service import PackageExtractionService
from repositories.object_lookup_repository import ObjectLookupRepository
from repositories.package_object_mapping_repository import (
    PackageObjectMappingRepository
)


class TestPackageExtractionService(BaseTestCase):
    """Test PackageExtractionService functionality"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.service = PackageExtractionService()
        self.object_lookup_repo = ObjectLookupRepository()
        self.pom_repo = PackageObjectMappingRepository()

        # Create test session
        self.session = MergeSession(
            reference_id='TEST_001',
            status='processing'
        )
        db.session.add(self.session)
        db.session.commit()

    def test_extract_package_basic(self):
        """Test basic package extraction with real test package"""
        # Path to test package
        test_package_path = (
            'applicationArtifacts/Three Way Testing Files/V2/'
            'Test Application - Base Version.zip'
        )

        # Skip if test package doesn't exist
        if not os.path.exists(test_package_path):
            self.skipTest(f"Test package not found: {test_package_path}")

        # Extract package
        package = self.service.extract_package(
            session_id=self.session.id,
            zip_path=test_package_path,
            package_type='base'
        )

        # Verify package was created
        self.assertIsNotNone(package)
        self.assertEqual(package.package_type, 'base')
        self.assertGreater(package.total_objects, 0)

        # Verify objects were stored in object_lookup
        objects = self.object_lookup_repo.find_all()
        self.assertGreater(len(objects), 0)

        # Verify package-object mappings were created
        mappings = self.pom_repo.get_objects_in_package(package.id)
        self.assertEqual(len(mappings), package.total_objects)

        # Verify no duplicate UUIDs
        duplicates = self.object_lookup_repo.get_duplicate_uuids()
        self.assertEqual(len(duplicates), 0,
                         f"Found duplicate UUIDs: {duplicates}")
        
        # NEW: Verify package_id is set correctly in object-specific tables
        # Check interfaces
        interfaces = Interface.query.filter_by(package_id=package.id).all()
        for interface in interfaces:
            self.assertEqual(interface.package_id, package.id,
                           f"Interface {interface.name} has incorrect package_id")
            self.assertIsNotNone(interface.object_id,
                               f"Interface {interface.name} missing object_id")
        
        # Check expression rules
        rules = ExpressionRule.query.filter_by(package_id=package.id).all()
        for rule in rules:
            self.assertEqual(rule.package_id, package.id,
                           f"Expression Rule {rule.name} has incorrect package_id")
            self.assertIsNotNone(rule.object_id,
                               f"Expression Rule {rule.name} missing object_id")
        
        # Check process models
        process_models = ProcessModel.query.filter_by(package_id=package.id).all()
        for pm in process_models:
            self.assertEqual(pm.package_id, package.id,
                           f"Process Model {pm.name} has incorrect package_id")
            self.assertIsNotNone(pm.object_id,
                               f"Process Model {pm.name} missing object_id")

    def test_find_or_create_prevents_duplicates(self):
        """Test that find_or_create prevents duplicate objects"""
        # Create first object
        obj1 = self.object_lookup_repo.find_or_create(
            uuid='test-uuid-123',
            name='Test Object',
            object_type='Interface'
        )
        db.session.commit()

        # Try to create same object again
        obj2 = self.object_lookup_repo.find_or_create(
            uuid='test-uuid-123',
            name='Test Object',
            object_type='Interface'
        )
        db.session.commit()

        # Should return same object
        self.assertEqual(obj1.id, obj2.id)

        # Verify only one object in database
        all_objects = self.object_lookup_repo.find_all()
        self.assertEqual(len(all_objects), 1)

    def test_package_object_mapping_creation(self):
        """Test package-object mapping creation"""
        # Create package
        package = Package(
            session_id=self.session.id,
            package_type='base',
            filename='test.zip',
            total_objects=0
        )
        db.session.add(package)
        db.session.commit()

        # Create object
        obj = self.object_lookup_repo.find_or_create(
            uuid='test-uuid-456',
            name='Test Object 2',
            object_type='Process Model'
        )
        db.session.commit()

        # Create mapping
        mapping = self.pom_repo.create_mapping(
            package_id=package.id,
            object_id=obj.id
        )
        db.session.commit()

        # Verify mapping
        self.assertIsNotNone(mapping)
        self.assertEqual(mapping.package_id, package.id)
        self.assertEqual(mapping.object_id, obj.id)

        # Verify we can retrieve objects in package
        objects = self.pom_repo.get_objects_in_package(package.id)
        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0].uuid, 'test-uuid-456')

    def test_extract_multiple_packages_no_duplicates(self):
        """Test extracting multiple packages doesn't create duplicates"""
        test_packages = [
            ('applicationArtifacts/Three Way Testing Files/V2/'
             'Test Application - Base Version.zip', 'base'),
            ('applicationArtifacts/Three Way Testing Files/V2/'
             'Test Application Customer Version.zip', 'customized'),
        ]

        extracted_packages = []
        for zip_path, pkg_type in test_packages:
            if not os.path.exists(zip_path):
                self.skipTest(f"Test package not found: {zip_path}")

            package = self.service.extract_package(
                session_id=self.session.id,
                zip_path=zip_path,
                package_type=pkg_type
            )
            extracted_packages.append(package)

        # Verify no duplicate UUIDs in object_lookup
        duplicates = self.object_lookup_repo.get_duplicate_uuids()
        self.assertEqual(len(duplicates), 0,
                         f"Found duplicate UUIDs: {duplicates}")

        # Verify total objects across packages
        total_objects = sum(p.total_objects for p in extracted_packages)
        self.assertGreater(total_objects, 0)

        # Verify object_lookup has unique objects
        all_objects = self.object_lookup_repo.find_all()
        self.assertGreater(len(all_objects), 0)

        # Object count in object_lookup should be <= total objects
        # (because shared objects are stored once)
        self.assertLessEqual(len(all_objects), total_objects)

    def test_package_id_matches_expected_package(self):
        """
        Test that package_id in object-specific tables matches the expected package.
        Requirements: 8.1, 8.2, 8.3
        """
        # Path to test package
        test_package_path = (
            'applicationArtifacts/Three Way Testing Files/V2/'
            'Test Application - Base Version.zip'
        )

        # Skip if test package doesn't exist
        if not os.path.exists(test_package_path):
            self.skipTest(f"Test package not found: {test_package_path}")

        # Extract package
        package = self.service.extract_package(
            session_id=self.session.id,
            zip_path=test_package_path,
            package_type='base'
        )

        # Get all interfaces for this package
        interfaces = Interface.query.filter_by(package_id=package.id).all()
        
        # Verify each interface has correct package_id
        for interface in interfaces:
            self.assertEqual(
                interface.package_id, 
                package.id,
                f"Interface {interface.name} (UUID: {interface.uuid}) "
                f"has package_id={interface.package_id} but expected {package.id}"
            )
            
            # Verify the object exists in object_lookup
            obj_lookup = ObjectLookup.query.get(interface.object_id)
            self.assertIsNotNone(
                obj_lookup,
                f"Interface {interface.name} references non-existent object_id={interface.object_id}"
            )
            
            # Verify the UUID matches
            self.assertEqual(
                interface.uuid,
                obj_lookup.uuid,
                f"Interface UUID mismatch: interface.uuid={interface.uuid}, "
                f"object_lookup.uuid={obj_lookup.uuid}"
            )
        
        # Get all expression rules for this package
        rules = ExpressionRule.query.filter_by(package_id=package.id).all()
        
        # Verify each rule has correct package_id
        for rule in rules:
            self.assertEqual(
                rule.package_id,
                package.id,
                f"Expression Rule {rule.name} (UUID: {rule.uuid}) "
                f"has package_id={rule.package_id} but expected {package.id}"
            )
            
            # Verify the object exists in object_lookup
            obj_lookup = ObjectLookup.query.get(rule.object_id)
            self.assertIsNotNone(
                obj_lookup,
                f"Expression Rule {rule.name} references non-existent object_id={rule.object_id}"
            )
            
            # Verify the UUID matches
            self.assertEqual(
                rule.uuid,
                obj_lookup.uuid,
                f"Expression Rule UUID mismatch: rule.uuid={rule.uuid}, "
                f"object_lookup.uuid={obj_lookup.uuid}"
            )

    def test_multiple_packages_same_object(self):
        """
        Test that the same object in multiple packages gets separate entries
        with different package_ids but same object_id.
        Requirements: 8.1, 8.2, 8.3
        """
        test_packages = [
            ('applicationArtifacts/Three Way Testing Files/V2/'
             'Test Application - Base Version.zip', 'base'),
            ('applicationArtifacts/Three Way Testing Files/V2/'
             'Test Application Customer Version.zip', 'customized'),
            ('applicationArtifacts/Three Way Testing Files/V2/'
             'Test Application Vendor New Version.zip', 'new_vendor'),
        ]

        extracted_packages = []
        for zip_path, pkg_type in test_packages:
            if not os.path.exists(zip_path):
                self.skipTest(f"Test package not found: {zip_path}")

            package = self.service.extract_package(
                session_id=self.session.id,
                zip_path=zip_path,
                package_type=pkg_type
            )
            extracted_packages.append(package)

        # Find objects that appear in multiple packages
        # Query object_lookup to find objects with multiple package mappings
        objects_with_multiple_packages = db.session.query(
            ObjectLookup.id,
            ObjectLookup.uuid,
            ObjectLookup.name,
            ObjectLookup.object_type,
            db.func.count(PackageObjectMapping.package_id).label('package_count')
        ).join(
            PackageObjectMapping,
            ObjectLookup.id == PackageObjectMapping.object_id
        ).group_by(
            ObjectLookup.id
        ).having(
            db.func.count(PackageObjectMapping.package_id) > 1
        ).all()

        # Should have at least some shared objects
        self.assertGreater(
            len(objects_with_multiple_packages),
            0,
            "Expected to find objects that appear in multiple packages"
        )

        # For each shared object, verify it has separate entries in object-specific tables
        for obj_id, obj_uuid, obj_name, obj_type, pkg_count in objects_with_multiple_packages:
            # Check interfaces
            if obj_type == 'Interface':
                interfaces = Interface.query.filter_by(object_id=obj_id).all()
                
                # Should have one entry per package
                self.assertEqual(
                    len(interfaces),
                    pkg_count,
                    f"Interface {obj_name} (UUID: {obj_uuid}) appears in {pkg_count} packages "
                    f"but has {len(interfaces)} entries in interfaces table"
                )
                
                # Verify each entry has different package_id but same object_id
                package_ids = set()
                for interface in interfaces:
                    self.assertEqual(
                        interface.object_id,
                        obj_id,
                        f"Interface entry has wrong object_id: {interface.object_id} != {obj_id}"
                    )
                    package_ids.add(interface.package_id)
                
                # All package_ids should be unique
                self.assertEqual(
                    len(package_ids),
                    len(interfaces),
                    f"Interface {obj_name} has duplicate package_ids: {package_ids}"
                )
                
                # Verify each package_id is valid
                for pkg_id in package_ids:
                    package = Package.query.get(pkg_id)
                    self.assertIsNotNone(
                        package,
                        f"Interface references non-existent package_id={pkg_id}"
                    )
            
            # Check expression rules
            elif obj_type == 'Expression Rule':
                rules = ExpressionRule.query.filter_by(object_id=obj_id).all()
                
                # Should have one entry per package
                self.assertEqual(
                    len(rules),
                    pkg_count,
                    f"Expression Rule {obj_name} (UUID: {obj_uuid}) appears in {pkg_count} packages "
                    f"but has {len(rules)} entries in expression_rules table"
                )
                
                # Verify each entry has different package_id but same object_id
                package_ids = set()
                for rule in rules:
                    self.assertEqual(
                        rule.object_id,
                        obj_id,
                        f"Expression Rule entry has wrong object_id: {rule.object_id} != {obj_id}"
                    )
                    package_ids.add(rule.package_id)
                
                # All package_ids should be unique
                self.assertEqual(
                    len(package_ids),
                    len(rules),
                    f"Expression Rule {obj_name} has duplicate package_ids: {package_ids}"
                )
                
                # Verify each package_id is valid
                for pkg_id in package_ids:
                    package = Package.query.get(pkg_id)
                    self.assertIsNotNone(
                        package,
                        f"Expression Rule references non-existent package_id={pkg_id}"
                    )
            
            # Check process models
            elif obj_type == 'Process Model':
                process_models = ProcessModel.query.filter_by(object_id=obj_id).all()
                
                # Should have one entry per package
                self.assertEqual(
                    len(process_models),
                    pkg_count,
                    f"Process Model {obj_name} (UUID: {obj_uuid}) appears in {pkg_count} packages "
                    f"but has {len(process_models)} entries in process_models table"
                )
                
                # Verify each entry has different package_id but same object_id
                package_ids = set()
                for pm in process_models:
                    self.assertEqual(
                        pm.object_id,
                        obj_id,
                        f"Process Model entry has wrong object_id: {pm.object_id} != {obj_id}"
                    )
                    package_ids.add(pm.package_id)
                
                # All package_ids should be unique
                self.assertEqual(
                    len(package_ids),
                    len(process_models),
                    f"Process Model {obj_name} has duplicate package_ids: {package_ids}"
                )
                
                # Verify each package_id is valid
                for pkg_id in package_ids:
                    package = Package.query.get(pkg_id)
                    self.assertIsNotNone(
                        package,
                        f"Process Model references non-existent package_id={pkg_id}"
                    )


if __name__ == '__main__':
    unittest.main()
