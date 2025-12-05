"""
Migration: Add customer_comparison_results table

This migration creates the customer_comparison_results table to store
complete customer changes (Set E).
"""

from app import create_app
from models import db
from sqlalchemy import text

def upgrade():
    """Apply migration."""
    app = create_app()
    with app.app_context():
        # Create customer_comparison_results table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS customer_comparison_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                object_id INTEGER NOT NULL,
                change_category VARCHAR(20) NOT NULL,
                change_type VARCHAR(20) NOT NULL,
                version_changed BOOLEAN DEFAULT 0,
                content_changed BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
                UNIQUE (session_id, object_id)
            )
        """))
        
        # Create indexes
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_customer_comparison_session_id 
            ON customer_comparison_results(session_id)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_customer_comparison_object_id 
            ON customer_comparison_results(object_id)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_customer_comparison_category
            ON customer_comparison_results(session_id, change_category)
        """))
        
        db.session.commit()
        print("✓ Migration completed successfully")

def downgrade():
    """Rollback migration."""
    app = create_app()
    with app.app_context():
        db.session.execute(text("DROP TABLE IF EXISTS customer_comparison_results"))
        db.session.commit()
        print("✓ Migration rolled back successfully")

if __name__ == '__main__':
    upgrade()
