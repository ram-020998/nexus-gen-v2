#!/usr/bin/env python3
"""Debug flow extraction from DGS Create Parent process model"""

from app import create_app
from models import db
import json
import xml.etree.ElementTree as ET

def main():
    app = create_app()
    with app.app_context():
        result = db.session.execute(
            db.text("SELECT reference_id, new_vendor_blueprint FROM merge_sessions ORDER BY created_at DESC LIMIT 1")
        ).fetchone()
        
        if not result:
            print('No merge sessions found')
            return
        
        reference_id, blueprint_json = result
        print(f'Merge Session: {reference_id}')
        print('=' * 80)
        
        blueprint = json.loads(blueprint_json)
        obj_lookup = blueprint.get('object_lookup', {})
        
        # Find DGS Create Parent
        for obj_uuid, obj_data in obj_lookup.items():
            name = obj_data.get('name', '')
            if 'Create Parent' in name:
                print(f'\nFound: {name}')
                print(f'UUID: {obj_uuid}')
                
                # Check if raw_xml_data exists
                raw_xml_data = obj_data.get('raw_xml_data', {})
                if raw_xml_data:
                    print('\n=== Checking for flow elements in raw XML ===')
                    
                    # Look for connection elements
                    def find_connections(data, path=""):
                        if isinstance(data, dict):
                            for key, value in data.items():
                                new_path = f"{path}.{key}" if path else key
                                if 'connection' in key.lower() or 'flow' in key.lower():
                                    print(f'\nFound at {new_path}:')
                                    print(json.dumps(value, indent=2)[:500])
                                find_connections(value, new_path)
                        elif isinstance(data, list):
                            for i, item in enumerate(data):
                                find_connections(item, f"{path}[{i}]")
                    
                    find_connections(raw_xml_data)
                
                # Check flows field
                flows = obj_data.get('flows', [])
                print(f'\n=== Flows field ===')
                print(f'Number of flows: {len(flows)}')
                if flows:
                    print('Flows:')
                    for flow in flows[:5]:  # Show first 5
                        print(json.dumps(flow, indent=2))
                
                # Check flow_graph
                flow_graph = obj_data.get('flow_graph', {})
                print(f'\n=== Flow Graph ===')
                print(f'Start nodes: {flow_graph.get("start_nodes", [])}')
                print(f'End nodes: {flow_graph.get("end_nodes", [])}')
                node_connections = flow_graph.get('node_connections', {})
                print(f'Node connections: {len(node_connections)} nodes')
                
                # Show a sample connection
                for node_uuid, connections in list(node_connections.items())[:2]:
                    print(f'\nNode {node_uuid}:')
                    print(f'  Incoming: {len(connections.get("incoming", []))}')
                    print(f'  Outgoing: {len(connections.get("outgoing", []))}')
                
                break

if __name__ == '__main__':
    main()
