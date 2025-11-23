"""
Unit Tests for MigrationService

Tests the migration of MergeSession data from JSON-based schema
to normalized relational schema.
"""
import json
import pytest
from tests.base_test import BaseTestCase
from models import (
    db, MergeSession, Package, AppianObject, Change, ChangeReview
)
from services.merge_assistant.migration_service import MigrationService, MigrationError


class TestMigrationService(BaseTestCase):
    """Unit tests for MigrationService"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.service = MigrationService()
    
    def test_migrate_session_basic(self):
        """Test basic session migration"""
        # Create a session with minimal JSON data
        session = MergeSession(
            reference_id='MRG_TEST_001',
            base_package_name='Base Package',
            customized_package_name='Custom Package',
            new_vendor_package_name='Vendor Package',
            status='ready',
            total_changes=0,
            base_blueprint=json.dumps({
                'blueprint': {'metadata': {'total_objects': 2, 'package_name': 'Base Package'}},
                'object_lookup': {
                    'uuid_1': {
                        'uuid': 'uuid_1',
                        'name': 'Object1',
                        'object_type': 'Interface'
                    },
                    'uuid_2': {
                        'uuid': 'uuid_2',
                        'name': 'Object2',
                        'object_type': 'Process Model'
                    }
                }
            }),
            customized_blueprint=json.dumps({
                'blueprint': {'metadata': {'total_objects': 2, 'package_name': 'Custom Package'}},
                'object_lookup': {
                    'uuid_1': {
                        'uuid': 'uuid_1',
                        'name': 'Object1',
                        'object_type': 'Interface'
                    },
                    'uuid_2': {
                        'uuid': 'uuid_2',
                        'name': 'Object2',
                        'object_type': 'Process Model'
                    }
                }
            }),
            new_vendor_blueprint=json.dumps({
                'blueprint': {'metadata': {'total_objects': 2, 'package_name': 'Vendor Package'}},
                'object_lookup': {
                    'uuid_1': {
                        'uuid': 'uuid_1',
                        'name': 'Object1',
                        'object_type': 'Interface'
                    },
                    'uuid_2': {
                        'uuid': 'uuid_2',
                        'name': 'Object2',
                        'object_type': 'Process Model'
                    }
                }
            }),
            ordered_changes=json.dumps([]),
            classification_results=json.dumps({}),
            vendor_changes=json.dumps({'added': [], 'modified': [], 'removed': []}),
            customer_changes=json.dumps({'added': [], 'modified': [], 'removed': []})
        )
        
        db.session.add(session)
        db.session.commit()
        session_id = session.id
        
        # Migrate the session
        success = self.service.migrate_session(session_id)
        
        # Verify migration succeeded
        assert success, "Migration should succeed"
        
        # Verify packages were created
        packages = Package.query.filter_by(session_id=session_id).all()
        assert len(packages) == 3, "Should have 3 packages"
        
        # Verify objects were created
        total_objects = AppianObject.query.join(Package).filter(
            Package.session_id == session_id
        ).count()
        assert total_objects == 6, f"Should have 6 objects (2 per package), got {total_objects}"
        
        # Verify no changes (since ordered_changes was empty)
        changes = Change.query.filter_by(session_id=session_id).all()
        assert len(changes) == 0, "Should have no changes"
    
    def test_migrate_session_with_changes(self):
        """Test session migration with changes"""
        # Create a session with changes
        session = MergeSession(
            reference_id='MRG_TEST_002',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor',
            total_changes=2,
            base_blueprint=json.dumps({
                'blueprint': {'metadata': {'total_objects': 1, 'package_name': 'Base'}},
                'object_lookup': {
                    'uuid_1': {'uuid': 'uuid_1', 'name': 'Obj1', 'object_type': 'Interface'}
                }
            }),
            customized_blueprint=json.dumps({
                'blueprint': {'metadata': {'total_objects': 1, 'package_name': 'Custom'}},
                'object_lookup': {
                    'uuid_1': {'uuid': 'uuid_1', 'name': 'Obj1', 'object_type': 'Interface'}
                }
            }),
            new_vendor_blueprint=json.dumps({
                'blueprint': {'metadata': {'total_objects': 1, 'package_name': 'Vendor'}},
                'object_lookup': {
                    'uuid_1': {'uuid': 'uuid_1', 'name': 'Obj1', 'object_type': 'Interface'}
                }
            }),
            ordered_changes=json.dumps([
                {
                    'uuid': 'uuid_1',
                    'name': 'Obj1',
                    'type': 'Interface',
                    'classification': 'NO_CONFLICT',
                    'change_type': 'MODIFIED'
                },
                {
                    'uuid': 'uuid_2',
                    'name': 'Obj2',
                    'type': 'Process Model',
                    'classification': 'CONFLICT',
                    'change_type': 'ADDED'
                }
            ]),
            classification_results=json.dumps({
                'NO_CONFLICT': [{'uuid': 'uuid_1'}],
                'CONFLICT': [{'uuid': 'uuid_2'}]
            }),
            vendor_changes=json.dumps({'added': [], 'modified': [], 'removed': []}),
            customer_changes=json.dumps({'added': [], 'modified': [], 'removed': []})
        )
        
        db.session.add(session)
        db.session.commit()
        session_id = session.id
        
        # Migrate the session
        success = self.service.migrate_session(session_id)
        
        # Verify migration succeeded
        assert success, "Migration should succeed"
        
        # Verify changes were created
        changes = Change.query.filter_by(session_id=session_id).order_by(Change.display_order).all()
        assert len(changes) == 2, f"Should have 2 changes, got {len(changes)}"
        
        # Verify change order
        assert changes[0].object_uuid == 'uuid_1'
        assert changes[0].classification == 'NO_CONFLICT'
        assert changes[1].object_uuid == 'uuid_2'
        assert changes[1].classification == 'CONFLICT'
    
    def test_verify_migration(self):
        """Test migration verification"""
        # Create and migrate a session
        session = MergeSession(
            reference_id='MRG_TEST_003',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor',
            total_changes=0,
            base_blueprint=json.dumps({
                'blueprint': {'metadata': {'total_objects': 1, 'package_name': 'Base'}},
                'object_lookup': {
                    'uuid_1': {'uuid': 'uuid_1', 'name': 'Obj1', 'object_type': 'Interface'}
                }
            }),
            customized_blueprint=json.dumps({
                'blueprint': {'metadata': {'total_objects': 1, 'package_name': 'Custom'}},
                'object_lookup': {
                    'uuid_1': {'uuid': 'uuid_1', 'name': 'Obj1', 'object_type': 'Interface'}
                }
            }),
            new_vendor_blueprint=json.dumps({
                'blueprint': {'metadata': {'total_objects': 1, 'package_name': 'Vendor'}},
                'object_lookup': {
                    'uuid_1': {'uuid': 'uuid_1', 'name': 'Obj1', 'object_type': 'Interface'}
                }
            }),
            ordered_changes=json.dumps([]),
            classification_results=json.dumps({}),
            vendor_changes=json.dumps({'added': [], 'modified': [], 'removed': []}),
            customer_changes=json.dumps({'added': [], 'modified': [], 'removed': []})
        )
        
        db.session.add(session)
        db.session.commit()
        session_id = session.id
        
        # Migrate
        self.service.migrate_session(session_id)
        
        # Verify
        verification = self.service.verify_migration(session_id)
        
        # Check all verification results
        assert verification['package_count'], "Package count should be correct"
        assert verification['object_count'], "Object count should be correct"
        assert verification['change_count'], "Change count should be correct"
        assert verification['review_count'], "Review count should be correct"
        assert verification['foreign_keys'], "Foreign keys should be valid"
    
    def test_migrate_session_already_migrated(self):
        """Test that migrating an already-migrated session is skipped"""
        # Create and migrate a session
        session = MergeSession(
            reference_id='MRG_TEST_004',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor',
            total_changes=0,
            base_blueprint=json.dumps({
                'blueprint': {'metadata': {'total_objects': 1, 'package_name': 'Base'}},
                'object_lookup': {
                    'uuid_1': {'uuid': 'uuid_1', 'name': 'Obj1', 'object_type': 'Interface'}
                }
            }),
            customized_blueprint=json.dumps({
                'blueprint': {'metadata': {'total_objects': 1, 'package_name': 'Custom'}},
                'object_lookup': {
                    'uuid_1': {'uuid': 'uuid_1', 'name': 'Obj1', 'object_type': 'Interface'}
                }
            }),
            new_vendor_blueprint=json.dumps({
                'blueprint': {'metadata': {'total_objects': 1, 'package_name': 'Vendor'}},
                'object_lookup': {
                    'uuid_1': {'uuid': 'uuid_1', 'name': 'Obj1', 'object_type': 'Interface'}
                }
            }),
            ordered_changes=json.dumps([]),
            classification_results=json.dumps({}),
            vendor_changes=json.dumps({'added': [], 'modified': [], 'removed': []}),
            customer_changes=json.dumps({'added': [], 'modified': [], 'removed': []})
        )
        
        db.session.add(session)
        db.session.commit()
        session_id = session.id
        
        # First migration
        success1 = self.service.migrate_session(session_id)
        assert success1, "First migration should succeed"
        
        # Count packages after first migration
        package_count1 = Package.query.filter_by(session_id=session_id).count()
        
        # Second migration (should be skipped)
        success2 = self.service.migrate_session(session_id)
        assert success2, "Second migration should succeed (skipped)"
        
        # Count packages after second migration (should be same)
        package_count2 = Package.query.filter_by(session_id=session_id).count()
        assert package_count1 == package_count2, "Package count should not change on re-migration"
    
    def test_migrate_session_invalid_json(self):
        """Test migration with invalid JSON"""
        # Create a session with invalid JSON
        session = MergeSession(
            reference_id='MRG_TEST_005',
            base_package_name='Base',
            customized_package_name='Custom',
            new_vendor_package_name='Vendor',
            base_blueprint='invalid json',
            customized_blueprint='{}',
            new_vendor_blueprint='{}',
            ordered_changes='[]',
            classification_results='{}',
            vendor_changes='{}',
            customer_changes='{}'
        )
        
        db.session.add(session)
        db.session.commit()
        session_id = session.id
        
        # Migration should fail
        with pytest.raises(MigrationError):
            self.service.migrate_session(session_id)
