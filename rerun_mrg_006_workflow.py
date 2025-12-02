"""
Re-run the complete three-way merge workflow for session MRG_006.

This will:
1. Clear existing delta, customer comparison, and changes
2. Re-run delta comparison (Step 5)
3. Re-run customer comparison (Step 6)
4. Re-run classification (Step 7)
5. Verify the two objects are correctly classified
"""

from app import create_app
from models import db, MergeSession, Package, DeltaComparisonResult, Change
from domain.enums import PackageType
from core.dependency_container import DependencyContainer
from services.delta_comparison_service import DeltaComparisonService
from services.customer_comparison_service import CustomerComparisonService
from services.classification_service import ClassificationService

def print_separator(title=""):
    print("\n" + "="*80)
    if title:
        print(title)
        print("="*80)

def main():
    app = create_app()
    
    with app.app_context():
        print_separator("RE-RUNNING THREE-WAY MERGE WORKFLOW FOR MRG_006")
        
        # Get session
        session = db.session.query(MergeSession).filter_by(reference_id='MRG_006').first()
        
        if not session:
            print("❌ Session MRG_006 not found")
            return
        
        print(f"✅ Session: {session.reference_id} (ID: {session.id})")
        
        # Get packages
        packages = db.session.query(Package).filter_by(session_id=session.id).all()
        package_map = {pkg.package_type: pkg for pkg in packages}
        
        base_pkg = package_map.get(PackageType.BASE.value)
        customized_pkg = package_map.get(PackageType.CUSTOMIZED.value)
        new_vendor_pkg = package_map.get(PackageType.NEW_VENDOR.value)
        
        print(f"✅ Packages loaded: Base, Customized, New Vendor")
        
        # Get services
        container = DependencyContainer.get_instance()
        delta_service = container.get_service(DeltaComparisonService)
        customer_service = container.get_service(CustomerComparisonService)
        classification_service = container.get_service(ClassificationService)
        
        # Step 1: Clear existing results
        print_separator("STEP 1: Clearing existing results")
        
        from models import CustomerComparisonResult
        
        delta_count = db.session.query(DeltaComparisonResult).filter_by(session_id=session.id).count()
        customer_count = db.session.query(CustomerComparisonResult).filter_by(session_id=session.id).count()
        change_count = db.session.query(Change).filter_by(session_id=session.id).count()
        
        print(f"Existing delta results: {delta_count}")
        print(f"Existing customer results: {customer_count}")
        print(f"Existing changes: {change_count}")
        
        if delta_count > 0:
            db.session.query(DeltaComparisonResult).filter_by(session_id=session.id).delete()
        if customer_count > 0:
            db.session.query(CustomerComparisonResult).filter_by(session_id=session.id).delete()
        if change_count > 0:
            db.session.query(Change).filter_by(session_id=session.id).delete()
        
        db.session.commit()
        print("✅ Cleared existing results")
        
        # Step 2: Re-run delta comparison (Step 5)
        print_separator("STEP 2: Running Delta Comparison (A → C)")
        
        delta_changes = delta_service.compare(
            session_id=session.id,
            base_package_id=base_pkg.id,
            new_vendor_package_id=new_vendor_pkg.id
        )
        
        print(f"✅ Delta comparison complete: {len(delta_changes)} changes")
        
        # Step 3: Re-run customer comparison (Step 6: A→B)
        print_separator("STEP 3: Running Customer Comparison (A → B)")
        
        customer_changes = customer_service.compare(
            session_id=session.id,
            base_package_id=base_pkg.id,
            customer_package_id=customized_pkg.id
        )
        
        print(f"✅ Customer comparison complete: {len(customer_changes)} changes")
        
        # Step 4: Re-run classification (Step 7)
        print_separator("STEP 4: Running Classification (7 Rules)")
        
        classified_changes = classification_service.classify(
            session_id=session.id,
            vendor_changes=delta_changes,
            customer_changes=customer_changes,
            customer_package_id=customized_pkg.id,
            new_vendor_package_id=new_vendor_pkg.id
        )
        
        print(f"✅ Classification complete: {len(classified_changes)} changes classified")
        
        # Step 5: Verify the two objects
        print_separator("STEP 5: Verifying Object Classifications")
        
        # Check Process Model
        pm_change = db.session.query(Change).join(
            Change.object
        ).filter(
            Change.session_id == session.id,
            db.text("object_lookup.name = 'DGS Create Parent'"),
            db.text("object_lookup.object_type = 'Process Model'")
        ).first()
        
        if pm_change:
            print(f"✅ Process Model 'DGS Create Parent':")
            print(f"   Classification: {pm_change.classification}")
            print(f"   Vendor change: {pm_change.vendor_change_type}")
            print(f"   Customer change: {pm_change.customer_change_type}")
            print(f"   Status: {pm_change.status}")
            
            if pm_change.classification == 'CONFLICT':
                print(f"   ✅ CORRECT: Should be CONFLICT (Rule 10b)")
            else:
                print(f"   ❌ WRONG: Should be CONFLICT, got {pm_change.classification}")
        else:
            print(f"❌ Process Model 'DGS Create Parent' NOT in working set")
        
        # Check Constant
        const_change = db.session.query(Change).join(
            Change.object
        ).filter(
            Change.session_id == session.id,
            db.text("object_lookup.name = 'DGS_TEXT_RELATIONSHP_MANY_TO_ONE'"),
            db.text("object_lookup.object_type = 'Constant'")
        ).first()
        
        if const_change:
            print(f"\n✅ Constant 'DGS_TEXT_RELATIONSHP_MANY_TO_ONE':")
            print(f"   Classification: {const_change.classification}")
            print(f"   Vendor change: {const_change.vendor_change_type}")
            print(f"   Customer change: {const_change.customer_change_type}")
            print(f"   Status: {const_change.status}")
            
            if const_change.classification == 'NO_CONFLICT':
                print(f"   ✅ CORRECT: Should be NO_CONFLICT (Rule 10a)")
            else:
                print(f"   ❌ WRONG: Should be NO_CONFLICT, got {const_change.classification}")
        else:
            print(f"\n❌ Constant 'DGS_TEXT_RELATIONSHP_MANY_TO_ONE' NOT in working set")
        
        # Step 6: Update session statistics
        print_separator("STEP 6: Updating Session Statistics")
        
        total_changes = db.session.query(Change).filter_by(session_id=session.id).count()
        session.total_changes = total_changes
        db.session.commit()
        
        print(f"✅ Updated session total_changes: {total_changes}")
        
        # Show final summary
        print_separator("FINAL SUMMARY")
        
        changes = db.session.query(Change).filter_by(session_id=session.id).all()
        
        classification_counts = {}
        for change in changes:
            classification_counts[change.classification] = classification_counts.get(change.classification, 0) + 1
        
        print(f"Total changes in working set: {len(changes)}")
        print(f"By classification:")
        for classification, count in sorted(classification_counts.items()):
            print(f"   {classification}: {count}")
        
        print_separator("WORKFLOW COMPLETE")
        
        if pm_change and const_change:
            if pm_change.classification == 'CONFLICT' and const_change.classification == 'NO_CONFLICT':
                print("\n✅ SUCCESS: Both objects correctly classified!")
            else:
                print("\n⚠️  PARTIAL: Objects found but classifications may be incorrect")
        else:
            print("\n❌ FAILURE: One or both objects missing from working set")

if __name__ == "__main__":
    main()
