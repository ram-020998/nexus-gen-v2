"""
Tests for Excel Report Export Service

Tests Excel report generation functionality for merge sessions.
"""
import pytest
import os
from unittest.mock import Mock
from services.merge_assistant.report_export_service import (
    ReportExportService
)


class TestReportExportExcelService:
    """Test cases for Excel report generation"""

    @pytest.fixture
    def export_service(self):
        """Create export service instance"""
        return ReportExportService()

    @pytest.fixture
    def mock_merge_service(self):
        """Create mock merge service"""
        service = Mock()

        # Mock session
        session = Mock()
        session.id = 1
        session.reference_id = 'MRG_001'
        session.base_package_name = 'App v1.0'
        session.customized_package_name = 'App v1.0 Custom'
        session.new_vendor_package_name = 'App v2.0'

        service.get_session.return_value = session

        # Mock changes
        change1 = {
            'uuid': 'uuid-1',
            'name': 'TestInterface',
            'type': 'Interface',
            'classification': 'NO_CONFLICT',
            'change_type': 'MODIFIED',
            'vendor_change_type': 'MODIFIED',
            'customer_change_type': None,
            'base_object': {
                'sail_code': 'a!textField(label: "Old")',
                'fields': {}
            },
            'customer_object': None,
            'vendor_object': {
                'sail_code': 'a!textField(label: "New")',
                'fields': {}
            }
        }

        change2 = {
            'uuid': 'uuid-2',
            'name': 'TestConstant',
            'type': 'Constant',
            'classification': 'CONFLICT',
            'change_type': 'MODIFIED',
            'vendor_change_type': 'MODIFIED',
            'customer_change_type': 'MODIFIED',
            'base_object': {'fields': {'value': '10'}},
            'customer_object': {'fields': {'value': '20'}},
            'vendor_object': {'fields': {'value': '30'}}
        }

        service.filter_changes.side_effect = lambda **kwargs: {
            'NO_CONFLICT': [change1],
            'CONFLICT': [change2],
            'REMOVED_BUT_CUSTOMIZED': []
        }.get(kwargs.get('classification'), [])

        return service

    def test_generate_report_creates_excel_file(
        self,
        export_service,
        mock_merge_service,
        tmp_path
    ):
        """Test that generate_report creates an Excel file"""
        # Mock the output path to use tmp_path
        from config import Config
        original_get_output_path = Config.get_output_path
        Config.get_output_path = (
            lambda filename: tmp_path / filename
        )

        try:
            # Generate report
            output_path = export_service.generate_report(
                1,
                mock_merge_service
            )

            # Verify file was created
            assert os.path.exists(output_path)
            assert output_path.endswith('.xlsx')

            # Verify file is not empty
            assert os.path.getsize(output_path) > 0

        finally:
            # Restore original method
            Config.get_output_path = original_get_output_path

    def test_generate_report_raises_error_for_missing_session(
        self,
        export_service,
        mock_merge_service
    ):
        """Test that generate_report raises error for missing session"""
        mock_merge_service.get_session.return_value = None

        with pytest.raises(ValueError, match="Session .* not found"):
            export_service.generate_report(999, mock_merge_service)

    def test_generate_report_raises_error_for_no_changes(
        self,
        export_service,
        mock_merge_service
    ):
        """Test that generate_report raises error when no changes exist"""
        # Mock empty changes for all classifications
        mock_merge_service.filter_changes.side_effect = lambda **kwargs: []

        with pytest.raises(ValueError, match="No changes found"):
            export_service.generate_report(1, mock_merge_service)

    def test_build_report_data_enriches_changes(
        self,
        export_service,
        mock_merge_service
    ):
        """Test that _build_report_data enriches changes correctly"""
        changes = [
            {
                'uuid': 'uuid-1',
                'name': 'TestInterface',
                'type': 'Interface',
                'classification': 'NO_CONFLICT',
                'change_type': 'MODIFIED',
                'vendor_change_type': 'MODIFIED',
                'customer_change_type': None,
                'base_object': {
                    'sail_code': 'a!textField(label: "Old")'
                },
                'customer_object': None,
                'vendor_object': {
                    'sail_code': 'a!textField(label: "New")'
                }
            }
        ]

        report_data = export_service._build_report_data(
            changes,
            mock_merge_service
        )

        # Verify enrichment
        assert len(report_data) == 1
        change = report_data[0]

        # Verify required fields
        assert 'serial_number' in change
        assert 'category' in change
        assert 'object_name' in change
        assert 'object_uuid' in change
        assert 'change_description' in change
        assert 'sail_changes' in change
        assert 'complexity' in change
        assert 'estimated_time' in change
        assert 'comments' in change

        # Verify values
        assert change['serial_number'] == 1
        assert change['object_name'] == 'TestInterface'
        assert change['complexity'] in ['Low', 'Medium', 'High']

    def test_generate_change_description_for_added(
        self,
        export_service
    ):
        """Test change description for added objects"""
        change = {
            'change_type': 'ADDED',
            'vendor_change_type': 'ADDED',
            'classification': 'NO_CONFLICT'
        }

        description = export_service._generate_change_description(change)
        assert description == "New object added in vendor release"

    def test_generate_change_description_for_removed(
        self,
        export_service
    ):
        """Test change description for removed objects"""
        change = {
            'change_type': 'REMOVED',
            'vendor_change_type': 'REMOVED',
            'classification': 'REMOVED_BUT_CUSTOMIZED'
        }

        description = export_service._generate_change_description(change)
        assert "removed" in description.lower()
        assert "customized" in description.lower()

    def test_generate_change_description_for_conflict(
        self,
        export_service
    ):
        """Test change description for conflicts"""
        change = {
            'change_type': 'MODIFIED',
            'vendor_change_type': 'MODIFIED',
            'customer_change_type': 'MODIFIED',
            'classification': 'CONFLICT'
        }

        description = export_service._generate_change_description(change)
        assert "Conflicting" in description
        assert "Vendor" in description
        assert "Customer" in description

    def test_extract_sail_changes_with_code(
        self,
        export_service
    ):
        """Test SAIL code extraction when code exists"""
        base_obj = {'sail_code': 'a!textField(label: "Old")'}
        vendor_obj = {'sail_code': 'a!textField(label: "New")'}

        result = export_service._extract_sail_changes(
            base_obj,
            None,
            vendor_obj
        )

        assert "SAIL Code Updated" in result
        assert "New" in result

    def test_extract_sail_changes_truncates_long_code(
        self,
        export_service
    ):
        """Test SAIL code truncation for long code"""
        long_code = "a!textField(label: 'test')" * 100
        base_obj = {'sail_code': 'short'}
        vendor_obj = {'sail_code': long_code}

        result = export_service._extract_sail_changes(
            base_obj,
            None,
            vendor_obj
        )

        # Should be truncated
        assert len(result) <= 510  # 500 + "..." + some header text
        assert "..." in result

    def test_format_classification(self, export_service):
        """Test classification formatting"""
        assert (
            export_service._format_classification('NO_CONFLICT') ==
            'No Conflict'
        )
        assert (
            export_service._format_classification('CONFLICT') ==
            'Conflicting'
        )
        assert (
            export_service._format_classification('CUSTOMER_ONLY') ==
            'Customer Only'
        )
        assert (
            export_service._format_classification('REMOVED_BUT_CUSTOMIZED')
            == 'Deprecated'
        )

    def test_generate_filename(self, export_service):
        """Test filename generation"""
        session = Mock()
        session.reference_id = 'MRG_001'

        filename = export_service._generate_filename(session)

        assert filename.startswith('merge_report_MRG_001_')
        assert filename.endswith('.xlsx')
