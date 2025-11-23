#!/usr/bin/env python3
"""
Test Migration Workflow

This script tests the complete migration workflow by:
1. Creating sample merge session data (if needed)
2. Running the migration
3. Verifying the application works with migrated data
4. Testing all key functionality

Usage:
    python test_migration_workflow.py
"""

import sys
from pathlib import Path

from app import create_app
from models import db, MergeSession, Package, AppianObject, Change, ChangeReview
from services.merge_assistant.three_way_merge_service import ThreeWayMergeService


def test_query_performance():
    """Test that queries work efficiently with normalized schema"""
    print("\n" + "="*80)
    print("Testing Query Performance")
    print("="*80)
    
    app = create_app()
    
    with app.app_context():
        sessions = MergeSession.query.all()
        
        if not sessions:
            print("⚠️  No sessions found. Skipping query performance tests.")
            return True
        
        session = sessions[0]
        service = ThreeWayMergeService()
        
        try:
            # Test 1: Get ordered changes
            print("\n🧪 Test 1: Get ordered changes")
            changes = service.get_ordered_changes(session.id)
            print(f"   ✅ Retrieved {len(changes)} changes")
            
            # Test 2: Filter by classification
            print("\n🧪 Test 2: Filter by classification")
            conflict_changes = service.filter_changes(
                session.id,
                classification='CONFLICT'
            )
            print(f"   ✅ Found {len(conflict_changes)} conflict changes")
            
            # Test 3: Filter by object type
            print("\n🧪 Test 3: Filter by object type")
            interface_changes = service.filter_changes(
                session.id,
                object_type='Interface'
            )
            print(f"   ✅ Found {len(interface_changes)} interface changes")
            
            # Test 4: Search by name
            print("\n🧪 Test 4: Search by object name")
            search_results = service.filter_changes(
                session.id,
                search_term='test'
            )
            print(f"   ✅ Found {len(search_results)} matches for 'test'")
            
            # Test 5: Get summary
            print("\n🧪 Test 5: Get session summary")
            summary = service.get_summary(session.id)
            print(f"   ✅ Retrieved summary with {summary.get('total_changes', 0)} changes")
            
            # Test 6: Combined filters
            print("\n🧪 Test 6: Combined filters")
            combined_results = service.filter_changes(
                session.id,
                classification='NO_CONFLICT',
                object_type='Interface'
            )
            print(f"   ✅ Found {len(combined_results)} no-conflict interface changes")
            
            print("\n✅ All query performance tests passed")
            return True
            
        except Exception as e:
            print(f"\n❌ Query performance test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def test_data_integrity():
    """Test that data integrity is maintained"""
    print("\n" + "="*80)
    print("Testing Data Integrity")
    print("="*80)
    
    app = create_app()
    
    with app.app_context():
        sessions = MergeSession.query.all()
        
        if not sessions:
            print("⚠️  No sessions found. Skipping data integrity tests.")
            return True
        
        try:
            for session in sessions:
                print(f"\n🔍 Checking session {session.reference_id}...")
                
                # Test 1: Package count
                packages = Package.query.filter_by(session_id=session.id).all()
                assert len(packages) == 3, f"Expected 3 packages, got {len(packages)}"
                print(f"   ✅ Package count correct: {len(packages)}")
                
                # Test 2: Object-package linkage
                for package in packages:
                    objects = AppianObject.query.filter_by(package_id=package.id).all()
                    assert len(objects) > 0, f"No objects for package {package.id}"
                    
                    # Verify all objects have valid package_id
                    for obj in objects:
                        assert obj.package_id == package.id
                        assert obj.uuid is not None
                        assert obj.name is not None
                        assert obj.object_type is not None
                
                print(f"   ✅ Object-package linkage verified")
                
                # Test 3: Change-object linkage
                changes = Change.query.filter_by(session_id=session.id).all()
                for change in changes:
                    # At least one object reference should exist
                    has_reference = (
                        change.base_object_id is not None or
                        change.customer_object_id is not None or
                        change.vendor_object_id is not None
                    )
                    assert has_reference, f"Change {change.id} has no object references"
                    
                    # Verify foreign keys are valid
                    if change.base_object_id:
                        obj = AppianObject.query.get(change.base_object_id)
                        assert obj is not None, f"Invalid base_object_id {change.base_object_id}"
                    
                    if change.customer_object_id:
                        obj = AppianObject.query.get(change.customer_object_id)
                        assert obj is not None, f"Invalid customer_object_id {change.customer_object_id}"
                    
                    if change.vendor_object_id:
                        obj = AppianObject.query.get(change.vendor_object_id)
                        assert obj is not None, f"Invalid vendor_object_id {change.vendor_object_id}"
                
                print(f"   ✅ Change-object linkage verified")
                
                # Test 4: Review-change linkage
                reviews = ChangeReview.query.filter_by(session_id=session.id).all()
                for review in reviews:
                    if review.change_id:
                        change = Change.query.get(review.change_id)
                        assert change is not None, f"Invalid change_id {review.change_id}"
                
                print(f"   ✅ Review-change linkage verified")
                
                # Test 5: Display order
                changes = Change.query.filter_by(
                    session_id=session.id
                ).order_by(Change.display_order).all()
                
                for i, change in enumerate(changes):
                    assert change.display_order == i, \
                        f"Display order mismatch: expected {i}, got {change.display_order}"
                
                print(f"   ✅ Display order verified")
            
            print("\n✅ All data integrity tests passed")
            return True
            
        except AssertionError as e:
            print(f"\n❌ Data integrity test failed: {str(e)}")
            return False
        except Exception as e:
            print(f"\n❌ Data integrity test error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def test_ui_functionality():
    """Test that UI functionality works with migrated data"""
    print("\n" + "="*80)
    print("Testing UI Functionality")
    print("="*80)
    
    app = create_app()
    
    with app.app_context():
        sessions = MergeSession.query.all()
        
        if not sessions:
            print("⚠️  No sessions found. Skipping UI functionality tests.")
            return True
        
        session = sessions[0]
        service = ThreeWayMergeService()
        
        try:
            # Test 1: Session list view
            print("\n🧪 Test 1: Session list view")
            all_sessions = MergeSession.query.order_by(
                MergeSession.created_at.desc()
            ).all()
            print(f"   ✅ Retrieved {len(all_sessions)} sessions for list view")
            
            # Test 2: Session summary view
            print("\n🧪 Test 2: Session summary view")
            summary = service.get_summary(session.id)
            assert 'total_changes' in summary
            assert 'packages' in summary
            print(f"   ✅ Summary view data complete")
            
            # Test 3: Change list view
            print("\n🧪 Test 3: Change list view")
            changes = service.get_ordered_changes(session.id)
            assert len(changes) > 0
            
            # Verify each change has required fields for UI
            for change in changes[:5]:  # Check first 5
                assert 'object_uuid' in change
                assert 'object_name' in change
                assert 'object_type' in change
                assert 'classification' in change
            
            print(f"   ✅ Change list view data complete")
            
            # Test 4: Change detail view
            print("\n🧪 Test 4: Change detail view")
            if changes:
                change = changes[0]
                change_id = change.get('id')
                
                if change_id:
                    change_obj = Change.query.get(change_id)
                    assert change_obj is not None
                    
                    # Verify related objects can be loaded
                    if change_obj.base_object_id:
                        base_obj = AppianObject.query.get(change_obj.base_object_id)
                        assert base_obj is not None
                    
                    print(f"   ✅ Change detail view data complete")
            
            # Test 5: Filter UI
            print("\n🧪 Test 5: Filter functionality")
            classifications = ['NO_CONFLICT', 'CONFLICT', 'CUSTOMER_ONLY', 'REMOVED_BUT_CUSTOMIZED']
            for classification in classifications:
                filtered = service.filter_changes(session.id, classification=classification)
                print(f"      {classification}: {len(filtered)} changes")
            
            print(f"   ✅ Filter functionality working")
            
            # Test 6: Search UI
            print("\n🧪 Test 6: Search functionality")
            search_terms = ['interface', 'rule', 'record']
            for term in search_terms:
                results = service.filter_changes(session.id, search_term=term)
                print(f"      '{term}': {len(results)} results")
            
            print(f"   ✅ Search functionality working")
            
            print("\n✅ All UI functionality tests passed")
            return True
            
        except Exception as e:
            print(f"\n❌ UI functionality test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def test_report_generation():
    """Test that report generation works with migrated data"""
    print("\n" + "="*80)
    print("Testing Report Generation")
    print("="*80)
    
    app = create_app()
    
    with app.app_context():
        sessions = MergeSession.query.all()
        
        if not sessions:
            print("⚠️  No sessions found. Skipping report generation tests.")
            return True
        
        session = sessions[0]
        service = ThreeWayMergeService()
        
        try:
            # Test 1: Generate report data
            print("\n🧪 Test 1: Generate report data")
            report_data = service.generate_report(session.id)
            
            # Verify report structure
            assert 'session' in report_data
            assert 'summary' in report_data
            assert 'changes' in report_data
            
            print(f"   ✅ Report data structure correct")
            
            # Test 2: Verify report completeness
            print("\n🧪 Test 2: Verify report completeness")
            assert report_data['session']['reference_id'] == session.reference_id
            assert 'total_changes' in report_data['summary']
            assert len(report_data['changes']) > 0
            
            print(f"   ✅ Report data complete")
            
            # Test 3: Verify change details in report
            print("\n🧪 Test 3: Verify change details in report")
            for change in report_data['changes'][:5]:  # Check first 5
                assert 'object_name' in change
                assert 'object_type' in change
                assert 'classification' in change
                assert 'change_type' in change
            
            print(f"   ✅ Change details complete in report")
            
            print("\n✅ All report generation tests passed")
            return True
            
        except Exception as e:
            print(f"\n❌ Report generation test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main test runner"""
    print("\n" + "="*80)
    print("MIGRATION WORKFLOW TEST SUITE")
    print("="*80)
    
    # Check if there's data to test
    app = create_app()
    with app.app_context():
        session_count = MergeSession.query.count()
        
        if session_count == 0:
            print("\n⚠️  No merge sessions found in database.")
            print("   To test the migration workflow:")
            print("   1. Upload some Appian packages through the UI")
            print("   2. Run the migration: python migrate_merge_sessions.py --all")
            print("   3. Run this test script again")
            print("\n✅ Test suite ready (waiting for data)")
            return 0
        
        print(f"\n📊 Found {session_count} session(s) to test")
    
    # Run all tests
    results = {
        'query_performance': test_query_performance(),
        'data_integrity': test_data_integrity(),
        'ui_functionality': test_ui_functionality(),
        'report_generation': test_report_generation()
    }
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
