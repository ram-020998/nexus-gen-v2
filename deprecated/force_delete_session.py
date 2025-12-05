"""Force delete MRG_001 session using raw SQL."""

from app import create_app
from models import db
from sqlalchemy import text

def force_delete():
    app = create_app()
    
    with app.app_context():
        print("Force deleting MRG_001 session and all related data...")
        
        # Delete tables with session_id
        session_tables = [
            'changes',
            'customer_comparison_results',
            'delta_comparison_results',
        ]
        
        for table in session_tables:
            result = db.session.execute(text(f"DELETE FROM {table} WHERE session_id = 1"))
            count = result.rowcount
            if count > 0:
                print(f"  ✓ Deleted {count} rows from {table}")
        
        # Delete tables with package_id (need to get package IDs first)
        package_tables = [
            'object_versions',
            'package_object_mappings',
            'interfaces',
            'expression_rules',
            'process_models',
            'record_types',
            'cdts',
            'integrations',
            'web_apis',
        ]
        
        for table in package_tables:
            result = db.session.execute(text(f"DELETE FROM {table} WHERE package_id IN (SELECT id FROM packages WHERE session_id = 1)"))
            count = result.rowcount
            if count > 0:
                print(f"  ✓ Deleted {count} rows from {table}")
        
        # Delete packages
        result = db.session.execute(text("DELETE FROM packages WHERE session_id = 1"))
        print(f"  ✓ Deleted {result.rowcount} packages")
        
        # Delete session
        result = db.session.execute(text("DELETE FROM merge_sessions WHERE id = 1"))
        print(f"  ✓ Deleted {result.rowcount} merge session")
        
        db.session.commit()
        
        print("\n✓ Session MRG_001 deleted successfully")
        
        # Show remaining data
        print("\nRemaining data:")
        result = db.session.execute(text("SELECT COUNT(*) FROM merge_sessions"))
        print(f"  - Merge sessions: {result.scalar()}")
        
        result = db.session.execute(text("SELECT COUNT(*) FROM object_lookup"))
        print(f"  - Objects: {result.scalar()}")
        
        result = db.session.execute(text("SELECT COUNT(*) FROM customer_comparison_results"))
        print(f"  - Customer comparisons: {result.scalar()}")

if __name__ == '__main__':
    force_delete()
