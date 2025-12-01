#!/usr/bin/env python
"""Check and create three-way merge schema with unique constraint validation"""

from app import create_app
from models import db
from sqlalchemy import text
import sys

def check_unique_constraints(table_name):
    """Check unique constraints on a table."""
    result = db.session.execute(text(f"PRAGMA index_list({table_name})"))
    indexes = list(result.fetchall())
    
    unique_constraints = []
    for idx in indexes:
        idx_name = idx[1]
        is_unique = idx[2]  # 1 if unique, 0 if not
        
        if is_unique:
            # Get columns in this index
            result = db.session.execute(text(f"PRAGMA index_info({idx_name})"))
            columns = [row[2] for row in result.fetchall()]
            unique_constraints.append({
                'name': idx_name,
                'columns': columns
            })
    
    return unique_constraints

def main():
    app = create_app()
    
    with app.app_context():
        print("="*60)
        print("THREE-WAY MERGE SCHEMA VALIDATION")
        print("="*60)
        
        # Get list of existing tables
        result = db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        )
        existing_tables = [row[0] for row in result.fetchall()]
        
        print(f"\nTotal tables: {len(existing_tables)}")
        
        # Check if three-way merge tables exist
        required_tables = [
            'merge_sessions',
            'packages',
            'object_lookup',
            'package_object_mappings',
            'delta_comparison_results',
            'changes',
            'object_versions'
        ]
        
        missing_tables = [t for t in required_tables if t not in existing_tables]
        
        if missing_tables:
            print(f"\n❌ Missing tables: {missing_tables}")
            print("\nCreating all tables...")
            db.create_all()
            print("✅ Tables created successfully!")
            
            # Verify
            result = db.session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            )
            existing_tables = [row[0] for row in result.fetchall()]
            print(f"\nTotal tables now: {len(existing_tables)}")
        else:
            print("\n✅ All required tables exist!")
        
        # Validate unique constraints on object-specific tables (Requirement 7.2)
        print("\n" + "="*60)
        print("UNIQUE CONSTRAINT VALIDATION")
        print("="*60)
        
        object_tables = [
            'interfaces', 'expression_rules', 'process_models', 'record_types',
            'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
            'connected_systems', 'data_stores', 'unknown_objects'
        ]
        
        validation_passed = True
        
        for table in object_tables:
            if table not in existing_tables:
                print(f"\n❌ {table}: TABLE NOT FOUND")
                validation_passed = False
                continue
            
            print(f"\n{table}:")
            
            # Check for unique constraint on (object_id, package_id)
            constraints = check_unique_constraints(table)
            
            # Look for constraint with both object_id and package_id
            object_package_constraint = None
            for constraint in constraints:
                if 'object_id' in constraint['columns'] and 'package_id' in constraint['columns']:
                    object_package_constraint = constraint
                    break
            
            if object_package_constraint:
                print(f"  ✅ Unique constraint found: {object_package_constraint['name']}")
                print(f"     Columns: {', '.join(object_package_constraint['columns'])}")
                
                # Check naming convention (Requirement 3.2)
                expected_name = f"uq_{table}_object_package"
                if object_package_constraint['name'] == expected_name:
                    print(f"  ✅ Constraint name follows convention: {expected_name}")
                else:
                    print(f"  ⚠️  Constraint name '{object_package_constraint['name']}' doesn't match convention '{expected_name}'")
            else:
                print(f"  ❌ No unique constraint on (object_id, package_id)")
                validation_passed = False
            
            # List all unique constraints for reference
            if len(constraints) > 1:
                print(f"  ℹ️  Other unique constraints:")
                for constraint in constraints:
                    if constraint != object_package_constraint:
                        print(f"     - {constraint['name']}: {', '.join(constraint['columns'])}")
        
        # Check data integrity (Requirements 7.3, 7.4, 7.5)
        print("\n" + "="*60)
        print("DATA INTEGRITY VALIDATION")
        print("="*60)
        
        # Check if there's any data to validate
        result = db.session.execute(text("SELECT COUNT(*) FROM packages"))
        package_count = result.scalar()
        
        if package_count == 0:
            print("\nℹ️  No packages found - skipping data integrity checks")
        else:
            print(f"\nFound {package_count} packages")
            
            # Requirement 7.3: All package_id values reference valid packages
            print("\nValidating foreign key integrity (package_id -> packages):")
            for table in object_tables:
                if table not in existing_tables:
                    continue
                
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
                    validation_passed = False
                else:
                    result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    total = result.scalar()
                    if total > 0:
                        print(f"  ✅ {table}: All {total} rows have valid package_id")
            
            # Requirement 7.4: Package-object mappings consistency
            print("\nValidating package-object mappings consistency:")
            for table in object_tables:
                if table not in existing_tables:
                    continue
                
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
                missing_mappings = result.scalar()
                
                if missing_mappings > 0:
                    print(f"  ⚠️  {table}: {missing_mappings} rows missing package_object_mappings")
                    validation_passed = False
                else:
                    result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    total = result.scalar()
                    if total > 0:
                        print(f"  ✅ {table}: All {total} rows have corresponding mappings")
            
            # Requirement 7.5: Count objects per package
            print("\nObjects per package distribution:")
            result = db.session.execute(text("""
                SELECT p.package_type, COUNT(DISTINCT pom.object_id) as object_count
                FROM packages p
                LEFT JOIN package_object_mappings pom ON pom.package_id = p.id
                GROUP BY p.package_type
                ORDER BY p.package_type
            """))
            
            for row in result.fetchall():
                print(f"  {row[0]}: {row[1]} objects")
        
        # Final summary
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        if validation_passed:
            print("✅ All validations PASSED")
            return 0
        else:
            print("❌ Some validations FAILED - see details above")
            return 1

if __name__ == '__main__':
    sys.exit(main())
