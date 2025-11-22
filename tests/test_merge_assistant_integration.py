"""
Integration Tests for Three-Way Merge Assistant

Tests the complete merge workflow end-to-end including:
- Upload → Blueprints → Comparison → Classification → Workflow → Report
- Session persistence and restoration
- Error recovery scenarios
- Concurrent session handling
"""
import pytest
import json
import time
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from app import create_app
from models import db, MergeSession, ChangeReview
from test_config import TestConfig
from tests.fixtures.three_way_merge.fixture_loader import (
    SMALL_PACKAGES,
    MEDIUM_PACKAGES,
    MALFORMED_EMPTY
)
from services.merge_assistant.three_way_merge_service import (
    ThreeWayMergeService
)
from services.merge_assistant.blueprint_generation_service import (
    BlueprintGenerationError
)


class TestMergeWorkflowIntegration:
    """Test complete merge workflow end-to-end"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config.from_object(TestConfig)
        TestConfig.init_directories()

        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        yield

        # Teardown
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_complete_workflow_small_packages(self):
        """
        Test complete workflow from upload to report with small packages
        
        This tests the full end-to-end flow:
        1. Upload three packages
        2. Generate blueprints
        3. Perform comparison
        4. Classify changes
        5. Order changes
        6. Generate guidance
        7. Review changes
        8. Generate report
        """
        # Get test packages
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Create merge service
        merge_service = ThreeWayMergeService()

        # Step 1: Create session (includes all analysis)
        session = merge_service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Verify session was created
        assert session is not None
        assert session.reference_id.startswith('MRG_')
        assert session.status == 'ready'
        assert session.total_changes > 0

        # Verify blueprints were generated
        assert session.base_blueprint is not None
        assert session.customized_blueprint is not None
        assert session.new_vendor_blueprint is not None

        # Verify comparisons were performed
        assert session.vendor_changes is not None
        assert session.customer_changes is not None

        # Verify classification was performed
        assert session.classification_results is not None
        classification = json.loads(session.classification_results)
        assert 'NO_CONFLICT' in classification
        assert 'CONFLICT' in classification
        assert 'CUSTOMER_ONLY' in classification
        assert 'REMOVED_BUT_CUSTOMIZED' in classification

        # Verify changes were ordered
        assert session.ordered_changes is not None
        ordered = json.loads(session.ordered_changes)
        assert len(ordered) == session.total_changes

        # Verify ChangeReview records were created
        reviews = ChangeReview.query.filter_by(
            session_id=session.id
        ).all()
        assert len(reviews) == session.total_changes

        # Step 2: Get summary
        summary = merge_service.get_summary(session.id)
        assert summary['session_id'] == session.id
        assert summary['reference_id'] == session.reference_id
        assert 'statistics' in summary
        assert 'breakdown_by_type' in summary
        assert 'estimated_complexity' in summary

        # Step 3: Get ordered changes
        changes = merge_service.get_ordered_changes(session.id)
        assert len(changes) > 0
        assert all('uuid' in c for c in changes)
        assert all('classification' in c for c in changes)
        assert all('merge_guidance' in c for c in changes)
        assert all('dependencies' in c for c in changes)

        # Step 4: Review some changes (adapt to actual number of changes)
        num_to_review = min(2, len(changes))
        for i in range(num_to_review):
            merge_service.update_progress(
                session.id,
                i,
                'reviewed',
                f'Test note for change {i}'
            )

        # Verify progress was updated
        session = merge_service.get_session(session.id)
        assert session.reviewed_count == num_to_review
        if num_to_review > 0:
            assert session.current_change_index == num_to_review - 1

        # Step 5: Skip remaining changes if any
        num_to_skip = 0
        for i in range(num_to_review, len(changes)):
            merge_service.update_progress(
                session.id,
                i,
                'skipped'
            )
            num_to_skip += 1

        # Verify skip count
        session = merge_service.get_session(session.id)
        assert session.skipped_count == num_to_skip

        # Step 6: Generate report
        report = merge_service.generate_report(session.id)
        assert 'summary' in report
        assert 'changes' in report
        assert 'changes_by_category' in report
        assert 'statistics' in report
        assert report['statistics']['reviewed'] == num_to_review
        assert report['statistics']['skipped'] == num_to_skip

    def test_complete_workflow_medium_packages(self):
        """Test complete workflow with medium-sized packages"""
        base, customized, new_vendor = MEDIUM_PACKAGES.get_paths()

        merge_service = ThreeWayMergeService()

        # Create session
        start_time = time.time()
        session = merge_service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )
        elapsed = time.time() - start_time

        # Verify session completed successfully
        assert session.status == 'ready'
        assert session.total_changes > 0

        # Verify processing time is reasonable (< 30 seconds for medium)
        assert elapsed < 30

        # Verify all components are present
        assert session.base_blueprint is not None
        assert session.ordered_changes is not None

        # Get summary
        summary = merge_service.get_summary(session.id)
        assert summary['statistics']['total_changes'] > 0

    def test_workflow_with_http_requests(self):
        """Test workflow through HTTP endpoints"""
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        # Step 1: Upload packages
        with open(base, 'rb') as bf, \
             open(customized, 'rb') as cf, \
             open(new_vendor, 'rb') as nf:

            data = {
                'base_package': (bf, 'base.zip'),
                'customized_package': (cf, 'customized.zip'),
                'new_vendor_package': (nf, 'new_vendor.zip')
            }

            response = self.client.post(
                '/merge-assistant/upload',
                data=data,
                content_type='multipart/form-data',
                follow_redirects=True
            )

            # Should redirect to summary page
            assert response.status_code == 200

        # Verify session was created
        sessions = MergeSession.query.all()
        assert len(sessions) == 1
        session = sessions[0]
        assert session.status == 'ready'

        # Step 2: View summary
        response = self.client.get(
            f'/merge-assistant/session/{session.id}/summary'
        )
        assert response.status_code == 200
        assert b'Merge Summary' in response.data

        # Step 3: Start workflow
        response = self.client.get(
            f'/merge-assistant/session/{session.id}/workflow'
        )
        # Should redirect to first change
        assert response.status_code == 302

        # Step 4: View first change
        response = self.client.get(
            f'/merge-assistant/session/{session.id}/change/0'
        )
        assert response.status_code == 200

        # Step 5: Review first change
        response = self.client.post(
            f'/merge-assistant/session/{session.id}/change/0/review',
            data=json.dumps({
                'action': 'reviewed',
                'notes': 'Test review'
            }),
            content_type='application/json'
        )
        assert response.status_code == 200

        # Step 6: Generate report
        response = self.client.get(
            f'/merge-assistant/session/{session.id}/report'
        )
        assert response.status_code == 200
        assert b'Merge Report' in response.data


class TestSessionPersistence:
    """Test session persistence and restoration"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config.from_object(TestConfig)
        TestConfig.init_directories()

        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        yield

        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_session_persists_across_requests(self):
        """Test that session data persists in database"""
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        merge_service = ThreeWayMergeService()

        # Create session
        session1 = merge_service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )
        session_id = session1.id
        reference_id = session1.reference_id

        # Clear session from memory
        db.session.expunge(session1)
        db.session.expire_all()

        # Retrieve session from database
        session2 = merge_service.get_session(session_id)

        # Verify all data persisted
        assert session2 is not None
        assert session2.id == session_id
        assert session2.reference_id == reference_id
        assert session2.status == 'ready'
        assert session2.base_blueprint is not None
        assert session2.ordered_changes is not None

    def test_session_restoration_after_progress(self):
        """Test that progress is saved and can be restored"""
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        merge_service = ThreeWayMergeService()

        # Create session and make progress
        session = merge_service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Get number of changes
        changes = json.loads(session.ordered_changes)
        num_changes = len(changes)

        # Review some changes (adapt to actual number)
        merge_service.update_progress(session.id, 0, 'reviewed', 'Note 1')
        if num_changes > 1:
            merge_service.update_progress(session.id, 1, 'skipped')

        # Clear from memory
        session_id = session.id
        db.session.expunge(session)
        db.session.expire_all()

        # Restore session
        restored = merge_service.get_session(session_id)

        # Verify progress was saved
        expected_reviewed = 1
        expected_skipped = 1 if num_changes > 1 else 0
        assert restored.reviewed_count == expected_reviewed
        assert restored.skipped_count == expected_skipped

        # Verify review records persisted
        reviews = ChangeReview.query.filter_by(
            session_id=session_id
        ).order_by(ChangeReview.id).all()

        reviewed = [r for r in reviews if r.review_status == 'reviewed']
        skipped = [r for r in reviews if r.review_status == 'skipped']

        assert len(reviewed) == expected_reviewed
        assert len(skipped) == expected_skipped
        assert reviewed[0].user_notes == 'Note 1'

    def test_session_retrieval_by_reference_id(self):
        """Test retrieving session by reference ID"""
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        merge_service = ThreeWayMergeService()

        # Create session
        session = merge_service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )
        reference_id = session.reference_id

        # Retrieve by reference ID
        retrieved = merge_service.get_session_by_reference_id(reference_id)

        assert retrieved is not None
        assert retrieved.id == session.id
        assert retrieved.reference_id == reference_id

    def test_multiple_sessions_persist_independently(self):
        """Test that multiple sessions can coexist"""
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        merge_service = ThreeWayMergeService()

        # Create multiple sessions
        session1 = merge_service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        session2 = merge_service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Verify both exist
        assert session1.id != session2.id
        assert session1.reference_id != session2.reference_id

        # Make different progress in each
        merge_service.update_progress(session1.id, 0, 'reviewed')
        merge_service.update_progress(session2.id, 0, 'skipped')

        # Refresh sessions from database
        db.session.expire_all()
        s1 = merge_service.get_session(session1.id)
        s2 = merge_service.get_session(session2.id)

        # Verify progress is independent
        assert s1.reviewed_count == 1
        assert s1.skipped_count == 0
        assert s2.reviewed_count == 0
        assert s2.skipped_count == 1


class TestErrorRecovery:
    """Test error recovery scenarios"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config.from_object(TestConfig)
        TestConfig.init_directories()

        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        yield

        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_blueprint_generation_failure(self):
        """Test handling of blueprint generation failure"""
        # Get malformed package
        malformed = MALFORMED_EMPTY
        base, customized, _ = SMALL_PACKAGES.get_paths()

        merge_service = ThreeWayMergeService()

        # Attempt to create session with malformed package
        with pytest.raises(Exception):
            merge_service.create_session(
                str(base),
                str(customized),
                str(malformed)
            )

        # Verify session was created but marked as error
        sessions = MergeSession.query.all()
        if sessions:
            session = sessions[0]
            assert session.status == 'error'
            assert session.error_log is not None

    def test_invalid_session_id(self):
        """Test handling of invalid session ID"""
        merge_service = ThreeWayMergeService()

        # Try to get non-existent session
        session = merge_service.get_session(99999)
        assert session is None

        # Try to get summary for non-existent session
        with pytest.raises(ValueError):
            merge_service.get_summary(99999)

    def test_invalid_change_index(self):
        """Test handling of invalid change index"""
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        merge_service = ThreeWayMergeService()

        # Create session
        session = merge_service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Try to update progress with invalid index
        with pytest.raises(ValueError):
            merge_service.update_progress(
                session.id,
                99999,
                'reviewed'
            )

        # Try negative index
        with pytest.raises(ValueError):
            merge_service.update_progress(
                session.id,
                -1,
                'reviewed'
            )

    def test_database_rollback_on_error(self):
        """Test that database rolls back on error"""
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        merge_service = ThreeWayMergeService()

        # Mock blueprint service to fail after first blueprint
        with patch.object(
            merge_service.blueprint_service,
            'generate_all_blueprints'
        ) as mock_gen:
            mock_gen.side_effect = BlueprintGenerationError(
                "Test error",
                "test.zip"
            )

            # Attempt to create session
            with pytest.raises(BlueprintGenerationError):
                merge_service.create_session(
                    str(base),
                    str(customized),
                    str(new_vendor)
                )

            # Verify session exists but is marked as error
            sessions = MergeSession.query.all()
            assert len(sessions) == 1
            assert sessions[0].status == 'error'


class TestConcurrentSessions:
    """Test concurrent session handling"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config.from_object(TestConfig)
        TestConfig.init_directories()

        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

        yield

        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_multiple_concurrent_sessions(self):
        """Test creating multiple sessions concurrently"""
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        merge_service = ThreeWayMergeService()

        # Create multiple sessions
        sessions = []
        for i in range(3):
            session = merge_service.create_session(
                str(base),
                str(customized),
                str(new_vendor)
            )
            sessions.append(session)

        # Verify all sessions were created
        assert len(sessions) == 3

        # Verify each has unique ID and reference
        ids = [s.id for s in sessions]
        refs = [s.reference_id for s in sessions]

        assert len(set(ids)) == 3
        assert len(set(refs)) == 3

        # Verify all are in ready state
        for session in sessions:
            assert session.status == 'ready'

    def test_concurrent_progress_updates(self):
        """Test updating progress in multiple sessions"""
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        merge_service = ThreeWayMergeService()

        # Create two sessions
        session1 = merge_service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        session2 = merge_service.create_session(
            str(base),
            str(customized),
            str(new_vendor)
        )

        # Get number of changes
        changes1 = json.loads(session1.ordered_changes)
        changes2 = json.loads(session2.ordered_changes)

        # Update progress in both
        merge_service.update_progress(session1.id, 0, 'reviewed', 'S1 Note')
        merge_service.update_progress(session2.id, 0, 'skipped')
        if len(changes1) > 1:
            merge_service.update_progress(session1.id, 1, 'skipped')
        if len(changes2) > 1:
            merge_service.update_progress(session2.id, 1, 'reviewed', 'S2 Note')

        # Refresh sessions from database
        db.session.expire_all()
        s1 = merge_service.get_session(session1.id)
        s2 = merge_service.get_session(session2.id)

        # Verify progress is independent
        assert s1.reviewed_count == 1
        assert s1.skipped_count == (1 if len(changes1) > 1 else 0)
        assert s2.reviewed_count == (1 if len(changes2) > 1 else 0)
        assert s2.skipped_count == 1

        # Verify review records are correct
        s1_reviews = ChangeReview.query.filter_by(
            session_id=session1.id
        ).all()
        s2_reviews = ChangeReview.query.filter_by(
            session_id=session2.id
        ).all()

        s1_reviewed = [r for r in s1_reviews if r.review_status == 'reviewed']
        s2_reviewed = [r for r in s2_reviews if r.review_status == 'reviewed']

        assert s1_reviewed[0].user_notes == 'S1 Note'
        if len(changes2) > 1:
            assert s2_reviewed[0].user_notes == 'S2 Note'

    def test_reference_id_generation_is_unique(self):
        """Test that reference IDs are unique across sessions"""
        base, customized, new_vendor = SMALL_PACKAGES.get_paths()

        merge_service = ThreeWayMergeService()

        # Create many sessions
        reference_ids = []
        for i in range(10):
            session = merge_service.create_session(
                str(base),
                str(customized),
                str(new_vendor)
            )
            reference_ids.append(session.reference_id)

        # Verify all are unique
        assert len(set(reference_ids)) == 10

        # Verify format is correct (MRG_XXX)
        for ref_id in reference_ids:
            assert ref_id.startswith('MRG_')
            assert len(ref_id) == 7  # MRG_001 format


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
