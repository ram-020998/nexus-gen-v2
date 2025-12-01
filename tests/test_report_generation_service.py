"""
Tests for Report Generation Service

Tests report generation including:
- Word document generation
- Report caching
- Data gathering
- Error handling
"""

import os
import pytest

from models import (
    db, MergeSession, Change, ObjectLookup, Package, ObjectVersion
)
from services.report_generation_service import ReportGenerationService
from tests.base_test import BaseTestCase


class TestReportGenerationService(BaseTestCase):
    """Test suite for ReportGenerationService."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.service = ReportGenerationService()

        # Create test session
        self.session = MergeSession(
            reference_id='MS_REPORT01',
            status='ready',
            total_changes=3,
            reviewed_count=1,
            skipped_count=1,
            estimated_complexity='Medium',
            estimated_time_hours=2.5
        )
        db.session.add(self.session)
        db.session.flush()

        # Create test packages
        self.packages = []
        for pkg_type in ['base', 'customized', 'new_vendor']:
            pkg = Package(
                session_id=self.session.id,
                package_type=pkg_type,
                filename=f'{pkg_type}_package.zip',
                total_objects=10
            )
            db.session.add(pkg)
            self.packages.append(pkg)
        db.session.flush()

        # Create test objects
        self.objects = []
        for i in range(3):
            obj = ObjectLookup(
                uuid=f'uuid-{i:03d}',
                name=f'Test Object {i}',
                object_type='interface',
                description=f'Test description {i}'
            )
            db.session.add(obj)
            self.objects.append(obj)
        db.session.flush()

        # Create test changes
        classifications = ['NO_CONFLICT', 'CONFLICT', 'NEW']
        for i, obj in enumerate(self.objects):
            change = Change(
                session_id=self.session.id,
                object_id=obj.id,
                classification=classifications[i],
                vendor_change_type='MODIFIED',
                customer_change_type='MODIFIED' if i == 1 else None,
                display_order=i + 1,
                status='reviewed' if i == 0 else (
                    'skipped' if i == 1 else 'pending'
                ),
                notes=f'Test notes {i}' if i == 0 else None
            )
            db.session.add(change)

        # Create object versions with SAIL code
        vendor_pkg = next(
            p for p in self.packages if p.package_type == 'new_vendor'
        )
        for obj in self.objects:
            version = ObjectVersion(
                object_id=obj.id,
                package_id=vendor_pkg.id,
                version_uuid=f'version-{obj.uuid}',
                sail_code='a!localVariables(\n  test: "value"\n)'
            )
            db.session.add(version)

        db.session.commit()

    def tearDown(self):
        """Clean up after tests."""
        # Clean up generated reports
        if os.path.exists(self.service.reports_dir):
            for filename in os.listdir(self.service.reports_dir):
                file_path = os.path.join(
                    self.service.reports_dir, filename
                )
                if os.path.isfile(file_path):
                    os.remove(file_path)
        super().tearDown()

    def test_generate_excel_report(self):
        """Test generating an Excel report."""
        # Generate report
        report_path = self.service.generate_report(
            'MS_REPORT01',
            format='xlsx'
        )

        # Verify report was created
        assert os.path.exists(report_path)
        assert report_path.endswith('.xlsx')
        assert 'MS_REPORT01' in report_path

        # Verify file is not empty
        assert os.path.getsize(report_path) > 0

    def test_invalid_format(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            self.service.generate_report('MS_REPORT01', format='docx')
        assert 'Invalid format' in str(exc_info.value)

    def test_session_not_found(self):
        """Test that non-existent session raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            self.service.generate_report('MS_NONEXISTENT', format='xlsx')
        assert 'Session not found' in str(exc_info.value)

    def test_report_caching(self):
        """Test that reports are cached for 1 hour."""
        # Generate report first time
        report_path1 = self.service.generate_report(
            'MS_REPORT01',
            format='xlsx'
        )

        # Get modification time
        mtime1 = os.path.getmtime(report_path1)

        # Generate report second time (should use cache)
        report_path2 = self.service.generate_report(
            'MS_REPORT01',
            format='xlsx'
        )

        # Verify same file was returned
        assert report_path1 == report_path2

        # Verify file was not regenerated
        mtime2 = os.path.getmtime(report_path2)
        assert mtime1 == mtime2

    def test_gather_report_data(self):
        """Test gathering report data."""
        data = self.service._gather_report_data(self.session)

        # Verify session data
        assert data['session'] == self.session

        # Verify package data
        assert 'base' in data['packages']
        assert 'customized' in data['packages']
        assert 'new_vendor' in data['packages']

        # Verify changes data
        assert len(data['changes']) == 3
        assert data['changes'][0]['object_name'] == 'Test Object 0'
        assert data['changes'][0]['classification'] == 'NO_CONFLICT'

        # Verify statistics
        stats = data['statistics']
        assert stats['total_changes'] == 3
        assert stats['reviewed_count'] == 1
        assert stats['skipped_count'] == 1
        assert stats['pending_count'] == 1
        assert stats['by_classification']['NO_CONFLICT'] == 1
        assert stats['by_classification']['CONFLICT'] == 1
        assert stats['by_classification']['NEW'] == 1

    def test_clear_cache_specific_session(self):
        """Test clearing cache for specific session."""
        # Generate report
        report_path = self.service.generate_report(
            'MS_REPORT01',
            format='xlsx'
        )
        assert os.path.exists(report_path)

        # Clear cache for this session
        self.service.clear_cache('MS_REPORT01')

        # Verify report was deleted
        assert not os.path.exists(report_path)

    def test_clear_cache_all(self):
        """Test clearing all cached reports."""
        # Generate report
        report_path = self.service.generate_report(
            'MS_REPORT01',
            format='xlsx'
        )
        assert os.path.exists(report_path)

        # Clear all cache
        self.service.clear_cache()

        # Verify report was deleted
        assert not os.path.exists(report_path)

    def test_reports_directory_created(self):
        """Test that reports directory is created if it doesn't exist."""
        # Remove directory if it exists
        if os.path.exists(self.service.reports_dir):
            for filename in os.listdir(self.service.reports_dir):
                os.remove(
                    os.path.join(self.service.reports_dir, filename)
                )
            os.rmdir(self.service.reports_dir)

        # Create new service instance
        service = ReportGenerationService()

        # Verify directory was created
        assert os.path.exists(service.reports_dir)
