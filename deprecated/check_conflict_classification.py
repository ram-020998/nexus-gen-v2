"""
Check the classification of AS_GSS_FM_AddConsensusVersion in MRG_001
to see if it's correctly classified based on B vs C content comparison.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, MergeSession, Change, ObjectLookup, ObjectVersion, Package


def check_classification():
    """Check classification of the specific object."""
    app = create_app()
    
    with app.app_context():
        # Find session MRG_001
        session = db.session.query(MergeSession).filter_by(
            reference_id='MRG_001'
        ).first()
        
        if not session:
            print("❌ Session MRG_001 not found!")
            return False
        
        print(f"✅ Found session: {session.reference_id}")
        print(f"Status: {session.status}")
        print(f"Total changes: {session.total_changes}")
        print(f"Created: {session.created_at}")
        
        # Find the specific object
        obj = db.session.query(ObjectLookup).filter_by(
            uuid="_a-0000ea4b-69d2-8000-9c9e-011c48011c48_7139691"
        ).first()
        
        if not obj:
            print("\n❌ Object AS_GSS_FM_AddConsensusVersion not found!")
            return False
        
        print(f"\n✅ Found object:")
        print(f"ID: {obj.id}")
        print(f"UUID: {obj.uuid}")
        print(f"Name: {obj.name}")
        print(f"Type: {obj.object_type}")
        
        # Get the change record
        change = db.session.query(Change).filter_by(
            session_id=session.id,
            object_id=obj.id
        ).first()
        
        if not change:
            print(f"\n❌ No change record found for object {obj.name}")
            return False
        
        print(f"\n✅ Found change record:")
        print(f"Classification: {change.classification}")
        print(f"Vendor change type: {change.vendor_change_type}")
        print(f"Customer change type: {change.customer_change_type}")
        print(f"Display order: {change.display_order}")
        print(f"Status: {change.status}")
        
        # Get delta comparison result
        from models import DeltaComparisonResult
        delta = db.session.query(DeltaComparisonResult).filter_by(
            session_id=session.id,
            object_id=obj.id
        ).first()
        
        if delta:
            print(f"\n✅ Delta comparison (A→C):")
            print(f"Change category: {delta.change_category}")
            print(f"Change type: {delta.change_type}")
            print(f"Version changed: {delta.version_changed}")
            print(f"Content changed: {delta.content_changed}")
        
        # Get packages
        packages = db.session.query(Package).filter_by(
            session_id=session.id
        ).all()
        
        package_map = {pkg.package_type: pkg for pkg in packages}
        
        print(f"\n📦 Packages in session:")
        for pkg_type, pkg in package_map.items():
            print(f"{pkg_type}: {pkg.filename} ({pkg.total_objects} objects)")
        
        # Check which packages contain this object
        from models import PackageObjectMapping
        mappings = db.session.query(PackageObjectMapping).filter_by(
            object_id=obj.id
        ).all()
        
        print(f"\n📋 Object exists in packages:")
        for mapping in mappings:
            pkg = db.session.query(Package).filter_by(id=mapping.package_id).first()
            if pkg:
                print(f"✓ {pkg.package_type}: {pkg.filename}")
        
        # Get versions from all three packages
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
        
        print(f"\n🔍 Classification Analysis:")
        print(f"Vendor change: {change.vendor_change_type}")
        print(f"Customer change: {change.customer_change_type}")
        
        # Determine which rule should apply
        if change.vendor_change_type == 'MODIFIED' and change.customer_change_type == 'MODIFIED':
            print(f"\n✅ Rule 10b: MODIFIED in delta AND modified in customer → CONFLICT")
            print(f"   BUT: Need to check if B == C")
        
        print(f"\n📊 Version details:")
        
        if base_version:
            print(f"base:")
            print(f"  Version UUID: {base_version.version_uuid}")
            print(f"  SAIL code length: {len(base_version.sail_code) if base_version.sail_code else 0} chars")
            print(f"  XML length: {len(base_version.raw_xml) if base_version.raw_xml else 0} chars")
        
        if customer_version:
            print(f"customized:")
            print(f"  Version UUID: {customer_version.version_uuid}")
            print(f"  SAIL code length: {len(customer_version.sail_code) if customer_version.sail_code else 0} chars")
            print(f"  XML length: {len(customer_version.raw_xml) if customer_version.raw_xml else 0} chars")
        
        if new_vendor_version:
            print(f"new_vendor:")
            print(f"  Version UUID: {new_vendor_version.version_uuid}")
            print(f"  SAIL code length: {len(new_vendor_version.sail_code) if new_vendor_version.sail_code else 0} chars")
            print(f"  XML length: {len(new_vendor_version.raw_xml) if new_vendor_version.raw_xml else 0} chars")
        
        # Check if B and C are identical
        if customer_version and new_vendor_version:
            same_version_uuid = customer_version.version_uuid == new_vendor_version.version_uuid
            same_sail_code = customer_version.sail_code == new_vendor_version.sail_code
            
            print(f"\n🔍 B vs C Comparison:")
            print(f"Same version UUID: {same_version_uuid}")
            print(f"Same SAIL code: {same_sail_code}")
            
            if same_version_uuid and same_sail_code:
                print(f"\n✅ B == C (Customer and New Vendor are IDENTICAL)")
                print(f"Expected classification: NO_CONFLICT")
                print(f"Actual classification: {change.classification}")
                
                if change.classification == 'NO_CONFLICT':
                    print(f"\n✅✅ CORRECT: Object properly classified as NO_CONFLICT")
                    return True
                else:
                    print(f"\n❌❌ INCORRECT: Should be NO_CONFLICT but is {change.classification}")
                    return False
            else:
                print(f"\n✅ B != C (Customer and New Vendor are DIFFERENT)")
                print(f"Expected classification: CONFLICT")
                print(f"Actual classification: {change.classification}")
                
                if change.classification == 'CONFLICT':
                    print(f"\n✅✅ CORRECT: Object properly classified as CONFLICT")
                    return True
                else:
                    print(f"\n❌❌ INCORRECT: Should be CONFLICT but is {change.classification}")
                    return False
        
        return False


if __name__ == '__main__':
    success = check_classification()
    sys.exit(0 if success else 1)
