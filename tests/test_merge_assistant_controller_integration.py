"""
Integration Tests for Merge Assistant Controller

Tests complete workflows from upload to report generation using the normalized schema.
"""
import json
import io
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from tests.base_test import BaseTestCase


class TestMergeAssistantControllerIntegration(BaseTestCase):
    """Integration tests for merge assistant controller workflows"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        
        # Create test ZIP files
        self.base_zip = self._create_test_zip('base_package.zip')
        self.customized_zip = self._create_test_zip('customized_package.zip')
        self.vendor_zip = self._create_test_zip('new_vendor_package.zip')

    def _create_test_zip(self, filename):
        """Create a minimal test ZIP file"""
        zip_path = Path('uploads/merge_assistant') / filename
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add a minimal package.properties file
            zf.writestr('package.properties', 'name=TestPackage\nversion=1.0')
            # Add a minimal object file
            zf.writestr('objects/test_interface.xml', '<interface><name>TestInterface</name></interface>')
        
        return zip_path

    def test_complete_upload_to_summary_workflow(self):
        """Test complete workflow: create session -> view summary (uses normalized schema)"""
        from models import db, MergeSession, Package, Change
        
        # Create a session with normalized data (simulating what upload would create)
        session = MergeSession(
            reference_id='MRG_INT_001',
            base_package_name='base_package',
            customized_package_name='customized_package',
            new_vendor_package_name='new_vendor_package',
            status='ready',
            total_changes=5
        )
        db.session.add(session)
        db.session.commit()
        
        # Create packages (normalized schema)
        for pkg_type, pkg_name in [
            ('base', 'base_package'),
            ('customized', 'customized_package'),
            ('new_vendor', 'new_vendor_package')
        ]:
            package = Package(
                session_id=session.id,
                package_type=pkg_type,
                package_name=pkg_name,
                total_objects=10
            )
            db.session.add(package)
        db.session.commit()
        
        # Create some changes
        for i in range(5):
            change = Change(
                session_id=session.id,
                object_uuid=f'uuid-{i:03d}',
                object_name=f'TestObject{i}',
                object_type='Interface',
                classification='NO_CONFLICT',
                change_type='MODIFIED',
                display_order=i
            )
            db.session.add(change)
        db.session.commit()
        
        # View summary (uses SQL aggregates on normalized schema)
        response = self.client.get(
            f'/merge-assistant/session/{session.id}/summary'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MRG_INT_001', response.data)
        self.assertIn(b'base_package', response.data)
        
        # Verify API endpoint also works
        response = self.client.get(
            f'/merge-assistant/api/session/{session.id}/summary'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['reference_id'], 'MRG_INT_001')
        self.assertEqual(data['statistics']['total_changes'], 5)

    def test_complete_filtering_workflow(self):
        """Test complete filtering workflow (uses indexed SQL WHERE clauses)"""
        from models import db, MergeSession, Package, AppianObject, Change
        
        # Create test session with normalized data
        session = MergeSession(
            reference_id='MRG_FILTER_001',
            base_package_name='BasePackage',
            customized_package_name='CustomizedPackage',
            new_vendor_package_name='NewVendorPackage',
            status='ready',
            total_changes=10
        )
        db.session.add(session)
        db.session.commit()
        
        # Create package
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='BasePackage',
            total_objects=10
        )
        db.session.add(package)
        db.session.commit()
        
        # Create test changes with different classifications and types
        changes = []
        for i in range(10):
            classification = ['NO_CONFLICT', 'CONFLICT', 'CUSTOMER_ONLY'][i % 3]
            obj_type = ['Interface', 'Expression Rule', 'Record Type'][i % 3]
            
            change = Change(
                session_id=session.id,
                object_uuid=f'uuid-{i:03d}',
                object_name=f'TestObject{i}',
                object_type=obj_type,
                classification=classification,
                change_type='MODIFIED',
                display_order=i
            )
            changes.append(change)
        
        db.session.add_all(changes)
        db.session.commit()
        
        # Test 1: Filter by classification
        response = self.client.get(
            f'/merge-assistant/api/session/{session.id}/changes'
            f'?classification=NO_CONFLICT'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertGreater(data['total'], 0)
        for change in data['changes']:
            self.assertEqual(change['classification'], 'NO_CONFLICT')
        
        # Test 2: Filter by object type
        response = self.client.get(
            f'/merge-assistant/api/session/{session.id}/changes'
            f'?object_type=Interface'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertGreater(data['total'], 0)
        for change in data['changes']:
            self.assertEqual(change['type'], 'Interface')
        
        # Test 3: Search by name
        response = self.client.get(
            f'/merge-assistant/api/session/{session.id}/changes'
            f'?search=TestObject5'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        self.assertIn('TestObject5', data['changes'][0]['name'])
        
        # Test 4: Combined filters
        response = self.client.get(
            f'/merge-assistant/api/session/{session.id}/changes'
            f'?classification=CONFLICT&object_type=Expression Rule'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        for change in data['changes']:
            self.assertEqual(change['classification'], 'CONFLICT')
            self.assertEqual(change['type'], 'Expression Rule')

    def test_complete_review_workflow(self):
        """Test complete review workflow (updates ChangeReview table in normalized schema)"""
        from models import db, MergeSession, Change, ChangeReview
        
        # Create test session
        session = MergeSession(
            reference_id='MRG_REVIEW_001',
            base_package_name='BasePackage',
            customized_package_name='CustomizedPackage',
            new_vendor_package_name='NewVendorPackage',
            status='in_progress',
            total_changes=3,
            reviewed_count=0,
            skipped_count=0
        )
        db.session.add(session)
        db.session.commit()
        
        # Create test changes
        changes = []
        for i in range(3):
            change = Change(
                session_id=session.id,
                object_uuid=f'uuid-{i:03d}',
                object_name=f'TestObject{i}',
                object_type='Interface',
                classification='NO_CONFLICT',
                change_type='MODIFIED',
                display_order=i
            )
            changes.append(change)
            db.session.add(change)
        db.session.commit()
        
        # Create initial reviews
        for change in changes:
            review = ChangeReview(
                session_id=session.id,
                change_id=change.id,
                review_status='pending'
            )
            db.session.add(review)
        db.session.commit()
        
        # Step 1: Start workflow
        response = self.client.get(
            f'/merge-assistant/session/{session.id}/workflow'
        )
        self.assertEqual(response.status_code, 302)  # Redirect to first change
        
        # Step 2: Review first change
        data = {'action': 'reviewed', 'notes': 'Looks good'}
        response = self.client.post(
            f'/merge-assistant/session/{session.id}/change/0/review',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        self.assertEqual(result['reviewed_count'], 1)
        
        # Step 3: Skip second change
        data = {'action': 'skipped', 'notes': 'Will review later'}
        response = self.client.post(
            f'/merge-assistant/session/{session.id}/change/1/review',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        self.assertEqual(result['skipped_count'], 1)
        
        # Step 4: Review third change (last one)
        data = {'action': 'reviewed', 'notes': 'Approved'}
        response = self.client.post(
            f'/merge-assistant/session/{session.id}/change/2/review',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        self.assertTrue(result['is_complete'])
        
        # Verify session status updated to completed
        db.session.refresh(session)
        self.assertEqual(session.status, 'completed')
        self.assertEqual(session.reviewed_count, 2)
        self.assertEqual(session.skipped_count, 1)
        
        # Step 5: Generate report (uses JOIN queries on normalized schema)
        response = self.client.get(
            f'/merge-assistant/session/{session.id}/report'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MRG_REVIEW_001', response.data)

    def test_complete_export_workflow(self):
        """Test complete export workflow"""
        from models import db, MergeSession, Package, Change
        
        # Create test session
        session = MergeSession(
            reference_id='MRG_EXPORT_001',
            base_package_name='BasePackage',
            customized_package_name='CustomizedPackage',
            new_vendor_package_name='NewVendorPackage',
            status='completed',
            total_changes=2
        )
        db.session.add(session)
        db.session.commit()
        
        # Create package
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='BasePackage',
            total_objects=2
        )
        db.session.add(package)
        db.session.commit()
        
        # Create changes
        for i in range(2):
            change = Change(
                session_id=session.id,
                object_uuid=f'uuid-{i:03d}',
                object_name=f'TestObject{i}',
                object_type='Interface',
                classification='NO_CONFLICT',
                change_type='MODIFIED',
                display_order=i
            )
            db.session.add(change)
        db.session.commit()
        
        # Test JSON export
        response = self.client.get(
            f'/merge-assistant/session/{session.id}/export/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        
        # Verify JSON structure
        data = json.loads(response.data)
        self.assertIn('summary', data)
        self.assertIn('changes', data)
        self.assertIn('session', data)
        self.assertEqual(data['session']['reference_id'], 'MRG_EXPORT_001')
        self.assertEqual(len(data['changes']), 2)

    def test_session_deletion_cascade(self):
        """Test that deleting session cascades to all normalized tables"""
        from models import (
            db, MergeSession, Package, AppianObject, Change,
            ChangeReview, ObjectDependency
        )
        
        # Create test session with complete normalized data
        session = MergeSession(
            reference_id='MRG_DELETE_001',
            base_package_name='BasePackage',
            customized_package_name='CustomizedPackage',
            new_vendor_package_name='NewVendorPackage',
            status='ready',
            total_changes=1
        )
        db.session.add(session)
        db.session.commit()
        
        # Create package
        package = Package(
            session_id=session.id,
            package_type='base',
            package_name='BasePackage',
            total_objects=1
        )
        db.session.add(package)
        db.session.commit()
        
        # Create object
        obj = AppianObject(
            package_id=package.id,
            uuid='uuid-001',
            name='TestInterface',
            object_type='Interface'
        )
        db.session.add(obj)
        db.session.commit()
        
        # Create dependency
        dep = ObjectDependency(
            package_id=package.id,
            parent_uuid='uuid-001',
            child_uuid='uuid-002',
            dependency_type='reference'
        )
        db.session.add(dep)
        db.session.commit()
        
        # Create change
        change = Change(
            session_id=session.id,
            object_uuid='uuid-001',
            object_name='TestInterface',
            object_type='Interface',
            classification='NO_CONFLICT',
            change_type='MODIFIED',
            base_object_id=obj.id,
            display_order=0
        )
        db.session.add(change)
        db.session.commit()
        
        # Create review
        review = ChangeReview(
            session_id=session.id,
            change_id=change.id,
            review_status='pending'
        )
        db.session.add(review)
        db.session.commit()
        
        # Record IDs for verification
        session_id = session.id
        package_id = package.id
        object_id = obj.id
        change_id = change.id
        
        # Delete session
        response = self.client.post(
            f'/merge-assistant/session/{session_id}/delete'
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify cascade deletes worked
        self.assertIsNone(MergeSession.query.get(session_id))
        self.assertIsNone(Package.query.get(package_id))
        self.assertIsNone(AppianObject.query.get(object_id))
        self.assertIsNone(Change.query.get(change_id))
        
        # Verify no orphaned records
        self.assertEqual(
            Package.query.filter_by(session_id=session_id).count(),
            0
        )
        self.assertEqual(
            AppianObject.query.filter_by(package_id=package_id).count(),
            0
        )
        self.assertEqual(
            Change.query.filter_by(session_id=session_id).count(),
            0
        )
        self.assertEqual(
            ChangeReview.query.filter_by(session_id=session_id).count(),
            0
        )
        self.assertEqual(
            ObjectDependency.query.filter_by(package_id=package_id).count(),
            0
        )

    def tearDown(self):
        """Clean up test files"""
        super().tearDown()
        
        # Clean up test ZIP files
        for zip_file in [self.base_zip, self.customized_zip, self.vendor_zip]:
            if zip_file.exists():
                zip_file.unlink()
