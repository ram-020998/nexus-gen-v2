"""
Check which objects are classified as CONFLICT in session MRG_006.
"""

from app import create_app
from models import db, Change

def main():
    app = create_app()
    
    with app.app_context():
        print("="*80)
        print("CONFLICT OBJECTS IN SESSION MRG_006")
        print("="*80)
        
        conflicts = db.session.query(Change).join(
            Change.object
        ).filter(
            Change.session_id == 6,
            Change.classification == 'CONFLICT'
        ).all()
        
        print(f"\nFound {len(conflicts)} CONFLICT objects:\n")
        
        for change in conflicts:
            print(f"Object: {change.object.name}")
            print(f"  Type: {change.object.object_type}")
            print(f"  UUID: {change.object.uuid}")
            print(f"  Vendor change: {change.vendor_change_type}")
            print(f"  Customer change: {change.customer_change_type}")
            print()

if __name__ == "__main__":
    main()
