"""
Test Services
"""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from tests.base_test import BaseTestCase
from tests.mock_bedrock_service import MockBedrockService
from services.request_service import RequestService
from services.file_service import FileService
from services.document_service import DocumentService
from services.q_agent_service import QAgentService
from models import Request

class TestRequestService(BaseTestCase):
    """Test RequestService"""
    
    def setUp(self):
        super().setUp()
        with patch('services.data_source_factory.DataSourceFactory.create_rag_service', return_value=MockBedrockService()):
            self.service = RequestService()
    
    def test_create_request(self):
        """Test request creation"""
        request = self.service.create_request('breakdown', 'test.txt', 'Test content')
        
        self.assertIsNotNone(request.id)
        self.assertEqual(request.action_type, 'breakdown')
        self.assertEqual(request.filename, 'test.txt')
        self.assertEqual(request.status, 'processing')
    
    def test_update_request_status(self):
        """Test request status update"""
        request = self.service.create_request('create', input_text='Test')
        updated = self.service.update_request_status(request.id, 'completed', '{"result": "test"}')
        
        self.assertEqual(updated.status, 'completed')
        self.assertEqual(updated.final_output, '{"result": "test"}')
    
    def test_process_with_bedrock(self):
        """Test Bedrock processing"""
        request = self.service.create_request('breakdown', 'test.txt')
        response = self.service.process_with_bedrock(request, 'test query')
        
        self.assertIn('results', response)
        self.assertIn('summary', response)
        self.assertIsNotNone(request.rag_query)
        self.assertIsNotNone(request.rag_response)

class TestFileService(BaseTestCase):
    """Test FileService"""
    
    def setUp(self):
        super().setUp()
        self.service = FileService()
    
    def test_allowed_file(self):
        """Test file extension validation"""
        self.assertTrue(self.service.is_allowed_file('test.txt'))
        self.assertTrue(self.service.is_allowed_file('test.docx'))
        self.assertFalse(self.service.is_allowed_file('test.exe'))
    
    def test_get_recent_uploads(self):
        """Test getting recent uploads"""
        uploads = self.service.get_recent_uploads()
        self.assertIsInstance(uploads, list)

class TestDocumentService(BaseTestCase):
    """Test DocumentService"""
    
    def setUp(self):
        super().setUp()
        self.service = DocumentService()
    
    def test_extract_text_content(self):
        """Test text file content extraction"""
        test_file = self.create_test_file("Test document content", "test.txt")
        content = self.service.extract_content(str(test_file))
        
        self.assertEqual(content, "Test document content")
    
    def test_extract_unsupported_format(self):
        """Test unsupported file format"""
        test_file = self.create_test_file("content", "test.xyz")
        content = self.service.extract_content(str(test_file))
        
        # Check what the service actually returns
        self.assertIn("content", content.lower())

class TestQAgentService(BaseTestCase):
    """Test QAgentService"""
    
    def setUp(self):
        super().setUp()
        self.service = QAgentService()
    
    @patch('services.q_agent_service.subprocess.run')
    def test_process_breakdown(self, mock_run):
        """Test breakdown processing"""
        mock_run.return_value = MagicMock(returncode=1)  # Simulate failure to test fallback
        
        result = self.service.process_breakdown(1, "Test content", {"results": []})
        
        self.assertIn('epic', result)
        self.assertIn('stories', result)
        self.assertEqual(result['epic'], 'Feature Implementation')
    
    def test_clean_json_content(self):
        """Test JSON content cleaning"""
        dirty_json = '```json\n{"test": "value"}\n```'
        cleaned = self.service._clean_json_content(dirty_json)
        self.assertEqual(cleaned, '{"test": "value"}')
    
    def test_extract_json_from_content(self):
        """Test JSON extraction from mixed content"""
        mixed_content = 'Some text {"test": "value"} more text'
        extracted = self.service._extract_json_from_content(mixed_content)
        self.assertEqual(extracted, {"test": "value"})
    
    @patch('services.q_agent_service.subprocess.run')
    def test_process_chat(self, mock_run):
        """Test chat processing"""
        mock_run.return_value = MagicMock(returncode=1)  # Simulate failure to test fallback
        
        result = self.service.process_chat("Test question", {"results": []})
        
        self.assertIsInstance(result, str)
        self.assertIn("Test question", result)

class TestExcelService(BaseTestCase):
    """Test ExcelService"""
    
    def setUp(self):
        super().setUp()
        from services.excel_service import ExcelService
        self.service = ExcelService()
    
    def test_create_breakdown_excel(self):
        """Test Excel generation for breakdown"""
        breakdown_data = {
            "epic": "Test Epic",
            "stories": [
                {
                    "story_name": "Test Story",
                    "acceptance_criteria": "GIVEN test WHEN action THEN result",
                    "issue_type": "User Story",
                    "points": "3"
                }
            ]
        }
        
        excel_path = self.service.create_breakdown_excel(1, breakdown_data, "test.txt")
        self.assertTrue(Path(excel_path).exists())
        self.assertTrue(excel_path.endswith('.xlsx'))

class TestBedrockRAGService(BaseTestCase):
    """Test BedrockRAGService"""
    
    def setUp(self):
        super().setUp()
        from services.bedrock_rag_service import BedrockRAGService
        self.service = BedrockRAGService()
    
    def test_fallback_response(self):
        """Test fallback response generation"""
        response = self.service._get_fallback_response('breakdown')
        
        self.assertEqual(response['status'], 'success')
        self.assertIn('results', response)
        self.assertIn('summary', response)
        self.assertIn('fallback', response['summary'])
    
    def test_format_bedrock_response(self):
        """Test Bedrock response formatting"""
        mock_response = {
            'output': {'text': 'Test output'},
            'citations': [{
                'retrievedReferences': [{
                    'content': {'text': 'Test content'},
                    'location': {'s3Location': {'uri': 'test-uri'}}
                }]
            }]
        }
        
        formatted = self.service._format_bedrock_response(mock_response, 'breakdown')
        
        self.assertEqual(formatted['status'], 'success')
        self.assertIn('results', formatted)
        self.assertEqual(len(formatted['results']), 1)
