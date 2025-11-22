#!/usr/bin/env python3
"""Test what the template would render for change 5"""

from app import create_app
from models import db
import json

def main():
    app = create_app()
    with app.app_context():
        # Get session 1
        result = db.session.execute(
            db.text("""
                SELECT ordered_changes 
                FROM merge_sessions 
                WHERE id = 1
            """)
        ).fetchone()
        
        if not result or not result[0]:
            print('No data')
            return
        
        ordered_changes = json.loads(result[0])
        change_5 = ordered_changes[5]
        
        pm_data = change_5.get('process_model_data', {})
        
        print('Template would see:')
        print(f'  has_enhanced_data: {pm_data.get("has_enhanced_data")}')
        print(f'  node_comparison exists: {pm_data.get("node_comparison") is not None}')
        print(f'  flow_comparison exists: {pm_data.get("flow_comparison") is not None}')
        
        node_comp = pm_data.get('node_comparison', {})
        if node_comp:
            print(f'\n  node_comparison.added: {len(node_comp.get("added", []))}')
            print(f'  node_comparison.removed: {len(node_comp.get("removed", []))}')
            print(f'  node_comparison.modified: {len(node_comp.get("modified", []))}')
            print(f'  node_comparison.unchanged: {len(node_comp.get("unchanged", []))}')
        
        flow_comp = pm_data.get('flow_comparison', {})
        if flow_comp:
            print(f'\n  flow_comparison.added_flows: {len(flow_comp.get("added_flows", []))}')
            print(f'  flow_comparison.unchanged_flows: {len(flow_comp.get("unchanged_flows", []))}')
            
            # Show what Mermaid would render
            print(f'\n  Mermaid diagram would include:')
            
            # Nodes
            all_nodes = []
            all_nodes.extend(node_comp.get('added', []))
            all_nodes.extend(node_comp.get('removed', []))
            all_nodes.extend([m.get('node', {}) for m in node_comp.get('modified', [])])
            all_nodes.extend(node_comp.get('unchanged', []))
            
            print(f'    {len(all_nodes)} nodes')
            for node in all_nodes[:3]:
                print(f'      - {node.get("name")} ({node.get("type")})')
            
            # Flows
            all_flows = []
            all_flows.extend(flow_comp.get('added_flows', []))
            all_flows.extend(flow_comp.get('unchanged_flows', []))
            
            print(f'    {len(all_flows)} flows')
            for flow in all_flows[:3]:
                print(f'      - {flow.get("from_node_name")} → {flow.get("to_node_name")}')
        
        # Check if template conditions would pass
        print(f'\n  Template condition check:')
        print(f'    pm_data.node_comparison: {bool(node_comp)}')
        print(f'    Would enter node rendering: {bool(node_comp)}')
        print(f'    pm_data.flow_comparison: {bool(flow_comp)}')
        print(f'    Would enter flow rendering: {bool(flow_comp)}')

if __name__ == '__main__':
    main()
