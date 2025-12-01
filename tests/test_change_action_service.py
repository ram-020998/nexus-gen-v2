"""
Tests for Change Action Service

Tests action functionality including:
- Marking changes as reviewed
- Skipping changes
- Saving notes
- Undoing actions
"""

import pytest

from models import db, MergeSession, Change, ObjectLookup
from services.change_action_service import ChangeActionService
from tests.base_test import BaseTestCase


class TestChangeActionService(BaseTestCase):
    """Test suite for ChangeActionService."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.service = ChangeActionService()

        # Create test session
        self.session = MergeSession(
            reference_id='MS_TEST01',
            status='ready',
            total_changes=3,
            reviewed_count=0,
            skipped_count=0
        )
        db.session.add(self.session)
        db.session.flush()

        # Create test objects
        self.obj1 = ObjectLookup(
            uuid='uuid-001',
            name='Test Object 1',
            object_type='Interface',
            description='Test description 1'
        )
        self.obj2 = ObjectLookup(
            uuid='uuid-002',
            name='Test Object 2',
            object_type='ProcessModel',
            description='Test description 2'
        )
        self.obj3 = ObjectLookup(
            uuid='uuid-003',
            name='Test Object 3',
            object_type='RecordType',
            description='Test description 3'
        )
        db.session.add_all([self.obj1, self.obj2, self.obj3])
        db.session.flush()

        # Create test changes
        self.change1 = Change(
            session_id=self.session.id,
            object_id=self.obj1.id,
            classification='NO_CONFLICT',
            vendor_change_type='MODIFIED',
            display_order=1,
            status='pending'
        )
        self.change2 = Change(
            session_id=self.session.id,
            object_id=self.obj2.id,
            classification='CONFLICT',
            vendor_change_type='MODIFIED',
            customer_change_type='MODIFIED',
            display_order=2,
            status='pending'
        )
        self.change3 = Change(
            session_id=self.session.id,
            object_id=self.obj3.id,
            classification='NEW',
            vendor_change_type='ADDED',
            display_order=3,
            status='pending'
        )
        db.session.add_all([self.change1, self.change2, self.change3])
        db.session.commit()

    def test_mark_as_reviewed_updates_status(self):
        """Test that marking a change as reviewed updates its status."""
        change = self.service.mark_as_reviewed(
            'MS_TEST01',
            self.change1.id,
            'user123'
        )

        assert change.status == 'reviewed'
        assert change.reviewed_at is not None
        assert change.reviewed_by == 'user123'

        # Verify session counter incremented
        db.session.refresh(self.session)
        assert self.session.reviewed_count == 1

    def test_mark_as_reviewed_without_user_id(self):
        """Test marking as reviewed without user_id."""
        change = self.service.mark_as_reviewed(
            'MS_TEST01',
            self.change1.id
        )

        assert change.status == 'reviewed'
        assert change.reviewed_at is not None
        assert change.reviewed_by is None

    def test_mark_as_reviewed_increments_counter_only_once(self):
        """Test that counter only increments when status changes."""
        # Mark as reviewed first time
        self.service.mark_as_reviewed('MS_TEST01', self.change1.id)
        db.session.refresh(self.session)
        assert self.session.reviewed_count == 1

        # Mark as reviewed again (already reviewed)
        self.service.mark_as_reviewed('MS_TEST01', self.change1.id)
        db.session.refresh(self.session)
        assert self.session.reviewed_count == 1  # Should not increment

    def test_skip_change_updates_status(self):
        """Test that skipping a change updates its status."""
        change = self.service.skip_change(
            'MS_TEST01',
            self.change1.id
        )

        assert change.status == 'skipped'

        # Verify session counter incremented
        db.session.refresh(self.session)
        assert self.session.skipped_count == 1

    def test_skip_change_increments_counter_only_once(self):
        """Test that counter only increments when status changes."""
        # Skip first time
        self.service.skip_change('MS_TEST01', self.change1.id)
        db.session.refresh(self.session)
        assert self.session.skipped_count == 1

        # Skip again (already skipped)
        self.service.skip_change('MS_TEST01', self.change1.id)
        db.session.refresh(self.session)
        assert self.session.skipped_count == 1  # Should not increment

    def test_save_notes_persists_notes(self):
        """Test that saving notes persists them to the database."""
        notes_text = "This change requires manual merge"
        change = self.service.save_notes(
            'MS_TEST01',
            self.change1.id,
            notes_text
        )

        assert change.notes == notes_text

        # Verify persistence by querying again
        db.session.refresh(change)
        assert change.notes == notes_text

    def test_save_notes_updates_existing_notes(self):
        """Test that saving notes updates existing notes."""
        # Save initial notes
        self.service.save_notes(
            'MS_TEST01',
            self.change1.id,
            "Initial notes"
        )

        # Update notes
        change = self.service.save_notes(
            'MS_TEST01',
            self.change1.id,
            "Updated notes"
        )

        assert change.notes == "Updated notes"

    def test_undo_action_resets_reviewed_change(self):
        """Test that undo resets a reviewed change to pending."""
        # Mark as reviewed
        self.service.mark_as_reviewed('MS_TEST01', self.change1.id)
        db.session.refresh(self.session)
        assert self.session.reviewed_count == 1

        # Undo
        change = self.service.undo_action('MS_TEST01', self.change1.id)

        assert change.status == 'pending'
        assert change.reviewed_at is None

        # Verify counter decremented
        db.session.refresh(self.session)
        assert self.session.reviewed_count == 0

    def test_undo_action_resets_skipped_change(self):
        """Test that undo resets a skipped change to pending."""
        # Skip change
        self.service.skip_change('MS_TEST01', self.change1.id)
        db.session.refresh(self.session)
        assert self.session.skipped_count == 1

        # Undo
        change = self.service.undo_action('MS_TEST01', self.change1.id)

        assert change.status == 'pending'

        # Verify counter decremented
        db.session.refresh(self.session)
        assert self.session.skipped_count == 0

    def test_undo_action_does_not_decrement_below_zero(self):
        """Test that undo does not decrement counters below zero."""
        # Undo a pending change (should not affect counters)
        self.service.undo_action('MS_TEST01', self.change1.id)

        db.session.refresh(self.session)
        assert self.session.reviewed_count == 0
        assert self.session.skipped_count == 0

    def test_mark_as_reviewed_raises_error_for_invalid_session(self):
        """Test that mark_as_reviewed raises error for invalid session."""
        with pytest.raises(ValueError, match="Session not found"):
            self.service.mark_as_reviewed('MS_INVALID', self.change1.id)

    def test_mark_as_reviewed_raises_error_for_invalid_change(self):
        """Test that mark_as_reviewed raises error for invalid change."""
        with pytest.raises(ValueError, match="Change .* not found"):
            self.service.mark_as_reviewed('MS_TEST01', 99999)

    def test_skip_change_raises_error_for_invalid_session(self):
        """Test that skip_change raises error for invalid session."""
        with pytest.raises(ValueError, match="Session not found"):
            self.service.skip_change('MS_INVALID', self.change1.id)

    def test_skip_change_raises_error_for_invalid_change(self):
        """Test that skip_change raises error for invalid change."""
        with pytest.raises(ValueError, match="Change .* not found"):
            self.service.skip_change('MS_TEST01', 99999)

    def test_save_notes_raises_error_for_invalid_session(self):
        """Test that save_notes raises error for invalid session."""
        with pytest.raises(ValueError, match="Session not found"):
            self.service.save_notes('MS_INVALID', self.change1.id, "notes")

    def test_save_notes_raises_error_for_invalid_change(self):
        """Test that save_notes raises error for invalid change."""
        with pytest.raises(ValueError, match="Change .* not found"):
            self.service.save_notes('MS_TEST01', 99999, "notes")

    def test_undo_action_raises_error_for_invalid_session(self):
        """Test that undo_action raises error for invalid session."""
        with pytest.raises(ValueError, match="Session not found"):
            self.service.undo_action('MS_INVALID', self.change1.id)

    def test_undo_action_raises_error_for_invalid_change(self):
        """Test that undo_action raises error for invalid change."""
        with pytest.raises(ValueError, match="Change .* not found"):
            self.service.undo_action('MS_TEST01', 99999)

    def test_multiple_actions_on_different_changes(self):
        """Test multiple actions on different changes."""
        # Mark change1 as reviewed
        self.service.mark_as_reviewed('MS_TEST01', self.change1.id)

        # Skip change2
        self.service.skip_change('MS_TEST01', self.change2.id)

        # Save notes on change3
        self.service.save_notes(
            'MS_TEST01',
            self.change3.id,
            "Important notes"
        )

        # Verify session counters
        db.session.refresh(self.session)
        assert self.session.reviewed_count == 1
        assert self.session.skipped_count == 1

        # Verify individual changes
        db.session.refresh(self.change1)
        db.session.refresh(self.change2)
        db.session.refresh(self.change3)

        assert self.change1.status == 'reviewed'
        assert self.change2.status == 'skipped'
        assert self.change3.status == 'pending'
        assert self.change3.notes == "Important notes"

    def test_session_updated_at_changes_on_actions(self):
        """Test that session updated_at timestamp changes on actions."""
        original_updated_at = self.session.updated_at

        # Perform action
        self.service.mark_as_reviewed('MS_TEST01', self.change1.id)

        # Verify updated_at changed
        db.session.refresh(self.session)
        assert self.session.updated_at > original_updated_at
