"""
Script to run the data completeness migration (migrations_003)
"""

import sys
from app import create_app
from models import db

# Import the migration module
sys.path.insert(0, 'migrations')
from migrations_003_data_completeness import upgrade, downgrade

def run_migration():
    """Run the data completeness migration"""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("Running Data Completeness Migration (003)")
        print("=" * 60)
        
        try:
            upgrade()
            print("\n" + "=" * 60)
            print("✅ Migration completed successfully!")
            print("=" * 60)
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
