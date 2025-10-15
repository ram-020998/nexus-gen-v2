"""
Integration Tests
"""
import json
import io
from unittest.mock import patch
from tests.base_test import BaseTestCase
from tests.mock_bedrock_service import MockBedrockService
from models import Request, ChatSession

class TestEndToEndWorkflows(BaseTestCase):
    """Test complete workflows"""
    
    @patch('services.data_source_factory.create_bedrock_service')
    @patch('services.q_agent_service.QAgentService.process_breakdown')
    def test_complete_breakdown_workflow(self, mock_process, mock_service):
        """Test complete breakdown workflow"""
        mock_service.return_value = MockBedrockService()
        mock_process.return_value = {
            'epics': [{'title': 'Test Epic', 'stories': []}],
            'stories': [{'title': 'Test Story', 'acceptance_criteria': []}]
        }
        
        # Upload file
        data = {
            'file': (io.BytesIO(b'Test specification document'), 'spec.txt')
        }
        
        response = self.client.post('/breakdown/upload', 
                                  data=data, 
                                  content_type='multipart/form-data')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        request_id = result['request_id']
        
        # Check request was created
        request = Request.query.get(request_id)
        self.assertIsNotNone(request)
        self.assertEqual(request.action_type, 'breakdown')
        self.assertEqual(request.status, 'completed')
        
        # View results
        response = self.client.get(f'/breakdown/results/{request_id}')
        self.assertEqual(response.status_code, 200)
    
    @patch('services.data_source_factory.create_bedrock_service')
    @patch('services.q_agent_service.QAgentService.process_creation')
    def test_complete_creation_workflow(self, mock_process, mock_service):
        """Test complete creation workflow"""
        mock_service.return_value = MockBedrockService()
        mock_process.return_value = {
            'objects': [{'name': 'TestObject', 'type': 'Entity'}],
            'implementation': {'approach': 'Test approach'}
        }
        
        # Generate design
        data = {'acceptance_criteria': 'As a user, I want to test the system'}
        
        response = self.client.post('/create/generate',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        request_id = result['request_id']
        
        # Check request was created
        request = Request.query.get(request_id)
        self.assertIsNotNone(request)
        self.assertEqual(request.action_type, 'create')
        
        # View results
        response = self.client.get(f'/create/results/{request_id}')
        self.assertEqual(response.status_code, 200)
    
    @patch('services.data_source_factory.create_bedrock_service')
    @patch('services.q_agent_service.QAgentService.process_chat')
    def test_complete_chat_workflow(self, mock_process, mock_service):
        """Test complete chat workflow"""
        mock_service.return_value = MockBedrockService()
        mock_process.return_value = 'This is a test response'
        
        # Send message
        data = {'message': 'What is the system architecture?'}
        
        response = self.client.post('/chat/message',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        
        # Check chat session was created
        sessions = ChatSession.query.all()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].question, 'What is the system architecture?')
        
        # Get history
        response = self.client.get('/chat/history')
        self.assertEqual(response.status_code, 200)
        history = json.loads(response.data)
        self.assertEqual(len(history['history']), 1)

class TestErrorHandling(BaseTestCase):
    """Test error handling"""
    
    def test_invalid_file_upload(self):
        """Test invalid file upload"""
        response = self.client.post('/breakdown/upload', data={})
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.data)
        self.assertIn('error', result)
    
    def test_empty_verification_content(self):
        """Test empty verification content"""
        data = {'design_content': ''}
        
        response = self.client.post('/verify/process',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.data)
        self.assertIn('error', result)
    
    def test_empty_chat_message(self):
        """Test empty chat message"""
        data = {'message': ''}
        
        response = self.client.post('/chat/message',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        result = json.loads(response.data)
        self.assertIn('error', result)
    
    def test_nonexistent_request_results(self):
        """Test viewing results for nonexistent request"""
        response = self.client.get('/breakdown/results/99999')
        self.assertEqual(response.status_code, 302)  # Redirect
