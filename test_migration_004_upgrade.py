"""
Test script for migration_004 complete upgrade workflow.

This script tests the complete upgrade() method that orchestrates
all 8 steps of the package_id migration.

Requirements: 1.1, 1.2, 1.4, 2.5, 3.1, 3.3, 9.1, 9.4
"""

import logging
from app import create_app
from models import db
from sqlalchemy import text, inspect
from migrations.migrations_004_add_package_id_to_objects import (
    Migration004AddPackageIdToObjects
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def check_index_exists(index_name: str) -> bool:
    """Check if an index exists"""
    sql = text("""
        SELECT name FROM sqlite_master
        WHERE type='index' AND name=:index_name
    """)
    result = db.session.execute(sql, {'index_name': index_name})
    return result.fetchone() is not None


def verify_migration_state():
    """
    Verify the complete state after migration.

    Checks:
    1. All 13 tables have package_id column
    2. All package_id columns have indexes
    3. All tables have unique constraints
    4. All tables have composite indexes
    5. No NULL package_id values (if data exists)
    """
    logger.info("\n" + "=" * 80)
    logger.info("VERIFYING MIGRATION STATE")
    logger.info("=" * 80)

    tables = Migration004AddPackageIdToObjects.OBJECT_TABLES
    all_checks_passed = True

    for table in tables:
        logger.info(f"\nChecking {table}...")

        # Check 1: package_id column exists
        if not check_column_exists(table, 'package_id'):
            logger.error(f"  ❌ Missing package_id column")
            all_checks_passed = False
            continue
        else:
            logger.info(f"  ✓ package_id column exists")

        # Check 2: Single-column index exists
        index_name = f"idx_{table}_package"
        if not check_index_exists(index_name):
            logger.error(f"  ❌ Missing index {index_name}")
            all_checks_passed = False
        else:
            logger.info(f"  ✓ Index {index_name} exists")

        # Check 3: Unique constraint exists
        constraint_name = f"uq_{table}_object_package"
        if not check_index_exists(constraint_name):
            logger.error(f"  ❌ Missing unique constraint {constraint_name}")
            all_checks_passed = False
        else:
            logger.info(f"  ✓ Unique constraint {constraint_name} exists")

        # Check 4: Composite index exists
        composite_index = f"idx_{table}_object_package"
        if not check_index_exists(composite_index):
            logger.error(f"  ❌ Missing composite index {composite_index}")
            all_checks_passed = False
        else:
            logger.info(f"  ✓ Composite index {composite_index} exists")

        # Check 5: No NULL values (if table has data)
        sql = text(f"SELECT COUNT(*) FROM {table}")
        result = db.session.execute(sql)
        total_count = result.scalar()

        if total_count > 0:
            sql = text(f"""
                SELECT COUNT(*) FROM {table} WHERE package_id IS NULL
            """)
            result = db.session.execute(sql)
            null_count = result.scalar()

            if null_count > 0:
                logger.warning(
                    f"  ⚠ {null_count}/{total_count} entries have NULL "
                    f"package_id"
                )
            else:
                logger.info(
                    f"  ✓ All {total_count} entries have package_id set"
                )

    logger.info("\n" + "=" * 80)
    if all_checks_passed:
        logger.info("✅ ALL VERIFICATION CHECKS PASSED")
    else:
        logger.error("❌ SOME VERIFICATION CHECKS FAILED")
    logger.info("=" * 80)

    return all_checks_passed


def test_upgrade_workflow():
    """
    Test the complete upgrade() workflow.

    This test runs the full migration and verifies all steps completed.
    """
    logger.info("\n" + "=" * 80)
    logger.info("TESTING COMPLETE UPGRADE WORKFLOW")
    logger.info("=" * 80)

    try:
        # Check if migration already ran
        if check_column_exists('interfaces', 'package_id'):
            logger.info("\n⚠ Migration appears to have already run")
            logger.info("  package_id column already exists in interfaces")
            logger.info("  Verifying migration state instead...")
            return verify_migration_state()

        # Run the migration
        logger.info("\nRunning migration...")
        migration = Migration004AddPackageIdToObjects()
        migration.upgrade()

        logger.info("\n✅ Migration completed successfully!")

        # Verify the results
        return verify_migration_state()

    except Exception as e:
        logger.error(f"\n❌ Migration failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        success = test_upgrade_workflow()
        exit(0 if success else 1)
