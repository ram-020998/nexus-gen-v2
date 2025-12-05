"""
Check object-specific tables for actual content.

The object_versions table may not have all content.
Need to check process_models and constants tables.
"""

from app import create_app
from models import db, ProcessModel, Constant, Package
from domain.enums import PackageType

def print_separator(title=""):
    print("\n" + "="*80)
    if title:
        print(title)
        print("="*80)

def check_process_model():
    """Check process_models table for DGS Create Parent."""
    print_separator("PROCESS MODEL: DGS Create Parent")
    
    # Get packages
    packages = db.session.query(Package).filter_by(session_id=6).all()
    package_map = {pkg.package_type: pkg for pkg in packages}
    
    base_pkg = package_map.get(PackageType.BASE.value)
    customized_pkg = package_map.get(PackageType.CUSTOMIZED.value)
    new_vendor_pkg = package_map.get(PackageType.NEW_VENDOR.value)
    
    # Object ID from diagnosis
    object_id = 2551
    
    # Check process_models table
    print("\n📊 Process Models Table:")
    
    # Get all process models for this object across all packages
    process_models = db.session.query(ProcessModel).filter_by(
        object_id=object_id
    ).all()
    
    print(f"   Found {len(process_models)} process model records")
    
    for pm in process_models:
        # Find which package this belongs to
        pkg_type = "UNKNOWN"
        if hasattr(pm, 'package_id'):
            if pm.package_id == base_pkg.id:
                pkg_type = "BASE (A)"
            elif pm.package_id == customized_pkg.id:
                pkg_type = "CUSTOMIZED (B)"
            elif pm.package_id == new_vendor_pkg.id:
                pkg_type = "NEW VENDOR (C)"
        
        print(f"\n   Package: {pkg_type}")
        print(f"      ID: {pm.id}")
        print(f"      UUID: {pm.uuid}")
        print(f"      Version UUID: {pm.version_uuid}")
        print(f"      Name: {pm.name}")
        
        # Check for nodes, flows, variables
        if hasattr(pm, 'nodes'):
            node_count = pm.nodes.count() if pm.nodes else 0
            print(f"      Nodes: {node_count}")
        if hasattr(pm, 'flows'):
            flow_count = pm.flows.count() if pm.flows else 0
            print(f"      Flows: {flow_count}")
        if hasattr(pm, 'variables'):
            var_count = pm.variables.count() if pm.variables else 0
            print(f"      Variables: {var_count}")

def check_constant():
    """Check constants table for DGS_TEXT_RELATIONSHP_MANY_TO_ONE."""
    print_separator("CONSTANT: DGS_TEXT_RELATIONSHP_MANY_TO_ONE")
    
    # Get packages
    packages = db.session.query(Package).filter_by(session_id=6).all()
    package_map = {pkg.package_type: pkg for pkg in packages}
    
    base_pkg = package_map.get(PackageType.BASE.value)
    customized_pkg = package_map.get(PackageType.CUSTOMIZED.value)
    new_vendor_pkg = package_map.get(PackageType.NEW_VENDOR.value)
    
    # Object ID from diagnosis
    object_id = 2548
    
    # Check constants table
    print("\n📊 Constants Table:")
    
    # Get all constants for this object
    constants = db.session.query(Constant).filter_by(
        object_id=object_id
    ).all()
    
    print(f"   Found {len(constants)} constant records")
    
    for const in constants:
        # Find which package this belongs to
        pkg_type = "UNKNOWN"
        if hasattr(const, 'package_id'):
            if const.package_id == base_pkg.id:
                pkg_type = "BASE (A)"
            elif const.package_id == customized_pkg.id:
                pkg_type = "CUSTOMIZED (B)"
            elif const.package_id == new_vendor_pkg.id:
                pkg_type = "NEW VENDOR (C)"
        
        print(f"\n   Package: {pkg_type}")
        print(f"      ID: {const.id}")
        print(f"      UUID: {const.uuid}")
        print(f"      Version UUID: {const.version_uuid}")
        print(f"      Name: {const.name}")
        
        # Check for value
        if hasattr(const, 'value'):
            value_preview = str(const.value)[:100] if const.value else "None"
            print(f"      Value: {value_preview}")
        if hasattr(const, 'data_type'):
            print(f"      Data Type: {const.data_type}")

def main():
    app = create_app()
    
    with app.app_context():
        print_separator("CHECKING OBJECT-SPECIFIC TABLES FOR SESSION MRG_006")
        
        check_process_model()
        check_constant()
        
        print_separator("CHECK COMPLETE")

if __name__ == "__main__":
    main()
