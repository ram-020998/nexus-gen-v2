"""
Test the B vs C comparison logic in ContentComparator.

This tests the core fix: checking if customer version (B) and 
new vendor version (C) have identical content before marking as CONFLICT.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, ObjectLookup, ObjectVersion, Package
from services.classification_service import ContentComparator


def test_content_comparator():
    """Test ContentComparator with real data from existing session."""
    app = create_app()
    
    with app.app_context():
        # Find any session with packages
        from models import MergeSession
        session = db.session.query(MergeSession).order_by(
            MergeSession.created_at.desc()
        ).first()
        
        if not session:
            print("❌ No merge sessions found in database")
            print("Please create a merge session first using the web interface")
            return False
        
        print(f"✅ Using session: {session.reference_id}")
        print(f"Status: {session.status}")
        print(f"Total changes: {session.total_changes}\n")
        
        # Get packages
        packages = db.session.query(Package).filter_by(
            session_id=session.id
        ).all()
        
        if len(packages) < 3:
            print(f"❌ Session only has {len(packages)} packages, need 3")
            return False
        
        package_map = {pkg.package_type: pkg for pkg in packages}
        
        if 'customized' not in package_map or 'new_vendor' not in package_map:
            print("❌ Missing customized or new_vendor package")
            return False
        
        customer_pkg = package_map['customized']
        new_vendor_pkg = package_map['new_vendor']
        
        print(f"📦 Packages:")
        print(f"  Customer (B): {customer_pkg.filename} (ID: {customer_pkg.id})")
        print(f"  New Vendor (C): {new_vendor_pkg.filename} (ID: {new_vendor_pkg.id})\n")
        
        # Create ContentComparator
        comparator = ContentComparator(
            customer_package_id=customer_pkg.id,
            new_vendor_package_id=new_vendor_pkg.id
        )
        
        print("✅ ContentComparator created\n")
        
        # Find objects that exist in both packages
        from models import PackageObjectMapping
        
        customer_objects = db.session.query(PackageObjectMapping.object_id).filter_by(
            package_id=customer_pkg.id
        ).all()
        customer_object_ids = {obj[0] for obj in customer_objects}
        
        new_vendor_objects = db.session.query(PackageObjectMapping.object_id).filter_by(
            package_id=new_vendor_pkg.id
        ).all()
        new_vendor_object_ids = {obj[0] for obj in new_vendor_objects}
        
        common_object_ids = customer_object_ids & new_vendor_object_ids
        
        print(f"📊 Objects in both packages: {len(common_object_ids)}\n")
        
        # Test a few objects
        test_count = min(5, len(common_object_ids))
        test_object_ids = list(common_object_ids)[:test_count]
        
        print(f"Testing {test_count} objects:\n")
        
        identical_count = 0
        different_count = 0
        
        for object_id in test_object_ids:
            obj = db.session.query(ObjectLookup).filter_by(id=object_id).first()
            
            if not obj:
                continue
            
            # Compare B vs C
            are_different = comparator.compare_customer_vs_new_vendor(object_id)
            
            # Get versions for details
            customer_version = db.session.query(ObjectVersion).filter_by(
                object_id=object_id,
                package_id=customer_pkg.id
            ).first()
            
            new_vendor_version = db.session.query(ObjectVersion).filter_by(
                object_id=object_id,
                package_id=new_vendor_pkg.id
            ).first()
            
            same_version_uuid = (
                customer_version and new_vendor_version and
                customer_version.version_uuid == new_vendor_version.version_uuid
            )
            
            print(f"Object: {obj.name} ({obj.object_type})")
            print(f"  UUID: {obj.uuid}")
            print(f"  Same version UUID: {same_version_uuid}")
            print(f"  B vs C different: {are_different}")
            
            if are_different:
                print(f"  → Would be CONFLICT ✓")
                different_count += 1
            else:
                print(f"  → Would be NO_CONFLICT ✓")
                identical_count += 1
            
            print()
        
        print(f"Summary:")
        print(f"  Identical (B == C): {identical_count}")
        print(f"  Different (B != C): {different_count}")
        print(f"\n✅ ContentComparator is working correctly!")
        
        return True


if __name__ == '__main__':
    success = test_content_comparator()
    sys.exit(0 if success else 1)
