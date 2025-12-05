"""
Simple SAIL Formatter Test

Test SAIL formatter without full workflow.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, ObjectVersion, Interface, ExpressionRule, ObjectLookup
from services.sail_formatter import SAILFormatter


def test_sail_formatter_with_db():
    """Test SAIL formatter with database objects"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("SAIL Formatter Database Test")
        print("=" * 80)
        
        # Get some objects with SAIL code
        print("\n1. Finding objects with SAIL code...")
        
        versions = ObjectVersion.query.filter(
            ObjectVersion.sail_code.isnot(None),
            ObjectVersion.sail_code != ''
        ).limit(3).all()
        
        if not versions:
            print("   ❌ No objects with SAIL code found in database")
            print("   Run a merge session first to populate data")
            return
        
        print(f"   Found {len(versions)} object versions with SAIL code")
        
        # Build object lookup from database
        print("\n2. Building object lookup cache...")
        all_objects = ObjectLookup.query.all()
        object_lookup = {}
        for obj in all_objects:
            object_lookup[obj.uuid] = {
                'name': obj.name,
                'object_type': obj.object_type
            }
        print(f"   Built lookup cache with {len(object_lookup)} objects")
        
        # Initialize formatter
        print("\n3. Initializing SAIL formatter...")
        formatter = SAILFormatter()
        formatter._initialize_dependencies()
        formatter.set_object_lookup(object_lookup)
        print("   ✓ Formatter initialized")
        
        # Format SAIL code
        print("\n4. Formatting SAIL code...")
        for version in versions:
            print(f"\n   Object ID: {version.object_id}")
            print(f"   Original length: {len(version.sail_code)} chars")
            
            # Show original preview
            print(f"   Original preview:")
            print(f"   {version.sail_code[:200]}...")
            
            # Format
            formatted = formatter.format_sail_code(version.sail_code)
            print(f"\n   Formatted length: {len(formatted)} chars")
            print(f"   Formatted preview:")
            print(f"   {formatted[:200]}...")
            
            # Check for improvements
            import re
            
            # Count UUID patterns
            uuid_pattern = r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
            orig_uuids = len(re.findall(uuid_pattern, version.sail_code))
            formatted_uuids = len(re.findall(uuid_pattern, formatted))
            
            # Count SYSTEM_SYSRULES patterns
            orig_system = len(re.findall(r'SYSTEM_SYSRULES', version.sail_code))
            formatted_system = len(re.findall(r'SYSTEM_SYSRULES', formatted))
            
            # Count internal function names
            orig_internal = len(re.findall(r'_internal', version.sail_code))
            formatted_internal = len(re.findall(r'_internal', formatted))
            
            print(f"\n   Improvements:")
            if orig_uuids != formatted_uuids:
                print(f"   - UUIDs: {orig_uuids} → {formatted_uuids}")
            if orig_system != formatted_system:
                print(f"   - SYSTEM_SYSRULES: {orig_system} → {formatted_system}")
            if orig_internal != formatted_internal:
                print(f"   - _internal functions: {orig_internal} → {formatted_internal}")
            
            if orig_uuids == formatted_uuids and orig_system == formatted_system and orig_internal == formatted_internal:
                print(f"   - No replacements made (may not contain UUIDs or internal functions)")
        
        print("\n" + "=" * 80)
        print("✓ SAIL Formatter Test Complete!")
        print("=" * 80)


if __name__ == '__main__':
    test_sail_formatter_with_db()
