"""
Migration Runner for UI Enhancement
"""
import sys
from app import create_app
from models import db

def run_migration():
    """Run the UI enhancement migration"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("Running UI Enhancement Migration")
        print("=" * 70)
        
        # Import migration functions
        sys.path.insert(0, 'migrations')
        from migrations_002_ui_enhancement import upgrade
        
        try:
            # Run the migration
            upgrade()
            
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
    """Validate the schema was updated correctly"""
    from models import db
    from sqlalchemy import text
    
    print("\nVerifying new columns in changes table...")
    try:
        result = db.session.execute(text("""
            SELECT status, notes, reviewed_at, reviewed_by 
            FROM changes 
            LIMIT 1
        """))
        print("✅ changes table: status, notes, reviewed_at, reviewed_by columns exist")
    except Exception as e:
        print(f"❌ changes table: ERROR - {e}")
    
    print("\nVerifying new columns in merge_sessions table...")
    try:
        result = db.session.execute(text("""
            SELECT reviewed_count, skipped_count, estimated_complexity, estimated_time_hours 
            FROM merge_sessions 
            LIMIT 1
        """))
        print("✅ merge_sessions table: reviewed_count, skipped_count, estimated_complexity, estimated_time_hours columns exist")
    except Exception as e:
        print(f"❌ merge_sessions table: ERROR - {e}")
    
    print("\nVerifying indexes...")
    try:
        result = db.session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='index' 
            AND (name='idx_change_session_status' OR name='idx_change_reviewed_at')
        """))
        indexes = result.fetchall()
        if len(indexes) == 2:
            print("✅ Performance indexes created successfully")
            for idx in indexes:
                print(f"   - {idx[0]}")
        else:
            print(f"⚠️  WARNING: Expected 2 indexes, found {len(indexes)}")
    except Exception as e:
        print(f"❌ Index verification: ERROR - {e}")
    
    print("\n" + "=" * 70)
    print("Schema validation complete!")
    print("=" * 70)


if __name__ == '__main__':
    run_migration()
