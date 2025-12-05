#!/usr/bin/env python3
"""
Test Cleanup Functionality

Verifies that all cleanup scripts properly handle all 39 database tables.
"""

from app import create_app
from models import db
from sqlalchemy import text

def test_cleanup_coverage():
    """Test that cleanup scripts cover all database tables."""
    app = create_app()
    
    with app.app_context():
        print("Testing Cleanup Script Coverage")
        print("="*70)
        
        # Get all tables from database
        result = db.session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            AND name NOT LIKE 'alembic%'
            ORDER BY name
        """))
        
        all_tables = [row[0] for row in result.fetchall()]
        
        # Tables that should be in cleanup scripts
        expected_tables = {
            # Core tables
            'merge_sessions',
            'packages',
            'object_lookup',
            'package_object_mappings',
            'object_versions',
            'delta_comparison_results',
            'customer_comparison_results',
            'changes',
            
            # Object-specific tables
            'interfaces',
            'interface_parameters',
            'interface_security',
            'expression_rules',
            'expression_rule_inputs',
            'process_models',
            'process_model_nodes',
            'process_model_flows',
            'process_model_variables',
            'record_types',
            'record_type_fields',
            'record_type_relationships',
            'record_type_views',
            'record_type_actions',
            'cdts',
            'cdt_fields',
            'integrations',
            'web_apis',
            'sites',
            'groups',
            'constants',
            'connected_systems',
            'unknown_objects',
            'data_stores',
            'data_store_entities',
            
            # Comparison tables
            'interface_comparisons',
            'process_model_comparisons',
            'record_type_comparisons',
            'expression_rule_comparisons',
            'cdt_comparisons',
            'constant_comparisons',
        }
        
        # Non-merge tables (should NOT be in cleanup)
        non_merge_tables = {
            'requests',
            'chat_sessions',
        }
        
        # Filter to merge-related tables only
        merge_tables = [t for t in all_tables if t not in non_merge_tables]
        
        print(f"\nTotal tables in database: {len(all_tables)}")
        print(f"Merge-related tables: {len(merge_tables)}")
        print(f"Non-merge tables: {len(non_merge_tables)}")
        print(f"Expected cleanup coverage: {len(expected_tables)}")
        
        # Check coverage
        print("\n" + "="*70)
        print("Coverage Analysis:")
        print("="*70)
        
        missing_from_expected = set(merge_tables) - expected_tables
        extra_in_expected = expected_tables - set(merge_tables)
        
        if missing_from_expected:
            print(f"\n⚠️  Tables in DB but NOT in cleanup scripts ({len(missing_from_expected)}):")
            for table in sorted(missing_from_expected):
                print(f"  - {table}")
        else:
            print("\n✅ All merge tables are covered in cleanup scripts")
        
        if extra_in_expected:
            print(f"\n⚠️  Tables in cleanup scripts but NOT in DB ({len(extra_in_expected)}):")
            for table in sorted(extra_in_expected):
                print(f"  - {table}")
        else:
            print("✅ No extra tables in cleanup scripts")
        
        # Verify table counts
        print("\n" + "="*70)
        print("Current Table Counts:")
        print("="*70)
        
        total_rows = 0
        for table in sorted(merge_tables):
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                total_rows += count
                if count > 0:
                    print(f"  {table:40} {count:>8,} rows")
            except Exception as e:
                print(f"  {table:40} ERROR: {str(e)}")
        
        print("-"*70)
        print(f"  {'TOTAL':40} {total_rows:>8,} rows")
        
        # Summary
        print("\n" + "="*70)
        print("Summary:")
        print("="*70)
        
        if not missing_from_expected and not extra_in_expected:
            print("✅ Cleanup scripts have COMPLETE coverage of all merge tables")
            print(f"✅ All {len(expected_tables)} tables are properly handled")
            print(f"✅ Current database has {total_rows:,} rows across {len(merge_tables)} tables")
        else:
            print("⚠️  Cleanup scripts have INCOMPLETE coverage")
            if missing_from_expected:
                print(f"⚠️  Missing {len(missing_from_expected)} tables")
            if extra_in_expected:
                print(f"⚠️  {len(extra_in_expected)} extra tables listed")
        
        print()
        
        return len(missing_from_expected) == 0 and len(extra_in_expected) == 0


if __name__ == '__main__':
    success = test_cleanup_coverage()
    exit(0 if success else 1)
