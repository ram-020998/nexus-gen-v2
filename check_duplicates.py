"""
Check for duplicate (object_id, package_id) combinations.
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
        logger.info("Checking for duplicate (object_id, package_id) combinations...")
        
        sql = text("""
            SELECT object_id, package_id, COUNT(*) as count
            FROM interfaces
            WHERE package_id IS NOT NULL
            GROUP BY object_id, package_id
            HAVING count > 1
        """)
        
        result = db.session.execute(sql)
        duplicates = result.fetchall()
        
        if duplicates:
            logger.warning(f"Found {len(duplicates)} duplicate combinations:")
            for dup in duplicates:
                logger.warning(f"  object_id={dup[0]}, package_id={dup[1]}, count={dup[2]}")
                
                # Show details
                detail_sql = text("""
                    SELECT id, uuid, name, version_uuid
                    FROM interfaces
                    WHERE object_id = :obj_id AND package_id = :pkg_id
                """)
                details = db.session.execute(
                    detail_sql,
                    {'obj_id': dup[0], 'pkg_id': dup[1]}
                ).fetchall()
                
                for detail in details:
                    logger.warning(f"    id={detail[0]}, uuid={detail[1]}, "
                                 f"name={detail[2]}, version_uuid={detail[3]}")
        else:
            logger.info("✓ No duplicates found!")
