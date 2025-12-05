#!/usr/bin/env python3
"""
Verify Database Cleanup

Checks all tables to ensure cleanup was complete and identifies any orphaned data.
"""

from app import create_app
from models import db
from sqlalchemy import text

def verify_cleanup():
    """Verify database cleanup and check for orphaned data."""
    app = create_app()
    
    with app.app_context():
        print("="*70)
        print("DATABASE CLEANUP VERIFICATION")
        print("="*70)
        
        # All tables in the database
        all_tables = [
            # Core merge tables
            ('merge_sessions', 'Merge sessions'),
            ('packages', 'Packages'),
            ('object_lookup', 'Object lookup (global)'),
            
            # Mapping and version tables
            ('package_object_mappings', 'Package-object mappings'),
            ('object_versions', 'Object versions'),
            
            # Comparison result tables
            ('delta_comparison_results', 'Delta comparison results'),
            ('customer_comparison_results', 'Customer comparison results'),
            ('changes', 'Changes (working set)'),
            
            # Object-specific tables
            ('interfaces', 'Interfaces'),
            ('interface_parameters', 'Interface parameters'),
            ('interface_security', 'Interface security'),
            ('expression_rules', 'Expression rules'),
            ('expression_rule_inputs', 'Expression rule inputs'),
            ('process_models', 'Process models'),
            ('process_model_nodes', 'Process model nodes'),
            ('process_model_flows', 'Process model flows'),
            ('process_model_variables', 'Process model variables'),
            ('record_types', 'Record types'),
            ('record_type_fields', 'Record type fields'),
            ('record_type_relationships', 'Record type relationships'),
            ('record_type_views', 'Record type views'),
            ('record_type_actions', 'Record type actions'),
            ('cdts', 'CDTs'),
            ('cdt_fields', 'CDT fields'),
            ('integrations', 'Integrations'),
            ('web_apis', 'Web APIs'),
            ('sites', 'Sites'),
            ('groups', 'Groups'),
            ('constants', 'Constants'),
            ('connected_systems', 'Connected systems'),
            ('unknown_objects', 'Unknown objects'),
            ('data_stores', 'Data stores'),
            ('data_store_entities', 'Data store entities'),
            
            # Comparison detail tables
            ('interface_comparisons', 'Interface comparisons'),
            ('process_model_comparisons', 'Process model comparisons'),
            ('record_type_comparisons', 'Record type comparisons'),
            ('expression_rule_comparisons', 'Expression rule comparisons'),
            ('cdt_comparisons', 'CDT comparisons'),
            ('constant_comparisons', 'Constant comparisons'),
        ]
        
        print("\n📊 TABLE ROW COUNTS:")
        print("-" * 70)
        
        total_rows = 0
        non_empty_tables = []
        
        for table_name, description in all_tables:
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                total_rows += count
                
                if count > 0:
                    print(f"  ⚠️  {description:40} {count:>8,} rows")
                    non_empty_tables.append((table_name, description, count))
                else:
                    print(f"  ✓  {description:40} {count:>8} rows")
            except Exception as e:
                print(f"  ❌ {description:40} ERROR: {str(e)}")
        
        print("-" * 70)
        print(f"  TOTAL ROWS ACROSS ALL TABLES: {total_rows:,}")
        print()
        
        # Check for orphaned data
        print("\n🔍 ORPHANED DATA CHECK:")
        print("-" * 70)
        
        issues_found = False
        
        # Check for packages without sessions
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM packages p
            LEFT JOIN merge_sessions ms ON p.session_id = ms.id
            WHERE ms.id IS NULL
        """))
        orphaned_packages = result.scalar()
        if orphaned_packages > 0:
            print(f"  ⚠️  Found {orphaned_packages} packages without merge sessions")
            issues_found = True
        else:
            print(f"  ✓  No orphaned packages")
        
        # Check for delta results without sessions
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM delta_comparison_results dcr
            LEFT JOIN merge_sessions ms ON dcr.session_id = ms.id
            WHERE ms.id IS NULL
        """))
        orphaned_delta = result.scalar()
        if orphaned_delta > 0:
            print(f"  ⚠️  Found {orphaned_delta} delta results without merge sessions")
            issues_found = True
        else:
            print(f"  ✓  No orphaned delta comparison results")
        
        # Check for customer results without sessions
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM customer_comparison_results ccr
            LEFT JOIN merge_sessions ms ON ccr.session_id = ms.id
            WHERE ms.id IS NULL
        """))
        orphaned_customer = result.scalar()
        if orphaned_customer > 0:
            print(f"  ⚠️  Found {orphaned_customer} customer results without merge sessions")
            issues_found = True
        else:
            print(f"  ✓  No orphaned customer comparison results")
        
        # Check for changes without sessions
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM changes c
            LEFT JOIN merge_sessions ms ON c.session_id = ms.id
            WHERE ms.id IS NULL
        """))
        orphaned_changes = result.scalar()
        if orphaned_changes > 0:
            print(f"  ⚠️  Found {orphaned_changes} changes without merge sessions")
            issues_found = True
        else:
            print(f"  ✓  No orphaned changes")
        
        # Check for object versions without packages
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM object_versions ov
            LEFT JOIN packages p ON ov.package_id = p.id
            WHERE p.id IS NULL
        """))
        orphaned_versions = result.scalar()
        if orphaned_versions > 0:
            print(f"  ⚠️  Found {orphaned_versions} object versions without packages")
            issues_found = True
        else:
            print(f"  ✓  No orphaned object versions")
        
        # Check for package mappings without packages
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM package_object_mappings pom
            LEFT JOIN packages p ON pom.package_id = p.id
            WHERE p.id IS NULL
        """))
        orphaned_mappings = result.scalar()
        if orphaned_mappings > 0:
            print(f"  ⚠️  Found {orphaned_mappings} package mappings without packages")
            issues_found = True
        else:
            print(f"  ✓  No orphaned package mappings")
        
        # Check for duplicate objects in object_lookup
        result = db.session.execute(text("""
            SELECT uuid, COUNT(*) as count 
            FROM object_lookup 
            GROUP BY uuid 
            HAVING count > 1
        """))
        duplicates = result.fetchall()
        if duplicates:
            print(f"  ⚠️  Found {len(duplicates)} duplicate UUIDs in object_lookup:")
            for uuid, count in duplicates[:5]:  # Show first 5
                print(f"      - {uuid}: {count} occurrences")
            if len(duplicates) > 5:
                print(f"      ... and {len(duplicates) - 5} more")
            issues_found = True
        else:
            print(f"  ✓  No duplicate objects in object_lookup")
        
        print()
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY:")
        print("="*70)
        
        if total_rows == 0:
            print("✅ Database is completely clean - no merge data found")
        elif not issues_found:
            print(f"✅ Database has {total_rows:,} rows but no orphaned data detected")
            if non_empty_tables:
                print("\nNon-empty tables:")
                for table_name, description, count in non_empty_tables:
                    print(f"  - {description}: {count:,} rows")
        else:
            print("⚠️  Database has orphaned data that needs cleanup")
            print("\nRun cleanup_orphaned_data.py to fix orphaned records")
        
        print()


if __name__ == '__main__':
    verify_cleanup()
