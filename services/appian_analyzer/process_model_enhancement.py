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


# ============================================================================
# BACKWARD COMPATIBILITY IMPORTS
# ============================================================================
# The following imports maintain backward compatibility after refactoring.
# Classes have been extracted to separate modules for better maintainability:
# - node_parser.py: NodeExtractor, VariableExtractor
# - flow_parser.py: FlowExtractor
# - process_model_analyzer.py: NodeComparator, ProcessModelRenderer, FlowDiagramGenerator
#
# Requirements: 7.3 (Import Preservation)
# ============================================================================

# Import extracted classes for backward compatibility
from .node_parser import NodeExtractor, VariableExtractor
from .flow_parser import FlowExtractor
from .process_model_analyzer import (
    NodeComparator,
    ProcessModelRenderer,
    FlowDiagramGenerator
)

# Export all classes to maintain public API
__all__ = [
    # Enums
    'NodeType',
    'AssignmentType',
    # Data classes
    'NodeProperties',
    'NodeDependency',
    'EnhancedNode',
    'Flow',
    'FlowGraph',
    'VariableInfo',
    'NodeSummary',
    'EnhancedProcessModel',
    'NodeComparison',
    'FlowComparison',
    'ProcessModelComparison',
    # Logging functions
    'log_parsing_start',
    'log_parsing_complete',
    'log_parsing_error',
    'log_node_extraction',
    'log_flow_extraction',
    'log_uuid_resolution',
    'log_uuid_resolution_failure',
    'log_fallback_to_raw_xml',
    'log_performance_metrics',
    'log_feature_usage',
    'log_comparison_metrics',
    'log_diagram_generation',
    # Extracted classes (backward compatibility)
    'NodeExtractor',
    'VariableExtractor',
    'FlowExtractor',
    'NodeComparator',
    'ProcessModelRenderer',
    'FlowDiagramGenerator',
]
