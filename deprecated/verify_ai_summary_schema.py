"""
Verify AI Summary Schema Changes

Checks that the changes table has the new AI summary fields.
"""
import sys
from app import create_app
from models import db
from sqlalchemy import inspect

def verify_schema():
    """Verify that AI summary columns exist in changes table"""
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        columns = inspector.get_columns('changes')
        indexes = inspector.get_indexes('changes')
        
        print("=" * 60)
        print("AI Summary Schema Verification")
        print("=" * 60)
        
        # Check for required columns
        required_columns = {
            'ai_summary': 'TEXT',
            'ai_summary_status': 'VARCHAR(20)',
            'ai_summary_generated_at': 'DATETIME'
        }
        
        column_names = {col['name']: col for col in columns}
        
        print("\n✓ Checking columns:")
        all_columns_exist = True
        
        for col_name, expected_type in required_columns.items():
            if col_name in column_names:
                col_info = column_names[col_name]
                print(f"  ✓ {col_name}: {col_info['type']}")
            else:
                print(f"  ✗ {col_name}: MISSING")
                all_columns_exist = False
        
        # Check for index
        print("\n✓ Checking indexes:")
        index_names = [idx['name'] for idx in indexes]
        
        if 'idx_change_ai_summary_status' in index_names:
            print(f"  ✓ idx_change_ai_summary_status exists")
            index_exists = True
        else:
            print(f"  ✗ idx_change_ai_summary_status: MISSING")
            index_exists = False
        
        # Summary
        print("\n" + "=" * 60)
        if all_columns_exist and index_exists:
            print("✓ Schema verification PASSED")
            print("=" * 60)
            return True
        else:
            print("✗ Schema verification FAILED")
            print("=" * 60)
            return False

if __name__ == '__main__':
    success = verify_schema()
    sys.exit(0 if success else 1)
