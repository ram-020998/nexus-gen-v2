"""Clean all merge-related data from database."""

from app import create_app
from models import db
from sqlalchemy import text

def clean_all():
    app = create_app()
    
    with app.app_context():
        print("Cleaning all merge-related data...")
        print("="*70)
        
        # Delete all data from merge tables in correct order (deepest dependencies first)
        tables = [
            # Comparison detail tables (deepest level)
            'constant_comparisons',
            'cdt_comparisons',
            'expression_rule_comparisons',
            'record_type_comparisons',
            'process_model_comparisons',
            'interface_comparisons',
            
            # Object detail tables (child tables)
            'data_store_entities',
            'cdt_fields',
            'record_type_actions',
            'record_type_views',
            'record_type_relationships',
            'record_type_fields',
            'process_model_variables',
            'process_model_flows',
            'process_model_nodes',
            'expression_rule_inputs',
            'interface_security',
            'interface_parameters',
            
            # Object-specific tables (parent tables)
            'data_stores',
            'unknown_objects',
            'connected_systems',
            'constants',
            'groups',
            'sites',
            'web_apis',
            'integrations',
            'cdts',
            'record_types',
            'process_models',
            'expression_rules',
            'interfaces',
            
            # Core comparison and change tables
            'changes',
            'customer_comparison_results',
            'delta_comparison_results',
            
            # Package-related tables
            'object_versions',
            'package_object_mappings',
            'packages',
            
            # Session table
            'merge_sessions',
            
            # Global object registry
            'object_lookup',
        ]
        
        total_deleted = 0
        
        for table in tables:
            try:
                result = db.session.execute(text(f"DELETE FROM {table}"))
                count = result.rowcount
                if count > 0:
                    print(f"  ✓ Deleted {count:,} rows from {table}")
                    total_deleted += count
            except Exception as e:
                print(f"  ⚠️  Error deleting from {table}: {str(e)}")
        
        db.session.commit()
        
        print("="*70)
        print(f"\n✅ Successfully deleted {total_deleted:,} total rows")
        print("\nDatabase is now empty and ready for a fresh merge session.")

if __name__ == '__main__':
    clean_all()
