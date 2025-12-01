"""
Check for duplicate (object_id, package_id) combinations before migration.

This script identifies any duplicate combinations that would violate
the unique constraint we're trying to add.
"""

from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    print("=" * 80)
    print("CHECKING FOR DUPLICATE (object_id, package_id) COMBINATIONS")
    print("=" * 80)
    
    total_duplicates = 0
    
    for table in tables:
        print(f"\n{table}:")
        
        # Check if package_id column exists
        check_sql = text(f"PRAGMA table_info({table})")
        result = db.session.execute(check_sql)
        columns = [row[1] for row in result]
        
        if 'package_id' not in columns:
            print(f"  ℹ package_id column does not exist yet")
            continue
        
        # Find duplicates
        sql = text(f"""
            SELECT object_id, package_id, COUNT(*) as count
            FROM {table}
            WHERE package_id IS NOT NULL
            GROUP BY object_id, package_id
            HAVING count > 1
        """)
        
        result = db.session.execute(sql)
        duplicates = result.fetchall()
        
        if duplicates:
            print(f"  ❌ Found {len(duplicates)} duplicate combinations:")
            for dup in duplicates:
                obj_id, pkg_id, count = dup
                print(f"      object_id={obj_id}, package_id={pkg_id}, count={count}")
                
                # Show details of duplicates
                details_sql = text(f"""
                    SELECT id, uuid, name, version_uuid
                    FROM {table}
                    WHERE object_id = :obj_id AND package_id = :pkg_id
                """)
                details_result = db.session.execute(details_sql, {"obj_id": obj_id, "pkg_id": pkg_id})
                details = details_result.fetchall()
                
                for detail in details:
                    print(f"        id={detail[0]}, uuid={detail[1]}, name={detail[2]}, version_uuid={detail[3]}")
            
            total_duplicates += len(duplicates)
        else:
            # Count total entries
            count_sql = text(f"SELECT COUNT(*) FROM {table} WHERE package_id IS NOT NULL")
            count_result = db.session.execute(count_sql)
            total = count_result.scalar()
            print(f"  ✓ No duplicates ({total} entries)")
    
    print("\n" + "=" * 80)
    if total_duplicates > 0:
        print(f"❌ TOTAL DUPLICATES FOUND: {total_duplicates}")
        print("=" * 80)
        print("\nThese duplicates must be resolved before the migration can proceed.")
        print("Options:")
        print("  1. Delete duplicate entries (keep only one per object_id + package_id)")
        print("  2. Investigate why duplicates exist (data integrity issue)")
    else:
        print("✅ NO DUPLICATES FOUND - Migration can proceed")
        print("=" * 80)
