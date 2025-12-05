"""
Test script to verify NO_CONFLICT display logic.

This script tests the new comparison strategy that determines which packages
to compare based on vendor and customer change types.
"""

from app import create_app
from models import db, Change, MergeSession
from services.comparison_retrieval_service import ComparisonRetrievalService
from core.dependency_container import DependencyContainer

def test_comparison_strategy():
    """Test the comparison strategy logic."""
    app = create_app()
    
    with app.app_context():
        # Get a NO_CONFLICT change from the database
        session = db.session.query(MergeSession).filter_by(
            status='ready'
        ).first()
        
        if not session:
            print("No ready session found. Please create a merge session first.")
            return
        
        print(f"\nTesting session: {session.reference_id}")
        print(f"Total changes: {session.total_changes}")
        
        # Get NO_CONFLICT changes
        no_conflict_changes = db.session.query(Change).filter_by(
            session_id=session.id,
            classification='NO_CONFLICT'
        ).limit(5).all()
        
        if not no_conflict_changes:
            print("No NO_CONFLICT changes found in this session.")
            return
        
        print(f"\nFound {len(no_conflict_changes)} NO_CONFLICT changes to test\n")
        
        # Initialize comparison service
        container = DependencyContainer.get_instance()
        comparison_service = container.get_service(ComparisonRetrievalService)
        
        # Test each change
        for change in no_conflict_changes:
            print(f"\n{'='*80}")
            print(f"Object: {change.object.name}")
            print(f"Type: {change.object.object_type}")
            print(f"Classification: {change.classification}")
            print(f"Vendor Change Type: {change.vendor_change_type}")
            print(f"Customer Change Type: {change.customer_change_type}")
            
            # Determine expected comparison type
            if not change.vendor_change_type and change.customer_change_type in ['MODIFIED', 'ADDED']:
                expected_type = 'customer_only'
                expected_old_label = 'Vendor Base'
                expected_new_label = 'Customer'
                print(f"\n✓ Expected: Customer-only comparison (Base vs Customer)")
            else:
                expected_type = 'vendor_changes'
                expected_old_label = 'Vendor Base'
                expected_new_label = 'Vendor Latest'
                print(f"\n✓ Expected: Vendor changes comparison (Base vs Latest)")
            
            # Get packages
            from models import Package
            packages = db.session.query(Package).filter_by(
                session_id=session.id
            ).all()
            
            package_map = {pkg.package_type: pkg.id for pkg in packages}
            
            # Get comparison details
            comparison = comparison_service.get_comparison_details(
                change,
                package_map['base'],
                package_map['customized'],
                package_map['new_vendor']
            )
            
            # Verify comparison type
            actual_type = comparison.get('comparison_type', 'unknown')
            actual_old_label = comparison.get('old_label', 'unknown')
            actual_new_label = comparison.get('new_label', 'unknown')
            
            print(f"\n✓ Actual: {actual_type}")
            print(f"  Old Label: {actual_old_label}")
            print(f"  New Label: {actual_new_label}")
            
            # Check if it matches expected
            if actual_type == expected_type:
                print(f"\n✅ PASS: Comparison type matches expected")
            else:
                print(f"\n❌ FAIL: Expected {expected_type}, got {actual_type}")
            
            if actual_old_label == expected_old_label and actual_new_label == expected_new_label:
                print(f"✅ PASS: Labels match expected")
            else:
                print(f"❌ FAIL: Expected labels ({expected_old_label} vs {expected_new_label})")
                print(f"         Got labels ({actual_old_label} vs {actual_new_label})")

if __name__ == '__main__':
    test_comparison_strategy()
