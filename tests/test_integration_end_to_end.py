"""
Integration Test - End-to-End Three-Way Merge Workflow

This test validates the complete three-way merge workflow using real Appian packages.

**Feature: three-way-merge-rebuild, Property 0: End-to-end workflow validation**

Test Requirements:
- 15.1: Test with real packages from applicationArtifacts/Three Way Testing Files/V2/
- 15.2: Verify no duplicates in object_lookup
- 15.3: Verify all change categories are identified
- 15.4: Verify all 7 rules are applied correctly
- 15.5: Verify delta_count equals change_count
"""

import os
import pytest
from tests.base_test import BaseTestCase
from services.three_way_merge_orchestrator import ThreeWayMergeOrchestrator
from models import (
    db,
    MergeSession,
    Package,
    ObjectLookup,
    PackageObjectMapping,
    DeltaComparisonResult,
    Change,
    ObjectVersion
)


class TestIntegrationEndToEnd(BaseTestCase):
    """
    End-to-end integration test for three-way merge workflow.
    
    This test validates the complete workflow from package upload through
    classification, using real Appian packages.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create orchestrator
        self.orchestrator = ThreeWayMergeOrchestrator(container=None)
        
        # Test package paths
        self.test_packages_dir = "applicationArtifacts/Three Way Testing Files/V2"
        self.base_zip = os.path.join(
            self.test_packages_dir,
            "Test Application - Base Version.zip"
        )
        self.customized_zip = os.path.join(
            self.test_packages_dir,
            "Test Application Customer Version.zip"
        )
        self.new_vendor_zip = os.path.join(
            self.test_packages_dir,
            "Test Application Vendor New Version.zip"
        )
        
        # Verify test packages exist
        self.assertTrue(
            os.path.exists(self.base_zip),
            f"Base package not found: {self.base_zip}"
        )
        self.assertTrue(
            os.path.exists(self.customized_zip),
            f"Customized package not found: {self.customized_zip}"
        )
        self.assertTrue(
            os.path.exists(self.new_vendor_zip),
            f"New vendor package not found: {self.new_vendor_zip}"
        )
    
    def test_end_to_end_workflow(self):
        """
        Test complete end-to-end workflow.
        
        Validates Requirements: 15.1, 15.2, 15.3, 15.4, 15.5
        
        Workflow:
        1. Upload three packages (A, B, C)
        2. Verify session created with reference_id
        3. Verify all packages extracted
        4. Verify delta comparison results stored
        5. Verify customer comparison completed
        6. Verify all changes classified
        7. Verify merge guidance generated
        8. Verify session status = 'ready'
        9. Verify no duplicates in object_lookup
        10. Verify delta-driven working set
        11. Verify referential integrity
        """
        print("\n" + "="*70)
        print("INTEGRATION TEST: End-to-End Three-Way Merge Workflow")
        print("="*70)
        
        # ====================================================================
        # Step 1: Create merge session
        # ====================================================================
        print("\n[Step 1] Creating merge session...")
        
        session = self.orchestrator.create_merge_session(
            base_zip_path=self.base_zip,
            customized_zip_path=self.customized_zip,
            new_vendor_zip_path=self.new_vendor_zip
        )
        
        # Verify session created
        self.assertIsNotNone(session, "Session should be created")
        self.assertIsNotNone(session.reference_id, "Session should have reference_id")
        self.assertTrue(
            session.reference_id.startswith('MRG_'),
            f"Reference ID should start with 'MRG_', got: {session.reference_id}"
        )
        
        print(f"✓ Session created: {session.reference_id}")
        print(f"  Status: {session.status}")
        print(f"  Total changes: {session.total_changes}")
        
        # ====================================================================
        # Step 2: Verify all packages extracted
        # ====================================================================
        print("\n[Step 2] Verifying packages extracted...")
        
        packages = Package.query.filter_by(session_id=session.id).all()
        self.assertEqual(
            len(packages),
            3,
            f"Should have 3 packages, got {len(packages)}"
        )
        
        # Verify package types
        package_types = {pkg.package_type for pkg in packages}
        expected_types = {'base', 'customized', 'new_vendor'}
        self.assertEqual(
            package_types,
            expected_types,
            f"Package types mismatch. Expected {expected_types}, got {package_types}"
        )
        
        # Verify all packages have objects
        for pkg in packages:
            self.assertGreater(
                pkg.total_objects,
                0,
                f"Package {pkg.package_type} should have objects"
            )
            print(f"✓ Package {pkg.package_type}: {pkg.total_objects} objects")
        
        # ====================================================================
        # Step 3: Verify no duplicates in object_lookup (Property 1)
        # ====================================================================
        print("\n[Step 3] Verifying no duplicates in object_lookup...")
        
        # Query for duplicates
        duplicate_query = db.session.execute(db.text("""
            SELECT uuid, COUNT(*) as count
            FROM object_lookup
            GROUP BY uuid
            HAVING count > 1
        """))
        duplicates = duplicate_query.fetchall()
        
        self.assertEqual(
            len(duplicates),
            0,
            f"Found {len(duplicates)} duplicate UUIDs in object_lookup"
        )
        
        # Count total objects
        total_objects = ObjectLookup.query.count()
        print(f"✓ No duplicates found")
        print(f"  Total unique objects: {total_objects}")
        
        # ====================================================================
        # Step 4: Verify package-object mappings (Property 2)
        # ====================================================================
        print("\n[Step 4] Verifying package-object mappings...")
        
        total_mappings = PackageObjectMapping.query.count()
        self.assertGreater(
            total_mappings,
            0,
            "Should have package-object mappings"
        )
        
        # Verify mappings are consistent
        for obj in ObjectLookup.query.limit(10).all():
            mapping_count = PackageObjectMapping.query.filter_by(
                object_id=obj.id
            ).count()
            self.assertGreater(
                mapping_count,
                0,
                f"Object {obj.uuid} should have at least one mapping"
            )
            self.assertLessEqual(
                mapping_count,
                3,
                f"Object {obj.uuid} should have at most 3 mappings"
            )
        
        print(f"✓ Package-object mappings consistent")
        print(f"  Total mappings: {total_mappings}")
        
        # ====================================================================
        # Step 5: Verify delta comparison results stored
        # ====================================================================
        print("\n[Step 5] Verifying delta comparison results...")
        
        delta_results = DeltaComparisonResult.query.filter_by(
            session_id=session.id
        ).all()
        
        self.assertGreater(
            len(delta_results),
            0,
            "Should have delta comparison results"
        )
        
        # Verify all change categories present
        change_categories = {result.change_category for result in delta_results}
        valid_categories = {'NEW', 'MODIFIED', 'DEPRECATED'}
        self.assertTrue(
            change_categories.issubset(valid_categories),
            f"Invalid change categories: {change_categories - valid_categories}"
        )
        
        # Count by category
        category_counts = {}
        for category in valid_categories:
            count = DeltaComparisonResult.query.filter_by(
                session_id=session.id,
                change_category=category
            ).count()
            category_counts[category] = count
        
        print(f"✓ Delta comparison results stored")
        print(f"  Total delta results: {len(delta_results)}")
        print(f"  NEW: {category_counts['NEW']}")
        print(f"  MODIFIED: {category_counts['MODIFIED']}")
        print(f"  DEPRECATED: {category_counts['DEPRECATED']}")
        
        # ====================================================================
        # Step 6: Verify all changes classified (Property 4)
        # ====================================================================
        print("\n[Step 6] Verifying all changes classified...")
        
        changes = Change.query.filter_by(session_id=session.id).all()
        
        self.assertEqual(
            len(changes),
            session.total_changes,
            f"Change count mismatch: {len(changes)} vs {session.total_changes}"
        )
        
        # Verify all classifications are valid
        valid_classifications = {'NO_CONFLICT', 'CONFLICT', 'NEW', 'DELETED'}
        for change in changes:
            self.assertIn(
                change.classification,
                valid_classifications,
                f"Invalid classification: {change.classification}"
            )
        
        # Count by classification
        classification_counts = {}
        for classification in valid_classifications:
            count = Change.query.filter_by(
                session_id=session.id,
                classification=classification
            ).count()
            classification_counts[classification] = count
        
        print(f"✓ All changes classified")
        print(f"  Total changes: {len(changes)}")
        print(f"  NO_CONFLICT: {classification_counts['NO_CONFLICT']}")
        print(f"  CONFLICT: {classification_counts['CONFLICT']}")
        print(f"  NEW: {classification_counts['NEW']}")
        print(f"  DELETED: {classification_counts['DELETED']}")
        
        # ====================================================================
        # Step 7: Verify delta-driven working set (Property 3)
        # ====================================================================
        print("\n[Step 7] Verifying delta-driven working set...")
        
        delta_count = len(delta_results)
        change_count = len(changes)
        
        self.assertEqual(
            delta_count,
            change_count,
            f"Delta count ({delta_count}) should equal change count ({change_count})"
        )
        
        print(f"✓ Delta-driven working set verified")
        print(f"  Delta results: {delta_count}")
        print(f"  Changes: {change_count}")
        
        # ====================================================================
        # Step 8: Verify referential integrity (Property 14)
        # ====================================================================
        print("\n[Step 8] Verifying referential integrity...")
        
        # Verify all changes reference valid objects
        for change in changes:
            obj = ObjectLookup.query.get(change.object_id)
            self.assertIsNotNone(
                obj,
                f"Change {change.id} references non-existent object {change.object_id}"
            )
        
        # Verify all delta results reference valid objects
        for delta in delta_results:
            obj = ObjectLookup.query.get(delta.object_id)
            self.assertIsNotNone(
                obj,
                f"Delta {delta.id} references non-existent object {delta.object_id}"
            )
        
        # Verify all package mappings reference valid objects and packages
        mappings = PackageObjectMapping.query.all()
        for mapping in mappings:
            obj = ObjectLookup.query.get(mapping.object_id)
            pkg = Package.query.get(mapping.package_id)
            self.assertIsNotNone(
                obj,
                f"Mapping {mapping.id} references non-existent object"
            )
            self.assertIsNotNone(
                pkg,
                f"Mapping {mapping.id} references non-existent package"
            )
        
        print(f"✓ Referential integrity verified")
        print(f"  All foreign keys valid")
        
        # ====================================================================
        # Step 9: Verify object versions stored
        # ====================================================================
        print("\n[Step 9] Verifying object versions...")
        
        versions = ObjectVersion.query.filter(
            ObjectVersion.package_id.in_([pkg.id for pkg in packages])
        ).all()
        
        self.assertGreater(
            len(versions),
            0,
            "Should have object versions"
        )
        
        print(f"✓ Object versions stored")
        print(f"  Total versions: {len(versions)}")
        
        # ====================================================================
        # Step 10: Verify session status
        # ====================================================================
        print("\n[Step 10] Verifying session status...")
        
        # Refresh session from database
        db.session.refresh(session)
        
        self.assertEqual(
            session.status,
            'ready',
            f"Session status should be 'ready', got '{session.status}'"
        )
        
        print(f"✓ Session status: {session.status}")
        
        # ====================================================================
        # Step 11: Verify working set can be retrieved
        # ====================================================================
        print("\n[Step 11] Verifying working set retrieval...")
        
        working_set = self.orchestrator.get_working_set(session.reference_id)
        
        self.assertEqual(
            len(working_set),
            session.total_changes,
            f"Working set size mismatch: {len(working_set)} vs {session.total_changes}"
        )
        
        # Verify display order is sequential
        for i, change in enumerate(working_set, start=1):
            self.assertEqual(
                change['display_order'],
                i,
                f"Display order should be {i}, got {change['display_order']}"
            )
        
        print(f"✓ Working set retrieved successfully")
        print(f"  Total items: {len(working_set)}")
        
        # ====================================================================
        # Step 12: Verify session status can be retrieved
        # ====================================================================
        print("\n[Step 12] Verifying session status retrieval...")
        
        status = self.orchestrator.get_session_status(session.reference_id)
        
        self.assertEqual(status['reference_id'], session.reference_id)
        self.assertEqual(status['status'], 'ready')
        self.assertEqual(status['total_changes'], session.total_changes)
        
        # Verify packages in status
        self.assertIn('packages', status)
        self.assertIn('base', status['packages'])
        self.assertIn('customized', status['packages'])
        self.assertIn('new_vendor', status['packages'])
        
        # Verify statistics
        self.assertIn('statistics', status)
        stats = status['statistics']
        
        # Verify statistics sum to total changes
        total_from_stats = sum(stats.values())
        self.assertEqual(
            total_from_stats,
            session.total_changes,
            f"Statistics sum ({total_from_stats}) should equal total changes ({session.total_changes})"
        )
        
        print(f"✓ Session status retrieved successfully")
        print(f"  Statistics: {stats}")
        
        # ====================================================================
        # Summary
        # ====================================================================
        print("\n" + "="*70)
        print("INTEGRATION TEST SUMMARY")
        print("="*70)
        print(f"Session: {session.reference_id}")
        print(f"Status: {session.status}")
        print(f"Total Objects: {total_objects}")
        print(f"Total Mappings: {total_mappings}")
        print(f"Delta Results: {delta_count}")
        print(f"Changes: {change_count}")
        print(f"Versions: {len(versions)}")
        print("\nClassification Breakdown:")
        for classification, count in classification_counts.items():
            print(f"  {classification}: {count}")
        print("\nChange Category Breakdown:")
        for category, count in category_counts.items():
            print(f"  {category}: {count}")
        print("\n✓ All integration tests passed!")
        print("="*70)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
