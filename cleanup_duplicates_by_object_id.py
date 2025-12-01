"""
Clean up duplicate entries by object_id (regardless of package_id).

This script removes duplicate entries that have the same object_id,
keeping only the first occurrence. This is necessary before the migration
can populate package_id values.
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
    """Clean up duplicates in a single table by object_id"""
    print(f"\n{table_name}:")
    
    # Find all duplicates by object_id (ignoring package_id)
    sql = text(f"""
        SELECT object_id, COUNT(*) as count
        FROM {table_name}
        GROUP BY object_id
        HAVING count > 1
    """)
    
    result = db.session.execute(sql)
    duplicates = result.fetchall()
    
    if not duplicates:
        # Count total entries
        count_sql = text(f"SELECT COUNT(*) FROM {table_name}")
        count_result = db.session.execute(count_sql)
        total = count_result.scalar()
        print(f"  ✓ No duplicates ({total} entries)")
        return 0
    
    print(f"  Found {len(duplicates)} objects with duplicate entries")
    
    total_deleted = 0
    
    for dup in duplicates:
        obj_id, count = dup
        print(f"  Processing object_id={obj_id} ({count} entries)...")
        
        # Get all IDs for this object_id
        ids_sql = text(f"""
            SELECT id, uuid, name, version_uuid
            FROM {table_name}
            WHERE object_id = :obj_id
            ORDER BY id ASC
        """)
        
        ids_result = db.session.execute(ids_sql, {"obj_id": obj_id})
        entries = ids_result.fetchall()
        
        # Keep the first one, delete the rest
        keep_id = entries[0][0]
        print(f"    Keeping id={keep_id} (uuid={entries[0][1]}, name={entries[0][2]}, version={entries[0][3]})")
        
        for entry in entries[1:]:
            entry_id = entry[0]
            print(f"    Deleting id={entry_id} (uuid={entry[1]}, name={entry[2]}, version={entry[3]})")
            
            # Delete child records first if this table has children
            if table_name in CHILD_TABLES:
                for child_table in CHILD_TABLES[table_name]:
                    # Determine the correct foreign key column name
                    if child_table == 'interface_parameters' or child_table == 'interface_security':
                        parent_fk = 'interface_id'
                    elif child_table == 'expression_rule_inputs':
                        parent_fk = 'rule_id'  # Special case!
                    elif child_table.startswith('process_model_'):
                        parent_fk = 'process_model_id'
                    elif child_table.startswith('record_type_'):
                        parent_fk = 'record_type_id'
                    elif child_table == 'cdt_fields':
                        parent_fk = 'cdt_id'
                    elif child_table == 'data_store_entities':
                        parent_fk = 'data_store_id'
                    else:
                        parent_fk = f"{table_name[:-1]}_id"
                    
                    delete_child_sql = text(f"DELETE FROM {child_table} WHERE {parent_fk} = :id")
                    db.session.execute(delete_child_sql, {"id": entry_id})
            
            # Delete the parent record
            delete_sql = text(f"DELETE FROM {table_name} WHERE id = :id")
            db.session.execute(delete_sql, {"id": entry_id})
            
            total_deleted += 1
    
    return total_deleted


with app.app_context():
    print("=" * 80)
    print("CLEANING UP DUPLICATE ENTRIES BY object_id")
    print("=" * 80)
    print("\nThis removes duplicate entries with the same object_id,")
    print("keeping only one entry per object. This is necessary before")
    print("the migration can populate package_id values.")
    
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
                SELECT object_id, COUNT(*) as count
                FROM {table}
                GROUP BY object_id
                HAVING count > 1
            )
        """)
        
        result = db.session.execute(sql)
        count = result.scalar()
        
        if count > 0:
            print(f"  ❌ {table}: {count} objects with duplicates still remain!")
            remaining_duplicates += count
    
    if remaining_duplicates == 0:
        print("✓ No duplicates remain - migration can now proceed")
    else:
        print(f"❌ ERROR: {remaining_duplicates} objects with duplicates still remain!")
