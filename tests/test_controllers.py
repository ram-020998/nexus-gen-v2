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
        from services.process_tracker import ProcessTracker
        
        mock_service.return_value = MockBedrockService()
        mock_tracker = ProcessTracker(1, 'breakdown')
        mock_process.return_value = ({'epics': [], 'stories': []}, mock_tracker)

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
        from services.process_tracker import ProcessTracker
        
        mock_service.return_value = MockBedrockService()
        mock_tracker = ProcessTracker(1, 'verification')
        mock_process.return_value = ({'missing_objects': [], 'recommendations': []}, mock_tracker)

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
        from services.process_tracker import ProcessTracker
        
        mock_service.return_value = MockBedrockService()
        mock_tracker = ProcessTracker(1, 'creation')
        mock_process.return_value = ({'objects': [], 'implementation': {}}, mock_tracker)

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


class TestMergeAssistantController(BaseTestCase):
    """Test merge assistant controller endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        # Import here to avoid circular imports
        from models import (
            db, MergeSession, Package, AppianObject, Change,
            ChangeReview, MergeGuidance
        )
        
        # Create a test session with normalized data
        self.session = MergeSession(
            reference_id='MRG_TEST_001',
            base_package_name='BasePackage',
            customized_package_name='CustomizedPackage',
            new_vendor_package_name='NewVendorPackage',
            status='ready',
            total_changes=3,
            reviewed_count=0,
            skipped_count=0
        )
        db.session.add(self.session)
        db.session.commit()
        
        # Create test packages
        self.base_package = Package(
            session_id=self.session.id,
            package_type='base',
            package_name='BasePackage',
            total_objects=2
        )
        self.customized_package = Package(
            session_id=self.session.id,
            package_type='customized',
            package_name='CustomizedPackage',
            total_objects=2
        )
        self.vendor_package = Package(
            session_id=self.session.id,
            package_type='new_vendor',
            package_name='NewVendorPackage',
            total_objects=2
        )
        db.session.add_all([
            self.base_package,
            self.customized_package,
            self.vendor_package
        ])
        db.session.commit()
        
        # Create test objects
        self.base_obj1 = AppianObject(
            package_id=self.base_package.id,
            uuid='uuid-001',
            name='TestInterface',
            object_type='Interface',
            sail_code='a!textField(label: "Test")'
        )
        self.vendor_obj1 = AppianObject(
            package_id=self.vendor_package.id,
            uuid='uuid-001',
            name='TestInterface',
            object_type='Interface',
            sail_code='a!textField(label: "Test Modified")'
        )
        db.session.add_all([self.base_obj1, self.vendor_obj1])
        db.session.commit()
        
        # Create test changes
        self.change1 = Change(
            session_id=self.session.id,
            object_uuid='uuid-001',
            object_name='TestInterface',
            object_type='Interface',
            classification='NO_CONFLICT',
            change_type='MODIFIED',
            vendor_change_type='MODIFIED',
            base_object_id=self.base_obj1.id,
            vendor_object_id=self.vendor_obj1.id,
            display_order=0
        )
        self.change2 = Change(
            session_id=self.session.id,
            object_uuid='uuid-002',
            object_name='TestRule',
            object_type='Expression Rule',
            classification='CONFLICT',
            change_type='MODIFIED',
            display_order=1
        )
        self.change3 = Change(
            session_id=self.session.id,
            object_uuid='uuid-003',
            object_name='TestRecord',
            object_type='Record Type',
            classification='CUSTOMER_ONLY',
            change_type='ADDED',
            display_order=2
        )
        db.session.add_all([self.change1, self.change2, self.change3])
        db.session.commit()
        
        # Create merge guidance for change1
        self.guidance1 = MergeGuidance(
            change_id=self.change1.id,
            recommendation='ACCEPT_VENDOR',
            reason='Vendor changes improve functionality'
        )
        db.session.add(self.guidance1)
        db.session.commit()
        
        # Create change reviews
        self.review1 = ChangeReview(
            session_id=self.session.id,
            change_id=self.change1.id,
            review_status='pending'
        )
        db.session.add(self.review1)
        db.session.commit()

    def test_merge_assistant_home(self):
        """Test merge assistant home page"""
        response = self.client.get('/merge-assistant')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'upload', response.data.lower())

    def test_list_sessions(self):
        """Test listing merge sessions"""
        response = self.client.get('/merge-assistant/sessions')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MRG_TEST_001', response.data)

    def test_view_summary(self):
        """Test viewing session summary (uses SQL aggregates)"""
        response = self.client.get(
            f'/merge-assistant/session/{self.session.id}/summary'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MRG_TEST_001', response.data)
        self.assertIn(b'BasePackage', response.data)

    def test_view_summary_not_found(self):
        """Test viewing summary for non-existent session"""
        response = self.client.get(
            '/merge-assistant/session/99999/summary'
        )
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_view_change(self):
        """Test viewing specific change (uses JOIN queries)"""
        response = self.client.get(
            f'/merge-assistant/session/{self.session.id}/change/0'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'TestInterface', response.data)

    def test_view_change_invalid_index(self):
        """Test viewing change with invalid index"""
        response = self.client.get(
            f'/merge-assistant/session/{self.session.id}/change/999'
        )
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_review_change_reviewed(self):
        """Test recording review action (updates ChangeReview table)"""
        from models import ChangeReview
        
        data = {
            'action': 'reviewed',
            'notes': 'Looks good'
        }
        response = self.client.post(
            f'/merge-assistant/session/{self.session.id}/change/0/review',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'reviewed')
        
        # Verify database was updated
        review = ChangeReview.query.filter_by(
            session_id=self.session.id,
            change_id=self.change1.id
        ).first()
        self.assertEqual(review.review_status, 'reviewed')
        self.assertEqual(review.user_notes, 'Looks good')

    def test_review_change_skipped(self):
        """Test recording skip action"""
        data = {
            'action': 'skipped',
            'notes': 'Will review later'
        }
        response = self.client.post(
            f'/merge-assistant/session/{self.session.id}/change/0/review',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        self.assertEqual(result['action'], 'skipped')

    def test_review_change_invalid_action(self):
        """Test review with invalid action"""
        data = {
            'action': 'invalid_action',
            'notes': ''
        }
        response = self.client.post(
            f'/merge-assistant/session/{self.session.id}/change/0/review',
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_generate_report(self):
        """Test generating report (uses JOIN queries)"""
        response = self.client.get(
            f'/merge-assistant/session/{self.session.id}/report'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MRG_TEST_001', response.data)

    def test_api_session_summary(self):
        """Test API endpoint for session summary"""
        response = self.client.get(
            f'/merge-assistant/api/session/{self.session.id}/summary'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['reference_id'], 'MRG_TEST_001')
        self.assertEqual(data['statistics']['total_changes'], 3)

    def test_api_session_changes(self):
        """Test API endpoint for session changes (uses indexed SQL WHERE clauses)"""
        response = self.client.get(
            f'/merge-assistant/api/session/{self.session.id}/changes'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 3)
        self.assertEqual(len(data['changes']), 3)

    def test_api_session_changes_filter_classification(self):
        """Test filtering changes by classification"""
        response = self.client.get(
            f'/merge-assistant/api/session/{self.session.id}/changes'
            f'?classification=NO_CONFLICT'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['changes'][0]['classification'], 'NO_CONFLICT')

    def test_api_session_changes_filter_object_type(self):
        """Test filtering changes by object type"""
        response = self.client.get(
            f'/merge-assistant/api/session/{self.session.id}/changes'
            f'?object_type=Interface'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        self.assertEqual(data['changes'][0]['type'], 'Interface')

    def test_api_session_changes_search(self):
        """Test searching changes by name"""
        response = self.client.get(
            f'/merge-assistant/api/session/{self.session.id}/changes'
            f'?search=TestInterface'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['total'], 1)
        self.assertIn('TestInterface', data['changes'][0]['name'])

    def test_delete_session(self):
        """Test deleting session (cascade deletes handle normalized tables)"""
        response = self.client.post(
            f'/merge-assistant/session/{self.session.id}/delete'
        )
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.data)
        self.assertTrue(result['success'])
        
        # Verify session was deleted
        from models import MergeSession
        session = MergeSession.query.get(self.session.id)
        self.assertIsNone(session)
        
        # Verify cascade deletes worked (packages should be deleted)
        from models import Package
        packages = Package.query.filter_by(
            session_id=self.session.id
        ).all()
        self.assertEqual(len(packages), 0)

    def test_delete_session_not_found(self):
        """Test deleting non-existent session"""
        response = self.client.post(
            '/merge-assistant/session/99999/delete'
        )
        self.assertEqual(response.status_code, 404)

    def test_export_report_json(self):
        """Test exporting report as JSON"""
        response = self.client.get(
            f'/merge-assistant/session/{self.session.id}/export/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        
        # Verify JSON content
        data = json.loads(response.data)
        self.assertIn('summary', data)
        self.assertIn('changes', data)

    def test_start_workflow(self):
        """Test starting merge workflow"""
        response = self.client.get(
            f'/merge-assistant/session/{self.session.id}/workflow'
        )
        # Should redirect to first change
        self.assertEqual(response.status_code, 302)
        self.assertIn(b'/change/0', response.data)
