"""
Migration Runner for Three-Way Merge Schema
"""
import sys
from app import create_app
from models import db

def run_migration():
    """Run the three-way merge schema migration"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("Running Three-Way Merge Schema Migration")
        print("=" * 70)
        
        # Import migration functions
        sys.path.insert(0, 'migrations')
        from migrations_001_three_way_merge_schema import upgrade
        
        try:
            # Run the migration
            upgrade()
            db.session.commit()
            
            print("\n" + "=" * 70)
            print("✅ Migration completed successfully!")
            print("=" * 70)
            
            # Run validation queries
            print("\nRunning validation queries...")
            validate_schema()
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            db.session.rollback()
            raise


def validate_schema():
    """Validate the schema was created correctly"""
    from models import db
    
    # Check for duplicates in object_lookup (should return 0)
    result = db.session.execute("""
        SELECT uuid, COUNT(*) as count 
        FROM object_lookup 
        GROUP BY uuid 
        HAVING count > 1
    """)
    duplicates = result.fetchall()
    
    if duplicates:
        print(f"⚠️  WARNING: Found {len(duplicates)} duplicate UUIDs in object_lookup")
        for row in duplicates:
            print(f"   - UUID: {row[0]}, Count: {row[1]}")
    else:
        print("✅ No duplicate UUIDs in object_lookup")
    
    # Verify tables exist
    tables_to_check = [
        'merge_sessions',
        'packages',
        'object_lookup',
        'package_object_mappings',
        'delta_comparison_results',
        'changes',
        'object_versions',
        'interfaces',
        'expression_rules',
        'process_models',
        'record_types',
        'cdts',
        'integrations',
        'web_apis',
        'sites',
        'groups',
        'constants',
        'connected_systems',
        'unknown_objects',
        'interface_comparisons',
        'process_model_comparisons',
        'record_type_comparisons'
    ]
    
    print("\nVerifying tables exist...")
    for table in tables_to_check:
        try:
            result = db.session.execute(f"SELECT COUNT(*) FROM {table}")
            count = result.fetchone()[0]
            print(f"✅ {table}: {count} rows")
        except Exception as e:
            print(f"❌ {table}: ERROR - {e}")
    
    print("\n" + "=" * 70)
    print("Schema validation complete!")
    print("=" * 70)


if __name__ == '__main__':
    run_migration()
