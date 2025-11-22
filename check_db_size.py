#!/usr/bin/env python3
"""
Check database size and content
"""
from app import create_app
from models import db, ComparisonRequest, MergeSession
import sys

app = create_app()

with app.app_context():
    try:
        # Get counts with timeout
        print("Counting records...")
        
        # Use raw SQL for faster counting
        comparison_count = db.session.execute(
            db.text("SELECT COUNT(*) FROM comparison_requests")
        ).scalar()
        
        merge_count = db.session.execute(
            db.text("SELECT COUNT(*) FROM merge_sessions")
        ).scalar()
        
        print(f"\nRecord Counts:")
        print(f"  Comparison Requests: {comparison_count}")
        print(f"  Merge Sessions: {merge_count}")
        
        # Get size of largest records
        print(f"\nLargest Comparison Requests:")
        largest_comparisons = db.session.execute(
            db.text("""
                SELECT 
                    id,
                    reference_id,
                    LENGTH(old_app_blueprint) + LENGTH(new_app_blueprint) + LENGTH(comparison_results) as total_size
                FROM comparison_requests
                ORDER BY total_size DESC
                LIMIT 5
            """)
        ).fetchall()
        
        for row in largest_comparisons:
            size_mb = row[2] / (1024 * 1024) if row[2] else 0
            print(f"  {row[1]}: {size_mb:.2f} MB")
        
        print(f"\nLargest Merge Sessions:")
        largest_merges = db.session.execute(
            db.text("""
                SELECT 
                    id,
                    reference_id,
                    LENGTH(COALESCE(base_blueprint, '')) + 
                    LENGTH(COALESCE(customized_blueprint, '')) + 
                    LENGTH(COALESCE(new_vendor_blueprint, '')) + 
                    LENGTH(COALESCE(ordered_changes, '')) +
                    LENGTH(COALESCE(classification_results, '')) as total_size
                FROM merge_sessions
                ORDER BY total_size DESC
                LIMIT 5
            """)
        ).fetchall()
        
        for row in largest_merges:
            size_mb = row[2] / (1024 * 1024) if row[2] else 0
            print(f"  {row[1]}: {size_mb:.2f} MB")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
