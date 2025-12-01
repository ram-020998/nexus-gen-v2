"""
Tests for Merge Guidance Service
"""

import pytest
from services.merge_guidance_service import (
    MergeGuidanceService,
    ConflictAnalyzer,
    RecommendationEngine
)


class MockChange:
    """Mock Change entity for testing."""

    def __init__(self, change_id, object_id, classification):
        self.id = change_id
        self.object_id = object_id
        self.classification = classification


class TestConflictAnalyzer:
    """Tests for ConflictAnalyzer."""

    def test_analyze_interface_conflict(self):
        """Test conflict analysis for Interface objects."""
        analyzer = ConflictAnalyzer()
        change = MockChange(1, 1, 'CONFLICT')
        object_data = {'object_type': 'Interface'}

        analysis = analyzer.analyze(change, object_data)

        assert analysis['conflict_type'] == 'SAIL_CODE'
        assert analysis['severity'] == 'HIGH'
        assert 'SAIL code' in analysis['overlap_areas']

    def test_analyze_process_model_conflict(self):
        """Test conflict analysis for Process Model objects."""
        analyzer = ConflictAnalyzer()
        change = MockChange(1, 1, 'CONFLICT')
        object_data = {'object_type': 'Process Model'}

        analysis = analyzer.analyze(change, object_data)

        assert analysis['conflict_type'] == 'PROCESS_STRUCTURE'
        assert analysis['severity'] == 'HIGH'

    def test_analyze_record_type_conflict(self):
        """Test conflict analysis for Record Type objects."""
        analyzer = ConflictAnalyzer()
        change = MockChange(1, 1, 'CONFLICT')
        object_data = {'object_type': 'Record Type'}

        analysis = analyzer.analyze(change, object_data)

        assert analysis['conflict_type'] == 'DATA_MODEL'
        assert analysis['severity'] == 'MEDIUM'

    def test_analyze_unknown_type_conflict(self):
        """Test conflict analysis for unknown object types."""
        analyzer = ConflictAnalyzer()
        change = MockChange(1, 1, 'CONFLICT')
        object_data = {'object_type': 'Unknown'}

        analysis = analyzer.analyze(change, object_data)

        assert analysis['conflict_type'] == 'GENERAL'
        assert analysis['severity'] == 'MEDIUM'


class TestRecommendationEngine:
    """Tests for RecommendationEngine."""

    def test_no_conflict_recommendation(self):
        """Test recommendation for NO_CONFLICT classification."""
        engine = RecommendationEngine()
        change = MockChange(1, 1, 'NO_CONFLICT')

        rec = engine.generate_recommendation(change)

        assert rec['action'] == 'AUTO_MERGE'
        assert rec['confidence'] == 'HIGH'
        assert 'Accept vendor version' in rec['steps']

    def test_new_recommendation(self):
        """Test recommendation for NEW classification."""
        engine = RecommendationEngine()
        change = MockChange(1, 1, 'NEW')

        rec = engine.generate_recommendation(change)

        assert rec['action'] == 'ACCEPT_VENDOR'
        assert rec['confidence'] == 'HIGH'

    def test_deleted_recommendation(self):
        """Test recommendation for DELETED classification."""
        engine = RecommendationEngine()
        change = MockChange(1, 1, 'DELETED')

        rec = engine.generate_recommendation(change)

        assert rec['action'] == 'MANUAL_REVIEW'
        assert rec['confidence'] == 'MEDIUM'

    def test_conflict_recommendation(self):
        """Test recommendation for CONFLICT classification."""
        engine = RecommendationEngine()
        change = MockChange(1, 1, 'CONFLICT')
        conflict_analysis = {'severity': 'HIGH'}

        rec = engine.generate_recommendation(change, conflict_analysis)

        assert rec['action'] == 'MANUAL_MERGE'
        assert rec['confidence'] == 'HIGH'
        assert rec['severity'] == 'HIGH'

    def test_unknown_classification_recommendation(self):
        """Test recommendation for unknown classification."""
        engine = RecommendationEngine()
        change = MockChange(1, 1, 'UNKNOWN')

        rec = engine.generate_recommendation(change)

        assert rec['action'] == 'MANUAL_REVIEW'
        assert rec['confidence'] == 'LOW'


class TestMergeGuidanceService:
    """Tests for MergeGuidanceService."""

    def test_generate_guidance_empty_list(self):
        """Test guidance generation with empty change list."""
        service = MergeGuidanceService()

        guidance = service.generate_guidance(1, [])

        assert len(guidance) == 0

    def test_generate_guidance_single_change(self):
        """Test guidance generation with single change."""
        service = MergeGuidanceService()
        changes = [MockChange(1, 1, 'NO_CONFLICT')]

        guidance = service.generate_guidance(1, changes)

        assert len(guidance) == 1
        assert guidance[0]['session_id'] == 1
        assert guidance[0]['change_id'] == 1
        assert guidance[0]['object_id'] == 1
        assert guidance[0]['classification'] == 'NO_CONFLICT'
        assert guidance[0]['recommendation']['action'] == 'AUTO_MERGE'

    def test_generate_guidance_multiple_changes(self):
        """Test guidance generation with multiple changes."""
        service = MergeGuidanceService()
        changes = [
            MockChange(1, 1, 'NO_CONFLICT'),
            MockChange(2, 2, 'CONFLICT'),
            MockChange(3, 3, 'NEW'),
            MockChange(4, 4, 'DELETED')
        ]

        guidance = service.generate_guidance(1, changes)

        assert len(guidance) == 4

        # Verify each guidance record
        assert guidance[0]['recommendation']['action'] == 'AUTO_MERGE'
        assert guidance[1]['recommendation']['action'] == 'MANUAL_MERGE'
        assert guidance[2]['recommendation']['action'] == 'ACCEPT_VENDOR'
        assert guidance[3]['recommendation']['action'] == 'MANUAL_REVIEW'

    def test_generate_guidance_with_conflict_analysis(self):
        """Test that CONFLICT changes get conflict analysis."""
        service = MergeGuidanceService()
        changes = [MockChange(1, 1, 'CONFLICT')]

        guidance = service.generate_guidance(1, changes)

        assert len(guidance) == 1
        assert guidance[0]['conflict_analysis'] is not None
        assert 'conflict_type' in guidance[0]['conflict_analysis']
        assert 'severity' in guidance[0]['conflict_analysis']

    def test_generate_guidance_no_conflict_analysis_for_non_conflict(self):
        """Test that non-CONFLICT changes don't get conflict analysis."""
        service = MergeGuidanceService()
        changes = [MockChange(1, 1, 'NO_CONFLICT')]

        guidance = service.generate_guidance(1, changes)

        assert len(guidance) == 1
        assert guidance[0]['conflict_analysis'] is None

    def test_get_guidance_stats(self):
        """Test guidance statistics calculation."""
        service = MergeGuidanceService()
        guidance_records = [
            {
                'recommendation': {'action': 'AUTO_MERGE'}
            },
            {
                'recommendation': {'action': 'AUTO_MERGE'}
            },
            {
                'recommendation': {'action': 'MANUAL_MERGE'}
            },
            {
                'recommendation': {'action': 'ACCEPT_VENDOR'}
            }
        ]

        stats = service._get_guidance_stats(guidance_records)

        assert stats['AUTO_MERGE'] == 2
        assert stats['MANUAL_MERGE'] == 1
        assert stats['ACCEPT_VENDOR'] == 1
        assert stats['MANUAL_REVIEW'] == 0

    def test_get_conflict_summary(self):
        """Test conflict summary retrieval."""
        service = MergeGuidanceService()

        summary = service.get_conflict_summary(1)

        assert 'total_conflicts' in summary
        assert 'by_severity' in summary
        assert 'by_type' in summary
        assert 'high_priority' in summary
