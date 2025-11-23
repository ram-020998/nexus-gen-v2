"""
Flow Parser for Process Model Enhancement

This module provides flow parsing capabilities for Appian Process Models,
extracting flow connections and building flow graphs.

Extracted from process_model_enhancement.py as part of repository refactoring.
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from .logger import get_logger

# Initialize logger
logger = get_logger()

# Import data classes from process_model_enhancement
from .process_model_enhancement import (
    Flow,
    FlowGraph,
    log_flow_extraction,
    log_parsing_error
)


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
