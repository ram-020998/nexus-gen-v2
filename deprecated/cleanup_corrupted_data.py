"""
Cleanup corrupted data from failed merge sessions.

This script removes records with NULL foreign keys across all tables.
"""

from app import create_app
from models import db
from sqlalchemy import text

def cleanup_corrupted_data():
    """Remove corrupted data from database."""
    app = create_app()
    
    with app.app_context():
        print("Starting database cleanup for corrupted data...")
        print("="*70)
        
        total_deleted = 0
        
        # Define tables and their NULL checks
        corruption_checks = [
            # Core tables
            ('customer_comparison_results', 'session_id IS NULL OR object_id IS NULL'),
            ('delta_comparison_results', 'session_id IS NULL OR object_id IS NULL'),
            ('changes', 'session_id IS NULL OR object_id IS NULL'),
            ('packages', 'session_id IS NULL'),
            ('package_object_mappings', 'package_id IS NULL OR object_id IS NULL'),
            ('object_versions', 'object_id IS NULL OR package_id IS NULL'),
            
            # Object-specific tables
            ('interfaces', 'object_id IS NULL OR package_id IS NULL'),
            ('interface_parameters', 'interface_id IS NULL'),
            ('interface_security', 'interface_id IS NULL'),
            ('expression_rules', 'object_id IS NULL OR package_id IS NULL'),
            ('expression_rule_inputs', 'rule_id IS NULL'),
            ('process_models', 'object_id IS NULL OR package_id IS NULL'),
            ('process_model_nodes', 'process_model_id IS NULL'),
            ('process_model_flows', 'process_model_id IS NULL OR from_node_id IS NULL OR to_node_id IS NULL'),
            ('process_model_variables', 'process_model_id IS NULL'),
            ('record_types', 'object_id IS NULL OR package_id IS NULL'),
            ('record_type_fields', 'record_type_id IS NULL'),
            ('record_type_relationships', 'record_type_id IS NULL'),
            ('record_type_views', 'record_type_id IS NULL'),
            ('record_type_actions', 'record_type_id IS NULL'),
            ('cdts', 'object_id IS NULL OR package_id IS NULL'),
            ('cdt_fields', 'cdt_id IS NULL'),
            ('integrations', 'object_id IS NULL OR package_id IS NULL'),
            ('web_apis', 'object_id IS NULL OR package_id IS NULL'),
            ('sites', 'object_id IS NULL OR package_id IS NULL'),
            ('groups', 'object_id IS NULL OR package_id IS NULL'),
            ('constants', 'object_id IS NULL OR package_id IS NULL'),
            ('connected_systems', 'object_id IS NULL OR package_id IS NULL'),
            ('unknown_objects', 'object_id IS NULL OR package_id IS NULL'),
            ('data_stores', 'object_id IS NULL OR package_id IS NULL'),
            ('data_store_entities', 'data_store_id IS NULL'),
            
            # Comparison tables
            ('interface_comparisons', 'change_id IS NULL'),
            ('process_model_comparisons', 'change_id IS NULL'),
            ('record_type_comparisons', 'change_id IS NULL'),
            ('expression_rule_comparisons', 'session_id IS NULL OR object_id IS NULL'),
            ('cdt_comparisons', 'session_id IS NULL OR object_id IS NULL'),
            ('constant_comparisons', 'session_id IS NULL OR object_id IS NULL'),
        ]
        
        for table_name, condition in corruption_checks:
            try:
                # Check for corrupted records
                result = db.session.execute(text(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE {condition}
                """))
                count = result.scalar()
                
                if count > 0:
                    print(f"  Found {count:,} corrupted records in {table_name}")
                    
                    # Delete corrupted records
                    db.session.execute(text(f"""
                        DELETE FROM {table_name} 
                        WHERE {condition}
                    """))
                    db.session.commit()
                    print(f"  ✓ Deleted {count:,} corrupted records from {table_name}")
                    total_deleted += count
                    
            except Exception as e:
                print(f"  ⚠️  Error checking {table_name}: {str(e)}")
        
        print("="*70)
        
        if total_deleted > 0:
            print(f"\n✅ Deleted {total_deleted:,} total corrupted records")
        else:
            print("\n✅ No corrupted data found - database is clean!")
        
        # Show current state
        print("\n" + "="*70)
        print("Current Database State:")
        print("="*70)
        
        key_tables = [
            'merge_sessions',
            'packages',
            'object_lookup',
            'customer_comparison_results',
            'delta_comparison_results',
            'changes',
        ]
        
        for table in key_tables:
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            print(f"  {table}: {result.scalar():,}")

if __name__ == '__main__':
    cleanup_corrupted_data()
