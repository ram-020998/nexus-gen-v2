"""
Cleanup corrupted data from failed merge sessions.

This script removes:
1. Orphaned customer_comparison_results with NULL session_id
2. Orphaned delta_comparison_results with NULL session_id
3. Any other orphaned data
"""

from app import create_app
from models import db
from sqlalchemy import text

def cleanup_corrupted_data():
    """Remove corrupted data from database."""
    app = create_app()
    
    with app.app_context():
        print("Starting database cleanup...")
        
        # 1. Check for corrupted customer_comparison_results
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM customer_comparison_results 
            WHERE session_id IS NULL
        """))
        count = result.scalar()
        print(f"Found {count} customer_comparison_results with NULL session_id")
        
        if count > 0:
            print("Deleting corrupted customer_comparison_results...")
            db.session.execute(text("""
                DELETE FROM customer_comparison_results 
                WHERE session_id IS NULL
            """))
            db.session.commit()
            print(f"✓ Deleted {count} corrupted customer_comparison_results")
        
        # 2. Check for corrupted delta_comparison_results
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM delta_comparison_results 
            WHERE session_id IS NULL
        """))
        count = result.scalar()
        print(f"Found {count} delta_comparison_results with NULL session_id")
        
        if count > 0:
            print("Deleting corrupted delta_comparison_results...")
            db.session.execute(text("""
                DELETE FROM delta_comparison_results 
                WHERE session_id IS NULL
            """))
            db.session.commit()
            print(f"✓ Deleted {count} corrupted delta_comparison_results")
        
        # 3. Check for corrupted changes
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM changes 
            WHERE session_id IS NULL OR object_id IS NULL
        """))
        count = result.scalar()
        print(f"Found {count} changes with NULL session_id or object_id")
        
        if count > 0:
            print("Deleting corrupted changes...")
            db.session.execute(text("""
                DELETE FROM changes 
                WHERE session_id IS NULL OR object_id IS NULL
            """))
            db.session.commit()
            print(f"✓ Deleted {count} corrupted changes")
        
        # 4. Check for orphaned package_object_mappings
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM package_object_mappings 
            WHERE package_id IS NULL OR object_id IS NULL
        """))
        count = result.scalar()
        print(f"Found {count} package_object_mappings with NULL package_id or object_id")
        
        if count > 0:
            print("Deleting corrupted package_object_mappings...")
            db.session.execute(text("""
                DELETE FROM package_object_mappings 
                WHERE package_id IS NULL OR object_id IS NULL
            """))
            db.session.commit()
            print(f"✓ Deleted {count} corrupted package_object_mappings")
        
        # 5. Summary
        print("\n" + "="*60)
        print("Database cleanup completed!")
        print("="*60)
        
        # Show current state
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM merge_sessions
        """))
        print(f"Merge sessions: {result.scalar()}")
        
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM object_lookup
        """))
        print(f"Objects in lookup: {result.scalar()}")
        
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM customer_comparison_results
        """))
        print(f"Customer comparison results: {result.scalar()}")
        
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM delta_comparison_results
        """))
        print(f"Delta comparison results: {result.scalar()}")
        
        result = db.session.execute(text("""
            SELECT COUNT(*) FROM changes
        """))
        print(f"Changes: {result.scalar()}")

if __name__ == '__main__':
    cleanup_corrupted_data()
