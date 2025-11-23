"""
Parser for Appian Process Model objects
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from ..models import ProcessModel
from .base_parser import XMLParser


class ProcessModelParser(XMLParser):
    """Parser for Process Model objects"""
    
    def __init__(self):
        super().__init__()
        self.object_lookup = {}
        self.sail_formatter = None
    
    def set_object_lookup(self, object_lookup: Dict[str, Any]):
        """Set object lookup for UUID resolution"""
        self.object_lookup = object_lookup
    
    def set_sail_formatter(self, sail_formatter: Any):
        """Set SAIL formatter for expression formatting"""
        self.sail_formatter = sail_formatter
    
    def can_parse(self, file_path: str) -> bool:
        return 'processModel/' in file_path
    
    def parse(self, root: ET.Element, file_path: str) -> Optional[ProcessModel]:
        """
        Parse process model XML with enhanced extraction
        
        Integrates NodeExtractor and FlowExtractor for enhanced parsing
        while maintaining backward compatibility with existing fields.
        
        Requirements: 9.1, 9.2
        """
        pm_port = root.find('{http://www.appian.com/ae/types/2009}process_model_port')
        if pm_port is None:
            return None
        
        pm_elem = pm_port.find('{http://www.appian.com/ae/types/2009}pm')
        if pm_elem is None:
            return None
        
        meta_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}meta')
        if meta_elem is None:
            return None
        
        uuid_elem = meta_elem.find('{http://www.appian.com/ae/types/2009}uuid')
        name_elem = meta_elem.find('{http://www.appian.com/ae/types/2009}name')
        desc_elem = meta_elem.find('{http://www.appian.com/ae/types/2009}desc')
        
        uuid = uuid_elem.text if uuid_elem is not None and uuid_elem.text else None
        
        # Parse name from string-map structure
        name = self._parse_string_map(name_elem) if name_elem is not None else None
        
        # Parse description from string-map structure  
        description = self._parse_string_map(desc_elem) if desc_elem is not None else ""
        
        if not uuid:
            return None
        
        if not name:
            name = f"Process Model {uuid.split('-')[0]}"
        
        process = ProcessModel(uuid=uuid, name=name, object_type="Process Model", description=description)
        
        # Try enhanced parsing with new extractors
        try:
            # Import here to avoid circular dependencies
            from ..process_model_enhancement import (
                NodeExtractor, FlowExtractor, log_parsing_start,
                log_parsing_complete, log_parsing_error, log_fallback_to_raw_xml
            )
            
            log_parsing_start(name)
            
            # Initialize extractors
            node_extractor = NodeExtractor(self.object_lookup, self.sail_formatter)
            
            # Extract nodes using enhanced extractor
            enhanced_nodes = []
            node_lookup = {}  # Map UUID to name for flow extraction
            
            nodes_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}nodes')
            if nodes_elem is not None:
                for node_elem in nodes_elem.findall('{http://www.appian.com/ae/types/2009}node'):
                    try:
                        enhanced_node = node_extractor.extract_node(node_elem)
                        enhanced_nodes.append(enhanced_node)
                        node_lookup[enhanced_node['uuid']] = enhanced_node['name']
                    except Exception as e:
                        # Log error but continue with other nodes
                        log_parsing_error(name, e, f"node extraction")
            
            # Initialize flow extractor with node lookup
            flow_extractor = FlowExtractor(node_lookup, self.sail_formatter)
            
            # Extract flows using enhanced extractor
            enhanced_flows = flow_extractor.extract_flows(pm_elem)
            
            # Build flow graph
            flow_graph = flow_extractor.build_flow_graph(enhanced_nodes, enhanced_flows)
            
            # Store enhanced data in process model
            process.nodes = enhanced_nodes
            process.flows = enhanced_flows
            
            # Add new fields for enhanced data
            if not hasattr(process, 'flow_graph'):
                # Dynamically add flow_graph attribute
                process.flow_graph = flow_graph
            else:
                process.flow_graph = flow_graph
            
            # Build node summary
            node_summary = self._build_node_summary(enhanced_nodes)
            if not hasattr(process, 'node_summary'):
                process.node_summary = node_summary
            else:
                process.node_summary = node_summary
            
            log_parsing_complete(name, len(enhanced_nodes), len(enhanced_flows))
            
        except Exception as e:
            # Fall back to basic parsing on error
            log_fallback_to_raw_xml(name, str(e))
            process.nodes = self._parse_nodes(pm_elem)
            process.flows = self._parse_flows(pm_elem)
            # Set empty enhanced fields
            if not hasattr(process, 'flow_graph'):
                process.flow_graph = {}
            if not hasattr(process, 'node_summary'):
                process.node_summary = {}
        
        # Continue with existing parsing for other fields (backward compatibility)
        process.variables = self._parse_variables(pm_elem)
        process.interfaces = self._parse_interfaces(pm_elem)
        process.rules = self._parse_rules(pm_elem)
        process.business_logic = self._extract_complete_business_logic(pm_elem)
        process.security = self._parse_security(root)
        
        # Extract raw XML and all elements
        process.raw_xml = self.extract_raw_xml(root)
        process.raw_xml_data = self.extract_all_elements(root)
        
        # Extract version information
        process.version_uuid = self.extract_current_version_uuid(root)
        process.version_history = self.extract_version_history(root)
        
        return process
    
    def _extract_complete_business_logic(self, pm_elem: ET.Element) -> str:
        """Extract all business logic from process model nodes"""
        business_logic_parts = []
        
        nodes_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}nodes')
        if nodes_elem is not None:
            for node in nodes_elem.findall('{http://www.appian.com/ae/types/2009}node'):
                ac_elem = node.find('{http://www.appian.com/ae/types/2009}ac')
                if ac_elem is not None:
                    # Get node name
                    name_elem = ac_elem.find('{http://www.appian.com/ae/types/2009}name')
                    node_name = name_elem.text if name_elem is not None and name_elem.text else "Unnamed Node"
                    
                    node_logic = f"=== NODE: {node_name} ===\\n"
                    
                    # Extract all expressions and logic from AC
                    for child in ac_elem.iter():
                        if child.text and child.text.strip():
                            # Skip simple values and focus on expressions/logic
                            text = child.text.strip()
                            if any(keyword in text for keyword in ['rule!', '#"', 'if(', 'and(', 'or(', 'not(', 'local!', 'pv!', 'rv!', 'cons!', 'fn!']):
                                tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                                node_logic += f"{tag_name}: {text}\\n"
                    
                    # Extract output expressions
                    output_elem = ac_elem.find('{http://www.appian.com/ae/types/2009}output-exprs')
                    if output_elem is not None and output_elem.text and output_elem.text.strip():
                        node_logic += f"output-exprs: {output_elem.text.strip()}\\n"
                    
                    if node_logic != f"=== NODE: {node_name} ===\\n":
                        business_logic_parts.append(node_logic)
        
        return "\\n".join(business_logic_parts) if business_logic_parts else ""
    
    def _parse_string_map(self, elem: ET.Element) -> str:
        """Parse string-map structure to extract localized text"""
        if elem is None:
            return ""
        
        string_map = elem.find('a:string-map', self.namespaces)
        if string_map is not None:
            # Look for English locale pair
            for pair in string_map.findall('a:pair', self.namespaces):
                locale = pair.find('a:locale', self.namespaces)
                value = pair.find('a:value', self.namespaces)
                
                if locale is not None and value is not None:
                    lang = locale.get('lang', '')
                    if lang == 'en':  # English locale
                        return value.text.strip() if value.text else ""
            
            # Fallback to first pair if no English found
            first_pair = string_map.find('a:pair', self.namespaces)
            if first_pair is not None:
                value = first_pair.find('a:value', self.namespaces)
                if value is not None:
                    return value.text.strip() if value.text else ""
        
        # Fallback to direct text if no string-map
        return elem.text.strip() if elem.text else ""
    
    def _parse_variables(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse process variables with proper names and types"""
        variables = []
        
        pvs_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}pvs')
        if pvs_elem is not None:
            for pv in pvs_elem.findall('{http://www.appian.com/ae/types/2009}pv'):
                # Parse name from string-map
                name_elem = pv.find('{http://www.appian.com/ae/types/2009}name')
                name = self._parse_string_map(name_elem) if name_elem is not None else ""
                
                # Parse type
                type_elem = pv.find('{http://www.appian.com/ae/types/2009}type')
                var_type = type_elem.text if type_elem is not None and type_elem.text else ""
                
                # Parse parameter flag
                param_elem = pv.find('{http://www.appian.com/ae/types/2009}parameter')
                is_parameter = param_elem.text == 'true' if param_elem is not None else False
                
                # Parse required flag
                req_elem = pv.find('{http://www.appian.com/ae/types/2009}required')
                is_required = req_elem.text == 'true' if req_elem is not None else False
                
                # Parse multiple flag
                mult_elem = pv.find('{http://www.appian.com/ae/types/2009}multiple')
                is_multiple = mult_elem.text == 'true' if mult_elem is not None else False
                
                if name:  # Only add if name exists
                    var_data = {
                        "name": name,
                        "type": var_type,
                        "parameter": is_parameter,
                        "required": is_required,
                        "multiple": is_multiple
                    }
                    variables.append(var_data)
        
        return variables
    
    def _parse_interfaces(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse interfaces used in the process model"""
        interfaces = []
        interface_uuids = set()
        
        # Extract from form-map (these are definitely interfaces)
        form_map = pm_elem.find('{http://www.appian.com/ae/types/2009}form-map')
        if form_map is not None:
            for ui_expr in form_map.findall('.//{http://www.appian.com/ae/types/2009}uiExpressionForm'):
                expr_elem = ui_expr.find('{http://www.appian.com/ae/types/2009}expression')
                if expr_elem is not None and expr_elem.text:
                    # Extract UUID from expression like #\"_a-uuid\"
                    import re
                    uuid_match = re.search(r'#\"(_a-[^\"]+)\"', expr_elem.text)
                    if uuid_match:
                        interface_uuid = uuid_match.group(1)
                        interface_uuids.add(interface_uuid)
        
        # Convert to list with resolved names and filter by object type
        for uuid in interface_uuids:
            # Check if this UUID is actually an interface in our lookup
            obj = self.object_lookup.get(uuid) if hasattr(self, 'object_lookup') else None
            if obj and obj.get('object_type') == 'Interface':
                interfaces.append({
                    "uuid": uuid,
                    "name": "Unknown"  # Will be resolved later
                })
        
        return interfaces
    
    def _parse_rules(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse rules used in the process model"""
        rules = []
        rule_uuids = set()
        
        # Extract from AC (activity class) elements - these contain business logic
        nodes_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}nodes')
        if nodes_elem is not None:
            for node in nodes_elem.findall('{http://www.appian.com/ae/types/2009}node'):
                ac_elem = node.find('{http://www.appian.com/ae/types/2009}ac')
                if ac_elem is not None:
                    # Look for rule references in output expressions and other AC elements
                    for child in ac_elem.iter():
                        if child.text and 'form' not in child.tag.lower() and 'ui' not in child.tag.lower():
                            import re
                            uuid_matches = re.findall(r'#\"(_a-[^\"]+)\"', child.text)
                            for uuid in uuid_matches:
                                rule_uuids.add(uuid)
        
        # Convert to list with resolved names and filter by object type
        for uuid in rule_uuids:
            # Check if this UUID is actually a rule in our lookup
            obj = self.object_lookup.get(uuid) if hasattr(self, 'object_lookup') else None
            if obj and obj.get('object_type') == 'Expression Rule':
                rules.append({
                    "uuid": uuid,
                    "name": "Unknown"  # Will be resolved later
                })
        
        return rules
    
    def _parse_nodes(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse process nodes"""
        nodes = []
        nodes_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}nodes')
        if nodes_elem is not None:
            for node_elem in nodes_elem.findall('{http://www.appian.com/ae/types/2009}node'):
                node_data = {
                    "uuid": node_elem.get('uuid'),
                    "name": self._get_element_text(node_elem, 'name'),
                    "type": self._determine_node_type(node_elem),
                    "details": self._parse_node_details(node_elem)
                }
                nodes.append(node_data)
        return nodes
    
    def _parse_flows(self, pm_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse process flows"""
        flows = []
        flows_elem = pm_elem.find('{http://www.appian.com/ae/types/2009}flows')
        if flows_elem is not None:
            for flow_elem in flows_elem.findall('{http://www.appian.com/ae/types/2009}flow'):
                flow_data = {
                    "from": self._get_element_text(flow_elem, '{http://www.appian.com/ae/types/2009}from'),
                    "to": self._get_element_text(flow_elem, '{http://www.appian.com/ae/types/2009}to'),
                    "condition": self._get_element_text(flow_elem, '{http://www.appian.com/ae/types/2009}condition')
                }
                flows.append(flow_data)
        return flows
    
    def _determine_node_type(self, node_elem: ET.Element) -> str:
        """Determine node type"""
        if node_elem.find('.//form-config') is not None:
            return "User Input Task"
        elif node_elem.find('.//expr') is not None:
            return "Script Task"
        elif node_elem.find('.//subprocess') is not None:
            return "Call Process"
        return "Unknown"
    
    def _parse_node_details(self, node_elem: ET.Element) -> Dict[str, Any]:
        """Parse node details"""
        details = {}
        
        # Look for AC (activity class) element which contains node configuration
        ac_elem = node_elem.find('{http://www.appian.com/ae/types/2009}ac')
        if ac_elem is not None:
            # Check for form configuration (User Input Task)
            form_config = ac_elem.find('.//{http://www.appian.com/ae/types/2009}form-config')
            if form_config is not None:
                ui_expr = form_config.find('.//{http://www.appian.com/ae/types/2009}uiExpressionForm')
                if ui_expr is not None:
                    expr_elem = ui_expr.find('{http://www.appian.com/ae/types/2009}expression')
                    if expr_elem is not None and expr_elem.text:
                        details["interface"] = {"uuid": expr_elem.text, "name": "Unknown"}
            
            # Check for expression (Script Task)
            expr_elem = ac_elem.find('.//{http://www.appian.com/ae/types/2009}expr')
            if expr_elem is not None and expr_elem.text:
                details["expression"] = expr_elem.text
        
        return details
    
    def _parse_security(self, root: ET.Element) -> Dict[str, Any]:
        """Parse process model security"""
        security = {"roles": []}
        role_map = root.find('roleMap')
        if role_map is not None:
            for role_elem in role_map.findall('role'):
                role_name = role_elem.get('name')
                users = [u.text for u in role_elem.findall('.//userUuid')]
                group_uuids = [g.text for g in role_elem.findall('.//groupUuid')]
                
                if users or group_uuids:
                    security["roles"].append({
                        "role": role_name,
                        "users": users,
                        "groups": [{"uuid": g, "name": "Unknown"} for g in group_uuids]
                    })
        return security
    
    def _build_node_summary(self, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Build organized node summary grouped by type
        
        Requirements: 9.1, 9.2
        
        Args:
            nodes: List of enhanced node dictionaries
            
        Returns:
            Node summary dictionary with nodes grouped by type
        """
        from ..process_model_enhancement import NodeType
        
        nodes_by_type = {}
        node_type_counts = {}
        
        for node in nodes:
            node_type = node.get('type', NodeType.UNKNOWN.value)
            
            if node_type not in nodes_by_type:
                nodes_by_type[node_type] = []
                node_type_counts[node_type] = 0
            
            nodes_by_type[node_type].append(node)
            node_type_counts[node_type] += 1
        
        return {
            'nodes_by_type': nodes_by_type,
            'total_nodes': len(nodes),
            'node_type_counts': node_type_counts
        }
