"""Delete MRG_001 session and all related data."""

from app import create_app
from models import db, MergeSession

def delete_session():
    app = create_app()
    
    with app.app_context():
        session = MergeSession.query.filter_by(reference_id='MRG_001').first()
        
        if session:
            print(f"Deleting session: {session.reference_id}")
            print(f"  - ID: {session.id}")
            print(f"  - Status: {session.status}")
            print(f"  - Total changes: {session.total_changes}")
            
            # Cascade delete will handle all related data
            db.session.delete(session)
            db.session.commit()
            
            print("✓ Session deleted successfully")
        else:
            print("Session MRG_001 not found")
        
        # Show remaining data
        print("\nRemaining data:")
        print(f"  - Merge sessions: {MergeSession.query.count()}")
        print(f"  - Objects: {db.session.execute(db.text('SELECT COUNT(*) FROM object_lookup')).scalar()}")

if __name__ == '__main__':
    delete_session()
