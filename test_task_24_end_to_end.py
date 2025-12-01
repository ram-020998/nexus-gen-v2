#!/usr/bin/env python3
"""
Task 24: End-to-End Test Verification
Verify all aspects of the package_id migration after running the complete workflow.
"""

from app import create_app
from models import db
import sys


def verify_package_id_populated():
    """Verify all object-specific tables have package_id populated"""
    print("\n" + "=" * 80)
    print("VERIFICATION 1: All object-specific tables have package_id populated")
    print("=" * 80)
    
    object_tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    all_passed = True
    for table in object_tables:
        # Check for NULL package_id values
        result = db.session.execute(db.text(
            f"SELECT COUNT(*) FROM {table} WHERE package_id IS NULL"
        ))
        null_count = result.scalar()
        
        # Get total count
        result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}"))
        total_count = result.scalar()
        
        if null_count > 0:
            print(f"✗ {table}: {null_count} NULL package_ids out of {total_count} total")
            all_passed = False
        elif total_count > 0:
            print(f"✓ {table}: All {total_count} entries have package_id")
        else:
            print(f"  {table}: No entries (empty table)")
    
    return all_passed


def verify_no_duplicates():
    """Verify no duplicate (object_id, package_id) combinations"""
    print("\n" + "=" * 80)
    print("VERIFICATION 2: No duplicate (object_id, package_id) combinations")
    print("=" * 80)
    
    object_tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    all_passed = True
    for table in object_tables:
        result = db.session.execute(db.text(f"""
            SELECT object_id, package_id, COUNT(*) as count
            FROM {table}
            GROUP BY object_id, package_id
            HAVING count > 1
        """))
        duplicates = result.fetchall()
        
        if duplicates:
            print(f"✗ {table}: Found {len(duplicates)} duplicate combinations")
            for dup in duplicates[:3]:  # Show first 3
                print(f"    object_id={dup[0]}, package_id={dup[1]}, count={dup[2]}")
            all_passed = False
        else:
            result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}"))
            total = result.scalar()
            if total > 0:
                print(f"✓ {table}: No duplicates ({total} unique combinations)")
            else:
                print(f"  {table}: No entries")
    
    return all_passed


def verify_referential_integrity():
    """Verify all package_id values reference valid packages"""
    print("\n" + "=" * 80)
    print("VERIFICATION 3: All package_id values reference valid packages")
    print("=" * 80)
    
    object_tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    all_passed = True
    for table in object_tables:
        result = db.session.execute(db.text(f"""
            SELECT COUNT(*)
            FROM {table} t
            LEFT JOIN packages p ON t.package_id = p.id
            WHERE p.id IS NULL
        """))
        invalid_count = result.scalar()
        
        if invalid_count > 0:
            print(f"✗ {table}: {invalid_count} entries with invalid package_id")
            all_passed = False
        else:
            result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}"))
            total = result.scalar()
            if total > 0:
                print(f"✓ {table}: All {total} entries reference valid packages")
            else:
                print(f"  {table}: No entries")
    
    return all_passed


def verify_package_object_mappings():
    """Verify package_object_mappings consistency"""
    print("\n" + "=" * 80)
    print("VERIFICATION 4: Package-object mappings consistency")
    print("=" * 80)
    
    object_tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    all_passed = True
    total_checked = 0
    total_missing = 0
    
    for table in object_tables:
        result = db.session.execute(db.text(f"""
            SELECT COUNT(*)
            FROM {table} t
            LEFT JOIN package_object_mappings pom 
                ON t.object_id = pom.object_id 
                AND t.package_id = pom.package_id
            WHERE pom.id IS NULL
        """))
        missing_count = result.scalar()
        
        result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}"))
        total = result.scalar()
        
        total_checked += total
        total_missing += missing_count
        
        if missing_count > 0:
            print(f"✗ {table}: {missing_count}/{total} entries missing mappings")
            all_passed = False
        elif total > 0:
            print(f"✓ {table}: All {total} entries have mappings")
    
    print(f"\nTotal: {total_checked} entries checked, {total_missing} missing mappings")
    return all_passed


def verify_session_statistics():
    """Verify session statistics"""
    print("\n" + "=" * 80)
    print("VERIFICATION 5: Session Statistics")
    print("=" * 80)
    
    # Get latest session
    result = db.session.execute(db.text("""
        SELECT id, reference_id, status, total_changes
        FROM merge_sessions
        ORDER BY created_at DESC
        LIMIT 1
    """))
    session = result.fetchone()
    
    if not session:
        print("✗ No merge session found")
        return False
    
    print(f"Session ID: {session[1]}")
    print(f"Status: {session[2]}")
    print(f"Total Changes: {session[3]}")
    
    # Get package counts
    result = db.session.execute(db.text("""
        SELECT package_type, total_objects
        FROM packages
        WHERE session_id = :session_id
        ORDER BY 
            CASE package_type
                WHEN 'base' THEN 1
                WHEN 'customized' THEN 2
                WHEN 'new_vendor' THEN 3
            END
    """), {'session_id': session[0]})
    packages = result.fetchall()
    
    print(f"\nPackages:")
    for pkg in packages:
        print(f"  {pkg[0]}: {pkg[1]} objects")
    
    # Get object counts by table
    print(f"\nObject counts by table:")
    object_tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    for table in object_tables:
        result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table}"))
        count = result.scalar()
        if count > 0:
            print(f"  {table}: {count}")
    
    return True


def verify_unique_constraints():
    """Verify unique constraints exist"""
    print("\n" + "=" * 80)
    print("VERIFICATION 6: Unique Constraints")
    print("=" * 80)
    
    object_tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    all_passed = True
    for table in object_tables:
        # Check if unique constraint exists
        result = db.session.execute(db.text(f"""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='{table}'
        """))
        table_sql = result.scalar()
        
        if table_sql and 'UNIQUE' in table_sql and 'object_id' in table_sql and 'package_id' in table_sql:
            print(f"✓ {table}: Unique constraint exists")
        else:
            print(f"✗ {table}: Unique constraint missing or incorrect")
            all_passed = False
    
    return all_passed


def main():
    """Main entry point"""
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 80)
        print("TASK 24: END-TO-END TEST VERIFICATION")
        print("=" * 80)
        
        results = []
        
        # Run all verifications
        results.append(("Package ID Populated", verify_package_id_populated()))
        results.append(("No Duplicates", verify_no_duplicates()))
        results.append(("Referential Integrity", verify_referential_integrity()))
        results.append(("Package-Object Mappings", verify_package_object_mappings()))
        results.append(("Session Statistics", verify_session_statistics()))
        results.append(("Unique Constraints", verify_unique_constraints()))
        
        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        
        all_passed = True
        for name, passed in results:
            status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"{status}: {name}")
            if not passed:
                all_passed = False
        
        print("=" * 80)
        
        if all_passed:
            print("\n✓ ALL VERIFICATIONS PASSED!")
            print("The package_id migration is working correctly.")
            return 0
        else:
            print("\n✗ SOME VERIFICATIONS FAILED")
            print("Please review the failures above.")
            return 1


if __name__ == '__main__':
    sys.exit(main())
