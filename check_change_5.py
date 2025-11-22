#!/usr/bin/env python3
"""Check what's in change 5 of merge session 1"""

from app import create_app
from models import db
import json

def main():
    app = create_app()
    with app.app_context():
        # Get merge session 1
        result = db.session.execute(
            db.text("""
                SELECT id, reference_id, new_vendor_blueprint, vendor_changes 
                FROM merge_sessions 
                WHERE id = 1
            """)
        ).fetchone()
        
        if not result:
            print('Merge session 1 not found')
            return
        
        session_id, reference_id, blueprint_json, changes_json = result
        
        print(f'Merge Session: {reference_id}')
        print('=' * 80)
        
        # Parse vendor changes to find change 5
        if changes_json:
            changes = json.loads(changes_json)
            
            if len(changes) >= 5:
                change_5 = changes[4]  # 0-indexed
                print(f'\nChange 5:')
                print(f'  UUID: {change_5.get("uuid")}')
                print(f'  Name: {change_5.get("name")}')
                print(f'  Type: {change_5.get("object_type")}')
                print(f'  Change Type: {change_5.get("change_type")}')
                
                # Check if it has flows
                flows = change_5.get('flows', [])
                flow_graph = change_5.get('flow_graph', {})
                
                print(f'\n  Current Data:')
                print(f'    Flows: {len(flows)}')
                print(f'    Start nodes: {len(flow_graph.get("start_nodes", []))}')
                print(f'    End nodes: {len(flow_graph.get("end_nodes", []))}')
                
                if len(flows) == 0:
                    print(f'\n  ⚠️  This change has no flows - needs regeneration')
                else:
                    print(f'\n  ✅ Flows are present')
            else:
                print(f'\nOnly {len(changes)} changes found, change 5 does not exist')
        else:
            print('\nNo vendor changes found')

if __name__ == '__main__':
    main()
