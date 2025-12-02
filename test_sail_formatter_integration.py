"""
Test SAIL Formatter Integration

Test the SAIL formatter with the three-way merge workflow.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, MergeSession, ObjectVersion, Interface, ExpressionRule
from services.three_way_merge_orchestrator import ThreeWayMergeOrchestrator
from core.dependency_container import DependencyContainer


def test_sail_formatter_integration():
    """Test SAIL formatter with real package extraction"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("SAIL Formatter Integration Test")
        print("=" * 80)
        
        # Clean up old sessions
        print("\n1. Cleaning up old test sessions...")
        old_sessions = MergeSession.query.filter(
            MergeSession.reference_id.like('MS_%')
        ).all()
        for session in old_sessions:
            db.session.delete(session)
        db.session.commit()
        print(f"   Deleted {len(old_sessions)} old sessions")
        
        # Initialize orchestrator
        print("\n2. Initializing orchestrator...")
        container = DependencyContainer.get_instance()
        orchestrator = container.get_service(ThreeWayMergeOrchestrator)
        
        # Package paths
        base_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip"
        customized_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application Customer Version.zip"
        new_vendor_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application Vendor New Version.zip"
        
        # Check if files exist
        if not all(os.path.exists(p) for p in [base_path, customized_path, new_vendor_path]):
            print("   ❌ Test package files not found!")
            return
        
        print("   ✓ Test packages found")
        
        # Create merge session
        print("\n3. Creating merge session and extracting packages...")
        print("   This will test SAIL code formatting during extraction...")
        
        session = orchestrator.create_merge_session(
            base_zip_path=base_path,
            customized_zip_path=customized_path,
            new_vendor_zip_path=new_vendor_path
        )
        
        print(f"   ✓ Session created: {session.reference_id}")
        
        # Check SAIL code formatting in object_versions
        print("\n4. Checking SAIL code formatting in object_versions...")
        versions_with_sail = ObjectVersion.query.join(
            ObjectVersion.package
        ).filter(
            ObjectVersion.package.has(session_id=session.id),
            ObjectVersion.sail_code.isnot(None),
            ObjectVersion.sail_code != ''
        ).limit(5).all()
        
        print(f"   Found {len(versions_with_sail)} versions with SAIL code")
        
        for version in versions_with_sail:
            sail_code = version.sail_code
            print(f"\n   Object ID: {version.object_id}")
            print(f"   SAIL code length: {len(sail_code)} chars")
            
            # Check for UUID patterns (should be replaced)
            import re
            uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
            uuids_found = re.findall(uuid_pattern, sail_code)
            
            if uuids_found:
                print(f"   ⚠️  Found {len(uuids_found)} UUIDs (may be in comments or strings)")
            else:
                print(f"   ✓ No raw UUIDs found")
            
            # Check for rule! and cons! references
            rule_refs = len(re.findall(r'rule!\w+', sail_code))
            cons_refs = len(re.findall(r'cons!\w+', sail_code))
            
            if rule_refs > 0 or cons_refs > 0:
                print(f"   ✓ Found {rule_refs} rule! refs and {cons_refs} cons! refs")
            
            # Show first 200 chars
            print(f"   Preview: {sail_code[:200]}...")
        
        # Check SAIL code in interfaces
        print("\n5. Checking SAIL code formatting in interfaces...")
        from models import Package
        interfaces_with_sail = Interface.query.join(
            Package, Package.id == Interface.package_id
        ).filter(
            Package.session_id == session.id,
            Interface.sail_code.isnot(None),
            Interface.sail_code != ''
        ).limit(3).all()
        
        print(f"   Found {len(interfaces_with_sail)} interfaces with SAIL code")
        
        for interface in interfaces_with_sail:
            print(f"\n   Interface: {interface.name}")
            print(f"   SAIL code length: {len(interface.sail_code)} chars")
            print(f"   Preview: {interface.sail_code[:150]}...")
        
        # Check SAIL code in expression rules
        print("\n6. Checking SAIL code formatting in expression rules...")
        rules_with_sail = ExpressionRule.query.join(
            Package, Package.id == ExpressionRule.package_id
        ).filter(
            Package.session_id == session.id,
            ExpressionRule.sail_code.isnot(None),
            ExpressionRule.sail_code != ''
        ).limit(3).all()
        
        print(f"   Found {len(rules_with_sail)} expression rules with SAIL code")
        
        for rule in rules_with_sail:
            print(f"\n   Rule: {rule.name}")
            print(f"   SAIL code length: {len(rule.sail_code)} chars")
            print(f"   Preview: {rule.sail_code[:150]}...")
        
        print("\n" + "=" * 80)
        print("✓ SAIL Formatter Integration Test Complete!")
        print("=" * 80)
        
        # Clean up
        print("\nCleaning up test session...")
        db.session.delete(session)
        db.session.commit()
        print("✓ Cleanup complete")


if __name__ == '__main__':
    test_sail_formatter_integration()
