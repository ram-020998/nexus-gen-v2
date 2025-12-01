"""
Verification script for Migration 003 - Data Completeness
This script verifies all requirements from Task 1 are met.
"""

from app import create_app
from models import db
from sqlalchemy import text

def verify_migration():
    """Verify all aspects of migration 003"""
    app = create_app()
    with app.app_context():
        print("=" * 70)
        print("MIGRATION 003 VERIFICATION - Data Completeness")
        print("=" * 70)
        
        all_passed = True
        
        # 1. Verify data_stores table exists
        print("\n1. Checking data_stores table...")
        result = db.session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='data_stores'"
        ))
        if result.fetchone():
            print("   ✅ data_stores table exists")
            # Check columns
            result = db.session.execute(text("PRAGMA table_info(data_stores)"))
            columns = [row[1] for row in result.fetchall()]
            expected = ['id', 'object_id', 'uuid', 'name', 'version_uuid', 
                       'description', 'connection_reference', 'configuration', 'created_at']
            if all(col in columns for col in expected):
                print(f"   ✅ All expected columns present: {', '.join(expected)}")
            else:
                print(f"   ❌ Missing columns. Expected: {expected}, Got: {columns}")
                all_passed = False
        else:
            print("   ❌ data_stores table does not exist")
            all_passed = False
        
        # 2. Verify data_store_entities table exists
        print("\n2. Checking data_store_entities table...")
        result = db.session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='data_store_entities'"
        ))
        if result.fetchone():
            print("   ✅ data_store_entities table exists")
            result = db.session.execute(text("PRAGMA table_info(data_store_entities)"))
            columns = [row[1] for row in result.fetchall()]
            expected = ['id', 'data_store_id', 'cdt_uuid', 'table_name', 
                       'column_mappings', 'created_at']
            if all(col in columns for col in expected):
                print(f"   ✅ All expected columns present: {', '.join(expected)}")
            else:
                print(f"   ❌ Missing columns. Expected: {expected}, Got: {columns}")
                all_passed = False
        else:
            print("   ❌ data_store_entities table does not exist")
            all_passed = False
        
        # 3. Verify expression_rule_comparisons table
        print("\n3. Checking expression_rule_comparisons table...")
        result = db.session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='expression_rule_comparisons'"
        ))
        if result.fetchone():
            print("   ✅ expression_rule_comparisons table exists")
            result = db.session.execute(text("PRAGMA table_info(expression_rule_comparisons)"))
            columns = [row[1] for row in result.fetchall()]
            expected = ['id', 'session_id', 'object_id', 'input_changes', 
                       'return_type_change', 'logic_diff', 'created_at']
            if all(col in columns for col in expected):
                print(f"   ✅ All expected columns present")
            else:
                print(f"   ❌ Missing columns. Expected: {expected}, Got: {columns}")
                all_passed = False
        else:
            print("   ❌ expression_rule_comparisons table does not exist")
            all_passed = False
        
        # 4. Verify cdt_comparisons table
        print("\n4. Checking cdt_comparisons table...")
        result = db.session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='cdt_comparisons'"
        ))
        if result.fetchone():
            print("   ✅ cdt_comparisons table exists")
            result = db.session.execute(text("PRAGMA table_info(cdt_comparisons)"))
            columns = [row[1] for row in result.fetchall()]
            expected = ['id', 'session_id', 'object_id', 'field_changes', 
                       'namespace_change', 'created_at']
            if all(col in columns for col in expected):
                print(f"   ✅ All expected columns present")
            else:
                print(f"   ❌ Missing columns. Expected: {expected}, Got: {columns}")
                all_passed = False
        else:
            print("   ❌ cdt_comparisons table does not exist")
            all_passed = False
        
        # 5. Verify constant_comparisons table
        print("\n5. Checking constant_comparisons table...")
        result = db.session.execute(text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='constant_comparisons'"
        ))
        if result.fetchone():
            print("   ✅ constant_comparisons table exists")
            result = db.session.execute(text("PRAGMA table_info(constant_comparisons)"))
            columns = [row[1] for row in result.fetchall()]
            expected = ['id', 'session_id', 'object_id', 'base_value', 
                       'customer_value', 'new_vendor_value', 'type_change', 'created_at']
            if all(col in columns for col in expected):
                print(f"   ✅ All expected columns present")
            else:
                print(f"   ❌ Missing columns. Expected: {expected}, Got: {columns}")
                all_passed = False
        else:
            print("   ❌ constant_comparisons table does not exist")
            all_passed = False
        
        # 6. Verify changes table has vendor_object_id and customer_object_id
        print("\n6. Checking changes table modifications...")
        result = db.session.execute(text("PRAGMA table_info(changes)"))
        columns = [row[1] for row in result.fetchall()]
        
        if 'vendor_object_id' in columns:
            print("   ✅ vendor_object_id column exists")
        else:
            print("   ❌ vendor_object_id column missing")
            all_passed = False
        
        if 'customer_object_id' in columns:
            print("   ✅ customer_object_id column exists")
        else:
            print("   ❌ customer_object_id column missing")
            all_passed = False
        
        # 7. Verify data migration (object_id → vendor_object_id)
        print("\n7. Checking data migration...")
        result = db.session.execute(text(
            "SELECT COUNT(*) as total, COUNT(vendor_object_id) as with_vendor FROM changes"
        ))
        row = result.fetchone()
        total = row[0]
        with_vendor = row[1]
        
        if total == 0:
            print(f"   ℹ️  No existing change records to migrate (table is empty)")
        elif total == with_vendor:
            print(f"   ✅ All {total} change records have vendor_object_id populated")
        else:
            print(f"   ❌ Only {with_vendor}/{total} change records have vendor_object_id")
            all_passed = False
        
        # 8. Verify foreign key constraints (check indexes as proxy)
        print("\n8. Checking indexes for dual object tracking...")
        result = db.session.execute(text("PRAGMA index_list(changes)"))
        indexes = [row[1] for row in result.fetchall()]
        
        required_indexes = [
            'idx_change_vendor_object',
            'idx_change_customer_object',
            'idx_change_vendor_customer'
        ]
        
        for idx in required_indexes:
            if idx in indexes:
                print(f"   ✅ Index {idx} exists")
            else:
                print(f"   ❌ Index {idx} missing")
                all_passed = False
        
        # 9. Verify comparison table indexes
        print("\n9. Checking comparison table indexes...")
        comparison_tables = [
            ('expression_rule_comparisons', ['idx_ercomp_session', 'idx_ercomp_object']),
            ('cdt_comparisons', ['idx_cdtcomp_session', 'idx_cdtcomp_object']),
            ('constant_comparisons', ['idx_constcomp_session', 'idx_constcomp_object'])
        ]
        
        for table, expected_indexes in comparison_tables:
            result = db.session.execute(text(f"PRAGMA index_list({table})"))
            indexes = [row[1] for row in result.fetchall()]
            for idx in expected_indexes:
                if idx in indexes:
                    print(f"   ✅ {table}.{idx} exists")
                else:
                    print(f"   ❌ {table}.{idx} missing")
                    all_passed = False
        
        # 10. Verify data_stores indexes
        print("\n10. Checking data_stores table indexes...")
        result = db.session.execute(text("PRAGMA index_list(data_stores)"))
        indexes = [row[1] for row in result.fetchall()]
        
        required_indexes = ['idx_datastore_object', 'idx_datastore_uuid']
        for idx in required_indexes:
            if idx in indexes:
                print(f"   ✅ Index {idx} exists")
            else:
                print(f"   ❌ Index {idx} missing")
                all_passed = False
        
        # Summary
        print("\n" + "=" * 70)
        if all_passed:
            print("✅ ALL VERIFICATION CHECKS PASSED")
            print("Migration 003 is complete and correct!")
        else:
            print("❌ SOME VERIFICATION CHECKS FAILED")
            print("Please review the errors above.")
        print("=" * 70)
        
        return all_passed

if __name__ == '__main__':
    import sys
    success = verify_migration()
    sys.exit(0 if success else 1)
