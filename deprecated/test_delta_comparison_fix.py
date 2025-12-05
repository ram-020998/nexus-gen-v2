"""
Test the delta comparison fix for session MRG_006.

This script will:
1. Delete existing delta comparison results for session MRG_006
2. Re-run delta comparison with the fixed service
3. Verify both missing objects are now detected
4. Show the results
"""

from app import create_app
from models import db, MergeSession, Package, DeltaComparisonResult
from domain.enums import PackageType
from core.dependency_container import DependencyContainer
from services.delta_comparison_service import DeltaComparisonService

def print_separator(title=""):
    print("\n" + "="*80)
    if title:
        print(title)
        print("="*80)

def main():
    app = create_app()
    
    with app.app_context():
        print_separator("TESTING DELTA COMPARISON FIX FOR SESSION MRG_006")
        
        # Get session
        session = db.session.query(MergeSession).filter_by(reference_id='MRG_006').first()
        
        if not session:
            print("❌ Session MRG_006 not found")
            return
        
        print(f"✅ Found session: {session.reference_id} (ID: {session.id})")
        
        # Get packages
        packages = db.session.query(Package).filter_by(session_id=session.id).all()
        package_map = {pkg.package_type: pkg for pkg in packages}
        
        base_pkg = package_map.get(PackageType.BASE.value)
        new_vendor_pkg = package_map.get(PackageType.NEW_VENDOR.value)
        
        if not base_pkg or not new_vendor_pkg:
            print("❌ Missing packages")
            return
        
        print(f"✅ Base package: {base_pkg.filename} (ID: {base_pkg.id})")
        print(f"✅ New Vendor package: {new_vendor_pkg.filename} (ID: {new_vendor_pkg.id})")
        
        # Step 1: Delete existing delta comparison results
        print_separator("STEP 1: Clearing existing delta comparison results")
        
        existing_count = db.session.query(DeltaComparisonResult).filter_by(
            session_id=session.id
        ).count()
        
        print(f"Found {existing_count} existing delta comparison results")
        
        if existing_count > 0:
            db.session.query(DeltaComparisonResult).filter_by(
                session_id=session.id
            ).delete()
            db.session.commit()
            print(f"✅ Deleted {existing_count} existing results")
        
        # Step 2: Re-run delta comparison with fixed service
        print_separator("STEP 2: Running delta comparison with fixed service")
        
        container = DependencyContainer.get_instance()
        delta_service = container.get_service(DeltaComparisonService)
        
        print(f"Comparing Package A (id={base_pkg.id}) → Package C (id={new_vendor_pkg.id})")
        
        delta_changes = delta_service.compare(
            session_id=session.id,
            base_package_id=base_pkg.id,
            new_vendor_package_id=new_vendor_pkg.id
        )
        
        print(f"✅ Delta comparison complete: {len(delta_changes)} changes detected")
        
        # Step 3: Verify the two missing objects are now detected
        print_separator("STEP 3: Verifying missing objects are now detected")
        
        # Check for Process Model
        pm_result = db.session.query(DeltaComparisonResult).join(
            DeltaComparisonResult.object
        ).filter(
            DeltaComparisonResult.session_id == session.id,
            db.text("object_lookup.name = 'DGS Create Parent'"),
            db.text("object_lookup.object_type = 'Process Model'")
        ).first()
        
        if pm_result:
            print(f"✅ Process Model 'DGS Create Parent' FOUND in delta")
            print(f"   Change category: {pm_result.change_category}")
            print(f"   Change type: {pm_result.change_type}")
            print(f"   Version changed: {pm_result.version_changed}")
            print(f"   Content changed: {pm_result.content_changed}")
        else:
            print(f"❌ Process Model 'DGS Create Parent' NOT FOUND in delta")
        
        # Check for Constant
        const_result = db.session.query(DeltaComparisonResult).join(
            DeltaComparisonResult.object
        ).filter(
            DeltaComparisonResult.session_id == session.id,
            db.text("object_lookup.name = 'DGS_TEXT_RELATIONSHP_MANY_TO_ONE'"),
            db.text("object_lookup.object_type = 'Constant'")
        ).first()
        
        if const_result:
            print(f"\n✅ Constant 'DGS_TEXT_RELATIONSHP_MANY_TO_ONE' FOUND in delta")
            print(f"   Change category: {const_result.change_category}")
            print(f"   Change type: {const_result.change_type}")
            print(f"   Version changed: {const_result.version_changed}")
            print(f"   Content changed: {const_result.content_changed}")
        else:
            print(f"\n❌ Constant 'DGS_TEXT_RELATIONSHP_MANY_TO_ONE' NOT FOUND in delta")
        
        # Step 4: Show summary
        print_separator("STEP 4: Delta Comparison Summary")
        
        stats = delta_service.get_delta_statistics(session.id)
        print(f"Total delta results: {stats['total']}")
        print(f"By category:")
        for category, count in stats['by_category'].items():
            print(f"   {category}: {count}")
        
        print_separator("TEST COMPLETE")
        
        if pm_result and const_result:
            print("\n✅ SUCCESS: Both missing objects are now detected!")
            print("\nNext step: Re-run customer comparison and classification")
            print("to verify they get the correct classifications:")
            print("  - Process Model: CONFLICT (Rule 10b)")
            print("  - Constant: NO_CONFLICT (Rule 10a)")
        else:
            print("\n❌ FAILURE: One or both objects still missing")

if __name__ == "__main__":
    main()
