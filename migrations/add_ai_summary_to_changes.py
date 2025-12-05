"""
Add AI summary fields to changes table

Migration: 004
Created: December 2, 2025
Purpose: Add AI-powered summary generation fields to support merge change analysis
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from models import db
from app import create_app


def upgrade():
    """Add AI summary columns to changes table"""
    app = create_app()
    
    with app.app_context():
        print("Starting migration: add_ai_summary_to_changes")
        
        # Add ai_summary column
        print("  Adding ai_summary column...")
        db.session.execute(text("""
            ALTER TABLE changes 
            ADD COLUMN ai_summary TEXT
        """))
        
        # Add ai_summary_status column with default value
        print("  Adding ai_summary_status column...")
        db.session.execute(text("""
            ALTER TABLE changes 
            ADD COLUMN ai_summary_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        """))
        
        # Add ai_summary_generated_at column
        print("  Adding ai_summary_generated_at column...")
        db.session.execute(text("""
            ALTER TABLE changes 
            ADD COLUMN ai_summary_generated_at DATETIME
        """))
        
        # Add index for efficient status queries
        print("  Creating index on ai_summary_status...")
        db.session.execute(text("""
            CREATE INDEX idx_change_ai_summary_status 
            ON changes (session_id, ai_summary_status)
        """))
        
        db.session.commit()
        print("✓ Migration completed successfully")


def downgrade():
    """Remove AI summary columns from changes table"""
    app = create_app()
    
    with app.app_context():
        print("Starting rollback: add_ai_summary_to_changes")
        
        # Drop index
        print("  Dropping index idx_change_ai_summary_status...")
        db.session.execute(text("""
            DROP INDEX IF EXISTS idx_change_ai_summary_status
        """))
        
        # Drop columns
        print("  Dropping ai_summary_generated_at column...")
        db.session.execute(text("""
            ALTER TABLE changes 
            DROP COLUMN ai_summary_generated_at
        """))
        
        print("  Dropping ai_summary_status column...")
        db.session.execute(text("""
            ALTER TABLE changes 
            DROP COLUMN ai_summary_status
        """))
        
        print("  Dropping ai_summary column...")
        db.session.execute(text("""
            ALTER TABLE changes 
            DROP COLUMN ai_summary
        """))
        
        db.session.commit()
        print("✓ Rollback completed successfully")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        downgrade()
    else:
        upgrade()
