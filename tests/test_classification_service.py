"""
Tests for Classification Service

Tests the classification of delta objects combined with customer
modifications using the 7 classification rules.
"""
import os
import unittest
from tests.base_test import BaseTestCase
from models import db, MergeSession
from services.package_extraction_service import PackageExtractionService
from services.delta_comparison_service import DeltaComparisonService
from services.customer_comparison_service import CustomerComparisonService
from services.classification_service import (
    ClassificationService,
    ClassificationRuleEngine
)
from repositories.change_repository import ChangeRepository
from domain.entities import DeltaChange, CustomerModification
from domain.enums import ChangeCategory, Classification


class TestClassificationRuleEngine(BaseTestCase):
    """Test ClassificationRuleEngine rules"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.engine = ClassificationRuleEngine()

    def test_rule_10d_new_object(self):
        """Test Rule 10d: NEW in delta → NEW"""
        delta_change = DeltaChange(
            object_id=1,
            change_category=ChangeCategory.NEW,
            version_changed=False,
            content_changed=False
        )
        customer_mod = CustomerModification(
            object_id=1,
            exists_in_customer=False,
            customer_modified=False,
            version_changed=False,
            content_changed=False
        )

        classification = self.engine.classify(delta_change, customer_mod)

        self.assertEqual(classification, Classification.NEW)

    def test_rule_10a_modified_not_modified_by_customer(self):
        """Test Rule 10a: MODIFIED in delta AND not modified in customer
        → NO_CONFLICT"""
        delta_change = DeltaChange(
            object_id=1,
            change_category=ChangeCategory.MODIFIED,
            version_changed=True,
            content_changed=False
        )
        customer_mod = CustomerModification(
            object_id=1,
            exists_in_customer=True,
            customer_modified=False,
            version_changed=False,
            content_changed=False
        )

        classification = self.engine.classify(delta_change, customer_mod)

        self.assertEqual(classification, Classification.NO_CONFLICT)

    def test_rule_10b_modified_and_modified_by_customer(self):
        """Test Rule 10b: MODIFIED in delta AND modified in customer
        → CONFLICT"""
        delta_change = DeltaChange(
            object_id=1,
            change_category=ChangeCategory.MODIFIED,
            version_changed=True,
            content_changed=False
        )
        customer_mod = CustomerModification(
            object_id=1,
            exists_in_customer=True,
            customer_modified=True,
            version_changed=True,
            content_changed=False
        )

        classification = self.engine.classify(delta_change, customer_mod)

        self.assertEqual(classification, Classification.CONFLICT)

    def test_rule_10c_modified_removed_by_customer(self):
        """Test Rule 10c: MODIFIED in delta AND removed in customer
        → DELETED"""
        delta_change = DeltaChange(
            object_id=1,
            change_category=ChangeCategory.MODIFIED,
            version_changed=True,
            content_changed=False
        )
        customer_mod = CustomerModification(
            object_id=1,
            exists_in_customer=False,
            customer_modified=False,
            version_changed=False,
            content_changed=False
        )

        classification = self.engine.classify(delta_change, customer_mod)

        self.assertEqual(classification, Classification.DELETED)

    def test_rule_10e_deprecated_not_modified_by_customer(self):
        """Test Rule 10e: DEPRECATED in delta AND not modified in customer
        → NO_CONFLICT"""
        delta_change = DeltaChange(
            object_id=1,
            change_category=ChangeCategory.DEPRECATED,
            version_changed=False,
            content_changed=False
        )
        customer_mod = CustomerModification(
            object_id=1,
            exists_in_customer=True,
            customer_modified=False,
            version_changed=False,
            content_changed=False
        )

        classification = self.engine.classify(delta_change, customer_mod)

        self.assertEqual(classification, Classification.NO_CONFLICT)

    def test_rule_10f_deprecated_modified_by_customer(self):
        """Test Rule 10f: DEPRECATED in delta AND modified in customer
        → CONFLICT"""
        delta_change = DeltaChange(
            object_id=1,
            change_category=ChangeCategory.DEPRECATED,
            version_changed=False,
            content_changed=False
        )
        customer_mod = CustomerModification(
            object_id=1,
            exists_in_customer=True,
            customer_modified=True,
            version_changed=True,
            content_changed=False
        )

        classification = self.engine.classify(delta_change, customer_mod)

        self.assertEqual(classification, Classification.CONFLICT)

    def test_rule_10g_deprecated_removed_by_customer(self):
        """Test Rule 10g: DEPRECATED in delta AND removed in customer
        → NO_CONFLICT"""
        delta_change = DeltaChange(
            object_id=1,
            change_category=ChangeCategory.DEPRECATED,
            version_changed=False,
            content_changed=False
        )
        customer_mod = CustomerModification(
            object_id=1,
            exists_in_customer=False,
            customer_modified=False,
            version_changed=False,
            content_changed=False
        )

        classification = self.engine.classify(delta_change, customer_mod)

        self.assertEqual(classification, Classification.NO_CONFLICT)


class TestClassificationService(BaseTestCase):
    """Test ClassificationService functionality"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.extraction_service = PackageExtractionService()
        self.delta_service = DeltaComparisonService()
        self.customer_service = CustomerComparisonService()
        self.classification_service = ClassificationService()
        self.change_repo = ChangeRepository()

        # Create test session
        self.session = MergeSession(
            reference_id='TEST_CLASS_001',
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

    def test_classification_with_real_packages(self):
        """Test classification with real test packages"""
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

        # Classify changes
        classified_changes = self.classification_service.classify(
            session_id=self.session.id,
            delta_changes=delta_changes,
            customer_modifications=customer_modifications
        )

        # Verify classified changes were returned
        self.assertIsNotNone(classified_changes)
        self.assertIsInstance(classified_changes, list)
        self.assertGreater(len(classified_changes), 0)

        # Verify all delta objects were classified
        self.assertEqual(
            len(classified_changes),
            len(delta_changes),
            "All delta objects should be classified"
        )

        # Verify changes were stored in database
        stored_changes = self.change_repo.get_by_session(self.session.id)
        self.assertEqual(len(stored_changes), len(classified_changes))

        # Verify statistics
        stats = self.change_repo.count_by_classification(self.session.id)
        self.assertGreater(len(stats), 0, "Should have classifications")

        # Verify total matches sum of classifications
        total_from_stats = sum(stats.values())
        self.assertEqual(
            len(classified_changes),
            total_from_stats,
            "Total should match sum of classifications"
        )

        print("\nClassification results:")
        print(f"  NO_CONFLICT: {stats.get('NO_CONFLICT', 0)}")
        print(f"  CONFLICT: {stats.get('CONFLICT', 0)}")
        print(f"  NEW: {stats.get('NEW', 0)}")
        print(f"  DELETED: {stats.get('DELETED', 0)}")
        print(f"  Total: {len(classified_changes)}")

    def test_display_order_assigned(self):
        """Test that display_order is assigned to all changes"""
        # Skip if test packages don't exist
        if not os.path.exists(self.base_package_path):
            self.skipTest(
                f"Test package not found: {self.base_package_path}"
            )

        # Extract packages and classify
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

        delta_changes = self.delta_service.compare(
            session_id=self.session.id,
            base_package_id=base_package.id,
            new_vendor_package_id=new_vendor_package.id
        )

        customer_modifications = self.customer_service.compare(
            base_package_id=base_package.id,
            customer_package_id=customer_package.id,
            delta_changes=delta_changes
        )

        classified_changes = self.classification_service.classify(
            session_id=self.session.id,
            delta_changes=delta_changes,
            customer_modifications=customer_modifications
        )

        # Verify all changes have display_order
        for change in classified_changes:
            self.assertGreater(
                change.display_order,
                0,
                "Display order should be positive"
            )

        # Verify display_order is sequential
        display_orders = [c.display_order for c in classified_changes]
        self.assertEqual(
            display_orders,
            list(range(1, len(classified_changes) + 1)),
            "Display order should be sequential starting from 1"
        )

    def test_priority_sorting(self):
        """Test that changes are sorted by priority"""
        # Skip if test packages don't exist
        if not os.path.exists(self.base_package_path):
            self.skipTest(
                f"Test package not found: {self.base_package_path}"
            )

        # Extract packages and classify
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

        delta_changes = self.delta_service.compare(
            session_id=self.session.id,
            base_package_id=base_package.id,
            new_vendor_package_id=new_vendor_package.id
        )

        customer_modifications = self.customer_service.compare(
            base_package_id=base_package.id,
            customer_package_id=customer_package.id,
            delta_changes=delta_changes
        )

        classified_changes = self.classification_service.classify(
            session_id=self.session.id,
            delta_changes=delta_changes,
            customer_modifications=customer_modifications
        )

        # Verify priority order: CONFLICT > NEW > DELETED > NO_CONFLICT
        priority_map = {
            Classification.CONFLICT: 1,
            Classification.NEW: 2,
            Classification.DELETED: 3,
            Classification.NO_CONFLICT: 4
        }

        for i in range(len(classified_changes) - 1):
            current_priority = priority_map[
                classified_changes[i].classification
            ]
            next_priority = priority_map[
                classified_changes[i + 1].classification
            ]
            self.assertLessEqual(
                current_priority,
                next_priority,
                "Changes should be sorted by priority"
            )


if __name__ == '__main__':
    unittest.main()
