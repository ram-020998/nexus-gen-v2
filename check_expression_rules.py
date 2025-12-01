"""Check expression_rules table for duplicates"""

from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("=" * 80)
    print("EXPRESSION_RULES TABLE ANALYSIS")
    print("=" * 80)
    
    # Count total entries
    total_sql = text("SELECT COUNT(*) FROM expression_rules")
    total_result = db.session.execute(total_sql)
    total = total_result.scalar()
    print(f"\nTotal entries: {total}")
    
    # Count entries with package_id
    with_pkg_sql = text("SELECT COUNT(*) FROM expression_rules WHERE package_id IS NOT NULL")
    with_pkg_result = db.session.execute(with_pkg_sql)
    with_pkg = with_pkg_result.scalar()
    print(f"Entries with package_id: {with_pkg}")
    
    # Count entries without package_id
    without_pkg = total - with_pkg
    print(f"Entries without package_id: {without_pkg}")
    
    # Show all entries
    print("\nAll entries:")
    all_sql = text("SELECT id, object_id, package_id, uuid, name FROM expression_rules ORDER BY object_id, package_id")
    all_result = db.session.execute(all_sql)
    entries = all_result.fetchall()
    
    for entry in entries:
        print(f"  id={entry[0]}, object_id={entry[1]}, package_id={entry[2]}, uuid={entry[3]}, name={entry[4]}")
    
    # Check for duplicates
    print("\nChecking for duplicates:")
    dup_sql = text("""
        SELECT object_id, package_id, COUNT(*) as count
        FROM expression_rules
        GROUP BY object_id, package_id
        HAVING count > 1
    """)
    dup_result = db.session.execute(dup_sql)
    duplicates = dup_result.fetchall()
    
    if duplicates:
        print(f"  ❌ Found {len(duplicates)} duplicate combinations:")
        for dup in duplicates:
            print(f"      object_id={dup[0]}, package_id={dup[1]}, count={dup[2]}")
    else:
        print("  ✓ No duplicates found")
