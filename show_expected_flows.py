#!/usr/bin/env python3
"""
Show the expected flow structure for DGS Create Parent based on the raw XML

This script analyzes the raw XML data to show what flows SHOULD be extracted.
"""

from app import create_app
from models import db
import json

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
                print(f'\nProcess Model: {name}')
                print(f'UUID: {obj_uuid}')
                print('\n' + '=' * 80)
                
                # Get nodes
                nodes = obj_data.get('nodes', [])
                print(f'\nNodes ({len(nodes)}):')
                
                # Build guiId to node mapping from raw XML
                raw_xml_data = obj_data.get('raw_xml_data', {})
                pm_nodes = raw_xml_data.get('process_model_port', {}).get('pm', {}).get('nodes', {}).get('node', [])
                
                gui_id_map = {}
                for node in nodes:
                    print(f'  - {node["name"]} ({node["uuid"][:8]}...)')
                
                # Extract guiId mapping from raw XML
                print(f'\n\nguiId to Node Mapping:')
                for pm_node in pm_nodes:
                    gui_id = pm_node.get('guiId', {}).get('@text', '')
                    node_uuid = pm_node.get('@attributes', {}).get('uuid', '')
                    
                    # Find node name
                    fname = pm_node.get('fname', {}).get('string-map', {}).get('pair', {}).get('value', {}).get('@text', 'Unknown')
                    
                    if gui_id and node_uuid:
                        gui_id_map[gui_id] = {'uuid': node_uuid, 'name': fname}
                        print(f'  guiId {gui_id} → {fname} ({node_uuid[:8]}...)')
                
                # Extract connections from raw XML
                print(f'\n\nExpected Flows (from raw XML connections):')
                flow_count = 0
                
                for pm_node in pm_nodes:
                    from_gui_id = pm_node.get('guiId', {}).get('@text', '')
                    from_info = gui_id_map.get(from_gui_id, {})
                    from_name = from_info.get('name', 'Unknown')
                    from_uuid = from_info.get('uuid', 'Unknown')
                    
                    connections = pm_node.get('connections', {})
                    if not connections:
                        continue
                    
                    connection_list = connections.get('connection', [])
                    if isinstance(connection_list, dict):
                        connection_list = [connection_list]
                    
                    for conn in connection_list:
                        to_gui_id = conn.get('to', {}).get('@text', '')
                        to_info = gui_id_map.get(to_gui_id, {})
                        to_name = to_info.get('name', 'Unknown')
                        to_uuid = to_info.get('uuid', 'Unknown')
                        
                        flow_label = conn.get('flowLabel', {})
                        condition = ''
                        if isinstance(flow_label, dict) and '@text' in flow_label:
                            condition = flow_label['@text']
                        
                        flow_count += 1
                        print(f'\n  Flow {flow_count}:')
                        print(f'    From: {from_name} (guiId: {from_gui_id})')
                        print(f'          UUID: {from_uuid}')
                        print(f'    To:   {to_name} (guiId: {to_gui_id})')
                        print(f'          UUID: {to_uuid}')
                        if condition:
                            print(f'    Condition: {condition}')
                        else:
                            print(f'    Condition: (none - default flow)')
                
                print(f'\n\nTotal Expected Flows: {flow_count}')
                
                # Show what the flow graph should look like
                print(f'\n\nExpected Flow Graph Structure:')
                
                # Identify start nodes (nodes with no incoming connections)
                incoming_counts = {}
                outgoing_counts = {}
                
                for node_uuid in gui_id_map.values():
                    uuid = node_uuid['uuid']
                    incoming_counts[uuid] = 0
                    outgoing_counts[uuid] = 0
                
                for pm_node in pm_nodes:
                    from_gui_id = pm_node.get('guiId', {}).get('@text', '')
                    from_info = gui_id_map.get(from_gui_id, {})
                    from_uuid = from_info.get('uuid')
                    
                    connections = pm_node.get('connections', {})
                    if not connections:
                        continue
                    
                    connection_list = connections.get('connection', [])
                    if isinstance(connection_list, dict):
                        connection_list = [connection_list]
                    
                    for conn in connection_list:
                        to_gui_id = conn.get('to', {}).get('@text', '')
                        to_info = gui_id_map.get(to_gui_id, {})
                        to_uuid = to_info.get('uuid')
                        
                        if from_uuid and to_uuid:
                            outgoing_counts[from_uuid] = outgoing_counts.get(from_uuid, 0) + 1
                            incoming_counts[to_uuid] = incoming_counts.get(to_uuid, 0) + 1
                
                start_nodes = [uuid for uuid, count in incoming_counts.items() if count == 0]
                end_nodes = [uuid for uuid, count in outgoing_counts.items() if count == 0]
                
                print(f'\n  Start Nodes ({len(start_nodes)}):')
                for uuid in start_nodes:
                    for gui_id, info in gui_id_map.items():
                        if info['uuid'] == uuid:
                            print(f'    - {info["name"]} ({uuid[:8]}...)')
                            break
                
                print(f'\n  End Nodes ({len(end_nodes)}):')
                for uuid in end_nodes:
                    for gui_id, info in gui_id_map.items():
                        if info['uuid'] == uuid:
                            print(f'    - {info["name"]} ({uuid[:8]}...)')
                            break
                
                print(f'\n  Node Connections:')
                for gui_id, info in gui_id_map.items():
                    uuid = info['uuid']
                    name = info['name']
                    incoming = incoming_counts.get(uuid, 0)
                    outgoing = outgoing_counts.get(uuid, 0)
                    print(f'    {name}:')
                    print(f'      Incoming: {incoming} flows')
                    print(f'      Outgoing: {outgoing} flows')
                
                break

if __name__ == '__main__':
    main()
