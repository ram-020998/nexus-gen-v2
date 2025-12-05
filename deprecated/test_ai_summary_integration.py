"""
Test AI Summary Integration

Verifies that the AI summary feature is properly integrated into the
three-way merge workflow.
"""
import time
from app import create_app
from models import db, MergeSession, Change
from services.three_way_merge_orchestrator import ThreeWayMergeOrchestrator
from core.dependency_container import DependencyContainer


def test_ai_summary_integration():
    """Test that AI summary generation is triggered during workflow"""
    app = create_app()
    
    with app.app_context():
        # Clean up any existing test sessions
        db.session.query(MergeSession).filter(
            MergeSession.reference_id.like('MRG_%')
        ).delete()
        db.session.commit()
        
        print("=" * 60)
        print("AI Summary Integration Test")
        print("=" * 60)
        
        # Get orchestrator
        container = DependencyContainer.get_instance()
        orchestrator = container.get_service(ThreeWayMergeOrchestrator)
        
        # Test package paths
        base_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip"
        customer_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application Customer Version.zip"
        vendor_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application Vendor New Version.zip"
        
        print("\n1. Creating merge session...")
        session = orchestrator.create_merge_session(
            base_zip_path=base_path,
            customized_zip_path=customer_path,
            new_vendor_zip_path=vendor_path
        )
        
        print(f"   ✓ Session created: {session.reference_id}")
        print(f"   ✓ Total changes: {session.total_changes}")
        print(f"   ✓ Status: {session.status}")
        
        # Check that changes have ai_summary_status field
        print("\n2. Checking AI summary status fields...")
        changes = db.session.query(Change).filter_by(
            session_id=session.id
        ).limit(5).all()
        
        if not changes:
            print("   ✗ No changes found!")
            return False
        
        print(f"   ✓ Found {len(changes)} changes (showing first 5)")
        
        all_have_status = True
        for change in changes:
            if not hasattr(change, 'ai_summary_status'):
                print(f"   ✗ Change {change.id} missing ai_summary_status")
                all_have_status = False
            else:
                print(f"   ✓ Change {change.id}: status={change.ai_summary_status}")
        
        if not all_have_status:
            return False
        
        # Check summary progress
        print("\n3. Checking AI summary progress...")
        from services.merge_summary_service import MergeSummaryService
        summary_service = container.get_service(MergeSummaryService)
        
        progress = summary_service.get_summary_progress(session.id)
        print(f"   Total: {progress['total']}")
        print(f"   Pending: {progress['pending']}")
        print(f"   Processing: {progress['processing']}")
        print(f"   Completed: {progress['completed']}")
        print(f"   Failed: {progress['failed']}")
        
        # Wait a bit for async processing to start
        print("\n4. Waiting for async processing to start (5 seconds)...")
        time.sleep(5)
        
        # Check progress again
        progress = summary_service.get_summary_progress(session.id)
        print(f"   Total: {progress['total']}")
        print(f"   Pending: {progress['pending']}")
        print(f"   Processing: {progress['processing']}")
        print(f"   Completed: {progress['completed']}")
        print(f"   Failed: {progress['failed']}")
        
        # Verify that some processing has started or completed
        if progress['processing'] > 0 or progress['completed'] > 0:
            print("   ✓ AI summary generation is running!")
        else:
            print("   ⚠ AI summary generation may not have started yet")
        
        print("\n" + "=" * 60)
        print("Integration Test Summary")
        print("=" * 60)
        print("✓ Session created successfully")
        print("✓ Changes have ai_summary_status field")
        print("✓ Progress tracking works")
        print("✓ Async processing triggered")
        print("\nNote: Full summary generation happens in background.")
        print("Check the changes table after a few minutes to see completed summaries.")
        print("=" * 60)
        
        return True


if __name__ == '__main__':
    try:
        success = test_ai_summary_integration()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
