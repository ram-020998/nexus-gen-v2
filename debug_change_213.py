"""
Debug script to check change 213 in session MRG_010
"""

from app import create_app
from models import db, Change, MergeSession, Package
from services.comparison_retrieval_service import ComparisonRetrievalService
from core.dependency_container import DependencyContainer

def debug_change():
    """Debug change 213."""
    app = create_app()
    
    with app.app_context():
        # Get session
        session = db.session.query(MergeSession).filter_by(
            reference_id='MRG_010'
        ).first()
        
        if not session:
            print("Session MRG_010 not found")
            return
        
        print(f"Session: {session.reference_id}")
        print(f"Status: {session.status}")
        
        # Get change 213
        change = db.session.query(Change).filter_by(
            id=213,
            session_id=session.id
        ).first()
        
        if not change:
            print("Change 213 not found")
            return
        
        print(f"\n{'='*80}")
        print(f"Change ID: {change.id}")
        print(f"Object: {change.object.name}")
        print(f"Object Type: {change.object.object_type}")
        print(f"Classification: {change.classification}")
        print(f"Vendor Change Type: {change.vendor_change_type}")
        print(f"Customer Change Type: {change.customer_change_type}")
        print(f"{'='*80}\n")
        
        # Get packages
        packages = db.session.query(Package).filter_by(
            session_id=session.id
        ).all()
        
        package_map = {pkg.package_type: pkg.id for pkg in packages}
        
        print("Packages:")
        for pkg_type, pkg_id in package_map.items():
            print(f"  {pkg_type}: {pkg_id}")
        
        # Get comparison service
        container = DependencyContainer.get_instance()
        comparison_service = container.get_service(ComparisonRetrievalService)
        
        # Test the strategy determination
        strategy = comparison_service._determine_comparison_strategy(
            change,
            package_map['base'],
            package_map['customized'],
            package_map['new_vendor']
        )
        
        print(f"\nComparison Strategy:")
        print(f"  Type: {strategy['comparison_type']}")
        print(f"  Old Package ID: {strategy['old_package_id']}")
        print(f"  New Package ID: {strategy['new_package_id']}")
        print(f"  Old Label: {strategy['old_label']}")
        print(f"  New Label: {strategy['new_label']}")
        
        # Get full comparison details
        comparison = comparison_service.get_comparison_details(
            change,
            package_map['base'],
            package_map['customized'],
            package_map['new_vendor']
        )
        
        print(f"\nComparison Details:")
        print(f"  Object Type: {comparison.get('object_type')}")
        print(f"  Comparison Type: {comparison.get('comparison_type')}")
        print(f"  Old Label: {comparison.get('old_label')}")
        print(f"  New Label: {comparison.get('new_label')}")
        print(f"  Has Changes: {comparison.get('has_changes')}")
        
        # Check the logic
        print(f"\n{'='*80}")
        print("Logic Check:")
        print(f"  vendor_change_type is None: {change.vendor_change_type is None}")
        print(f"  customer_change_type in ['MODIFIED', 'ADDED']: {change.customer_change_type in ['MODIFIED', 'ADDED']}")
        
        if not change.vendor_change_type and change.customer_change_type in ['MODIFIED', 'ADDED']:
            print(f"  ✓ Should show: Customer vs Base")
            print(f"  ✓ Expected labels: 'Vendor Base' vs 'Customer'")
        else:
            print(f"  ✓ Should show: Vendor Base vs Vendor Latest")
            print(f"  ✓ Expected labels: 'Vendor Base' vs 'Vendor Latest'")
        
        print(f"{'='*80}")

if __name__ == '__main__':
    debug_change()
