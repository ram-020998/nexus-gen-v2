#!/usr/bin/env python3
"""
Truncate All Tables
Clears all data from all tables in the database for fresh testing.

Usage:
    python truncate_all_tables.py
    or
    ./truncate_all_tables.py
"""

from app import create_app
from models import db
import sys


def truncate_all_tables():
    """Truncate all tables in the database"""
    
    app = create_app()
    with app.app_context():
        print("Starting database truncation...")
        print("=" * 60)
        
        # Get all table names
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"Found {len(tables)} tables")
        print()
        
        try:
            # Disable foreign key constraints temporarily (SQLite specific)
            db.session.execute(db.text("PRAGMA foreign_keys = OFF"))
            
            # Truncate each table
            for table in tables:
                try:
                    # For SQLite, we use DELETE instead of TRUNCATE
                    db.session.execute(db.text(f"DELETE FROM {table}"))
                    # Reset auto-increment counter
                    db.session.execute(db.text(f"DELETE FROM sqlite_sequence WHERE name='{table}'"))
                    print(f"✓ Truncated: {table}")
                except Exception as e:
                    print(f"✗ Error truncating {table}: {str(e)}")
            
            # Re-enable foreign key constraints
            db.session.execute(db.text("PRAGMA foreign_keys = ON"))
            
            # Commit all changes
            db.session.commit()
            
            print()
            print("=" * 60)
            print("✓ All tables truncated successfully!")
            print("Database is now clean and ready for fresh testing.")
            
        except Exception as e:
            db.session.rollback()
            print()
            print("=" * 60)
            print(f"✗ Error during truncation: {str(e)}")
            sys.exit(1)


def main():
    """Main entry point"""
    print()
    response = input("⚠️  WARNING: This will delete ALL data from ALL tables. Continue? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Aborted. No changes made.")
        sys.exit(0)
    
    print()
    truncate_all_tables()


if __name__ == '__main__':
    main()

# Method 1: Direct execution
# ./truncate_all_tables.py

# Method 2: Using python
# python truncate_all_tables.py
