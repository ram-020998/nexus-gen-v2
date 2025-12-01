"""
Tests for Session Statistics Service

Tests statistical analysis and metrics including:
- Complexity calculation
- Review time estimation
- Progress metrics
- Caching behavior
"""

import pytest

from models import db, MergeSession, Change, ObjectLookup
from services.session_statistics_service import SessionStatisticsService
from tests.base_test import BaseTestCase


class TestSessionStatisticsService(BaseTestCase):
    """Test suite for SessionStatisticsService."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.service = SessionStatisticsService()
        # Clear cache before each test
        self.service.cache.cache.clear()

        # Create test session
        self.session = MergeSession(
            reference_id='MS_STATS01',
            status='ready',
            total_changes=10,
            reviewed_count=3,
            skipped_count=2
        )
        db.session.add(self.session)
        db.session.flush()

        # Create test objects of various types
        self.objects = []
        object_types = [
            'interface', 'interface', 'process_model', 'process_model',
            'record_type', 'expression_rule', 'integration',
            'web_api', 'constant', 'group'
        ]

        for i, obj_type in enumerate(object_types):
            obj = ObjectLookup(
                uuid=f'uuid-{i:03d}',
                name=f'Test {obj_type} {i}',
                object_type=obj_type,
                description=f'Test description {i}'
            )
            self.objects.append(obj)
            db.session.add(obj)

        db.session.flush()

        # Create test changes with various classifications
        classifications = [
            'NO_CONFLICT', 'NO_CONFLICT', 'CONFLICT', 'CONFLICT',
            'CONFLICT', 'NEW', 'NEW', 'DELETED', 'NO_CONFLICT',
            'CONFLICT'
        ]

        statuses = [
            'reviewed', 'reviewed', 'reviewed', 'skipped',
            'skipped', 'pending', 'pending', 'pending',
            'pending', 'pending'
        ]

        for i, (obj, classification, status) in enumerate(
            zip(self.objects, classifications, statuses)
        ):
            change = Change(
                session_id=self.session.id,
                object_id=obj.id,
                classification=classification,
                vendor_change_type='MODIFIED',
                display_order=i + 1,
                status=status
            )
            db.session.add(change)

        db.session.commit()

    def test_calculate_complexity_low(self):
        """Test complexity calculation for low complexity session."""
        # Create a simple session with few changes and no conflicts
        simple_session = MergeSession(
            reference_id='MS_SIMPLE',
            status='ready',
            total_changes=3
        )
        db.session.add(simple_session)
        db.session.flush()

        # Add simple changes
        for i in range(3):
            obj = ObjectLookup(
                uuid=f'simple-{i}',
                name=f'Simple Object {i}',
                object_type='interface'
            )
            db.session.add(obj)
            db.session.flush()

            change = Change(
                session_id=simple_session.id,
                object_id=obj.id,
                classification='NO_CONFLICT',
                vendor_change_type='MODIFIED',
                display_order=i + 1
            )
            db.session.add(change)

        db.session.commit()

        complexity = self.service.calculate_complexity(simple_session.id)
        assert complexity == 'Low'

    def test_calculate_complexity_medium(self):
        """Test complexity calculation for medium complexity session."""
        complexity = self.service.calculate_complexity(self.session.id)
        # With 10 changes and 4 conflicts, should be Medium
        assert complexity in ['Medium', 'High']

    def test_calculate_complexity_high(self):
        """Test complexity calculation for high complexity session."""
        # Create a complex session with many changes and conflicts
        complex_session = MergeSession(
            reference_id='MS_COMPLEX',
            status='ready',
            total_changes=50
        )
        db.session.add(complex_session)
        db.session.flush()

        # Add many conflicting changes
        for i in range(50):
            obj = ObjectLookup(
                uuid=f'complex-{i}',
                name=f'Complex Object {i}',
                object_type='process_model'
            )
            db.session.add(obj)
            db.session.flush()

            change = Change(
                session_id=complex_session.id,
                object_id=obj.id,
                classification='CONFLICT',
                vendor_change_type='MODIFIED',
                display_order=i + 1
            )
            db.session.add(change)

        db.session.commit()

        complexity = self.service.calculate_complexity(complex_session.id)
        assert complexity == 'High'

    def test_calculate_complexity_raises_error_for_invalid_session(self):
        """Test that calculate_complexity raises error for invalid session."""
        with pytest.raises(ValueError, match="Session not found"):
            self.service.calculate_complexity(99999)

    def test_estimate_review_time_basic(self):
        """Test basic review time estimation."""
        time = self.service.estimate_review_time(self.session.id)

        # Should be a positive float
        assert isinstance(time, float)
        assert time > 0

        # With 10 changes, should be at least 0.5 hours (base time)
        assert time >= 0.5

    def test_estimate_review_time_with_conflicts(self):
        """Test that conflicts increase estimated time."""
        # Session has 4 conflicts, so time should be higher
        time = self.service.estimate_review_time(self.session.id)

        # Base time (10 * 5 min) + conflict time (4 * 10 min)
        # + complex objects (2 PM * 5 + 1 RT * 3)
        # = 50 + 40 + 13 = 103 minutes = ~1.7 hours
        assert time >= 1.5

    def test_estimate_review_time_zero_changes(self):
        """Test review time estimation for session with no changes."""
        empty_session = MergeSession(
            reference_id='MS_EMPTY',
            status='ready',
            total_changes=0
        )
        db.session.add(empty_session)
        db.session.commit()

        time = self.service.estimate_review_time(empty_session.id)
        assert time == 0.0

    def test_estimate_review_time_raises_error_for_invalid_session(self):
        """Test that estimate_review_time raises error for invalid session."""
        with pytest.raises(ValueError, match="Session not found"):
            self.service.estimate_review_time(99999)

    def test_get_progress_metrics_basic(self):
        """Test basic progress metrics retrieval."""
        metrics = self.service.get_progress_metrics(self.session.id)

        # Verify structure
        assert 'total_changes' in metrics
        assert 'reviewed_count' in metrics
        assert 'skipped_count' in metrics
        assert 'pending_count' in metrics
        assert 'progress_percent' in metrics
        assert 'by_classification' in metrics
        assert 'by_object_type' in metrics
        assert 'by_status' in metrics

        # Verify values
        assert metrics['total_changes'] == 10
        assert metrics['reviewed_count'] == 3
        assert metrics['skipped_count'] == 2
        assert metrics['pending_count'] == 5

    def test_get_progress_metrics_progress_percentage(self):
        """Test progress percentage calculation."""
        metrics = self.service.get_progress_metrics(self.session.id)

        # 3 reviewed + 2 skipped = 5 completed out of 10 = 50%
        assert metrics['progress_percent'] == 50.0

    def test_get_progress_metrics_by_classification(self):
        """Test classification breakdown in metrics."""
        metrics = self.service.get_progress_metrics(self.session.id)

        by_classification = metrics['by_classification']

        # Verify all classifications are present
        assert 'NO_CONFLICT' in by_classification
        assert 'CONFLICT' in by_classification
        assert 'NEW' in by_classification
        assert 'DELETED' in by_classification

        # Verify counts (from our test data)
        assert by_classification['NO_CONFLICT'] == 3
        assert by_classification['CONFLICT'] == 4
        assert by_classification['NEW'] == 2
        assert by_classification['DELETED'] == 1

    def test_get_progress_metrics_by_object_type(self):
        """Test object type breakdown in metrics."""
        metrics = self.service.get_progress_metrics(self.session.id)

        by_object_type = metrics['by_object_type']

        # Verify some object types are present
        assert 'interface' in by_object_type
        assert 'process_model' in by_object_type
        assert 'record_type' in by_object_type

        # Verify counts
        assert by_object_type['interface'] == 2
        assert by_object_type['process_model'] == 2
        assert by_object_type['record_type'] == 1

    def test_get_progress_metrics_by_status(self):
        """Test status breakdown in metrics."""
        metrics = self.service.get_progress_metrics(self.session.id)

        by_status = metrics['by_status']

        # Verify all statuses are present
        assert 'pending' in by_status
        assert 'reviewed' in by_status
        assert 'skipped' in by_status

        # Verify counts
        assert by_status['pending'] == 5
        assert by_status['reviewed'] == 3
        assert by_status['skipped'] == 2

    def test_get_progress_metrics_raises_error_for_invalid_session(self):
        """Test that get_progress_metrics raises error for invalid session."""
        with pytest.raises(ValueError, match="Session not found"):
            self.service.get_progress_metrics(99999)

    def test_get_progress_metrics_caching(self):
        """Test that progress metrics are cached."""
        # First call - should cache
        metrics1 = self.service.get_progress_metrics(self.session.id)

        # Second call - should return cached value
        metrics2 = self.service.get_progress_metrics(self.session.id)

        # Should be the same object (from cache)
        assert metrics1 == metrics2

    def test_invalidate_cache(self):
        """Test cache invalidation."""
        # Get metrics to populate cache
        metrics1 = self.service.get_progress_metrics(self.session.id)

        # Verify it's cached
        cached = self.service.cache.get_statistics(self.session.id)
        assert cached is not None

        # Invalidate cache
        self.service.invalidate_cache(self.session.id)

        # Verify cache is cleared
        cached_after = self.service.cache.get_statistics(self.session.id)
        assert cached_after is None

        # Get metrics again - should recalculate
        metrics2 = self.service.get_progress_metrics(self.session.id)

        # Values should be the same, but recalculated
        assert metrics1 == metrics2

    def test_cache_invalidation_on_change_action(self):
        """Test that cache is invalidated when changes are updated."""
        from services.change_action_service import ChangeActionService

        action_service = ChangeActionService()

        # Get initial metrics
        metrics1 = self.service.get_progress_metrics(self.session.id)
        initial_reviewed = metrics1['reviewed_count']

        # Mark a pending change as reviewed
        pending_change = db.session.query(Change).filter_by(
            session_id=self.session.id,
            status='pending'
        ).first()

        action_service.mark_as_reviewed(
            'MS_STATS01',
            pending_change.id
        )

        # Get metrics again - should reflect the change
        metrics2 = self.service.get_progress_metrics(self.session.id)

        # Reviewed count should have increased
        assert metrics2['reviewed_count'] == initial_reviewed + 1

    def test_progress_metrics_zero_changes(self):
        """Test progress metrics for session with no changes."""
        empty_session = MergeSession(
            reference_id='MS_EMPTY2',
            status='ready',
            total_changes=0
        )
        db.session.add(empty_session)
        db.session.commit()

        metrics = self.service.get_progress_metrics(empty_session.id)

        assert metrics['total_changes'] == 0
        assert metrics['reviewed_count'] == 0
        assert metrics['skipped_count'] == 0
        assert metrics['pending_count'] == 0
        assert metrics['progress_percent'] == 0

    def test_complexity_with_process_models(self):
        """Test that process models increase complexity."""
        # Create session with mostly process models
        pm_session = MergeSession(
            reference_id='MS_PM',
            status='ready',
            total_changes=10
        )
        db.session.add(pm_session)
        db.session.flush()

        for i in range(10):
            obj = ObjectLookup(
                uuid=f'pm-{i}',
                name=f'Process Model {i}',
                object_type='process_model'
            )
            db.session.add(obj)
            db.session.flush()

            change = Change(
                session_id=pm_session.id,
                object_id=obj.id,
                classification='NO_CONFLICT',
                vendor_change_type='MODIFIED',
                display_order=i + 1
            )
            db.session.add(change)

        db.session.commit()

        complexity = self.service.calculate_complexity(pm_session.id)
        # Should be at least Medium due to complex object types
        assert complexity in ['Medium', 'High']

    def test_review_time_with_process_models(self):
        """Test that process models increase review time."""
        # Create session with process models
        pm_session = MergeSession(
            reference_id='MS_PM2',
            status='ready',
            total_changes=5
        )
        db.session.add(pm_session)
        db.session.flush()

        for i in range(5):
            obj = ObjectLookup(
                uuid=f'pm2-{i}',
                name=f'Process Model {i}',
                object_type='process_model'
            )
            db.session.add(obj)
            db.session.flush()

            change = Change(
                session_id=pm_session.id,
                object_id=obj.id,
                classification='NO_CONFLICT',
                vendor_change_type='MODIFIED',
                display_order=i + 1
            )
            db.session.add(change)

        db.session.commit()

        time = self.service.estimate_review_time(pm_session.id)

        # Base time (5 * 5 min) + PM time (5 * 5 min)
        # = 25 + 25 = 50 minutes = ~0.8 hours
        assert time >= 0.8
