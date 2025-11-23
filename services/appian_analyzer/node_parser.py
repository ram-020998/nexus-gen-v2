"""
Node Parser for Process Model Enhancement

This module provides node parsing capabilities for Appian Process Models,
extracting structured information about nodes and variables.

Extracted from process_model_enhancement.py as part of repository refactoring.
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Set
from .logger import get_logger

# Initialize logger
logger = get_logger()

# Import data classes and enums from process_model_enhancement
from .process_model_enhancement import (
    NodeType,
    AssignmentType,
    NodeProperties,
    NodeDependency,
    EnhancedNode,
    VariableInfo,
    log_node_extraction,
    log_uuid_resolution,
    log_uuid_resolution_failure,
    log_parsing_error
)


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
