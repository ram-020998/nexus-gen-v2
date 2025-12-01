"""
Tests for Customer Comparison Service

Tests the comparison of delta objects against Package B (Customer)
to identify customer modifications and potential conflicts.
"""
import os
import unittest
from tests.base_test import BaseTestCase
from models import db, MergeSession
from services.package_extraction_service import PackageExtractionService
from services.delta_comparison_service import DeltaComparisonService
from services.customer_comparison_service import CustomerComparisonService
from domain.entities import CustomerModification


class TestCustomerComparisonService(BaseTestCase):
    """Test CustomerComparisonService functionality"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.extraction_service = PackageExtractionService()
        self.delta_service = DeltaComparisonService()
        self.customer_service = CustomerComparisonService()

        # Create test session
        self.session = MergeSession(
            reference_id='TEST_CUSTOMER_001',
            status='processing'
        )
        db.session.add(self.session)
        db.session.commit()

        # Paths to test packages
        self.base_package_path = (
            'applicationArtifacts/Three Way Testing Files/V2/'
            'Test Application - Base Version.zip'
        )
        self.customer_package_path = (
            'applicationArtifacts/Three Way Testing Files/V2/'
            'Test Application Customer Version.zip'
        )
        self.new_vendor_package_path = (
            'applicationArtifacts/Three Way Testing Files/V2/'
            'Test Application Vendor New Version.zip'
        )

    def test_customer_comparison_basic(self):
        """Test basic customer comparison with real test packages"""
        # Skip if test packages don't exist
        if not os.path.exists(self.base_package_path):
            self.skipTest(
                f"Test package not found: {self.base_package_path}"
            )
        if not os.path.exists(self.customer_package_path):
            self.skipTest(
                f"Test package not found: {self.customer_package_path}"
            )
        if not os.path.exists(self.new_vendor_package_path):
            self.skipTest(
                f"Test package not found: {self.new_vendor_package_path}"
            )

        # Extract all three packages
        base_package = self.extraction_service.extract_package(
            session_id=self.session.id,
            zip_path=self.base_package_path,
            package_type='base'
        )

        customer_package = self.extraction_service.extract_package(
            session_id=self.session.id,
            zip_path=self.customer_package_path,
            package_type='customized'
        )

        new_vendor_package = self.extraction_service.extract_package(
            session_id=self.session.id,
            zip_path=self.new_vendor_package_path,
            package_type='new_vendor'
        )

        # Perform delta comparison (A→C)
        delta_changes = self.delta_service.compare(
            session_id=self.session.id,
            base_package_id=base_package.id,
            new_vendor_package_id=new_vendor_package.id
        )

        # Perform customer comparison (delta vs B)
        customer_modifications = self.customer_service.compare(
            base_package_id=base_package.id,
            customer_package_id=customer_package.id,
            delta_changes=delta_changes
        )

        # Verify customer modifications were returned
        self.assertIsNotNone(customer_modifications)
        self.assertIsInstance(customer_modifications, dict)

        # Verify we have modifications for all delta objects
        self.assertEqual(
            len(customer_modifications),
            len(delta_changes),
            "Should have customer modification for each delta object"
        )

        # Verify all values are CustomerModification entities
        for obj_id, mod in customer_modifications.items():
            self.assertIsInstance(
                mod,
                CustomerModification,
                f"Object {obj_id} should have CustomerModification"
            )

        # Count statistics
        exists_count = sum(
            1 for m in customer_modifications.values()
            if m.exists_in_customer
        )
        modified_count = sum(
            1 for m in customer_modifications.values()
            if m.customer_modified
        )

        print("\nCustomer comparison results:")
        print(f"  Total delta objects: {len(delta_changes)}")
        print(f"  Exist in customer: {exists_count}")
        print(f"  Modified by customer: {modified_count}")
        print(f"  Removed by customer: {len(delta_changes) - exists_count}")

    def test_customer_statistics(self):
        """Test customer statistics retrieval"""
        # Skip if test packages don't exist
        if not os.path.exists(self.base_package_path):
            self.skipTest(
                f"Test package not found: {self.base_package_path}"
            )
        if not os.path.exists(self.customer_package_path):
            self.skipTest(
                f"Test package not found: {self.customer_package_path}"
            )
        if not os.path.exists(self.new_vendor_package_path):
            self.skipTest(
                f"Test package not found: {self.new_vendor_package_path}"
            )

        # Extract all three packages
        base_package = self.extraction_service.extract_package(
            session_id=self.session.id,
            zip_path=self.base_package_path,
            package_type='base'
        )

        customer_package = self.extraction_service.extract_package(
            session_id=self.session.id,
            zip_path=self.customer_package_path,
            package_type='customized'
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

        # Perform customer comparison
        customer_modifications = self.customer_service.compare(
            base_package_id=base_package.id,
            customer_package_id=customer_package.id,
            delta_changes=delta_changes
        )

        # Get statistics
        stats = self.customer_service.get_customer_statistics(
            customer_modifications
        )

        # Verify statistics structure
        self.assertIn('total', stats)
        self.assertIn('exists_in_customer', stats)
        self.assertIn('customer_modified', stats)
        self.assertIn('version_changes', stats)
        self.assertIn('content_changes', stats)

        # Verify counts are non-negative
        self.assertGreaterEqual(stats['total'], 0)
        self.assertGreaterEqual(stats['exists_in_customer'], 0)
        self.assertGreaterEqual(stats['customer_modified'], 0)
        self.assertGreaterEqual(stats['version_changes'], 0)
        self.assertGreaterEqual(stats['content_changes'], 0)

        # Verify total matches delta changes
        self.assertEqual(
            stats['total'],
            len(delta_changes),
            "Total should match number of delta changes"
        )

        print("\nCustomer statistics:")
        print(f"  Total: {stats['total']}")
        print(f"  Exists in customer: {stats['exists_in_customer']}")
        print(f"  Customer modified: {stats['customer_modified']}")
        print(f"  Version changes: {stats['version_changes']}")
        print(f"  Content changes: {stats['content_changes']}")

    def test_customer_comparison_with_removed_objects(self):
        """Test that removed objects are correctly identified"""
        # Skip if test packages don't exist
        if not os.path.exists(self.base_package_path):
            self.skipTest(
                f"Test package not found: {self.base_package_path}"
            )
        if not os.path.exists(self.customer_package_path):
            self.skipTest(
                f"Test package not found: {self.customer_package_path}"
            )
        if not os.path.exists(self.new_vendor_package_path):
            self.skipTest(
                f"Test package not found: {self.new_vendor_package_path}"
            )

        # Extract all three packages
        base_package = self.extraction_service.extract_package(
            session_id=self.session.id,
            zip_path=self.base_package_path,
            package_type='base'
        )

        customer_package = self.extraction_service.extract_package(
            session_id=self.session.id,
            zip_path=self.customer_package_path,
            package_type='customized'
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

        # Perform customer comparison
        customer_modifications = self.customer_service.compare(
            base_package_id=base_package.id,
            customer_package_id=customer_package.id,
            delta_changes=delta_changes
        )

        # Find objects that don't exist in customer
        removed_objects = [
            obj_id for obj_id, mod in customer_modifications.items()
            if not mod.exists_in_customer
        ]

        # Verify removed objects have correct flags
        for obj_id in removed_objects:
            mod = customer_modifications[obj_id]
            self.assertFalse(
                mod.exists_in_customer,
                f"Object {obj_id} should not exist in customer"
            )
            self.assertFalse(
                mod.customer_modified,
                f"Object {obj_id} should not be marked as modified"
            )
            self.assertFalse(
                mod.version_changed,
                f"Object {obj_id} should not have version change"
            )
            self.assertFalse(
                mod.content_changed,
                f"Object {obj_id} should not have content change"
            )

        print("\nRemoved objects test:")
        print(f"  Total delta objects: {len(delta_changes)}")
        print(f"  Removed by customer: {len(removed_objects)}")


if __name__ == '__main__':
    unittest.main()
