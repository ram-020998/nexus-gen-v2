"""
Database migration script to create normalized schema tables.

This script creates the new normalized tables for the merge assistant refactoring:
- packages
- package_object_type_counts
- appian_objects
- process_model_metadata
- process_model_nodes
- process_model_flows
- changes
- merge_guidance
- merge_conflicts
- merge_changes
- object_dependencies

It also updates the change_reviews table to add the change_id foreign key.
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import (
    db, 
    Package, 
    PackageObjectTypeCount, 
    AppianObject,
    ProcessModelMetadata,
    ProcessModelNode,
    ProcessModelFlow,
    Change,
    MergeGuidance,
    MergeConflict,
    MergeChange,
    ObjectDependency,
    ChangeReview
)
from sqlalchemy import inspect, text


def check_table_exists(table_name):
    """Check if a table exists in the database"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()


def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    inspector = inspect(db.engine)
    if not check_table_exists(table_name):
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def create_tables():
    """Create all new normalized tables"""
    print("Creating normalized schema tables...")
    
    # List of new tables to create
    new_tables = [
        'packages',
        'package_object_type_counts',
        'appian_objects',
        'process_model_metadata',
        'process_model_nodes',
        'process_model_flows',
        'changes',
        'merge_guidance',
        'merge_conflicts',
        'merge_changes',
        'object_dependencies'
    ]
    
    # Check which tables already exist
    existing_tables = []
    for table_name in new_tables:
        if check_table_exists(table_name):
            existing_tables.append(table_name)
            print(f"  ⚠️  Table '{table_name}' already exists")
        else:
            print(f"  ✓ Will create table '{table_name}'")
    
    if existing_tables:
        print(f"\n⚠️  {len(existing_tables)} table(s) already exist. Skipping creation for existing tables.")
    
    # Create all tables
    print("\nCreating tables...")
    db.create_all()
    print("✓ All tables created successfully")
    
    return True


def update_change_reviews_table():
    """Add change_id column to change_reviews table if it doesn't exist"""
    print("\nUpdating change_reviews table...")
    
    if not check_table_exists('change_reviews'):
        print("  ⚠️  change_reviews table doesn't exist yet")
        return True
    
    if check_column_exists('change_reviews', 'change_id'):
        print("  ✓ change_id column already exists")
        return True
    
    try:
        # Add change_id column
        with db.engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE change_reviews ADD COLUMN change_id INTEGER"
            ))
            conn.commit()
        
        print("  ✓ Added change_id column")
        
        # Create index on change_id
        with db.engine.connect() as conn:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_change_reviews_change_id ON change_reviews (change_id)"
            ))
            conn.commit()
        
        print("  ✓ Created index on change_id")
        
        # Create unique constraint
        with db.engine.connect() as conn:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_change_reviews_change_id ON change_reviews (change_id)"
            ))
            conn.commit()
        
        print("  ✓ Created unique constraint on change_id")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error updating change_reviews: {e}")
        return False


def verify_schema():
    """Verify that all tables and indexes were created correctly"""
    print("\nVerifying schema...")
    
    inspector = inspect(db.engine)
    
    # Check tables
    required_tables = [
        'packages',
        'package_object_type_counts',
        'appian_objects',
        'process_model_metadata',
        'process_model_nodes',
        'process_model_flows',
        'changes',
        'merge_guidance',
        'merge_conflicts',
        'merge_changes',
        'object_dependencies',
        'change_reviews'
    ]
    
    missing_tables = []
    for table_name in required_tables:
        if check_table_exists(table_name):
            print(f"  ✓ Table '{table_name}' exists")
        else:
            print(f"  ✗ Table '{table_name}' missing")
            missing_tables.append(table_name)
    
    if missing_tables:
        print(f"\n✗ Migration incomplete: {len(missing_tables)} table(s) missing")
        return False
    
    # Check key indexes
    print("\nVerifying indexes...")
    
    key_indexes = [
        ('packages', 'idx_package_session_type'),
        ('appian_objects', 'idx_object_type_name'),
        ('changes', 'idx_change_session_classification'),
        ('change_reviews', 'idx_review_session_status'),
    ]
    
    for table_name, index_name in key_indexes:
        indexes = inspector.get_indexes(table_name)
        index_names = [idx['name'] for idx in indexes]
        if index_name in index_names:
            print(f"  ✓ Index '{index_name}' exists on '{table_name}'")
        else:
            print(f"  ⚠️  Index '{index_name}' not found on '{table_name}'")
    
    # Check foreign keys
    print("\nVerifying foreign keys...")
    
    key_foreign_keys = [
        ('packages', 'session_id'),
        ('appian_objects', 'package_id'),
        ('changes', 'session_id'),
        ('change_reviews', 'change_id'),
    ]
    
    for table_name, fk_column in key_foreign_keys:
        fks = inspector.get_foreign_keys(table_name)
        fk_columns = [fk['constrained_columns'][0] for fk in fks if fk['constrained_columns']]
        if fk_column in fk_columns:
            print(f"  ✓ Foreign key on '{table_name}.{fk_column}' exists")
        else:
            print(f"  ⚠️  Foreign key on '{table_name}.{fk_column}' not found")
    
    print("\n✓ Schema verification complete")
    return True


def main():
    """Main migration function"""
    print("=" * 60)
    print("Merge Assistant Data Model Refactoring - Schema Migration")
    print("=" * 60)
    print()
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Step 1: Create new tables
        if not create_tables():
            return
        
        # Step 2: Update change_reviews table
        if not update_change_reviews_table():
            print("\n✗ Migration failed during change_reviews update")
            return
        
        # Step 3: Verify schema
        if not verify_schema():
            print("\n✗ Migration verification failed")
            return
        
        print("\n" + "=" * 60)
        print("✓ Migration completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Run tests to verify schema structure")
        print("2. Implement PackageService and ChangeService")
        print("3. Migrate existing data from JSON columns")
        print()


if __name__ == '__main__':
    main()
