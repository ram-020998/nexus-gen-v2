"""
Database Optimization Script

This script performs database optimization operations:
1. Run VACUUM to reclaim space from deleted data
2. Run ANALYZE to update query planner statistics
3. Verify database size reduction
4. Report optimization results

Requirements: 4.1
"""

import sys
import os
import time

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_size():
    """
    Get the current database file size
    
    Returns:
        int: Database size in bytes
    """
    db_path = 'instance/docflow.db'
    if os.path.exists(db_path):
        return os.path.getsize(db_path)
    return 0


def format_size(size_bytes):
    """
    Format size in bytes to human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def get_table_info():
    """
    Get information about all tables in the database
    
    Returns:
        list: List of tuples (table_name, row_count)
    """
    result = db.session.execute(text("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)).fetchall()
    
    table_info = []
    for (table_name,) in result:
        count_result = db.session.execute(
            text(f"SELECT COUNT(*) FROM {table_name}")
        ).scalar()
        table_info.append((table_name, count_result))
    
    return table_info


def get_index_info():
    """
    Get information about all indexes in the database
    
    Returns:
        list: List of tuples (index_name, table_name)
    """
    result = db.session.execute(text("""
        SELECT name, tbl_name FROM sqlite_master 
        WHERE type='index' 
        AND name NOT LIKE 'sqlite_%'
        ORDER BY tbl_name, name
    """)).fetchall()
    
    return result


def vacuum_database():
    """
    Run VACUUM to reclaim space and defragment the database
    
    VACUUM rebuilds the database file, repacking it into a minimal amount
    of disk space. This:
    - Reclaims space from deleted records
    - Defragments the database
    - Resets auto-increment counters
    - Optimizes page layout
    
    Returns:
        float: Time taken in seconds
    """
    logger.info("Running VACUUM...")
    start_time = time.time()
    
    # VACUUM must be run outside of a transaction
    db.session.commit()
    db.session.execute(text("VACUUM"))
    
    elapsed = time.time() - start_time
    logger.info(f"✅ VACUUM completed in {elapsed:.2f}s")
    return elapsed


def analyze_database():
    """
    Run ANALYZE to update query planner statistics
    
    ANALYZE gathers statistics about the contents of tables and indexes.
    These statistics are used by the query planner to choose the best
    query execution plan.
    
    Returns:
        float: Time taken in seconds
    """
    logger.info("Running ANALYZE...")
    start_time = time.time()
    
    db.session.execute(text("ANALYZE"))
    db.session.commit()
    
    elapsed = time.time() - start_time
    logger.info(f"✅ ANALYZE completed in {elapsed:.2f}s")
    return elapsed


def verify_integrity():
    """
    Verify database integrity
    
    Returns:
        bool: True if integrity check passes, False otherwise
    """
    logger.info("Verifying database integrity...")
    
    result = db.session.execute(text("PRAGMA integrity_check")).fetchone()
    
    if result and result[0] == 'ok':
        logger.info("✅ Database integrity check passed")
        return True
    else:
        logger.error(f"❌ Database integrity check failed: {result}")
        return False


def optimize_database():
    """
    Main optimization function
    
    Performs all optimization operations and reports results
    """
    logger.info("=" * 80)
    logger.info("Database Optimization")
    logger.info("=" * 80)
    logger.info("")
    
    # Get initial state
    logger.info("Collecting initial database information...")
    initial_size = get_database_size()
    logger.info(f"Initial database size: {format_size(initial_size)}")
    logger.info("")
    
    # Show table information
    logger.info("Table Information:")
    table_info = get_table_info()
    for table_name, row_count in table_info:
        logger.info(f"  {table_name}: {row_count:,} rows")
    logger.info("")
    
    # Show index information
    logger.info("Index Information:")
    index_info = get_index_info()
    current_table = None
    for index_name, table_name in index_info:
        if table_name != current_table:
            logger.info(f"  {table_name}:")
            current_table = table_name
        logger.info(f"    - {index_name}")
    logger.info("")
    
    # Verify integrity before optimization
    if not verify_integrity():
        logger.error("❌ Database integrity check failed. Aborting optimization.")
        return False
    logger.info("")
    
    # Run VACUUM
    vacuum_time = vacuum_database()
    logger.info("")
    
    # Run ANALYZE
    analyze_time = analyze_database()
    logger.info("")
    
    # Get final state
    logger.info("Collecting final database information...")
    final_size = get_database_size()
    logger.info(f"Final database size: {format_size(final_size)}")
    logger.info("")
    
    # Calculate savings
    size_reduction = initial_size - final_size
    if initial_size > 0:
        reduction_percent = (size_reduction / initial_size) * 100
    else:
        reduction_percent = 0
    
    logger.info("Optimization Results:")
    logger.info(f"  Initial size: {format_size(initial_size)}")
    logger.info(f"  Final size: {format_size(final_size)}")
    logger.info(f"  Space reclaimed: {format_size(size_reduction)}")
    logger.info(f"  Reduction: {reduction_percent:.2f}%")
    logger.info(f"  VACUUM time: {vacuum_time:.2f}s")
    logger.info(f"  ANALYZE time: {analyze_time:.2f}s")
    logger.info(f"  Total time: {vacuum_time + analyze_time:.2f}s")
    logger.info("")
    
    # Verify integrity after optimization
    if not verify_integrity():
        logger.error("❌ Database integrity check failed after optimization!")
        return False
    logger.info("")
    
    logger.info("=" * 80)
    logger.info("✅ Database optimization completed successfully")
    logger.info("=" * 80)
    
    return True


def main():
    """Main execution function"""
    app = create_app()
    
    with app.app_context():
        success = optimize_database()
        
        if not success:
            logger.error("Optimization failed")
            exit(1)


if __name__ == '__main__':
    main()
