"""
Tests for ThreeWayMergeService object filtering methods

Tests the new get_objects_by_type() and get_summary_with_complexity() methods.
"""
import pytest
from tests.base_test import BaseTestCase
from services.merge_assistant.three_way_merge_service import ThreeWayMergeService
from models import db, MergeSession, Change, AppianObject, Package


class TestThreeWayMergeObjectFiltering(BaseTestCase):
    """Test object filtering and complexity summary methods"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.service = ThreeWayMergeService()

    def test_get_objects_by_type_basic(self):
        """Test basic object filtering by type"""
        # Create a test session
        session = MergeSession(
            reference_id='MRG_TEST_001',
            base_package_name='Base',
            customized_package_name='Customized',
            new_vendor_package_name='Vendor',
            status='ready',
            total_changes=10
        )
        db.session.add(session)
        db.session.commit()

        # Create test packages
        base_pkg = Package(
            session_id=session.id,
            package_type='base',
            package_name='Base'
        )
        db.session.add(base_pkg)
        db.session.commit()

        # Create test objects
        interface_obj = AppianObject(
            package_id=base_pkg.id,
            uuid='test-uuid-1',
            name='Test Interface',
            object_type='Interface',
            sail_code='a!textField(label: "Test")'
        )
        db.session.add(interface_obj)
        db.session.commit()

        # Create test changes
        for i in range(7):
            change = Change(
                session_id=session.id,
                object_uuid=f'test-uuid-{i}',
                object_name=f'Test Interface {i}',
                object_type='Interface',
                classification='NO_CONFLICT' if i < 3 else 'CONFLICT',
                change_type='MODIFIED',
                display_order=i,
                vendor_object_id=interface_obj.id
            )
            db.session.add(change)
        
        db.session.commit()

        # Test filtering by type
        result = self.service.get_objects_by_type(
            session_id=session.id,
            object_type='Interface',
            page=1,
            page_size=5
        )

        # Verify results
        assert result['total'] == 7
        assert len(result['objects']) == 5  # First page
        assert result['page'] == 1
        assert result['page_size'] == 5
        assert result['total_pages'] == 2

        # Verify each object has complexity
        for obj in result['objects']:
            assert 'complexity' in obj
            assert obj['complexity'] in ['Low', 'Medium', 'High']

    def test_get_objects_by_type_with_classification_filter(self):
        """Test filtering by type and classification"""
        # Create a test session
        session = MergeSession(
            reference_id='MRG_TEST_002',
            base_package_name='Base',
            customized_package_name='Customized',
            new_vendor_package_name='Vendor',
            status='ready',
            total_changes=10
        )
        db.session.add(session)
        db.session.commit()

        # Create test packages
        base_pkg = Package(
            session_id=session.id,
            package_type='base',
            package_name='Base'
        )
        db.session.add(base_pkg)
        db.session.commit()

        # Create test object
        interface_obj = AppianObject(
            package_id=base_pkg.id,
            uuid='test-uuid-1',
            name='Test Interface',
            object_type='Interface',
            sail_code='a!textField(label: "Test")'
        )
        db.session.add(interface_obj)
        db.session.commit()

        # Create changes with different classifications
        for i in range(10):
            change = Change(
                session_id=session.id,
                object_uuid=f'test-uuid-{i}',
                object_name=f'Test Interface {i}',
                object_type='Interface',
                classification='CONFLICT' if i < 3 else 'NO_CONFLICT',
                change_type='MODIFIED',
                display_order=i,
                vendor_object_id=interface_obj.id
            )
            db.session.add(change)
        
        db.session.commit()

        # Test filtering by type and classification
        result = self.service.get_objects_by_type(
            session_id=session.id,
            object_type='Interface',
            classification='CONFLICT',
            page=1,
            page_size=5
        )

        # Verify results
        assert result['total'] == 3  # Only conflicts
        assert len(result['objects']) == 3
        assert all(obj['classification'] == 'CONFLICT' for obj in result['objects'])

    def test_get_objects_by_type_pagination(self):
        """Test pagination works correctly"""
        # Create a test session
        session = MergeSession(
            reference_id='MRG_TEST_003',
            base_package_name='Base',
            customized_package_name='Customized',
            new_vendor_package_name='Vendor',
            status='ready',
            total_changes=12
        )
        db.session.add(session)
        db.session.commit()

        # Create test packages
        base_pkg = Package(
            session_id=session.id,
            package_type='base',
            package_name='Base'
        )
        db.session.add(base_pkg)
        db.session.commit()

        # Create test object
        interface_obj = AppianObject(
            package_id=base_pkg.id,
            uuid='test-uuid-1',
            name='Test Interface',
            object_type='Interface',
            sail_code='a!textField(label: "Test")'
        )
        db.session.add(interface_obj)
        db.session.commit()

        # Create 12 changes
        for i in range(12):
            change = Change(
                session_id=session.id,
                object_uuid=f'test-uuid-{i}',
                object_name=f'Test Interface {i}',
                object_type='Interface',
                classification='NO_CONFLICT',
                change_type='MODIFIED',
                display_order=i,
                vendor_object_id=interface_obj.id
            )
            db.session.add(change)
        
        db.session.commit()

        # Test page 1
        result_page1 = self.service.get_objects_by_type(
            session_id=session.id,
            object_type='Interface',
            page=1,
            page_size=5
        )
        assert len(result_page1['objects']) == 5
        assert result_page1['page'] == 1
        assert result_page1['total_pages'] == 3

        # Test page 2
        result_page2 = self.service.get_objects_by_type(
            session_id=session.id,
            object_type='Interface',
            page=2,
            page_size=5
        )
        assert len(result_page2['objects']) == 5
        assert result_page2['page'] == 2

        # Test page 3 (partial)
        result_page3 = self.service.get_objects_by_type(
            session_id=session.id,
            object_type='Interface',
            page=3,
            page_size=5
        )
        assert len(result_page3['objects']) == 2  # Only 2 left
        assert result_page3['page'] == 3

    def test_get_summary_with_complexity(self):
        """Test summary with complexity calculations"""
        # Create a test session
        session = MergeSession(
            reference_id='MRG_TEST_004',
            base_package_name='Base',
            customized_package_name='Customized',
            new_vendor_package_name='Vendor',
            status='ready',
            total_changes=5
        )
        db.session.add(session)
        db.session.commit()

        # Create test packages
        base_pkg = Package(
            session_id=session.id,
            package_type='base',
            package_name='Base'
        )
        db.session.add(base_pkg)
        db.session.commit()

        # Create test objects with different complexities
        # Low complexity: Constant
        constant_obj = AppianObject(
            package_id=base_pkg.id,
            uuid='const-uuid',
            name='Test Constant',
            object_type='Constant',
            sail_code='10'
        )
        db.session.add(constant_obj)
        db.session.commit()

        # Create changes (excluding CUSTOMER_ONLY)
        changes_data = [
            ('const-uuid', 'Test Constant', 'Constant', 'NO_CONFLICT', constant_obj.id),
            ('int-uuid-1', 'Test Interface 1', 'Interface', 'NO_CONFLICT', constant_obj.id),
            ('int-uuid-2', 'Test Interface 2', 'Interface', 'CONFLICT', constant_obj.id),
            ('int-uuid-3', 'Test Interface 3', 'Interface', 'CONFLICT', constant_obj.id),
        ]

        for i, (uuid, name, obj_type, classification, obj_id) in enumerate(changes_data):
            change = Change(
                session_id=session.id,
                object_uuid=uuid,
                object_name=name,
                object_type=obj_type,
                classification=classification,
                change_type='MODIFIED',
                display_order=i,
                vendor_object_id=obj_id
            )
            db.session.add(change)
        
        db.session.commit()

        # Get summary with complexity
        summary = self.service.get_summary_with_complexity(session_id=session.id)

        # Verify enhanced fields are present
        assert 'estimated_complexity' in summary
        assert 'estimated_time_minutes' in summary
        assert 'estimated_time_hours' in summary
        assert 'estimated_time_display' in summary
        assert 'complexity_breakdown' in summary

        # Verify complexity breakdown
        breakdown = summary['complexity_breakdown']
        assert 'low' in breakdown
        assert 'medium' in breakdown
        assert 'high' in breakdown

        # Verify time is calculated
        assert summary['estimated_time_minutes'] > 0
        assert summary['estimated_time_hours'] > 0

    def test_get_objects_by_type_invalid_session(self):
        """Test error handling for invalid session"""
        with pytest.raises(ValueError, match="Session 99999 not found"):
            self.service.get_objects_by_type(
                session_id=99999,
                object_type='Interface'
            )

    def test_get_summary_with_complexity_invalid_session(self):
        """Test error handling for invalid session"""
        with pytest.raises(ValueError, match="Session 99999 not found"):
            self.service.get_summary_with_complexity(session_id=99999)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
