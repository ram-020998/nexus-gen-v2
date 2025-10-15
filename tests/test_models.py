"""
Test Models
"""
from tests.base_test import BaseTestCase
from models import db, Request, ChatSession

class TestModels(BaseTestCase):
    """Test database models"""
    
    def test_request_creation(self):
        """Test Request model creation"""
        request = Request(
            action_type='breakdown',
            filename='test.txt',
            input_text='Test content',
            status='processing'
        )
        db.session.add(request)
        db.session.commit()
        
        self.assertIsNotNone(request.id)
        self.assertEqual(request.action_type, 'breakdown')
        self.assertEqual(request.status, 'processing')
    
    def test_request_to_dict(self):
        """Test Request to_dict method"""
        request = Request(
            action_type='create',
            input_text='Test criteria'
        )
        db.session.add(request)
        db.session.commit()
        
        data = request.to_dict()
        self.assertIn('id', data)
        self.assertIn('action_type', data)
        self.assertIn('created_at', data)
    
    def test_chat_session_creation(self):
        """Test ChatSession model creation"""
        session = ChatSession(
            session_id='test-session',
            question='Test question?',
            answer='Test answer',
            rag_response='{"results": []}'
        )
        db.session.add(session)
        db.session.commit()
        
        self.assertIsNotNone(session.id)
        self.assertEqual(session.session_id, 'test-session')
    
    def test_chat_session_to_dict(self):
        """Test ChatSession to_dict method"""
        session = ChatSession(
            session_id='test-session',
            question='Test question?',
            answer='Test answer'
        )
        db.session.add(session)
        db.session.commit()
        
        data = session.to_dict()
        self.assertIn('question', data)
        self.assertIn('answer', data)
        self.assertIn('created_at', data)
