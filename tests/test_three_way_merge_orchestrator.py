"""
Tests for Three Way Merge Orchestrator

Tests the complete three-way merge workflow orchestration.
"""

import os
import pytest
from tests.base_test import BaseTestCase
from services.three_way_merge_orchestrator import (
    ThreeWayMergeOrchestrator,
    ThreeWayMergeException
)
from models import db, MergeSession, Package, ObjectLookup, Change


class TestThreeWayMergeOrchestrator(BaseTestCase):
    """Test suite for ThreeWayMergeOrchestrator."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        # Create orchestrator without using dependency container
        # (services don't currently support container injection)
        self.orchestrator = ThreeWayMergeOrchestrator(container=None)
        
        # Test package paths
        self.test_packages_dir = (
            "applicationArtifacts/Three Way Testing Files/V2"
        )
        self.base_zip = os.path.join(
            self.test_packages_dir,
            "Test Application - Base Version.zip"
        )
        self.customized_zip = os.path.join(
            self.test_packages_dir,
            "Test Application Customer Version.zip"
        )
        self.new_vendor_zip = os.path.join(
            self.test_packages_dir,
            "Test Application Vendor New Version.zip"
        )
    
    def test_create_merge_session_success(self):
        """
        Test successful creation of merge session.
        
        Verifies:
        - Session is created with reference_id
        - Status is 'ready'
        - All three packages are extracted
        - Changes are classified
        - Total changes count is correct
        """
        # Create merge session
        session = self.orchestrator.create_merge_session(
            base_zip_path=self.base_zip,
            customized_zip_path=self.customized_zip,
            new_vendor_zip_path=self.new_vendor_zip
        )
        
        # Verify session created
        self.assertIsNotNone(session)
        self.assertIsNotNone(session.reference_id)
        self.assertTrue(session.reference_id.startswith('MS_'))
        self.assertEqual(session.status, 'ready')
        self.assertGreater(session.total_changes, 0)
        
        # Verify packages extracted
        packages = Package.query.filter_by(session_id=session.id).all()
        self.assertEqual(len(packages), 3)
        
        package_types = {pkg.package_type for pkg in packages}
        self.assertEqual(
            package_types,
            {'base', 'customized', 'new_vendor'}
        )
        
        # Verify all packages have objects
        for pkg in packages:
            self.assertGreater(pkg.total_objects, 0)
        
        # Verify changes created
        changes = Change.query.filter_by(session_id=session.id).all()
        self.assertEqual(len(changes), session.total_changes)
        
        # Verify all changes have valid classifications
        valid_classifications = {'NO_CONFLICT', 'CONFLICT', 'NEW', 'DELETED'}
        for change in changes:
            self.assertIn(change.classification, valid_classifications)
        
        print(f"\n✓ Session {session.reference_id} created successfully")
        print(f"  Total changes: {session.total_changes}")
        print(f"  Status: {session.status}")
    
    def test_get_session_status(self):
        """
        Test getting session status.
        
        Verifies:
        - Status information is returned
        - Package information is included
        - Statistics are correct
        """
        # Create session
        session = self.orchestrator.create_merge_session(
            base_zip_path=self.base_zip,
            customized_zip_path=self.customized_zip,
            new_vendor_zip_path=self.new_vendor_zip
        )
        
        # Get status
        status = self.orchestrator.get_session_status(session.reference_id)
        
        # Verify status structure
        self.assertEqual(status['reference_id'], session.reference_id)
        self.assertEqual(status['status'], 'ready')
        self.assertEqual(status['total_changes'], session.total_changes)
        
        # Verify packages
        self.assertIn('packages', status)
        self.assertIn('base', status['packages'])
        self.assertIn('customized', status['packages'])
        self.assertIn('new_vendor', status['packages'])
        
        # Verify statistics
        self.assertIn('statistics', status)
        stats = status['statistics']
        self.assertIn('NO_CONFLICT', stats)
        self.assertIn('CONFLICT', stats)
        self.assertIn('NEW', stats)
        self.assertIn('DELETED', stats)
        
        # Verify statistics sum to total changes
        total_from_stats = sum(stats.values())
        self.assertEqual(total_from_stats, session.total_changes)
        
        print(f"\n✓ Session status retrieved successfully")
        print(f"  Statistics: {stats}")
    
    def test_get_working_set(self):
        """
        Test getting working set of changes.
        
        Verifies:
        - Working set is returned
        - Changes include object information
        - Display order is correct
        """
        # Create session
        session = self.orchestrator.create_merge_session(
            base_zip_path=self.base_zip,
            customized_zip_path=self.customized_zip,
            new_vendor_zip_path=self.new_vendor_zip
        )
        
        # Get working set
        working_set = self.orchestrator.get_working_set(
            session.reference_id
        )
        
        # Verify working set
        self.assertEqual(len(working_set), session.total_changes)
        
        # Verify each change has required fields
        for change in working_set:
            self.assertIn('change_id', change)
            self.assertIn('display_order', change)
            self.assertIn('classification', change)
            self.assertIn('object', change)
            
            # Verify object details
            obj = change['object']
            self.assertIn('id', obj)
            self.assertIn('uuid', obj)
            self.assertIn('name', obj)
            self.assertIn('object_type', obj)
        
        # Verify display order is sequential
        for i, change in enumerate(working_set, start=1):
            self.assertEqual(change['display_order'], i)
        
        print(f"\n✓ Working set retrieved successfully")
        print(f"  Total changes: {len(working_set)}")
    
    def test_get_working_set_with_filter(self):
        """
        Test getting working set with classification filter.
        
        Verifies:
        - Filter is applied correctly
        - Only requested classifications are returned
        """
        # Create session
        session = self.orchestrator.create_merge_session(
            base_zip_path=self.base_zip,
            customized_zip_path=self.customized_zip,
            new_vendor_zip_path=self.new_vendor_zip
        )
        
        # Get only conflicts
        conflicts = self.orchestrator.get_working_set(
            session.reference_id,
            classification_filter=['CONFLICT']
        )
        
        # Verify all are conflicts
        for change in conflicts:
            self.assertEqual(change['classification'], 'CONFLICT')
        
        # Get conflicts and new
        conflict_and_new = self.orchestrator.get_working_set(
            session.reference_id,
            classification_filter=['CONFLICT', 'NEW']
        )
        
        # Verify all are conflicts or new
        for change in conflict_and_new:
            self.assertIn(
                change['classification'],
                ['CONFLICT', 'NEW']
            )
        
        print(f"\n✓ Working set filter works correctly")
        print(f"  Conflicts: {len(conflicts)}")
        print(f"  Conflicts + NEW: {len(conflict_and_new)}")
    
    def test_session_not_found(self):
        """
        Test error handling when session not found.
        
        Verifies:
        - ValueError is raised
        - Error message is correct
        """
        with self.assertRaises(ValueError) as context:
            self.orchestrator.get_session_status("MS_NOTFOUND")
        
        self.assertIn("Session not found", str(context.exception))
        
        print("\n✓ Session not found error handled correctly")
    
    def test_delete_session(self):
        """
        Test deleting a session.
        
        Verifies:
        - Session is deleted
        - Related data is cascade deleted
        - Objects in object_lookup remain
        """
        # Create session
        session = self.orchestrator.create_merge_session(
            base_zip_path=self.base_zip,
            customized_zip_path=self.customized_zip,
            new_vendor_zip_path=self.new_vendor_zip
        )
        
        reference_id = session.reference_id
        session_id = session.id
        
        # Count objects before deletion
        object_count_before = ObjectLookup.query.count()
        
        # Delete session
        self.orchestrator.delete_session(reference_id)
        
        # Verify session deleted
        deleted_session = MergeSession.query.filter_by(
            reference_id=reference_id
        ).first()
        self.assertIsNone(deleted_session)
        
        # Verify packages deleted
        packages = Package.query.filter_by(session_id=session_id).all()
        self.assertEqual(len(packages), 0)
        
        # Verify changes deleted
        changes = Change.query.filter_by(session_id=session_id).all()
        self.assertEqual(len(changes), 0)
        
        # Verify objects remain in object_lookup
        object_count_after = ObjectLookup.query.count()
        self.assertEqual(object_count_before, object_count_after)
        
        print(f"\n✓ Session {reference_id} deleted successfully")
        print(f"  Objects in object_lookup: {object_count_after}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
