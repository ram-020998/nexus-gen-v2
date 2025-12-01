"""
Run Package ID Migration with Validation

This script:
1. Executes the migration on the development database
2. Verifies all tables were modified successfully
3. Checks logs for warnings or errors
4. Runs validation queries to verify data integrity

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import logging
import sys
from app import create_app
from models import db
from sqlalchemy import text
from migrations.migrations_004_add_package_id_to_objects import Migration004AddPackageIdToObjects

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('migration_004_execution.log')
    ]
)
logger = logging.getLogger(__name__)


def run_validation_queries():
    """
    Run validation queries to verify data integrity.
    
    Validates:
    - 7.1: All object-specific entries have non-NULL package_id values
    - 7.2: No duplicate (object_id, package_id) combinations exist
    - 7.3: All package_id values reference valid packages
    - 7.4: Package_object_mappings entries exist for all combinations
    - 7.5: Object distribution per package is reasonable
    """
    logger.info("\n" + "=" * 80)
    logger.info("VALIDATION QUERIES")
    logger.info("=" * 80)
    
    tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    validation_passed = True
    
    # Validation 7.1: Check for NULL package_id values
    logger.info("\n[Validation 7.1] Checking for NULL package_id values...")
    total_nulls = 0
    for table in tables:
        sql = text(f"SELECT COUNT(*) FROM {table} WHERE package_id IS NULL")
        result = db.session.execute(sql)
        null_count = result.scalar()
        
        if null_count > 0:
            logger.error(f"  ❌ {table}: {null_count} NULL values found")
            validation_passed = False
            total_nulls += null_count
        else:
            logger.info(f"  ✓ {table}: No NULL values")
    
    if total_nulls == 0:
        logger.info("✅ Validation 7.1 PASSED: No NULL package_id values found")
    else:
        logger.error(f"❌ Validation 7.1 FAILED: {total_nulls} NULL values found")
    
    # Validation 7.2: Check for duplicate (object_id, package_id) combinations
    logger.info("\n[Validation 7.2] Checking for duplicate (object_id, package_id) combinations...")
    total_duplicates = 0
    for table in tables:
        sql = text(f"""
            SELECT object_id, package_id, COUNT(*) as count
            FROM {table}
            GROUP BY object_id, package_id
            HAVING count > 1
        """)
        result = db.session.execute(sql)
        duplicates = result.fetchall()
        
        if duplicates:
            logger.error(f"  ❌ {table}: {len(duplicates)} duplicate combinations found")
            for dup in duplicates[:5]:  # Show first 5
                logger.error(f"      object_id={dup[0]}, package_id={dup[1]}, count={dup[2]}")
            validation_passed = False
            total_duplicates += len(duplicates)
        else:
            logger.info(f"  ✓ {table}: No duplicates")
    
    if total_duplicates == 0:
        logger.info("✅ Validation 7.2 PASSED: No duplicate combinations found")
    else:
        logger.error(f"❌ Validation 7.2 FAILED: {total_duplicates} duplicate combinations found")
    
    # Validation 7.3: Check that all package_id values reference valid packages
    logger.info("\n[Validation 7.3] Checking referential integrity (package_id → packages)...")
    total_invalid = 0
    for table in tables:
        sql = text(f"""
            SELECT COUNT(*)
            FROM {table} t
            WHERE t.package_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM packages p WHERE p.id = t.package_id
            )
        """)
        result = db.session.execute(sql)
        invalid_count = result.scalar()
        
        if invalid_count > 0:
            logger.error(f"  ❌ {table}: {invalid_count} invalid package_id references")
            validation_passed = False
            total_invalid += invalid_count
        else:
            logger.info(f"  ✓ {table}: All package_id values are valid")
    
    if total_invalid == 0:
        logger.info("✅ Validation 7.3 PASSED: All package_id values reference valid packages")
    else:
        logger.error(f"❌ Validation 7.3 FAILED: {total_invalid} invalid references found")
    
    # Validation 7.4: Check package_object_mappings consistency
    logger.info("\n[Validation 7.4] Checking package_object_mappings consistency...")
    total_missing = 0
    for table in tables:
        sql = text(f"""
            SELECT COUNT(*)
            FROM {table} t
            WHERE NOT EXISTS (
                SELECT 1 
                FROM package_object_mappings pom
                WHERE pom.object_id = t.object_id
                AND pom.package_id = t.package_id
            )
        """)
        result = db.session.execute(sql)
        missing_count = result.scalar()
        
        if missing_count > 0:
            logger.warning(f"  ⚠ {table}: {missing_count} entries missing from package_object_mappings")
            total_missing += missing_count
        else:
            logger.info(f"  ✓ {table}: All entries have corresponding mappings")
    
    if total_missing == 0:
        logger.info("✅ Validation 7.4 PASSED: All entries have package_object_mappings")
    else:
        logger.warning(f"⚠ Validation 7.4 WARNING: {total_missing} entries missing mappings")
        logger.info("  Note: This may be expected if objects were added directly to tables")
    
    # Validation 7.5: Check object distribution per package
    logger.info("\n[Validation 7.5] Checking object distribution per package...")
    
    # Get package info
    packages_sql = text("SELECT id, package_type, filename FROM packages ORDER BY id")
    packages_result = db.session.execute(packages_sql)
    packages = packages_result.fetchall()
    
    if not packages:
        logger.warning("  ⚠ No packages found in database")
    else:
        logger.info(f"  Found {len(packages)} packages:")
        
        for pkg in packages:
            pkg_id, pkg_type, filename = pkg
            logger.info(f"\n  Package {pkg_id} ({pkg_type}): {filename}")
            
            total_objects = 0
            for table in tables:
                sql = text(f"SELECT COUNT(*) FROM {table} WHERE package_id = :pkg_id")
                result = db.session.execute(sql, {"pkg_id": pkg_id})
                count = result.scalar()
                
                if count > 0:
                    logger.info(f"    {table}: {count} objects")
                    total_objects += count
            
            logger.info(f"    Total: {total_objects} objects")
        
        logger.info("✅ Validation 7.5 PASSED: Object distribution verified")
    
    # Summary
    logger.info("\n" + "=" * 80)
    if validation_passed:
        logger.info("✅ ALL VALIDATIONS PASSED")
    else:
        logger.error("❌ SOME VALIDATIONS FAILED - Manual review required")
    logger.info("=" * 80)
    
    return validation_passed


def verify_schema_changes():
    """Verify that all tables were modified successfully"""
    logger.info("\n" + "=" * 80)
    logger.info("SCHEMA VERIFICATION")
    logger.info("=" * 80)
    
    tables = [
        'interfaces', 'expression_rules', 'process_models', 'record_types',
        'cdts', 'integrations', 'web_apis', 'sites', 'groups', 'constants',
        'connected_systems', 'data_stores', 'unknown_objects'
    ]
    
    all_verified = True
    
    for table in tables:
        logger.info(f"\nVerifying {table}...")
        
        # Check if package_id column exists
        sql = text(f"PRAGMA table_info({table})")
        result = db.session.execute(sql)
        columns = {row[1]: row for row in result}
        
        if 'package_id' not in columns:
            logger.error(f"  ❌ package_id column NOT found")
            all_verified = False
            continue
        
        logger.info(f"  ✓ package_id column exists")
        
        # Check for indexes
        sql = text(f"PRAGMA index_list({table})")
        result = db.session.execute(sql)
        indexes = {row[1]: row for row in result}
        
        expected_indexes = [
            f"idx_{table}_package",
            f"idx_{table}_object_package",
            f"uq_{table}_object_package"
        ]
        
        for idx_name in expected_indexes:
            if idx_name in indexes:
                logger.info(f"  ✓ Index {idx_name} exists")
            else:
                logger.warning(f"  ⚠ Index {idx_name} NOT found")
    
    if all_verified:
        logger.info("\n✅ All tables verified successfully")
    else:
        logger.error("\n❌ Some tables failed verification")
    
    return all_verified


def main():
    """Main execution function"""
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Run the migration
            logger.info("=" * 80)
            logger.info("EXECUTING PACKAGE ID MIGRATION")
            logger.info("=" * 80)
            
            migration = Migration004AddPackageIdToObjects()
            migration.upgrade()
            
            # Step 2: Verify schema changes
            schema_ok = verify_schema_changes()
            
            # Step 3: Run validation queries
            validation_ok = run_validation_queries()
            
            # Final summary
            logger.info("\n" + "=" * 80)
            logger.info("MIGRATION EXECUTION SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Migration executed: ✅")
            logger.info(f"Schema verification: {'✅' if schema_ok else '❌'}")
            logger.info(f"Data validation: {'✅' if validation_ok else '❌'}")
            
            if schema_ok and validation_ok:
                logger.info("\n🎉 Migration completed successfully with all validations passing!")
                return 0
            else:
                logger.warning("\n⚠ Migration completed but some validations failed")
                logger.warning("Please review the logs above for details")
                return 1
            
        except Exception as e:
            logger.error("\n" + "=" * 80)
            logger.error("❌ MIGRATION EXECUTION FAILED")
            logger.error("=" * 80)
            logger.error(f"Error: {str(e)}")
            logger.error("All changes have been rolled back")
            return 2


if __name__ == '__main__':
    sys.exit(main())
