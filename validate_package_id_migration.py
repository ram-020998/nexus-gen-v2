#!/usr/bin/env python
"""
Comprehensive validation script for package_id migration.
Validates all requirements from 7.1 through 7.5.
"""

from app import create_app
from models import db
from sqlalchemy import text
import sys

def validate_no_null_package_ids():
    """
    Requirement 7.1: Verify that all object-specific entries have non-NULL package_id values.
    """
    print("\n" + "="*60)
    print("REQUIREMENT 7.1: No NULL package_id values")
    print("="*60)
    
    object_tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    all_passed = True
    total_rows = 0
    
    for table in object_tables:
        result = db.session.execute(text(f"SELECT COUNT(*) FROM {table} WHERE package_id IS NULL"))
        null_count = result.scalar()
        
        result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        table_count = result.scalar()
        total_rows += table_count
        
        if null_count > 0:
            print(f"  ❌ {table}: {null_count} NULL values out of {table_count} rows")
            all_passed = False
        elif table_count > 0:
            print(f"  ✅ {table}: All {table_count} rows have package_id")
        else:
            print(f"  ℹ️  {table}: Empty table")
    
    print(f"\nTotal rows checked: {total_rows}")
    return all_passed

def validate_no_duplicates():
    """
    Requirement 7.2: Verify that no duplicate (object_id, package_id) combinations exist.
    """
    print("\n" + "="*60)
    print("REQUIREMENT 7.2: No duplicate (object_id, package_id) combinations")
    print("="*60)
    
    object_tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    all_passed = True
    
    for table in object_tables:
        result = db.session.execute(text(f"""
            SELECT object_id, package_id, COUNT(*) as count
            FROM {table}
            GROUP BY object_id, package_id
            HAVING count > 1
        """))
        duplicates = result.fetchall()
        
        if duplicates:
            print(f"  ❌ {table}: {len(duplicates)} duplicate combinations found")
            for dup in duplicates[:5]:  # Show first 5
                print(f"     object_id={dup[0]}, package_id={dup[1]}, count={dup[2]}")
            if len(duplicates) > 5:
                print(f"     ... and {len(duplicates) - 5} more")
            all_passed = False
        else:
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            if count > 0:
                print(f"  ✅ {table}: No duplicates ({count} unique combinations)")
            else:
                print(f"  ℹ️  {table}: Empty table")
    
    return all_passed

def validate_referential_integrity():
    """
    Requirement 7.3: Verify that all package_id values reference valid packages.
    """
    print("\n" + "="*60)
    print("REQUIREMENT 7.3: All package_id values reference valid packages")
    print("="*60)
    
    object_tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    all_passed = True
    
    # First check if packages table has data
    result = db.session.execute(text("SELECT COUNT(*) FROM packages"))
    package_count = result.scalar()
    
    if package_count == 0:
        print("  ℹ️  No packages found - skipping validation")
        return True
    
    print(f"  Found {package_count} packages in database")
    
    for table in object_tables:
        result = db.session.execute(text(f"""
            SELECT COUNT(*)
            FROM {table} t
            WHERE NOT EXISTS (
                SELECT 1 FROM packages p WHERE p.id = t.package_id
            )
        """))
        invalid_count = result.scalar()
        
        if invalid_count > 0:
            print(f"  ❌ {table}: {invalid_count} rows with invalid package_id")
            
            # Show some examples
            result = db.session.execute(text(f"""
                SELECT t.id, t.object_id, t.package_id
                FROM {table} t
                WHERE NOT EXISTS (
                    SELECT 1 FROM packages p WHERE p.id = t.package_id
                )
                LIMIT 5
            """))
            examples = result.fetchall()
            for ex in examples:
                print(f"     id={ex[0]}, object_id={ex[1]}, package_id={ex[2]}")
            
            all_passed = False
        else:
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            if count > 0:
                print(f"  ✅ {table}: All {count} rows reference valid packages")
    
    return all_passed

def validate_mapping_consistency():
    """
    Requirement 7.4: Verify that package_object_mappings entries exist for all 
    (object_id, package_id) combinations in object-specific tables.
    """
    print("\n" + "="*60)
    print("REQUIREMENT 7.4: Package-object mappings consistency")
    print("="*60)
    
    object_tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    all_passed = True
    
    for table in object_tables:
        result = db.session.execute(text(f"""
            SELECT COUNT(*)
            FROM {table} t
            WHERE NOT EXISTS (
                SELECT 1
                FROM package_object_mappings pom
                WHERE pom.object_id = t.object_id
                AND pom.package_id = t.package_id
            )
        """))
        missing_count = result.scalar()
        
        if missing_count > 0:
            print(f"  ❌ {table}: {missing_count} rows missing package_object_mappings")
            
            # Show some examples
            result = db.session.execute(text(f"""
                SELECT t.id, t.object_id, t.package_id
                FROM {table} t
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM package_object_mappings pom
                    WHERE pom.object_id = t.object_id
                    AND pom.package_id = t.package_id
                )
                LIMIT 5
            """))
            examples = result.fetchall()
            for ex in examples:
                print(f"     id={ex[0]}, object_id={ex[1]}, package_id={ex[2]}")
            
            all_passed = False
        else:
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            if count > 0:
                print(f"  ✅ {table}: All {count} rows have corresponding mappings")
    
    return all_passed

def validate_distribution():
    """
    Requirement 7.5: Count objects per package and verify the distribution is reasonable.
    """
    print("\n" + "="*60)
    print("REQUIREMENT 7.5: Objects per package distribution")
    print("="*60)
    
    # Check if there's any data
    result = db.session.execute(text("SELECT COUNT(*) FROM packages"))
    package_count = result.scalar()
    
    if package_count == 0:
        print("  ℹ️  No packages found - skipping distribution check")
        return True
    
    # Get distribution by package type
    result = db.session.execute(text("""
        SELECT 
            p.id,
            p.package_type,
            p.filename,
            COUNT(DISTINCT pom.object_id) as object_count
        FROM packages p
        LEFT JOIN package_object_mappings pom ON pom.package_id = p.id
        GROUP BY p.id, p.package_type, p.filename
        ORDER BY p.package_type
    """))
    
    distributions = result.fetchall()
    
    print("\nPackage distribution:")
    for dist in distributions:
        print(f"  {dist[1]}: {dist[3]} objects (package_id={dist[0]}, file={dist[2]})")
    
    # Get distribution by object type
    print("\nObject type distribution:")
    
    object_tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    for table in object_tables:
        result = db.session.execute(text(f"""
            SELECT COUNT(*) FROM {table}
        """))
        count = result.scalar()
        
        if count > 0:
            # Get breakdown by package
            result = db.session.execute(text(f"""
                SELECT p.package_type, COUNT(*) as count
                FROM {table} t
                JOIN packages p ON p.id = t.package_id
                GROUP BY p.package_type
                ORDER BY p.package_type
            """))
            breakdown = result.fetchall()
            breakdown_str = ", ".join([f"{b[0]}={b[1]}" for b in breakdown])
            print(f"  {table}: {count} total ({breakdown_str})")
    
    # Check for reasonable distribution (all packages should have some objects)
    result = db.session.execute(text("""
        SELECT COUNT(*)
        FROM packages p
        WHERE NOT EXISTS (
            SELECT 1 FROM package_object_mappings pom WHERE pom.package_id = p.id
        )
    """))
    empty_packages = result.scalar()
    
    if empty_packages > 0:
        print(f"\n  ⚠️  WARNING: {empty_packages} packages have no objects")
        return False
    else:
        print(f"\n  ✅ All packages have objects")
        return True

def main():
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("PACKAGE_ID MIGRATION DATA INTEGRITY VALIDATION")
        print("="*60)
        
        # Run all validations
        results = {
            '7.1 No NULL package_id values': validate_no_null_package_ids(),
            '7.2 No duplicate combinations': validate_no_duplicates(),
            '7.3 Referential integrity': validate_referential_integrity(),
            '7.4 Mapping consistency': validate_mapping_consistency(),
            '7.5 Distribution check': validate_distribution()
        }
        
        # Summary
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        all_passed = True
        for requirement, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {requirement}: {status}")
            if not passed:
                all_passed = False
        
        print("\n" + "="*60)
        if all_passed:
            print("✅ ALL VALIDATIONS PASSED")
            return 0
        else:
            print("❌ SOME VALIDATIONS FAILED")
            return 1

if __name__ == '__main__':
    sys.exit(main())
