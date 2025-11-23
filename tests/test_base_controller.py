"""
Tests for BaseController

Verifies that the base controller provides correct functionality for
response formatting, error handling, and service access.
"""

import pytest
from flask import Flask
from controllers.base_controller import BaseController
from core.dependency_container import DependencyContainer


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.secret_key = 'test-secret-key'
    return app


@pytest.fixture
def controller():
    """Create BaseController instance"""
    return BaseController()


def test_base_controller_initialization():
    """Test that BaseController initializes correctly"""
    controller = BaseController()
    assert controller._container is not None
    assert isinstance(controller._container, DependencyContainer)


def test_base_controller_with_custom_container():
    """Test BaseController with custom container"""
    custom_container = DependencyContainer()
    controller = BaseController(container=custom_container)
    assert controller._container is custom_container


def test_json_success_response(controller, app):
    """Test JSON success response formatting"""
    with app.app_context():
        response, status_code = controller.json_success(
            data={'id': 123},
            message='Success'
        )
        
        assert status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['message'] == 'Success'
        assert data['data'] == {'id': 123}


def test_json_error_response(controller, app):
    """Test JSON error response formatting"""
    with app.app_context():
        response, status_code = controller.json_error(
            'Something went wrong',
            status_code=400
        )
        
        assert status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert data['error'] == 'Something went wrong'


def test_validate_file_extension(controller):
    """Test file extension validation"""
    # Valid extensions
    assert controller.validate_file_extension('file.zip', {'zip'})
    assert controller.validate_file_extension('file.PDF', {'pdf'})
    assert controller.validate_file_extension('file.txt', {'txt', 'csv'})
    
    # Invalid extensions
    assert not controller.validate_file_extension('file.exe', {'zip'})
    assert not controller.validate_file_extension('file', {'zip'})
    assert not controller.validate_file_extension('file.zip', {'pdf'})


def test_validate_file_size(controller):
    """Test file size validation"""
    # Valid sizes
    assert controller.validate_file_size(1024, max_size_mb=1)  # 1KB
    assert controller.validate_file_size(1024 * 1024, max_size_mb=1)  # 1MB
    
    # Invalid sizes
    assert not controller.validate_file_size(
        2 * 1024 * 1024,
        max_size_mb=1
    )  # 2MB > 1MB limit


def test_validate_required_fields(controller, app):
    """Test required fields validation"""
    with app.app_context():
        # Valid data
        data = {'name': 'John', 'email': 'john@example.com'}
        error = controller.validate_required_fields(data, ['name', 'email'])
        assert error is None
        
        # Missing field
        data = {'name': 'John'}
        error = controller.validate_required_fields(data, ['name', 'email'])
        assert error is not None
        response, status_code = error
        assert status_code == 400
        
        # Empty field
        data = {'name': '', 'email': 'john@example.com'}
        error = controller.validate_required_fields(data, ['name', 'email'])
        assert error is not None


def test_get_pagination_params(controller, app):
    """Test pagination parameter extraction"""
    with app.test_request_context('/?page=2&per_page=20'):
        from flask import request
        page, per_page = controller.get_pagination_params(request)
        assert page == 2
        assert per_page == 20
    
    # Test defaults
    with app.test_request_context('/'):
        from flask import request
        page, per_page = controller.get_pagination_params(request)
        assert page == 1
        assert per_page == 10
    
    # Test invalid values
    with app.test_request_context('/?page=invalid&per_page=-5'):
        from flask import request
        page, per_page = controller.get_pagination_params(request)
        assert page == 1
        assert per_page == 10
    
    # Test max cap
    with app.test_request_context('/?per_page=200'):
        from flask import request
        page, per_page = controller.get_pagination_params(request)
        assert per_page == 100  # Capped at 100


def test_is_ajax_request(controller, app):
    """Test AJAX request detection"""
    # JSON request
    with app.test_request_context(
        '/',
        content_type='application/json'
    ):
        from flask import request
        assert controller.is_ajax_request(request)
    
    # XMLHttpRequest header
    with app.test_request_context(
        '/',
        headers={'X-Requested-With': 'XMLHttpRequest'}
    ):
        from flask import request
        assert controller.is_ajax_request(request)
    
    # Regular request
    with app.test_request_context('/'):
        from flask import request
        assert not controller.is_ajax_request(request)


def test_flash_methods(controller, app):
    """Test flash messaging methods"""
    with app.test_request_context('/'):
        from flask import get_flashed_messages
        
        controller.flash_success('Success message')
        controller.flash_error('Error message')
        controller.flash_warning('Warning message')
        controller.flash_info('Info message')
        
        messages = get_flashed_messages(with_categories=True)
        assert len(messages) == 4
        assert ('success', 'Success message') in messages
        assert ('error', 'Error message') in messages
        assert ('warning', 'Warning message') in messages
        assert ('info', 'Info message') in messages


def test_ensure_directory_exists(controller, tmp_path):
    """Test directory creation"""
    test_dir = tmp_path / 'test' / 'nested' / 'dir'
    
    result = controller.ensure_directory_exists(test_dir)
    
    assert result.exists()
    assert result.is_dir()
    assert result == test_dir


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
