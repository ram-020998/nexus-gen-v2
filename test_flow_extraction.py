#!/usr/bin/env python3
"""Test flow extraction with the fixed FlowExtractor"""

import sys
import xml.etree.ElementTree as ET
from services.appian_analyzer.process_model_enhancement import FlowExtractor

# Sample process model XML with connections
xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<process_model_port xmlns="http://www.appian.com/ae/types/2009">
  <pm>
    <nodes>
      <node uuid="node-1">
        <guiId>1</guiId>
        <fname>Start Node</fname>
        <connections>
          <connection>
            <guiId>conn-1</guiId>
            <to>2</to>
          </connection>
        </connections>
      </node>
      <node uuid="node-2">
        <guiId>2</guiId>
        <fname>Task A</fname>
        <connections>
          <connection>
            <guiId>conn-2</guiId>
            <to>3</to>
            <flowLabel>if approved</flowLabel>
          </connection>
        </connections>
      </node>
      <node uuid="node-3">
        <guiId>3</guiId>
        <fname>End Node</fname>
        <connections/>
      </node>
    </nodes>
  </pm>
</process_model_port>
"""

def main():
    print("Testing FlowExtractor with fixed connection parsing...")
    print("=" * 80)
    
    # Parse XML
    root = ET.fromstring(xml_data)
    pm_elem = root.find('{http://www.appian.com/ae/types/2009}pm')
    
    # Create node lookup
    node_lookup = {
        'node-1': 'Start Node',
        'node-2': 'Task A',
        'node-3': 'End Node'
    }
    
    # Create FlowExtractor
    extractor = FlowExtractor(node_lookup, None)
    
    # Extract flows
    flows = extractor.extract_flows(pm_elem)
    
    print(f"\nExtracted {len(flows)} flows:")
    for i, flow in enumerate(flows, 1):
        print(f"\n{i}. Flow {flow['uuid']}")
        print(f"   From: {flow['from_node_name']} ({flow['from_node_uuid']})")
        print(f"   To: {flow['to_node_name']} ({flow['to_node_uuid']})")
        print(f"   Condition: {flow['condition'] or '(none)'}")
        print(f"   Is Default: {flow['is_default']}")
        print(f"   Label: {flow['label']}")
    
    # Build flow graph
    nodes = [
        {'uuid': 'node-1', 'name': 'Start Node'},
        {'uuid': 'node-2', 'name': 'Task A'},
        {'uuid': 'node-3', 'name': 'End Node'}
    ]
    
    flow_graph = extractor.build_flow_graph(nodes, flows)
    
    print(f"\n\nFlow Graph:")
    print(f"Start nodes: {flow_graph['start_nodes']}")
    print(f"End nodes: {flow_graph['end_nodes']}")
    print(f"\nNode connections:")
    for node_uuid, connections in flow_graph['node_connections'].items():
        print(f"\n  {node_uuid}:")
        print(f"    Incoming: {len(connections['incoming'])} flows")
        print(f"    Outgoing: {len(connections['outgoing'])} flows")
    
    print("\n" + "=" * 80)
    print("✅ Test completed successfully!")

if __name__ == '__main__':
    main()
