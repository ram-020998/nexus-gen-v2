#!/usr/bin/env python3
"""
Cleanup Orphaned Data

Removes orphaned records from comparison tables when merge sessions don't exist.
"""

from app import create_app
from models import db, MergeSession, CustomerComparisonResult, DeltaComparisonResult, Change

def cleanup_orphaned_data():
    """Remove orphaned comparison results and changes."""
    app = create_app()
    
    with app.app_context():
        # Get all valid session IDs
        valid_session_ids = {s.id for s in MergeSession.query.all()}
        print(f"Valid session IDs: {valid_session_ids if valid_session_ids else 'None'}")
        
        # Find orphaned customer comparison results
        orphaned_customer = db.session.query(CustomerComparisonResult).filter(
            ~CustomerComparisonResult.session_id.in_(valid_session_ids) if valid_session_ids else True
        ).all()
        
        print(f"\nOrphaned customer comparison results: {len(orphaned_customer)}")
        if orphaned_customer:
            orphaned_sessions = {r.session_id for r in orphaned_customer}
            print(f"Orphaned session IDs: {orphaned_sessions}")
            
            # Delete orphaned customer comparison results
            for result in orphaned_customer:
                db.session.delete(result)
            print(f"Deleted {len(orphaned_customer)} orphaned customer comparison results")
        
        # Find orphaned delta comparison results
        orphaned_delta = db.session.query(DeltaComparisonResult).filter(
            ~DeltaComparisonResult.session_id.in_(valid_session_ids) if valid_session_ids else True
        ).all()
        
        print(f"\nOrphaned delta comparison results: {len(orphaned_delta)}")
        if orphaned_delta:
            # Delete orphaned delta comparison results
            for result in orphaned_delta:
                db.session.delete(result)
            print(f"Deleted {len(orphaned_delta)} orphaned delta comparison results")
        
        # Find orphaned changes
        orphaned_changes = db.session.query(Change).filter(
            ~Change.session_id.in_(valid_session_ids) if valid_session_ids else True
        ).all()
        
        print(f"\nOrphaned changes: {len(orphaned_changes)}")
        if orphaned_changes:
            # Delete orphaned changes
            for change in orphaned_changes:
                db.session.delete(change)
            print(f"Deleted {len(orphaned_changes)} orphaned changes")
        
        # Commit all deletions
        db.session.commit()
        print("\n✅ Cleanup complete!")
        
        # Verify cleanup
        print("\n--- Verification ---")
        print(f"Remaining customer comparison results: {CustomerComparisonResult.query.count()}")
        print(f"Remaining delta comparison results: {DeltaComparisonResult.query.count()}")
        print(f"Remaining changes: {Change.query.count()}")
        print(f"Total merge sessions: {MergeSession.query.count()}")

if __name__ == '__main__':
    cleanup_orphaned_data()
