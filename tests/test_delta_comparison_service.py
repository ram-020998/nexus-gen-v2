"""
Tests for Delta Comparison Service

Tests the comparison between Package A (Base) and Package C (New Vendor)
to identify NEW, MODIFIED, and DEPRECATED objects.
"""
import os
import unittest
from tests.base_test import BaseTestCase
from models import db, MergeSession
from services.package_extraction_service import PackageExtractionService
from services.delta_comparison_service import DeltaComparisonService
from repositories.delta_comparison_repository import (
    DeltaComparisonRepository
)
from domain.enums import ChangeCategory


class TestDeltaComparisonService(BaseTestCase):
    """Test DeltaComparisonService functionality"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.extraction_service = PackageExtractionService()
        self.delta_service = DeltaComparisonService()
        self.delta_repo = DeltaComparisonRepository()

        # Create test session
        self.session = MergeSession(
            reference_id='TEST_DELTA_001',
            status='processing'
        )
        db.session.add(self.session)
        db.session.commit()

        # Paths to test packages
        self.base_package_path = (
            'applicationArtifacts/Three Way Testing Files/V2/'
            'Test Application - Base Version.zip'
        )
        self.new_vendor_package_path = (
            'applicationArtifacts/Three Way Testing Files/V2/'
            'Test Application Vendor New Version.zip'
        )

    def test_delta_comparison_basic(self):
        """Test basic delta comparison with real test packages"""
        # Skip if test packages don't exist
        if not os.path.exists(self.base_package_path):
            self.skipTest(
                f"Test package not found: {self.base_package_path}"
            )
        if not os.path.exists(self.new_vendor_package_path):
            self.skipTest(
                f"Test package not found: {self.new_vendor_package_path}"
            )

        # Extract both packages
        base_package = self.extraction_service.extract_package(
            session_id=self.session.id,
            zip_path=self.base_package_path,
            package_type='base'
        )

        new_vendor_package = self.extraction_service.extract_package(
            session_id=self.session.id,
            zip_path=self.new_vendor_package_path,
            package_type='new_vendor'
        )

        # Perform delta comparison
        delta_changes = self.delta_service.compare(
            session_id=self.session.id,
            base_package_id=base_package.id,
            new_vendor_package_id=new_vendor_package.id
        )

        # Verify delta changes were returned
        self.assertIsNotNone(delta_changes)
        self.assertIsInstance(delta_changes, list)

        # Verify results were stored in database
        stored_results = self.delta_repo.get_by_session(self.session.id)
        self.assertEqual(len(stored_results), len(delta_changes))

        # Verify we have at least one category
        counts = self.delta_repo.count_by_category(self.session.id)
        self.assertGreater(len(counts), 0, "Should have at least one category")

        # Verify total matches sum of categories
        total_from_categories = sum(counts.values())
        self.assertEqual(
            len(delta_changes),
            total_from_categories,
            "Total should match sum of categories"
        )

        print(f"\nDelta comparison results:")
        print(f"  NEW: {counts.get('NEW', 0)}")
        print(f"  MODIFIED: {counts.get('MODIFIED', 0)}")
        print(f"  DEPRECATED: {counts.get('DEPRECATED', 0)}")
        print(f"  Total: {len(delta_changes)}")

    def test_delta_statistics(self):
        """Test delta statistics retrieval"""
        # Skip if test packages don't exist
        if not os.path.exists(self.base_package_path):
            self.skipTest(
                f"Test package not found: {self.base_package_path}"
            )
        if not os.path.exists(self.new_vendor_package_path):
            self.skipTest(
                f"Test package not found: {self.new_vendor_package_path}"
            )

        # Extract both packages
        base_package = self.extraction_service.extract_package(
            session_id=self.session.id,
            zip_path=self.base_package_path,
            package_type='base'
        )

        new_vendor_package = self.extraction_service.extract_package(
            session_id=self.session.id,
            zip_path=self.new_vendor_package_path,
            package_type='new_vendor'
        )

        # Perform delta comparison
        self.delta_service.compare(
            session_id=self.session.id,
            base_package_id=base_package.id,
            new_vendor_package_id=new_vendor_package.id
        )

        # Get statistics
        stats = self.delta_service.get_delta_statistics(self.session.id)

        # Verify statistics structure
        self.assertIn('total', stats)
        self.assertIn('by_category', stats)
        self.assertIn('version_changes', stats)
        self.assertIn('content_changes', stats)

        # Verify counts are non-negative
        self.assertGreaterEqual(stats['total'], 0)
        self.assertGreaterEqual(stats['version_changes'], 0)
        self.assertGreaterEqual(stats['content_changes'], 0)


if __name__ == '__main__':
    unittest.main()
