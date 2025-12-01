"""
Run migration_004 to add package_id to all object-specific tables.

This script runs the complete upgrade workflow.
"""

import logging
from app import create_app
from models import db
from migrations.migrations_004_add_package_id_to_objects import (
    Migration004AddPackageIdToObjects
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    logger.info("Starting migration_004 execution...")
    
    app = create_app()
    with app.app_context():
        try:
            migration = Migration004AddPackageIdToObjects()
            migration.upgrade()
            logger.info("\n✅ Migration completed successfully!")
        except Exception as e:
            logger.error(f"\n❌ Migration failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            exit(1)
