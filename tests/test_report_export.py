"""
Tests for Report Export Service

Tests JSON and PDF export functionality for merge reports.
"""
import json
import pytest
from services.merge_assistant.report_export_service import (
    ReportExportService
)


class TestReportExportService:
    """Test cases for ReportExportService"""

    @pytest.fixture
    def export_service(self):
        """Create export service instance"""
        return ReportExportService()

    @pytest.fixture
    def sample_report_data(self):
        """Create sample report data for testing"""
        return {
            'session': {
                'reference_id': 'MRG_001',
                'status': 'completed',
                'created_at': '2024-01-01T10:00:00',
                'updated_at': '2024-01-01T11:00:00'
            },
            'summary': {
                'packages': {
                    'base': 'App v1.0',
                    'customized': 'App v1.0 Custom',
                    'new_vendor': 'App v2.0'
                },
                'estimated_complexity': 'MEDIUM',
                'estimated_time_hours': 4,
                'breakdown_by_type': {
                    'interfaces': {
                        'no_conflict': 10,
                        'conflict': 5
                    }
                }
            },
            'statistics': {
                'total_changes': 50,
                'reviewed': 30,
                'skipped': 10,
                'pending': 10,
                'conflicts': 15,
                'processing_time_seconds': 120
            },
            'changes': [
                {
                    'uuid': 'uuid-1',
                    'name': 'TestInterface',
                    'type': 'Interface',
                    'classification': 'NO_CONFLICT',
                    'review_status': 'reviewed',
                    'user_notes': 'Looks good',
                    'reviewed_at': '2024-01-01T10:30:00',
                    'merge_guidance': {
                        'strategy': 'ACCEPT_VENDOR',
                        'recommendations': ['Accept vendor changes']
                    },
                    'dependencies': {
                        'parents': [],
                        'children': []
                    }
                },
                {
                    'uuid': 'uuid-2',
                    'name': 'TestRule',
                    'type': 'Expression Rule',
                    'classification': 'CONFLICT',
                    'review_status': 'pending',
                    'user_notes': None,
                    'reviewed_at': None
                }
            ],
            'changes_by_category': {
                'NO_CONFLICT': [
                    {
                        'uuid': 'uuid-1',
                        'name': 'TestInterface',
                        'type': 'Interface',
                        'classification': 'NO_CONFLICT',
                        'review_status': 'reviewed',
                        'user_notes': 'Looks good'
                    }
                ],
                'CONFLICT': [
                    {
                        'uuid': 'uuid-2',
                        'name': 'TestRule',
                        'type': 'Expression Rule',
                        'classification': 'CONFLICT',
                        'review_status': 'pending',
                        'user_notes': None
                    }
                ],
                'CUSTOMER_ONLY': [],
                'REMOVED_BUT_CUSTOMIZED': []
            }
        }

    def test_export_json_structure(
        self,
        export_service,
        sample_report_data
    ):
        """Test JSON export creates valid JSON with correct structure"""
        json_str = export_service.export_json(sample_report_data)

        # Parse JSON to verify it's valid
        data = json.loads(json_str)

        # Verify top-level structure
        assert 'metadata' in data
        assert 'session' in data
        assert 'packages' in data
        assert 'statistics' in data
        assert 'summary' in data
        assert 'changes' in data
        assert 'changes_by_category' in data

        # Verify metadata
        assert data['metadata']['format_version'] == '1.0'
        assert data['metadata']['report_type'] == 'three_way_merge'
        assert 'export_date' in data['metadata']

        # Verify session info
        assert data['session']['reference_id'] == 'MRG_001'
        assert data['session']['status'] == 'completed'

        # Verify statistics
        assert data['statistics']['total_changes'] == 50
        assert data['statistics']['reviewed'] == 30
        assert data['statistics']['conflicts'] == 15

    def test_export_json_includes_changes(
        self,
        export_service,
        sample_report_data
    ):
        """Test JSON export includes all changes with essential info"""
        json_str = export_service.export_json(sample_report_data)
        data = json.loads(json_str)

        # Verify changes are included
        assert len(data['changes']) == 2

        # Verify first change
        change1 = data['changes'][0]
        assert change1['uuid'] == 'uuid-1'
        assert change1['name'] == 'TestInterface'
        assert change1['type'] == 'Interface'
        assert change1['classification'] == 'NO_CONFLICT'
        assert change1['review_status'] == 'reviewed'
        assert change1['user_notes'] == 'Looks good'

        # Verify merge guidance is included
        assert 'merge_guidance' in change1
        assert change1['merge_guidance']['strategy'] == 'ACCEPT_VENDOR'

        # Verify dependencies are included
        assert 'dependencies' in change1

    def test_export_json_handles_missing_optional_fields(
        self,
        export_service,
        sample_report_data
    ):
        """Test JSON export handles changes without optional fields"""
        json_str = export_service.export_json(sample_report_data)
        data = json.loads(json_str)

        # Second change has no merge guidance or dependencies
        change2 = data['changes'][1]
        assert change2['uuid'] == 'uuid-2'
        assert change2['user_notes'] is None
        assert change2['reviewed_at'] is None

    def test_export_pdf_html_generates_valid_html(
        self,
        export_service,
        sample_report_data
    ):
        """Test PDF HTML export generates valid HTML"""
        html = export_service.export_pdf_html(sample_report_data)

        # Verify it's HTML
        assert html.startswith('<!DOCTYPE html>')
        assert '<html>' in html
        assert '</html>' in html

        # Verify essential content is present
        assert 'MRG_001' in html
        assert 'Three-Way Merge Report' in html
        assert 'TestInterface' in html
        assert 'TestRule' in html

        # Verify statistics are present
        assert '50' in html  # total changes
        assert '30' in html  # reviewed
        assert '15' in html  # conflicts

        # Verify package names are present
        assert 'App v1.0' in html
        assert 'App v1.0 Custom' in html
        assert 'App v2.0' in html

    def test_export_pdf_html_includes_styling(
        self,
        export_service,
        sample_report_data
    ):
        """Test PDF HTML includes print-friendly styling"""
        html = export_service.export_pdf_html(sample_report_data)

        # Verify CSS is present
        assert '<style>' in html
        assert '@media print' in html
        assert 'page-break' in html

        # Verify print-friendly elements
        assert 'font-family' in html
        assert 'color' in html

    def test_format_datetime(self, export_service):
        """Test datetime formatting"""
        # Test ISO format
        result = export_service._format_datetime('2024-01-01T10:30:00')
        assert '2024-01-01' in result
        assert '10:30:00' in result

        # Test with timezone
        result = export_service._format_datetime(
            '2024-01-01T10:30:00+00:00'
        )
        assert '2024-01-01' in result

        # Test invalid format returns original
        result = export_service._format_datetime('invalid')
        assert result == 'invalid'
