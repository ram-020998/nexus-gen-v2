"""
Tests for Change Navigation Service

Tests navigation functionality including:
- Getting change details
- Sequential navigation (next/previous)
- Position tracking
- Progress calculation
- Object version retrieval
"""

import pytest

from models import (
    db, MergeSession, Change, ObjectLookup, Package, ObjectVersion
)
from services.change_navigation_service import ChangeNavigationService
from tests.base_test import BaseTestCase


class TestChangeNavigationService(BaseTestCase):
    """Test suite for ChangeNavigationService."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.service = ChangeNavigationService()
        
        # Create test session
        self.session = MergeSession(
            reference_id='MRG_001',
            status='ready',
            total_changes=3
        )
        db.session.add(self.session)
        db.session.flush()
        
        # Create test packages
        self.package_base = Package(
            session_id=self.session.id,
            package_type='base',
            filename='base.zip',
            total_objects=2
        )
        self.package_customized = Package(
            session_id=self.session.id,
            package_type='customized',
            filename='customized.zip',
            total_objects=2
        )
        self.package_new_vendor = Package(
            session_id=self.session.id,
            package_type='new_vendor',
            filename='new_vendor.zip',
            total_objects=2
        )
        db.session.add_all([
            self.package_base,
            self.package_customized,
            self.package_new_vendor
        ])
        db.session.flush()
        
        # Create test objects
        self.obj1 = ObjectLookup(
            uuid='uuid-001',
            name='Test Object 1',
            object_type='Interface',
            description='Test description 1'
        )
        self.obj2 = ObjectLookup(
            uuid='uuid-002',
            name='Test Object 2',
            object_type='ProcessModel',
            description='Test description 2'
        )
        self.obj3 = ObjectLookup(
            uuid='uuid-003',
            name='Test Object 3',
            object_type='RecordType',
            description='Test description 3'
        )
        db.session.add_all([self.obj1, self.obj2, self.obj3])
        db.session.flush()
        
        # Create test changes
        self.change1 = Change(
            session_id=self.session.id,
            object_id=self.obj1.id,
            classification='NO_CONFLICT',
            vendor_change_type='MODIFIED',
            display_order=1,
            status='pending'
        )
        self.change2 = Change(
            session_id=self.session.id,
            object_id=self.obj2.id,
            classification='CONFLICT',
            vendor_change_type='MODIFIED',
            customer_change_type='MODIFIED',
            display_order=2,
            status='pending'
        )
        self.change3 = Change(
            session_id=self.session.id,
            object_id=self.obj3.id,
            classification='NEW',
            vendor_change_type='ADDED',
            display_order=3,
            status='pending'
        )
        db.session.add_all([self.change1, self.change2, self.change3])
        db.session.flush()
        
        # Create object versions
        self.version1_base = ObjectVersion(
            object_id=self.obj1.id,
            package_id=self.package_base.id,
            version_uuid='v1-base',
            sail_code='a!localVariables()'
        )
        self.version1_vendor = ObjectVersion(
            object_id=self.obj1.id,
            package_id=self.package_new_vendor.id,
            version_uuid='v1-vendor',
            sail_code='a!localVariables(local!test: "value")'
        )
        db.session.add_all([self.version1_base, self.version1_vendor])
        db.session.commit()
    
    def test_get_change_detail_returns_complete_information(self):
        """Test that get_change_detail returns all required information."""
        detail = self.service.get_change_detail(
            'MRG_001',
            self.change1.id
        )
        
        # Verify change information
        assert detail['change']['id'] == self.change1.id
        assert detail['change']['classification'] == 'NO_CONFLICT'
        assert detail['change']['vendor_change_type'] == 'MODIFIED'
        assert detail['change']['status'] == 'pending'
        
        # Verify object information
        assert detail['object']['uuid'] == 'uuid-001'
        assert detail['object']['name'] == 'Test Object 1'
        assert detail['object']['object_type'] == 'Interface'
        
        # Verify session information
        assert detail['session']['reference_id'] == 'MRG_001'
        assert detail['session']['status'] == 'ready'
        assert detail['session']['total_changes'] == 3
        
        # Verify navigation
        assert detail['navigation']['has_next'] is True
        assert detail['navigation']['has_previous'] is False
        assert detail['navigation']['next_change_id'] == self.change2.id
        assert detail['navigation']['previous_change_id'] is None
        
        # Verify position
        assert detail['position'] == '1 of 3'
        assert detail['current_position'] == 1
        assert detail['total_changes'] == 3
        
        # Verify progress
        assert detail['progress_percent'] == pytest.approx(33.33, rel=0.01)
        
        # Verify versions
        assert detail['versions']['base'] is not None
        assert detail['versions']['new_vendor'] is not None
        assert detail['versions']['customized'] is None
    
    def test_get_next_change_returns_correct_id(self):
        """Test that get_next_change returns the next change ID."""
        next_id = self.service.get_next_change(
            'MRG_001',
            self.change1.id
        )
        assert next_id == self.change2.id
        
        next_id = self.service.get_next_change(
            'MRG_001',
            self.change2.id
        )
        assert next_id == self.change3.id
    
    def test_get_next_change_returns_none_at_end(self):
        """Test that get_next_change returns None for last change."""
        next_id = self.service.get_next_change(
            'MRG_001',
            self.change3.id
        )
        assert next_id is None
    
    def test_get_previous_change_returns_correct_id(self):
        """Test that get_previous_change returns the previous change ID."""
        prev_id = self.service.get_previous_change(
            'MRG_001',
            self.change3.id
        )
        assert prev_id == self.change2.id
        
        prev_id = self.service.get_previous_change(
            'MRG_001',
            self.change2.id
        )
        assert prev_id == self.change1.id
    
    def test_get_previous_change_returns_none_at_beginning(self):
        """Test that get_previous_change returns None for first change."""
        prev_id = self.service.get_previous_change(
            'MRG_001',
            self.change1.id
        )
        assert prev_id is None
    
    def test_get_change_position_returns_correct_position(self):
        """Test that get_change_position returns correct position."""
        position, total = self.service.get_change_position(
            'MRG_001',
            self.change1.id
        )
        assert position == 1
        assert total == 3
        
        position, total = self.service.get_change_position(
            'MRG_001',
            self.change2.id
        )
        assert position == 2
        assert total == 3
        
        position, total = self.service.get_change_position(
            'MRG_001',
            self.change3.id
        )
        assert position == 3
        assert total == 3
    
    def test_get_object_versions_returns_all_versions(self):
        """Test that get_object_versions returns versions from all packages."""
        versions = self.service.get_object_versions(
            self.session.id,
            self.obj1.id
        )
        
        assert versions['base'] is not None
        assert versions['base']['version_uuid'] == 'v1-base'
        assert versions['base']['sail_code'] == 'a!localVariables()'
        
        assert versions['new_vendor'] is not None
        assert versions['new_vendor']['version_uuid'] == 'v1-vendor'
        assert (
            versions['new_vendor']['sail_code'] ==
            'a!localVariables(local!test: "value")'
        )
        
        assert versions['customized'] is None
    
    def test_get_change_detail_raises_error_for_invalid_session(self):
        """Test that get_change_detail raises error for invalid session."""
        with pytest.raises(ValueError, match="Session not found"):
            self.service.get_change_detail('MS_INVALID', self.change1.id)
    
    def test_get_change_detail_raises_error_for_invalid_change(self):
        """Test that get_change_detail raises error for invalid change."""
        with pytest.raises(ValueError, match="Change .* not found"):
            self.service.get_change_detail('MRG_001', 99999)
    
    def test_navigation_with_middle_change(self):
        """Test navigation from middle change has both next and previous."""
        detail = self.service.get_change_detail(
            'MRG_001',
            self.change2.id
        )
        
        assert detail['navigation']['has_next'] is True
        assert detail['navigation']['has_previous'] is True
        assert detail['navigation']['next_change_id'] == self.change3.id
        assert detail['navigation']['previous_change_id'] == self.change1.id
        assert detail['position'] == '2 of 3'
        assert detail['progress_percent'] == pytest.approx(66.67, rel=0.01)
