"""
Enhanced Process Model Parsing Infrastructure

This module provides enhanced parsing capabilities for Appian Process Models,
extracting structured information about nodes, flows, and flow graphs for
better visualization and comparison.

Requirements: 9.1, 9.2
"""
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from .logger import get_logger

# Initialize logger
logger = get_logger()


class NodeType(Enum):
    """Process model node types"""
    USER_INPUT_TASK = "USER_INPUT_TASK"
    SCRIPT_TASK = "SCRIPT_TASK"
    GATEWAY = "GATEWAY"
    SUBPROCESS = "SUBPROCESS"
    START_NODE = "START_NODE"
    END_NODE = "END_NODE"
    UNKNOWN = "UNKNOWN"


class AssignmentType(Enum):
    """Assignment types for user input tasks"""
    USER = "USER"
    GROUP = "GROUP"
    EXPRESSION = "EXPRESSION"
    NONE = "NONE"


@dataclass
class NodeProperties:
    """
    Structured node properties organized by category

    This structure provides a clean separation of different types of
    node configuration for easier display and comparison.
    """
    basic: Dict[str, Any] = field(default_factory=dict)
    assignment: Dict[str, Any] = field(default_factory=dict)
    forms: Dict[str, Any] = field(default_factory=dict)
    expressions: Dict[str, Any] = field(default_factory=dict)
    escalation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NodeDependency:
    """Reference to another Appian object"""
    uuid: str
    name: str
    object_type: str = ""


@dataclass
class EnhancedNode:
    """
    Enhanced node structure with complete information

    This structure captures all relevant information about a process
    model node including its type, properties, and dependencies on
    other objects.

    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
    """
    uuid: str
    name: str
    node_type: NodeType
    properties: NodeProperties = field(default_factory=NodeProperties)
    dependencies: Dict[str, List[NodeDependency]] = field(
        default_factory=lambda: {
            'interfaces': [],
            'rules': [],
            'groups': []
        }
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'uuid': self.uuid,
            'name': self.name,
            'type': self.node_type.value,
            'properties': {
                'basic': self.properties.basic,
                'assignment': self.properties.assignment,
                'forms': self.properties.forms,
                'expressions': self.properties.expressions,
                'escalation': self.properties.escalation
            },
            'dependencies': {
                'interfaces': [
                    {
                        'uuid': d.uuid,
                        'name': d.name,
                        'object_type': d.object_type
                    }
                    for d in self.dependencies['interfaces']
                ],
                'rules': [
                    {
                        'uuid': d.uuid,
                        'name': d.name,
                        'object_type': d.object_type
                    }
                    for d in self.dependencies['rules']
                ],
                'groups': [
                    {
                        'uuid': d.uuid,
                        'name': d.name,
                        'object_type': d.object_type
                    }
                    for d in self.dependencies['groups']
                ]
            }
        }


@dataclass
class Flow:
    """
    Process flow connection between nodes

    Represents a directed edge in the process flow graph, optionally
    with a condition that determines when the flow is taken.

    Requirements: 5.1, 5.2, 5.3, 5.5
    """
    uuid: str
    from_node_uuid: str
    from_node_name: str
    to_node_uuid: str
    to_node_name: str
    condition: str = ""
    is_default: bool = False
    label: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'uuid': self.uuid,
            'from_node_uuid': self.from_node_uuid,
            'from_node_name': self.from_node_name,
            'to_node_uuid': self.to_node_uuid,
            'to_node_name': self.to_node_name,
            'condition': self.condition,
            'is_default': self.is_default,
            'label': self.label
        }


@dataclass
class FlowGraph:
    """
    Complete flow graph structure

    Represents the entire process flow as a directed graph, identifying
    start nodes, end nodes, and all connections between nodes.

    Requirements: 5.6, 5.7
    """
    start_nodes: List[str] = field(default_factory=list)
    end_nodes: List[str] = field(default_factory=list)
    node_connections: Dict[str, Dict[str, List[Flow]]] = field(
        default_factory=dict
    )
    paths: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'start_nodes': self.start_nodes,
            'end_nodes': self.end_nodes,
            'node_connections': {
                node_uuid: {
                    'incoming': [
                        f.to_dict() for f in connections['incoming']
                    ],
                    'outgoing': [
                        f.to_dict() for f in connections['outgoing']
                    ]
                }
                for node_uuid, connections in self.node_connections.items()
            },
            'paths': self.paths
        }


@dataclass
class VariableInfo:
    """
    Process variable information

    Tracks process variables including their type, usage, and whether
    they are parameters (inputs to the process).

    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    name: str
    var_type: str
    is_parameter: bool = False
    is_required: bool = False
    is_multiple: bool = False
    used_in_nodes: Set[str] = field(default_factory=set)
    modified_by_nodes: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'type': self.var_type,
            'parameter': self.is_parameter,
            'required': self.is_required,
            'multiple': self.is_multiple,
            'used_in_nodes': list(self.used_in_nodes),
            'modified_by_nodes': list(self.modified_by_nodes)
        }


@dataclass
class NodeSummary:
    """
    Organized summary of all nodes in a process model

    Groups nodes by type for easier navigation and understanding
    of the process structure.
    """
    nodes_by_type: Dict[str, List[EnhancedNode]] = field(default_factory=dict)
    total_nodes: int = 0
    node_type_counts: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'nodes_by_type': {
                node_type: [node.to_dict() for node in nodes]
                for node_type, nodes in self.nodes_by_type.items()
            },
            'total_nodes': self.total_nodes,
            'node_type_counts': self.node_type_counts
        }


@dataclass
class EnhancedProcessModel:
    """
    Enhanced process model structure with complete parsing results

    This structure extends the basic ProcessModel with enhanced node
    data, flow graphs, and variable tracking for better visualization
    and comparison.

    Requirements: 9.1, 9.2
    """
    # Basic information
    uuid: str
    name: str
    description: str = ""
    
    # Enhanced structures
    nodes: List[EnhancedNode] = field(default_factory=list)
    flows: List[Flow] = field(default_factory=list)
    flow_graph: FlowGraph = field(default_factory=FlowGraph)
    variables: List[VariableInfo] = field(default_factory=list)
    node_summary: NodeSummary = field(default_factory=NodeSummary)
    
    # Backward compatibility
    business_logic: str = ""
    security: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    version_uuid: str = ""
    raw_xml: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'uuid': self.uuid,
            'name': self.name,
            'description': self.description,
            'nodes': [node.to_dict() for node in self.nodes],
            'flows': [flow.to_dict() for flow in self.flows],
            'flow_graph': self.flow_graph.to_dict(),
            'variables': [var.to_dict() for var in self.variables],
            'node_summary': self.node_summary.to_dict(),
            'business_logic': self.business_logic,
            'security': self.security,
            'version_uuid': self.version_uuid
        }


@dataclass
class NodeComparison:
    """
    Result of comparing two nodes

    Captures the differences between two versions of a node,
    identifying which properties changed and their before/after
    values.

    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    node_uuid: str
    node_name: str
    change_type: str  # 'ADDED', 'REMOVED', 'MODIFIED', 'UNCHANGED'
    property_changes: List[Dict[str, Any]] = field(default_factory=list)
    base_node: Optional[EnhancedNode] = None
    target_node: Optional[EnhancedNode] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'node_uuid': self.node_uuid,
            'node_name': self.node_name,
            'change_type': self.change_type,
            'property_changes': self.property_changes,
            'base_node': (
                self.base_node.to_dict() if self.base_node else None
            ),
            'target_node': (
                self.target_node.to_dict() if self.target_node else None
            )
        }


@dataclass
class FlowComparison:
    """
    Result of comparing flows between versions
    
    Requirements: 5.8
    """
    added_flows: List[Flow] = field(default_factory=list)
    removed_flows: List[Flow] = field(default_factory=list)
    modified_flows: List[Dict[str, Any]] = field(default_factory=list)
    unchanged_flows: List[Flow] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'added_flows': [f.to_dict() for f in self.added_flows],
            'removed_flows': [f.to_dict() for f in self.removed_flows],
            'modified_flows': self.modified_flows,
            'unchanged_flows': [f.to_dict() for f in self.unchanged_flows]
        }


@dataclass
class ProcessModelComparison:
    """
    Complete comparison result for process models

    Combines node and flow comparisons into a single structure
    for comprehensive process model comparison.

    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.8
    """
    node_comparison: Dict[str, List[NodeComparison]] = field(
        default_factory=lambda: {
            'added': [],
            'removed': [],
            'modified': [],
            'unchanged': []
        }
    )
    flow_comparison: FlowComparison = field(default_factory=FlowComparison)
    summary: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'node_comparison': {
                change_type: [comp.to_dict() for comp in comparisons]
                for change_type, comparisons in self.node_comparison.items()
            },
            'flow_comparison': self.flow_comparison.to_dict(),
            'summary': self.summary
        }


# Logging utilities for process model parsing

def log_parsing_start(process_model_name: str, node_count: int = 0):
    """
    Log the start of process model parsing
    
    Args:
        process_model_name: Name of the process model being parsed
        node_count: Expected number of nodes (optional)
    """
    logger.info(
        f"Starting enhanced parsing for process model: "
        f"{process_model_name}"
    )
    if node_count > 0:
        logger.debug(f"Expected node count: {node_count}")


def log_parsing_complete(
    process_model_name: str, 
    nodes_parsed: int, 
    flows_parsed: int,
    parsing_time: float = 0.0
):
    """
    Log successful completion of parsing with performance metrics
    
    Args:
        process_model_name: Name of the process model
        nodes_parsed: Number of nodes successfully parsed
        flows_parsed: Number of flows successfully parsed
        parsing_time: Time taken to parse in seconds
    """
    logger.info(
        f"Completed parsing for {process_model_name}: "
        f"{nodes_parsed} nodes, {flows_parsed} flows"
    )
    if parsing_time > 0:
        logger.info(f"Parsing time: {parsing_time:.2f}s")
        if nodes_parsed > 0:
            avg_time = (parsing_time / nodes_parsed) * 1000
            logger.debug(f"Average time per node: {avg_time:.2f}ms")


def log_parsing_error(
    process_model_name: str, error: Exception, context: str = ""
):
    """
    Log parsing errors with context
    
    Args:
        process_model_name: Name of the process model
        error: Exception that occurred
        context: Additional context about where the error occurred
    """
    error_msg = f"Error parsing process model {process_model_name}"
    if context:
        error_msg += f" ({context})"
    error_msg += f": {str(error)}"
    logger.error(error_msg, exc_info=True)


def log_node_extraction(node_name: str, node_type: NodeType):
    """
    Log individual node extraction
    
    Args:
        node_name: Name of the extracted node
        node_type: Type of the node
    """
    logger.debug(f"Extracted node: {node_name} (type: {node_type.value})")


def log_flow_extraction(
    from_node: str, to_node: str, has_condition: bool
):
    """
    Log individual flow extraction
    
    Args:
        from_node: Source node name
        to_node: Target node name
        has_condition: Whether the flow has a condition
    """
    condition_str = "conditional" if has_condition else "unconditional"
    logger.debug(f"Extracted flow: {from_node} -> {to_node} ({condition_str})")


def log_uuid_resolution(
    uuid: str, resolved_name: str, object_type: str
):
    """
    Log successful UUID resolution
    
    Args:
        uuid: UUID that was resolved
        resolved_name: Resolved object name
        object_type: Type of the resolved object
    """
    logger.debug(f"Resolved UUID {uuid} to {resolved_name} ({object_type})")


def log_uuid_resolution_failure(uuid: str, context: str = ""):
    """
    Log UUID resolution failures
    
    Args:
        uuid: UUID that failed to resolve
        context: Context where the resolution was attempted
    """
    msg = f"Failed to resolve UUID: {uuid}"
    if context:
        msg += f" in {context}"
    logger.warning(msg)


def log_fallback_to_raw_xml(process_model_name: str, reason: str):
    """
    Log when falling back to raw XML display
    
    Args:
        process_model_name: Name of the process model
        reason: Reason for fallback
    """
    logger.warning(
        f"Falling back to raw XML for {process_model_name}: {reason}"
    )


def log_performance_metrics(
    operation: str,
    duration: float,
    item_count: int = 0,
    details: Dict[str, Any] = None
):
    """
    Log performance metrics for monitoring
    
    Args:
        operation: Name of the operation (e.g., "node_extraction", "flow_graph_build")
        duration: Duration in seconds
        item_count: Number of items processed
        details: Additional performance details
    """
    metrics = {
        'operation': operation,
        'duration_seconds': f"{duration:.3f}",
        'duration_ms': f"{duration * 1000:.1f}"
    }
    
    if item_count > 0:
        metrics['item_count'] = item_count
        metrics['items_per_second'] = f"{item_count / duration:.1f}"
    
    if details:
        metrics.update(details)
    
    metric_str = ", ".join(f"{k}={v}" for k, v in metrics.items())
    logger.info(f"Performance: {metric_str}")


def log_feature_usage(feature: str, details: Dict[str, Any] = None):
    """
    Log feature usage for analytics
    
    Args:
        feature: Name of the feature being used
        details: Additional usage details
    """
    usage_str = f"Feature used: {feature}"
    if details:
        detail_str = ", ".join(f"{k}={v}" for k, v in details.items())
        usage_str += f" | {detail_str}"
    logger.info(usage_str)


def log_comparison_metrics(
    process_model_name: str,
    nodes_added: int,
    nodes_removed: int,
    nodes_modified: int,
    flows_added: int,
    flows_removed: int,
    flows_modified: int,
    comparison_time: float = 0.0
):
    """
    Log comparison metrics for monitoring
    
    Args:
        process_model_name: Name of the process model
        nodes_added: Number of nodes added
        nodes_removed: Number of nodes removed
        nodes_modified: Number of nodes modified
        flows_added: Number of flows added
        flows_removed: Number of flows removed
        flows_modified: Number of flows modified
        comparison_time: Time taken for comparison in seconds
    """
    total_changes = (
        nodes_added + nodes_removed + nodes_modified +
        flows_added + flows_removed + flows_modified
    )
    
    logger.info(
        f"Comparison metrics for {process_model_name}: "
        f"{total_changes} total changes "
        f"(nodes: +{nodes_added}/-{nodes_removed}/~{nodes_modified}, "
        f"flows: +{flows_added}/-{flows_removed}/~{flows_modified})"
    )
    
    if comparison_time > 0:
        logger.info(f"Comparison time: {comparison_time:.2f}s")


def log_diagram_generation(
    process_model_name: str,
    node_count: int,
    edge_count: int,
    generation_time: float = 0.0
):
    """
    Log diagram generation metrics
    
    Args:
        process_model_name: Name of the process model
        node_count: Number of nodes in diagram
        edge_count: Number of edges in diagram
        generation_time: Time taken to generate diagram in seconds
    """
    logger.info(
        f"Generated diagram for {process_model_name}: "
        f"{node_count} nodes, {edge_count} edges"
    )
    
    if generation_time > 0:
        logger.info(f"Diagram generation time: {generation_time:.2f}s")


# Node Extraction Classes

class NodeExtractor:
    """
    Extracts structured information from process model node XML elements
    
    This class parses node XML elements from Appian process models and
    extracts all relevant information including node type, properties,
    assignments, forms, expressions, and escalations.
    
    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4
    """
    
    def __init__(
        self,
        object_lookup: Dict[str, Any],
        sail_formatter: Optional[Any] = None
    ):
        """
        Initialize NodeExtractor with object lookup for UUID resolution
        
        Args:
            object_lookup: Dictionary mapping UUIDs to object information
            sail_formatter: SAILFormatter instance for formatting expressions
        """
        self.object_lookup = object_lookup
        self.sail_formatter = sail_formatter
        self.namespaces = {
            'a': 'http://www.appian.com/ae/types/2009',
            'xsd': 'http://www.w3.org/2001/XMLSchema'
        }
    
    def extract_node(self, node_elem: ET.Element) -> Dict[str, Any]:
        """
        Extract complete node information from XML element
        
        Parses a process model node XML element and extracts all relevant
        information including UUID, name, type, and all configuration
        properties organized by category.
        
        Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
        
        Args:
            node_elem: XML element representing a process model node
            
        Returns:
            Dictionary containing complete node information with structure:
            {
                'uuid': str,
                'name': str,
                'type': str,
                'properties': {
                    'basic': {...},
                    'assignment': {...},
                    'forms': {...},
                    'expressions': {...},
                    'escalation': {...}
                },
                'dependencies': {
                    'interfaces': [...],
                    'rules': [...],
                    'groups': [...]
                }
            }
            
        Raises:
            ValueError: If node element is missing required fields (uuid, name)
        """
        try:
            # Extract UUID from node element
            uuid = node_elem.get('{http://www.appian.com/ae/types/2009}uuid')
            if not uuid:
                uuid = node_elem.get('uuid')
            
            if not uuid:
                raise ValueError("Node element missing UUID")
            
            # Find AC (Activity Class) element which contains node configuration
            ac_elem = node_elem.find('{http://www.appian.com/ae/types/2009}ac')
            if ac_elem is None:
                ac_elem = node_elem.find('ac')
            
            if ac_elem is None:
                log_parsing_error(
                    "Unknown Node",
                    Exception("Missing AC element"),
                    f"node {uuid}"
                )
                return self._create_minimal_node(uuid, "Unknown Node")
            
            # Extract node name
            name = self._extract_node_name(ac_elem)
            if not name:
                name = f"Node {uuid[:8]}"
            
            # Determine node type (pass name for hint-based detection)
            node_type = self.determine_node_type(ac_elem, name)
            
            # Extract properties by category
            properties = NodeProperties()
            properties.basic = self._extract_basic_properties(ac_elem)
            properties.assignment = self.extract_assignment(ac_elem)
            properties.forms = self.extract_form_config(ac_elem)
            properties.expressions = self.extract_expressions(ac_elem)
            properties.escalation = self.extract_escalation(ac_elem)
            
            # Extract dependencies
            dependencies = self._extract_dependencies(ac_elem)
            
            # Create enhanced node
            enhanced_node = EnhancedNode(
                uuid=uuid,
                name=name,
                node_type=node_type,
                properties=properties,
                dependencies=dependencies
            )
            
            log_node_extraction(name, node_type)
            
            return enhanced_node.to_dict()
            
        except Exception as e:
            log_parsing_error(
                "Unknown Node",
                e,
                f"extracting node"
            )
            # Return minimal node structure on error
            return self._create_minimal_node(
                uuid if uuid else "unknown",
                "Parse Error"
            )
    
    def determine_node_type(self, ac_elem: ET.Element, node_name: str = "") -> NodeType:
        """
        Determine node type from AC element structure
        
        Analyzes the AC element structure to identify the type of process
        model node (User Input Task, Script Task, Gateway, etc.)
        
        Requirements: 1.2, 8.1, 8.2, 8.3, 8.4, 8.5
        
        Args:
            ac_elem: AC (Activity Class) XML element
            node_name: Node name for hint-based detection
            
        Returns:
            NodeType enum value indicating the node type
        """
        try:
            # First check node name for obvious indicators
            if node_name:
                name_lower = node_name.lower()
                if name_lower in ['start node', 'start', 'begin']:
                    return NodeType.START_NODE
                elif name_lower in ['end node', 'end', 'finish', 'terminate']:
                    return NodeType.END_NODE
                elif name_lower in ['xor', 'gateway', 'decision', 'branch']:
                    return NodeType.GATEWAY
            
            # Check for form configuration (User Input Task)
            form_config = ac_elem.find('{http://www.appian.com/ae/types/2009}form-config')
            if form_config is None:
                form_config = ac_elem.find('form-config')
            
            if form_config is not None:
                return NodeType.USER_INPUT_TASK
            
            # Check for subprocess reference
            subprocess_elem = ac_elem.find('{http://www.appian.com/ae/types/2009}subprocess')
            if subprocess_elem is None:
                subprocess_elem = ac_elem.find('subprocess')
            
            if subprocess_elem is not None:
                return NodeType.SUBPROCESS
            
            # Check for gateway indicators (branching conditions)
            # Gateways typically have multiple outgoing flows with conditions
            # Look for gateway-specific elements
            gateway_type = ac_elem.find('{http://www.appian.com/ae/types/2009}gateway-type')
            if gateway_type is None:
                gateway_type = ac_elem.find('gateway-type')
            
            if gateway_type is not None:
                return NodeType.GATEWAY
            
            # Check for start/end node indicators in AC element
            node_class = ac_elem.get('class')
            if node_class:
                if 'start' in node_class.lower():
                    return NodeType.START_NODE
                elif 'end' in node_class.lower():
                    return NodeType.END_NODE
            
            # Check for expressions (Script Task) - do this last
            output_exprs = ac_elem.find('{http://www.appian.com/ae/types/2009}output-exprs')
            if output_exprs is None:
                output_exprs = ac_elem.find('output-exprs')
            
            pre_activity = ac_elem.find('{http://www.appian.com/ae/types/2009}pre-activity')
            if pre_activity is None:
                pre_activity = ac_elem.find('pre-activity')
            
            if output_exprs is not None or pre_activity is not None:
                return NodeType.SCRIPT_TASK
            
            # Default to unknown
            return NodeType.UNKNOWN
            
        except Exception as e:
            logger.warning(f"Error determining node type: {e}")
            return NodeType.UNKNOWN
    
    def extract_assignment(self, ac_elem: ET.Element) -> Dict[str, Any]:
        """
        Extract assignment configuration from AC element
        
        Extracts information about who is assigned to complete a task,
        including users, groups, or assignment expressions.
        
        Requirements: 3.1, 3.4
        
        Args:
            ac_elem: AC (Activity Class) XML element
            
        Returns:
            Dictionary containing assignment information
        """
        assignment = {
            'type': AssignmentType.NONE.value,
            'assignees': [],
            'assignment_expression': ''
        }
        
        try:
            # Look for assignment element
            assignment_elem = ac_elem.find('{http://www.appian.com/ae/types/2009}assignment')
            if assignment_elem is None:
                assignment_elem = ac_elem.find('assignment')
            
            if assignment_elem is None:
                return assignment
            
            # Check for direct user assignment
            assignee_elem = assignment_elem.find('{http://www.appian.com/ae/types/2009}assignee')
            if assignee_elem is None:
                assignee_elem = assignment_elem.find('assignee')
            
            if assignee_elem is not None and assignee_elem.text:
                assignment['type'] = AssignmentType.USER.value
                assignment['assignees'] = [assignee_elem.text.strip()]
                return assignment
            
            # Check for group assignment
            group_elem = assignment_elem.find('{http://www.appian.com/ae/types/2009}group')
            if group_elem is None:
                group_elem = assignment_elem.find('group')
            
            if group_elem is not None:
                group_uuid = group_elem.text.strip() if group_elem.text else None
                if group_uuid:
                    assignment['type'] = AssignmentType.GROUP.value
                    # Resolve group UUID to name
                    group_name = self._resolve_uuid(group_uuid, 'Security Group')
                    assignment['assignees'] = [group_name]
                    return assignment
            
            # Check for expression-based assignment
            expr_elem = assignment_elem.find('{http://www.appian.com/ae/types/2009}expression')
            if expr_elem is None:
                expr_elem = assignment_elem.find('expression')
            
            if expr_elem is not None and expr_elem.text:
                assignment['type'] = AssignmentType.EXPRESSION.value
                expr_text = expr_elem.text.strip()
                # Format expression if formatter available
                if self.sail_formatter:
                    expr_text = self.sail_formatter.format_sail_code(expr_text)
                assignment['assignment_expression'] = expr_text
                return assignment
            
        except Exception as e:
            logger.warning(f"Error extracting assignment: {e}")
        
        return assignment
    
    def extract_escalation(self, ac_elem: ET.Element) -> Dict[str, Any]:
        """
        Extract escalation configuration from AC element
        
        Extracts escalation rules and timing for tasks that can escalate
        if not completed within a specified timeframe.
        
        Requirements: 3.2
        
        Args:
            ac_elem: AC (Activity Class) XML element
            
        Returns:
            Dictionary containing escalation information
        """
        escalation = {
            'enabled': False,
            'escalation_time': '',
            'escalation_action': '',
            'notify_assignees': False
        }
        
        try:
            # Look for escalation element
            escalation_elem = ac_elem.find('{http://www.appian.com/ae/types/2009}escalation')
            if escalation_elem is None:
                escalation_elem = ac_elem.find('escalation')
            
            if escalation_elem is None:
                return escalation
            
            escalation['enabled'] = True
            
            # Extract escalation time
            time_elem = escalation_elem.find('{http://www.appian.com/ae/types/2009}time')
            if time_elem is None:
                time_elem = escalation_elem.find('time')
            
            if time_elem is not None and time_elem.text:
                escalation['escalation_time'] = time_elem.text.strip()
            
            # Extract escalation action
            action_elem = escalation_elem.find('{http://www.appian.com/ae/types/2009}action')
            if action_elem is None:
                action_elem = escalation_elem.find('action')
            
            if action_elem is not None and action_elem.text:
                escalation['escalation_action'] = action_elem.text.strip()
            
            # Extract notify flag
            notify_elem = escalation_elem.find('{http://www.appian.com/ae/types/2009}notify')
            if notify_elem is None:
                notify_elem = escalation_elem.find('notify')
            
            if notify_elem is not None and notify_elem.text:
                escalation['notify_assignees'] = notify_elem.text.strip().lower() == 'true'
            
        except Exception as e:
            logger.warning(f"Error extracting escalation: {e}")
        
        return escalation
    
    def extract_form_config(self, ac_elem: ET.Element) -> Dict[str, Any]:
        """
        Extract form/interface configuration from AC element
        
        Extracts information about which interface is used for a user
        input task, including input and output mappings.
        
        Requirements: 1.4, 1.5, 2.1, 2.2
        
        Args:
            ac_elem: AC (Activity Class) XML element
            
        Returns:
            Dictionary containing form configuration information
        """
        form_config = {
            'interface_uuid': '',
            'interface_name': '',
            'input_mappings': {},
            'output_mappings': {}
        }
        
        try:
            # Look for form-config element
            form_config_elem = ac_elem.find('{http://www.appian.com/ae/types/2009}form-config')
            if form_config_elem is None:
                form_config_elem = ac_elem.find('form-config')
            
            if form_config_elem is None:
                return form_config
            
            # Extract interface UUID from uiExpressionForm
            ui_expr_form = form_config_elem.find('{http://www.appian.com/ae/types/2009}uiExpressionForm')
            if ui_expr_form is None:
                ui_expr_form = form_config_elem.find('uiExpressionForm')
            
            if ui_expr_form is not None:
                expr_elem = ui_expr_form.find('{http://www.appian.com/ae/types/2009}expression')
                if expr_elem is None:
                    expr_elem = ui_expr_form.find('expression')
                
                if expr_elem is not None and expr_elem.text:
                    # Extract UUID from expression like #"_a-uuid"
                    import re
                    uuid_match = re.search(r'#"(_a-[^"]+)"', expr_elem.text)
                    if uuid_match:
                        interface_uuid = uuid_match.group(1)
                        form_config['interface_uuid'] = interface_uuid
                        # Resolve UUID to interface name
                        form_config['interface_name'] = self._resolve_uuid(
                            interface_uuid,
                            'Interface'
                        )
            
            # Extract input mappings (parameters passed to interface)
            # These are typically in the expression itself
            # For now, we'll leave this as a placeholder for future enhancement
            
            # Extract output mappings (values returned from interface)
            # These are typically in output-exprs
            
        except Exception as e:
            logger.warning(f"Error extracting form config: {e}")
        
        return form_config
    
    def extract_expressions(self, ac_elem: ET.Element) -> Dict[str, Any]:
        """
        Extract all expressions from AC element
        
        Extracts pre-activity expressions, post-activity expressions,
        output expressions, and conditions.
        
        Requirements: 1.4, 1.5, 2.3, 2.5
        
        Args:
            ac_elem: AC (Activity Class) XML element
            
        Returns:
            Dictionary containing all expressions
        """
        expressions = {
            'pre_activity': '',
            'post_activity': '',
            'output_expressions': {},
            'conditions': {}
        }
        
        try:
            # Extract pre-activity expression
            pre_activity = ac_elem.find('{http://www.appian.com/ae/types/2009}pre-activity')
            if pre_activity is None:
                pre_activity = ac_elem.find('pre-activity')
            
            if pre_activity is not None and pre_activity.text:
                expr_text = pre_activity.text.strip()
                if self.sail_formatter:
                    expr_text = self.sail_formatter.format_sail_code(expr_text)
                expressions['pre_activity'] = expr_text
            
            # Extract post-activity expression
            post_activity = ac_elem.find('{http://www.appian.com/ae/types/2009}post-activity')
            if post_activity is None:
                post_activity = ac_elem.find('post-activity')
            
            if post_activity is not None and post_activity.text:
                expr_text = post_activity.text.strip()
                if self.sail_formatter:
                    expr_text = self.sail_formatter.format_sail_code(expr_text)
                expressions['post_activity'] = expr_text
            
            # Extract output expressions
            output_exprs = ac_elem.find('{http://www.appian.com/ae/types/2009}output-exprs')
            if output_exprs is None:
                output_exprs = ac_elem.find('output-exprs')
            
            if output_exprs is not None and output_exprs.text:
                # Parse output expressions (format: variable=expression)
                expr_text = output_exprs.text.strip()
                if self.sail_formatter:
                    expr_text = self.sail_formatter.format_sail_code(expr_text)
                # Store as single string for now, could be parsed further
                expressions['output_expressions']['raw'] = expr_text
            
        except Exception as e:
            logger.warning(f"Error extracting expressions: {e}")
        
        return expressions
    
    def track_variable_usage(
        self,
        node_uuid: str,
        ac_elem: ET.Element
    ) -> Dict[str, Set[str]]:
        """
        Track which variables are referenced in this node's expressions
        
        Analyzes all expressions in the node to identify which process
        variables are being read/referenced.
        
        Requirements: 6.3, 6.4
        
        Args:
            node_uuid: UUID of the node being analyzed
            ac_elem: AC (Activity Class) XML element
            
        Returns:
            Dictionary with 'used' and 'modified' sets of variable names
        """
        variable_usage = {
            'used': set(),
            'modified': set()
        }
        
        try:
            import re
            
            # Get all text content from the AC element
            ac_text = ET.tostring(ac_elem, encoding='unicode', method='xml')
            
            # Pattern to match process variable references
            # Appian uses pv!variableName for process variables
            pv_pattern = r'pv!(\w+)'
            
            # Find all process variable references
            pv_matches = re.findall(pv_pattern, ac_text)
            variable_usage['used'] = set(pv_matches)
            
            # Track variables modified by output expressions
            output_exprs = ac_elem.find('{http://www.appian.com/ae/types/2009}output-exprs')
            if output_exprs is None:
                output_exprs = ac_elem.find('output-exprs')
            
            if output_exprs is not None and output_exprs.text:
                expr_text = output_exprs.text.strip()
                
                # Parse output expressions to find variable assignments
                # Format is typically: pv!variable1 = expression, pv!variable2 = expression
                assignment_pattern = r'pv!(\w+)\s*='
                modified_vars = re.findall(assignment_pattern, expr_text)
                variable_usage['modified'] = set(modified_vars)
            
            logger.debug(
                f"Node {node_uuid}: uses {len(variable_usage['used'])} variables, "
                f"modifies {len(variable_usage['modified'])} variables"
            )
            
        except Exception as e:
            logger.warning(f"Error tracking variable usage for node {node_uuid}: {e}")
        
        return variable_usage
    
    def extract_node_with_variable_tracking(
        self,
        node_elem: ET.Element
    ) -> tuple[Dict[str, Any], Dict[str, Set[str]]]:
        """
        Extract node information along with variable usage tracking
        
        This is an enhanced version of extract_node that also returns
        variable usage information for tracking purposes.
        
        Requirements: 6.3, 6.4
        
        Args:
            node_elem: XML element representing a process model node
            
        Returns:
            Tuple of (node_dict, variable_usage_dict)
        """
        # Extract node information normally
        node_dict = self.extract_node(node_elem)
        
        # Track variable usage
        uuid = node_dict.get('uuid', 'unknown')
        
        # Find AC element for variable tracking
        ac_elem = node_elem.find('{http://www.appian.com/ae/types/2009}ac')
        if ac_elem is None:
            ac_elem = node_elem.find('ac')
        
        variable_usage = {'used': set(), 'modified': set()}
        if ac_elem is not None:
            variable_usage = self.track_variable_usage(uuid, ac_elem)
        
        return node_dict, variable_usage
    
    def _extract_node_name(self, ac_elem: ET.Element) -> str:
        """Extract node name from AC element"""
        name_elem = ac_elem.find('{http://www.appian.com/ae/types/2009}name')
        if name_elem is None:
            name_elem = ac_elem.find('name')
        
        if name_elem is not None and name_elem.text:
            return name_elem.text.strip()
        
        return ""
    
    def _extract_basic_properties(self, ac_elem: ET.Element) -> Dict[str, Any]:
        """Extract basic node properties"""
        basic = {}
        
        try:
            # Extract description
            desc_elem = ac_elem.find('{http://www.appian.com/ae/types/2009}description')
            if desc_elem is None:
                desc_elem = ac_elem.find('description')
            
            if desc_elem is not None and desc_elem.text:
                basic['description'] = desc_elem.text.strip()
            
            # Extract priority
            priority_elem = ac_elem.find('{http://www.appian.com/ae/types/2009}priority')
            if priority_elem is None:
                priority_elem = ac_elem.find('priority')
            
            if priority_elem is not None and priority_elem.text:
                basic['priority'] = priority_elem.text.strip()
            
            # Extract deadline
            deadline_elem = ac_elem.find('{http://www.appian.com/ae/types/2009}deadline')
            if deadline_elem is None:
                deadline_elem = ac_elem.find('deadline')
            
            if deadline_elem is not None and deadline_elem.text:
                basic['deadline'] = deadline_elem.text.strip()
            
        except Exception as e:
            logger.warning(f"Error extracting basic properties: {e}")
        
        return basic
    
    def _extract_dependencies(self, ac_elem: ET.Element) -> Dict[str, List[NodeDependency]]:
        """Extract dependencies on other objects"""
        dependencies = {
            'interfaces': [],
            'rules': [],
            'groups': []
        }
        
        try:
            # Extract all text content and look for UUID references
            import re
            ac_text = ET.tostring(ac_elem, encoding='unicode', method='xml')
            
            # Find all UUID references
            uuid_pattern = r'#"(_a-[^"]+)"'
            uuid_matches = re.findall(uuid_pattern, ac_text)
            
            for uuid in set(uuid_matches):  # Use set to avoid duplicates
                obj = self.object_lookup.get(uuid)
                if obj:
                    obj_type = obj.get('object_type', '')
                    obj_name = obj.get('name', 'Unknown')
                    
                    dependency = NodeDependency(
                        uuid=uuid,
                        name=obj_name,
                        object_type=obj_type
                    )
                    
                    if obj_type == 'Interface':
                        dependencies['interfaces'].append(dependency)
                    elif obj_type == 'Expression Rule':
                        dependencies['rules'].append(dependency)
                    elif obj_type == 'Security Group':
                        dependencies['groups'].append(dependency)
            
        except Exception as e:
            logger.warning(f"Error extracting dependencies: {e}")
        
        return dependencies
    
    def _resolve_uuid(self, uuid: str, expected_type: str = '') -> str:
        """
        Resolve UUID to object name
        
        Requirements: 2.2, 2.4, 3.3, 10.2
        
        Args:
            uuid: UUID to resolve
            expected_type: Expected object type for validation
            
        Returns:
            Resolved object name or "Unknown (uuid)" if not found
        """
        try:
            obj = self.object_lookup.get(uuid)
            if obj:
                obj_name = obj.get('name', 'Unknown')
                obj_type = obj.get('object_type', '')
                
                # Log successful resolution
                log_uuid_resolution(uuid, obj_name, obj_type)
                
                # Validate type if specified
                if expected_type and obj_type != expected_type:
                    logger.warning(
                        f"UUID {uuid} resolved to {obj_type}, "
                        f"expected {expected_type}"
                    )
                
                return obj_name
            else:
                log_uuid_resolution_failure(uuid, "object lookup")
                return f"Unknown ({uuid[:8]}...)"
                
        except Exception as e:
            logger.warning(f"Error resolving UUID {uuid}: {e}")
            return f"Unknown ({uuid[:8]}...)"
    
    def _create_minimal_node(self, uuid: str, name: str) -> Dict[str, Any]:
        """Create minimal node structure for error cases"""
        return {
            'uuid': uuid,
            'name': name,
            'type': NodeType.UNKNOWN.value,
            'properties': {
                'basic': {},
                'assignment': {},
                'forms': {},
                'expressions': {},
                'escalation': {}
            },
            'dependencies': {
                'interfaces': [],
                'rules': [],
                'groups': []
            }
        }


class VariableExtractor:
    """
    Extracts process variable information from process model XML
    
    This class parses process variable definitions and tracks their
    usage throughout the process model.
    
    Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
    """
    
    def __init__(self):
        """Initialize VariableExtractor"""
        self.namespaces = {
            'a': 'http://www.appian.com/ae/types/2009',
            'xsd': 'http://www.w3.org/2001/XMLSchema'
        }
    
    def extract_variables(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract all process variable definitions from process model XML
        
        Parses the process model to find all variable definitions including
        their name, type, and whether they are parameters (inputs).
        
        Requirements: 6.1, 6.2, 6.5
        
        Args:
            pm_elem: Process model XML element
            
        Returns:
            List of variable dictionaries with structure:
            [
                {
                    'name': str,
                    'type': str,
                    'parameter': bool,
                    'required': bool,
                    'multiple': bool,
                    'used_in_nodes': [],
                    'modified_by_nodes': []
                }
            ]
        """
        variables = []
        
        try:
            # Find variables element in process model
            variables_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}variables')
            if variables_elem is None:
                variables_elem = pm_elem.find('variables')
            
            if variables_elem is None:
                logger.debug("No variables element found in process model")
                return variables
            
            # Find all variable elements
            var_elems = variables_elem.findall('{http://www.appian.com/ae/types/2009}variable')
            if not var_elems:
                var_elems = variables_elem.findall('variable')
            
            for var_elem in var_elems:
                var_info = self._extract_single_variable(var_elem)
                if var_info:
                    variables.append(var_info)
            
            logger.info(f"Extracted {len(variables)} process variables")
            
        except Exception as e:
            log_parsing_error("Process Model", e, "extracting variables")
        
        return variables
    
    def _extract_single_variable(self, var_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Extract information from a single variable element
        
        Requirements: 6.1, 6.2, 6.5
        
        Args:
            var_elem: Variable XML element
            
        Returns:
            Variable dictionary or None if extraction fails
        """
        try:
            # Extract variable name
            name_elem = var_elem.find('{http://www.appian.com/ae/types/2009}name')
            if name_elem is None:
                name_elem = var_elem.find('name')
            
            var_name = name_elem.text.strip() if name_elem is not None and name_elem.text else None
            
            if not var_name:
                logger.warning("Variable element missing name")
                return None
            
            # Extract variable type
            type_elem = var_elem.find('{http://www.appian.com/ae/types/2009}type')
            if type_elem is None:
                type_elem = var_elem.find('type')
            
            var_type = type_elem.text.strip() if type_elem is not None and type_elem.text else "Unknown"
            
            # Check if variable is a parameter (input to process)
            is_parameter = False
            parameter_elem = var_elem.find('{http://www.appian.com/ae/types/2009}parameter')
            if parameter_elem is None:
                parameter_elem = var_elem.find('parameter')
            
            if parameter_elem is not None:
                param_text = parameter_elem.text.strip() if parameter_elem.text else "false"
                is_parameter = param_text.lower() == 'true'
            
            # Check if parameter is required
            is_required = False
            required_elem = var_elem.find('{http://www.appian.com/ae/types/2009}required')
            if required_elem is None:
                required_elem = var_elem.find('required')
            
            if required_elem is not None:
                required_text = required_elem.text.strip() if required_elem.text else "false"
                is_required = required_text.lower() == 'true'
            
            # Check if variable is multiple (array)
            is_multiple = False
            multiple_elem = var_elem.find('{http://www.appian.com/ae/types/2009}multiple')
            if multiple_elem is None:
                multiple_elem = var_elem.find('multiple')
            
            if multiple_elem is not None:
                multiple_text = multiple_elem.text.strip() if multiple_elem.text else "false"
                is_multiple = multiple_text.lower() == 'true'
            
            return {
                'name': var_name,
                'type': var_type,
                'parameter': is_parameter,
                'required': is_required,
                'multiple': is_multiple,
                'used_in_nodes': [],
                'modified_by_nodes': []
            }
            
        except Exception as e:
            logger.warning(f"Error extracting variable: {e}")
            return None
    
    def update_variable_usage(
        self,
        variables: List[Dict[str, Any]],
        node_uuid: str,
        node_name: str,
        variable_usage: Dict[str, Set[str]]
    ) -> List[Dict[str, Any]]:
        """
        Update variable usage information based on node analysis
        
        Updates the variables list to track which nodes use and modify
        each variable.
        
        Requirements: 6.3, 6.4
        
        Args:
            variables: List of variable dictionaries
            node_uuid: UUID of the node
            node_name: Name of the node
            variable_usage: Dictionary with 'used' and 'modified' sets
            
        Returns:
            Updated variables list
        """
        try:
            # Create a lookup dictionary for faster access
            var_lookup = {var['name']: var for var in variables}
            
            # Update used_in_nodes for variables referenced in this node
            for var_name in variable_usage.get('used', set()):
                if var_name in var_lookup:
                    if node_name not in var_lookup[var_name]['used_in_nodes']:
                        var_lookup[var_name]['used_in_nodes'].append(node_name)
            
            # Update modified_by_nodes for variables modified in this node
            for var_name in variable_usage.get('modified', set()):
                if var_name in var_lookup:
                    if node_name not in var_lookup[var_name]['modified_by_nodes']:
                        var_lookup[var_name]['modified_by_nodes'].append(node_name)
            
        except Exception as e:
            logger.warning(f"Error updating variable usage: {e}")
        
        return variables


class FlowExtractor:
    """
    Extracts flow information from process model XML elements
    
    This class parses flow elements from Appian process models and
    extracts information about connections between nodes, including
    conditions and flow types.
    
    Requirements: 5.1, 5.2, 5.3, 5.5, 5.6, 5.7
    """
    
    def __init__(
        self,
        node_lookup: Dict[str, str],
        sail_formatter: Optional[Any] = None
    ):
        """
        Initialize FlowExtractor with node lookup for name resolution
        
        Args:
            node_lookup: Dictionary mapping node UUIDs to node names
            sail_formatter: SAILFormatter instance for formatting conditions
        """
        self.node_lookup = node_lookup
        self.sail_formatter = sail_formatter
        self.namespaces = {
            'a': 'http://www.appian.com/ae/types/2009',
            'xsd': 'http://www.w3.org/2001/XMLSchema'
        }
    
    def extract_flows(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract all flows from process model XML
        
        Parses flow elements from the process model and extracts source node,
        target node, and optional conditions for each flow.
        
        Requirements: 5.1, 5.2, 5.3, 5.5
        
        Args:
            pm_elem: Process model XML element
            
        Returns:
            List of flow dictionaries with structure:
            [
                {
                    'uuid': str,
                    'from_node_uuid': str,
                    'from_node_name': str,
                    'to_node_uuid': str,
                    'to_node_name': str,
                    'condition': str,
                    'is_default': bool,
                    'label': str
                }
            ]
        """
        flows = []
        
        try:
            # First, build a mapping of guiId to node UUID
            # Appian uses guiId for connections, not UUIDs
            gui_id_to_uuid = {}
            nodes_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}nodes')
            if nodes_elem is None:
                nodes_elem = pm_elem.find('nodes')
            
            if nodes_elem is not None:
                for node_elem in nodes_elem.findall('{http://www.appian.com/ae/types/2009}node'):
                    if node_elem is None:
                        continue
                    
                    # Get node UUID
                    node_uuid = node_elem.get('{http://www.appian.com/ae/types/2009}uuid')
                    if not node_uuid:
                        node_uuid = node_elem.get('uuid')
                    
                    # Get guiId
                    gui_id_elem = node_elem.find('{http://www.appian.com/ae/types/2009}guiId')
                    if gui_id_elem is None:
                        gui_id_elem = node_elem.find('guiId')
                    
                    if gui_id_elem is not None and gui_id_elem.text and node_uuid:
                        gui_id = gui_id_elem.text.strip()
                        gui_id_to_uuid[gui_id] = node_uuid
            
            logger.debug(f"Built guiId to UUID mapping: {len(gui_id_to_uuid)} nodes")
            
            # Pattern 1: Extract connections from within each node
            if nodes_elem is not None:
                for node_elem in nodes_elem.findall('{http://www.appian.com/ae/types/2009}node'):
                    if node_elem is None:
                        continue
                    
                    # Get source node UUID and guiId
                    from_uuid = node_elem.get('{http://www.appian.com/ae/types/2009}uuid')
                    if not from_uuid:
                        from_uuid = node_elem.get('uuid')
                    
                    if not from_uuid:
                        continue
                    
                    # Get guiId for this node
                    gui_id_elem = node_elem.find('{http://www.appian.com/ae/types/2009}guiId')
                    if gui_id_elem is None:
                        gui_id_elem = node_elem.find('guiId')
                    
                    from_gui_id = gui_id_elem.text.strip() if gui_id_elem is not None and gui_id_elem.text else None
                    
                    # Find connections element
                    connections_elem = node_elem.find('{http://www.appian.com/ae/types/2009}connections')
                    if connections_elem is None:
                        connections_elem = node_elem.find('connections')
                    
                    if connections_elem is not None:
                        # Find connection elements (can be single or multiple)
                        connection_elems = connections_elem.findall('{http://www.appian.com/ae/types/2009}connection')
                        if not connection_elems:
                            connection_elems = connections_elem.findall('connection')
                        
                        for connection_elem in connection_elems:
                            flow = self._extract_connection(connection_elem, from_uuid, from_gui_id, gui_id_to_uuid)
                            if flow:
                                flows.append(flow)
                                log_flow_extraction(
                                    flow['from_node_name'],
                                    flow['to_node_name'],
                                    bool(flow['condition'])
                                )
            
            # Pattern 2: Direct flows element (fallback for older Appian versions)
            flows_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}flows')
            if flows_elem is None:
                flows_elem = pm_elem.find('flows')
            
            if flows_elem is not None:
                flow_elems = flows_elem.findall('{http://www.appian.com/ae/types/2009}flow')
                if not flow_elems:
                    flow_elems = flows_elem.findall('flow')
                
                for flow_elem in flow_elems:
                    flow = self._extract_single_flow(flow_elem)
                    if flow:
                        # Check if this flow is already in the list (avoid duplicates)
                        if not any(f['from_node_uuid'] == flow['from_node_uuid'] and 
                                 f['to_node_uuid'] == flow['to_node_uuid'] for f in flows):
                            flows.append(flow)
                            log_flow_extraction(
                                flow['from_node_name'],
                                flow['to_node_name'],
                                bool(flow['condition'])
                            )
            
            logger.info(f"Extracted {len(flows)} flows from process model")
            
        except Exception as e:
            log_parsing_error("Process Model", e, "extracting flows")
        
        return flows
    
    def _extract_connection(
        self,
        connection_elem: ET.Element,
        from_node_uuid: str,
        from_gui_id: Optional[str],
        gui_id_to_uuid: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """
        Extract information from a connection element within a node
        
        Args:
            connection_elem: Connection XML element
            from_node_uuid: UUID of the source node
            from_gui_id: GUI ID of the source node
            gui_id_to_uuid: Mapping of GUI IDs to node UUIDs
            
        Returns:
            Flow dictionary or None if extraction fails
        """
        try:
            # Extract connection guiId
            gui_id_elem = connection_elem.find('{http://www.appian.com/ae/types/2009}guiId')
            if gui_id_elem is None:
                gui_id_elem = connection_elem.find('guiId')
            
            connection_gui_id = gui_id_elem.text.strip() if gui_id_elem is not None and gui_id_elem.text else None
            
            # Generate flow UUID from connection guiId
            import uuid
            flow_uuid = f"_flow-{connection_gui_id}" if connection_gui_id else f"_flow-{uuid.uuid4().hex[:16]}"
            
            # Extract target node guiId
            to_elem = connection_elem.find('{http://www.appian.com/ae/types/2009}to')
            if to_elem is None:
                to_elem = connection_elem.find('to')
            
            to_gui_id = to_elem.text.strip() if to_elem is not None and to_elem.text else None
            
            if not to_gui_id:
                logger.warning(f"Connection {connection_gui_id} missing target guiId")
                return None
            
            # Resolve target guiId to UUID
            to_node_uuid = gui_id_to_uuid.get(to_gui_id)
            
            if not to_node_uuid:
                logger.warning(f"Could not resolve target guiId {to_gui_id} to UUID")
                return None
            
            # Extract condition (if present) - look for flowLabel or condition
            condition = ""
            
            # Check for flowLabel element
            flow_label_elem = connection_elem.find('{http://www.appian.com/ae/types/2009}flowLabel')
            if flow_label_elem is None:
                flow_label_elem = connection_elem.find('flowLabel')
            
            if flow_label_elem is not None and flow_label_elem.text:
                condition = flow_label_elem.text.strip()
            
            # Check for condition element (alternative location)
            if not condition:
                condition_elem = connection_elem.find('{http://www.appian.com/ae/types/2009}condition')
                if condition_elem is None:
                    condition_elem = connection_elem.find('condition')
                
                if condition_elem is not None and condition_elem.text:
                    condition = condition_elem.text.strip()
            
            # Format condition if formatter available
            if self.sail_formatter and condition:
                condition = self.sail_formatter.format_sail_code(condition)
            
            # Determine if this is a default flow (no condition)
            is_default = not bool(condition)
            
            # Resolve node names
            from_node_name = self.node_lookup.get(from_node_uuid, f"Node {from_node_uuid[:8]}")
            to_node_name = self.node_lookup.get(to_node_uuid, f"Node {to_node_uuid[:8]}")
            
            # Create label for display
            if condition:
                label = f"{condition[:50]}..." if len(condition) > 50 else condition
            else:
                label = "default"
            
            return {
                'uuid': flow_uuid,
                'from_node_uuid': from_node_uuid,
                'from_node_name': from_node_name,
                'to_node_uuid': to_node_uuid,
                'to_node_name': to_node_name,
                'condition': condition,
                'is_default': is_default,
                'label': label
            }
            
        except Exception as e:
            logger.warning(f"Error extracting connection: {e}")
            return None
    
    def _extract_single_flow(self, flow_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """
        Extract information from a single flow element
        
        Args:
            flow_elem: Flow XML element
            
        Returns:
            Flow dictionary or None if extraction fails
        """
        try:
            # Extract flow UUID
            flow_uuid = flow_elem.get('{http://www.appian.com/ae/types/2009}uuid')
            if not flow_uuid:
                flow_uuid = flow_elem.get('uuid')
            
            if not flow_uuid:
                # Generate a UUID if not present
                import uuid
                flow_uuid = f"_flow-{uuid.uuid4().hex[:16]}"
            
            # Extract source node UUID
            from_elem = flow_elem.find('{http://www.appian.com/ae/types/2009}from')
            if from_elem is None:
                from_elem = flow_elem.find('from')
            
            from_node_uuid = from_elem.text.strip() if from_elem is not None and from_elem.text else None
            
            # Extract target node UUID
            to_elem = flow_elem.find('{http://www.appian.com/ae/types/2009}to')
            if to_elem is None:
                to_elem = flow_elem.find('to')
            
            to_node_uuid = to_elem.text.strip() if to_elem is not None and to_elem.text else None
            
            if not from_node_uuid or not to_node_uuid:
                logger.warning(f"Flow {flow_uuid} missing source or target node")
                return None
            
            # Extract condition (if present)
            condition = ""
            condition_elem = flow_elem.find('{http://www.appian.com/ae/types/2009}condition')
            if condition_elem is None:
                condition_elem = flow_elem.find('condition')
            
            if condition_elem is not None and condition_elem.text:
                condition = condition_elem.text.strip()
                # Format condition if formatter available
                if self.sail_formatter and condition:
                    condition = self.sail_formatter.format_sail_code(condition)
            
            # Determine if this is a default flow (no condition)
            is_default = not bool(condition)
            
            # Resolve node names
            from_node_name = self.node_lookup.get(from_node_uuid, f"Node {from_node_uuid[:8]}")
            to_node_name = self.node_lookup.get(to_node_uuid, f"Node {to_node_uuid[:8]}")
            
            # Create label for display
            if condition:
                label = f"{condition[:50]}..." if len(condition) > 50 else condition
            else:
                label = "default"
            
            return {
                'uuid': flow_uuid,
                'from_node_uuid': from_node_uuid,
                'from_node_name': from_node_name,
                'to_node_uuid': to_node_uuid,
                'to_node_name': to_node_name,
                'condition': condition,
                'is_default': is_default,
                'label': label
            }
            
        except Exception as e:
            logger.warning(f"Error extracting flow: {e}")
            return None
    
    def _extract_outgoing_flow(
        self,
        outgoing_flow_elem: ET.Element,
        from_node_uuid: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract information from an outgoing flow element within a node
        
        Args:
            outgoing_flow_elem: Outgoing flow XML element
            from_node_uuid: UUID of the source node
            
        Returns:
            Flow dictionary or None if extraction fails
        """
        try:
            # Extract flow UUID
            flow_uuid = outgoing_flow_elem.get('{http://www.appian.com/ae/types/2009}uuid')
            if not flow_uuid:
                flow_uuid = outgoing_flow_elem.get('uuid')
            
            if not flow_uuid:
                # Generate a UUID if not present
                import uuid
                flow_uuid = f"_flow-{uuid.uuid4().hex[:16]}"
            
            # Extract target node UUID
            target_elem = outgoing_flow_elem.find('{http://www.appian.com/ae/types/2009}target')
            if target_elem is None:
                target_elem = outgoing_flow_elem.find('target')
            
            to_node_uuid = target_elem.text.strip() if target_elem is not None and target_elem.text else None
            
            if not to_node_uuid:
                logger.warning(f"Outgoing flow {flow_uuid} missing target node")
                return None
            
            # Extract condition (if present)
            condition = ""
            condition_elem = outgoing_flow_elem.find('{http://www.appian.com/ae/types/2009}condition')
            if condition_elem is None:
                condition_elem = outgoing_flow_elem.find('condition')
            
            if condition_elem is not None and condition_elem.text:
                condition = condition_elem.text.strip()
                # Format condition if formatter available
                if self.sail_formatter and condition:
                    condition = self.sail_formatter.format_sail_code(condition)
            
            # Determine if this is a default flow (no condition)
            is_default = not bool(condition)
            
            # Resolve node names
            from_node_name = self.node_lookup.get(from_node_uuid, f"Node {from_node_uuid[:8]}")
            to_node_name = self.node_lookup.get(to_node_uuid, f"Node {to_node_uuid[:8]}")
            
            # Create label for display
            if condition:
                label = f"{condition[:50]}..." if len(condition) > 50 else condition
            else:
                label = "default"
            
            return {
                'uuid': flow_uuid,
                'from_node_uuid': from_node_uuid,
                'from_node_name': from_node_name,
                'to_node_uuid': to_node_uuid,
                'to_node_name': to_node_name,
                'condition': condition,
                'is_default': is_default,
                'label': label
            }
            
        except Exception as e:
            logger.warning(f"Error extracting outgoing flow: {e}")
            return None
    
    def build_flow_graph(
        self,
        nodes: List[Dict[str, Any]],
        flows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build complete flow graph structure from nodes and flows
        
        Constructs a graph representation of the process flow, identifying
        start nodes (no incoming flows), end nodes (no outgoing flows), and
        all connections between nodes.
        
        Requirements: 5.6, 5.7
        
        Args:
            nodes: List of node dictionaries
            flows: List of flow dictionaries
            
        Returns:
            Flow graph dictionary with structure:
            {
                'start_nodes': [node_uuid],
                'end_nodes': [node_uuid],
                'node_connections': {
                    node_uuid: {
                        'incoming': [flow],
                        'outgoing': [flow]
                    }
                },
                'paths': []
            }
        """
        try:
            # Initialize node connections dictionary
            node_connections = {}
            node_uuids = {node['uuid'] for node in nodes}
            
            # Initialize connections for all nodes
            for node_uuid in node_uuids:
                node_connections[node_uuid] = {
                    'incoming': [],
                    'outgoing': []
                }
            
            # Populate connections from flows
            for flow in flows:
                from_uuid = flow['from_node_uuid']
                to_uuid = flow['to_node_uuid']
                
                # Add outgoing flow to source node
                if from_uuid in node_connections:
                    node_connections[from_uuid]['outgoing'].append(flow)
                
                # Add incoming flow to target node
                if to_uuid in node_connections:
                    node_connections[to_uuid]['incoming'].append(flow)
            
            # Identify start nodes (no incoming flows)
            start_nodes = [
                node_uuid
                for node_uuid, connections in node_connections.items()
                if len(connections['incoming']) == 0
            ]
            
            # Identify end nodes (no outgoing flows)
            end_nodes = [
                node_uuid
                for node_uuid, connections in node_connections.items()
                if len(connections['outgoing']) == 0
            ]
            
            # Build flow graph
            flow_graph = {
                'start_nodes': start_nodes,
                'end_nodes': end_nodes,
                'node_connections': node_connections,
                'paths': []  # Path analysis can be added later if needed
            }
            
            logger.info(
                f"Built flow graph: {len(start_nodes)} start nodes, "
                f"{len(end_nodes)} end nodes, {len(node_connections)} total nodes"
            )
            
            return flow_graph
            
        except Exception as e:
            log_parsing_error("Process Model", e, "building flow graph")
            # Return empty flow graph on error
            return {
                'start_nodes': [],
                'end_nodes': [],
                'node_connections': {},
                'paths': []
            }


class NodeComparator:
    """
    Compares nodes between process model versions
    
    This class performs node-by-node comparison between two versions of a
    process model, identifying added, removed, and modified nodes, and
    generating property-level diffs for modified nodes.
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    def __init__(self):
        """Initialize NodeComparator"""
        pass
    
    def compare_nodes(
        self,
        base_nodes: List[Dict[str, Any]],
        target_nodes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare nodes between two process model versions
        
        Compares nodes by UUID to identify which nodes were added, removed,
        or modified between versions. For modified nodes, generates detailed
        property-level diffs showing what changed.
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
        
        Args:
            base_nodes: List of node dictionaries from base version
            target_nodes: List of node dictionaries from target version
            
        Returns:
            Dictionary containing comparison results with structure:
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
        try:
            # Create UUID-indexed lookups for efficient comparison
            base_lookup = {node['uuid']: node for node in base_nodes}
            target_lookup = {node['uuid']: node for node in target_nodes}
            
            base_uuids = set(base_lookup.keys())
            target_uuids = set(target_lookup.keys())
            
            # Identify added nodes (in target but not in base)
            added_uuids = target_uuids - base_uuids
            added_nodes = [target_lookup[uuid] for uuid in added_uuids]
            
            # Identify removed nodes (in base but not in target)
            removed_uuids = base_uuids - target_uuids
            removed_nodes = [base_lookup[uuid] for uuid in removed_uuids]
            
            # Identify potentially modified nodes (in both versions)
            common_uuids = base_uuids & target_uuids
            
            modified_nodes = []
            unchanged_nodes = []
            
            for uuid in common_uuids:
                base_node = base_lookup[uuid]
                target_node = target_lookup[uuid]
                
                # Compare nodes to find property changes
                changes = self._compare_node_properties(base_node, target_node)
                
                if changes:
                    # Node has changes
                    modified_nodes.append({
                        'node': target_node,
                        'changes': changes
                    })
                else:
                    # Node is unchanged
                    unchanged_nodes.append(target_node)
            
            result = {
                'added': added_nodes,
                'removed': removed_nodes,
                'modified': modified_nodes,
                'unchanged': unchanged_nodes
            }
            
            logger.info(
                f"Node comparison: {len(added_nodes)} added, "
                f"{len(removed_nodes)} removed, {len(modified_nodes)} modified, "
                f"{len(unchanged_nodes)} unchanged"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error comparing nodes: {e}", exc_info=True)
            # Return empty comparison on error
            return {
                'added': [],
                'removed': [],
                'modified': [],
                'unchanged': []
            }
    
    def _compare_node_properties(
        self,
        base_node: Dict[str, Any],
        target_node: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Compare properties between two versions of the same node
        
        Performs deep comparison of node properties to identify all changes
        at the property level, including changes in basic info, assignments,
        forms, expressions, and escalations.
        
        Requirements: 4.5
        
        Args:
            base_node: Node dictionary from base version
            target_node: Node dictionary from target version
            
        Returns:
            List of property change dictionaries with structure:
            [
                {
                    'property': str,  # Property path (e.g., 'properties.basic.description')
                    'before': Any,
                    'after': Any
                }
            ]
        """
        changes = []
        
        try:
            # Compare node name
            if base_node.get('name') != target_node.get('name'):
                changes.append({
                    'property': 'name',
                    'before': base_node.get('name'),
                    'after': target_node.get('name')
                })
            
            # Compare node type
            if base_node.get('type') != target_node.get('type'):
                changes.append({
                    'property': 'type',
                    'before': base_node.get('type'),
                    'after': target_node.get('type')
                })
            
            # Compare properties by category
            base_props = base_node.get('properties', {})
            target_props = target_node.get('properties', {})
            
            # Compare each property category
            for category in ['basic', 'assignment', 'forms', 'expressions', 'escalation']:
                base_category = base_props.get(category, {})
                target_category = target_props.get(category, {})
                
                # Find all keys in either version
                all_keys = set(base_category.keys()) | set(target_category.keys())
                
                for key in all_keys:
                    base_value = base_category.get(key)
                    target_value = target_category.get(key)
                    
                    # Compare values
                    if base_value != target_value:
                        changes.append({
                            'property': f'properties.{category}.{key}',
                            'before': base_value,
                            'after': target_value
                        })
            
            # Compare dependencies
            base_deps = base_node.get('dependencies', {})
            target_deps = target_node.get('dependencies', {})
            
            for dep_type in ['interfaces', 'rules', 'groups']:
                base_dep_list = base_deps.get(dep_type, [])
                target_dep_list = target_deps.get(dep_type, [])
                
                # Convert to sets of UUIDs for comparison
                base_dep_uuids = {dep['uuid'] for dep in base_dep_list}
                target_dep_uuids = {dep['uuid'] for dep in target_dep_list}
                
                if base_dep_uuids != target_dep_uuids:
                    changes.append({
                        'property': f'dependencies.{dep_type}',
                        'before': base_dep_list,
                        'after': target_dep_list
                    })
            
        except Exception as e:
            logger.warning(f"Error comparing node properties: {e}")
        
        return changes
    
    def compare_flows(
        self,
        base_flows: List[Dict[str, Any]],
        target_flows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare flows between two process model versions
        
        Compares flow lists to identify which flows were added, removed,
        or modified between versions. Flows are compared by their source
        and target node UUIDs.
        
        Requirements: 5.8
        
        Args:
            base_flows: List of flow dictionaries from base version
            target_flows: List of flow dictionaries from target version
            
        Returns:
            Dictionary containing flow comparison results with structure:
            {
                'added_flows': [flow],
                'removed_flows': [flow],
                'modified_flows': [
                    {
                        'flow': flow,
                        'changes': [
                            {
                                'property': str,
                                'before': Any,
                                'after': Any
                            }
                        ]
                    }
                ],
                'unchanged_flows': [flow]
            }
        """
        try:
            # Create flow identifiers based on source and target nodes
            # A flow is uniquely identified by (from_node_uuid, to_node_uuid)
            def flow_key(flow):
                return (flow['from_node_uuid'], flow['to_node_uuid'])
            
            # Create lookups indexed by flow key
            base_lookup = {flow_key(flow): flow for flow in base_flows}
            target_lookup = {flow_key(flow): flow for flow in target_flows}
            
            base_keys = set(base_lookup.keys())
            target_keys = set(target_lookup.keys())
            
            # Identify added flows (in target but not in base)
            added_keys = target_keys - base_keys
            added_flows = [target_lookup[key] for key in added_keys]
            
            # Identify removed flows (in base but not in target)
            removed_keys = base_keys - target_keys
            removed_flows = [base_lookup[key] for key in removed_keys]
            
            # Identify potentially modified flows (in both versions)
            common_keys = base_keys & target_keys
            
            modified_flows = []
            unchanged_flows = []
            
            for key in common_keys:
                base_flow = base_lookup[key]
                target_flow = target_lookup[key]
                
                # Compare flow properties
                changes = self._compare_flow_properties(base_flow, target_flow)
                
                if changes:
                    # Flow has changes
                    modified_flows.append({
                        'flow': target_flow,
                        'changes': changes
                    })
                else:
                    # Flow is unchanged
                    unchanged_flows.append(target_flow)
            
            result = {
                'added_flows': added_flows,
                'removed_flows': removed_flows,
                'modified_flows': modified_flows,
                'unchanged_flows': unchanged_flows
            }
            
            logger.info(
                f"Flow comparison: {len(added_flows)} added, "
                f"{len(removed_flows)} removed, {len(modified_flows)} modified, "
                f"{len(unchanged_flows)} unchanged"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error comparing flows: {e}", exc_info=True)
            # Return empty comparison on error
            return {
                'added_flows': [],
                'removed_flows': [],
                'modified_flows': [],
                'unchanged_flows': []
            }
    
    def _compare_flow_properties(
        self,
        base_flow: Dict[str, Any],
        target_flow: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Compare properties between two versions of the same flow
        
        Compares flow properties to identify changes in conditions,
        labels, or other flow attributes.
        
        Requirements: 5.8
        
        Args:
            base_flow: Flow dictionary from base version
            target_flow: Flow dictionary from target version
            
        Returns:
            List of property change dictionaries
        """
        changes = []
        
        try:
            # Compare condition
            if base_flow.get('condition') != target_flow.get('condition'):
                changes.append({
                    'property': 'condition',
                    'before': base_flow.get('condition'),
                    'after': target_flow.get('condition')
                })
            
            # Compare is_default flag
            if base_flow.get('is_default') != target_flow.get('is_default'):
                changes.append({
                    'property': 'is_default',
                    'before': base_flow.get('is_default'),
                    'after': target_flow.get('is_default')
                })
            
            # Compare label
            if base_flow.get('label') != target_flow.get('label'):
                changes.append({
                    'property': 'label',
                    'before': base_flow.get('label'),
                    'after': target_flow.get('label')
                })
            
            # Compare node names (in case nodes were renamed)
            if base_flow.get('from_node_name') != target_flow.get('from_node_name'):
                changes.append({
                    'property': 'from_node_name',
                    'before': base_flow.get('from_node_name'),
                    'after': target_flow.get('from_node_name')
                })
            
            if base_flow.get('to_node_name') != target_flow.get('to_node_name'):
                changes.append({
                    'property': 'to_node_name',
                    'before': base_flow.get('to_node_name'),
                    'after': target_flow.get('to_node_name')
                })
            
        except Exception as e:
            logger.warning(f"Error comparing flow properties: {e}")
        
        return changes


class ProcessModelRenderer:
    """
    Renders process model data as HTML for display
    
    This class formats process model nodes, properties, and comparisons
    as HTML for display in the web interface. It provides structured,
    human-readable views of process model information.
    
    Requirements: 7.1, 7.2, 7.3, 7.4
    """
    
    def __init__(self):
        """Initialize ProcessModelRenderer"""
        pass
    
    def render_node_summary(self, node: Dict[str, Any]) -> str:
        """
        Render a single node as HTML summary
        
        Creates an HTML representation of a process model node with all
        its properties organized by category for easy reading.
        
        Requirements: 7.1, 7.2
        
        Args:
            node: Node dictionary containing all node information
            
        Returns:
            HTML string representing the node summary
        """
        try:
            import html
            
            # Extract node information
            node_name = html.escape(str(node.get('name', 'Unknown')))
            node_type = html.escape(str(node.get('type', 'UNKNOWN')))
            node_uuid = html.escape(str(node.get('uuid', '')))
            
            # Start building HTML
            html_parts = []
            
            # Node header
            html_parts.append(f'<div class="node-summary" data-node-uuid="{node_uuid}">')
            html_parts.append(f'  <div class="node-header">')
            html_parts.append(f'    <h4 class="node-name">{node_name}</h4>')
            html_parts.append(f'    <span class="node-type badge badge-info">{node_type}</span>')
            html_parts.append(f'  </div>')
            
            # Render property groups
            properties = node.get('properties', {})
            
            # Basic properties
            if properties.get('basic'):
                html_parts.append(self.render_property_group('Basic', properties['basic']))
            
            # Assignment properties
            if properties.get('assignment'):
                html_parts.append(self.render_property_group('Assignment', properties['assignment']))
            
            # Forms properties
            if properties.get('forms'):
                html_parts.append(self.render_property_group('Forms', properties['forms']))
            
            # Expressions properties
            if properties.get('expressions'):
                html_parts.append(self.render_property_group('Expressions', properties['expressions']))
            
            # Escalation properties
            if properties.get('escalation') and properties['escalation'].get('enabled'):
                html_parts.append(self.render_property_group('Escalation', properties['escalation']))
            
            # Dependencies
            dependencies = node.get('dependencies', {})
            if any(dependencies.get(dep_type) for dep_type in ['interfaces', 'rules', 'groups']):
                html_parts.append(self._render_dependencies(dependencies))
            
            html_parts.append('</div>')
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.error(f"Error rendering node summary: {e}", exc_info=True)
            return f'<div class="alert alert-danger">Error rendering node: {html.escape(str(e))}</div>'
    
    def render_property_group(
        self,
        group_name: str,
        properties: Dict[str, Any]
    ) -> str:
        """
        Render a property group as HTML
        
        Creates an HTML representation of a group of related properties
        (e.g., Basic, Assignment, Forms) with proper formatting and escaping.
        
        Requirements: 7.1, 7.2
        
        Args:
            group_name: Name of the property group (e.g., "Basic", "Assignment")
            properties: Dictionary of properties in this group
            
        Returns:
            HTML string representing the property group
        """
        try:
            import html
            
            # Filter out empty properties
            non_empty_props = {
                k: v for k, v in properties.items()
                if v is not None and v != '' and v != [] and v != {}
            }
            
            if not non_empty_props:
                return ''
            
            html_parts = []
            
            # Group header
            html_parts.append(f'  <div class="property-group">')
            html_parts.append(f'    <h5 class="property-group-name">{html.escape(group_name)}</h5>')
            html_parts.append(f'    <div class="property-list">')
            
            # Render each property
            for key, value in non_empty_props.items():
                # Format property name (convert snake_case to Title Case)
                prop_name = key.replace('_', ' ').title()
                
                # Format property value
                formatted_value = self._format_property_value(value)
                
                html_parts.append(f'      <div class="property-item">')
                html_parts.append(f'        <span class="property-name">{html.escape(prop_name)}:</span>')
                html_parts.append(f'        <span class="property-value">{formatted_value}</span>')
                html_parts.append(f'      </div>')
            
            html_parts.append(f'    </div>')
            html_parts.append(f'  </div>')
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.error(f"Error rendering property group: {e}", exc_info=True)
            return ''
    
    def render_node_comparison(
        self,
        base_node: Optional[Dict[str, Any]],
        target_node: Optional[Dict[str, Any]],
        changes: List[Dict[str, Any]]
    ) -> str:
        """
        Render a three-way node comparison as HTML
        
        Creates an HTML representation showing the differences between
        two versions of a node, highlighting changed properties with
        before and after values.
        
        Requirements: 7.3, 7.4
        
        Args:
            base_node: Node dictionary from base version (can be None if added)
            target_node: Node dictionary from target version (can be None if removed)
            changes: List of property changes with before/after values
            
        Returns:
            HTML string representing the node comparison
        """
        try:
            import html
            
            html_parts = []
            
            # Determine comparison type
            if base_node is None and target_node is not None:
                # Node was added
                comparison_type = 'added'
                node_name = html.escape(str(target_node.get('name', 'Unknown')))
                html_parts.append(f'<div class="node-comparison node-added">')
                html_parts.append(f'  <div class="comparison-header">')
                html_parts.append(f'    <h4>{node_name} <span class="badge badge-success">ADDED</span></h4>')
                html_parts.append(f'  </div>')
                html_parts.append(self.render_node_summary(target_node))
                html_parts.append('</div>')
                
            elif base_node is not None and target_node is None:
                # Node was removed
                comparison_type = 'removed'
                node_name = html.escape(str(base_node.get('name', 'Unknown')))
                html_parts.append(f'<div class="node-comparison node-removed">')
                html_parts.append(f'  <div class="comparison-header">')
                html_parts.append(f'    <h4>{node_name} <span class="badge badge-danger">REMOVED</span></h4>')
                html_parts.append(f'  </div>')
                html_parts.append(self.render_node_summary(base_node))
                html_parts.append('</div>')
                
            elif base_node is not None and target_node is not None:
                # Node was modified
                comparison_type = 'modified'
                node_name = html.escape(str(target_node.get('name', 'Unknown')))
                html_parts.append(f'<div class="node-comparison node-modified">')
                html_parts.append(f'  <div class="comparison-header">')
                html_parts.append(f'    <h4>{node_name} <span class="badge badge-warning">MODIFIED</span></h4>')
                html_parts.append(f'  </div>')
                
                # Render side-by-side comparison
                html_parts.append(f'  <div class="comparison-content">')
                html_parts.append(f'    <div class="row">')
                
                # Before column
                html_parts.append(f'      <div class="col-md-6">')
                html_parts.append(f'        <h5>Before</h5>')
                html_parts.append(self.render_node_summary(base_node))
                html_parts.append(f'      </div>')
                
                # After column
                html_parts.append(f'      <div class="col-md-6">')
                html_parts.append(f'        <h5>After</h5>')
                html_parts.append(self.render_node_summary(target_node))
                html_parts.append(f'      </div>')
                
                html_parts.append(f'    </div>')
                
                # Render changes summary
                if changes:
                    html_parts.append(self._render_changes_summary(changes))
                
                html_parts.append(f'  </div>')
                html_parts.append('</div>')
            
            else:
                # Invalid comparison
                return '<div class="alert alert-warning">Invalid node comparison</div>'
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.error(f"Error rendering node comparison: {e}", exc_info=True)
            return f'<div class="alert alert-danger">Error rendering comparison: {html.escape(str(e))}</div>'
    
    def _format_property_value(self, value: Any) -> str:
        """
        Format a property value for HTML display
        
        Converts various property value types (strings, lists, dicts, etc.)
        into properly formatted and escaped HTML.
        
        Args:
            value: Property value to format
            
        Returns:
            HTML-formatted string
        """
        import html
        
        try:
            if value is None:
                return '<span class="text-muted">None</span>'
            
            elif isinstance(value, bool):
                return '<span class="badge badge-secondary">' + str(value) + '</span>'
            
            elif isinstance(value, (int, float)):
                return html.escape(str(value))
            
            elif isinstance(value, str):
                # Escape HTML and preserve line breaks
                escaped = html.escape(value)
                # If it's a long expression, format it in a code block
                if len(escaped) > 100 or '\n' in escaped:
                    return f'<pre class="code-block">{escaped}</pre>'
                else:
                    return escaped
            
            elif isinstance(value, list):
                if not value:
                    return '<span class="text-muted">[]</span>'
                
                # Format list items
                items = []
                for item in value:
                    if isinstance(item, dict):
                        # For dependency objects, show name
                        item_name = item.get('name', str(item))
                        items.append(f'<li>{html.escape(str(item_name))}</li>')
                    else:
                        items.append(f'<li>{html.escape(str(item))}</li>')
                
                return '<ul class="property-list-value">' + ''.join(items) + '</ul>'
            
            elif isinstance(value, dict):
                if not value:
                    return '<span class="text-muted">{}</span>'
                
                # Format dict as nested properties
                items = []
                for k, v in value.items():
                    formatted_v = self._format_property_value(v)
                    items.append(f'<div><strong>{html.escape(str(k))}:</strong> {formatted_v}</div>')
                
                return '<div class="nested-properties">' + ''.join(items) + '</div>'
            
            else:
                return html.escape(str(value))
                
        except Exception as e:
            logger.warning(f"Error formatting property value: {e}")
            return html.escape(str(value))
    
    def _render_dependencies(self, dependencies: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Render node dependencies as HTML
        
        Args:
            dependencies: Dictionary of dependency lists by type
            
        Returns:
            HTML string representing dependencies
        """
        import html
        
        html_parts = []
        html_parts.append('  <div class="property-group">')
        html_parts.append('    <h5 class="property-group-name">Dependencies</h5>')
        html_parts.append('    <div class="property-list">')
        
        # Render each dependency type
        for dep_type, dep_list in dependencies.items():
            if dep_list:
                # Format dependency type name
                dep_type_name = dep_type.replace('_', ' ').title()
                
                # Create list of dependency names
                dep_names = [html.escape(dep.get('name', 'Unknown')) for dep in dep_list]
                
                html_parts.append('      <div class="property-item">')
                html_parts.append(f'        <span class="property-name">{dep_type_name}:</span>')
                html_parts.append('        <span class="property-value">')
                html_parts.append('          <ul class="dependency-list">')
                for name in dep_names:
                    html_parts.append(f'            <li>{name}</li>')
                html_parts.append('          </ul>')
                html_parts.append('        </span>')
                html_parts.append('      </div>')
        
        html_parts.append('    </div>')
        html_parts.append('  </div>')
        
        return '\n'.join(html_parts)
    
    def _render_changes_summary(self, changes: List[Dict[str, Any]]) -> str:
        """
        Render a summary of changes between node versions
        
        Args:
            changes: List of property changes
            
        Returns:
            HTML string representing changes summary
        """
        import html
        
        html_parts = []
        html_parts.append('    <div class="changes-summary">')
        html_parts.append('      <h5>Changes Summary</h5>')
        html_parts.append('      <table class="table table-sm table-bordered">')
        html_parts.append('        <thead>')
        html_parts.append('          <tr>')
        html_parts.append('            <th>Property</th>')
        html_parts.append('            <th>Before</th>')
        html_parts.append('            <th>After</th>')
        html_parts.append('          </tr>')
        html_parts.append('        </thead>')
        html_parts.append('        <tbody>')
        
        for change in changes:
            prop_name = html.escape(str(change.get('property', 'Unknown')))
            before_value = self._format_change_value(change.get('before'))
            after_value = self._format_change_value(change.get('after'))
            
            html_parts.append('          <tr>')
            html_parts.append(f'            <td><strong>{prop_name}</strong></td>')
            html_parts.append(f'            <td class="before-value">{before_value}</td>')
            html_parts.append(f'            <td class="after-value">{after_value}</td>')
            html_parts.append('          </tr>')
        
        html_parts.append('        </tbody>')
        html_parts.append('      </table>')
        html_parts.append('    </div>')
        
        return '\n'.join(html_parts)
    
    def _format_change_value(self, value: Any) -> str:
        """
        Format a change value for display in comparison table
        
        Args:
            value: Value to format
            
        Returns:
            HTML-formatted string
        """
        import html
        
        try:
            if value is None or value == '':
                return '<span class="text-muted">None</span>'
            
            elif isinstance(value, bool):
                return str(value)
            
            elif isinstance(value, (int, float)):
                return html.escape(str(value))
            
            elif isinstance(value, str):
                # Truncate long strings
                if len(value) > 100:
                    return html.escape(value[:100]) + '...'
                else:
                    return html.escape(value)
            
            elif isinstance(value, list):
                if not value:
                    return '<span class="text-muted">[]</span>'
                
                # Show count for lists
                return f'{len(value)} items'
            
            elif isinstance(value, dict):
                if not value:
                    return '<span class="text-muted">{}</span>'
                
                # Show count for dicts
                return f'{len(value)} properties'
            
            else:
                return html.escape(str(value))
                
        except Exception as e:
            logger.warning(f"Error formatting change value: {e}")
            return html.escape(str(value))



class FlowDiagramGenerator:
    """
    Generates flow diagram data for visual representation
    
    This class creates Mermaid.js compatible data structures from process
    model nodes and flows for visual flow diagram rendering. It handles
    node positioning, shape selection based on node type, and edge formatting.
    
    Requirements: 7.5, 7.6, 7.9
    """
    
    def __init__(self):
        """Initialize FlowDiagramGenerator"""
        # Map node types to Mermaid shapes
        self.node_shapes = {
            NodeType.USER_INPUT_TASK: ('rect', '[', ']'),  # Rectangle
            NodeType.SCRIPT_TASK: ('rect', '[', ']'),  # Rectangle
            NodeType.GATEWAY: ('diamond', '{', '}'),  # Diamond
            NodeType.SUBPROCESS: ('subroutine', '[[', ']]'),  # Subroutine
            NodeType.START_NODE: ('circle', '((', '))'),  # Circle
            NodeType.END_NODE: ('circle', '((', '))'),  # Circle
            NodeType.UNKNOWN: ('rect', '[', ']')  # Rectangle
        }
    
    def generate_diagram_data(
        self,
        nodes: List[Dict[str, Any]],
        flows: List[Dict[str, Any]],
        flow_graph: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate data structure for flow diagram visualization
        
        Creates a Mermaid.js compatible data structure from process model
        nodes and flows. The structure includes node definitions with
        appropriate shapes based on node type, and edge definitions with
        conditions.
        
        Requirements: 7.5, 7.6, 7.9
        
        Args:
            nodes: List of node dictionaries with complete node information
            flows: List of flow dictionaries with connection information
            flow_graph: Flow graph structure with start/end nodes
            
        Returns:
            Dictionary containing diagram data with structure:
            {
                'mermaid_syntax': str,  # Complete Mermaid.js syntax
                'nodes': [
                    {
                        'id': str,  # Node UUID (sanitized for Mermaid)
                        'label': str,  # Node name
                        'type': str,  # Node type
                        'shape': str,  # Mermaid shape type
                        'properties': {...}  # Full node properties
                    }
                ],
                'edges': [
                    {
                        'id': str,  # Flow UUID
                        'source': str,  # Source node ID
                        'target': str,  # Target node ID
                        'label': str,  # Condition or 'default'
                        'type': str  # 'default' or 'conditional'
                    }
                ],
                'start_nodes': [str],  # IDs of start nodes
                'end_nodes': [str]  # IDs of end nodes
            }
        """
        try:
            logger.info(f"Generating diagram data for {len(nodes)} nodes and {len(flows)} flows")
            
            # Generate node data
            diagram_nodes = []
            node_id_map = {}  # Map UUIDs to sanitized IDs
            
            for node in nodes:
                node_id = self._sanitize_id(node['uuid'])
                node_id_map[node['uuid']] = node_id
                
                # Determine node shape based on type
                node_type_enum = NodeType(node.get('type', 'UNKNOWN'))
                shape_info = self.node_shapes.get(node_type_enum, self.node_shapes[NodeType.UNKNOWN])
                
                diagram_node = {
                    'id': node_id,
                    'label': node.get('name', 'Unknown'),
                    'type': node.get('type', 'UNKNOWN'),
                    'shape': shape_info[0],
                    'shape_open': shape_info[1],
                    'shape_close': shape_info[2],
                    'properties': node.get('properties', {})
                }
                
                diagram_nodes.append(diagram_node)
            
            # Generate edge data
            diagram_edges = []
            
            for flow in flows:
                source_id = node_id_map.get(flow['from_node_uuid'])
                target_id = node_id_map.get(flow['to_node_uuid'])
                
                if not source_id or not target_id:
                    logger.warning(
                        f"Flow {flow['uuid']} references unknown nodes: "
                        f"{flow['from_node_uuid']} -> {flow['to_node_uuid']}"
                    )
                    continue
                
                # Create edge label from condition
                edge_label = flow.get('label', '')
                if not edge_label:
                    edge_label = 'default' if flow.get('is_default', True) else ''
                
                # Truncate long labels for diagram readability
                if len(edge_label) > 30:
                    edge_label = edge_label[:27] + '...'
                
                diagram_edge = {
                    'id': self._sanitize_id(flow['uuid']),
                    'source': source_id,
                    'target': target_id,
                    'label': edge_label,
                    'type': 'default' if flow.get('is_default', True) else 'conditional',
                    'condition': flow.get('condition', '')
                }
                
                diagram_edges.append(diagram_edge)
            
            # Get start and end nodes from flow graph
            start_node_ids = [
                node_id_map.get(uuid) for uuid in flow_graph.get('start_nodes', [])
                if uuid in node_id_map
            ]
            
            end_node_ids = [
                node_id_map.get(uuid) for uuid in flow_graph.get('end_nodes', [])
                if uuid in node_id_map
            ]
            
            # Generate Mermaid syntax
            mermaid_syntax = self._generate_mermaid_syntax(
                diagram_nodes,
                diagram_edges,
                start_node_ids,
                end_node_ids
            )
            
            diagram_data = {
                'mermaid_syntax': mermaid_syntax,
                'nodes': diagram_nodes,
                'edges': diagram_edges,
                'start_nodes': start_node_ids,
                'end_nodes': end_node_ids
            }
            
            logger.info(
                f"Generated diagram data: {len(diagram_nodes)} nodes, "
                f"{len(diagram_edges)} edges, {len(start_node_ids)} start nodes, "
                f"{len(end_node_ids)} end nodes"
            )
            
            return diagram_data
            
        except Exception as e:
            logger.error(f"Error generating diagram data: {e}", exc_info=True)
            # Return empty diagram data on error
            return {
                'mermaid_syntax': 'graph TD\n  Error[Error generating diagram]',
                'nodes': [],
                'edges': [],
                'start_nodes': [],
                'end_nodes': []
            }
    
    def _sanitize_id(self, uuid: str) -> str:
        """
        Sanitize UUID for use as Mermaid node ID
        
        Mermaid.js has restrictions on node IDs. This method converts
        UUIDs to valid Mermaid IDs by replacing invalid characters.
        
        Args:
            uuid: Original UUID string
            
        Returns:
            Sanitized ID string safe for Mermaid
        """
        # Replace hyphens and other special characters with underscores
        # Keep only alphanumeric and underscores
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', uuid)
        
        # Ensure it starts with a letter (Mermaid requirement)
        if sanitized and not sanitized[0].isalpha():
            sanitized = 'n' + sanitized
        
        return sanitized
    
    def _generate_mermaid_syntax(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        start_node_ids: List[str],
        end_node_ids: List[str]
    ) -> str:
        """
        Generate Mermaid.js syntax from diagram data
        
        Creates the complete Mermaid.js flowchart syntax string that can
        be rendered by the Mermaid.js library in the browser.
        
        Args:
            nodes: List of diagram node dictionaries
            edges: List of diagram edge dictionaries
            start_node_ids: List of start node IDs
            end_node_ids: List of end node IDs
            
        Returns:
            Complete Mermaid.js syntax string
        """
        try:
            lines = []
            
            # Start with flowchart declaration (TD = Top Down)
            lines.append('graph TD')
            
            # Add node definitions
            for node in nodes:
                node_id = node['id']
                label = node['label'].replace('"', '\\"')  # Escape quotes
                shape_open = node['shape_open']
                shape_close = node['shape_close']
                
                # Create node definition with shape
                node_def = f'  {node_id}{shape_open}"{label}"{shape_close}'
                lines.append(node_def)
                
                # Add styling for special nodes
                if node_id in start_node_ids:
                    lines.append(f'  style {node_id} fill:#90EE90')  # Light green
                elif node_id in end_node_ids:
                    lines.append(f'  style {node_id} fill:#FFB6C1')  # Light pink
            
            # Add edge definitions
            for edge in edges:
                source = edge['source']
                target = edge['target']
                label = edge['label'].replace('"', '\\"')  # Escape quotes
                
                # Choose arrow style based on edge type
                if edge['type'] == 'conditional':
                    # Conditional flow with label
                    if label:
                        edge_def = f'  {source} -->|"{label}"| {target}'
                    else:
                        edge_def = f'  {source} --> {target}'
                else:
                    # Default flow
                    if label and label != 'default':
                        edge_def = f'  {source} -->|"{label}"| {target}'
                    else:
                        edge_def = f'  {source} --> {target}'
                
                lines.append(edge_def)
            
            # Join all lines
            mermaid_syntax = '\n'.join(lines)
            
            return mermaid_syntax
            
        except Exception as e:
            logger.error(f"Error generating Mermaid syntax: {e}", exc_info=True)
            return 'graph TD\n  Error[Error generating syntax]'
    
    def generate_comparison_diagram(
        self,
        base_diagram: Dict[str, Any],
        target_diagram: Dict[str, Any],
        node_changes: Dict[str, Any],
        flow_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate diagram with change highlighting for comparison view
        
        Creates a flow diagram that highlights changes between two versions
        of a process model. Added nodes are shown in green, removed nodes
        in red, and modified nodes in yellow.
        
        Requirements: 7.7
        
        Args:
            base_diagram: Diagram data from base version
            target_diagram: Diagram data from target version
            node_changes: Node comparison results with added/removed/modified
            flow_changes: Flow comparison results
            
        Returns:
            Dictionary containing comparison diagram data with structure:
            {
                'mermaid_syntax': str,  # Mermaid syntax with change highlighting
                'nodes': [...],  # All nodes with change_type annotation
                'edges': [...],  # All edges with change_type annotation
                'changes_summary': {
                    'nodes_added': int,
                    'nodes_removed': int,
                    'nodes_modified': int,
                    'flows_added': int,
                    'flows_removed': int,
                    'flows_modified': int
                }
            }
        """
        try:
            logger.info("Generating comparison diagram with change highlighting")
            
            # Create sets of node UUIDs by change type
            added_node_uuids = {node['uuid'] for node in node_changes.get('added', [])}
            removed_node_uuids = {node['uuid'] for node in node_changes.get('removed', [])}
            modified_node_uuids = {
                mod['node']['uuid'] for mod in node_changes.get('modified', [])
            }
            
            # Create sets of flow keys by change type
            def flow_key(flow):
                return (flow['from_node_uuid'], flow['to_node_uuid'])
            
            added_flow_keys = {
                flow_key(flow) for flow in flow_changes.get('added_flows', [])
            }
            removed_flow_keys = {
                flow_key(flow) for flow in flow_changes.get('removed_flows', [])
            }
            modified_flow_keys = {
                flow_key(mod['flow']) for mod in flow_changes.get('modified_flows', [])
            }
            
            # Combine nodes from both versions
            all_nodes = []
            processed_uuids = set()
            
            # Add target nodes (added and modified)
            for node in target_diagram.get('nodes', []):
                # Find original UUID from node properties
                original_uuid = self._find_original_uuid(node, target_diagram)
                
                if original_uuid in added_node_uuids:
                    node['change_type'] = 'ADDED'
                    node['change_color'] = '#90EE90'  # Light green
                elif original_uuid in modified_node_uuids:
                    node['change_type'] = 'MODIFIED'
                    node['change_color'] = '#FFD700'  # Gold/yellow
                else:
                    node['change_type'] = 'UNCHANGED'
                    node['change_color'] = None
                
                all_nodes.append(node)
                processed_uuids.add(original_uuid)
            
            # Add removed nodes from base
            for node in base_diagram.get('nodes', []):
                original_uuid = self._find_original_uuid(node, base_diagram)
                
                if original_uuid in removed_node_uuids and original_uuid not in processed_uuids:
                    node['change_type'] = 'REMOVED'
                    node['change_color'] = '#FFB6C1'  # Light red/pink
                    all_nodes.append(node)
                    processed_uuids.add(original_uuid)
            
            # Combine edges from both versions
            all_edges = []
            processed_flow_keys = set()
            
            # Add target edges (added and modified)
            for edge in target_diagram.get('edges', []):
                # Reconstruct flow key from edge
                edge_key = self._edge_to_flow_key(edge, target_diagram)
                
                if edge_key in added_flow_keys:
                    edge['change_type'] = 'ADDED'
                    edge['change_style'] = 'stroke:#90EE90,stroke-width:3px'
                elif edge_key in modified_flow_keys:
                    edge['change_type'] = 'MODIFIED'
                    edge['change_style'] = 'stroke:#FFD700,stroke-width:3px'
                else:
                    edge['change_type'] = 'UNCHANGED'
                    edge['change_style'] = None
                
                all_edges.append(edge)
                processed_flow_keys.add(edge_key)
            
            # Add removed edges from base
            for edge in base_diagram.get('edges', []):
                edge_key = self._edge_to_flow_key(edge, base_diagram)
                
                if edge_key in removed_flow_keys and edge_key not in processed_flow_keys:
                    edge['change_type'] = 'REMOVED'
                    edge['change_style'] = 'stroke:#FFB6C1,stroke-width:3px,stroke-dasharray: 5 5'
                    all_edges.append(edge)
                    processed_flow_keys.add(edge_key)
            
            # Generate Mermaid syntax with change highlighting
            mermaid_syntax = self._generate_comparison_mermaid_syntax(all_nodes, all_edges)
            
            # Create changes summary
            changes_summary = {
                'nodes_added': len(added_node_uuids),
                'nodes_removed': len(removed_node_uuids),
                'nodes_modified': len(modified_node_uuids),
                'flows_added': len(added_flow_keys),
                'flows_removed': len(removed_flow_keys),
                'flows_modified': len(modified_flow_keys)
            }
            
            comparison_diagram = {
                'mermaid_syntax': mermaid_syntax,
                'nodes': all_nodes,
                'edges': all_edges,
                'changes_summary': changes_summary
            }
            
            logger.info(
                f"Generated comparison diagram: "
                f"{changes_summary['nodes_added']} nodes added, "
                f"{changes_summary['nodes_removed']} nodes removed, "
                f"{changes_summary['nodes_modified']} nodes modified"
            )
            
            return comparison_diagram
            
        except Exception as e:
            logger.error(f"Error generating comparison diagram: {e}", exc_info=True)
            # Return empty comparison diagram on error
            return {
                'mermaid_syntax': 'graph TD\n  Error[Error generating comparison diagram]',
                'nodes': [],
                'edges': [],
                'changes_summary': {
                    'nodes_added': 0,
                    'nodes_removed': 0,
                    'nodes_modified': 0,
                    'flows_added': 0,
                    'flows_removed': 0,
                    'flows_modified': 0
                }
            }
    
    def _find_original_uuid(
        self,
        node: Dict[str, Any],
        diagram: Dict[str, Any]
    ) -> str:
        """
        Find the original UUID for a diagram node
        
        Diagram nodes use sanitized IDs, this method finds the original
        UUID from the node properties or by reverse lookup.
        
        Args:
            node: Diagram node dictionary
            diagram: Complete diagram data
            
        Returns:
            Original UUID string
        """
        # Try to get UUID from properties if available
        if 'uuid' in node:
            return node['uuid']
        
        # Otherwise, try to find it in the original nodes list
        # This is a fallback and may not always work
        node_id = node.get('id', '')
        
        # Look through all nodes in the diagram to find matching ID
        for n in diagram.get('nodes', []):
            if n.get('id') == node_id and 'uuid' in n.get('properties', {}):
                return n['properties']['uuid']
        
        # If all else fails, return the sanitized ID
        return node_id
    
    def _edge_to_flow_key(
        self,
        edge: Dict[str, Any],
        diagram: Dict[str, Any]
    ) -> tuple:
        """
        Convert an edge to a flow key for comparison
        
        Args:
            edge: Diagram edge dictionary
            diagram: Complete diagram data
            
        Returns:
            Tuple of (from_uuid, to_uuid)
        """
        # Get source and target node IDs
        source_id = edge.get('source', '')
        target_id = edge.get('target', '')
        
        # Find original UUIDs for these nodes
        source_uuid = source_id
        target_uuid = target_id
        
        for node in diagram.get('nodes', []):
            if node.get('id') == source_id:
                source_uuid = self._find_original_uuid(node, diagram)
            if node.get('id') == target_id:
                target_uuid = self._find_original_uuid(node, diagram)
        
        return (source_uuid, target_uuid)
    
    def _generate_comparison_mermaid_syntax(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> str:
        """
        Generate Mermaid syntax with change highlighting
        
        Creates Mermaid.js syntax that includes color coding for added,
        removed, and modified nodes and flows.
        
        Args:
            nodes: List of nodes with change_type annotations
            edges: List of edges with change_type annotations
            
        Returns:
            Mermaid.js syntax string with change highlighting
        """
        try:
            lines = []
            
            # Start with flowchart declaration
            lines.append('graph TD')
            
            # Add node definitions with change highlighting
            for node in nodes:
                node_id = node['id']
                label = node['label'].replace('"', '\\"')
                shape_open = node.get('shape_open', '[')
                shape_close = node.get('shape_close', ']')
                
                # Create node definition
                node_def = f'  {node_id}{shape_open}"{label}"{shape_close}'
                lines.append(node_def)
                
                # Add styling based on change type
                change_color = node.get('change_color')
                if change_color:
                    lines.append(f'  style {node_id} fill:{change_color}')
            
            # Add edge definitions with change highlighting
            for edge in edges:
                source = edge['source']
                target = edge['target']
                label = edge.get('label', '').replace('"', '\\"')
                
                # Create edge definition
                if label and label != 'default':
                    edge_def = f'  {source} -->|"{label}"| {target}'
                else:
                    edge_def = f'  {source} --> {target}'
                
                lines.append(edge_def)
                
                # Note: Mermaid.js doesn't support per-edge styling directly
                # Edge styling would need to be handled differently in the UI
            
            # Add legend
            lines.append('')
            lines.append('  %% Legend')
            lines.append('  Legend["Legend"]')
            lines.append('  Added["Added"]')
            lines.append('  Modified["Modified"]')
            lines.append('  Removed["Removed"]')
            lines.append('  style Added fill:#90EE90')
            lines.append('  style Modified fill:#FFD700')
            lines.append('  style Removed fill:#FFB6C1')
            
            mermaid_syntax = '\n'.join(lines)
            
            return mermaid_syntax
            
        except Exception as e:
            logger.error(f"Error generating comparison Mermaid syntax: {e}", exc_info=True)
            return 'graph TD\n  Error[Error generating comparison syntax]'
