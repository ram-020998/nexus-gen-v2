#!/usr/bin/env python3
"""List all changes in merge session 1"""

from app import create_app
from models import db
import json

def main():
    app = create_app()
    with app.app_context():
        # Get merge session 1
        result = db.session.execute(
            db.text("""
                SELECT id, reference_id, vendor_changes 
                FROM merge_sessions 
                WHERE id = 1
            """)
        ).fetchone()
        
        if not result:
            print('Merge session 1 not found')
            return
        
        session_id, reference_id, changes_json = result
        
        print(f'Merge Session: {reference_id}')
        print('=' * 80)
        
        if changes_json:
            changes = json.loads(changes_json)
            
            print(f'\nTotal Changes: {len(changes)}')
            print('\nAll Changes:')
            
            for i, change in enumerate(changes, 1):
                print(f'\n{i}. {change.get("name")} ({change.get("object_type")})')
                print(f'   UUID: {change.get("uuid")}')
                print(f'   Change Type: {change.get("change_type")}')
                
                # Check if it's a process model
                if change.get("object_type") == "Process Model":
                    flows = change.get('flows', [])
                    flow_graph = change.get('flow_graph', {})
                    
                    print(f'   Flows: {len(flows)}')
                    print(f'   Start nodes: {len(flow_graph.get("start_nodes", []))}')
                    print(f'   End nodes: {len(flow_graph.get("end_nodes", []))}')
                    
                    if len(flows) == 0:
                        print(f'   ⚠️  No flows extracted')
                    else:
                        print(f'   ✅ Has flows')
        else:
            print('\nNo vendor changes found')

if __name__ == '__main__':
    main()
