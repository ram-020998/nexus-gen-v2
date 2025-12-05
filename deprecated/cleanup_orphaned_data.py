#!/usr/bin/env python3
"""
Cleanup Orphaned Data

Removes orphaned records across all tables when parent records don't exist.
"""

from app import create_app
from models import db
from sqlalchemy import text

def cleanup_orphaned_data():
    """Remove orphaned records from all tables."""
    app = create_app()
    
    with app.app_context():
        print("Starting orphaned data cleanup...")
        print("="*70)
        
        total_deleted = 0
        
        # Get valid IDs for reference
        valid_session_ids = db.session.execute(text("SELECT id FROM merge_sessions")).fetchall()
        valid_session_ids = {row[0] for row in valid_session_ids}
        print(f"Valid session IDs: {len(valid_session_ids)}")
        
        valid_package_ids = db.session.execute(text("SELECT id FROM packages")).fetchall()
        valid_package_ids = {row[0] for row in valid_package_ids}
        print(f"Valid package IDs: {len(valid_package_ids)}")
        
        valid_object_ids = db.session.execute(text("SELECT id FROM object_lookup")).fetchall()
        valid_object_ids = {row[0] for row in valid_object_ids}
        print(f"Valid object IDs: {len(valid_object_ids)}")
        
        print()
        
        # Define orphan checks (table, condition, description)
        orphan_checks = [
            # Session-based orphans
            ('packages', 
             'session_id NOT IN (SELECT id FROM merge_sessions)',
             'packages without sessions'),
            ('delta_comparison_results',
             'session_id NOT IN (SELECT id FROM merge_sessions)',
             'delta results without sessions'),
            ('customer_comparison_results',
             'session_id NOT IN (SELECT id FROM merge_sessions)',
             'customer results without sessions'),
            ('changes',
             'session_id NOT IN (SELECT id FROM merge_sessions)',
             'changes without sessions'),
            
            # Package-based orphans
            ('package_object_mappings',
             'package_id NOT IN (SELECT id FROM packages)',
             'mappings without packages'),
            ('object_versions',
             'package_id NOT IN (SELECT id FROM packages)',
             'versions without packages'),
            ('interfaces',
             'package_id NOT IN (SELECT id FROM packages)',
             'interfaces without packages'),
            ('expression_rules',
             'package_id NOT IN (SELECT id FROM packages)',
             'expression rules without packages'),
            ('process_models',
             'package_id NOT IN (SELECT id FROM packages)',
             'process models without packages'),
            ('record_types',
             'package_id NOT IN (SELECT id FROM packages)',
             'record types without packages'),
            ('cdts',
             'package_id NOT IN (SELECT id FROM packages)',
             'CDTs without packages'),
            ('integrations',
             'package_id NOT IN (SELECT id FROM packages)',
             'integrations without packages'),
            ('web_apis',
             'package_id NOT IN (SELECT id FROM packages)',
             'web APIs without packages'),
            ('sites',
             'package_id NOT IN (SELECT id FROM packages)',
             'sites without packages'),
            ('groups',
             'package_id NOT IN (SELECT id FROM packages)',
             'groups without packages'),
            ('constants',
             'package_id NOT IN (SELECT id FROM packages)',
             'constants without packages'),
            ('connected_systems',
             'package_id NOT IN (SELECT id FROM packages)',
             'connected systems without packages'),
            ('unknown_objects',
             'package_id NOT IN (SELECT id FROM packages)',
             'unknown objects without packages'),
            ('data_stores',
             'package_id NOT IN (SELECT id FROM packages)',
             'data stores without packages'),
            
            # Object-based orphans
            ('package_object_mappings',
             'object_id NOT IN (SELECT id FROM object_lookup)',
             'mappings without objects'),
            ('object_versions',
             'object_id NOT IN (SELECT id FROM object_lookup)',
             'versions without objects'),
            ('delta_comparison_results',
             'object_id NOT IN (SELECT id FROM object_lookup)',
             'delta results without objects'),
            ('customer_comparison_results',
             'object_id NOT IN (SELECT id FROM object_lookup)',
             'customer results without objects'),
            ('changes',
             'object_id NOT IN (SELECT id FROM object_lookup)',
             'changes without objects'),
            
            # Child table orphans
            ('interface_parameters',
             'interface_id NOT IN (SELECT id FROM interfaces)',
             'interface parameters without interfaces'),
            ('interface_security',
             'interface_id NOT IN (SELECT id FROM interfaces)',
             'interface security without interfaces'),
            ('expression_rule_inputs',
             'rule_id NOT IN (SELECT id FROM expression_rules)',
             'expression rule inputs without rules'),
            ('process_model_nodes',
             'process_model_id NOT IN (SELECT id FROM process_models)',
             'process model nodes without models'),
            ('process_model_flows',
             'process_model_id NOT IN (SELECT id FROM process_models)',
             'process model flows without models'),
            ('process_model_variables',
             'process_model_id NOT IN (SELECT id FROM process_models)',
             'process model variables without models'),
            ('record_type_fields',
             'record_type_id NOT IN (SELECT id FROM record_types)',
             'record type fields without types'),
            ('record_type_relationships',
             'record_type_id NOT IN (SELECT id FROM record_types)',
             'record type relationships without types'),
            ('record_type_views',
             'record_type_id NOT IN (SELECT id FROM record_types)',
             'record type views without types'),
            ('record_type_actions',
             'record_type_id NOT IN (SELECT id FROM record_types)',
             'record type actions without types'),
            ('cdt_fields',
             'cdt_id NOT IN (SELECT id FROM cdts)',
             'CDT fields without CDTs'),
            ('data_store_entities',
             'data_store_id NOT IN (SELECT id FROM data_stores)',
             'data store entities without stores'),
            
            # Comparison table orphans
            ('interface_comparisons',
             'change_id NOT IN (SELECT id FROM changes)',
             'interface comparisons without changes'),
            ('process_model_comparisons',
             'change_id NOT IN (SELECT id FROM changes)',
             'process model comparisons without changes'),
            ('record_type_comparisons',
             'change_id NOT IN (SELECT id FROM changes)',
             'record type comparisons without changes'),
        ]
        
        for table_name, condition, description in orphan_checks:
            try:
                # Check for orphaned records
                result = db.session.execute(text(f"""
                    SELECT COUNT(*) FROM {table_name} 
                    WHERE {condition}
                """))
                count = result.scalar()
                
                if count > 0:
                    print(f"  Found {count:,} {description}")
                    
                    # Delete orphaned records
                    db.session.execute(text(f"""
                        DELETE FROM {table_name} 
                        WHERE {condition}
                    """))
                    db.session.commit()
                    print(f"  ✓ Deleted {count:,} orphaned records from {table_name}")
                    total_deleted += count
                    
            except Exception as e:
                print(f"  ⚠️  Error checking {table_name}: {str(e)}")
        
        print("="*70)
        
        if total_deleted > 0:
            print(f"\n✅ Deleted {total_deleted:,} total orphaned records")
        else:
            print("\n✅ No orphaned data found - database is clean!")
        
        # Verification
        print("\n" + "="*70)
        print("Verification:")
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
    cleanup_orphaned_data()
