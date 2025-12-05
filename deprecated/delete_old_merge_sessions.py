"""
Delete old merge sessions that used incorrect logic.

These sessions were created before the customer-only changes fix
and contain incomplete data (missing E \ D objects).

This script explicitly deletes all related data:
- customer_comparison_results
- delta_comparison_results
- changes
- packages
- merge_sessions
"""

from app import create_app
from models import (
    db, MergeSession, CustomerComparisonResult, 
    DeltaComparisonResult, Change, Package
)

def delete_old_sessions():
    """Delete all existing merge sessions and related data."""
    app = create_app()
    with app.app_context():
        sessions = MergeSession.query.all()
        
        if not sessions:
            print("No merge sessions found.")
            return
        
        print(f"Found {len(sessions)} existing merge sessions:")
        for session in sessions:
            print(f"  - {session.reference_id}: {session.status}, {session.total_changes} changes")
        
        print("\nDeleting old sessions and all related data...")
        
        total_deleted = {
            'customer_comparison_results': 0,
            'delta_comparison_results': 0,
            'changes': 0,
            'packages': 0,
            'sessions': 0
        }
        
        for session in sessions:
            print(f"\n  Processing {session.reference_id}...")
            
            # Delete customer comparison results
            customer_results = CustomerComparisonResult.query.filter_by(
                session_id=session.id
            ).all()
            for result in customer_results:
                db.session.delete(result)
            total_deleted['customer_comparison_results'] += len(customer_results)
            print(f"    - Deleted {len(customer_results)} customer comparison results")
            
            # Delete delta comparison results
            delta_results = DeltaComparisonResult.query.filter_by(
                session_id=session.id
            ).all()
            for result in delta_results:
                db.session.delete(result)
            total_deleted['delta_comparison_results'] += len(delta_results)
            print(f"    - Deleted {len(delta_results)} delta comparison results")
            
            # Delete changes
            changes = Change.query.filter_by(session_id=session.id).all()
            for change in changes:
                db.session.delete(change)
            total_deleted['changes'] += len(changes)
            print(f"    - Deleted {len(changes)} changes")
            
            # Delete packages
            packages = Package.query.filter_by(session_id=session.id).all()
            for package in packages:
                db.session.delete(package)
            total_deleted['packages'] += len(packages)
            print(f"    - Deleted {len(packages)} packages")
            
            # Delete session
            db.session.delete(session)
            total_deleted['sessions'] += 1
            print(f"    - Deleted session {session.reference_id}")
        
        db.session.commit()
        
        print(f"\n✓ Successfully deleted all old sessions and related data:")
        print(f"  - {total_deleted['customer_comparison_results']} customer comparison results")
        print(f"  - {total_deleted['delta_comparison_results']} delta comparison results")
        print(f"  - {total_deleted['changes']} changes")
        print(f"  - {total_deleted['packages']} packages")
        print(f"  - {total_deleted['sessions']} sessions")
        print("\nReady to create new sessions with correct logic!")

if __name__ == '__main__':
    delete_old_sessions()
