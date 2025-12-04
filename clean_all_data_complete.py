#!/usr/bin/env python3
"""
Complete Database Cleanup Script

Removes ALL merge-related data from the database, including all object-specific
tables and comparison tables that were missing from the original script.

This script deletes data in the correct order to avoid foreign key violations.
"""

from app import create_app
from models import db
from sqlalchemy import text

def clean_all(dry_run=False, session_id=None):
    """
    Clean all merge-related data from database.
    
    Args:
        dry_run: If True, only show what would be deleted without actually deleting
        session_id: If provided, only delete data for this specific session
    """
    app = create_app()
    
    with app.app_context():
        if dry_run:
            print("🔍 DRY RUN MODE - No data will be deleted\n")
        
        if session_id:
            print(f"Cleaning data for session: {session_id}\n")
        else:
            print("Cleaning ALL merge-related data...\n")
        
        # Define tables in deletion order (deepest dependencies first)
        # This ensures no foreign key violations
        tables_to_clean = [
            # Comparison detail tables (deepest level)
            ('constant_comparisons', 'Constant comparison results'),
            ('cdt_comparisons', 'CDT comparison results'),
            ('expression_rule_comparisons', 'Expression rule comparison results'),
            ('record_type_comparisons', 'Record type comparison results'),
            ('process_model_comparisons', 'Process model comparison results'),
            ('interface_comparisons', 'Interface comparison results'),
            
            # Object detail tables (child tables)
            ('data_store_entities', 'Data store entities'),
            ('cdt_fields', 'CDT fields'),
            ('record_type_actions', 'Record type actions'),
            ('record_type_views', 'Record type views'),
            ('record_type_relationships', 'Record type relationships'),
            ('record_type_fields', 'Record type fields'),
            ('process_model_variables', 'Process model variables'),
            ('process_model_flows', 'Process model flows'),
            ('process_model_nodes', 'Process model nodes'),
            ('expression_rule_inputs', 'Expression rule inputs'),
            ('interface_security', 'Interface security'),
            ('interface_parameters', 'Interface parameters'),
            
            # Object-specific tables (parent tables)
            ('data_stores', 'Data stores'),
            ('unknown_objects', 'Unknown objects'),
            ('connected_systems', 'Connected systems'),
            ('constants', 'Constants'),
            ('groups', 'Groups'),
            ('sites', 'Sites'),
            ('web_apis', 'Web APIs'),
            ('integrations', 'Integrations'),
            ('cdts', 'CDTs'),
            ('record_types', 'Record types'),
            ('process_models', 'Process models'),
            ('expression_rules', 'Expression rules'),
            ('interfaces', 'Interfaces'),
            
            # Core comparison and change tables
            ('changes', 'Changes'),
            ('customer_comparison_results', 'Customer comparison results'),
            ('delta_comparison_results', 'Delta comparison results'),
            
            # Package-related tables
            ('object_versions', 'Object versions'),
            ('package_object_mappings', 'Package-object mappings'),
            ('packages', 'Packages'),
            
            # Session table
            ('merge_sessions', 'Merge sessions'),
            
            # Global object registry (only if cleaning all)
            ('object_lookup', 'Object lookup (global registry)'),
        ]
        
        total_deleted = 0
        
        for table_name, description in tables_to_clean:
            try:
                # Build query based on whether we're cleaning a specific session
                if session_id and table_name != 'object_lookup':
                    # For session-specific cleanup, we need to handle different FK relationships
                    if table_name == 'merge_sessions':
                        query = f"DELETE FROM {table_name} WHERE reference_id = :session_id"
                        params = {'session_id': session_id}
                    elif table_name == 'packages':
                        query = f"""
                            DELETE FROM {table_name} 
                            WHERE session_id IN (
                                SELECT id FROM merge_sessions WHERE reference_id = :session_id
                            )
                        """
                        params = {'session_id': session_id}
                    elif table_name in ['changes', 'customer_comparison_results', 'delta_comparison_results']:
                        query = f"""
                            DELETE FROM {table_name} 
                            WHERE session_id IN (
                                SELECT id FROM merge_sessions WHERE reference_id = :session_id
                            )
                        """
                        params = {'session_id': session_id}
                    elif table_name in ['interface_comparisons', 'process_model_comparisons', 
                                       'record_type_comparisons', 'expression_rule_comparisons',
                                       'cdt_comparisons', 'constant_comparisons']:
                        query = f"""
                            DELETE FROM {table_name} 
                            WHERE change_id IN (
                                SELECT id FROM changes 
                                WHERE session_id IN (
                                    SELECT id FROM merge_sessions WHERE reference_id = :session_id
                                )
                            )
                        """
                        params = {'session_id': session_id}
                    else:
                        # Object-specific tables - delete by package_id
                        query = f"""
                            DELETE FROM {table_name} 
                            WHERE package_id IN (
                                SELECT id FROM packages 
                                WHERE session_id IN (
                                    SELECT id FROM merge_sessions WHERE reference_id = :session_id
                                )
                            )
                        """
                        params = {'session_id': session_id}
                    
                    if dry_run:
                        count_query = query.replace('DELETE FROM', 'SELECT COUNT(*) FROM')
                        result = db.session.execute(text(count_query), params)
                        count = result.scalar()
                    else:
                        result = db.session.execute(text(query), params)
                        count = result.rowcount
                else:
                    # Clean all data from table
                    if dry_run:
                        result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        count = result.scalar()
                    else:
                        result = db.session.execute(text(f"DELETE FROM {table_name}"))
                        count = result.rowcount
                
                if count > 0:
                    status = "Would delete" if dry_run else "Deleted"
                    print(f"  {'🔍' if dry_run else '✓'} {status} {count:,} rows from {table_name} ({description})")
                    total_deleted += count
                    
            except Exception as e:
                print(f"  ⚠️  Error processing {table_name}: {str(e)}")
        
        if not dry_run:
            db.session.commit()
            print(f"\n✅ Successfully deleted {total_deleted:,} total rows")
            print("\nDatabase is now clean and ready for fresh merge sessions.")
        else:
            print(f"\n🔍 Would delete {total_deleted:,} total rows")
            print("\nRun without --dry-run to actually delete the data.")
        
        # Show remaining data
        print("\n" + "="*60)
        print("Current Database State:")
        print("="*60)
        
        key_tables = [
            ('merge_sessions', 'Merge sessions'),
            ('packages', 'Packages'),
            ('object_lookup', 'Objects in lookup'),
            ('changes', 'Changes'),
            ('delta_comparison_results', 'Delta results'),
            ('customer_comparison_results', 'Customer results'),
        ]
        
        for table_name, description in key_tables:
            result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            print(f"  {description}: {count:,}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean merge-related data from database')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--session', type=str,
                       help='Only delete data for specific session (e.g., MRG_001)')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.session:
        print("⚠️  WARNING: This will delete ALL merge-related data!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
    
    clean_all(dry_run=args.dry_run, session_id=args.session)


if __name__ == '__main__':
    main()
