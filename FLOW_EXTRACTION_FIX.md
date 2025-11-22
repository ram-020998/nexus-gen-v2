# Process Model Flow Extraction Fix

## Issue Summary

Process model blueprints were not capturing node connections (flows) properly. The `flow_graph` showed all nodes as disconnected with empty incoming/outgoing arrays.

### Root Cause

The `FlowExtractor` class was looking for flow connections in the wrong XML structure. Appian process models store connections in two ways:

1. **Within each node** - `node.connections.connection` elements
2. **Using guiId references** - Connections reference nodes by `guiId` (like "1", "2", "4") instead of UUIDs

The original code was only looking for:
- Direct `<flows>` elements (older Appian format)
- `<outgoing-flow>` elements within AC elements (not present in this XML structure)

It was **not** looking for `<connections>` elements within each `<node>`, which is where the actual flow data exists.

## What Was Fixed

### 1. Added guiId to UUID Mapping

The extractor now builds a mapping of `guiId` → `node UUID` before extracting flows:

```python
gui_id_to_uuid = {}
for node_elem in nodes_elem.findall('{http://www.appian.com/ae/types/2009}node'):
    node_uuid = node_elem.get('{http://www.appian.com/ae/types/2009}uuid')
    gui_id_elem = node_elem.find('{http://www.appian.com/ae/types/2009}guiId')
    if gui_id_elem is not None and gui_id_elem.text and node_uuid:
        gui_id = gui_id_elem.text.strip()
        gui_id_to_uuid[gui_id] = node_uuid
```

### 2. Extract Connections from Within Nodes

The extractor now looks for `<connections>` elements within each node:

```python
connections_elem = node_elem.find('{http://www.appian.com/ae/types/2009}connections')
if connections_elem is not None:
    connection_elems = connections_elem.findall('{http://www.appian.com/ae/types/2009}connection')
    for connection_elem in connection_elems:
        flow = self._extract_connection(connection_elem, from_uuid, from_gui_id, gui_id_to_uuid)
```

### 3. New `_extract_connection()` Method

Added a new method to handle connection elements:

```python
def _extract_connection(
    self,
    connection_elem: ET.Element,
    from_node_uuid: str,
    from_gui_id: Optional[str],
    gui_id_to_uuid: Dict[str, str]
) -> Optional[Dict[str, Any]]:
    """Extract information from a connection element within a node"""
    # Extracts:
    # - Connection guiId
    # - Target node guiId from <to> element
    # - Resolves target guiId to UUID using mapping
    # - Extracts condition from <flowLabel> or <condition>
    # - Formats condition using SAIL formatter
    # - Returns flow dictionary
```

## Example: DGS Create Parent Process Model

### Before Fix

```json
{
  "flows": [],
  "flow_graph": {
    "start_nodes": ["node-1", "node-2", "node-3", "node-4", "node-5"],
    "end_nodes": ["node-1", "node-2", "node-3", "node-4", "node-5"],
    "node_connections": {
      "node-1": {"incoming": [], "outgoing": []},
      "node-2": {"incoming": [], "outgoing": []},
      "node-3": {"incoming": [], "outgoing": []},
      "node-4": {"incoming": [], "outgoing": []},
      "node-5": {"incoming": [], "outgoing": []}
    }
  }
}
```

All nodes appear as both start and end nodes because no connections were found.

### After Fix (Expected)

```json
{
  "flows": [
    {
      "uuid": "_flow-1",
      "from_node_uuid": "1224c32f-4ad9-42f8-a14a-63704e7968b9",
      "from_node_name": "Start Node",
      "to_node_uuid": "0001eede-a3c5-8000-fe36-7f0000014e7a",
      "to_node_name": "Set Comments",
      "condition": "",
      "is_default": true,
      "label": "default"
    },
    {
      "uuid": "_flow-3",
      "from_node_uuid": "94229ce5-3367-46b1-9513-d8077584437b",
      "from_node_name": "Write Records",
      "to_node_uuid": "b18865d2-c73f-4549-86ad-e6a617b7df3f",
      "to_node_name": "End Node",
      "condition": "",
      "is_default": true,
      "label": "default"
    }
    // ... more flows
  ],
  "flow_graph": {
    "start_nodes": ["1224c32f-4ad9-42f8-a14a-63704e7968b9"],
    "end_nodes": ["b18865d2-c73f-4549-86ad-e6a617b7df3f"],
    "node_connections": {
      "1224c32f-4ad9-42f8-a14a-63704e7968b9": {
        "incoming": [],
        "outgoing": [/* flow to Set Comments */]
      },
      "0001eede-a3c5-8000-fe36-7f0000014e7a": {
        "incoming": [/* flow from Start Node */],
        "outgoing": [/* flow to End Node */]
      }
      // ... more connections
    }
  }
}
```

Proper flow graph with correct start/end nodes and connections.

## Files Modified

1. **services/appian_analyzer/process_model_enhancement.py**
   - Modified `FlowExtractor.extract_flows()` method
   - Added `FlowExtractor._extract_connection()` method
   - Added guiId to UUID mapping logic

## Testing

Created test script `test_flow_extraction.py` that verifies:
- ✅ Connections are extracted from node elements
- ✅ guiId references are resolved to UUIDs
- ✅ Flow conditions are captured
- ✅ Flow graph is built correctly with proper start/end nodes
- ✅ Node connections show correct incoming/outgoing flows

Test output:
```
Extracted 2 flows:

1. Flow _flow-conn-1
   From: Start Node (node-1)
   To: Task A (node-2)
   Condition: (none)
   Is Default: True

2. Flow _flow-conn-2
   From: Task A (node-2)
   To: End Node (node-3)
   Condition: if approved
   Is Default: False

Flow Graph:
Start nodes: ['node-1']
End nodes: ['node-3']

Node connections:
  node-1: Incoming: 0 flows, Outgoing: 1 flows
  node-2: Incoming: 1 flows, Outgoing: 1 flows
  node-3: Incoming: 1 flows, Outgoing: 0 flows
```

## Next Steps

To get the fixed flow extraction into the database, you need to:

### Option 1: Re-run Merge Comparison (Recommended)

1. Navigate to the Merge Assistant web interface
2. Upload the three package ZIP files again:
   - Base version
   - Customer version  
   - Vendor version
3. Click "Start Comparison"
4. The new comparison will use the fixed flow extraction
5. View the process model details to verify flows are present

### Option 2: Process Existing Files Programmatically

If you have the original ZIP file paths, you can process them directly:

```python
from services.appian_analyzer.analyzer import AppianAnalyzer

analyzer = AppianAnalyzer()
blueprint = analyzer.analyze_package('/path/to/package.zip')

# Blueprint will now have proper flows in process models
```

## Verification

After regenerating blueprints, verify the fix by:

1. **Query the database:**
   ```bash
   python query_merge_blueprint.py
   ```

2. **Check for flows:**
   - `flows` array should have multiple entries
   - `flow_graph.start_nodes` should have 1-2 entries (not all nodes)
   - `flow_graph.end_nodes` should have 1-2 entries (not all nodes)
   - `flow_graph.node_connections` should show incoming/outgoing flows

3. **View in UI:**
   - Navigate to process model change details
   - Flow diagram should show connected nodes
   - Node connections should be visible

## Impact

This fix enables:
- ✅ Proper process flow visualization
- ✅ Accurate identification of start and end nodes
- ✅ Flow condition display
- ✅ Path analysis through the process
- ✅ Better understanding of process logic
- ✅ Accurate three-way comparison of process flows

## Related Files

- `services/appian_analyzer/process_model_enhancement.py` - Flow extraction logic
- `services/appian_analyzer/parsers.py` - Process model parser integration
- `test_flow_extraction.py` - Unit test for flow extraction
- `debug_flows.py` - Debug script to inspect flow data
- `query_merge_blueprint.py` - Query script to view blueprint data

---

**Status:** ✅ Fixed and tested  
**Date:** 2024-11-22  
**Version:** NexusGen v2.0
