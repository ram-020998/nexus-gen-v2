"""
Test Controllers
"""
import json
import io
from unittest.mock import patch
from tests.base_test import BaseTestCase
from tests.mock_bedrock_service import MockBedrockService


class TestBreakdownController(BaseTestCase):
    """Test breakdown controller"""

    def test_breakdown_index(self):
        """Test breakdown index page"""
        response = self.client.get('/breakdown/')
        self.assertEqual(response.status_code, 200)

    @patch('services.data_source_factory.DataSourceFactory.create_rag_service')
    @patch('services.q_agent_service.QAgentService.process_breakdown')
    def test_file_upload(self, mock_process, mock_service):
        """Test file upload for breakdown"""
        mock_service.return_value = MockBedrockService()
        mock_process.return_value = {'epics': [], 'stories': []}

        data = {
            'file': (io.BytesIO(b'Test document content'), 'test.txt')
        }

        response = self.client.post('/breakdown/upload',
                                    data=data,
                                    content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('request_id', data)


class TestVerifyController(BaseTestCase):
    """Test verify controller"""

    def test_verify_index(self):
        """Test verify index page"""
        response = self.client.get('/verify/')
        self.assertEqual(response.status_code, 200)

    @patch('services.data_source_factory.DataSourceFactory.create_rag_service')
    @patch('services.q_agent_service.QAgentService.process_verification')
    def test_process_verification(self, mock_process, mock_service):
        """Test design verification"""
        mock_service.return_value = MockBedrockService()
        mock_process.return_value = {'missing_objects': [], 'recommendations': []}

        data = {'design_content': 'Test design document content'}

        response = self.client.post('/verify/process',
                                    data=json.dumps(data),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])


class TestCreateController(BaseTestCase):
    """Test create controller"""

    def test_create_index(self):
        """Test create index page"""
        response = self.client.get('/create/')
        self.assertEqual(response.status_code, 200)

    @patch('services.data_source_factory.DataSourceFactory.create_rag_service')
    @patch('services.q_agent_service.QAgentService.process_creation')
    def test_generate_design(self, mock_process, mock_service):
        """Test design generation"""
        mock_service.return_value = MockBedrockService()
        mock_process.return_value = {'objects': [], 'implementation': {}}

        data = {'acceptance_criteria': 'Test acceptance criteria'}

        response = self.client.post('/create/generate',
                                    data=json.dumps(data),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])


class TestChatController(BaseTestCase):
    """Test chat controller"""

    def test_chat_index(self):
        """Test chat index page"""
        response = self.client.get('/chat/')
        self.assertEqual(response.status_code, 200)

    @patch('services.data_source_factory.DataSourceFactory.create_rag_service')
    @patch('services.q_agent_service.QAgentService.process_chat')
    def test_send_message(self, mock_process, mock_service):
        """Test sending chat message"""
        mock_service.return_value = MockBedrockService()
        mock_process.return_value = 'Test response'

        data = {'message': 'Test question'}

        response = self.client.post('/chat/message',
                                    data=json.dumps(data),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        self.assertEqual(result['answer'], 'Test response')

    def test_clear_history(self):
        """Test clearing chat history"""
        response = self.client.post('/chat/clear')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])


class TestDashboard(BaseTestCase):
    """Test dashboard"""

    def test_dashboard(self):
        """Test dashboard page"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
