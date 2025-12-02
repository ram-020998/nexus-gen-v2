"""
Tests for Merge Assistant Controller

Tests the REST API endpoints for three-way merge operations.
"""

import os
import pytest
from io import BytesIO
from flask import Flask

from app import create_app
from models import db, MergeSession


class TestMergeAssistantController:
    """Test suite for merge assistant controller endpoints."""
    
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
    
    def test_create_merge_session_missing_files(self):
        """Test create_merge_session with missing files."""
        # Test missing base_package
        response = self.client.post('/merge/create', data={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'base_package' in data['error']
        
        # Test missing customized_package
        response = self.client.post(
            '/merge/create',
            data={
                'base_package': (BytesIO(b'test'), 'base.zip')
            }
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'customized_package' in data['error']
        
        # Test missing new_vendor_package
        response = self.client.post(
            '/merge/create',
            data={
                'base_package': (BytesIO(b'test'), 'base.zip'),
                'customized_package': (BytesIO(b'test'), 'customized.zip')
            }
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'new_vendor_package' in data['error']
    
    def test_create_merge_session_invalid_file_type(self):
        """Test create_merge_session with invalid file types."""
        response = self.client.post(
            '/merge/create',
            data={
                'base_package': (BytesIO(b'test'), 'base.txt'),
                'customized_package': (BytesIO(b'test'), 'customized.zip'),
                'new_vendor_package': (BytesIO(b'test'), 'new_vendor.zip')
            }
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'ZIP' in data['error']
    
    def test_get_merge_summary_not_found(self):
        """Test get_merge_summary with non-existent session."""
        response = self.client.get('/merge/INVALID_REF/summary')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'not found' in data['error'].lower()
    
    def test_get_working_set_not_found(self):
        """Test get_working_set with non-existent session."""
        response = self.client.get('/merge/INVALID_REF/changes')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'not found' in data['error'].lower()
    
    def test_get_change_detail_not_found(self):
        """Test get_change_detail with non-existent session."""
        response = self.client.get('/merge/INVALID_REF/changes/1')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'not found' in data['error'].lower()
    
    def test_get_working_set_with_classification_filter(self):
        """Test get_working_set with classification filter."""
        # Create a mock session
        with self.app.app_context():
            session = MergeSession(
                reference_id='MRG_001',
                status='ready',
                total_changes=0
            )
            db.session.add(session)
            db.session.commit()
        
        # Test with classification filter
        response = self.client.get(
            '/merge/MS_TEST01/changes',
            query_string={'classification': 'CONFLICT,NEW'}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'changes' in data['data']
        assert 'total' in data['data']
        assert 'filtered' in data['data']
    
    def test_endpoints_exist(self):
        """Test that all required endpoints are registered."""
        # Get all routes
        with self.app.app_context():
            routes = [str(rule) for rule in self.app.url_map.iter_rules()]
        
        # Check required endpoints exist
        assert '/merge/create' in routes
        assert '/merge/<reference_id>/summary' in routes
        assert '/merge/<reference_id>/changes' in routes
        assert '/merge/<reference_id>/changes/<int:change_id>' in routes


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
