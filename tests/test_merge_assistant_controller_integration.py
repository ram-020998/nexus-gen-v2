"""
Integration Tests for Merge Assistant Controller

Tests the complete three-way merge workflow using real Appian packages.
"""

import os
import pytest
from pathlib import Path

from app import create_app
from models import db, MergeSession, Change


class TestMergeAssistantControllerIntegration:
    """Integration test suite for merge assistant controller."""
    
    # Test package paths
    BASE_DIR = Path("applicationArtifacts/Three Way Testing Files/V2")
    BASE_PACKAGE = BASE_DIR / "Test Application - Base Version.zip"
    CUSTOMIZED_PACKAGE = BASE_DIR / "Test Application Customer Version.zip"
    NEW_VENDOR_PACKAGE = (
        BASE_DIR / "Test Application Vendor New Version.zip"
    )
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        # Create app
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Set up database
        with self.app.app_context():
            db.create_all()
        
        yield
        
        # Teardown
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    @pytest.mark.skipif(
        not BASE_PACKAGE.exists(),
        reason="Test packages not available"
    )
    def test_complete_merge_workflow(self):
        """
        Test complete three-way merge workflow with real packages.
        
        This test verifies:
        1. Create merge session with 3 packages
        2. Get merge summary
        3. Get working set
        4. Get individual change details
        """
        # Step 1: Create merge session
        with open(self.BASE_PACKAGE, 'rb') as base_file, \
             open(self.CUSTOMIZED_PACKAGE, 'rb') as customized_file, \
             open(self.NEW_VENDOR_PACKAGE, 'rb') as new_vendor_file:
            
            response = self.client.post(
                '/merge/create',
                data={
                    'base_package': (base_file, 'base.zip'),
                    'customized_package': (customized_file, 'customized.zip'),
                    'new_vendor_package': (new_vendor_file, 'new_vendor.zip')
                },
                content_type='multipart/form-data'
            )
        
        # Verify session created
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'reference_id' in data['data']
        assert 'total_changes' in data['data']
        
        reference_id = data['data']['reference_id']
        total_changes = data['data']['total_changes']
        
        print(f"\n✓ Session created: {reference_id}")
        print(f"  Total changes: {total_changes}")
        
        # Step 2: Get merge summary
        response = self.client.get(f'/merge/{reference_id}/summary')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'reference_id' in data['data']
        assert 'status' in data['data']
        assert 'packages' in data['data']
        assert 'statistics' in data['data']
        
        session_data = data['data']
        assert session_data['reference_id'] == reference_id
        assert session_data['status'] == 'ready'
        
        statistics = data['data']['statistics']
        
        print(f"\n✓ Summary retrieved:")
        print(f"  Status: {session_data['status']}")
        print(f"  Classifications: {statistics}")
        
        # Step 3: Get working set (all changes)
        response = self.client.get(f'/merge/{reference_id}/changes')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'changes' in data['data']
        assert 'total' in data['data']
        assert 'filtered' in data['data']
        
        changes = data['data']['changes']
        assert len(changes) == total_changes
        assert data['data']['total'] == total_changes
        assert data['data']['filtered'] == total_changes
        
        print(f"\n✓ Working set retrieved:")
        print(f"  Total changes: {len(changes)}")
        
        # Verify change structure
        if changes:
            first_change = changes[0]
            assert 'change_id' in first_change
            assert 'classification' in first_change
            assert 'object' in first_change
            assert 'uuid' in first_change['object']
            assert 'name' in first_change['object']
            assert 'object_type' in first_change['object']
            
            print(f"  First change: {first_change['object']['name']}")
            print(f"    Type: {first_change['object']['object_type']}")
            print(f"    Classification: {first_change['classification']}")
        
        # Step 4: Get working set with filter (conflicts only)
        response = self.client.get(
            f'/merge/{reference_id}/changes',
            query_string={'classification': 'CONFLICT'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        conflicts = data['data']['changes']
        conflict_count = len(conflicts)
        
        print(f"\n✓ Filtered working set (CONFLICT):")
        print(f"  Conflicts: {conflict_count}")
        
        # Verify all returned changes are conflicts
        for change in conflicts:
            assert change['classification'] == 'CONFLICT'
        
        # Step 5: Get individual change details
        if changes:
            first_change_id = changes[0]['change_id']
            
            response = self.client.get(
                f'/merge/{reference_id}/changes/{first_change_id}'
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'change' in data['data']
            assert 'object' in data['data']
            assert 'session' in data['data']
            
            change_detail = data['data']['change']
            assert change_detail['id'] == first_change_id
            
            print(f"\n✓ Change detail retrieved:")
            print(f"  Change ID: {change_detail['id']}")
            print(f"  Display order: {change_detail['display_order']}")
            print(f"  Classification: {change_detail['classification']}")
        
        print("\n✓ Complete workflow test passed!")
    
    def test_get_summary_for_nonexistent_session(self):
        """Test getting summary for non-existent session."""
        response = self.client.get('/merge/MS_INVALID/summary')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
    
    def test_get_changes_for_nonexistent_session(self):
        """Test getting changes for non-existent session."""
        response = self.client.get('/merge/MS_INVALID/changes')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
    
    def test_get_change_detail_for_nonexistent_change(self):
        """Test getting detail for non-existent change."""
        # Create a session first
        with self.app.app_context():
            session = MergeSession(
                reference_id='MRG_002',
                status='ready',
                total_changes=0
            )
            db.session.add(session)
            db.session.commit()
        
        # Try to get non-existent change
        response = self.client.get('/merge/MS_TEST02/changes/99999')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
