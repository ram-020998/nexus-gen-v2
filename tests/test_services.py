"""
Test Services
"""
from unittest.mock import patch, MagicMock
from tests.base_test import BaseTestCase
from tests.mock_bedrock_service import MockBedrockService
from services.request_service import RequestService
from services.file_service import FileService
from services.document_service import DocumentService
from services.q_agent_service import QAgentService


class TestRequestService(BaseTestCase):
    """Test RequestService"""

    def setUp(self):
        super().setUp()
        with patch('services.data_source_factory.DataSourceFactory.create_rag_service',
                   return_value=MockBedrockService()):
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

        self.assertEqual(content, "content")


class TestQAgentService(BaseTestCase):
    """Test QAgentService"""

    def setUp(self):
        super().setUp()
        self.service = QAgentService()

    @patch('services.q_agent_service.subprocess.run')
    def test_process_breakdown_success(self, mock_run):
        """Test successful breakdown processing with Q CLI output"""
        # Mock realistic Q CLI output with ANSI codes
        mock_stderr = '''
\x1b[38;5;10m> \x1b[0m{"epics": [{"name": "Test Epic", "stories": []}]}\x1b[0m
'''
        mock_run.return_value = MagicMock(
            returncode=0, 
            stdout="", 
            stderr=mock_stderr
        )

        result, tracker = self.service.process_breakdown(1, "Test content", {"results": []})

        self.assertIn('epics', result)
        self.assertEqual(len(result['epics']), 1)
        self.assertEqual(result['epics'][0]['name'], "Test Epic")

    def test_extract_agent_response(self):
        """Test Q CLI output parsing with ANSI codes"""
        mock_result = MagicMock()
        mock_result.stderr = '''
\x1b[36mQ CLI Header\x1b[0m
\x1b[38;5;10m> \x1b[0m{"test": "success"}\x1b[0m
\x1b[1G\x1b[0m\x1b[?25h
'''
        mock_result.stdout = ""
        
        extracted = self.service._extract_agent_response(mock_result)
        self.assertEqual(extracted, '{"test": "success"}')

    @patch('services.q_agent_service.subprocess.run')
    def test_process_chat(self, mock_run):
        """Test chat processing"""
        mock_run.return_value = MagicMock(returncode=1)  # Simulate failure to test fallback

        result = self.service.process_chat("Test question", {"results": []})

        self.assertIsInstance(result, str)
        self.assertIn("I understand you're asking", result)
