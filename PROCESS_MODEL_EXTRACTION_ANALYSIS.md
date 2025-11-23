# Process Model Extraction Analysis

## Test Results Summary

**Date:** 2024-11-23  
**XML File:** `applicationArtifacts/Three Way Testing Files/V2/de199b3f-b072-4438-9508-3b6594827eaf.xml`  
**Process Model:** DGS Create Parent (UUID: de199b3f-b072-4438-9508-3b6594827eaf)

### ✅ What Works

1. **XML Parsing** - Successfully parses process model XML files
2. **Node Extraction** - Correctly extracts all 5 nodes with proper structure:
   - 1 START_NODE
   - 1 END_NODE  
   - 1 GATEWAY (XOR)
   - 2 SCRIPT_TASK nodes
3. **Flow Extraction** - Extracts all 5 flows between nodes
4. **Database Storage** - Successfully stores data in all tables:
   - `appian_objects` - Process model metadata
   - `process_model_metadata` - Counts and metrics
   - `process_model_nodes` - Individual nodes with properties
   - `process_model_flows` - Connections between nodes
5. **Data Integrity** - All relationships and foreign keys work correctly

### ❌ Issue Identified: Gateway Conditions Not Extracted

**Problem:** The XOR gateway has conditional logic that is NOT being extracted and stored in flows.

**Expected Behavior:**
- XOR gateway node (UUID: `e7bfe4ce-682a-4936-b88d-121ba36dd398`) has a rule:
  - Expression: `=pv!cancel`
  - Target node: guiId=1 (End Node)
  - Label: "Yes"
- This should create a flow with `flow_condition = "=pv!cancel"` and `flow_label = "Yes"`

**Actual Behavior:**
- All 5 flows show `flow_condition = ""` (empty)
- All flows labeled as "default"
- Conditional flows count: 0

**Root Cause:**
The `FlowExtractor` class looks for conditions in the `<connection>` element itself, but Appian stores gateway conditions in the gateway node's activity class parameters (acps) under the "rules" parameter.

## XML Structure Analysis

### Gateway Node Structure (XOR)

```xml
<node uuid="e7bfe4ce-682a-4936-b88d-121ba36dd398">
  <guiId>2</guiId>
  <fname>Cancel?</fname>
  <ac>
    <local-id>core.4</local-id>
    <name>XOR</name>
    <acps>
      <acp name="defaultNode">
        <a:value>3</a:value>  <!-- Default goes to guiId=3 -->
      </acp>
      <acp name="rules">
        <a:value xsi:type="a:Bean?list">
          <a:acps>
            <a:acp name="rule">
              <a:value xsi:type="a:Bean">
                <a:acps>
                  <a:acp name="expression">
                    <a:expr><![CDATA[=pv!cancel]]></a:expr>  <!-- CONDITION -->
                  </a:acp>
                  <a:acp name="node">
                    <a:value xsi:type="xsd:int">1</a:value>  <!-- Target guiId -->
                  </a:acp>
                  <a:acp name="label">
                    <a:value xsi:type="xsd:string">Yes</a:value>  <!-- LABEL -->
                  </a:acp>
                </a:acps>
              </a:value>
            </a:acp>
          </a:acps>
        </a:value>
      </acp>
    </acps>
  </ac>
  <connections>
    <connection>
      <guiId>4</guiId>
      <to>1</to>  <!-- Goes to guiId=1 -->
    </connection>
    <connection>
      <guiId>2</guiId>
      <to>3</to>  <!-- Goes to guiId=3 (default) -->
    </connection>
  </connections>
</node>
```

### Key Observations

1. **Conditions are in node's acps, not in connection elements**
2. **Rules map target guiId to expression and label**
3. **Default node is specified separately**
4. **Connections just specify target guiId, no condition**

## Required Fix

### Location
`services/appian_analyzer/process_model_enhancement.py` - `FlowExtractor` class

### Solution Approach

The `FlowExtractor` needs to:

1. **Extract gateway rules** when processing nodes
2. **Build a mapping** of `{from_node_uuid: {to_gui_id: {condition, label}}}`
3. **Enrich flows** with conditions when creating flow objects

### Implementation Steps

1. Add method `_extract_gateway_rules(node_elem)` to extract rules from XOR/OR gateways
2. Build gateway rules mapping during flow extraction
3. In `_extract_connection()`, check if source node is a gateway and lookup condition
4. Associate condition and label with the flow

### Pseudo-code

```python
def extract_flows(self, pm_elem: ET.Element):
    # Step 1: Build gateway rules mapping
    gateway_rules = {}  # {node_uuid: {target_gui_id: {condition, label}}}
    
    nodes_elem = pm_elem.find('nodes')
    for node_elem in nodes_elem.findall('node'):
        node_uuid = node_elem.get('uuid')
        ac_elem = node_elem.find('ac')
        
        # Check if this is a gateway (XOR, OR, AND)
        name_elem = ac_elem.find('name')
        if name_elem.text in ['XOR', 'OR', 'AND']:
            rules = self._extract_gateway_rules(ac_elem)
            gateway_rules[node_uuid] = rules
    
    # Step 2: Extract flows and enrich with conditions
    for node_elem in nodes_elem.findall('node'):
        from_uuid = node_elem.get('uuid')
        connections = node_elem.find('connections')
        
        for connection in connections.findall('connection'):
            to_gui_id = connection.find('to').text
            
            # Check if source is a gateway with rules
            if from_uuid in gateway_rules:
                rule = gateway_rules[from_uuid].get(to_gui_id, {})
                condition = rule.get('condition', '')
                label = rule.get('label', 'default')
            else:
                condition = ''
                label = 'default'
            
            flow = {
                'from_node_uuid': from_uuid,
                'to_node_uuid': to_node_uuid,
                'condition': condition,
                'label': label,
                'is_default': not bool(condition)
            }
            flows.append(flow)
```

## Impact Assessment

### Files Affected
1. `services/appian_analyzer/process_model_enhancement.py` - FlowExtractor class
2. Tests need to verify conditional flows are extracted

### Database Impact
- No schema changes needed
- `process_model_flows.flow_condition` column already exists
- `process_model_flows.flow_label` column already exists

### Backward Compatibility
- Existing code will continue to work
- Enhanced extraction will populate previously empty condition fields
- No breaking changes

## Testing Recommendations

### Unit Tests
1. Test `_extract_gateway_rules()` with XOR, OR, AND gateways
2. Test flow extraction with conditional and unconditional flows
3. Test default flow identification

### Integration Tests
1. Parse process model with XOR gateway
2. Verify conditional flows have non-empty `flow_condition`
3. Verify default flows are correctly identified
4. Verify database storage includes conditions

### Test Cases
- Simple XOR with 2 branches (1 conditional, 1 default)
- Complex XOR with multiple conditions
- OR gateway with multiple conditions
- AND gateway (all branches execute)
- Mixed process with multiple gateway types

## Priority

**HIGH** - This is a critical feature for process model comparison and analysis. Without conditions, users cannot understand the business logic and decision points in process flows.

## Estimated Effort

- Implementation: 2-3 hours
- Testing: 1-2 hours
- Total: 3-5 hours

## Next Steps

1. Implement `_extract_gateway_rules()` method
2. Modify `extract_flows()` to use gateway rules
3. Update `_extract_connection()` to accept and use conditions
4. Add unit tests for gateway rule extraction
5. Run integration tests with sample process models
6. Verify database storage includes conditions
7. Update documentation

## Related Files

- `services/appian_analyzer/process_model_enhancement.py` - FlowExtractor
- `services/appian_analyzer/parsers.py` - ProcessModelParser
- `models.py` - ProcessModelFlow model
- `test_process_model_extraction.py` - Extraction tests
- `test_process_model_db_storage.py` - Database tests
