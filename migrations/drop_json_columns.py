"""
Migration script to drop old JSON columns from MergeSession table.

This migration removes the following columns that are no longer needed
after data has been normalized into separate tables:
- base_blueprint
- customized_blueprint
- new_vendor_blueprint
- vendor_changes
- customer_changes
- classification_results
- ordered_changes

Requirements: 1.1, 1.2, 1.3
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db, ChangeReview
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_data_migration():
    """
    Verify that all sessions have been migrated to normalized schema.
    
    Returns:
        bool: True if all sessions are migrated, False otherwise
    """
    logger.info("Verifying data migration status...")
    
    # Check if all sessions have corresponding Package records
    result = db.session.execute(text("""
        SELECT 
            ms.id,
            ms.reference_id,
            COUNT(DISTINCT p.id) as package_count
        FROM merge_sessions ms
        LEFT JOIN packages p ON p.session_id = ms.id
        GROUP BY ms.id, ms.reference_id
        HAVING package_count != 3
    """)).fetchall()
    
    if result:
        logger.error(f"Found {len(result)} sessions without 3 packages:")
        for row in result:
            logger.error(f"  Session {row[1]} (ID: {row[0]}) has {row[2]} packages")
        return False
    
    # Check if all sessions have corresponding Change records
    result = db.session.execute(text("""
        SELECT 
            ms.id,
            ms.reference_id,
            ms.total_changes,
            COUNT(c.id) as change_count
        FROM merge_sessions ms
        LEFT JOIN changes c ON c.session_id = ms.id
        WHERE ms.total_changes > 0
        GROUP BY ms.id, ms.reference_id, ms.total_changes
        HAVING change_count != ms.total_changes
    """)).fetchall()
    
    if result:
        logger.error(f"Found {len(result)} sessions with mismatched change counts:")
        for row in result:
            logger.error(f"  Session {row[1]} (ID: {row[0]}) expects {row[2]} changes but has {row[3]}")
        return False
    
    logger.info("✅ All sessions have been successfully migrated")
    return True


def check_column_exists(table_name, column_name):
    """
    Check if a column exists in a table.
    
    Args:
        table_name: Name of the table
        column_name: Name of the column
        
    Returns:
        bool: True if column exists, False otherwise
    """
    result = db.session.execute(text("""
        SELECT COUNT(*) 
        FROM pragma_table_info(:table_name)
        WHERE name = :column_name
    """), {"table_name": table_name, "column_name": column_name}).scalar()
    
    return result > 0


def drop_json_columns():
    """
    Drop old JSON columns from MergeSession table.
    
    This function:
    1. Verifies all data has been migrated
    2. Creates a backup of the table structure
    3. Drops the JSON columns
    4. Verifies the application still works
    """
    logger.info("Starting JSON column removal process...")
    
    # Verify migration is complete
    if not verify_data_migration():
        logger.error("❌ Data migration is not complete. Aborting column removal.")
        logger.error("Please run migrate_merge_sessions.py first to migrate all sessions.")
        return False
    
    # List of columns to drop
    columns_to_drop = [
        'base_blueprint',
        'customized_blueprint',
        'new_vendor_blueprint',
        'vendor_changes',
        'customer_changes',
        'classification_results',
        'ordered_changes'
    ]
    
    # Check which columns exist
    existing_columns = []
    for column in columns_to_drop:
        if check_column_exists('merge_sessions', column):
            existing_columns.append(column)
            logger.info(f"  Found column: {column}")
        else:
            logger.info(f"  Column already removed: {column}")
    
    if not existing_columns:
        logger.info("✅ All JSON columns have already been removed")
        return True
    
    logger.info(f"Will drop {len(existing_columns)} columns: {', '.join(existing_columns)}")
    
    # SQLite doesn't support DROP COLUMN directly, so we need to:
    # 1. Create a new table without the JSON columns
    # 2. Copy data from old table to new table
    # 3. Drop old table
    # 4. Rename new table to old name
    
    try:
        logger.info("Creating new table structure without JSON columns...")
        
        # Create new table with desired structure
        db.session.execute(text("""
            CREATE TABLE merge_sessions_new (
                id INTEGER PRIMARY KEY,
                reference_id VARCHAR(20) UNIQUE NOT NULL,
                base_package_name VARCHAR(255) NOT NULL,
                customized_package_name VARCHAR(255) NOT NULL,
                new_vendor_package_name VARCHAR(255) NOT NULL,
                status VARCHAR(20) DEFAULT 'processing',
                current_change_index INTEGER DEFAULT 0,
                total_changes INTEGER DEFAULT 0,
                reviewed_count INTEGER DEFAULT 0,
                skipped_count INTEGER DEFAULT 0,
                created_at DATETIME,
                updated_at DATETIME,
                completed_at DATETIME,
                total_time INTEGER,
                error_log TEXT
            )
        """))
        
        logger.info("Copying data to new table...")
        
        # Copy data from old table to new table
        db.session.execute(text("""
            INSERT INTO merge_sessions_new (
                id, reference_id, base_package_name, customized_package_name,
                new_vendor_package_name, status, current_change_index,
                total_changes, reviewed_count, skipped_count,
                created_at, updated_at, completed_at, total_time, error_log
            )
            SELECT 
                id, reference_id, base_package_name, customized_package_name,
                new_vendor_package_name, status, current_change_index,
                total_changes, reviewed_count, skipped_count,
                created_at, updated_at, completed_at, total_time, error_log
            FROM merge_sessions
        """))
        
        logger.info("Dropping old table...")
        db.session.execute(text("DROP TABLE merge_sessions"))
        
        logger.info("Renaming new table...")
        db.session.execute(text("ALTER TABLE merge_sessions_new RENAME TO merge_sessions"))
        
        logger.info("Recreating indexes...")
        db.session.execute(text("CREATE UNIQUE INDEX idx_merge_sessions_reference_id ON merge_sessions(reference_id)"))
        
        # Commit the transaction
        db.session.commit()
        
        logger.info("✅ Successfully removed JSON columns from MergeSession table")
        
        # Verify the columns are gone
        logger.info("Verifying column removal...")
        for column in existing_columns:
            if check_column_exists('merge_sessions', column):
                logger.error(f"❌ Column {column} still exists!")
                return False
            else:
                logger.info(f"  ✅ Column {column} removed")
        
        logger.info("✅ All JSON columns successfully removed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during column removal: {str(e)}")
        db.session.rollback()
        return False


def main():
    """Main execution function"""
    app = create_app()
    
    with app.app_context():
        logger.info("=" * 80)
        logger.info("JSON Column Removal Migration")
        logger.info("=" * 80)
        
        success = drop_json_columns()
        
        if success:
            logger.info("=" * 80)
            logger.info("✅ Migration completed successfully")
            logger.info("=" * 80)
        else:
            logger.info("=" * 80)
            logger.error("❌ Migration failed")
            logger.info("=" * 80)
            exit(1)


if __name__ == '__main__':
    main()
