"""
Test script to verify the complete workflow functionality.

This script tests:
1. Session status transitions from 'ready' to 'in_progress' when first change is reviewed/skipped
2. Complete button appears when all changes are reviewed/skipped
3. Session status transitions to 'completed' when complete endpoint is called
"""

import sys
from app import create_app
from models import db, MergeSession, Change
from services.change_action_service import ChangeActionService
from core.dependency_container import DependencyContainer

def test_complete_workflow():
    """Test the complete workflow functionality."""
    app = create_app()
    
    with app.app_context():
        # Find a test session (or create one if needed)
        session = db.session.query(MergeSession).filter_by(
            status='ready'
        ).first()
        
        if not session:
            print("❌ No 'ready' session found. Please create a merge session first.")
            return False
        
        print(f"✓ Found test session: {session.reference_id}")
        print(f"  Status: {session.status}")
        print(f"  Total changes: {session.total_changes}")
        print(f"  Reviewed: {session.reviewed_count}")
        print(f"  Skipped: {session.skipped_count}")
        print()
        
        # Get the first pending change
        first_change = db.session.query(Change).filter_by(
            session_id=session.id,
            status='pending'
        ).first()
        
        if not first_change:
            print("❌ No pending changes found.")
            return False
        
        print(f"✓ Found first pending change: {first_change.id}")
        print()
        
        # Test 1: Mark first change as reviewed - should move session to 'in_progress'
        print("TEST 1: Marking first change as reviewed...")
        container = DependencyContainer.get_instance()
        action_service = container.get_service(ChangeActionService)
        
        action_service.mark_as_reviewed(session.reference_id, first_change.id)
        
        # Refresh session
        db.session.refresh(session)
        
        if session.status == 'in_progress':
            print(f"✓ Session status changed to 'in_progress'")
            print(f"  Reviewed count: {session.reviewed_count}")
        else:
            print(f"❌ Session status is '{session.status}', expected 'in_progress'")
            return False
        print()
        
        # Test 2: Mark all remaining changes as reviewed or skipped
        print("TEST 2: Marking all remaining changes as reviewed/skipped...")
        pending_changes = db.session.query(Change).filter_by(
            session_id=session.id,
            status='pending'
        ).all()
        
        print(f"  Found {len(pending_changes)} pending changes")
        
        for i, change in enumerate(pending_changes):
            if i % 2 == 0:
                action_service.mark_as_reviewed(session.reference_id, change.id)
            else:
                action_service.skip_change(session.reference_id, change.id)
        
        # Refresh session
        db.session.refresh(session)
        
        completed_count = session.reviewed_count + session.skipped_count
        print(f"✓ All changes processed")
        print(f"  Reviewed: {session.reviewed_count}")
        print(f"  Skipped: {session.skipped_count}")
        print(f"  Total completed: {completed_count}/{session.total_changes}")
        
        if completed_count != session.total_changes:
            print(f"❌ Not all changes completed: {completed_count}/{session.total_changes}")
            return False
        print()
        
        # Test 3: Complete the session
        print("TEST 3: Completing the session...")
        try:
            action_service.complete_session(session.reference_id)
            
            # Refresh session
            db.session.refresh(session)
            
            if session.status == 'completed':
                print(f"✓ Session status changed to 'completed'")
            else:
                print(f"❌ Session status is '{session.status}', expected 'completed'")
                return False
        except ValueError as e:
            print(f"❌ Failed to complete session: {e}")
            return False
        print()
        
        print("=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Summary:")
        print(f"  Session: {session.reference_id}")
        print(f"  Status: {session.status}")
        print(f"  Total changes: {session.total_changes}")
        print(f"  Reviewed: {session.reviewed_count}")
        print(f"  Skipped: {session.skipped_count}")
        
        return True

if __name__ == '__main__':
    success = test_complete_workflow()
    sys.exit(0 if success else 1)
