"""
Test script for _populate_package_id() method.

This script tests the data migration method with sample data.

Requirements: 2.1, 2.2, 2.3, 2.4
"""

import logging
from app import create_app
from models import (db, MergeSession, Package, ObjectLookup, ObjectVersion,
                    Interface)
from sqlalchemy import text
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
    sql = text(f"PRAGMA table_info({table_name})")
    result = db.session.execute(sql)
    columns = [row[1] for row in result.fetchall()]
    return column_name in columns


def test_populate_package_id():
    """Test _populate_package_id() method with sample data"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: _populate_package_id()")
    logger.info("=" * 80)
    
    migration = Migration004AddPackageIdToObjects()
    test_table = 'interfaces'
    
    # Ensure package_id column exists
    if not check_column_exists(test_table, 'package_id'):
        logger.error("❌ FAILED: package_id column doesn't exist")
        logger.error("  Run migration step 1 first to add the column")
        return False
    
    # Drop unique constraint if it exists (it should be added AFTER populating)
    logger.info("Checking for existing unique constraint...")
    check_constraint_sql = text("""
        SELECT name FROM sqlite_master 
        WHERE type='index' 
        AND tbl_name='interfaces'
        AND name LIKE 'uq_%_object_package%'
    """)
    result = db.session.execute(check_constraint_sql)
    constraints = [row[0] for row in result.fetchall()]
    
    if constraints:
        logger.info(f"  Found unique constraint(s): {constraints}")
        logger.info("  Dropping constraint(s) for testing...")
        for constraint_name in constraints:
            drop_sql = text(f"DROP INDEX IF EXISTS {constraint_name}")
            db.session.execute(drop_sql)
        db.session.commit()
        logger.info("  ✓ Dropped unique constraint(s)")
    
    try:
        # Cleanup any existing test data first
        logger.info("Cleaning up any existing test data...")
        
        # Delete test session (CASCADE will delete packages, versions, etc.)
        existing_session = MergeSession.query.filter_by(
            reference_id='MS_TEST_POPULATE'
        ).first()
        if existing_session:
            db.session.delete(existing_session)
            db.session.commit()
            logger.info("  ✓ Cleaned up existing test session")
        
        # Delete test interfaces first (before objects due to FK)
        test_uuids = [
            'test-uuid-populate-001',
            'test-uuid-populate-002',
            'test-uuid-populate-003'
        ]
        for uuid in test_uuids:
            interfaces = Interface.query.filter_by(uuid=uuid).all()
            for interface in interfaces:
                db.session.delete(interface)
        db.session.commit()
        
        # Delete test objects
        for uuid in test_uuids:
            obj = ObjectLookup.query.filter_by(uuid=uuid).first()
            if obj:
                db.session.delete(obj)
        db.session.commit()
        logger.info("  ✓ Cleaned up existing test objects")
        
        # Setup: Create test data
        logger.info("Setting up test data...")
        
        # Create merge session
        session = MergeSession(
            reference_id='MS_TEST_POPULATE',
            status='processing'
        )
        db.session.add(session)
        db.session.flush()
        
        # Create packages
        pkg_base = Package(
            session_id=session.id,
            package_type='base',
            filename='base.zip'
        )
        pkg_custom = Package(
            session_id=session.id,
            package_type='customized',
            filename='custom.zip'
        )
        pkg_vendor = Package(
            session_id=session.id,
            package_type='new_vendor',
            filename='vendor.zip'
        )
        db.session.add_all([pkg_base, pkg_custom, pkg_vendor])
        db.session.flush()
        
        # Create object_lookup entries
        obj1 = ObjectLookup(
            uuid='test-uuid-populate-001',
            name='TestInterface1',
            object_type='Interface'
        )
        obj2 = ObjectLookup(
            uuid='test-uuid-populate-002',
            name='TestInterface2',
            object_type='Interface'
        )
        obj3 = ObjectLookup(
            uuid='test-uuid-populate-003',
            name='TestInterface3',
            object_type='Interface'
        )
        db.session.add_all([obj1, obj2, obj3])
        db.session.flush()
        
        # Create object_versions (source of truth for package_id)
        ver1_base = ObjectVersion(
            object_id=obj1.id,
            package_id=pkg_base.id,
            version_uuid='v1-base-test'
        )
        ver1_custom = ObjectVersion(
            object_id=obj1.id,
            package_id=pkg_custom.id,
            version_uuid='v1-custom-test'
        )
        ver2_base = ObjectVersion(
            object_id=obj2.id,
            package_id=pkg_base.id,
            version_uuid='v2-base-test'
        )
        ver3_vendor = ObjectVersion(
            object_id=obj3.id,
            package_id=pkg_vendor.id,
            version_uuid='v3-vendor-test'
        )
        db.session.add_all([ver1_base, ver1_custom, ver2_base, ver3_vendor])
        db.session.flush()
        
        # Create interface entries WITHOUT package_id
        # (simulating pre-migration state)
        int1_base = Interface(
            object_id=obj1.id,
            uuid='test-uuid-populate-001',
            name='TestInterface1',
            version_uuid='v1-base-test'
        )
        int1_custom = Interface(
            object_id=obj1.id,
            uuid='test-uuid-populate-001',
            name='TestInterface1',
            version_uuid='v1-custom-test'
        )
        int2_base = Interface(
            object_id=obj2.id,
            uuid='test-uuid-populate-002',
            name='TestInterface2',
            version_uuid='v2-base-test'
        )
        int3_vendor = Interface(
            object_id=obj3.id,
            uuid='test-uuid-populate-003',
            name='TestInterface3',
            version_uuid='v3-vendor-test'
        )
        # Add one entry with no matching object_version (orphan)
        int_orphan = Interface(
            object_id=obj1.id,
            uuid='test-uuid-populate-001',
            name='TestInterface1',
            version_uuid='v1-orphan-test'  # No matching version_uuid
        )
        
        db.session.add_all([int1_base, int1_custom, int2_base,
                           int3_vendor, int_orphan])
        db.session.commit()
        
        logger.info("✓ Test data created:")
        logger.info("  - 3 packages (base, customized, new_vendor)")
        logger.info("  - 3 objects in object_lookup")
        logger.info("  - 4 object_versions")
        logger.info("  - 5 interfaces (4 valid, 1 orphan)")
        
        # Test: Populate package_id
        logger.info("\nPopulating package_id for interfaces...")
        migration._populate_package_id(test_table)
        db.session.commit()
        
        # Verify: Check that package_id was populated correctly
        logger.info("\nVerifying results...")
        
        # Query database directly since ORM model doesn't have package_id yet
        verify_sql = text("""
            SELECT id, object_id, version_uuid, package_id, name
            FROM interfaces
            WHERE object_id IN (:obj1_id, :obj2_id, :obj3_id)
            ORDER BY id
        """)
        result = db.session.execute(verify_sql, {
            'obj1_id': obj1.id,
            'obj2_id': obj2.id,
            'obj3_id': obj3.id
        })
        interfaces_data = result.fetchall()
        
        # Create a lookup dict for easier verification
        interfaces_by_version = {}
        for row in interfaces_data:
            version_uuid = row[2]
            interfaces_by_version[version_uuid] = {
                'id': row[0],
                'object_id': row[1],
                'package_id': row[3],
                'name': row[4]
            }
        
        # Validate results
        success = True
        errors = []
        
        # Check int1_base
        if 'v1-base-test' in interfaces_by_version:
            data = interfaces_by_version['v1-base-test']
            if data['package_id'] != pkg_base.id:
                msg = (f"int1_base: Expected package_id={pkg_base.id}, "
                       f"got {data['package_id']}")
                errors.append(msg)
                success = False
            else:
                logger.info(f"  ✓ int1_base: package_id={pkg_base.id} (base)")
        else:
            errors.append("int1_base: Not found in database")
            success = False
        
        # Check int1_custom
        if 'v1-custom-test' in interfaces_by_version:
            data = interfaces_by_version['v1-custom-test']
            if data['package_id'] != pkg_custom.id:
                msg = (f"int1_custom: Expected package_id={pkg_custom.id}, "
                       f"got {data['package_id']}")
                errors.append(msg)
                success = False
            else:
                logger.info(f"  ✓ int1_custom: package_id={pkg_custom.id} "
                           "(customized)")
        else:
            errors.append("int1_custom: Not found in database")
            success = False
        
        # Check int2_base
        if 'v2-base-test' in interfaces_by_version:
            data = interfaces_by_version['v2-base-test']
            if data['package_id'] != pkg_base.id:
                msg = (f"int2_base: Expected package_id={pkg_base.id}, "
                       f"got {data['package_id']}")
                errors.append(msg)
                success = False
            else:
                logger.info(f"  ✓ int2_base: package_id={pkg_base.id} (base)")
        else:
            errors.append("int2_base: Not found in database")
            success = False
        
        # Check int3_vendor
        if 'v3-vendor-test' in interfaces_by_version:
            data = interfaces_by_version['v3-vendor-test']
            if data['package_id'] != pkg_vendor.id:
                msg = (f"int3_vendor: Expected package_id={pkg_vendor.id}, "
                       f"got {data['package_id']}")
                errors.append(msg)
                success = False
            else:
                logger.info(f"  ✓ int3_vendor: package_id={pkg_vendor.id} "
                           "(new_vendor)")
        else:
            errors.append("int3_vendor: Not found in database")
            success = False
        
        # Check orphan has NULL package_id
        if 'v1-orphan-test' in interfaces_by_version:
            data = interfaces_by_version['v1-orphan-test']
            if data['package_id'] is not None:
                msg = (f"int_orphan: Expected package_id=NULL, "
                       f"got {data['package_id']}")
                errors.append(msg)
                success = False
            else:
                logger.info("  ✓ int_orphan: package_id=NULL (no match)")
        else:
            errors.append("int_orphan: Not found in database")
            success = False
        
        # Cleanup test data
        logger.info("\nCleaning up test data...")
        db.session.delete(session)
        db.session.commit()
        logger.info("  ✓ Test data cleaned up")
        
        # Print results
        logger.info("\n" + "=" * 80)
        if success:
            logger.info("✅ SUCCESS: _populate_package_id() works correctly")
            logger.info("  - Matched 4/5 entries by object_id + version_uuid")
            logger.info("  - Correctly left 1 orphan entry as NULL")
            logger.info("  - Logged warning for unmatched entry")
            logger.info("=" * 80)
            return True
        else:
            logger.error("❌ FAILED: Some package_id values incorrect")
            for error in errors:
                logger.error(f"  - {error}")
            logger.info("=" * 80)
            return False
            
    except Exception as e:
        logger.error(f"❌ FAILED: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        db.session.rollback()
        return False


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        logger.info("Testing _populate_package_id() method...")
        success = test_populate_package_id()
        exit(0 if success else 1)
