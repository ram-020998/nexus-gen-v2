# Design Document

## Overview

This design enhances the Appian Process Model visualization in the merge assistant by implementing a comprehensive XML parser that extracts structured, human-readable information from process model files. The enhancement will transform raw XML into organized node summaries, flow diagrams, and property comparisons, enabling developers to understand and implement process model changes effectively.

The solution extends the existing `ProcessModelParser` class and introduces new components for node analysis, flow graph generation, and visual rendering. All enhancements maintain backward compatibility with existing functionality.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Merge Assistant UI                        │
│  (change_detail.html - displays process model comparisons)  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Process Model Visualization Layer               │
│  • ProcessModelRenderer (formats for display)                │
│  • FlowDiagramGenerator (creates visual flow)                │
│  • NodeComparator (compares nodes between versions)          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           Enhanced Process Model Parser                      │
│  • NodeExtractor (parses node XML)                           │
│  • FlowExtractor (parses flow connections)                   │
│  • PropertyExtractor (extracts node properties)              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  Existing Infrastructure                     │
│  • AppianAnalyzer (blueprint generation)                     │
│  • ObjectLookup (UUID resolution)                            │
│  • SAILFormatter (expression formatting)                     │
│  • ThreeWayComparisonService (version comparison)            │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **Blueprint Generation Phase**
   - `AppianAnalyzer` calls `ProcessModelParser.parse()`
   - Enhanced parser extracts nodes, flows, and properties
   - `NodeExtractor` parses each node's AC element
   - `FlowExtractor` builds flow graph
   - Results stored in `ProcessModel` object with structured data

2. **Comparison Phase**
   - `ThreeWayComparisonService` compares process models
   - `NodeComparator` performs node-by-node comparison
   - Flow differences identified
   - Results include structured change details

3. **Display Phase**
   - `change_detail.html` receives comparison data
   - `ProcessModelRenderer` formats node information
   - `FlowDiagramGenerator` creates visual flow diagram
   - Interactive UI displays structured information

## Components and Interfaces

### 1. NodeExtractor

**Purpose:** Extract structured information from process model node XML elements.

**Interface:**
```python
class NodeExtractor:
    def __init__(self, object_lookup: Dict[str, Any], sail_formatter: SAILFormatter):
        """Initialize with object lookup for UUID resolution"""
        
    def extract_node(self, node_elem: ET.Element) -> Dict[str, Any]:
        """
        Extract complete node information from XML element
        
        Returns:
        {
            'uuid': str,
            'name': str,
            'type': str,  # User Input Task, Script Task, Gateway, etc.
            'properties': {
                'basic': {...},
                'assignment': {...},
                'forms': {...},
                'expressions': {...},
                'escalation': {...}
            },
            'dependencies': {
                'interfaces': [{'uuid': str, 'name': str}],
                'rules': [{'uuid': str, 'name': str}],
                'groups': [{'uuid': str, 'name': str}]
            }
        }
        """
        
    def determine_node_type(self, ac_elem: ET.Element) -> str:
        """Determine node type from AC element structure"""
        
    def extract_assignment(self, ac_elem: ET.Element) -> Dict[str, Any]:
        """Extract assignment configuration"""
        
    def extract_escalation(self, ac_elem: ET.Element) -> Dict[str, Any]:
        """Extract escalation configuration"""
        
    def extract_form_config(self, ac_elem: ET.Element) -> Dict[str, Any]:
        """Extract form/interface configuration"""
        
    def extract_expressions(self, ac_elem: ET.Element) -> Dict[str, Any]:
        """Extract all expressions (input, output, conditions)"""
```

### 2. FlowExtractor

**Purpose:** Extract and build flow graph from process model XML.

**Interface:**
```python
class FlowExtractor:
    def extract_flows(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract all flows from process model
        
        Returns:
        [
            {
                'uuid': str,
                'from_node_uuid': str,
                'to_node_uuid': str,
                'condition': str,  # Empty if unconditional
                'is_default': bool
            }
        ]
        """
        
    def build_flow_graph(
        self, 
        nodes: List[Dict[str, Any]], 
        flows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build complete flow graph structure
        
        Returns:
        {
            'start_nodes': [node_uuid],
            'end_nodes': [node_uuid],
            'node_connections': {
                node_uuid: {
                    'incoming': [flow],
                    'outgoing': [flow]
                }
            }
        }
        """
```

### 3. NodeComparator

**Purpose:** Compare nodes between process model versions.

**Interface:**
```python
class NodeComparator:
    def compare_nodes(
        self,
        base_nodes: List[Dict[str, Any]],
        target_nodes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare nodes between versions
        
        Returns:
        {
            'added': [node],
            'removed': [node],
            'modified': [
                {
                    'node': node,
                    'changes': [
                        {
                            'property': str,
                            'before': Any,
                            'after': Any
                        }
                    ]
                }
            ],
            'unchanged': [node]
        }
        """
        
    def compare_flows(
        self,
        base_flows: List[Dict[str, Any]],
        target_flows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare flows between versions"""
```

### 4. ProcessModelRenderer

**Purpose:** Format process model data for HTML display.

**Interface:**
```python
class ProcessModelRenderer:
    def render_node_summary(self, node: Dict[str, Any]) -> str:
        """Render node as HTML summary"""
        
    def render_node_comparison(
        self,
        base_node: Dict[str, Any],
        target_node: Dict[str, Any],
        changes: List[Dict[str, Any]]
    ) -> str:
        """Render node comparison as HTML"""
        
    def render_property_group(
        self,
        group_name: str,
        properties: Dict[str, Any]
    ) -> str:
        """Render property group as HTML"""
```

### 5. FlowDiagramGenerator

**Purpose:** Generate visual flow diagram data for frontend rendering.

**Interface:**
```python
class FlowDiagramGenerator:
    def generate_diagram_data(
        self,
        nodes: List[Dict[str, Any]],
        flows: List[Dict[str, Any]],
        flow_graph: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate data structure for flow diagram visualization
        
        Returns:
        {
            'nodes': [
                {
                    'id': str,
                    'label': str,
                    'type': str,
                    'properties': {...},
                    'position': {'x': int, 'y': int}  # Auto-layout
                }
            ],
            'edges': [
                {
                    'id': str,
                    'source': str,
                    'target': str,
                    'label': str,  # Condition if present
                    'type': str  # 'default' or 'conditional'
                }
            ]
        }
        """
        
    def generate_comparison_diagram(
        self,
        base_diagram: Dict[str, Any],
        target_diagram: Dict[str, Any],
        node_changes: Dict[str, Any],
        flow_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate diagram with change highlighting"""
```

## Data Models

### Enhanced ProcessModel Structure

```python
@dataclass
class ProcessModel(AppianObject):
    # Existing fields
    variables: List[Dict[str, Any]]
    nodes: List[Dict[str, Any]]  # Enhanced structure
    flows: List[Dict[str, Any]]  # Enhanced structure
    interfaces: List[Dict[str, Any]]
    rules: List[Dict[str, Any]]
    business_logic: str  # Kept for backward compatibility
    security: Dict[str, Any]
    
    # New fields
    flow_graph: Dict[str, Any]  # Complete flow graph structure
    node_summary: Dict[str, Any]  # Organized node information
```

### Enhanced Node Structure

```python
{
    'uuid': str,
    'name': str,
    'type': str,  # 'USER_INPUT_TASK', 'SCRIPT_TASK', 'GATEWAY', 'SUBPROCESS', etc.
    'properties': {
        'basic': {
            'description': str,
            'priority': str,
            'deadline': str
        },
        'assignment': {
            'type': str,  # 'USER', 'GROUP', 'EXPRESSION', 'NONE'
            'assignees': List[str],  # Resolved names
            'assignment_expression': str
        },
        'forms': {
            'interface_uuid': str,
            'interface_name': str,
            'input_mappings': Dict[str, str],
            'output_mappings': Dict[str, str]
        },
        'expressions': {
            'pre_activity': str,
            'post_activity': str,
            'output_expressions': Dict[str, str],  # variable: expression
            'conditions': Dict[str, str]
        },
        'escalation': {
            'enabled': bool,
            'escalation_time': str,
            'escalation_action': str,
            'notify_assignees': bool
        }
    },
    'dependencies': {
        'interfaces': [{'uuid': str, 'name': str}],
        'rules': [{'uuid': str, 'name': str}],
        'groups': [{'uuid': str, 'name': str}]
    }
}
```

### Flow Structure

```python
{
    'uuid': str,
    'from_node_uuid': str,
    'from_node_name': str,
    'to_node_uuid': str,
    'to_node_name': str,
    'condition': str,  # SAIL expression or empty
    'is_default': bool,
    'label': str  # Human-readable label
}
```

### Flow Graph Structure

```python
{
    'start_nodes': [str],  # UUIDs of nodes with no incoming flows
    'end_nodes': [str],  # UUIDs of nodes with no outgoing flows
    'node_connections': {
        node_uuid: {
            'incoming': [flow],
            'outgoing': [flow]
        }
    },
    'paths': [
        {
            'path_id': str,
            'nodes': [str],  # Ordered list of node UUIDs
            'description': str
        }
    ]
}
```

## Correctness Properties
## Error Handling

### XML Parsing Errors

**Strategy:** Graceful degradation with fallback to raw XML display

**Error Scenarios:**
1. **Malformed XML**: If XML parsing fails, log error and return raw XML string
2. **Missing Required Elements**: If critical elements (uuid, name) are missing, skip the node but continue parsing others
3. **Invalid Node Structure**: If AC element is malformed, extract what's available and mark as "partial extraction"
4. **UUID Resolution Failure**: If UUID cannot be resolved, display UUID with "Unknown" label

**Implementation:**
```python
try:
    node = extract_node(node_elem)
except XMLParseError as e:
    logger.error(f"Failed to parse node: {e}")
    return {
        'uuid': 'unknown',
        'name': 'Parse Error',
        'type': 'UNKNOWN',
        'raw_xml': ET.tostring(node_elem),
        'error': str(e)
    }
```

### Comparison Errors

**Strategy:** Continue comparison with partial results

**Error Scenarios:**
1. **Missing Nodes in Lookup**: If node UUID not found in either version, mark as orphaned
2. **Property Comparison Failure**: If property comparison fails, log and continue with other properties
3. **Flow Graph Construction Failure**: If flow graph cannot be built, provide node list without graph structure

### Display Errors

**Strategy:** Show error message with option to view raw data

**Error Scenarios:**
1. **Rendering Failure**: If HTML rendering fails, show JSON representation
2. **Diagram Generation Failure**: If diagram cannot be generated, show tabular node/flow list
3. **Large Process Models**: If process model exceeds size limits, paginate or provide download option

## Testing Strategy

### Unit Testing

**Scope:** Test individual components in isolation

**Key Test Areas:**

1. **NodeExtractor Tests**
   - Test extraction of each node type (User Input Task, Script Task, Gateway, Subprocess)
   - Test handling of missing optional fields
   - Test error handling for malformed nodes
   - Test UUID resolution with mock object lookup

2. **FlowExtractor Tests**
   - Test extraction of conditional and unconditional flows
   - Test flow graph construction with various topologies (linear, branching, loops)
   - Test identification of start and end nodes
   - Test handling of disconnected nodes

3. **NodeComparator Tests**
   - Test detection of added, removed, and modified nodes
   - Test property-level diff generation
   - Test flow comparison
   - Test handling of empty or null inputs

4. **ProcessModelRenderer Tests**
   - Test HTML generation for various node types
   - Test property grouping
   - Test comparison view rendering
   - Test handling of missing data

5. **FlowDiagramGenerator Tests**
   - Test diagram data structure generation
   - Test node positioning algorithm
   - Test change highlighting in comparison diagrams
   - Test handling of complex flows

### Property-Based Testing

**Framework:** Hypothesis (Python)

**Configuration:** Minimum 100 iterations per property test

**Property Test Implementation:**

Each correctness property from the design document must be implemented as a property-based test with explicit tagging.

**Example Property Test:**
```python
from hypothesis import given, strategies as st
import hypothesis

@given(
    nodes=st.lists(
        st.fixed_dictionaries({
            'uuid': st.uuids().map(str),
            'name': st.text(min_size=1),
            'type': st.sampled_from(['USER_INPUT_TASK', 'SCRIPT_TASK', 'GATEWAY'])
        }),
        min_size=1,
        max_size=20
    )
)
@hypothesis.settings(max_examples=100)
def test_property_1_complete_node_extraction(nodes):
    """
    **Feature: process-model-visualization, Property 1: Complete node extraction**
    
    For any process model XML, parsing should extract all node elements
    and capture their UUID, name, type, and all configuration properties
    """
    # Generate XML from nodes
    xml = generate_process_model_xml(nodes)
    
    # Parse XML
    parser = ProcessModelParser()
    result = parser.parse(xml)
    
    # Verify all nodes extracted
    assert len(result.nodes) == len(nodes)
    
    # Verify each node has required fields
    for node in result.nodes:
        assert 'uuid' in node
        assert 'name' in node
        assert 'type' in node
        assert 'properties' in node
        assert isinstance(node['properties'], dict)
```

**Property Test Tagging Format:**
```python
"""
**Feature: process-model-visualization, Property {number}: {property_text}**
"""
```

**Test Data Generators:**

1. **Process Model Generator**
   - Generate random process models with varying numbers of nodes and flows
   - Include different node types in random combinations
   - Generate valid and edge-case XML structures

2. **Node Generator**
   - Generate nodes of all supported types
   - Include optional and required fields
   - Generate with and without assignments, escalations, forms

3. **Flow Generator**
   - Generate conditional and unconditional flows
   - Generate valid flow graphs (no orphaned nodes)
   - Generate edge cases (single node, no flows, circular flows)

4. **Expression Generator**
   - Generate SAIL expressions with UUID references
   - Generate expressions with Appian functions
   - Generate complex nested expressions

### Integration Testing

**Scope:** Test end-to-end workflows

**Test Scenarios:**

1. **Blueprint Generation with Enhanced Parser**
   - Upload real Appian package ZIP
   - Verify blueprint contains enhanced process model data
   - Verify backward compatibility (business_logic field present)
   - Verify all nodes and flows extracted

2. **Three-Way Comparison with Process Models**
   - Create three versions of a process model (base, customized, new vendor)
   - Run three-way comparison
   - Verify node-level changes identified
   - Verify flow changes identified
   - Verify comparison results displayable

3. **Change Detail Page Rendering**
   - Load comparison results with process model changes
   - Navigate to process model change detail page
   - Verify structured node display (not raw XML)
   - Verify flow diagram data present
   - Verify three-way comparison display

4. **Error Recovery**
   - Test with malformed process model XML
   - Verify fallback to raw XML display
   - Verify application doesn't crash
   - Verify other objects still process correctly

### Performance Testing

**Scope:** Ensure acceptable performance with large process models

**Test Cases:**

1. **Large Process Model Parsing**
   - Test with process models containing 100+ nodes
   - Measure parsing time (target: < 5 seconds)
   - Verify memory usage stays reasonable

2. **Flow Graph Construction**
   - Test with complex flow graphs (50+ nodes, 100+ flows)
   - Measure graph construction time (target: < 2 seconds)
   - Verify correctness of start/end node identification

3. **Comparison Performance**
   - Test comparison of large process models
   - Measure comparison time (target: < 10 seconds)
   - Verify all changes detected

### Test Execution Guidelines

1. **Run property-based tests with 100 iterations minimum**
2. **Use real Appian package samples for integration tests**
3. **Mock external dependencies (database, file system) in unit tests**
4. **Test both happy path and error scenarios**
5. **Verify backward compatibility with existing functionality**
6. **Test with Python 3.13 (project standard)**

### Test Coverage Goals

- **Unit Test Coverage:** > 80% of new code
- **Property Test Coverage:** All 30 correctness properties implemented
- **Integration Test Coverage:** All major workflows tested
- **Error Handling Coverage:** All identified error scenarios tested

## Implementation Notes

### Phase 1: Core Parsing Enhancement (Priority: High)

1. Implement `NodeExtractor` class
2. Enhance `ProcessModelParser` to use `NodeExtractor`
3. Implement `FlowExtractor` class
4. Update `ProcessModel` data structure
5. Write unit tests for extractors

### Phase 2: Comparison Enhancement (Priority: High)

1. Implement `NodeComparator` class
2. Update `ThreeWayComparisonService` to use enhanced node data
3. Implement flow comparison logic
4. Write unit tests for comparator

### Phase 3: Display Enhancement (Priority: Medium)

1. Implement `ProcessModelRenderer` class
2. Update `change_detail.html` template
3. Add process model-specific display sections
4. Write integration tests for display

### Phase 4: Flow Visualization (Priority: Medium)

1. Implement `FlowDiagramGenerator` class
2. Choose and integrate frontend diagram library (e.g., Mermaid.js, D3.js, or Cytoscape.js)
3. Add interactive diagram to change detail page
4. Implement change highlighting in diagrams

### Phase 5: Testing and Refinement (Priority: High)

1. Implement all property-based tests
2. Run integration tests with real data
3. Performance testing and optimization
4. Error handling refinement
5. Documentation updates

### Technology Choices

**Frontend Diagram Library Options:**

1. **Mermaid.js** (Recommended)
   - Pros: Simple syntax, no dependencies, good for static diagrams
   - Cons: Limited interactivity
   - Use case: Quick implementation, read-only diagrams

2. **Cytoscape.js**
   - Pros: Highly interactive, good layout algorithms, extensive API
   - Cons: Larger bundle size, steeper learning curve
   - Use case: Complex interactions, advanced features

3. **D3.js**
   - Pros: Maximum flexibility, powerful
   - Cons: Requires custom implementation, complex
   - Use case: Custom visualization requirements

**Recommendation:** Start with Mermaid.js for MVP, migrate to Cytoscape.js if advanced interactivity needed.

### Backward Compatibility Considerations

1. **Maintain existing `business_logic` field** - Don't remove, keep for legacy support
2. **Add new fields alongside existing ones** - `node_summary`, `flow_graph`
3. **Conditional rendering in templates** - Check for enhanced data, fall back to raw XML
4. **Version detection** - Add `parser_version` field to blueprints
5. **Migration path** - Provide utility to re-parse old blueprints with enhanced parser

### Security Considerations

1. **XML Injection Prevention** - Use safe XML parsing, validate input
2. **XSS Prevention** - Escape all user-generated content in HTML rendering
3. **Resource Limits** - Set maximum node count, flow count to prevent DoS
4. **Access Control** - Ensure process model data respects existing permissions

### Monitoring and Logging

1. **Log parsing errors** - Track which process models fail to parse
2. **Log performance metrics** - Track parsing time, comparison time
3. **Log feature usage** - Track how often enhanced display is used
4. **Alert on failures** - Notify if parser failure rate exceeds threshold
