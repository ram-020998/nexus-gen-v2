#!/usr/bin/env python3
"""Verify flows in change 5 of session 1"""

from app import create_app
from models import db
import json

def main():
    app = create_app()
    with app.app_context():
        # Get session 1
        result = db.session.execute(
            db.text("""
                SELECT id, reference_id, ordered_changes 
                FROM merge_sessions 
                WHERE id = 1
            """)
        ).fetchone()
        
        if not result:
            print('Session 1 not found')
            return
        
        session_id, reference_id, ordered_changes_json = result
        
        print(f'Merge Session: {reference_id}')
        print('=' * 80)
        
        if not ordered_changes_json:
            print('No ordered changes')
            return
        
        ordered_changes = json.loads(ordered_changes_json)
        
        print(f'\nTotal changes: {len(ordered_changes)}')
        
        if len(ordered_changes) > 5:
            change_5 = ordered_changes[5]  # 0-indexed, so index 5 is change #6
            
            print(f'\nChange at index 5 (Change #6):')
            print(f'  Name: {change_5.get("name")}')
            print(f'  Type: {change_5.get("type")}')
            print(f'  UUID: {change_5.get("uuid")}')
            
            # Check process model data
            pm_data = change_5.get('process_model_data', {})
            print(f'\n  Process Model Data:')
            print(f'    has_enhanced_data: {pm_data.get("has_enhanced_data")}')
            
            flow_graph = pm_data.get('flow_graph', {})
            if flow_graph:
                # Check if flows are in flow_graph or as separate field
                flows_in_graph = flow_graph.get('flows', [])
                print(f'    flow_graph.flows: {len(flows_in_graph)}')
                print(f'    flow_graph.start_nodes: {len(flow_graph.get("start_nodes", []))}')
                print(f'    flow_graph.end_nodes: {len(flow_graph.get("end_nodes", []))}')
            
            flow_comparison = pm_data.get('flow_comparison', {})
            if flow_comparison:
                print(f'    flow_comparison.added_flows: {len(flow_comparison.get("added_flows", []))}')
                print(f'    flow_comparison.unchanged_flows: {len(flow_comparison.get("unchanged_flows", []))}')
            
            node_comparison = pm_data.get('node_comparison', {})
            if node_comparison:
                print(f'    node_comparison.added: {len(node_comparison.get("added", []))}')
                print(f'    node_comparison.unchanged: {len(node_comparison.get("unchanged", []))}')
            
            # Show actual flow data if available
            if flow_comparison:
                added_flows = flow_comparison.get('added_flows', [])
                unchanged_flows = flow_comparison.get('unchanged_flows', [])
                
                if added_flows or unchanged_flows:
                    print(f'\n  Sample Flows:')
                    all_flows = added_flows + unchanged_flows
                    for i, flow in enumerate(all_flows[:3], 1):
                        print(f'    {i}. {flow.get("from_node_name")} → {flow.get("to_node_name")}')
                else:
                    print(f'\n  ⚠️  NO FLOWS FOUND - Blueprint needs regeneration!')

if __name__ == '__main__':
    main()
