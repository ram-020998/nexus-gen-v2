"""
Health Check Tests - Comprehensive application health monitoring
"""
import json
import io
import unittest
from unittest.mock import patch
from tests.base_test import BaseTestCase
from tests.mock_bedrock_service import MockBedrockService
from models import Request, ChatSession

# Optional psutil import
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class TestApplicationHealth(BaseTestCase):
    """Comprehensive health checks for the application"""
    
    def test_database_connectivity(self):
        """Test database is accessible and working"""
        # Test creating and querying records
        request = Request(action_type='test', status='processing')
        from models import db
        db.session.add(request)
        db.session.commit()
        
        # Verify we can query it back
        found = Request.query.filter_by(action_type='test').first()
        self.assertIsNotNone(found)
        self.assertEqual(found.status, 'processing')
    
    def test_all_routes_accessible(self):
        """Test all main routes are accessible"""
        routes_to_test = [
            ('/', 200),
            ('/breakdown/', 200),
            ('/verify/', 200),
            ('/create/', 200),
            ('/chat/', 200),
        ]
        
        for route, expected_status in routes_to_test:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, expected_status, 
                               f"Route {route} returned {response.status_code}, expected {expected_status}")
    
    @patch('services.data_source_factory.DataSourceFactory.create_rag_service')
    def test_bedrock_service_integration(self, mock_service):
        """Test Bedrock service integration works"""
        mock_service.return_value = MockBedrockService()
        
        from services.request_service import RequestService
        service = RequestService()
        
        # Test Bedrock query
        request = service.create_request('breakdown', 'test.txt')
        response = service.process_with_bedrock(request, 'test query')
        
        self.assertIn('results', response)
        self.assertIn('summary', response)
    
    @patch('services.data_source_factory.DataSourceFactory.create_rag_service')
    @patch('services.q_agent_service.QAgentService.process_breakdown')
    def test_complete_breakdown_flow(self, mock_process, mock_service):
        """Test complete breakdown workflow health"""
        mock_service.return_value = MockBedrockService()
        mock_process.return_value = {
            'epic': 'Health Test Epic',
            'stories': [
                {
                    'story_name': 'Health Test Story',
                    'acceptance_criteria': 'GIVEN health check WHEN executed THEN passes',
                    'issue_type': 'User Story',
                    'points': ''
                }
            ]
        }
        
        # Test file upload
        data = {
            'file': (io.BytesIO(b'Health check document content'), 'health_test.txt')
        }
        
        response = self.client.post('/breakdown/upload', 
                                  data=data, 
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        
        # Test viewing results
        request_id = result['request_id']
        response = self.client.get(f'/breakdown/results/{request_id}')
        self.assertEqual(response.status_code, 200)
    
    @patch('services.data_source_factory.DataSourceFactory.create_rag_service')
    @patch('services.q_agent_service.QAgentService.process_chat')
    def test_chat_functionality_health(self, mock_process, mock_service):
        """Test chat functionality health"""
        mock_service.return_value = MockBedrockService()
        mock_process.return_value = 'Health check response from chat agent'
        
        # Test sending message
        data = {'message': 'Health check: Is the system working?'}
        
        response = self.client.post('/chat/message',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        self.assertIn('Health check response', result['answer'])
        
        # Test chat history
        response = self.client.get('/chat/history')
        self.assertEqual(response.status_code, 200)
        history = json.loads(response.data)
        self.assertGreater(len(history['history']), 0)
    
    def test_file_service_health(self):
        """Test file service functionality"""
        from services.file_service import FileService
        service = FileService()
        
        # Test file validation
        self.assertTrue(service.is_allowed_file('test.txt'))
        self.assertTrue(service.is_allowed_file('document.docx'))
        self.assertTrue(service.is_allowed_file('spec.pdf'))
        self.assertFalse(service.is_allowed_file('malicious.exe'))
        
        # Test recent uploads (should not crash)
        uploads = service.get_recent_uploads()
        self.assertIsInstance(uploads, list)
    
    def test_document_service_health(self):
        """Test document processing service"""
        from services.document_service import DocumentService
        service = DocumentService()
        
        # Test text file processing
        test_file = self.create_test_file("Health check content", "health.txt")
        content = service.extract_content(str(test_file))
        self.assertEqual(content, "Health check content")
        
        # Test unsupported format handling
        test_file = self.create_test_file("content", "test.unknown")
        content = service.extract_content(str(test_file))
        self.assertIn("content", content.lower())
    
    def test_json_parsing_robustness(self):
        """Test JSON parsing handles various formats"""
        from services.q_agent_service import QAgentService
        service = QAgentService()
        
        # Test clean JSON
        clean_json = '{"test": "value"}'
        cleaned = service._clean_json_content(clean_json)
        self.assertEqual(cleaned, clean_json)
        
        # Test JSON with markdown
        markdown_json = '```json\n{"test": "value"}\n```'
        cleaned = service._clean_json_content(markdown_json)
        self.assertEqual(cleaned, '{"test": "value"}')
        
        # Test JSON extraction
        mixed_content = 'Some text {"extracted": "json"} more text'
        extracted = service._extract_json_from_content(mixed_content)
        self.assertEqual(extracted, {"extracted": "json"})
    
    def test_error_handling_robustness(self):
        """Test application handles errors gracefully"""
        # Test invalid file upload
        response = self.client.post('/breakdown/upload', data={})
        self.assertEqual(response.status_code, 400)
        
        # Test empty verification content
        data = {'design_content': ''}
        response = self.client.post('/verify/process',
                                  data=json.dumps(data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        # Test empty chat message
        data = {'message': ''}
        response = self.client.post('/chat/message',
                                  data=json.dumps(data),
                                  content_type='application/json')
        self.assertEqual(response.status_code, 400)
        
        # Test nonexistent request
        response = self.client.get('/breakdown/results/99999')
        self.assertEqual(response.status_code, 302)  # Redirect to index
    
    def test_configuration_health(self):
        """Test application configuration is valid"""
        from config import Config
        
        # Test required configuration exists
        self.assertTrue(hasattr(Config, 'SECRET_KEY'))
        self.assertTrue(hasattr(Config, 'SQLALCHEMY_DATABASE_URI'))
        self.assertTrue(hasattr(Config, 'BEDROCK_KB_ID'))
        self.assertTrue(hasattr(Config, 'AWS_REGION'))
        
        # Test directories are configured
        self.assertTrue(hasattr(Config, 'UPLOAD_FOLDER'))
        self.assertTrue(hasattr(Config, 'OUTPUT_FOLDER'))
        
        # Test file settings
        self.assertTrue(hasattr(Config, 'ALLOWED_EXTENSIONS'))
        self.assertIn('txt', Config.ALLOWED_EXTENSIONS)
        self.assertIn('docx', Config.ALLOWED_EXTENSIONS)

class TestSystemResources(BaseTestCase):
    """Test system resource usage and limits"""
    
    @unittest.skipUnless(PSUTIL_AVAILABLE, "psutil not available")
    def test_memory_usage_reasonable(self):
        """Test application doesn't use excessive memory"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        # Should use less than 500MB for tests
        self.assertLess(memory_mb, 500, f"Memory usage too high: {memory_mb:.1f}MB")
    
    def test_file_size_limits(self):
        """Test file size limits are enforced"""
        from config import Config
        
        # Should have reasonable file size limit
        self.assertLessEqual(Config.MAX_CONTENT_LENGTH, 50 * 1024 * 1024)  # 50MB max
        self.assertGreaterEqual(Config.MAX_CONTENT_LENGTH, 1 * 1024 * 1024)  # 1MB min
    
    def test_concurrent_request_handling(self):
        """Test application can handle multiple requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = self.client.get('/')
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        self.assertEqual(len(results), 5)
        for status_code in results:
            self.assertEqual(status_code, 200)
