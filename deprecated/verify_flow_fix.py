"""Verify that the flow storage fix works correctly."""
from services.parsers.process_model_parser import ProcessModelParser

# Parse a real process model
parser = ProcessModelParser()
xml_path = 'applicationArtifacts/ObjectSpecificXml /processModel.xml'

data = parser.parse(xml_path)

print(f"Process Model: {data['name']}")
print(f"Total Nodes: {data['total_nodes']}")
print(f"Total Flows: {data['total_flows']}")

# Simulate the FIXED storage logic
node_map = {}
for node in data['nodes']:
    # Map both node_id (UUID) and gui_id
    node_map[node.get('node_id')] = f"db_id_{node.get('node_id')}"
    if node.get('gui_id'):
        node_map[node.get('gui_id')] = f"db_id_gui_{node.get('gui_id')}"

print(f"\nNode map has {len(node_map)} entries (should be {len(data['nodes']) * 2})")

# Test flow lookups
stored_count = 0
skipped_count = 0

for flow in data['flows']:
    from_id = node_map.get(flow.get('from_node_id'))
    to_id = node_map.get(flow.get('to_node_id'))
    
    if from_id and to_id:
        stored_count += 1
    else:
        skipped_count += 1
        print(f"✗ Flow SKIPPED: {flow['from_node_id']} -> {flow['to_node_id']}")

print(f"\n{'='*60}")
print(f"RESULT: {stored_count}/{len(data['flows'])} flows would be stored")
print(f"{'='*60}")

if stored_count == len(data['flows']):
    print("✓ SUCCESS: All flows will be stored with the fix!")
else:
    print(f"✗ FAILURE: {skipped_count} flows would still be skipped")
