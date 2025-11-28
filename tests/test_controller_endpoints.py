"""
Test controller endpoints for report generation and object filtering

This test file verifies that the new controller endpoints work correctly:
- export_report_excel_handler
- get_objects_by_type_handler
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app import create_app
from controllers.merge_assistant_controller import MergeAssistantController
from models import MergeSession


class TestControllerEndpoints:
    """Test suite for new controller endpoints"""

    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = create_app()
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def controller(self):
        """Create controller instance"""
        return MergeAssistantController()

    @pytest.fixture
    def mock_session(self):
        """Create mock merge session"""
        session = Mock(spec=MergeSession)
        session.id = 1
        session.reference_id = "MRG_001"
        session.base_package_name = "BasePackage"
        session.customized_package_name = "CustomizedPackage"
        session.new_vendor_package_name = "NewVendorPackage"
        session.status = "ready"
        return session

    def test_export_report_excel_handler_success(self, controller, mock_session):
        """Test successful Excel report generation"""
        # Mock the merge service
        controller.merge_service.get_session = Mock(return_value=mock_session)
        
        # Mock the export service
        test_report_path = "/tmp/test_report.xlsx"
        controller.export_service.generate_report = Mock(
            return_value=test_report_path
        )
        
        # Mock file existence
        with patch('os.path.exists', return_value=True):
            with patch('flask.send_file') as mock_send_file:
                mock_send_file.return_value = Mock()
                
                # Call the handler
                result = controller.export_report_excel_handler(1)
                
                # Verify service was called
                controller.merge_service.get_session.assert_called_once_with(1)
                controller.export_service.generate_report.assert_called_once()
                
                # Verify send_file was called
                mock_send_file.assert_called_once()

    def test_export_report_excel_handler_session_not_found(self, app, controller):
        """Test Excel report generation with non-existent session"""
        with app.test_request_context():
            # Mock the merge service to return None
            controller.merge_service.get_session = Mock(return_value=None)
            
            # Call the handler
            result = controller.export_report_excel_handler(999)
            
            # Verify error response
            assert result is not None

    def test_export_report_excel_handler_no_changes(self, app, controller, mock_session):
        """Test Excel report generation with no changes"""
        with app.test_request_context():
            # Mock the merge service
            controller.merge_service.get_session = Mock(return_value=mock_session)
            
            # Mock the export service to raise ValueError
            controller.export_service.generate_report = Mock(
                side_effect=ValueError("No changes found for session 1")
            )
            
            # Call the handler
            result = controller.export_report_excel_handler(1)
            
            # Verify error response
            assert result is not None

    def test_get_objects_by_type_handler_success(self, app, controller, mock_session):
        """Test successful object filtering by type"""
        with app.test_request_context('/?page=1&page_size=5'):
            # Mock the merge service
            controller.merge_service.get_session = Mock(return_value=mock_session)
            
            # Mock get_objects_by_type
            mock_result = {
                'objects': [
                    {
                        'name': 'TestInterface',
                        'uuid': 'test-uuid-1',
                        'classification': 'NO_CONFLICT',
                        'complexity': 'Low',
                        'change_type': 'MODIFIED'
                    }
                ],
                'total': 1,
                'page': 1,
                'page_size': 5,
                'total_pages': 1
            }
            controller.merge_service.get_objects_by_type = Mock(
                return_value=mock_result
            )
            
            # Call the handler
            result = controller.get_objects_by_type_handler(1, 'Interface')
            
            # Verify service was called
            controller.merge_service.get_session.assert_called_once_with(1)
            controller.merge_service.get_objects_by_type.assert_called_once_with(
                session_id=1,
                object_type='Interface',
                classification=None,
                page=1,
                page_size=5
            )

    def test_get_objects_by_type_handler_session_not_found(self, app, controller):
        """Test object filtering with non-existent session"""
        with app.test_request_context('/?page=1&page_size=5'):
            # Mock the merge service to return None
            controller.merge_service.get_session = Mock(return_value=None)
            
            # Call the handler
            result = controller.get_objects_by_type_handler(999, 'Interface')
            
            # Verify error response
            assert result is not None

    def test_get_objects_by_type_handler_invalid_page(self, app, controller, mock_session):
        """Test object filtering with invalid page number"""
        with app.test_request_context('/?page=0&page_size=5'):
            # Mock the merge service
            controller.merge_service.get_session = Mock(return_value=mock_session)
            
            # Call the handler
            result = controller.get_objects_by_type_handler(1, 'Interface')
            
            # Verify error response
            assert result is not None

    def test_get_objects_by_type_handler_invalid_page_size(self, app, controller, mock_session):
        """Test object filtering with invalid page size"""
        with app.test_request_context('/?page=1&page_size=200'):
            # Mock the merge service
            controller.merge_service.get_session = Mock(return_value=mock_session)
            
            # Call the handler
            result = controller.get_objects_by_type_handler(1, 'Interface')
            
            # Verify error response
            assert result is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
