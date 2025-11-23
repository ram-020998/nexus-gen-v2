"""
Unit Tests for ChangeService

Tests the ChangeService methods for comparison normalization.
"""
import json
from tests.base_test import BaseTestCase
from models import (
    db, MergeSession, Package, AppianObject, Change,
    MergeGuidance, MergeConflict, MergeChange, ChangeReview
)
from services.merge_assistant.change_service import ChangeService
from services.merge_assistant.package_service import PackageService


class TestChangeService(BaseTestCase):
    """Unit tests for ChangeService."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.change_service = ChangeService()
        self.package_service = PackageService()

        # Create a test session
        self.session = MergeSession(
            reference_id='MRG_TEST_CHANGE_001',
            base_package_name='TestBase',
            customized_package_name='TestCustom',
            new_vendor_package_name='TestVendor',
            status='processing'
        )
        db.session.add(self.session)
        db.session.commit()

        # Create test packages with objects
        self._create_test_packages()

    def _create_test_packages(self):
        """Create test packages with sample objects."""
        # Base package
        self.base_package = Package(
            session_id=self.session.id,
            package_type='base',
            package_name='TestBase',
            total_objects=3
        )
        db.session.add(self.base_package)
        db.session.flush()

        # Customized package
        self.customized_package = Package(
            session_id=self.session.id,
            package_type='customized',
            package_name='TestCustom',
            total_objects=3
        )
        db.session.add(self.customized_package)
        db.session.flush()

        # Vendor package
        self.vendor_package = Package(
            session_id=self.session.id,
            package_type='new_vendor',
            package_name='TestVendor',
            total_objects=3
        )
        db.session.add(self.vendor_package)
        db.session.flush()

        # Create test objects in each package
        self.test_uuid1 = '_a-test-uuid-001'
        self.test_uuid2 = '_a-test-uuid-002'
        self.test_uuid3 = '_a-test-uuid-003'

        # Base objects
        self.base_obj1 = AppianObject(
            package_id=self.base_package.id,
            uuid=self.test_uuid1,
            name='Interface1',
            object_type='Interface',
            version_uuid='v-base-1',
            sail_code='a!textField(label: "Base")'
        )
        self.base_obj2 = AppianObject(
            package_id=self.base_package.id,
            uuid=self.test_uuid2,
            name='ProcessModel1',
            object_type='Process Model',
            version_uuid='v-base-2'
        )
        self.base_obj3 = AppianObject(
            package_id=self.base_package.id,
            uuid=self.test_uuid3,
            name='Rule1',
            object_type='Expression Rule',
            version_uuid='v-base-3',
            sail_code='if(true, "yes", "no")'
        )
        db.session.add_all([self.base_obj1, self.base_obj2, self.base_obj3])
        db.session.flush()

        # Customized objects (modified version of obj1)
        self.custom_obj1 = AppianObject(
            package_id=self.customized_package.id,
            uuid=self.test_uuid1,
            name='Interface1',
            object_type='Interface',
            version_uuid='v-custom-1',
            sail_code='a!textField(label: "Custom")'
        )
        self.custom_obj2 = AppianObject(
            package_id=self.customized_package.id,
            uuid=self.test_uuid2,
            name='ProcessModel1',
            object_type='Process Model',
            version_uuid='v-base-2'  # Same as base
        )
        self.custom_obj3 = AppianObject(
            package_id=self.customized_package.id,
            uuid=self.test_uuid3,
            name='Rule1',
            object_type='Expression Rule',
            version_uuid='v-base-3',  # Same as base
            sail_code='if(true, "yes", "no")'
        )
        db.session.add_all([self.custom_obj1, self.custom_obj2, self.custom_obj3])
        db.session.flush()

        # Vendor objects (modified version of obj1 and obj2)
        self.vendor_obj1 = AppianObject(
            package_id=self.vendor_package.id,
            uuid=self.test_uuid1,
            name='Interface1',
            object_type='Interface',
            version_uuid='v-vendor-1',
            sail_code='a!textField(label: "Vendor")'
        )
        self.vendor_obj2 = AppianObject(
            package_id=self.vendor_package.id,
            uuid=self.test_uuid2,
            name='ProcessModel1',
            object_type='Process Model',
            version_uuid='v-vendor-2'
        )
        self.vendor_obj3 = AppianObject(
            package_id=self.vendor_package.id,
            uuid=self.test_uuid3,
            name='Rule1',
            object_type='Expression Rule',
            version_uuid='v-base-3',  # Same as base
            sail_code='if(true, "yes", "no")'
        )
        db.session.add_all([self.vendor_obj1, self.vendor_obj2, self.vendor_obj3])
        db.session.commit()

    def test_create_changes_from_comparison(self):
        """Test creating Change records from comparison results."""
        # Create ordered changes
        ordered_changes = [
            {
                'uuid': self.test_uuid1,
                'name': 'Interface1',
                'type': 'Interface',
                'classification': 'CONFLICT',
                'change_type': 'MODIFIED',
                'vendor_change_type': 'MODIFIED',
                'customer_change_type': 'MODIFIED'
            },
            {
                'uuid': self.test_uuid2,
                'name': 'ProcessModel1',
                'type': 'Process Model',
                'classification': 'NO_CONFLICT',
                'change_type': 'MODIFIED',
                'vendor_change_type': 'MODIFIED',
                'customer_change_type': None
            },
            {
                'uuid': self.test_uuid3,
                'name': 'Rule1',
                'type': 'Expression Rule',
                'classification': 'NO_CONFLICT',
                'change_type': None,
                'vendor_change_type': None,
                'customer_change_type': None
            }
        ]

        # Create changes
        changes = self.change_service.create_changes_from_comparison(
            session_id=self.session.id,
            classification_results={},
            ordered_changes=ordered_changes
        )

        # Verify changes were created
        self.assertEqual(len(changes), 3)

        # Verify first change (CONFLICT)
        change1 = changes[0]
        self.assertEqual(change1.object_uuid, self.test_uuid1)
        self.assertEqual(change1.object_name, 'Interface1')
        self.assertEqual(change1.object_type, 'Interface')
        self.assertEqual(change1.classification, 'CONFLICT')
        self.assertEqual(change1.change_type, 'MODIFIED')
        self.assertEqual(change1.display_order, 0)
        self.assertIsNotNone(change1.base_object_id)
        self.assertIsNotNone(change1.customer_object_id)
        self.assertIsNotNone(change1.vendor_object_id)

        # Verify second change (NO_CONFLICT)
        change2 = changes[1]
        self.assertEqual(change2.classification, 'NO_CONFLICT')
        self.assertEqual(change2.display_order, 1)

        # Verify third change
        change3 = changes[2]
        self.assertEqual(change3.display_order, 2)

        # Verify changes are in database
        db_changes = Change.query.filter_by(
            session_id=self.session.id
        ).order_by(Change.display_order).all()
        self.assertEqual(len(db_changes), 3)

    def test_create_change_record_with_foreign_keys(self):
        """Test that change records have valid foreign keys."""
        change_data = {
            'uuid': self.test_uuid1,
            'name': 'Interface1',
            'type': 'Interface',
            'classification': 'CONFLICT',
            'change_type': 'MODIFIED'
        }

        change = self.change_service._create_change_record(
            session_id=self.session.id,
            change_data=change_data,
            display_order=0
        )

        # Verify foreign keys are set
        self.assertIsNotNone(change.base_object_id)
        self.assertIsNotNone(change.customer_object_id)
        self.assertIsNotNone(change.vendor_object_id)

        # Verify foreign keys reference correct objects
        self.assertEqual(change.base_object_id, self.base_obj1.id)
        self.assertEqual(change.customer_object_id, self.custom_obj1.id)
        self.assertEqual(change.vendor_object_id, self.vendor_obj1.id)

    def test_create_merge_guidance(self):
        """Test creating MergeGuidance records."""
        # Create a change first
        change = Change(
            session_id=self.session.id,
            object_uuid=self.test_uuid1,
            object_name='Interface1',
            object_type='Interface',
            classification='CONFLICT',
            change_type='MODIFIED',
            base_object_id=self.base_obj1.id,
            customer_object_id=self.custom_obj1.id,
            vendor_object_id=self.vendor_obj1.id,
            display_order=0
        )
        db.session.add(change)
        db.session.flush()

        # Create guidance data
        guidance_data = {
            'recommendation': 'MANUAL_MERGE',
            'reason': 'Both versions modified the interface',
            'conflicts': [
                {
                    'field_name': 'label',
                    'conflict_type': 'value_conflict',
                    'description': 'Label changed in both versions'
                }
            ],
            'changes': [
                {
                    'field_name': 'columns',
                    'description': 'Vendor added new column',
                    'old_value': '2 columns',
                    'new_value': '3 columns'
                }
            ]
        }

        # Create guidance
        guidance = self.change_service._create_merge_guidance(
            change,
            guidance_data
        )

        # Verify guidance was created
        self.assertIsNotNone(guidance.id)
        self.assertEqual(guidance.change_id, change.id)
        self.assertEqual(guidance.recommendation, 'MANUAL_MERGE')
        self.assertEqual(guidance.reason, 'Both versions modified the interface')

        # Verify conflicts were created
        conflicts = MergeConflict.query.filter_by(
            guidance_id=guidance.id
        ).all()
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].field_name, 'label')
        self.assertEqual(conflicts[0].conflict_type, 'value_conflict')

        # Verify changes were created
        changes = MergeChange.query.filter_by(
            guidance_id=guidance.id
        ).all()
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].field_name, 'columns')
        self.assertEqual(changes[0].old_value, '2 columns')
        self.assertEqual(changes[0].new_value, '3 columns')

    def test_create_change_review(self):
        """Test creating ChangeReview records."""
        # Create a change first
        change = Change(
            session_id=self.session.id,
            object_uuid=self.test_uuid1,
            object_name='Interface1',
            object_type='Interface',
            classification='CONFLICT',
            change_type='MODIFIED',
            base_object_id=self.base_obj1.id,
            display_order=0
        )
        db.session.add(change)
        db.session.flush()

        # Create review
        review = self.change_service._create_change_review(change)

        # Verify review was created
        self.assertIsNotNone(review.id)
        self.assertEqual(review.session_id, self.session.id)
        self.assertEqual(review.change_id, change.id)
        self.assertEqual(review.review_status, 'pending')
        self.assertIsNone(review.reviewed_at)

        # Verify review is in database
        db_review = ChangeReview.query.filter_by(
            change_id=change.id
        ).first()
        self.assertIsNotNone(db_review)
        self.assertEqual(db_review.review_status, 'pending')

    def test_get_change_with_objects(self):
        """Test getting change with all related objects."""
        # Create a change with guidance and review
        ordered_changes = [
            {
                'uuid': self.test_uuid1,
                'name': 'Interface1',
                'type': 'Interface',
                'classification': 'CONFLICT',
                'change_type': 'MODIFIED',
                'merge_guidance': {
                    'recommendation': 'MANUAL_MERGE',
                    'reason': 'Both versions modified',
                    'conflicts': [],
                    'changes': []
                }
            }
        ]

        changes = self.change_service.create_changes_from_comparison(
            session_id=self.session.id,
            classification_results={},
            ordered_changes=ordered_changes
        )

        change = changes[0]

        # Get change with objects
        result = self.change_service.get_change_with_objects(change.id)

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], change.id)
        self.assertEqual(result['object_uuid'], self.test_uuid1)
        self.assertEqual(result['classification'], 'CONFLICT')

        # Verify related objects are included
        self.assertIn('base_object', result)
        self.assertIn('customer_object', result)
        self.assertIn('vendor_object', result)
        self.assertIn('merge_guidance', result)
        self.assertIn('review', result)

        # Verify object details
        self.assertEqual(result['base_object']['uuid'], self.test_uuid1)
        self.assertEqual(result['customer_object']['uuid'], self.test_uuid1)
        self.assertEqual(result['vendor_object']['uuid'], self.test_uuid1)

        # Verify guidance details
        self.assertEqual(result['merge_guidance']['recommendation'], 'MANUAL_MERGE')

        # Verify review details
        self.assertEqual(result['review']['review_status'], 'pending')

    def test_create_changes_with_merge_guidance(self):
        """Test creating changes with merge guidance in one operation."""
        ordered_changes = [
            {
                'uuid': self.test_uuid1,
                'name': 'Interface1',
                'type': 'Interface',
                'classification': 'CONFLICT',
                'change_type': 'MODIFIED',
                'merge_guidance': {
                    'recommendation': 'MANUAL_MERGE',
                    'reason': 'Both versions modified the interface',
                    'conflicts': [
                        {
                            'field_name': 'label',
                            'conflict_type': 'value_conflict',
                            'description': 'Label changed in both versions'
                        }
                    ],
                    'changes': []
                }
            },
            {
                'uuid': self.test_uuid2,
                'name': 'ProcessModel1',
                'type': 'Process Model',
                'classification': 'NO_CONFLICT',
                'change_type': 'MODIFIED',
                'merge_guidance': {
                    'recommendation': 'ACCEPT_VENDOR',
                    'reason': 'Only vendor modified',
                    'conflicts': [],
                    'changes': [
                        {
                            'field_name': 'nodes',
                            'description': 'Added validation node',
                            'old_value': '3 nodes',
                            'new_value': '4 nodes'
                        }
                    ]
                }
            }
        ]

        # Create changes
        changes = self.change_service.create_changes_from_comparison(
            session_id=self.session.id,
            classification_results={},
            ordered_changes=ordered_changes
        )

        # Verify changes were created
        self.assertEqual(len(changes), 2)

        # Verify first change has guidance with conflicts
        change1 = changes[0]
        guidance1 = MergeGuidance.query.filter_by(
            change_id=change1.id
        ).first()
        self.assertIsNotNone(guidance1)
        self.assertEqual(guidance1.recommendation, 'MANUAL_MERGE')

        conflicts1 = MergeConflict.query.filter_by(
            guidance_id=guidance1.id
        ).all()
        self.assertEqual(len(conflicts1), 1)

        # Verify second change has guidance with changes
        change2 = changes[1]
        guidance2 = MergeGuidance.query.filter_by(
            change_id=change2.id
        ).first()
        self.assertIsNotNone(guidance2)
        self.assertEqual(guidance2.recommendation, 'ACCEPT_VENDOR')

        changes2 = MergeChange.query.filter_by(
            guidance_id=guidance2.id
        ).all()
        self.assertEqual(len(changes2), 1)

    def test_get_object_id_lookup(self):
        """Test looking up object IDs by package type and UUID."""
        # Test base package lookup
        base_id = self.change_service._get_object_id(
            session_id=self.session.id,
            package_type='base',
            object_uuid=self.test_uuid1
        )
        self.assertEqual(base_id, self.base_obj1.id)

        # Test customized package lookup
        custom_id = self.change_service._get_object_id(
            session_id=self.session.id,
            package_type='customized',
            object_uuid=self.test_uuid1
        )
        self.assertEqual(custom_id, self.custom_obj1.id)

        # Test vendor package lookup
        vendor_id = self.change_service._get_object_id(
            session_id=self.session.id,
            package_type='new_vendor',
            object_uuid=self.test_uuid1
        )
        self.assertEqual(vendor_id, self.vendor_obj1.id)

        # Test non-existent object
        none_id = self.change_service._get_object_id(
            session_id=self.session.id,
            package_type='base',
            object_uuid='_a-nonexistent-uuid'
        )
        self.assertIsNone(none_id)

    def test_change_ordering_preserved(self):
        """Test that display_order is correctly set and preserved."""
        ordered_changes = [
            {
                'uuid': self.test_uuid1,
                'name': 'Interface1',
                'type': 'Interface',
                'classification': 'CONFLICT',
                'change_type': 'MODIFIED'
            },
            {
                'uuid': self.test_uuid2,
                'name': 'ProcessModel1',
                'type': 'Process Model',
                'classification': 'NO_CONFLICT',
                'change_type': 'MODIFIED'
            },
            {
                'uuid': self.test_uuid3,
                'name': 'Rule1',
                'type': 'Expression Rule',
                'classification': 'NO_CONFLICT',
                'change_type': None
            }
        ]

        # Create changes
        changes = self.change_service.create_changes_from_comparison(
            session_id=self.session.id,
            classification_results={},
            ordered_changes=ordered_changes
        )

        # Verify display_order matches input order
        for i, change in enumerate(changes):
            self.assertEqual(change.display_order, i)

        # Query changes by display_order
        db_changes = Change.query.filter_by(
            session_id=self.session.id
        ).order_by(Change.display_order).all()

        # Verify order is preserved
        self.assertEqual(db_changes[0].object_uuid, self.test_uuid1)
        self.assertEqual(db_changes[1].object_uuid, self.test_uuid2)
        self.assertEqual(db_changes[2].object_uuid, self.test_uuid3)
