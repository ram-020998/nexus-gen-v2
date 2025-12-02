"""
Test script to verify customer-only changes fix.

This script:
1. Creates a new merge session with real packages
2. Verifies customer comparison was performed
3. Checks for customer-only changes (E \ D)
4. Validates they appear in the working set
"""

from app import create_app
from core.dependency_container import DependencyContainer
from services.three_way_merge_orchestrator import ThreeWayMergeOrchestrator
from models import db, DeltaComparisonResult, CustomerComparisonResult, Change

def test_customer_only_fix():
    """Test that customer-only changes are now included."""
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("TESTING CUSTOMER-ONLY CHANGES FIX")
        print("=" * 80)
        
        # Create merge session
        print("\n1. Creating merge session with real packages...")
        container = DependencyContainer.get_instance()
        orchestrator = container.get_service(ThreeWayMergeOrchestrator)
        
        session = orchestrator.create_merge_session(
            base_zip_path='applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip',
            customized_zip_path='applicationArtifacts/Three Way Testing Files/V2/Test Application Customer Version.zip',
            new_vendor_zip_path='applicationArtifacts/Three Way Testing Files/V2/Test Application Vendor New Version.zip'
        )
        
        print(f"✓ Session created: {session.reference_id}")
        print(f"  Status: {session.status}")
        print(f"  Total changes: {session.total_changes}")
        
        # Get vendor changes (Set D)
        print("\n2. Analyzing vendor changes (Set D)...")
        vendor_results = db.session.query(DeltaComparisonResult).filter_by(
            session_id=session.id
        ).all()
        vendor_objects = {r.object_id for r in vendor_results}
        print(f"✓ Vendor changes (Set D): {len(vendor_objects)} objects")
        
        # Get customer changes (Set E)
        print("\n3. Analyzing customer changes (Set E)...")
        customer_results = db.session.query(CustomerComparisonResult).filter_by(
            session_id=session.id
        ).all()
        
        if not customer_results:
            print("❌ FAILED: No customer comparison results found!")
            print("   The customer comparison service was not called or failed.")
            return False
        
        customer_objects = {r.object_id for r in customer_results}
        print(f"✓ Customer changes (Set E): {len(customer_objects)} objects")
        
        # Find customer-only objects (E \ D)
        print("\n4. Finding customer-only changes (E \\ D)...")
        customer_only = customer_objects - vendor_objects
        print(f"✓ Customer-only changes: {len(customer_only)} objects")
        
        if len(customer_only) == 0:
            print("⚠ WARNING: No customer-only changes in test data")
            print("   This might be expected if customer didn't add/modify unique objects")
        else:
            print(f"   These are objects the customer changed but vendor didn't touch")
        
        # Verify working set contains all changes (D ∪ E)
        print("\n5. Verifying working set (D ∪ E)...")
        changes = db.session.query(Change).filter_by(
            session_id=session.id
        ).all()
        working_set_objects = {c.object_id for c in changes}
        
        union = vendor_objects | customer_objects
        print(f"✓ Working set size: {len(working_set_objects)} objects")
        print(f"✓ Expected size (D ∪ E): {len(union)} objects")
        
        if working_set_objects != union:
            print(f"❌ FAILED: Working set doesn't match D ∪ E!")
            print(f"   Missing: {len(union - working_set_objects)} objects")
            print(f"   Extra: {len(working_set_objects - union)} objects")
            return False
        
        print("✓ Working set equals D ∪ E")
        
        # Verify customer-only objects are in working set
        if len(customer_only) > 0:
            print("\n6. Verifying customer-only objects in working set...")
            customer_only_in_working_set = customer_only & working_set_objects
            
            if len(customer_only_in_working_set) != len(customer_only):
                print(f"❌ FAILED: Not all customer-only changes in working set!")
                print(f"   Expected: {len(customer_only)}")
                print(f"   Found: {len(customer_only_in_working_set)}")
                return False
            
            print(f"✓ All {len(customer_only)} customer-only changes in working set")
            
            # Check their classifications
            customer_only_changes = [
                c for c in changes if c.object_id in customer_only
            ]
            
            print("\n7. Checking customer-only change classifications...")
            for change in customer_only_changes[:5]:  # Show first 5
                print(f"   - Object {change.object_id}: {change.classification}")
                print(f"     Vendor change: {change.vendor_change_type}")
                print(f"     Customer change: {change.customer_change_type}")
            
            if len(customer_only_changes) > 5:
                print(f"   ... and {len(customer_only_changes) - 5} more")
        
        # Summary statistics
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Session: {session.reference_id}")
        print(f"Vendor changes (D): {len(vendor_objects)}")
        print(f"Customer changes (E): {len(customer_objects)}")
        print(f"Intersection (D ∩ E): {len(vendor_objects & customer_objects)}")
        print(f"Vendor-only (D \\ E): {len(vendor_objects - customer_objects)}")
        print(f"Customer-only (E \\ D): {len(customer_only)}")
        print(f"Union (D ∪ E): {len(union)}")
        print(f"Working set: {len(working_set_objects)}")
        
        # Classification breakdown
        print("\nClassification breakdown:")
        classification_counts = {}
        for change in changes:
            classification_counts[change.classification] = \
                classification_counts.get(change.classification, 0) + 1
        
        for classification, count in sorted(classification_counts.items()):
            print(f"  {classification}: {count}")
        
        print("\n" + "=" * 80)
        print("✅ TEST PASSED: Customer-only changes fix is working!")
        print("=" * 80)
        
        return True

if __name__ == '__main__':
    success = test_customer_only_fix()
    exit(0 if success else 1)
