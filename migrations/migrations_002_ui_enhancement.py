"""
Three-Way Merge UI Enhancement Migration
Version: 2.0
Date: 2025-11-30

This migration adds new columns to support UI enhancements including:
- Change status tracking (pending, reviewed, skipped)
- User notes on changes
- Review timestamps and user tracking
- Session progress metrics
- Complexity and time estimates

Requirements: 3.5, 3.6, 3.7, 4.3, 4.4, 5.5
"""

from models import db
from sqlalchemy import text


def upgrade():
    """Apply migration - add UI enhancement columns"""
    
    print("Adding UI enhancement columns to changes table...")
    add_changes_columns()
    
    print("Adding UI enhancement columns to merge_sessions table...")
    add_merge_sessions_columns()
    
    print("Creating performance indexes...")
    create_performance_indexes()
    
    db.session.commit()
    print("✅ UI enhancement migration completed successfully")


def downgrade():
    """Rollback migration - remove UI enhancement columns"""
    
    print("Removing performance indexes...")
    remove_performance_indexes()
    
    print("Removing UI enhancement columns from merge_sessions table...")
    remove_merge_sessions_columns()
    
    print("Removing UI enhancement columns from changes table...")
    remove_changes_columns()
    
    db.session.commit()
    print("✅ UI enhancement migration rolled back successfully")


def add_changes_columns():
    """Add new columns to changes table"""
    # Add status column with default 'pending'
    db.session.execute(text("""
        ALTER TABLE changes 
        ADD COLUMN status VARCHAR(20) DEFAULT 'pending'
    """))
    
    # Add notes TEXT column
    db.session.execute(text("""
        ALTER TABLE changes 
        ADD COLUMN notes TEXT
    """))
    
    # Add reviewed_at TIMESTAMP column
    db.session.execute(text("""
        ALTER TABLE changes 
        ADD COLUMN reviewed_at DATETIME
    """))
    
    # Add reviewed_by VARCHAR(255) column
    db.session.execute(text("""
        ALTER TABLE changes 
        ADD COLUMN reviewed_by VARCHAR(255)
    """))
    
    print("  ✓ Added status, notes, reviewed_at, reviewed_by to changes table")


def add_merge_sessions_columns():
    """Add new columns to merge_sessions table"""
    # Add reviewed_count INTEGER with default 0
    db.session.execute(text("""
        ALTER TABLE merge_sessions 
        ADD COLUMN reviewed_count INTEGER DEFAULT 0
    """))
    
    # Add skipped_count INTEGER with default 0
    db.session.execute(text("""
        ALTER TABLE merge_sessions 
        ADD COLUMN skipped_count INTEGER DEFAULT 0
    """))
    
    # Add estimated_complexity VARCHAR(20)
    db.session.execute(text("""
        ALTER TABLE merge_sessions 
        ADD COLUMN estimated_complexity VARCHAR(20)
    """))
    
    # Add estimated_time_hours FLOAT
    db.session.execute(text("""
        ALTER TABLE merge_sessions 
        ADD COLUMN estimated_time_hours FLOAT
    """))
    
    print("  ✓ Added reviewed_count, skipped_count, estimated_complexity, estimated_time_hours to merge_sessions table")


def create_performance_indexes():
    """Create indexes for performance optimization"""
    # Index on changes(session_id, status) for filtering by status
    db.session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_change_session_status 
        ON changes(session_id, status)
    """))
    
    # Index on changes(reviewed_at) for sorting by review time
    db.session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_change_reviewed_at 
        ON changes(reviewed_at)
    """))
    
    print("  ✓ Created performance indexes")


def remove_changes_columns():
    """Remove columns from changes table (SQLite doesn't support DROP COLUMN directly)"""
    # Note: SQLite doesn't support DROP COLUMN, so we need to recreate the table
    # For now, we'll just document this limitation
    print("  ⚠ SQLite doesn't support DROP COLUMN - manual rollback required")
    print("    To rollback, recreate the changes table without the new columns")


def remove_merge_sessions_columns():
    """Remove columns from merge_sessions table"""
    # Note: SQLite doesn't support DROP COLUMN, so we need to recreate the table
    print("  ⚠ SQLite doesn't support DROP COLUMN - manual rollback required")
    print("    To rollback, recreate the merge_sessions table without the new columns")


def remove_performance_indexes():
    """Remove performance indexes"""
    db.session.execute(text("DROP INDEX IF EXISTS idx_change_session_status"))
    db.session.execute(text("DROP INDEX IF EXISTS idx_change_reviewed_at"))
    print("  ✓ Removed performance indexes")


if __name__ == '__main__':
    """Run migration directly"""
    from app import create_app
    
    app = create_app()
    with app.app_context():
        print("Running UI enhancement migration...")
        upgrade()
        print("Migration completed successfully!")
