"""
Clean up duplicate (object_id, package_id) combinations in interfaces table.

This script removes duplicate entries, keeping only the first occurrence
of each (object_id, package_id) combination.
"""

from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("=" * 80)
    print("CLEANING UP DUPLICATE INTERFACES")
    print("=" * 80)
    
    # Find all duplicates
    sql = text("""
        SELECT object_id, package_id, COUNT(*) as count
        FROM interfaces
        WHERE package_id IS NOT NULL
        GROUP BY object_id, package_id
        HAVING count > 1
    """)
    
    result = db.session.execute(sql)
    duplicates = result.fetchall()
    
    if not duplicates:
        print("\n✓ No duplicates found")
        exit(0)
    
    print(f"\nFound {len(duplicates)} duplicate combinations")
    
    total_deleted = 0
    
    for dup in duplicates:
        obj_id, pkg_id, count = dup
        print(f"\nProcessing object_id={obj_id}, package_id={pkg_id} ({count} entries)...")
        
        # Get all IDs for this combination
        ids_sql = text("""
            SELECT id, uuid, name, version_uuid
            FROM interfaces
            WHERE object_id = :obj_id AND package_id = :pkg_id
            ORDER BY id ASC
        """)
        
        ids_result = db.session.execute(ids_sql, {"obj_id": obj_id, "pkg_id": pkg_id})
        entries = ids_result.fetchall()
        
        # Keep the first one, delete the rest
        keep_id = entries[0][0]
        print(f"  Keeping id={keep_id} (uuid={entries[0][1]}, name={entries[0][2]})")
        
        for entry in entries[1:]:
            entry_id = entry[0]
            print(f"  Deleting id={entry_id} (uuid={entry[1]}, name={entry[2]})")
            
            # Delete child records first (interface_parameters, interface_security)
            delete_params_sql = text("DELETE FROM interface_parameters WHERE interface_id = :id")
            db.session.execute(delete_params_sql, {"id": entry_id})
            
            delete_security_sql = text("DELETE FROM interface_security WHERE interface_id = :id")
            db.session.execute(delete_security_sql, {"id": entry_id})
            
            # Delete the interface
            delete_sql = text("DELETE FROM interfaces WHERE id = :id")
            db.session.execute(delete_sql, {"id": entry_id})
            
            total_deleted += 1
    
    # Commit changes
    db.session.commit()
    
    print("\n" + "=" * 80)
    print(f"✅ CLEANUP COMPLETE")
    print(f"   Deleted {total_deleted} duplicate entries")
    print("=" * 80)
    
    # Verify no duplicates remain
    print("\nVerifying cleanup...")
    result = db.session.execute(sql)
    remaining = result.fetchall()
    
    if remaining:
        print(f"❌ ERROR: {len(remaining)} duplicates still remain!")
    else:
        print("✓ No duplicates remain - migration can now proceed")
