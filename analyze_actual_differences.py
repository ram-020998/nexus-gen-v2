"""
Analyze actual differences in process model and constant content.
"""

from app import create_app
from models import db, ProcessModel, ProcessModelVariable, Constant, Package
from domain.enums import PackageType

def print_separator(title=""):
    print("\n" + "="*80)
    if title:
        print(title)
        print("="*80)

def analyze_process_model():
    """Analyze process model differences."""
    print_separator("PROCESS MODEL ANALYSIS: DGS Create Parent")
    
    # Get packages
    packages = db.session.query(Package).filter_by(session_id=6).all()
    package_map = {pkg.package_type: pkg for pkg in packages}
    
    base_pkg = package_map.get(PackageType.BASE.value)
    customized_pkg = package_map.get(PackageType.CUSTOMIZED.value)
    new_vendor_pkg = package_map.get(PackageType.NEW_VENDOR.value)
    
    # Get process models
    base_pm = db.session.query(ProcessModel).filter_by(
        object_id=2551,
        package_id=base_pkg.id
    ).first()
    
    cust_pm = db.session.query(ProcessModel).filter_by(
        object_id=2551,
        package_id=customized_pkg.id
    ).first()
    
    new_pm = db.session.query(ProcessModel).filter_by(
        object_id=2551,
        package_id=new_vendor_pkg.id
    ).first()
    
    print("\n📊 Structure Comparison:")
    print(f"   Base (A):       {base_pm.nodes.count()} nodes, {base_pm.flows.count()} flows, {base_pm.variables.count()} variables")
    print(f"   Customized (B): {cust_pm.nodes.count()} nodes, {cust_pm.flows.count()} flows, {cust_pm.variables.count()} variables")
    print(f"   New Vendor (C): {new_pm.nodes.count()} nodes, {new_pm.flows.count()} flows, {new_pm.variables.count()} variables")
    
    # Compare A → C (Delta)
    print("\n🔍 Delta Comparison (A → C):")
    a_nodes = base_pm.nodes.count()
    c_nodes = new_pm.nodes.count()
    a_flows = base_pm.flows.count()
    c_flows = new_pm.flows.count()
    a_vars = base_pm.variables.count()
    c_vars = new_pm.variables.count()
    
    delta_changed = (a_nodes != c_nodes) or (a_flows != c_flows) or (a_vars != c_vars)
    print(f"   Nodes changed: {a_nodes} → {c_nodes} = {'YES' if a_nodes != c_nodes else 'NO'}")
    print(f"   Flows changed: {a_flows} → {c_flows} = {'YES' if a_flows != c_flows else 'NO'}")
    print(f"   Variables changed: {a_vars} → {c_vars} = {'YES' if a_vars != c_vars else 'NO'}")
    print(f"   ⚠️  DELTA HAS CHANGES: {delta_changed}")
    
    if delta_changed:
        print("\n   📝 Variable Details:")
        print(f"\n   Base (A) Variables:")
        for var in base_pm.variables:
            print(f"      - {var.variable_name} ({var.variable_type})")
        
        print(f"\n   New Vendor (C) Variables:")
        for var in new_pm.variables:
            print(f"      - {var.variable_name} ({var.variable_type})")
    
    # Compare B vs C (Customer)
    print("\n🔍 Customer Comparison (B vs C):")
    b_nodes = cust_pm.nodes.count()
    b_flows = cust_pm.flows.count()
    b_vars = cust_pm.variables.count()
    
    customer_changed = (b_nodes != c_nodes) or (b_flows != c_flows) or (b_vars != c_vars)
    print(f"   Nodes changed: {b_nodes} vs {c_nodes} = {'YES' if b_nodes != c_nodes else 'NO'}")
    print(f"   Flows changed: {b_flows} vs {c_flows} = {'YES' if b_flows != c_flows else 'NO'}")
    print(f"   Variables changed: {b_vars} vs {c_vars} = {'YES' if b_vars != c_vars else 'NO'}")
    print(f"   ⚠️  CUSTOMER HAS CHANGES: {customer_changed}")
    
    if customer_changed:
        print(f"\n   📝 Variable Details:")
        print(f"\n   Customized (B) Variables:")
        for var in cust_pm.variables:
            print(f"      - {var.variable_name} ({var.variable_type})")
        
        print(f"\n   New Vendor (C) Variables:")
        for var in new_pm.variables:
            print(f"      - {var.variable_name} ({var.variable_type})")
    
    # Classification
    print("\n🎯 Expected Classification:")
    if delta_changed and customer_changed:
        print("   ✅ CONFLICT (Rule 10b: MODIFIED in delta AND modified in customer)")
    elif delta_changed and not customer_changed:
        print("   ✅ NO_CONFLICT (Rule 10a: MODIFIED in delta AND not modified in customer)")
    else:
        print("   ❌ Should not be in working set (no delta change)")

def analyze_constant():
    """Analyze constant differences."""
    print_separator("CONSTANT ANALYSIS: DGS_TEXT_RELATIONSHP_MANY_TO_ONE")
    
    # Get packages
    packages = db.session.query(Package).filter_by(session_id=6).all()
    package_map = {pkg.package_type: pkg for pkg in packages}
    
    base_pkg = package_map.get(PackageType.BASE.value)
    customized_pkg = package_map.get(PackageType.CUSTOMIZED.value)
    new_vendor_pkg = package_map.get(PackageType.NEW_VENDOR.value)
    
    # Get constants
    base_const = db.session.query(Constant).filter_by(
        object_id=2548,
        package_id=base_pkg.id
    ).first()
    
    cust_const = db.session.query(Constant).filter_by(
        object_id=2548,
        package_id=customized_pkg.id
    ).first()
    
    new_const = db.session.query(Constant).filter_by(
        object_id=2548,
        package_id=new_vendor_pkg.id
    ).first()
    
    print("\n📊 Constant Values:")
    print(f"   Base (A):       value='{base_const.constant_value}', type={base_const.constant_type}")
    print(f"   Customized (B): value='{cust_const.constant_value}', type={cust_const.constant_type}")
    print(f"   New Vendor (C): value='{new_const.constant_value}', type={new_const.constant_type}")
    
    # Compare A → C (Delta)
    print("\n🔍 Delta Comparison (A → C):")
    delta_changed = (base_const.constant_value != new_const.constant_value) or (base_const.constant_type != new_const.constant_type)
    print(f"   Value changed: '{base_const.constant_value}' → '{new_const.constant_value}' = {'YES' if base_const.constant_value != new_const.constant_value else 'NO'}")
    print(f"   Type changed: {base_const.constant_type} → {new_const.constant_type} = {'YES' if base_const.constant_type != new_const.constant_type else 'NO'}")
    print(f"   ⚠️  DELTA HAS CHANGES: {delta_changed}")
    
    # Compare B vs C (Customer)
    print("\n🔍 Customer Comparison (B vs C):")
    customer_changed = (cust_const.constant_value != new_const.constant_value) or (cust_const.constant_type != new_const.constant_type)
    print(f"   Value changed: '{cust_const.constant_value}' vs '{new_const.constant_value}' = {'YES' if cust_const.constant_value != new_const.constant_value else 'NO'}")
    print(f"   Type changed: {cust_const.constant_type} vs {new_const.constant_type} = {'YES' if cust_const.constant_type != new_const.constant_type else 'NO'}")
    print(f"   ⚠️  CUSTOMER HAS CHANGES: {customer_changed}")
    
    # Classification
    print("\n🎯 Expected Classification:")
    if delta_changed and customer_changed:
        print("   ✅ CONFLICT (Rule 10b: MODIFIED in delta AND modified in customer)")
    elif delta_changed and not customer_changed:
        print("   ✅ NO_CONFLICT (Rule 10a: MODIFIED in delta AND not modified in customer)")
    else:
        print("   ❌ Should not be in working set (no delta change)")

def main():
    app = create_app()
    
    with app.app_context():
        print_separator("ANALYZING ACTUAL CONTENT DIFFERENCES")
        
        analyze_process_model()
        analyze_constant()
        
        print_separator("ANALYSIS COMPLETE")
        
        print("\n💡 CONCLUSION:")
        print("   The delta comparison service is NOT checking object-specific tables.")
        print("   It only checks object_versions (sail_code, fields, properties).")
        print("   For process models, it needs to check nodes/flows/variables.")
        print("   For constants, it needs to check the value field.")

if __name__ == "__main__":
    main()
