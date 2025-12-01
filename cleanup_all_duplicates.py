"""
Clean up all duplicate (object_id, package_id) combinations across all tables.

This script removes duplicate entries from all object-specific tables,
keeping only the first occurrence of each (object_id, package_id) combination.
"""

from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

# Define child tables for each parent table
CHILD_TABLES = {
    'interfaces': ['interface_parameters', 'interface_security'],
    'expression_rules': ['expression_rule_inputs'],
    'process_models': ['process_model_nodes', 'process_model_flows', 'process_model_variables'],
    'record_types': ['record_type_fields', 'record_type_relationships', 'record_type_views', 'record_type_actions'],
    'cdts': ['cdt_fields'],
    'data_stores': ['data_store_entities']
}

def cleanup_table(table_name):
    """Clean up duplicates in a single table"""
    print(f"\n{table_name}:")
    
    # Find all duplicates
    sql = text(f"""
        SELECT object_id, package_id, COUNT(*) as count
        FROM {table_name}
        WHERE package_id IS NOT NULL
        GROUP BY object_id, package_id
        HAVING count > 1
    """)
    
    result = db.session.execute(sql)
    duplicates = result.fetchall()
    
    if not duplicates:
        # Count total entries
        count_sql = text(f"SELECT COUNT(*) FROM {table_name} WHERE package_id IS NOT NULL")
        count_result = db.session.execute(count_sql)
        total = count_result.scalar()
        print(f"  ✓ No duplicates ({total} entries)")
        return 0
    
    print(f"  Found {len(duplicates)} duplicate combinations")
    
    total_deleted = 0
    
    for dup in duplicates:
        obj_id, pkg_id, count = dup
        print(f"  Processing object_id={obj_id}, package_id={pkg_id} ({count} entries)...")
        
        # Get all IDs for this combination
        ids_sql = text(f"""
            SELECT id, uuid, name
            FROM {table_name}
            WHERE object_id = :obj_id AND package_id = :pkg_id
            ORDER BY id ASC
        """)
        
        ids_result = db.session.execute(ids_sql, {"obj_id": obj_id, "pkg_id": pkg_id})
        entries = ids_result.fetchall()
        
        # Keep the first one, delete the rest
        keep_id = entries[0][0]
        print(f"    Keeping id={keep_id} (uuid={entries[0][1]}, name={entries[0][2]})")
        
        for entry in entries[1:]:
            entry_id = entry[0]
            print(f"    Deleting id={entry_id} (uuid={entry[1]}, name={entry[2]})")
            
            # Delete child records first if this table has children
            if table_name in CHILD_TABLES:
                for child_table in CHILD_TABLES[table_name]:
                    parent_fk = f"{table_name[:-1]}_id"  # Remove 's' and add '_id'
                    if table_name == 'cdts':
                        parent_fk = 'cdt_id'
                    elif table_name == 'data_stores':
                        parent_fk = 'data_store_id'
                    
                    delete_child_sql = text(f"DELETE FROM {child_table} WHERE {parent_fk} = :id")
                    db.session.execute(delete_child_sql, {"id": entry_id})
            
            # Delete the parent record
            delete_sql = text(f"DELETE FROM {table_name} WHERE id = :id")
            db.session.execute(delete_sql, {"id": entry_id})
            
            total_deleted += 1
    
    return total_deleted


with app.app_context():
    print("=" * 80)
    print("CLEANING UP ALL DUPLICATE (object_id, package_id) COMBINATIONS")
    print("=" * 80)
    
    tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    total_deleted = 0
    
    for table in tables:
        deleted = cleanup_table(table)
        total_deleted += deleted
    
    # Commit all changes
    db.session.commit()
    
    print("\n" + "=" * 80)
    print(f"✅ CLEANUP COMPLETE")
    print(f"   Deleted {total_deleted} duplicate entries across all tables")
    print("=" * 80)
    
    # Verify no duplicates remain
    print("\nVerifying cleanup...")
    remaining_duplicates = 0
    
    for table in tables:
        sql = text(f"""
            SELECT COUNT(*)
            FROM (
                SELECT object_id, package_id, COUNT(*) as count
                FROM {table}
                WHERE package_id IS NOT NULL
                GROUP BY object_id, package_id
                HAVING count > 1
            )
        """)
        
        result = db.session.execute(sql)
        count = result.scalar()
        
        if count > 0:
            print(f"  ❌ {table}: {count} duplicates still remain!")
            remaining_duplicates += count
    
    if remaining_duplicates == 0:
        print("✓ No duplicates remain - migration can now proceed")
    else:
        print(f"❌ ERROR: {remaining_duplicates} duplicates still remain!")
