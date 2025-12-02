"""
Diagnostic script to investigate why specific objects are missing from delta comparison.

This script checks:
1. If objects exist in object_lookup
2. If objects are mapped to packages A and C
3. If object_versions exist for both packages
4. Version UUID comparison
5. Content comparison
6. Why they weren't detected as MODIFIED
"""

import logging
from app import create_app
from models import db, MergeSession, Package, ObjectLookup, ObjectVersion, PackageObjectMapping
from domain.enums import PackageType
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def print_separator(title=""):
    """Print a visual separator."""
    print("\n" + "="*80)
    if title:
        print(title)
        print("="*80)

def diagnose_object(session_id: int, object_name: str, object_type: str):
    """
    Diagnose why an object is missing from delta comparison.
    
    Args:
        session_id: Merge session ID
        object_name: Name of the object
        object_type: Type of the object
    """
    print_separator(f"DIAGNOSING: {object_name} ({object_type})")
    
    # Step 1: Find the object in object_lookup
    obj = db.session.query(ObjectLookup).filter_by(
        name=object_name,
        object_type=object_type
    ).first()
    
    if not obj:
        print(f"❌ Object not found in object_lookup")
        return
    
    print(f"✅ Found in object_lookup:")
    print(f"   ID: {obj.id}")
    print(f"   UUID: {obj.uuid}")
    print(f"   Name: {obj.name}")
    print(f"   Type: {obj.object_type}")
    
    # Step 2: Get packages for this session
    session = db.session.query(MergeSession).filter_by(id=session_id).first()
    if not session:
        print(f"❌ Session {session_id} not found")
        return
    
    packages = db.session.query(Package).filter_by(session_id=session_id).all()
    package_map = {pkg.package_type: pkg for pkg in packages}
    
    base_pkg = package_map.get(PackageType.BASE.value)
    customized_pkg = package_map.get(PackageType.CUSTOMIZED.value)
    new_vendor_pkg = package_map.get(PackageType.NEW_VENDOR.value)
    
    if not base_pkg or not new_vendor_pkg:
        print(f"❌ Missing packages (Base: {base_pkg is not None}, New Vendor: {new_vendor_pkg is not None})")
        return
    
    print(f"\n📦 Packages:")
    print(f"   Base (A): ID={base_pkg.id}, {base_pkg.filename}")
    print(f"   Customized (B): ID={customized_pkg.id if customized_pkg else 'N/A'}, {customized_pkg.filename if customized_pkg else 'N/A'}")
    print(f"   New Vendor (C): ID={new_vendor_pkg.id}, {new_vendor_pkg.filename}")
    
    # Step 3: Check package_object_mappings
    print(f"\n🔗 Package Object Mappings:")
    
    base_mapping = db.session.query(PackageObjectMapping).filter_by(
        package_id=base_pkg.id,
        object_id=obj.id
    ).first()
    
    new_vendor_mapping = db.session.query(PackageObjectMapping).filter_by(
        package_id=new_vendor_pkg.id,
        object_id=obj.id
    ).first()
    
    customized_mapping = None
    if customized_pkg:
        customized_mapping = db.session.query(PackageObjectMapping).filter_by(
            package_id=customized_pkg.id,
            object_id=obj.id
        ).first()
    
    print(f"   In Base (A): {'✅ YES' if base_mapping else '❌ NO'}")
    print(f"   In Customized (B): {'✅ YES' if customized_mapping else '❌ NO'}")
    print(f"   In New Vendor (C): {'✅ YES' if new_vendor_mapping else '❌ NO'}")
    
    # Step 4: Check object_versions
    print(f"\n📄 Object Versions:")
    
    base_version = db.session.query(ObjectVersion).filter_by(
        object_id=obj.id,
        package_id=base_pkg.id
    ).first()
    
    new_vendor_version = db.session.query(ObjectVersion).filter_by(
        object_id=obj.id,
        package_id=new_vendor_pkg.id
    ).first()
    
    customized_version = None
    if customized_pkg:
        customized_version = db.session.query(ObjectVersion).filter_by(
            object_id=obj.id,
            package_id=customized_pkg.id
        ).first()
    
    print(f"   Base (A) version: {'✅ EXISTS' if base_version else '❌ MISSING'}")
    if base_version:
        print(f"      Version UUID: {base_version.version_uuid}")
        print(f"      Has SAIL code: {base_version.sail_code is not None and len(base_version.sail_code) > 0}")
        print(f"      Has fields: {base_version.fields is not None}")
        print(f"      Has properties: {base_version.properties is not None}")
    
    print(f"\n   Customized (B) version: {'✅ EXISTS' if customized_version else '❌ MISSING'}")
    if customized_version:
        print(f"      Version UUID: {customized_version.version_uuid}")
        print(f"      Has SAIL code: {customized_version.sail_code is not None and len(customized_version.sail_code) > 0}")
        print(f"      Has fields: {customized_version.fields is not None}")
        print(f"      Has properties: {customized_version.properties is not None}")
    
    print(f"\n   New Vendor (C) version: {'✅ EXISTS' if new_vendor_version else '❌ MISSING'}")
    if new_vendor_version:
        print(f"      Version UUID: {new_vendor_version.version_uuid}")
        print(f"      Has SAIL code: {new_vendor_version.sail_code is not None and len(new_vendor_version.sail_code) > 0}")
        print(f"      Has fields: {new_vendor_version.fields is not None}")
        print(f"      Has properties: {new_vendor_version.properties is not None}")
    
    # Step 5: Compare versions
    if base_version and new_vendor_version:
        print(f"\n🔍 Version Comparison (A → C):")
        
        version_changed = base_version.version_uuid != new_vendor_version.version_uuid
        print(f"   Version UUID changed: {'✅ YES' if version_changed else '❌ NO'}")
        
        if version_changed:
            print(f"      Base: {base_version.version_uuid}")
            print(f"      New:  {new_vendor_version.version_uuid}")
        
        # Compare content
        print(f"\n   Content Comparison:")
        
        # SAIL code
        base_sail = base_version.sail_code or ""
        new_sail = new_vendor_version.sail_code or ""
        sail_changed = base_sail != new_sail
        print(f"      SAIL code changed: {'✅ YES' if sail_changed else '❌ NO'}")
        if sail_changed:
            print(f"         Base length: {len(base_sail)}")
            print(f"         New length: {len(new_sail)}")
        
        # Fields
        base_fields = base_version.fields or ""
        new_fields = new_vendor_version.fields or ""
        fields_changed = base_fields != new_fields
        print(f"      Fields changed: {'✅ YES' if fields_changed else '❌ NO'}")
        
        # Properties
        base_props = base_version.properties or ""
        new_props = new_vendor_version.properties or ""
        props_changed = base_props != new_props
        print(f"      Properties changed: {'✅ YES' if props_changed else '❌ NO'}")
        
        content_changed = sail_changed or fields_changed or props_changed
        print(f"\n   ⚠️  OVERALL: Content changed = {content_changed}")
        
        if not content_changed:
            print(f"   ℹ️  This explains why object is NOT in delta comparison")
            print(f"      (Version UUID may have changed, but content is identical)")
    
    # Step 6: Compare with customer version if exists
    if customized_version and new_vendor_version:
        print(f"\n🔍 Customer Comparison (B vs C):")
        
        version_changed = customized_version.version_uuid != new_vendor_version.version_uuid
        print(f"   Version UUID changed: {'✅ YES' if version_changed else '❌ NO'}")
        
        # Compare content
        cust_sail = customized_version.sail_code or ""
        new_sail = new_vendor_version.sail_code or ""
        sail_changed = cust_sail != new_sail
        print(f"   SAIL code changed: {'✅ YES' if sail_changed else '❌ NO'}")
        if sail_changed:
            print(f"      Customer length: {len(cust_sail)}")
            print(f"      New length: {len(new_sail)}")
        
        cust_fields = customized_version.fields or ""
        new_fields = new_vendor_version.fields or ""
        fields_changed = cust_fields != new_fields
        print(f"   Fields changed: {'✅ YES' if fields_changed else '❌ NO'}")
        
        cust_props = customized_version.properties or ""
        new_props = new_vendor_version.properties or ""
        props_changed = cust_props != new_props
        print(f"   Properties changed: {'✅ YES' if props_changed else '❌ NO'}")
        
        content_changed = sail_changed or fields_changed or props_changed
        print(f"\n   ⚠️  Customer content changed = {content_changed}")

def main():
    """Main diagnostic function."""
    app = create_app()
    
    with app.app_context():
        print_separator("MERGE SESSION MRG_006 - MISSING OBJECTS DIAGNOSIS")
        
        # Get session
        session = db.session.query(MergeSession).filter_by(reference_id='MRG_006').first()
        
        if not session:
            print("❌ Session MRG_006 not found")
            return
        
        print(f"✅ Found session: {session.reference_id}")
        print(f"   ID: {session.id}")
        print(f"   Status: {session.status}")
        print(f"   Total changes: {session.total_changes}")
        print(f"   Created: {session.created_at}")
        
        # Diagnose both objects
        diagnose_object(session.id, "DGS Create Parent", "Process Model")
        diagnose_object(session.id, "DGS_TEXT_RELATIONSHP_MANY_TO_ONE", "Constant")
        
        print_separator("DIAGNOSIS COMPLETE")

if __name__ == "__main__":
    main()
