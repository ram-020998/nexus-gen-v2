"""Clean all merge-related data from database."""

from app import create_app
from models import db
from sqlalchemy import text

def clean_all():
    app = create_app()
    
    with app.app_context():
        print("Cleaning all merge-related data...")
        
        # Delete all data from merge tables
        tables = [
            'changes',
            'customer_comparison_results',
            'delta_comparison_results',
            'object_versions',
            'package_object_mappings',
            'interfaces',
            'expression_rules',
            'process_models',
            'record_types',
            'cdts',
            'integrations',
            'web_apis',
            'packages',
            'merge_sessions',
            'object_lookup',
        ]
        
        for table in tables:
            result = db.session.execute(text(f"DELETE FROM {table}"))
            count = result.rowcount
            if count > 0:
                print(f"  ✓ Deleted {count} rows from {table}")
        
        db.session.commit()
        
        print("\n✓ All merge data cleaned successfully")
        print("\nDatabase is now empty and ready for a fresh merge session.")

if __name__ == '__main__':
    clean_all()
