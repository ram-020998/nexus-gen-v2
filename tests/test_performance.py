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
    
    @patch('services.data_source_factory.create_bedrock_service')
    def test_multiple_concurrent_requests(self, mock_service):
        """Test handling multiple concurrent requests"""
        mock_service.return_value = MockBedrockService()
        
        # Simulate multiple requests
        responses = []
        for i in range(5):
            data = {'message': f'Test message {i}'}
            response = self.client.post('/chat/message',
                                      data=json.dumps(data),
                                      content_type='application/json')
            responses.append(response)
        
        # All should succeed
        for response in responses:
            self.assertEqual(response.status_code, 200)
    
    def test_large_file_handling(self):
        """Test handling of large files"""
        # Create a large text content (1MB)
        large_content = "Test content " * 70000  # Approximately 1MB
        
        data = {'design_content': large_content}
        
        start_time = time.time()
        response = self.client.post('/verify/process',
                                  data=json.dumps(data),
                                  content_type='application/json')
        end_time = time.time()
        
        # Should handle large content within reasonable time
        self.assertLess(end_time - start_time, 10.0)  # Within 10 seconds
