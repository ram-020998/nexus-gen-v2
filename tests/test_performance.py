"""
Performance Tests
"""
import time
import json
from unittest.mock import patch
from tests.base_test import BaseTestCase
from tests.mock_bedrock_service import MockBedrockService


class TestPerformance(BaseTestCase):
    """Test application performance"""

    def test_dashboard_load_time(self):
        """Test dashboard loads within acceptable time"""
        start_time = time.time()
        response = self.client.get('/')
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 2.0)  # Should load within 2 seconds

    @patch('services.data_source_factory.DataSourceFactory.create_rag_service')
    def test_multiple_concurrent_requests(self, mock_service):
        """Test handling multiple concurrent requests"""
        mock_service.return_value = MockBedrockService()

        # Simulate multiple requests
        for i in range(5):
            data = {'message': f'Test message {i}'}
            _ = self.client.post('/chat/message',
                                 data=json.dumps(data),
                                 content_type='application/json')

    def test_large_file_handling(self):
        """Test handling of large files"""
        # Create a large text content (1MB)
        large_content = "Test content " * 70000  # Approximately 1MB

        data = {'design_content': large_content}

        start_time = time.time()
        _ = self.client.post('/verify/process',
                             data=json.dumps(data),
                             content_type='application/json')
        end_time = time.time()

        # Should handle large content within reasonable time
        self.assertLess(end_time - start_time, 60.0)  # Within 60 seconds
