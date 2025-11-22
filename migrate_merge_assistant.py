"""
Database Migration Script for Three-Way Merge Assistant

This script creates the merge_sessions and change_reviews tables
with proper indexes and foreign keys.

Usage:
    python migrate_merge_assistant.py
"""
from app import create_app
from models import db, MergeSession, ChangeReview


def migrate():
    """Run database migration"""
    app = create_app()
    
    with app.app_context():
        print("Starting database migration for Three-Way Merge Assistant...")
        
        # Create tables
        print("Creating merge_sessions and change_reviews tables...")
        db.create_all()
        
        # Verify tables were created
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'merge_sessions' in tables:
            print("✓ merge_sessions table created successfully")
            
            # Check indexes
            indexes = inspector.get_indexes('merge_sessions')
            index_names = [idx['name'] for idx in indexes]
            print(f"  Indexes: {', '.join(index_names) if index_names else 'None (using default)'}")
        else:
            print("✗ Failed to create merge_sessions table")
            
        if 'change_reviews' in tables:
            print("✓ change_reviews table created successfully")
            
            # Check indexes
            indexes = inspector.get_indexes('change_reviews')
            index_names = [idx['name'] for idx in indexes]
            print(f"  Indexes: {', '.join(index_names) if index_names else 'None (using default)'}")
            
            # Check foreign keys
            foreign_keys = inspector.get_foreign_keys('change_reviews')
            if foreign_keys:
                print(f"  Foreign keys: {len(foreign_keys)} defined")
                for fk in foreign_keys:
                    print(f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            else:
                print("  Foreign keys: None")
        else:
            print("✗ Failed to create change_reviews table")
        
        print("\nMigration completed successfully!")
        print("\nConfiguration:")
        print(f"  Upload folder: {app.config['MERGE_UPLOAD_FOLDER']}")
        print(f"  Max file size: {app.config['MERGE_MAX_FILE_SIZE'] / (1024*1024):.0f}MB")
        print(f"  Session timeout: {app.config['MERGE_SESSION_TIMEOUT'] / 3600:.0f} hours")


if __name__ == '__main__':
    migrate()
