"""
Clean up orphan test data before running migration.
"""

import logging
from app import create_app
from models import db
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        logger.info("Cleaning up orphan test data...")
        
        # Delete orphan interfaces
        sql = text("""
            DELETE FROM interfaces 
            WHERE version_uuid IN ('v1-orphan', 'v1-orphan-test')
        """)
        result = db.session.execute(sql)
        deleted = result.rowcount
        db.session.commit()
        
        logger.info(f"✓ Deleted {deleted} orphan interface entries")
        logger.info("Cleanup complete!")
