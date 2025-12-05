"""Test deleting MRG_002 session"""
from app import create_app
from models import db, MergeSession

app = create_app()

with app.app_context():
    # Find MRG_002
    session = MergeSession.query.filter_by(reference_id='MRG_002').first()
    
    if not session:
        print("MRG_002 not found")
    else:
        print(f"Found session: {session.reference_id} (ID: {session.id})")
        print(f"Status: {session.status}")
        print(f"Total changes: {session.total_changes}")
        
        # Check related records
        print(f"\nRelated records:")
        print(f"  Packages: {session.packages.count()}")
        print(f"  Delta results: {session.delta_results.count()}")
        print(f"  Customer comparison results: {session.customer_comparison_results.count()}")
        print(f"  Changes: {session.changes.count()}")
        
        # Delete
        print(f"\nDeleting session {session.reference_id}...")
        db.session.delete(session)
        db.session.commit()
        print("✓ Session deleted successfully")
