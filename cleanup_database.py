#!/usr/bin/env python3
"""
Database Cleanup Script

This script cleans up the database by truncating all tables.
Useful during testing when you need to start fresh.

Usage:
    python cleanup_database.py
"""
import os
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, db
from models import MergeSession, ChangeReview, ComparisonRequest, Request


def cleanup_database():
    """Clean up all database tables"""
    print("🧹 Starting database cleanup...")
    
    with app.app_context():
        try:
            # Count records before cleanup
            merge_sessions_before = MergeSession.query.count()
            change_reviews_before = ChangeReview.query.count()
            comparison_requests_before = ComparisonRequest.query.count()
            requests_before = Request.query.count()
            
            print(f"\n📊 Current database state:")
            print(f"   - MergeSession: {merge_sessions_before} records")
            print(f"   - ChangeReview: {change_reviews_before} records")
            print(f"   - ComparisonRequest: {comparison_requests_before} records")
            print(f"   - Request: {requests_before} records")
            
            # Delete all records
            print(f"\n🗑️  Deleting records...")
            ChangeReview.query.delete()
            MergeSession.query.delete()
            ComparisonRequest.query.delete()
            Request.query.delete()
            
            # Commit changes
            db.session.commit()
            
            # Verify cleanup
            merge_sessions_after = MergeSession.query.count()
            change_reviews_after = ChangeReview.query.count()
            comparison_requests_after = ComparisonRequest.query.count()
            requests_after = Request.query.count()
            
            print(f"\n✅ Database cleanup completed!")
            print(f"\n📊 New database state:")
            print(f"   - MergeSession: {merge_sessions_after} records")
            print(f"   - ChangeReview: {change_reviews_after} records")
            print(f"   - ComparisonRequest: {comparison_requests_after} records")
            print(f"   - Request: {requests_after} records")
            
            total_deleted = (
                merge_sessions_before + change_reviews_before +
                comparison_requests_before + requests_before
            )
            print(f"\n🎉 Successfully deleted {total_deleted} total records!")
            
        except Exception as e:
            print(f"\n❌ Error during cleanup: {str(e)}")
            db.session.rollback()
            sys.exit(1)


def cleanup_uploaded_files():
    """Clean up uploaded files"""
    print("\n🧹 Cleaning up uploaded files...")
    
    upload_dirs = [
        'uploads/merge_assistant',
        'uploads'
    ]
    
    total_deleted = 0
    for upload_dir in upload_dirs:
        if os.path.exists(upload_dir):
            for file in os.listdir(upload_dir):
                file_path = os.path.join(upload_dir, file)
                if os.path.isfile(file_path) and file != '.gitkeep':
                    try:
                        os.remove(file_path)
                        total_deleted += 1
                        print(f"   - Deleted: {file_path}")
                    except Exception as e:
                        print(f"   - Failed to delete {file_path}: {str(e)}")
    
    if total_deleted > 0:
        print(f"\n✅ Deleted {total_deleted} uploaded files")
    else:
        print(f"\n✅ No uploaded files to delete")


def main():
    """Main function"""
    print("=" * 60)
    print("  DATABASE CLEANUP SCRIPT")
    print("=" * 60)
    
    # Confirm action
    response = input("\n⚠️  This will delete ALL data from the database. Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("\n❌ Cleanup cancelled.")
        sys.exit(0)
    
    # Clean up database
    cleanup_database()
    
    # Clean up uploaded files
    cleanup_uploaded_files()
    
    print("\n" + "=" * 60)
    print("  CLEANUP COMPLETE!")
    print("=" * 60)
    print("\n💡 You can now restart the application with a clean database.")


if __name__ == '__main__':
    main()
