"""
Test to verify that objects with identical content in B and C
are NOT classified as CONFLICT.

This test verifies the fix for the issue where AS_GSS_FM_AddConsensusVersion
was incorrectly marked as CONFLICT even though the customer version (B)
and new vendor version (C) had identical content.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, MergeSession, Change, ObjectLookup, ObjectVersion
from services.three_way_merge_orchestrator import ThreeWayMergeOrchestrator
from core.dependency_container import DependencyContainer


def test_identical_content_not_conflict():
    """
    Test that objects modified in both delta and customer,
    but with identical content in B and C, are NOT marked as CONFLICT.
    """
    app = create_app()
    
    with app.app_context():
        # Clean database
        print("Cleaning database...")
        db.session.query(Change).delete()
        db.session.query(ObjectVersion).delete()
        db.session.query(MergeSession).delete()
        db.session.commit()
        
        # Create orchestrator
        container = DependencyContainer.get_instance()
        orchestrator = container.get_service(ThreeWayMergeOrchestrator)
        
        # Package paths
        base_path = "applicationArtifacts/Three Way Testing Files/V3/Base Package.zip"
        customer_path = "applicationArtifacts/Three Way Testing Files/V3/Customer Version.zip"
        new_vendor_path = "applicationArtifacts/Three Way Testing Files/V3/Latest Package.zip"
        
        print(f"\nCreating merge session...")
        print(f"Base: {base_path}")
        print(f"Customer: {customer_path}")
        print(f"New Vendor: {new_vendor_path}")
        
        # Create merge session
        session = orchestrator.create_merge_session(
            base_zip_path=base_path,
            customized_zip_path=customer_path,
            new_vendor_zip_path=new_vendor_path
        )
        
        print(f"\n✓ Session created: {session.reference_id}")
        print(f"Total changes: {session.total_changes}")
        
        # Find the specific object
        obj = db.session.query(ObjectLookup).filter_by(
            uuid="_a-0000ea4b-69d2-8000-9c9e-011c48011c48_7139691"
        ).first()
        
        if not obj:
            print("\n❌ Object AS_GSS_FM_AddConsensusVersion not found!")
            return False
        
        print(f"\n✓ Found object: {obj.name} (ID: {obj.id})")
        
        # Get the change record
        change = db.session.query(Change).filter_by(
            session_id=session.id,
            object_id=obj.id
        ).first()
        
        if not change:
            print(f"❌ No change record found for object {obj.name}")
            return False
        
        print(f"\nChange details:")
        print(f"  Classification: {change.classification}")
        print(f"  Vendor change type: {change.vendor_change_type}")
        print(f"  Customer change type: {change.customer_change_type}")
        
        # Get versions from all three packages
        from models import Package
        packages = db.session.query(Package).filter_by(
            session_id=session.id
        ).all()
        
        package_map = {pkg.package_type: pkg for pkg in packages}
        
        base_version = db.session.query(ObjectVersion).filter_by(
            object_id=obj.id,
            package_id=package_map['base'].id
        ).first()
        
        customer_version = db.session.query(ObjectVersion).filter_by(
            object_id=obj.id,
            package_id=package_map['customized'].id
        ).first()
        
        new_vendor_version = db.session.query(ObjectVersion).filter_by(
            object_id=obj.id,
            package_id=package_map['new_vendor'].id
        ).first()
        
        print(f"\nVersion UUIDs:")
        print(f"  Base (A): {base_version.version_uuid if base_version else 'N/A'}")
        print(f"  Customer (B): {customer_version.version_uuid if customer_version else 'N/A'}")
        print(f"  New Vendor (C): {new_vendor_version.version_uuid if new_vendor_version else 'N/A'}")
        
        print(f"\nSAIL code lengths:")
        print(f"  Base (A): {len(base_version.sail_code) if base_version and base_version.sail_code else 0} chars")
        print(f"  Customer (B): {len(customer_version.sail_code) if customer_version and customer_version.sail_code else 0} chars")
        print(f"  New Vendor (C): {len(new_vendor_version.sail_code) if new_vendor_version and new_vendor_version.sail_code else 0} chars")
        
        # Check if B and C are identical
        b_and_c_identical = (
            customer_version and new_vendor_version and
            customer_version.version_uuid == new_vendor_version.version_uuid and
            customer_version.sail_code == new_vendor_version.sail_code
        )
        
        print(f"\nB and C identical: {b_and_c_identical}")
        
        # Verify classification
        if b_and_c_identical:
            # If B and C are identical, should be NO_CONFLICT
            if change.classification == 'NO_CONFLICT':
                print(f"\n✅ PASS: Object correctly classified as NO_CONFLICT")
                print(f"   Reason: Both vendor and customer modified, but B == C")
                return True
            else:
                print(f"\n❌ FAIL: Object incorrectly classified as {change.classification}")
                print(f"   Expected: NO_CONFLICT (because B == C)")
                print(f"   Actual: {change.classification}")
                return False
        else:
            # If B and C are different, should be CONFLICT
            if change.classification == 'CONFLICT':
                print(f"\n✅ PASS: Object correctly classified as CONFLICT")
                print(f"   Reason: Both vendor and customer modified, and B != C")
                return True
            else:
                print(f"\n❌ FAIL: Object incorrectly classified as {change.classification}")
                print(f"   Expected: CONFLICT (because B != C)")
                print(f"   Actual: {change.classification}")
                return False


if __name__ == '__main__':
    success = test_identical_content_not_conflict()
    sys.exit(0 if success else 1)
