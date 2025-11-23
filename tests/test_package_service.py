"""
Unit Tests for PackageService

Tests the PackageService methods for blueprint normalization.
"""
import json
import uuid
from tests.base_test import BaseTestCase
from models import (
    db, MergeSession, Package, AppianObject, PackageObjectTypeCount,
    ProcessModelMetadata, ProcessModelNode, ProcessModelFlow,
    ObjectDependency
)
from services.merge_assistant.package_service import PackageService


class TestPackageService(BaseTestCase):
    """Unit tests for PackageService."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.service = PackageService()

        # Create a test session
        self.session = MergeSession(
            reference_id='MRG_TEST_001',
            base_package_name='TestBase',
            customized_package_name='TestCustom',
            new_vendor_package_name='TestVendor',
            status='processing'
        )
        db.session.add(self.session)
        db.session.commit()

    def test_create_package_from_blueprint(self):
        """Test creating a Package record from blueprint."""
        blueprint_result = {
            'blueprint': {
                'metadata': {
                    'package_name': 'TestPackage',
                    'total_objects': 10,
                    'generation_time': 45.2
                }
            },
            'object_lookup': {}
        }

        package = self.service.create_package_from_blueprint(
            session_id=self.session.id,
            package_type='base',
            blueprint_result=blueprint_result
        )

        # Verify package was created
        self.assertIsNotNone(package.id)
        self.assertEqual(package.session_id, self.session.id)
        self.assertEqual(package.package_type, 'base')
        self.assertEqual(package.package_name, 'TestPackage')
        self.assertEqual(package.total_objects, 10)
        self.assertEqual(package.generation_time, 45.2)

    def test_extract_and_create_objects(self):
        """Test extracting and creating AppianObject records."""
        # Create a package
        package = Package(
            session_id=self.session.id,
            package_type='base',
            package_name='TestPackage',
            total_objects=3
        )
        db.session.add(package)
        db.session.commit()

        # Create object lookup
        object_lookup = {
            '_a-uuid1': {
                'uuid': '_a-uuid1',
                'name': 'Interface1',
                'type': 'Interface',
                'version_uuid': 'v-uuid1',
                'sail_code': 'a!textField(label: "Test")'
            },
            '_a-uuid2': {
                'uuid': '_a-uuid2',
                'name': 'ProcessModel1',
                'type': 'Process Model',
                'version_uuid': 'v-uuid2'
            },
            '_a-uuid3': {
                'uuid': '_a-uuid3',
                'name': 'Rule1',
                'type': 'Expression Rule',
                'version_uuid': 'v-uuid3',
                'sail_code': 'if(true, "yes", "no")'
            }
        }

        # Extract and create objects
        objects = self.service.extract_and_create_objects(
            package,
            object_lookup
        )

        # Verify objects were created
        self.assertEqual(len(objects), 3)

        # Verify objects in database
        db_objects = AppianObject.query.filter_by(
            package_id=package.id
        ).all()
        self.assertEqual(len(db_objects), 3)

        # Verify object details
        interface = AppianObject.query.filter_by(
            package_id=package.id,
            uuid='_a-uuid1'
        ).first()
        self.assertIsNotNone(interface)
        self.assertEqual(interface.name, 'Interface1')
        self.assertEqual(interface.object_type, 'Interface')
        self.assertIsNotNone(interface.sail_code)

    def test_extract_and_create_object_type_counts(self):
        """Test extracting and creating PackageObjectTypeCount records."""
        # Create a package
        package = Package(
            session_id=self.session.id,
            package_type='base',
            package_name='TestPackage',
            total_objects=10
        )
        db.session.add(package)
        db.session.commit()

        # Create metadata with type counts
        metadata = {
            'object_type_counts': {
                'Interface': 5,
                'Process Model': 3,
                'Expression Rule': 2
            }
        }

        # Extract and create counts
        counts = self.service.extract_and_create_object_type_counts(
            package,
            metadata
        )

        # Verify counts were created
        self.assertEqual(len(counts), 3)

        # Verify counts in database
        db_counts = PackageObjectTypeCount.query.filter_by(
            package_id=package.id
        ).all()
        self.assertEqual(len(db_counts), 3)

        # Verify specific counts
        interface_count = PackageObjectTypeCount.query.filter_by(
            package_id=package.id,
            object_type='Interface'
        ).first()
        self.assertIsNotNone(interface_count)
        self.assertEqual(interface_count.count, 5)

    def test_extract_and_create_process_models(self):
        """Test extracting and creating process model records."""
        # Create a package
        package = Package(
            session_id=self.session.id,
            package_type='base',
            package_name='TestPackage',
            total_objects=1
        )
        db.session.add(package)
        db.session.commit()

        # Create a process model object
        pm_uuid = '_a-pm-uuid1'
        appian_obj = AppianObject(
            package_id=package.id,
            uuid=pm_uuid,
            name='TestProcessModel',
            object_type='Process Model',
            version_uuid='v-pm-uuid1'
        )
        db.session.add(appian_obj)
        db.session.commit()

        # Create object lookup with process model data
        object_lookup = {
            pm_uuid: {
                'uuid': pm_uuid,
                'name': 'TestProcessModel',
                'type': 'Process Model',
                'version_uuid': 'v-pm-uuid1',
                'process_model_data': {
                    'has_enhanced_data': True,
                    'nodes': [
                        {
                            'id': 'node_1',
                            'type': 'Start Node',
                            'name': 'Start'
                        },
                        {
                            'id': 'node_2',
                            'type': 'End Node',
                            'name': 'End'
                        }
                    ],
                    'flows': [
                        {
                            'from': 'node_1',
                            'to': 'node_2'
                        }
                    ]
                }
            }
        }

        # Extract and create process models
        count = self.service.extract_and_create_process_models(
            package,
            object_lookup
        )

        # Verify process model was created
        self.assertEqual(count, 1)

        # Verify metadata
        pm_metadata = ProcessModelMetadata.query.filter_by(
            appian_object_id=appian_obj.id
        ).first()
        self.assertIsNotNone(pm_metadata)
        self.assertEqual(pm_metadata.total_nodes, 2)
        self.assertEqual(pm_metadata.total_flows, 1)

        # Verify nodes
        nodes = ProcessModelNode.query.filter_by(
            process_model_id=pm_metadata.id
        ).all()
        self.assertEqual(len(nodes), 2)

        # Verify flows
        flows = ProcessModelFlow.query.filter_by(
            process_model_id=pm_metadata.id
        ).all()
        self.assertEqual(len(flows), 1)

    def test_extract_and_create_dependencies(self):
        """Test extracting and creating ObjectDependency records."""
        # Create a package
        package = Package(
            session_id=self.session.id,
            package_type='base',
            package_name='TestPackage',
            total_objects=2
        )
        db.session.add(package)
        db.session.commit()

        # Create object lookup with dependencies
        interface_uuid = '_a-interface-uuid'
        rule_uuid = '_a-rule-uuid'

        object_lookup = {
            interface_uuid: {
                'uuid': interface_uuid,
                'name': 'TestInterface',
                'type': 'Interface',
                'sail_code': 'rule!TestRule()'
            },
            rule_uuid: {
                'uuid': rule_uuid,
                'name': 'TestRule',
                'type': 'Expression Rule',
                'sail_code': 'if(true, "yes", "no")'
            }
        }

        # Extract and create dependencies
        dependencies = self.service.extract_and_create_dependencies(
            package,
            object_lookup
        )

        # Verify dependencies were created
        self.assertGreater(len(dependencies), 0)

        # Verify dependencies in database
        db_deps = ObjectDependency.query.filter_by(
            package_id=package.id
        ).all()
        self.assertGreater(len(db_deps), 0)

    def test_create_package_with_all_data(self):
        """Test creating package with all related data."""
        blueprint_result = {
            'blueprint': {
                'metadata': {
                    'package_name': 'CompletePackage',
                    'total_objects': 2,
                    'generation_time': 30.5,
                    'object_type_counts': {
                        'Interface': 1,
                        'Expression Rule': 1
                    }
                }
            },
            'object_lookup': {
                '_a-uuid1': {
                    'uuid': '_a-uuid1',
                    'name': 'Interface1',
                    'type': 'Interface',
                    'version_uuid': 'v-uuid1',
                    'sail_code': 'a!textField(label: "Test")'
                },
                '_a-uuid2': {
                    'uuid': '_a-uuid2',
                    'name': 'Rule1',
                    'type': 'Expression Rule',
                    'version_uuid': 'v-uuid2',
                    'sail_code': 'if(true, "yes", "no")'
                }
            }
        }

        # Create package with all data
        package = self.service.create_package_with_all_data(
            session_id=self.session.id,
            package_type='base',
            blueprint_result=blueprint_result
        )

        # Verify package was created
        self.assertIsNotNone(package.id)
        self.assertEqual(package.package_name, 'CompletePackage')

        # Verify objects were created
        objects = AppianObject.query.filter_by(
            package_id=package.id
        ).all()
        self.assertEqual(len(objects), 2)

        # Verify type counts were created
        type_counts = PackageObjectTypeCount.query.filter_by(
            package_id=package.id
        ).all()
        self.assertEqual(len(type_counts), 2)

    def test_get_object_by_uuid(self):
        """Test getting object by UUID."""
        # Create a package and object
        package = Package(
            session_id=self.session.id,
            package_type='base',
            package_name='TestPackage',
            total_objects=1
        )
        db.session.add(package)
        db.session.commit()

        test_uuid = '_a-test-uuid'
        appian_obj = AppianObject(
            package_id=package.id,
            uuid=test_uuid,
            name='TestObject',
            object_type='Interface',
            version_uuid='v-test-uuid'
        )
        db.session.add(appian_obj)
        db.session.commit()

        # Get object by UUID
        found_obj = self.service.get_object_by_uuid(package.id, test_uuid)

        # Verify object was found
        self.assertIsNotNone(found_obj)
        self.assertEqual(found_obj.uuid, test_uuid)
        self.assertEqual(found_obj.name, 'TestObject')

    def test_get_objects_by_type(self):
        """Test getting objects by type."""
        # Create a package and objects
        package = Package(
            session_id=self.session.id,
            package_type='base',
            package_name='TestPackage',
            total_objects=3
        )
        db.session.add(package)
        db.session.commit()

        # Create objects of different types
        for i in range(2):
            obj = AppianObject(
                package_id=package.id,
                uuid=f'_a-interface-{i}',
                name=f'Interface{i}',
                object_type='Interface',
                version_uuid=f'v-interface-{i}'
            )
            db.session.add(obj)

        obj = AppianObject(
            package_id=package.id,
            uuid='_a-rule-1',
            name='Rule1',
            object_type='Expression Rule',
            version_uuid='v-rule-1'
        )
        db.session.add(obj)
        db.session.commit()

        # Get objects by type
        interfaces = self.service.get_objects_by_type(
            package.id,
            'Interface'
        )

        # Verify correct objects were returned
        self.assertEqual(len(interfaces), 2)
        for obj in interfaces:
            self.assertEqual(obj.object_type, 'Interface')
