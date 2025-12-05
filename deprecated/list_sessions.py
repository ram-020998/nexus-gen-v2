"""List all merge sessions in the database."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, MergeSession


def list_sessions():
    """List all merge sessions."""
    app = create_app()
    
    with app.app_context():
        sessions = db.session.query(MergeSession).order_by(MergeSession.created_at.desc()).all()
        
        if not sessions:
            print("No merge sessions found in database.")
            return
        
        print(f"Found {len(sessions)} merge session(s):\n")
        
        for session in sessions:
            print(f"Reference ID: {session.reference_id}")
            print(f"  Status: {session.status}")
            print(f"  Total changes: {session.total_changes}")
            print(f"  Created: {session.created_at}")
            print(f"  Updated: {session.updated_at}")
            print()


if __name__ == '__main__':
    list_sessions()
