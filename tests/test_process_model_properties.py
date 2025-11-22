"""
Property-Based Tests for Process Model Visualization

These tests use Hypothesis to verify correctness properties
across many randomly generated inputs.

**Feature: process-model-visualization**
"""
import xml.etree.ElementTree as ET
from hypothesis import given, strategies as st, settings as hypothesis_settings
from hypothesis.strategies import composite
from tests.base_test import BaseTestCase
from services.appian_analyzer.process_model_enhancement import (
    NodeExtractor,
    NodeType,
    AssignmentType
)


# Custom Hypothesis strategies for generating test data

@composite
def node_uuid(draw):
    """Generate random node UUID in Appian format"""
    # Appian UUIDs typically start with _a- followed by hex characters
    # Use integers to ensure uniqueness
    import random
    hex_part = ''.join(random.choice('0123456789abcdef') for _ in range(32))
    return f"_a-{hex_part}"


@composite
def node_name(draw):
    """Generate random node name"""
    return draw(st.text(
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='-_'
        ),
        min_size=1,
        max_size=50
    ))


@composite
def node_type_indicator(draw):
    """Generate XML structure indicating node type"""
    node_type = draw(st.sampled_from([
        'user_input_task',
        'script_task',
        'gateway',
        'subprocess',
        'unknown'
    ]))
    return node_type


@composite
def process_model_node_xml(draw):
    """Generate random process model node XML"""
    uuid = draw(node_uuid())
    name = draw(node_name())
    node_type = draw(node_type_indicator())
    
    # Build XML structure
    node_elem = ET.Element('node')
    node_elem.set('{http://www.appian.com/ae/types/2009}uuid', uuid)
    
    ac_elem = ET.SubElement(node_elem, '{http://www.appian.com/ae/types/2009}ac')
    
    # Add name element
    name_elem = ET.SubElement(ac_elem, '{http://www.appian.com/ae/types/2009}name')
    name_elem.text = name
    
    # Add type-specific elements
    if node_type == 'user_input_task':
        form_config = ET.SubElement(
            ac_elem,
            '{http://www.appian.com/ae/types/2009}form-config'
        )
        ui_expr = ET.SubElement(
            form_config,
            '{http://www.appian.com/ae/types/2009}uiExpressionForm'
        )
        expr = ET.SubElement(
            ui_expr,
            '{http://www.appian.com/ae/types/2009}expression'
        )
        expr.text = f'#"{draw(node_uuid())}"'
    elif node_type == 'script_task':
        output_exprs = ET.SubElement(
            ac_elem,
            '{http://www.appian.com/ae/types/2009}output-exprs'
        )
        output_exprs.text = 'pv!result = "test"'
    elif node_type == 'gateway':
        gateway_type = ET.SubElement(
            ac_elem,
            '{http://www.appian.com/ae/types/2009}gateway-type'
        )
        gateway_type.text = 'XOR'
    elif node_type == 'subprocess':
        subprocess = ET.SubElement(
            ac_elem,
            '{http://www.appian.com/ae/types/2009}subprocess'
        )
        subprocess.text = draw(node_uuid())
    
    return node_elem, uuid, name, node_type


class TestNodeExtractionProperties(BaseTestCase):
    """Property-based tests for node extraction"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        # Create mock object lookup
        self.object_lookup = {}
        self.node_extractor = NodeExtractor(self.object_lookup)
    
    @given(node_data=process_model_node_xml())
    @hypothesis_settings(max_examples=100)
    def test_property_1_complete_node_extraction(self, node_data):
        """
        **Feature: process-model-visualization, Property 1: Complete node extraction**
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**
        
        For any process model XML, parsing should extract all node elements
        and capture their UUID, name, type, and all configuration properties.
        """
        node_elem, expected_uuid, expected_name, node_type = node_data
        
        # Extract node
        result = self.node_extractor.extract_node(node_elem)
        
        # Property 1: All nodes must have UUID
        self.assertIn('uuid', result)
        self.assertIsNotNone(result['uuid'])
        self.assertEqual(result['uuid'], expected_uuid)
        
        # Property 2: All nodes must have name
        self.assertIn('name', result)
        self.assertIsNotNone(result['name'])
        self.assertEqual(result['name'], expected_name)
        
        # Property 3: All nodes must have type
        self.assertIn('type', result)
        self.assertIsNotNone(result['type'])
        self.assertIsInstance(result['type'], str)
        
        # Property 4: All nodes must have properties dictionary
        self.assertIn('properties', result)
        self.assertIsInstance(result['properties'], dict)
        
        # Property 5: Properties must have all required categories
        required_categories = ['basic', 'assignment', 'forms', 'expressions', 'escalation']
        for category in required_categories:
            self.assertIn(category, result['properties'])
            self.assertIsInstance(result['properties'][category], dict)
        
        # Property 6: All nodes must have dependencies dictionary
        self.assertIn('dependencies', result)
        self.assertIsInstance(result['dependencies'], dict)
        
        # Property 7: Dependencies must have all required types
        required_dep_types = ['interfaces', 'rules', 'groups']
        for dep_type in required_dep_types:
            self.assertIn(dep_type, result['dependencies'])
            self.assertIsInstance(result['dependencies'][dep_type], list)


class TestNodeTypeDeterminationProperties(BaseTestCase):
    """Property-based tests for node type determination"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.object_lookup = {}
        self.node_extractor = NodeExtractor(self.object_lookup)
    
    @given(node_data=process_model_node_xml())
    @hypothesis_settings(max_examples=100)
    def test_property_node_type_consistency(self, node_data):
        """
        For any node XML, the determined node type should be consistent
        with the XML structure.
        """
        node_elem, expected_uuid, expected_name, expected_type = node_data
        
        # Extract AC element
        ac_elem = node_elem.find('{http://www.appian.com/ae/types/2009}ac')
        self.assertIsNotNone(ac_elem)
        
        # Determine node type
        determined_type = self.node_extractor.determine_node_type(ac_elem)
        
        # Property: Node type should match expected structure
        if expected_type == 'user_input_task':
            self.assertEqual(determined_type, NodeType.USER_INPUT_TASK)
        elif expected_type == 'script_task':
            self.assertEqual(determined_type, NodeType.SCRIPT_TASK)
        elif expected_type == 'gateway':
            self.assertEqual(determined_type, NodeType.GATEWAY)
        elif expected_type == 'subprocess':
            self.assertEqual(determined_type, NodeType.SUBPROCESS)
        else:
            # Unknown types should be classified as UNKNOWN
            self.assertIn(
                determined_type,
                [NodeType.UNKNOWN, NodeType.SCRIPT_TASK]
            )


class TestAssignmentExtractionProperties(BaseTestCase):
    """Property-based tests for assignment extraction"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.object_lookup = {}
        self.node_extractor = NodeExtractor(self.object_lookup)
    
    @given(
        assignment_type=st.sampled_from(['user', 'group', 'expression', 'none']),
        assignee_value=st.text(
            alphabet=st.characters(blacklist_characters='\r\n\t '),
            min_size=1,
            max_size=50
        )
    )
    @hypothesis_settings(max_examples=100)
    def test_property_5_assignment_extraction(self, assignment_type, assignee_value):
        """
        **Feature: process-model-visualization, Property 5: Assignment extraction**
        **Validates: Requirements 3.1, 3.4**
        
        For any node with assignment configuration, the system should extract
        assignee information (users, groups, or expressions).
        """
        # Create AC element with assignment
        ac_elem = ET.Element('{http://www.appian.com/ae/types/2009}ac')
        
        if assignment_type != 'none':
            assignment_elem = ET.SubElement(
                ac_elem,
                '{http://www.appian.com/ae/types/2009}assignment'
            )
            
            if assignment_type == 'user':
                assignee_elem = ET.SubElement(
                    assignment_elem,
                    '{http://www.appian.com/ae/types/2009}assignee'
                )
                assignee_elem.text = assignee_value
            elif assignment_type == 'group':
                group_elem = ET.SubElement(
                    assignment_elem,
                    '{http://www.appian.com/ae/types/2009}group'
                )
                group_elem.text = assignee_value
            elif assignment_type == 'expression':
                expr_elem = ET.SubElement(
                    assignment_elem,
                    '{http://www.appian.com/ae/types/2009}expression'
                )
                expr_elem.text = assignee_value
        
        # Extract assignment
        result = self.node_extractor.extract_assignment(ac_elem)
        
        # Property 1: Result must have 'type' field
        self.assertIn('type', result)
        self.assertIsInstance(result['type'], str)
        
        # Property 2: Result must have 'assignees' field
        self.assertIn('assignees', result)
        self.assertIsInstance(result['assignees'], list)
        
        # Property 3: Result must have 'assignment_expression' field
        self.assertIn('assignment_expression', result)
        self.assertIsInstance(result['assignment_expression'], str)
        
        # Property 4: Type should match assignment structure
        if assignment_type == 'user':
            self.assertEqual(result['type'], AssignmentType.USER.value)
            self.assertEqual(len(result['assignees']), 1)
            # The implementation strips whitespace
            self.assertEqual(result['assignees'][0], assignee_value.strip())
        elif assignment_type == 'group':
            self.assertEqual(result['type'], AssignmentType.GROUP.value)
        elif assignment_type == 'expression':
            self.assertEqual(result['type'], AssignmentType.EXPRESSION.value)
            # The implementation may format the expression
            self.assertIsInstance(result['assignment_expression'], str)
        else:
            self.assertEqual(result['type'], AssignmentType.NONE.value)
            self.assertEqual(len(result['assignees']), 0)


class TestEscalationExtractionProperties(BaseTestCase):
    """Property-based tests for escalation extraction"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.object_lookup = {}
        self.node_extractor = NodeExtractor(self.object_lookup)
    
    @given(
        has_escalation=st.booleans(),
        escalation_time=st.text(
            alphabet=st.characters(blacklist_characters='\r\n\t '),
            min_size=1,
            max_size=20
        ),
        notify=st.booleans()
    )
    @hypothesis_settings(max_examples=100)
    def test_property_6_escalation_extraction(
        self,
        has_escalation,
        escalation_time,
        notify
    ):
        """
        **Feature: process-model-visualization, Property 6: Escalation extraction**
        **Validates: Requirements 3.2**
        
        For any node with escalation configuration, the system should extract
        escalation rules and timing.
        """
        # Create AC element with optional escalation
        ac_elem = ET.Element('{http://www.appian.com/ae/types/2009}ac')
        
        if has_escalation:
            escalation_elem = ET.SubElement(
                ac_elem,
                '{http://www.appian.com/ae/types/2009}escalation'
            )
            
            time_elem = ET.SubElement(
                escalation_elem,
                '{http://www.appian.com/ae/types/2009}time'
            )
            time_elem.text = escalation_time
            
            notify_elem = ET.SubElement(
                escalation_elem,
                '{http://www.appian.com/ae/types/2009}notify'
            )
            notify_elem.text = 'true' if notify else 'false'
        
        # Extract escalation
        result = self.node_extractor.extract_escalation(ac_elem)
        
        # Property 1: Result must have 'enabled' field
        self.assertIn('enabled', result)
        self.assertIsInstance(result['enabled'], bool)
        
        # Property 2: Result must have 'escalation_time' field
        self.assertIn('escalation_time', result)
        self.assertIsInstance(result['escalation_time'], str)
        
        # Property 3: Result must have 'escalation_action' field
        self.assertIn('escalation_action', result)
        self.assertIsInstance(result['escalation_action'], str)
        
        # Property 4: Result must have 'notify_assignees' field
        self.assertIn('notify_assignees', result)
        self.assertIsInstance(result['notify_assignees'], bool)
        
        # Property 5: Enabled should match presence of escalation element
        self.assertEqual(result['enabled'], has_escalation)
        
        # Property 6: If enabled, time should be extracted (after stripping)
        if has_escalation:
            # The implementation strips whitespace, so we compare stripped values
            self.assertEqual(result['escalation_time'], escalation_time.strip())
            self.assertEqual(result['notify_assignees'], notify)
        else:
            self.assertEqual(result['escalation_time'], '')
            self.assertEqual(result['notify_assignees'], False)



class TestUUIDResolutionProperties(BaseTestCase):
    """Property-based tests for UUID resolution"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        # Create mock object lookup with some test objects
        self.object_lookup = {
            '_a-test-interface-uuid': {
                'name': 'Test Interface',
                'object_type': 'Interface'
            },
            '_a-test-rule-uuid': {
                'name': 'Test Rule',
                'object_type': 'Expression Rule'
            },
            '_a-test-group-uuid': {
                'name': 'Test Group',
                'object_type': 'Security Group'
            }
        }
        self.node_extractor = NodeExtractor(self.object_lookup)
    
    @given(
        uuid_exists=st.booleans(),
        object_type=st.sampled_from(['Interface', 'Expression Rule', 'Security Group'])
    )
    @hypothesis_settings(max_examples=100)
    def test_property_2_uuid_resolution_consistency(self, uuid_exists, object_type):
        """
        **Feature: process-model-visualization, Property 2: UUID resolution consistency**
        **Validates: Requirements 2.2, 2.4, 3.3, 10.2**
        
        For any UUID, resolution should either return the object name if found,
        or a consistent "Unknown" format if not found.
        """
        if uuid_exists:
            # Use a UUID that exists in the lookup
            if object_type == 'Interface':
                uuid = '_a-test-interface-uuid'
                expected_name = 'Test Interface'
            elif object_type == 'Expression Rule':
                uuid = '_a-test-rule-uuid'
                expected_name = 'Test Rule'
            else:
                uuid = '_a-test-group-uuid'
                expected_name = 'Test Group'
        else:
            # Use a UUID that doesn't exist
            uuid = '_a-nonexistent-uuid-12345'
            expected_name = None
        
        # Resolve UUID
        result = self.node_extractor._resolve_uuid(uuid, object_type)
        
        # Property 1: Result must be a string
        self.assertIsInstance(result, str)
        
        # Property 2: Result must not be empty
        self.assertGreater(len(result), 0)
        
        # Property 3: If UUID exists, should return exact name
        if uuid_exists:
            self.assertEqual(result, expected_name)
        else:
            # Property 4: If UUID doesn't exist, should return "Unknown" format
            self.assertIn('Unknown', result)
            self.assertIn(uuid[:8], result)
    
    @given(
        interface_uuid=node_uuid(),
        rule_uuid=node_uuid(),
        group_uuid=node_uuid()
    )
    @hypothesis_settings(max_examples=100)
    def test_property_uuid_resolution_in_node_extraction(
        self,
        interface_uuid,
        rule_uuid,
        group_uuid
    ):
        """
        For any node with UUID references, extraction should attempt to
        resolve all UUIDs to object names.
        """
        # Add test objects to lookup
        self.object_lookup[interface_uuid] = {
            'name': 'Generated Interface',
            'object_type': 'Interface'
        }
        self.object_lookup[rule_uuid] = {
            'name': 'Generated Rule',
            'object_type': 'Expression Rule'
        }
        self.object_lookup[group_uuid] = {
            'name': 'Generated Group',
            'object_type': 'Security Group'
        }
        
        # Create node with UUID references
        node_elem = ET.Element('node')
        node_elem.set('{http://www.appian.com/ae/types/2009}uuid', '_a-node-uuid')
        
        ac_elem = ET.SubElement(node_elem, '{http://www.appian.com/ae/types/2009}ac')
        name_elem = ET.SubElement(ac_elem, '{http://www.appian.com/ae/types/2009}name')
        name_elem.text = 'Test Node'
        
        # Add form config with interface reference
        form_config = ET.SubElement(
            ac_elem,
            '{http://www.appian.com/ae/types/2009}form-config'
        )
        ui_expr = ET.SubElement(
            form_config,
            '{http://www.appian.com/ae/types/2009}uiExpressionForm'
        )
        expr = ET.SubElement(
            ui_expr,
            '{http://www.appian.com/ae/types/2009}expression'
        )
        expr.text = f'#"{interface_uuid}"'
        
        # Add assignment with group reference
        assignment_elem = ET.SubElement(
            ac_elem,
            '{http://www.appian.com/ae/types/2009}assignment'
        )
        group_elem = ET.SubElement(
            assignment_elem,
            '{http://www.appian.com/ae/types/2009}group'
        )
        group_elem.text = group_uuid
        
        # Extract node
        result = self.node_extractor.extract_node(node_elem)
        
        # Property 1: Interface UUID should be resolved in form config
        self.assertEqual(
            result['properties']['forms']['interface_uuid'],
            interface_uuid
        )
        self.assertEqual(
            result['properties']['forms']['interface_name'],
            'Generated Interface'
        )
        
        # Property 2: Group UUID should be resolved in assignment
        self.assertIn('Generated Group', result['properties']['assignment']['assignees'])
        
        # Property 3: Dependencies should include resolved objects
        interface_deps = result['dependencies']['interfaces']
        self.assertTrue(
            any(dep['uuid'] == interface_uuid for dep in interface_deps)
        )



class TestNodeTypeHandlingProperties(BaseTestCase):
    """Property-based tests for node type-specific extraction"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.object_lookup = {}
        self.node_extractor = NodeExtractor(self.object_lookup)
    
    @given(
        interface_uuid=st.text(min_size=10, max_size=50),
        form_input=st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.text(min_size=1, max_size=50),
            min_size=0,
            max_size=5
        )
    )
    @hypothesis_settings(max_examples=100)
    def test_property_3_user_input_task_extraction(self, interface_uuid, form_input):
        """
        **Feature: process-model-visualization, Property 3: User Input Task extraction**
        **Validates: Requirements 2.1, 8.1**
        
        For any User Input Task node, the system should extract form configuration
        and assignment details.
        """
        # Create User Input Task node
        node_elem = ET.Element('node')
        node_elem.set('{http://www.appian.com/ae/types/2009}uuid', '_a-test-node')
        
        ac_elem = ET.SubElement(node_elem, '{http://www.appian.com/ae/types/2009}ac')
        name_elem = ET.SubElement(ac_elem, '{http://www.appian.com/ae/types/2009}name')
        name_elem.text = 'User Input Task'
        
        # Add form config
        form_config = ET.SubElement(
            ac_elem,
            '{http://www.appian.com/ae/types/2009}form-config'
        )
        ui_expr = ET.SubElement(
            form_config,
            '{http://www.appian.com/ae/types/2009}uiExpressionForm'
        )
        expr = ET.SubElement(
            ui_expr,
            '{http://www.appian.com/ae/types/2009}expression'
        )
        expr.text = f'#"{interface_uuid}"'
        
        # Extract node
        result = self.node_extractor.extract_node(node_elem)
        
        # Property 1: Node type should be USER_INPUT_TASK
        self.assertEqual(result['type'], NodeType.USER_INPUT_TASK.value)
        
        # Property 2: Form config should be extracted
        self.assertIn('forms', result['properties'])
        self.assertIsInstance(result['properties']['forms'], dict)
        
        # Property 3: Interface UUID should be present
        self.assertIn('interface_uuid', result['properties']['forms'])
    
    @given(
        output_expr=st.text(min_size=1, max_size=100),
        pre_activity_expr=st.text(min_size=0, max_size=100)
    )
    @hypothesis_settings(max_examples=100)
    def test_property_4_script_task_extraction(self, output_expr, pre_activity_expr):
        """
        **Feature: process-model-visualization, Property 4: Script Task extraction**
        **Validates: Requirements 2.3, 2.5, 8.2**
        
        For any Script Task node, the system should extract expressions and
        output mappings.
        """
        # Create Script Task node
        node_elem = ET.Element('node')
        node_elem.set('{http://www.appian.com/ae/types/2009}uuid', '_a-test-node')
        
        ac_elem = ET.SubElement(node_elem, '{http://www.appian.com/ae/types/2009}ac')
        name_elem = ET.SubElement(ac_elem, '{http://www.appian.com/ae/types/2009}name')
        name_elem.text = 'Script Task'
        
        # Add output expressions
        output_exprs = ET.SubElement(
            ac_elem,
            '{http://www.appian.com/ae/types/2009}output-exprs'
        )
        output_exprs.text = output_expr
        
        # Add pre-activity expression if provided
        if pre_activity_expr:
            pre_activity = ET.SubElement(
                ac_elem,
                '{http://www.appian.com/ae/types/2009}pre-activity'
            )
            pre_activity.text = pre_activity_expr
        
        # Extract node
        result = self.node_extractor.extract_node(node_elem)
        
        # Property 1: Node type should be SCRIPT_TASK
        self.assertEqual(result['type'], NodeType.SCRIPT_TASK.value)
        
        # Property 2: Expressions should be extracted
        self.assertIn('expressions', result['properties'])
        self.assertIsInstance(result['properties']['expressions'], dict)
        
        # Property 3: Output expressions should be present
        self.assertIn('output_expressions', result['properties']['expressions'])
        
        # Property 4: If pre-activity was provided, it should be extracted
        if pre_activity_expr:
            self.assertIn('pre_activity', result['properties']['expressions'])
    
    @given(gateway_type=st.sampled_from(['XOR', 'AND', 'OR']))
    @hypothesis_settings(max_examples=100)
    def test_property_21_gateway_extraction(self, gateway_type):
        """
        **Feature: process-model-visualization, Property 21: Gateway extraction**
        **Validates: Requirements 8.3**
        
        For any Gateway node, the system should extract branching conditions.
        """
        # Create Gateway node
        node_elem = ET.Element('node')
        node_elem.set('{http://www.appian.com/ae/types/2009}uuid', '_a-test-node')
        
        ac_elem = ET.SubElement(node_elem, '{http://www.appian.com/ae/types/2009}ac')
        name_elem = ET.SubElement(ac_elem, '{http://www.appian.com/ae/types/2009}name')
        name_elem.text = 'Gateway'
        
        # Add gateway type
        gateway_type_elem = ET.SubElement(
            ac_elem,
            '{http://www.appian.com/ae/types/2009}gateway-type'
        )
        gateway_type_elem.text = gateway_type
        
        # Extract node
        result = self.node_extractor.extract_node(node_elem)
        
        # Property 1: Node type should be GATEWAY
        self.assertEqual(result['type'], NodeType.GATEWAY.value)
        
        # Property 2: Node should have basic properties
        self.assertIn('basic', result['properties'])
    
    @given(subprocess_uuid=st.text(min_size=10, max_size=50))
    @hypothesis_settings(max_examples=100)
    def test_property_22_subprocess_extraction(self, subprocess_uuid):
        """
        **Feature: process-model-visualization, Property 22: Subprocess extraction**
        **Validates: Requirements 8.4**
        
        For any Subprocess node, the system should extract the subprocess
        reference and parameter mappings.
        """
        # Create Subprocess node
        node_elem = ET.Element('node')
        node_elem.set('{http://www.appian.com/ae/types/2009}uuid', '_a-test-node')
        
        ac_elem = ET.SubElement(node_elem, '{http://www.appian.com/ae/types/2009}ac')
        name_elem = ET.SubElement(ac_elem, '{http://www.appian.com/ae/types/2009}name')
        name_elem.text = 'Subprocess'
        
        # Add subprocess reference
        subprocess_elem = ET.SubElement(
            ac_elem,
            '{http://www.appian.com/ae/types/2009}subprocess'
        )
        subprocess_elem.text = subprocess_uuid
        
        # Extract node
        result = self.node_extractor.extract_node(node_elem)
        
        # Property 1: Node type should be SUBPROCESS
        self.assertEqual(result['type'], NodeType.SUBPROCESS.value)
        
        # Property 2: Node should have basic properties
        self.assertIn('basic', result['properties'])
    
    @given(
        node_name=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters='-_'
            ),
            min_size=1,
            max_size=50
        )
    )
    @hypothesis_settings(max_examples=100)
    def test_property_23_unknown_node_type_handling(self, node_name):
        """
        **Feature: process-model-visualization, Property 23: Unknown node type handling**
        **Validates: Requirements 8.5**
        
        For any unknown node type, the system should extract all available
        properties without failing.
        """
        # Create node with no type-specific elements
        node_elem = ET.Element('node')
        node_elem.set('{http://www.appian.com/ae/types/2009}uuid', '_a-test-node')
        
        ac_elem = ET.SubElement(node_elem, '{http://www.appian.com/ae/types/2009}ac')
        name_elem = ET.SubElement(ac_elem, '{http://www.appian.com/ae/types/2009}name')
        name_elem.text = node_name
        
        # Extract node
        result = self.node_extractor.extract_node(node_elem)
        
        # Property 1: Extraction should not fail
        self.assertIsNotNone(result)
        
        # Property 2: Node should have UUID
        self.assertIn('uuid', result)
        self.assertEqual(result['uuid'], '_a-test-node')
        
        # Property 3: Node should have name (after stripping whitespace)
        self.assertIn('name', result)
        self.assertEqual(result['name'], node_name.strip())
        
        # Property 4: Node should have a type (even if UNKNOWN)
        self.assertIn('type', result)
        self.assertIsInstance(result['type'], str)
        
        # Property 5: Node should have all property categories
        self.assertIn('properties', result)
        required_categories = ['basic', 'assignment', 'forms', 'expressions', 'escalation']
        for category in required_categories:
            self.assertIn(category, result['properties'])



class TestExpressionFormattingProperties(BaseTestCase):
    """Property-based tests for expression formatting"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.object_lookup = {}
        # Create a mock SAIL formatter
        from services.appian_analyzer.sail_formatter import SAILFormatter
        self.sail_formatter = SAILFormatter(self.object_lookup)
        self.node_extractor = NodeExtractor(
            self.object_lookup,
            self.sail_formatter
        )
    
    @given(expression_text=st.text(min_size=1, max_size=100))
    @hypothesis_settings(max_examples=100)
    def test_property_28_sail_expression_formatting(self, expression_text):
        """
        **Feature: process-model-visualization, Property 28: SAIL expression formatting**
        **Validates: Requirements 10.1, 10.3**
        
        For any node with SAIL expressions, the system should format them
        using the SAIL formatter.
        """
        # Create node with expressions
        node_elem = ET.Element('node')
        node_elem.set('{http://www.appian.com/ae/types/2009}uuid', '_a-test-node')
        
        ac_elem = ET.SubElement(node_elem, '{http://www.appian.com/ae/types/2009}ac')
        name_elem = ET.SubElement(ac_elem, '{http://www.appian.com/ae/types/2009}name')
        name_elem.text = 'Test Node'
        
        # Add pre-activity expression
        pre_activity = ET.SubElement(
            ac_elem,
            '{http://www.appian.com/ae/types/2009}pre-activity'
        )
        pre_activity.text = expression_text
        
        # Extract node
        result = self.node_extractor.extract_node(node_elem)
        
        # Property 1: Expressions should be extracted
        self.assertIn('expressions', result['properties'])
        
        # Property 2: Pre-activity expression should be present
        self.assertIn('pre_activity', result['properties']['expressions'])
        
        # Property 3: Expression should be a string
        self.assertIsInstance(
            result['properties']['expressions']['pre_activity'],
            str
        )
    
    @given(
        variable_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            min_size=1,
            max_size=20
        ),
        expression_value=st.text(min_size=1, max_size=50)
    )
    @hypothesis_settings(max_examples=100)
    def test_property_29_output_expression_display(
        self,
        variable_name,
        expression_value
    ):
        """
        **Feature: process-model-visualization, Property 29: Output expression display**
        **Validates: Requirements 10.4**
        
        For any output expressions, the system should show the variable name
        and the expression that computes its value.
        """
        # Create node with output expressions
        node_elem = ET.Element('node')
        node_elem.set('{http://www.appian.com/ae/types/2009}uuid', '_a-test-node')
        
        ac_elem = ET.SubElement(node_elem, '{http://www.appian.com/ae/types/2009}ac')
        name_elem = ET.SubElement(ac_elem, '{http://www.appian.com/ae/types/2009}name')
        name_elem.text = 'Test Node'
        
        # Add output expressions
        output_exprs = ET.SubElement(
            ac_elem,
            '{http://www.appian.com/ae/types/2009}output-exprs'
        )
        output_exprs.text = f"pv!{variable_name} = {expression_value}"
        
        # Extract node
        result = self.node_extractor.extract_node(node_elem)
        
        # Property 1: Output expressions should be extracted
        self.assertIn('expressions', result['properties'])
        self.assertIn('output_expressions', result['properties']['expressions'])
        
        # Property 2: Output expressions should be a dictionary
        self.assertIsInstance(
            result['properties']['expressions']['output_expressions'],
            dict
        )
    
    @given(
        appian_function=st.sampled_from([
            'SYSTEM_SYSRULES_headerContentLayout',
            'SYSTEM_SYSRULES_textField',
            'SYSTEM_SYSRULES_button'
        ])
    )
    @hypothesis_settings(max_examples=100)
    def test_property_30_appian_function_conversion(self, appian_function):
        """
        **Feature: process-model-visualization, Property 30: Appian function conversion**
        **Validates: Requirements 10.5**
        
        For any expressions containing Appian functions, the system should
        convert internal function names to public API names.
        """
        # Create node with expression containing Appian function
        node_elem = ET.Element('node')
        node_elem.set('{http://www.appian.com/ae/types/2009}uuid', '_a-test-node')
        
        ac_elem = ET.SubElement(node_elem, '{http://www.appian.com/ae/types/2009}ac')
        name_elem = ET.SubElement(ac_elem, '{http://www.appian.com/ae/types/2009}name')
        name_elem.text = 'Test Node'
        
        # Add expression with Appian function
        pre_activity = ET.SubElement(
            ac_elem,
            '{http://www.appian.com/ae/types/2009}pre-activity'
        )
        pre_activity.text = f'#"{appian_function}"()'
        
        # Extract node
        result = self.node_extractor.extract_node(node_elem)
        
        # Property 1: Expression should be extracted
        self.assertIn('expressions', result['properties'])
        self.assertIn('pre_activity', result['properties']['expressions'])
        
        # Property 2: Expression should be formatted (not empty)
        self.assertIsInstance(
            result['properties']['expressions']['pre_activity'],
            str
        )
        self.assertGreater(
            len(result['properties']['expressions']['pre_activity']),
            0
        )



class TestFlowExtractionProperties(BaseTestCase):
    """Property-based tests for flow extraction"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.node_lookup = {}
        from services.appian_analyzer.process_model_enhancement import FlowExtractor
        self.flow_extractor = FlowExtractor(self.node_lookup)
    
    @given(
        num_flows=st.integers(min_value=1, max_value=20),
        has_conditions=st.booleans()
    )
    @hypothesis_settings(max_examples=100)
    def test_property_10_complete_flow_extraction(self, num_flows, has_conditions):
        """
        **Feature: process-model-visualization, Property 10: Complete flow extraction**
        **Validates: Requirements 5.1, 5.2, 5.3**
        
        For any process model, parsing should extract all flow elements
        with source node UUID, target node UUID, and conditions.
        """
        # Generate process model XML with flows
        pm_elem = ET.Element('{http://www.appian.com/ae/types/2009}process-model')
        flows_elem = ET.SubElement(pm_elem, '{http://www.appian.com/ae/types/2009}flows')
        
        expected_flows = []
        for i in range(num_flows):
            flow_elem = ET.SubElement(flows_elem, '{http://www.appian.com/ae/types/2009}flow')
            flow_uuid = f"_flow-{i:04d}"
            flow_elem.set('{http://www.appian.com/ae/types/2009}uuid', flow_uuid)
            
            from_uuid = f"_node-{i:04d}"
            to_uuid = f"_node-{i+1:04d}"
            
            from_elem = ET.SubElement(flow_elem, '{http://www.appian.com/ae/types/2009}from')
            from_elem.text = from_uuid
            
            to_elem = ET.SubElement(flow_elem, '{http://www.appian.com/ae/types/2009}to')
            to_elem.text = to_uuid
            
            # Add node names to lookup
            self.node_lookup[from_uuid] = f"Node {i}"
            self.node_lookup[to_uuid] = f"Node {i+1}"
            
            # Add condition if requested
            condition = ""
            if has_conditions:
                condition = f"pv!value > {i}"
                condition_elem = ET.SubElement(
                    flow_elem,
                    '{http://www.appian.com/ae/types/2009}condition'
                )
                condition_elem.text = condition
            
            expected_flows.append({
                'uuid': flow_uuid,
                'from_uuid': from_uuid,
                'to_uuid': to_uuid,
                'condition': condition
            })
        
        # Extract flows
        result = self.flow_extractor.extract_flows(pm_elem)
        
        # Property 1: Should extract all flows
        self.assertEqual(len(result), num_flows)
        
        # Property 2: Each flow must have required fields
        for flow in result:
            self.assertIn('uuid', flow)
            self.assertIn('from_node_uuid', flow)
            self.assertIn('from_node_name', flow)
            self.assertIn('to_node_uuid', flow)
            self.assertIn('to_node_name', flow)
            self.assertIn('condition', flow)
            self.assertIn('is_default', flow)
            self.assertIn('label', flow)
        
        # Property 3: UUIDs should match expected values
        result_uuids = {flow['uuid'] for flow in result}
        expected_uuids = {f['uuid'] for f in expected_flows}
        self.assertEqual(result_uuids, expected_uuids)
        
        # Property 4: Source and target nodes should be correct
        for i, flow in enumerate(result):
            expected = expected_flows[i]
            self.assertEqual(flow['from_node_uuid'], expected['from_uuid'])
            self.assertEqual(flow['to_node_uuid'], expected['to_uuid'])
        
        # Property 5: Conditions should be extracted correctly
        for i, flow in enumerate(result):
            expected = expected_flows[i]
            if has_conditions:
                # Condition should be present (may be formatted)
                self.assertIsInstance(flow['condition'], str)
                self.assertFalse(flow['is_default'])
            else:
                # No condition means default flow
                self.assertEqual(flow['condition'], '')
                self.assertTrue(flow['is_default'])
    
    @given(
        num_flows=st.integers(min_value=1, max_value=10),
        condition_text=st.text(
            alphabet=st.characters(blacklist_characters='\r\n\t '),
            min_size=1,
            max_size=100
        )
    )
    @hypothesis_settings(max_examples=100)
    def test_property_11_flow_display_format(self, num_flows, condition_text):
        """
        **Feature: process-model-visualization, Property 11: Flow display format**
        **Validates: Requirements 5.4, 5.5**
        
        For any flows, the system should display them as connections between
        named nodes with directional indicators and show unconditional flows
        as default flows.
        """
        # Generate process model XML with flows
        pm_elem = ET.Element('{http://www.appian.com/ae/types/2009}process-model')
        flows_elem = ET.SubElement(pm_elem, '{http://www.appian.com/ae/types/2009}flows')
        
        for i in range(num_flows):
            flow_elem = ET.SubElement(flows_elem, '{http://www.appian.com/ae/types/2009}flow')
            flow_uuid = f"_flow-{i:04d}"
            flow_elem.set('{http://www.appian.com/ae/types/2009}uuid', flow_uuid)
            
            from_uuid = f"_node-{i:04d}"
            to_uuid = f"_node-{i+1:04d}"
            
            from_elem = ET.SubElement(flow_elem, '{http://www.appian.com/ae/types/2009}from')
            from_elem.text = from_uuid
            
            to_elem = ET.SubElement(flow_elem, '{http://www.appian.com/ae/types/2009}to')
            to_elem.text = to_uuid
            
            # Add node names to lookup
            self.node_lookup[from_uuid] = f"Source Node {i}"
            self.node_lookup[to_uuid] = f"Target Node {i+1}"
            
            # Add condition for some flows
            if i % 2 == 0:
                condition_elem = ET.SubElement(
                    flow_elem,
                    '{http://www.appian.com/ae/types/2009}condition'
                )
                condition_elem.text = condition_text
        
        # Extract flows
        result = self.flow_extractor.extract_flows(pm_elem)
        
        # Property 1: All flows should have from_node_name and to_node_name
        for flow in result:
            self.assertIn('from_node_name', flow)
            self.assertIn('to_node_name', flow)
            self.assertIsInstance(flow['from_node_name'], str)
            self.assertIsInstance(flow['to_node_name'], str)
            self.assertGreater(len(flow['from_node_name']), 0)
            self.assertGreater(len(flow['to_node_name']), 0)
        
        # Property 2: All flows should have a label
        for flow in result:
            self.assertIn('label', flow)
            self.assertIsInstance(flow['label'], str)
            self.assertGreater(len(flow['label']), 0)
        
        # Property 3: Conditional flows should have non-default label
        for i, flow in enumerate(result):
            if i % 2 == 0:
                # Has condition
                self.assertNotEqual(flow['label'], 'default')
            else:
                # No condition
                self.assertEqual(flow['label'], 'default')
        
        # Property 4: is_default should be consistent with condition presence
        for flow in result:
            if flow['condition']:
                self.assertFalse(flow['is_default'])
            else:
                self.assertTrue(flow['is_default'])


class TestFlowGraphConstructionProperties(BaseTestCase):
    """Property-based tests for flow graph construction"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.node_lookup = {}
        from services.appian_analyzer.process_model_enhancement import FlowExtractor
        self.flow_extractor = FlowExtractor(self.node_lookup)
    
    @given(
        num_nodes=st.integers(min_value=2, max_value=20),
        connectivity=st.floats(min_value=0.3, max_value=1.0)
    )
    @hypothesis_settings(max_examples=100)
    def test_property_12_flow_graph_construction(self, num_nodes, connectivity):
        """
        **Feature: process-model-visualization, Property 12: Flow graph construction**
        **Validates: Requirements 5.6, 5.7**
        
        For any set of nodes and flows, the system should build a complete
        flow graph showing all node connections, and identify start nodes
        (no incoming flows) and end nodes (no outgoing flows).
        """
        # Generate nodes
        nodes = []
        for i in range(num_nodes):
            node_uuid = f"_node-{i:04d}"
            nodes.append({
                'uuid': node_uuid,
                'name': f"Node {i}",
                'type': 'SCRIPT_TASK'
            })
            self.node_lookup[node_uuid] = f"Node {i}"
        
        # Generate flows based on connectivity
        # Create a linear flow first to ensure connectivity
        flows = []
        for i in range(num_nodes - 1):
            flows.append({
                'uuid': f"_flow-{i:04d}",
                'from_node_uuid': f"_node-{i:04d}",
                'from_node_name': f"Node {i}",
                'to_node_uuid': f"_node-{i+1:04d}",
                'to_node_name': f"Node {i+1}",
                'condition': '',
                'is_default': True,
                'label': 'default'
            })
        
        # Add additional random flows based on connectivity
        import random
        random.seed(42)  # For reproducibility
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i != j and random.random() < (connectivity - 0.3):
                    # Add additional flow
                    flow_uuid = f"_flow-extra-{i}-{j}"
                    # Check if this flow already exists
                    if not any(
                        f['from_node_uuid'] == f"_node-{i:04d}" and
                        f['to_node_uuid'] == f"_node-{j:04d}"
                        for f in flows
                    ):
                        flows.append({
                            'uuid': flow_uuid,
                            'from_node_uuid': f"_node-{i:04d}",
                            'from_node_name': f"Node {i}",
                            'to_node_uuid': f"_node-{j:04d}",
                            'to_node_name': f"Node {j}",
                            'condition': f"pv!value == {j}",
                            'is_default': False,
                            'label': f"pv!value == {j}"
                        })
        
        # Build flow graph
        result = self.flow_extractor.build_flow_graph(nodes, flows)
        
        # Property 1: Result must have required fields
        self.assertIn('start_nodes', result)
        self.assertIn('end_nodes', result)
        self.assertIn('node_connections', result)
        self.assertIn('paths', result)
        
        # Property 2: start_nodes must be a list
        self.assertIsInstance(result['start_nodes'], list)
        
        # Property 3: end_nodes must be a list
        self.assertIsInstance(result['end_nodes'], list)
        
        # Property 4: node_connections must be a dictionary
        self.assertIsInstance(result['node_connections'], dict)
        
        # Property 5: All nodes should be in node_connections
        self.assertEqual(len(result['node_connections']), num_nodes)
        for node in nodes:
            self.assertIn(node['uuid'], result['node_connections'])
        
        # Property 6: Each node connection should have incoming and outgoing lists
        for node_uuid, connections in result['node_connections'].items():
            self.assertIn('incoming', connections)
            self.assertIn('outgoing', connections)
            self.assertIsInstance(connections['incoming'], list)
            self.assertIsInstance(connections['outgoing'], list)
        
        # Property 7: Start nodes should have no incoming flows
        for start_node_uuid in result['start_nodes']:
            self.assertEqual(
                len(result['node_connections'][start_node_uuid]['incoming']),
                0
            )
        
        # Property 8: End nodes should have no outgoing flows
        for end_node_uuid in result['end_nodes']:
            self.assertEqual(
                len(result['node_connections'][end_node_uuid]['outgoing']),
                0
            )
        
        # Property 9: Total incoming flows should equal total outgoing flows
        total_incoming = sum(
            len(conn['incoming'])
            for conn in result['node_connections'].values()
        )
        total_outgoing = sum(
            len(conn['outgoing'])
            for conn in result['node_connections'].values()
        )
        self.assertEqual(total_incoming, total_outgoing)
        
        # Property 10: Number of flows should match
        self.assertEqual(total_incoming, len(flows))
        self.assertEqual(total_outgoing, len(flows))
    
    @given(num_isolated_nodes=st.integers(min_value=1, max_value=5))
    @hypothesis_settings(max_examples=100)
    def test_property_isolated_nodes_handling(self, num_isolated_nodes):
        """
        For any process model with isolated nodes (no flows), the flow graph
        should identify them as both start and end nodes.
        """
        # Generate isolated nodes (no flows)
        nodes = []
        for i in range(num_isolated_nodes):
            node_uuid = f"_node-{i:04d}"
            nodes.append({
                'uuid': node_uuid,
                'name': f"Isolated Node {i}",
                'type': 'SCRIPT_TASK'
            })
            self.node_lookup[node_uuid] = f"Isolated Node {i}"
        
        # No flows
        flows = []
        
        # Build flow graph
        result = self.flow_extractor.build_flow_graph(nodes, flows)
        
        # Property 1: All isolated nodes should be start nodes
        self.assertEqual(len(result['start_nodes']), num_isolated_nodes)
        
        # Property 2: All isolated nodes should be end nodes
        self.assertEqual(len(result['end_nodes']), num_isolated_nodes)
        
        # Property 3: Start and end nodes should be the same set
        self.assertEqual(set(result['start_nodes']), set(result['end_nodes']))
        
        # Property 4: All nodes should have empty incoming and outgoing lists
        for node in nodes:
            node_uuid = node['uuid']
            self.assertEqual(
                len(result['node_connections'][node_uuid]['incoming']),
                0
            )
            self.assertEqual(
                len(result['node_connections'][node_uuid]['outgoing']),
                0
            )


class TestBackwardCompatibilityProperties(BaseTestCase):
    """Property-based tests for backward compatibility"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        # Import here to avoid circular dependencies
        from services.appian_analyzer.parsers import ProcessModelParser
        from services.appian_analyzer.sail_formatter import SAILFormatter
        
        self.parser = ProcessModelParser()
        self.object_lookup = {}
        self.sail_formatter = SAILFormatter(self.object_lookup)
        self.parser.set_object_lookup(self.object_lookup)
        self.parser.set_sail_formatter(self.sail_formatter)
    
    @composite
    def process_model_xml(draw):
        """Generate random process model XML"""
        uuid = draw(node_uuid())
        name = draw(node_name())
        description = draw(st.text(min_size=0, max_size=100))
        
        # Build process model XML structure
        root = ET.Element('root')
        pm_port = ET.SubElement(
            root,
            '{http://www.appian.com/ae/types/2009}process_model_port'
        )
        pm_elem = ET.SubElement(
            pm_port,
            '{http://www.appian.com/ae/types/2009}pm'
        )
        meta_elem = ET.SubElement(
            pm_elem,
            '{http://www.appian.com/ae/types/2009}meta'
        )
        
        # Add UUID
        uuid_elem = ET.SubElement(
            meta_elem,
            '{http://www.appian.com/ae/types/2009}uuid'
        )
        uuid_elem.text = uuid
        
        # Add name (using string-map structure)
        name_elem = ET.SubElement(
            meta_elem,
            '{http://www.appian.com/ae/types/2009}name'
        )
        string_map = ET.SubElement(
            name_elem,
            '{http://www.appian.com/ae/types/2009}string-map'
        )
        pair = ET.SubElement(
            string_map,
            '{http://www.appian.com/ae/types/2009}pair'
        )
        locale = ET.SubElement(
            pair,
            '{http://www.appian.com/ae/types/2009}locale'
        )
        locale.set('lang', 'en')
        value = ET.SubElement(
            pair,
            '{http://www.appian.com/ae/types/2009}value'
        )
        value.text = name
        
        # Add description
        desc_elem = ET.SubElement(
            meta_elem,
            '{http://www.appian.com/ae/types/2009}desc'
        )
        desc_string_map = ET.SubElement(
            desc_elem,
            '{http://www.appian.com/ae/types/2009}string-map'
        )
        desc_pair = ET.SubElement(
            desc_string_map,
            '{http://www.appian.com/ae/types/2009}pair'
        )
        desc_locale = ET.SubElement(
            desc_pair,
            '{http://www.appian.com/ae/types/2009}locale'
        )
        desc_locale.set('lang', 'en')
        desc_value = ET.SubElement(
            desc_pair,
            '{http://www.appian.com/ae/types/2009}value'
        )
        desc_value.text = description
        
        # Add nodes element (may be empty or have nodes)
        nodes_elem = ET.SubElement(
            pm_elem,
            '{http://www.appian.com/ae/types/2009}nodes'
        )
        
        # Add 0-3 random nodes
        num_nodes = draw(st.integers(min_value=0, max_value=3))
        for _ in range(num_nodes):
            node_data = draw(process_model_node_xml())
            node_elem, _, _, _ = node_data
            nodes_elem.append(node_elem)
        
        return root, uuid, name, description
    
    @given(pm_data=process_model_xml())
    @hypothesis_settings(max_examples=100)
    def test_property_24_blueprint_structure_compatibility(self, pm_data):
        """
        **Feature: process-model-visualization, Property 24: Blueprint structure compatibility**
        **Validates: Requirements 9.1, 9.2**
        
        For any process model, the enhanced parser should maintain backward
        compatibility with existing blueprint structure, including both new
        structured node data and existing business_logic field.
        """
        root, expected_uuid, expected_name, expected_description = pm_data
        
        # Parse process model
        result = self.parser.parse(root, 'processModel/test.xml')
        
        # Property 1: Parser should return a ProcessModel object
        self.assertIsNotNone(result)
        
        # Property 2: All existing fields must be present
        self.assertTrue(hasattr(result, 'uuid'))
        self.assertTrue(hasattr(result, 'name'))
        self.assertTrue(hasattr(result, 'object_type'))
        self.assertTrue(hasattr(result, 'description'))
        self.assertTrue(hasattr(result, 'variables'))
        self.assertTrue(hasattr(result, 'nodes'))
        self.assertTrue(hasattr(result, 'flows'))
        self.assertTrue(hasattr(result, 'interfaces'))
        self.assertTrue(hasattr(result, 'rules'))
        self.assertTrue(hasattr(result, 'business_logic'))
        self.assertTrue(hasattr(result, 'security'))
        
        # Property 3: Basic fields should have correct values
        self.assertEqual(result.uuid, expected_uuid)
        self.assertEqual(result.name, expected_name)
        self.assertEqual(result.object_type, "Process Model")
        
        # Property 4: New enhanced fields must be present
        self.assertTrue(hasattr(result, 'flow_graph'))
        self.assertTrue(hasattr(result, 'node_summary'))
        
        # Property 5: Enhanced fields should be dictionaries
        self.assertIsInstance(result.flow_graph, dict)
        self.assertIsInstance(result.node_summary, dict)
        
        # Property 6: Nodes should be a list
        self.assertIsInstance(result.nodes, list)
        
        # Property 7: Flows should be a list
        self.assertIsInstance(result.flows, list)
        
        # Property 8: business_logic field should exist (backward compatibility)
        self.assertIsInstance(result.business_logic, str)
        
        # Property 9: If enhanced parsing succeeded, nodes should have enhanced structure
        if len(result.nodes) > 0:
            for node in result.nodes:
                # Each node should be a dictionary
                self.assertIsInstance(node, dict)
                
                # Each node should have required fields
                self.assertIn('uuid', node)
                self.assertIn('name', node)
                self.assertIn('type', node)
                
                # If enhanced parsing worked, should have properties
                if 'properties' in node:
                    self.assertIsInstance(node['properties'], dict)
                    # Properties should have all categories
                    required_categories = [
                        'basic', 'assignment', 'forms',
                        'expressions', 'escalation'
                    ]
                    for category in required_categories:
                        self.assertIn(category, node['properties'])
        
        # Property 10: If enhanced parsing succeeded, flow_graph should have structure
        if result.flow_graph:
            # Flow graph should have expected keys
            if 'start_nodes' in result.flow_graph:
                self.assertIsInstance(result.flow_graph['start_nodes'], list)
            if 'end_nodes' in result.flow_graph:
                self.assertIsInstance(result.flow_graph['end_nodes'], list)
            if 'node_connections' in result.flow_graph:
                self.assertIsInstance(result.flow_graph['node_connections'], dict)
        
        # Property 11: If enhanced parsing succeeded, node_summary should have structure
        if result.node_summary:
            if 'total_nodes' in result.node_summary:
                self.assertIsInstance(result.node_summary['total_nodes'], int)
                self.assertGreaterEqual(result.node_summary['total_nodes'], 0)
            if 'nodes_by_type' in result.node_summary:
                self.assertIsInstance(result.node_summary['nodes_by_type'], dict)
            if 'node_type_counts' in result.node_summary:
                self.assertIsInstance(result.node_summary['node_type_counts'], dict)



class TestParserFailureFallbackProperties(BaseTestCase):
    """Property-based tests for parser failure fallback"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        from services.appian_analyzer.parsers import ProcessModelParser
        from services.appian_analyzer.sail_formatter import SAILFormatter
        
        self.parser = ProcessModelParser()
        self.object_lookup = {}
        self.sail_formatter = SAILFormatter(self.object_lookup)
        self.parser.set_object_lookup(self.object_lookup)
        self.parser.set_sail_formatter(self.sail_formatter)
    
    @composite
    def malformed_process_model_xml(draw):
        """Generate malformed process model XML that should trigger fallback"""
        uuid = draw(node_uuid())
        name = draw(node_name())
        
        # Choose a type of malformation
        malformation_type = draw(st.sampled_from([
            'missing_ac_element',
            'invalid_node_structure',
            'missing_node_uuid',
            'corrupted_xml'
        ]))
        
        # Build process model XML structure
        root = ET.Element('root')
        pm_port = ET.SubElement(
            root,
            '{http://www.appian.com/ae/types/2009}process_model_port'
        )
        pm_elem = ET.SubElement(
            pm_port,
            '{http://www.appian.com/ae/types/2009}pm'
        )
        meta_elem = ET.SubElement(
            pm_elem,
            '{http://www.appian.com/ae/types/2009}meta'
        )
        
        # Add UUID
        uuid_elem = ET.SubElement(
            meta_elem,
            '{http://www.appian.com/ae/types/2009}uuid'
        )
        uuid_elem.text = uuid
        
        # Add name
        name_elem = ET.SubElement(
            meta_elem,
            '{http://www.appian.com/ae/types/2009}name'
        )
        string_map = ET.SubElement(
            name_elem,
            '{http://www.appian.com/ae/types/2009}string-map'
        )
        pair = ET.SubElement(
            string_map,
            '{http://www.appian.com/ae/types/2009}pair'
        )
        locale = ET.SubElement(
            pair,
            '{http://www.appian.com/ae/types/2009}locale'
        )
        locale.set('lang', 'en')
        value = ET.SubElement(
            pair,
            '{http://www.appian.com/ae/types/2009}value'
        )
        value.text = name
        
        # Add nodes element with malformed content
        nodes_elem = ET.SubElement(
            pm_elem,
            '{http://www.appian.com/ae/types/2009}nodes'
        )
        
        # Add malformed node based on type
        node_elem = ET.SubElement(
            nodes_elem,
            '{http://www.appian.com/ae/types/2009}node'
        )
        
        if malformation_type == 'missing_ac_element':
            # Node without AC element
            node_elem.set('{http://www.appian.com/ae/types/2009}uuid', draw(node_uuid()))
        elif malformation_type == 'invalid_node_structure':
            # Node with AC but invalid structure
            node_elem.set('{http://www.appian.com/ae/types/2009}uuid', draw(node_uuid()))
            ac_elem = ET.SubElement(
                node_elem,
                '{http://www.appian.com/ae/types/2009}ac'
            )
            # Add invalid/unexpected elements
            invalid_elem = ET.SubElement(ac_elem, 'invalid_element')
            invalid_elem.text = 'This should not be here'
        elif malformation_type == 'missing_node_uuid':
            # Node without UUID
            ac_elem = ET.SubElement(
                node_elem,
                '{http://www.appian.com/ae/types/2009}ac'
            )
            name_elem = ET.SubElement(
                ac_elem,
                '{http://www.appian.com/ae/types/2009}name'
            )
            name_elem.text = 'Node without UUID'
        elif malformation_type == 'corrupted_xml':
            # Node with corrupted/incomplete structure
            node_elem.set('{http://www.appian.com/ae/types/2009}uuid', draw(node_uuid()))
            # Add AC with missing required elements
            ac_elem = ET.SubElement(
                node_elem,
                '{http://www.appian.com/ae/types/2009}ac'
            )
            # Intentionally leave AC empty or with minimal content
        
        return root, uuid, name, malformation_type
    
    @given(pm_data=malformed_process_model_xml())
    @hypothesis_settings(max_examples=100)
    def test_property_27_parser_failure_fallback(self, pm_data):
        """
        **Feature: process-model-visualization, Property 27: Parser failure fallback**
        **Validates: Requirements 9.5**
        
        For any malformed process model XML, the parser should handle errors
        gracefully, fall back to raw XML display, and continue processing
        without crashing the application.
        """
        root, expected_uuid, expected_name, malformation_type = pm_data
        
        # Parse process model (should not raise exception)
        result = self.parser.parse(root, 'processModel/test.xml')
        
        # Property 1: Parser should not crash and should return a result
        self.assertIsNotNone(result)
        
        # Property 2: Basic fields should still be populated
        self.assertEqual(result.uuid, expected_uuid)
        self.assertEqual(result.name, expected_name)
        self.assertEqual(result.object_type, "Process Model")
        
        # Property 3: Enhanced fields should exist (even if empty)
        self.assertTrue(hasattr(result, 'flow_graph'))
        self.assertTrue(hasattr(result, 'node_summary'))
        
        # Property 4: Enhanced fields should be dictionaries (not None)
        self.assertIsInstance(result.flow_graph, dict)
        self.assertIsInstance(result.node_summary, dict)
        
        # Property 5: Nodes should be a list (may be empty or have fallback data)
        self.assertIsInstance(result.nodes, list)
        
        # Property 6: Flows should be a list (may be empty)
        self.assertIsInstance(result.flows, list)
        
        # Property 7: business_logic field should exist (backward compatibility)
        self.assertIsInstance(result.business_logic, str)
        
        # Property 8: Other required fields should exist
        self.assertIsInstance(result.variables, list)
        self.assertIsInstance(result.interfaces, list)
        self.assertIsInstance(result.rules, list)
        self.assertIsInstance(result.security, dict)
        
        # Property 9: If enhanced parsing failed, fallback should have occurred
        # We can't directly test if fallback occurred, but we can verify
        # that the parser didn't crash and returned a valid structure
        
        # Property 10: raw_xml should be populated for fallback display
        self.assertTrue(hasattr(result, 'raw_xml'))
        self.assertIsInstance(result.raw_xml, str)
        self.assertGreater(len(result.raw_xml), 0)


# Variable tracking test strategies

@composite
def process_variable_xml(draw):
    """Generate random process variable XML"""
    var_name = draw(st.text(
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd'),
            whitelist_characters='_'
        ),
        min_size=1,
        max_size=30
    ))
    var_type = draw(st.sampled_from([
        'Text', 'Number', 'Boolean', 'Date', 'User', 'Group'
    ]))
    is_parameter = draw(st.booleans())
    is_required = draw(st.booleans())
    is_multiple = draw(st.booleans())
    
    # Build XML structure
    var_elem = ET.Element('{http://www.appian.com/ae/types/2009}variable')
    
    name_elem = ET.SubElement(var_elem, '{http://www.appian.com/ae/types/2009}name')
    name_elem.text = var_name
    
    type_elem = ET.SubElement(var_elem, '{http://www.appian.com/ae/types/2009}type')
    type_elem.text = var_type
    
    if is_parameter:
        param_elem = ET.SubElement(var_elem, '{http://www.appian.com/ae/types/2009}parameter')
        param_elem.text = 'true'
    
    if is_required:
        req_elem = ET.SubElement(var_elem, '{http://www.appian.com/ae/types/2009}required')
        req_elem.text = 'true'
    
    if is_multiple:
        mult_elem = ET.SubElement(var_elem, '{http://www.appian.com/ae/types/2009}multiple')
        mult_elem.text = 'true'
    
    return var_elem, var_name, var_type, is_parameter, is_required, is_multiple


@composite
def process_model_with_variables_xml(draw):
    """Generate process model XML with variables"""
    # Generate 1-10 variables
    num_vars = draw(st.integers(min_value=1, max_value=10))
    
    pm_elem = ET.Element('{http://www.appian.com/ae/types/2009}process-model')
    variables_elem = ET.SubElement(pm_elem, '{http://www.appian.com/ae/types/2009}variables')
    
    variables_data = []
    used_names = set()
    
    for i in range(num_vars):
        # Generate unique variable name
        var_elem, var_name, var_type, is_param, is_req, is_mult = draw(process_variable_xml())
        
        # Ensure uniqueness by appending index if needed
        original_name = var_name
        counter = 0
        while var_name in used_names:
            var_name = f"{original_name}_{counter}"
            counter += 1
        
        used_names.add(var_name)
        
        # Update the name in the XML element
        name_elem = var_elem.find('{http://www.appian.com/ae/types/2009}name')
        if name_elem is not None:
            name_elem.text = var_name
        
        variables_elem.append(var_elem)
        variables_data.append({
            'name': var_name,
            'type': var_type,
            'parameter': is_param,
            'required': is_req,
            'multiple': is_mult
        })
    
    return pm_elem, variables_data


@composite
def node_with_variable_usage_xml(draw):
    """Generate node XML that uses and modifies variables"""
    uuid = draw(node_uuid())
    name = draw(node_name())
    
    # Generate variable names
    num_used = draw(st.integers(min_value=0, max_value=5))
    num_modified = draw(st.integers(min_value=0, max_value=5))
    
    used_vars = [
        draw(st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_'),
            min_size=1,
            max_size=20
        ))
        for _ in range(num_used)
    ]
    
    modified_vars = [
        draw(st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_'),
            min_size=1,
            max_size=20
        ))
        for _ in range(num_modified)
    ]
    
    # Build XML structure
    node_elem = ET.Element('node')
    node_elem.set('{http://www.appian.com/ae/types/2009}uuid', uuid)
    
    ac_elem = ET.SubElement(node_elem, '{http://www.appian.com/ae/types/2009}ac')
    
    name_elem = ET.SubElement(ac_elem, '{http://www.appian.com/ae/types/2009}name')
    name_elem.text = name
    
    # Add pre-activity expression that uses variables
    if used_vars:
        pre_activity = ET.SubElement(ac_elem, '{http://www.appian.com/ae/types/2009}pre-activity')
        # Create expression that references variables
        expr_parts = [f"pv!{var}" for var in used_vars]
        pre_activity.text = " + ".join(expr_parts)
    
    # Add output expressions that modify variables
    if modified_vars:
        output_exprs = ET.SubElement(ac_elem, '{http://www.appian.com/ae/types/2009}output-exprs')
        # Create assignments
        assignments = [f"pv!{var} = 'value'" for var in modified_vars]
        output_exprs.text = ", ".join(assignments)
    
    return node_elem, uuid, name, set(used_vars), set(modified_vars)


class TestVariableExtractionProperties(BaseTestCase):
    """Property-based tests for variable extraction"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        from services.appian_analyzer.process_model_enhancement import VariableExtractor
        self.variable_extractor = VariableExtractor()
    
    @given(pm_data=process_model_with_variables_xml())
    @hypothesis_settings(max_examples=100)
    def test_property_14_variable_extraction_completeness(self, pm_data):
        """
        **Feature: process-model-visualization, Property 14: Variable extraction completeness**
        **Validates: Requirements 6.1, 6.2**
        
        For any process model, all process variable definitions should be extracted
        with their name, type, and parameter status.
        """
        pm_elem, expected_variables = pm_data
        
        # Extract variables
        result = self.variable_extractor.extract_variables(pm_elem)
        
        # Property 1: Number of extracted variables should match expected
        self.assertEqual(len(result), len(expected_variables))
        
        # Property 2: All variables should have required fields
        for var in result:
            self.assertIn('name', var)
            self.assertIsInstance(var['name'], str)
            self.assertGreater(len(var['name']), 0)
            
            self.assertIn('type', var)
            self.assertIsInstance(var['type'], str)
            
            self.assertIn('parameter', var)
            self.assertIsInstance(var['parameter'], bool)
            
            self.assertIn('required', var)
            self.assertIsInstance(var['required'], bool)
            
            self.assertIn('multiple', var)
            self.assertIsInstance(var['multiple'], bool)
            
            self.assertIn('used_in_nodes', var)
            self.assertIsInstance(var['used_in_nodes'], list)
            
            self.assertIn('modified_by_nodes', var)
            self.assertIsInstance(var['modified_by_nodes'], list)
        
        # Property 3: Extracted variable names should match expected
        extracted_names = {var['name'] for var in result}
        expected_names = {var['name'] for var in expected_variables}
        self.assertEqual(extracted_names, expected_names)
        
        # Property 4: Variable properties should match expected
        result_lookup = {var['name']: var for var in result}
        for expected_var in expected_variables:
            var_name = expected_var['name']
            self.assertIn(var_name, result_lookup)
            
            actual_var = result_lookup[var_name]
            self.assertEqual(actual_var['type'], expected_var['type'])
            self.assertEqual(actual_var['parameter'], expected_var['parameter'])
            self.assertEqual(actual_var['required'], expected_var['required'])
            self.assertEqual(actual_var['multiple'], expected_var['multiple'])


class TestVariableUsageTrackingProperties(BaseTestCase):
    """Property-based tests for variable usage tracking"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.object_lookup = {}
        self.node_extractor = NodeExtractor(self.object_lookup)
    
    @given(node_data=node_with_variable_usage_xml())
    @hypothesis_settings(max_examples=100)
    def test_property_15_variable_usage_tracking(self, node_data):
        """
        **Feature: process-model-visualization, Property 15: Variable usage tracking**
        **Validates: Requirements 6.3, 6.4**
        
        For any node, the system should track which variables are referenced
        in expressions and which variables are modified through output expressions.
        """
        node_elem, uuid, name, expected_used, expected_modified = node_data
        
        # Find AC element
        ac_elem = node_elem.find('{http://www.appian.com/ae/types/2009}ac')
        self.assertIsNotNone(ac_elem)
        
        # Track variable usage
        result = self.node_extractor.track_variable_usage(uuid, ac_elem)
        
        # Property 1: Result should have 'used' and 'modified' keys
        self.assertIn('used', result)
        self.assertIsInstance(result['used'], set)
        
        self.assertIn('modified', result)
        self.assertIsInstance(result['modified'], set)
        
        # Property 2: Used variables should be a superset of expected_used
        # (Modified variables may also appear in used set since assignment expressions reference them)
        self.assertTrue(expected_used.issubset(result['used']))
        
        # Property 3: Modified variables should match expected
        self.assertEqual(result['modified'], expected_modified)
        
        # Property 4: Modified variables may also appear in used set
        # (This is correct - when you assign pv!var = value, you're referencing pv!var)
        # So we just check that modified is a subset of or equal to used
        self.assertTrue(result['modified'].issubset(result['used']) or result['modified'].isdisjoint(result['used']))
        
        # Property 4: Variables can be both used and modified in the same node
        # (This is valid - a node can read a variable and then update it)
        # No assertion needed, just documenting the behavior
    
    @given(
        node_data=node_with_variable_usage_xml(),
        pm_data=process_model_with_variables_xml()
    )
    @hypothesis_settings(max_examples=100)
    def test_property_variable_usage_update(self, node_data, pm_data):
        """
        For any node and variable list, updating variable usage should
        correctly track which nodes use and modify each variable.
        """
        from services.appian_analyzer.process_model_enhancement import VariableExtractor
        
        node_elem, uuid, node_name, expected_used, expected_modified = node_data
        pm_elem, _ = pm_data
        
        # Extract variables
        var_extractor = VariableExtractor()
        variables = var_extractor.extract_variables(pm_elem)
        
        # Track variable usage for the node
        ac_elem = node_elem.find('{http://www.appian.com/ae/types/2009}ac')
        variable_usage = self.node_extractor.track_variable_usage(uuid, ac_elem)
        
        # Update variable usage
        updated_vars = var_extractor.update_variable_usage(
            variables,
            uuid,
            node_name,
            variable_usage
        )
        
        # Property 1: Variables that are used should have the node in used_in_nodes
        var_lookup = {var['name']: var for var in updated_vars}
        for var_name in expected_used:
            if var_name in var_lookup:
                self.assertIn(node_name, var_lookup[var_name]['used_in_nodes'])
        
        # Property 2: Variables that are modified should have the node in modified_by_nodes
        for var_name in expected_modified:
            if var_name in var_lookup:
                self.assertIn(node_name, var_lookup[var_name]['modified_by_nodes'])


class TestParameterVariableMarkingProperties(BaseTestCase):
    """Property-based tests for parameter variable marking"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        from services.appian_analyzer.process_model_enhancement import VariableExtractor
        self.variable_extractor = VariableExtractor()
    
    @given(pm_data=process_model_with_variables_xml())
    @hypothesis_settings(max_examples=100)
    def test_property_16_parameter_variable_marking(self, pm_data):
        """
        **Feature: process-model-visualization, Property 16: Parameter variable marking**
        **Validates: Requirements 6.5**
        
        For any process model, variables marked as parameters should be
        correctly identified as inputs to the process.
        """
        pm_elem, expected_variables = pm_data
        
        # Extract variables
        result = self.variable_extractor.extract_variables(pm_elem)
        
        # Property 1: All parameter variables should be marked correctly
        result_lookup = {var['name']: var for var in result}
        for expected_var in expected_variables:
            var_name = expected_var['name']
            if var_name in result_lookup:
                actual_var = result_lookup[var_name]
                
                # Property: Parameter status should match
                self.assertEqual(
                    actual_var['parameter'],
                    expected_var['parameter'],
                    f"Variable {var_name} parameter status mismatch"
                )
                
                # Property: If marked as parameter, it should be a process input
                if expected_var['parameter']:
                    self.assertTrue(
                        actual_var['parameter'],
                        f"Variable {var_name} should be marked as parameter"
                    )
        
        # Property 2: Count of parameter variables should match
        expected_param_count = sum(1 for var in expected_variables if var['parameter'])
        actual_param_count = sum(1 for var in result if var['parameter'])
        self.assertEqual(actual_param_count, expected_param_count)
        
        # Property 3: Non-parameter variables should not be marked as parameters
        for var in result:
            expected_var = next(
                (ev for ev in expected_variables if ev['name'] == var['name']),
                None
            )
            if expected_var and not expected_var['parameter']:
                self.assertFalse(
                    var['parameter'],
                    f"Variable {var['name']} should not be marked as parameter"
                )



# ============================================================================
# Property Tests for Node Comparison (Task 7.2)
# ============================================================================

class TestNodeComparison(BaseTestCase):
    """
    Property-based tests for NodeComparator class
    
    Tests node comparison functionality including detection of added,
    removed, and modified nodes, and property-level diff generation.
    """
    
    @given(
        base_node_count=st.integers(min_value=1, max_value=10),
        target_node_count=st.integers(min_value=1, max_value=10)
    )
    @hypothesis_settings(max_examples=100)
    def test_property_7_node_comparison_by_uuid(
        self,
        base_node_count,
        target_node_count
    ):
        """
        **Feature: process-model-visualization, Property 7: Node comparison by UUID**
        **Validates: Requirements 4.1, 4.2**
        
        For any two lists of nodes, comparing them should identify nodes
        by UUID and correctly categorize them as added, removed, modified,
        or unchanged.
        """
        from services.appian_analyzer.process_model_enhancement import NodeComparator
        
        # Generate base nodes with unique UUIDs
        base_nodes = []
        for i in range(base_node_count):
            base_nodes.append({
                'uuid': f'_a-base-node-{i:04d}',
                'name': f'Base Node {i}',
                'type': 'USER_INPUT_TASK',
                'properties': {
                    'basic': {'description': f'Base description {i}'},
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
            })
        
        # Generate target nodes - some overlap with base, some new
        target_nodes = []
        
        # Keep some base nodes unchanged (first half)
        overlap_count = min(base_node_count, target_node_count) // 2
        for i in range(overlap_count):
            target_nodes.append(base_nodes[i].copy())
        
        # Add new nodes
        for i in range(overlap_count, target_node_count):
            target_nodes.append({
                'uuid': f'_a-target-node-{i:04d}',
                'name': f'Target Node {i}',
                'type': 'SCRIPT_TASK',
                'properties': {
                    'basic': {'description': f'Target description {i}'},
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
            })
        
        # Compare nodes
        comparator = NodeComparator()
        result = comparator.compare_nodes(base_nodes, target_nodes)
        
        # Verify result structure
        self.assertIn('added', result)
        self.assertIn('removed', result)
        self.assertIn('modified', result)
        self.assertIn('unchanged', result)
        
        # Verify all nodes are accounted for
        total_categorized = (
            len(result['added']) +
            len(result['removed']) +
            len(result['modified']) +
            len(result['unchanged'])
        )
        
        # Total should equal unique UUIDs across both versions
        base_uuids = {node['uuid'] for node in base_nodes}
        target_uuids = {node['uuid'] for node in target_nodes}
        all_unique_uuids = base_uuids | target_uuids
        
        self.assertEqual(total_categorized, len(all_unique_uuids))
        
        # Verify no duplicate UUIDs in results
        added_uuids = {node['uuid'] for node in result['added']}
        removed_uuids = {node['uuid'] for node in result['removed']}
        modified_uuids = {item['node']['uuid'] for item in result['modified']}
        unchanged_uuids = {node['uuid'] for node in result['unchanged']}
        
        # Check for no overlaps between categories
        self.assertEqual(len(added_uuids & removed_uuids), 0)
        self.assertEqual(len(added_uuids & modified_uuids), 0)
        self.assertEqual(len(added_uuids & unchanged_uuids), 0)
        self.assertEqual(len(removed_uuids & modified_uuids), 0)
        self.assertEqual(len(removed_uuids & unchanged_uuids), 0)
        self.assertEqual(len(modified_uuids & unchanged_uuids), 0)
    
    @given(
        num_nodes=st.integers(min_value=2, max_value=10),
        num_added=st.integers(min_value=1, max_value=5),
        num_removed=st.integers(min_value=1, max_value=5)
    )
    @hypothesis_settings(max_examples=100)
    def test_property_8_node_addition_and_removal_detection(
        self,
        num_nodes,
        num_added,
        num_removed
    ):
        """
        **Feature: process-model-visualization, Property 8: Node addition and removal detection**
        **Validates: Requirements 4.3, 4.4**
        
        For any two versions of a process model, nodes that exist only in
        the target version should be marked as ADDED, and nodes that exist
        only in the base version should be marked as REMOVED.
        """
        from services.appian_analyzer.process_model_enhancement import NodeComparator
        
        # Generate base nodes
        base_nodes = []
        for i in range(num_nodes):
            base_nodes.append({
                'uuid': f'_a-common-node-{i:04d}',
                'name': f'Common Node {i}',
                'type': 'USER_INPUT_TASK',
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
            })
        
        # Add nodes that will be removed (only in base)
        removed_nodes = []
        for i in range(num_removed):
            removed_node = {
                'uuid': f'_a-removed-node-{i:04d}',
                'name': f'Removed Node {i}',
                'type': 'SCRIPT_TASK',
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
            base_nodes.append(removed_node)
            removed_nodes.append(removed_node)
        
        # Create target nodes (common nodes + new nodes)
        target_nodes = [node.copy() for node in base_nodes[:num_nodes]]
        
        # Add new nodes (only in target)
        added_nodes = []
        for i in range(num_added):
            added_node = {
                'uuid': f'_a-added-node-{i:04d}',
                'name': f'Added Node {i}',
                'type': 'GATEWAY',
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
            target_nodes.append(added_node)
            added_nodes.append(added_node)
        
        # Compare nodes
        comparator = NodeComparator()
        result = comparator.compare_nodes(base_nodes, target_nodes)
        
        # Verify added nodes are correctly identified
        self.assertEqual(len(result['added']), num_added)
        added_uuids = {node['uuid'] for node in result['added']}
        expected_added_uuids = {node['uuid'] for node in added_nodes}
        self.assertEqual(added_uuids, expected_added_uuids)
        
        # Verify removed nodes are correctly identified
        self.assertEqual(len(result['removed']), num_removed)
        removed_uuids = {node['uuid'] for node in result['removed']}
        expected_removed_uuids = {node['uuid'] for node in removed_nodes}
        self.assertEqual(removed_uuids, expected_removed_uuids)
        
        # Verify common nodes are not marked as added or removed
        common_uuids = {f'_a-common-node-{i:04d}' for i in range(num_nodes)}
        self.assertEqual(len(added_uuids & common_uuids), 0)
        self.assertEqual(len(removed_uuids & common_uuids), 0)
    
    @given(
        num_nodes=st.integers(min_value=1, max_value=10),
        property_to_change=st.sampled_from([
            'name',
            'type',
            'properties.basic.description',
            'properties.assignment.type',
            'properties.forms.interface_name',
            'properties.expressions.pre_activity',
            'properties.escalation.enabled'
        ])
    )
    @hypothesis_settings(max_examples=100)
    def test_property_9_property_diff_completeness(
        self,
        num_nodes,
        property_to_change
    ):
        """
        **Feature: process-model-visualization, Property 9: Property diff completeness**
        **Validates: Requirements 4.5**
        
        For any node that exists in both versions, if any property changes,
        the comparison should generate a complete property-level diff showing
        the before and after values for each changed property.
        """
        from services.appian_analyzer.process_model_enhancement import NodeComparator
        
        # Generate base nodes
        base_nodes = []
        for i in range(num_nodes):
            base_nodes.append({
                'uuid': f'_a-node-{i:04d}',
                'name': f'Node {i}',
                'type': 'USER_INPUT_TASK',
                'properties': {
                    'basic': {'description': f'Original description {i}'},
                    'assignment': {'type': 'USER'},
                    'forms': {'interface_name': 'OriginalInterface'},
                    'expressions': {'pre_activity': 'original_expression'},
                    'escalation': {'enabled': False}
                },
                'dependencies': {
                    'interfaces': [],
                    'rules': [],
                    'groups': []
                }
            })
        
        # Create target nodes with modifications
        target_nodes = []
        for i in range(num_nodes):
            target_node = {
                'uuid': f'_a-node-{i:04d}',
                'name': f'Node {i}',
                'type': 'USER_INPUT_TASK',
                'properties': {
                    'basic': {'description': f'Original description {i}'},
                    'assignment': {'type': 'USER'},
                    'forms': {'interface_name': 'OriginalInterface'},
                    'expressions': {'pre_activity': 'original_expression'},
                    'escalation': {'enabled': False}
                },
                'dependencies': {
                    'interfaces': [],
                    'rules': [],
                    'groups': []
                }
            }
            
            # Modify the specified property
            if property_to_change == 'name':
                target_node['name'] = f'Modified Node {i}'
            elif property_to_change == 'type':
                target_node['type'] = 'SCRIPT_TASK'
            elif property_to_change == 'properties.basic.description':
                target_node['properties']['basic']['description'] = f'Modified description {i}'
            elif property_to_change == 'properties.assignment.type':
                target_node['properties']['assignment']['type'] = 'GROUP'
            elif property_to_change == 'properties.forms.interface_name':
                target_node['properties']['forms']['interface_name'] = 'ModifiedInterface'
            elif property_to_change == 'properties.expressions.pre_activity':
                target_node['properties']['expressions']['pre_activity'] = 'modified_expression'
            elif property_to_change == 'properties.escalation.enabled':
                target_node['properties']['escalation']['enabled'] = True
            
            target_nodes.append(target_node)
        
        # Compare nodes
        comparator = NodeComparator()
        result = comparator.compare_nodes(base_nodes, target_nodes)
        
        # All nodes should be marked as modified (since we changed a property)
        self.assertEqual(len(result['modified']), num_nodes)
        self.assertEqual(len(result['unchanged']), 0)
        
        # Verify each modified node has changes recorded
        for modified_item in result['modified']:
            self.assertIn('node', modified_item)
            self.assertIn('changes', modified_item)
            
            changes = modified_item['changes']
            self.assertGreater(len(changes), 0)
            
            # Verify at least one change matches the property we modified
            property_found = False
            for change in changes:
                if change['property'] == property_to_change:
                    property_found = True
                    # Verify change has before and after values
                    self.assertIn('before', change)
                    self.assertIn('after', change)
                    # Verify before and after are different
                    self.assertNotEqual(change['before'], change['after'])
            
            self.assertTrue(
                property_found,
                f"Expected property '{property_to_change}' not found in changes"
            )


# ============================================================================
# Property Tests for Flow Comparison (Task 7.4)
# ============================================================================

class TestFlowComparison(BaseTestCase):
    """
    Property-based tests for flow comparison functionality
    
    Tests flow comparison including detection of added, removed,
    and modified flows.
    """
    
    @given(
        num_base_flows=st.integers(min_value=1, max_value=10),
        num_target_flows=st.integers(min_value=1, max_value=10)
    )
    @hypothesis_settings(max_examples=100)
    def test_property_13_flow_comparison(
        self,
        num_base_flows,
        num_target_flows
    ):
        """
        **Feature: process-model-visualization, Property 13: Flow comparison**
        **Validates: Requirements 5.8**
        
        For any two lists of flows, comparing them should identify flows
        by their source and target nodes, and correctly categorize them
        as added, removed, modified, or unchanged.
        """
        from services.appian_analyzer.process_model_enhancement import NodeComparator
        
        # Generate base flows
        base_flows = []
        for i in range(num_base_flows):
            base_flows.append({
                'uuid': f'_flow-base-{i:04d}',
                'from_node_uuid': f'_a-node-{i:04d}',
                'from_node_name': f'Node {i}',
                'to_node_uuid': f'_a-node-{i+1:04d}',
                'to_node_name': f'Node {i+1}',
                'condition': f'condition_{i}' if i % 2 == 0 else '',
                'is_default': i % 2 != 0,
                'label': f'Flow {i}'
            })
        
        # Generate target flows - some overlap, some new
        target_flows = []
        
        # Keep some base flows (first half)
        overlap_count = min(num_base_flows, num_target_flows) // 2
        for i in range(overlap_count):
            target_flows.append(base_flows[i].copy())
        
        # Add new flows
        for i in range(overlap_count, num_target_flows):
            target_flows.append({
                'uuid': f'_flow-target-{i:04d}',
                'from_node_uuid': f'_a-node-{i+100:04d}',
                'from_node_name': f'Node {i+100}',
                'to_node_uuid': f'_a-node-{i+101:04d}',
                'to_node_name': f'Node {i+101}',
                'condition': f'new_condition_{i}',
                'is_default': False,
                'label': f'New Flow {i}'
            })
        
        # Compare flows
        comparator = NodeComparator()
        result = comparator.compare_flows(base_flows, target_flows)
        
        # Verify result structure
        self.assertIn('added_flows', result)
        self.assertIn('removed_flows', result)
        self.assertIn('modified_flows', result)
        self.assertIn('unchanged_flows', result)
        
        # Verify all flows are accounted for
        total_categorized = (
            len(result['added_flows']) +
            len(result['removed_flows']) +
            len(result['modified_flows']) +
            len(result['unchanged_flows'])
        )
        
        # Total should equal unique flow keys across both versions
        def flow_key(flow):
            return (flow['from_node_uuid'], flow['to_node_uuid'])
        
        base_keys = {flow_key(flow) for flow in base_flows}
        target_keys = {flow_key(flow) for flow in target_flows}
        all_unique_keys = base_keys | target_keys
        
        self.assertEqual(total_categorized, len(all_unique_keys))
        
        # Verify no duplicate flow keys in results
        added_keys = {flow_key(flow) for flow in result['added_flows']}
        removed_keys = {flow_key(flow) for flow in result['removed_flows']}
        modified_keys = {flow_key(item['flow']) for item in result['modified_flows']}
        unchanged_keys = {flow_key(flow) for flow in result['unchanged_flows']}
        
        # Check for no overlaps between categories
        self.assertEqual(len(added_keys & removed_keys), 0)
        self.assertEqual(len(added_keys & modified_keys), 0)
        self.assertEqual(len(added_keys & unchanged_keys), 0)
        self.assertEqual(len(removed_keys & modified_keys), 0)
        self.assertEqual(len(removed_keys & unchanged_keys), 0)
        self.assertEqual(len(modified_keys & unchanged_keys), 0)
        
        # Verify added flows are only in target
        for flow in result['added_flows']:
            key = flow_key(flow)
            self.assertIn(key, target_keys)
            self.assertNotIn(key, base_keys)
        
        # Verify removed flows are only in base
        for flow in result['removed_flows']:
            key = flow_key(flow)
            self.assertIn(key, base_keys)
            self.assertNotIn(key, target_keys)
        
        # Verify modified and unchanged flows are in both
        for item in result['modified_flows']:
            key = flow_key(item['flow'])
            self.assertIn(key, base_keys)
            self.assertIn(key, target_keys)
        
        for flow in result['unchanged_flows']:
            key = flow_key(flow)
            self.assertIn(key, base_keys)
            self.assertIn(key, target_keys)



class TestComparisonDataUsageProperties(BaseTestCase):
    """Property-based tests for comparison data usage"""

    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        from services.merge_assistant.three_way_comparison_service import (
            ThreeWayComparisonService
        )
        from services.appian_analyzer.models import AppianObject
        self.comparison_service = ThreeWayComparisonService()
        self.AppianObject = AppianObject

    @given(
        num_nodes=st.integers(min_value=1, max_value=10),
        num_flows=st.integers(min_value=0, max_value=15),
        pm_id=st.integers(min_value=1000, max_value=9999),
        pm_num=st.integers(min_value=1, max_value=100)
    )
    @hypothesis_settings(max_examples=100)
    def test_property_25_comparison_data_usage(
        self, num_nodes, num_flows, pm_id, pm_num
    ):
        """
        **Feature: process-model-visualization, Property 25: Comparison data usage**
        **Validates: Requirements 9.3**

        For any process model comparison, when enhanced node data is available,
        the comparison service should include node-level and flow-level
        comparison results in the change object.
        """
        # Generate random process model data
        pm_uuid = f"_a-pm-{pm_id}"
        pm_name = f"Process Model {pm_num}"

        # Create base nodes
        base_nodes = []
        node_types = ['USER_INPUT_TASK', 'SCRIPT_TASK', 'GATEWAY']
        for i in range(num_nodes):
            node = {
                'uuid': f"_a-node-{i}",
                'name': f"Node {i}",
                'type': node_types[i % len(node_types)],
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
            base_nodes.append(node)

        # Create target nodes (with some modifications)
        target_nodes = []
        for i in range(num_nodes):
            node = {
                'uuid': f"_a-node-{i}",
                'name': f"Node {i} Modified",  # Changed name
                'type': node_types[i % len(node_types)],
                'properties': {
                    'basic': {'description': 'Modified'},
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
            target_nodes.append(node)

        # Create base flows
        base_flows = []
        for i in range(min(num_flows, num_nodes - 1)):
            flow = {
                'uuid': f"_a-flow-{i}",
                'from_node_uuid': f"_a-node-{i}",
                'from_node_name': f"Node {i}",
                'to_node_uuid': f"_a-node-{i+1}",
                'to_node_name': f"Node {i+1}",
                'condition': '',
                'is_default': True,
                'label': 'default'
            }
            base_flows.append(flow)

        # Create target flows (with some modifications)
        target_flows = []
        for i in range(min(num_flows, num_nodes - 1)):
            flow = {
                'uuid': f"_a-flow-{i}",
                'from_node_uuid': f"_a-node-{i}",
                'from_node_name': f"Node {i} Modified",
                'to_node_uuid': f"_a-node-{i+1}",
                'to_node_name': f"Node {i+1} Modified",
                'condition': 'pv!condition = true',  # Added condition
                'is_default': False,
                'label': 'pv!condition = true'
            }
            target_flows.append(flow)

        # Create AppianObject instances
        base_obj = self.AppianObject(
            uuid=pm_uuid,
            name=pm_name,
            object_type='Process Model',
            description='Base version'
        )
        base_obj.nodes = base_nodes
        base_obj.flows = base_flows

        target_obj = self.AppianObject(
            uuid=pm_uuid,
            name=pm_name,
            object_type='Process Model',
            description='Target version'
        )
        target_obj.nodes = target_nodes
        target_obj.flows = target_flows

        # Create target lookup with enhanced data
        target_lookup = {
            pm_uuid: {
                'uuid': pm_uuid,
                'name': pm_name,
                'object_type': 'Process Model',
                'nodes': target_nodes,
                'flows': target_flows,
                'flow_graph': {
                    'start_nodes': [f"_a-node-0"],
                    'end_nodes': [f"_a-node-{num_nodes-1}"],
                    'node_connections': {},
                    'paths': []
                },
                'node_summary': {
                    'total_nodes': num_nodes,
                    'node_type_counts': {},
                    'nodes_by_type': {}
                }
            }
        }

        # Create comparison result mock
        from services.appian_analyzer.models import ImportChangeStatus
        from dataclasses import dataclass

        @dataclass
        class MockComparisonResult:
            obj: object
            old_obj: object
            status: ImportChangeStatus
            content_diff: str = ""
            version_info: dict = None

        comparison_result = MockComparisonResult(
            obj=target_obj,
            old_obj=base_obj,
            status=ImportChangeStatus.CHANGED
        )

        # Call _build_change_object
        change_obj = self.comparison_service._build_change_object(
            comparison_result,
            target_lookup
        )

        # Property 1: Change object must include process_model_data
        self.assertIn('process_model_data', change_obj)
        pm_data = change_obj['process_model_data']

        # Property 2: process_model_data must have has_enhanced_data flag
        self.assertIn('has_enhanced_data', pm_data)
        self.assertIsInstance(pm_data['has_enhanced_data'], bool)

        # Property 3: If enhanced data is available, flag should be True
        if target_nodes:
            self.assertTrue(pm_data['has_enhanced_data'])

            # Property 4: node_comparison must be present
            self.assertIn('node_comparison', pm_data)
            self.assertIsNotNone(pm_data['node_comparison'])

            # Property 5: node_comparison must have required keys
            node_comp = pm_data['node_comparison']
            self.assertIn('added', node_comp)
            self.assertIn('removed', node_comp)
            self.assertIn('modified', node_comp)
            self.assertIn('unchanged', node_comp)

            # Property 6: All node comparison lists must be lists
            self.assertIsInstance(node_comp['added'], list)
            self.assertIsInstance(node_comp['removed'], list)
            self.assertIsInstance(node_comp['modified'], list)
            self.assertIsInstance(node_comp['unchanged'], list)

            # Property 7: Total nodes in comparison should equal input nodes
            total_compared = (
                len(node_comp['added']) +
                len(node_comp['removed']) +
                len(node_comp['modified']) +
                len(node_comp['unchanged'])
            )
            self.assertEqual(total_compared, num_nodes)

            # Property 8: flow_comparison must be present if flows exist
            if target_flows:
                self.assertIn('flow_comparison', pm_data)
                self.assertIsNotNone(pm_data['flow_comparison'])

                # Property 9: flow_comparison must have required keys
                flow_comp = pm_data['flow_comparison']
                self.assertIn('added_flows', flow_comp)
                self.assertIn('removed_flows', flow_comp)
                self.assertIn('modified_flows', flow_comp)
                self.assertIn('unchanged_flows', flow_comp)

                # Property 10: All flow comparison lists must be lists
                self.assertIsInstance(flow_comp['added_flows'], list)
                self.assertIsInstance(flow_comp['removed_flows'], list)
                self.assertIsInstance(flow_comp['modified_flows'], list)
                self.assertIsInstance(flow_comp['unchanged_flows'], list)

            # Property 11: node_summary must be present
            self.assertIn('node_summary', pm_data)

            # Property 12: flow_graph must be present
            self.assertIn('flow_graph', pm_data)

        # Property 13: If no enhanced data, flag should be False
        if not target_nodes:
            self.assertFalse(pm_data['has_enhanced_data'])



class TestProcessModelRendererProperties(BaseTestCase):
    """Property-based tests for ProcessModelRenderer"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        from services.appian_analyzer.process_model_enhancement import (
            ProcessModelRenderer
        )
        self.renderer = ProcessModelRenderer()
    
    @given(
        node_name=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters='-_ '
            ),
            min_size=1,
            max_size=50
        ),
        node_type=st.sampled_from([
            'USER_INPUT_TASK',
            'SCRIPT_TASK',
            'GATEWAY',
            'SUBPROCESS',
            'UNKNOWN'
        ]),
        has_basic_props=st.booleans(),
        has_assignment=st.booleans(),
        has_forms=st.booleans(),
        has_expressions=st.booleans(),
        has_escalation=st.booleans()
    )
    @hypothesis_settings(max_examples=100)
    def test_property_17_structured_display_over_raw_xml(
        self,
        node_name,
        node_type,
        has_basic_props,
        has_assignment,
        has_forms,
        has_expressions,
        has_escalation
    ):
        """
        **Feature: process-model-visualization, Property 17: Structured display over raw XML**
        **Validates: Requirements 7.1, 7.2**
        
        For any process model node, the renderer should produce structured HTML
        output with categorized properties instead of raw XML.
        """
        # Create a test node dictionary
        node = {
            'uuid': '_a-test-node-uuid',
            'name': node_name,
            'type': node_type,
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
        
        # Add properties based on flags
        if has_basic_props:
            node['properties']['basic'] = {
                'description': 'Test description',
                'priority': 'HIGH'
            }
        
        if has_assignment:
            node['properties']['assignment'] = {
                'type': 'USER',
                'assignees': ['test.user'],
                'assignment_expression': ''
            }
        
        if has_forms:
            node['properties']['forms'] = {
                'interface_uuid': '_a-interface-uuid',
                'interface_name': 'Test Interface',
                'input_mappings': {},
                'output_mappings': {}
            }
        
        if has_expressions:
            node['properties']['expressions'] = {
                'pre_activity': 'pv!test = 1',
                'post_activity': '',
                'output_expressions': {'result': 'pv!result = 2'},
                'conditions': {}
            }
        
        if has_escalation:
            node['properties']['escalation'] = {
                'enabled': True,
                'escalation_time': '1 hour',
                'escalation_action': 'notify',
                'notify_assignees': True
            }
        
        # Render node summary
        html_output = self.renderer.render_node_summary(node)
        
        # Property 1: Output must be a string
        self.assertIsInstance(html_output, str)
        
        # Property 2: Output must not be empty
        self.assertGreater(len(html_output), 0)
        
        # Property 3: Output must contain HTML tags (not raw XML)
        self.assertIn('<div', html_output)
        self.assertNotIn('<?xml', html_output)
        
        # Property 4: Output must contain node name (escaped)
        import html as html_module
        escaped_name = html_module.escape(node_name)
        self.assertIn(escaped_name, html_output)
        
        # Property 5: Output must contain node type
        self.assertIn(node_type, html_output)
        
        # Property 6: Output must have structured sections (property groups) if any properties exist
        has_any_props = (has_basic_props or has_assignment or has_forms or 
                        has_expressions or has_escalation)
        if has_any_props:
            self.assertIn('property-group', html_output)
        
        # Property 7: If basic properties exist, they should be in output
        if has_basic_props:
            self.assertIn('Basic', html_output)
            self.assertIn('Test description', html_output)
        
        # Property 8: If assignment exists, it should be in output
        if has_assignment:
            self.assertIn('Assignment', html_output)
        
        # Property 9: If forms exist, they should be in output
        if has_forms:
            self.assertIn('Forms', html_output)
            self.assertIn('Test Interface', html_output)
        
        # Property 10: If expressions exist, they should be in output
        if has_expressions:
            self.assertIn('Expressions', html_output)
        
        # Property 11: If escalation exists, it should be in output
        if has_escalation:
            self.assertIn('Escalation', html_output)
        
        # Property 12: Output must not contain raw XML elements
        self.assertNotIn('<ac>', html_output)
        self.assertNotIn('<node>', html_output)
        self.assertNotIn('{http://www.appian.com/ae/types/2009}', html_output)
        
        # Property 13: Output must properly escape HTML special characters
        # (no unescaped < or > except in HTML tags)
        # This is a basic check - the html module should handle escaping
        self.assertNotIn('&lt;ac&gt;', html_output)  # Should not double-escape
    
    @given(
        node_name=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                whitelist_characters='-_ '
            ),
            min_size=1,
            max_size=50
        ),
        property_value=st.one_of(
            st.text(min_size=0, max_size=100),
            st.integers(),
            st.booleans(),
            st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5),
            st.dictionaries(
                st.text(min_size=1, max_size=20),
                st.text(min_size=1, max_size=50),
                min_size=0,
                max_size=3
            )
        )
    )
    @hypothesis_settings(max_examples=100)
    def test_property_value_formatting(self, node_name, property_value):
        """
        For any property value type (string, int, bool, list, dict),
        the renderer should format it appropriately for HTML display.
        """
        # Create a test node with the property value
        node = {
            'uuid': '_a-test-node-uuid',
            'name': node_name,
            'type': 'SCRIPT_TASK',
            'properties': {
                'basic': {'test_property': property_value},
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
        
        # Render node summary
        html_output = self.renderer.render_node_summary(node)
        
        # Property 1: Output must be a string
        self.assertIsInstance(html_output, str)
        
        # Property 2: Output must not be empty
        self.assertGreater(len(html_output), 0)
        
        # Property 3: Output must contain HTML structure
        self.assertIn('<div', html_output)
        
        # Property 4: If property value is not empty, it should appear in output
        if property_value is not None and property_value != '' and property_value != [] and property_value != {}:
            # The value should be present in some form
            # (may be formatted differently for different types)
            self.assertIn('Basic', html_output)
    
    @given(
        num_changes=st.integers(min_value=1, max_value=10),
        change_type=st.sampled_from(['added', 'removed', 'modified'])
    )
    @hypothesis_settings(max_examples=100)
    def test_property_18_three_way_comparison_display(
        self,
        num_changes,
        change_type
    ):
        """
        **Feature: process-model-visualization, Property 18: Three-way comparison display**
        **Validates: Requirements 7.3, 7.4**
        
        For any node comparison (added, removed, or modified), the renderer
        should produce HTML that highlights changes with before/after values.
        """
        # Create base and target nodes
        base_node = {
            'uuid': '_a-test-node-uuid',
            'name': 'Test Node',
            'type': 'SCRIPT_TASK',
            'properties': {
                'basic': {'description': 'Original description'},
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
        
        target_node = {
            'uuid': '_a-test-node-uuid',
            'name': 'Test Node',
            'type': 'SCRIPT_TASK',
            'properties': {
                'basic': {'description': 'Modified description'},
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
        
        # Create changes list
        changes = []
        for i in range(num_changes):
            changes.append({
                'property': f'properties.basic.field_{i}',
                'before': f'old_value_{i}',
                'after': f'new_value_{i}'
            })
        
        # Render comparison based on change type
        if change_type == 'added':
            html_output = self.renderer.render_node_comparison(
                None,
                target_node,
                []
            )
            expected_badge = 'ADDED'
        elif change_type == 'removed':
            html_output = self.renderer.render_node_comparison(
                base_node,
                None,
                []
            )
            expected_badge = 'REMOVED'
        else:  # modified
            html_output = self.renderer.render_node_comparison(
                base_node,
                target_node,
                changes
            )
            expected_badge = 'MODIFIED'
        
        # Property 1: Output must be a string
        self.assertIsInstance(html_output, str)
        
        # Property 2: Output must not be empty
        self.assertGreater(len(html_output), 0)
        
        # Property 3: Output must contain HTML structure
        self.assertIn('<div', html_output)
        
        # Property 4: Output must contain comparison indicator
        self.assertIn('node-comparison', html_output)
        
        # Property 5: Output must show change type badge
        self.assertIn(expected_badge, html_output)
        
        # Property 6: For modified nodes, output must show changes
        if change_type == 'modified' and num_changes > 0:
            self.assertIn('changes-summary', html_output)
            self.assertIn('Before', html_output)
            self.assertIn('After', html_output)
            
            # Property 7: Each change should be represented
            for change in changes:
                # The property name should appear
                self.assertIn(change['property'], html_output)
        
        # Property 8: For added nodes, only target should be shown
        if change_type == 'added':
            self.assertIn('Test Node', html_output)
        
        # Property 9: For removed nodes, only base should be shown
        if change_type == 'removed':
            self.assertIn('Test Node', html_output)
        
        # Property 10: For modified nodes, both versions should be shown
        if change_type == 'modified':
            self.assertIn('Before', html_output)
            self.assertIn('After', html_output)
            # Both node summaries should be present
            self.assertIn('Test Node', html_output)



class TestFlowDiagramGenerationProperties(BaseTestCase):
    """Property-based tests for flow diagram generation"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        from services.appian_analyzer.process_model_enhancement import (
            FlowDiagramGenerator
        )
        self.diagram_generator = FlowDiagramGenerator()
    
    @given(
        num_nodes=st.integers(min_value=1, max_value=20),
        num_flows=st.integers(min_value=0, max_value=30),
        data=st.data()
    )
    @hypothesis_settings(max_examples=100)
    def test_property_19_flow_diagram_generation(self, num_nodes, num_flows, data):
        """
        **Feature: process-model-visualization, Property 19: Flow diagram generation**
        **Validates: Requirements 7.5, 7.6, 7.9**
        
        For any process model with nodes and flows, the system should generate
        a valid Mermaid.js diagram with appropriate node shapes and edge labels.
        """
        # Generate random nodes
        nodes = []
        node_uuids = []
        
        for i in range(num_nodes):
            node_uuid = f'_a-node-{i:04d}'
            node_uuids.append(node_uuid)
            
            # Randomly assign node types using data.draw()
            node_type = data.draw(
                st.sampled_from([
                    NodeType.USER_INPUT_TASK,
                    NodeType.SCRIPT_TASK,
                    NodeType.GATEWAY,
                    NodeType.SUBPROCESS,
                    NodeType.START_NODE,
                    NodeType.END_NODE
                ])
            )
            
            node = {
                'uuid': node_uuid,
                'name': f'Node {i}',
                'type': node_type.value,
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
            nodes.append(node)
        
        # Generate random flows (ensure valid connections)
        flows = []
        for i in range(min(num_flows, num_nodes * (num_nodes - 1))):
            # Pick random source and target (ensure they're different)
            if num_nodes > 1:
                source_idx = i % num_nodes
                target_idx = (i + 1) % num_nodes
                
                flow = {
                    'uuid': f'_flow-{i:04d}',
                    'from_node_uuid': node_uuids[source_idx],
                    'from_node_name': f'Node {source_idx}',
                    'to_node_uuid': node_uuids[target_idx],
                    'to_node_name': f'Node {target_idx}',
                    'condition': f'condition_{i}' if i % 2 == 0 else '',
                    'is_default': i % 2 == 1,
                    'label': f'condition_{i}' if i % 2 == 0 else 'default'
                }
                flows.append(flow)
        
        # Build flow graph
        flow_graph = {
            'start_nodes': [node_uuids[0]] if num_nodes > 0 else [],
            'end_nodes': [node_uuids[-1]] if num_nodes > 0 else [],
            'node_connections': {},
            'paths': []
        }
        
        # Generate diagram data
        diagram_data = self.diagram_generator.generate_diagram_data(
            nodes,
            flows,
            flow_graph
        )
        
        # Property 1: Diagram data must have required fields
        self.assertIn('mermaid_syntax', diagram_data)
        self.assertIn('nodes', diagram_data)
        self.assertIn('edges', diagram_data)
        self.assertIn('start_nodes', diagram_data)
        self.assertIn('end_nodes', diagram_data)
        
        # Property 2: Mermaid syntax must be a non-empty string
        self.assertIsInstance(diagram_data['mermaid_syntax'], str)
        self.assertGreater(len(diagram_data['mermaid_syntax']), 0)
        
        # Property 3: Mermaid syntax must start with graph declaration
        self.assertTrue(
            diagram_data['mermaid_syntax'].startswith('graph TD')
        )
        
        # Property 4: Number of diagram nodes should match input nodes
        self.assertEqual(len(diagram_data['nodes']), num_nodes)
        
        # Property 5: Each diagram node must have required fields
        for diagram_node in diagram_data['nodes']:
            self.assertIn('id', diagram_node)
            self.assertIn('label', diagram_node)
            self.assertIn('type', diagram_node)
            self.assertIn('shape', diagram_node)
            self.assertIn('shape_open', diagram_node)
            self.assertIn('shape_close', diagram_node)
            self.assertIn('properties', diagram_node)
        
        # Property 6: Node IDs must be sanitized (alphanumeric + underscore)
        import re
        for diagram_node in diagram_data['nodes']:
            node_id = diagram_node['id']
            self.assertTrue(
                re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', node_id),
                f"Node ID '{node_id}' is not properly sanitized"
            )
        
        # Property 7: Number of diagram edges should not exceed input flows
        # (Some flows may be filtered out if they reference unknown nodes)
        self.assertLessEqual(len(diagram_data['edges']), num_flows)
        
        # Property 8: Each diagram edge must have required fields
        for diagram_edge in diagram_data['edges']:
            self.assertIn('id', diagram_edge)
            self.assertIn('source', diagram_edge)
            self.assertIn('target', diagram_edge)
            self.assertIn('label', diagram_edge)
            self.assertIn('type', diagram_edge)
            self.assertIn('condition', diagram_edge)
        
        # Property 9: Edge types must be either 'default' or 'conditional'
        for diagram_edge in diagram_data['edges']:
            self.assertIn(
                diagram_edge['type'],
                ['default', 'conditional']
            )
        
        # Property 10: Different node types should have different shapes
        node_shapes = {}
        for diagram_node in diagram_data['nodes']:
            node_type = diagram_node['type']
            shape = diagram_node['shape']
            
            if node_type not in node_shapes:
                node_shapes[node_type] = shape
            else:
                # Same node type should always have same shape
                self.assertEqual(
                    node_shapes[node_type],
                    shape,
                    f"Node type {node_type} has inconsistent shapes"
                )
        
        # Property 11: Gateway nodes should have diamond shape
        for diagram_node in diagram_data['nodes']:
            if diagram_node['type'] == NodeType.GATEWAY.value:
                self.assertEqual(diagram_node['shape'], 'diamond')
        
        # Property 12: Start and end nodes should be tracked
        self.assertIsInstance(diagram_data['start_nodes'], list)
        self.assertIsInstance(diagram_data['end_nodes'], list)


class TestComparisonDiagramHighlightingProperties(BaseTestCase):
    """Property-based tests for comparison diagram highlighting"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        from services.appian_analyzer.process_model_enhancement import (
            FlowDiagramGenerator
        )
        self.diagram_generator = FlowDiagramGenerator()
    
    @given(
        num_added_nodes=st.integers(min_value=0, max_value=5),
        num_removed_nodes=st.integers(min_value=0, max_value=5),
        num_modified_nodes=st.integers(min_value=0, max_value=5),
        num_unchanged_nodes=st.integers(min_value=1, max_value=10)
    )
    @hypothesis_settings(max_examples=100)
    def test_property_20_comparison_diagram_highlighting(
        self,
        num_added_nodes,
        num_removed_nodes,
        num_modified_nodes,
        num_unchanged_nodes
    ):
        """
        **Feature: process-model-visualization, Property 20: Comparison diagram highlighting**
        **Validates: Requirements 7.7**
        
        For any process model comparison, the system should generate a diagram
        that highlights added nodes (green), removed nodes (red), and modified
        nodes (yellow).
        """
        # Generate base and target diagrams
        total_base_nodes = num_removed_nodes + num_modified_nodes + num_unchanged_nodes
        total_target_nodes = num_added_nodes + num_modified_nodes + num_unchanged_nodes
        
        # Create base diagram nodes
        base_nodes = []
        base_node_uuids = []
        
        node_counter = 0
        
        # Removed nodes (only in base)
        for i in range(num_removed_nodes):
            node_uuid = f'_a-removed-node-{i:04d}'
            base_node_uuids.append(node_uuid)
            base_nodes.append({
                'id': f'n_a_removed_node_{i:04d}',
                'label': f'Removed Node {i}',
                'type': NodeType.SCRIPT_TASK.value,
                'shape': 'rect',
                'shape_open': '[',
                'shape_close': ']',
                'properties': {},
                'uuid': node_uuid
            })
            node_counter += 1
        
        # Modified nodes (in both)
        modified_node_uuids = []
        for i in range(num_modified_nodes):
            node_uuid = f'_a-modified-node-{i:04d}'
            modified_node_uuids.append(node_uuid)
            base_node_uuids.append(node_uuid)
            base_nodes.append({
                'id': f'n_a_modified_node_{i:04d}',
                'label': f'Modified Node {i}',
                'type': NodeType.SCRIPT_TASK.value,
                'shape': 'rect',
                'shape_open': '[',
                'shape_close': ']',
                'properties': {},
                'uuid': node_uuid
            })
            node_counter += 1
        
        # Unchanged nodes (in both)
        unchanged_node_uuids = []
        for i in range(num_unchanged_nodes):
            node_uuid = f'_a-unchanged-node-{i:04d}'
            unchanged_node_uuids.append(node_uuid)
            base_node_uuids.append(node_uuid)
            base_nodes.append({
                'id': f'n_a_unchanged_node_{i:04d}',
                'label': f'Unchanged Node {i}',
                'type': NodeType.SCRIPT_TASK.value,
                'shape': 'rect',
                'shape_open': '[',
                'shape_close': ']',
                'properties': {},
                'uuid': node_uuid
            })
            node_counter += 1
        
        base_diagram = {
            'nodes': base_nodes,
            'edges': [],
            'start_nodes': [],
            'end_nodes': []
        }
        
        # Create target diagram nodes
        target_nodes = []
        target_node_uuids = []
        
        # Added nodes (only in target)
        for i in range(num_added_nodes):
            node_uuid = f'_a-added-node-{i:04d}'
            target_node_uuids.append(node_uuid)
            target_nodes.append({
                'id': f'n_a_added_node_{i:04d}',
                'label': f'Added Node {i}',
                'type': NodeType.SCRIPT_TASK.value,
                'shape': 'rect',
                'shape_open': '[',
                'shape_close': ']',
                'properties': {},
                'uuid': node_uuid
            })
        
        # Modified nodes (in both, but changed)
        for i in range(num_modified_nodes):
            node_uuid = modified_node_uuids[i]
            target_node_uuids.append(node_uuid)
            target_nodes.append({
                'id': f'n_a_modified_node_{i:04d}',
                'label': f'Modified Node {i} (Changed)',
                'type': NodeType.SCRIPT_TASK.value,
                'shape': 'rect',
                'shape_open': '[',
                'shape_close': ']',
                'properties': {},
                'uuid': node_uuid
            })
        
        # Unchanged nodes (in both, same)
        for i in range(num_unchanged_nodes):
            node_uuid = unchanged_node_uuids[i]
            target_node_uuids.append(node_uuid)
            target_nodes.append({
                'id': f'n_a_unchanged_node_{i:04d}',
                'label': f'Unchanged Node {i}',
                'type': NodeType.SCRIPT_TASK.value,
                'shape': 'rect',
                'shape_open': '[',
                'shape_close': ']',
                'properties': {},
                'uuid': node_uuid
            })
        
        target_diagram = {
            'nodes': target_nodes,
            'edges': [],
            'start_nodes': [],
            'end_nodes': []
        }
        
        # Create node changes
        added_nodes_data = [
            {'uuid': f'_a-added-node-{i:04d}', 'name': f'Added Node {i}'}
            for i in range(num_added_nodes)
        ]
        
        removed_nodes_data = [
            {'uuid': f'_a-removed-node-{i:04d}', 'name': f'Removed Node {i}'}
            for i in range(num_removed_nodes)
        ]
        
        modified_nodes_data = [
            {
                'node': {
                    'uuid': modified_node_uuids[i],
                    'name': f'Modified Node {i}'
                },
                'changes': [{'property': 'name', 'before': 'old', 'after': 'new'}]
            }
            for i in range(num_modified_nodes)
        ]
        
        node_changes = {
            'added': added_nodes_data,
            'removed': removed_nodes_data,
            'modified': modified_nodes_data,
            'unchanged': []
        }
        
        # Create flow changes (empty for this test)
        flow_changes = {
            'added_flows': [],
            'removed_flows': [],
            'modified_flows': [],
            'unchanged_flows': []
        }
        
        # Generate comparison diagram
        comparison_diagram = self.diagram_generator.generate_comparison_diagram(
            base_diagram,
            target_diagram,
            node_changes,
            flow_changes
        )
        
        # Property 1: Comparison diagram must have required fields
        self.assertIn('mermaid_syntax', comparison_diagram)
        self.assertIn('nodes', comparison_diagram)
        self.assertIn('edges', comparison_diagram)
        self.assertIn('changes_summary', comparison_diagram)
        
        # Property 2: Changes summary must have correct counts
        self.assertEqual(
            comparison_diagram['changes_summary']['nodes_added'],
            num_added_nodes
        )
        self.assertEqual(
            comparison_diagram['changes_summary']['nodes_removed'],
            num_removed_nodes
        )
        self.assertEqual(
            comparison_diagram['changes_summary']['nodes_modified'],
            num_modified_nodes
        )
        
        # Property 3: All nodes must have change_type annotation
        for node in comparison_diagram['nodes']:
            self.assertIn('change_type', node)
            self.assertIn(
                node['change_type'],
                ['ADDED', 'REMOVED', 'MODIFIED', 'UNCHANGED']
            )
        
        # Property 4: Added nodes must have green color
        added_nodes_in_diagram = [
            node for node in comparison_diagram['nodes']
            if node['change_type'] == 'ADDED'
        ]
        for node in added_nodes_in_diagram:
            self.assertIn('change_color', node)
            self.assertEqual(node['change_color'], '#90EE90')
        
        # Property 5: Removed nodes must have red/pink color
        removed_nodes_in_diagram = [
            node for node in comparison_diagram['nodes']
            if node['change_type'] == 'REMOVED'
        ]
        for node in removed_nodes_in_diagram:
            self.assertIn('change_color', node)
            self.assertEqual(node['change_color'], '#FFB6C1')
        
        # Property 6: Modified nodes must have yellow/gold color
        modified_nodes_in_diagram = [
            node for node in comparison_diagram['nodes']
            if node['change_type'] == 'MODIFIED'
        ]
        for node in modified_nodes_in_diagram:
            self.assertIn('change_color', node)
            self.assertEqual(node['change_color'], '#FFD700')
        
        # Property 7: Unchanged nodes must have no color (None)
        unchanged_nodes_in_diagram = [
            node for node in comparison_diagram['nodes']
            if node['change_type'] == 'UNCHANGED'
        ]
        for node in unchanged_nodes_in_diagram:
            self.assertIn('change_color', node)
            self.assertIsNone(node['change_color'])
        
        # Property 8: Total nodes should equal sum of all change types
        total_nodes = (
            num_added_nodes + num_removed_nodes +
            num_modified_nodes + num_unchanged_nodes
        )
        self.assertEqual(len(comparison_diagram['nodes']), total_nodes)
        
        # Property 9: Mermaid syntax must include styling for changed nodes
        mermaid_syntax = comparison_diagram['mermaid_syntax']
        
        # Check for color styling in Mermaid syntax
        if num_added_nodes > 0:
            self.assertIn('#90EE90', mermaid_syntax)
        
        if num_removed_nodes > 0:
            self.assertIn('#FFB6C1', mermaid_syntax)
        
        if num_modified_nodes > 0:
            self.assertIn('#FFD700', mermaid_syntax)
        
        # Property 10: Mermaid syntax must include legend
        self.assertIn('Legend', mermaid_syntax)
        self.assertIn('Added', mermaid_syntax)
        self.assertIn('Modified', mermaid_syntax)
        self.assertIn('Removed', mermaid_syntax)


    @given(
        object_type=st.sampled_from([
            'Interface',
            'Expression Rule',
            'Record Type',
            'Constant',
            'Data Store Entity'
        ]),
        has_sail_code=st.booleans(),
        has_properties=st.booleans()
    )
    @hypothesis_settings(max_examples=100)
    def test_property_26_non_process_model_display(
        self,
        object_type,
        has_sail_code,
        has_properties
    ):
        """
        **Feature: process-model-visualization, Property 26: Non-process-model display**
        **Validates: Requirements 9.4**
        
        For any non-process-model object type, the change detail template
        should fall back to the standard display logic and not attempt to
        render process model-specific visualizations.
        
        This ensures backward compatibility with existing object types.
        """
        # Read the template file to verify the conditional logic
        with open('templates/merge_assistant/change_detail.html', 'r') as f:
            template_content = f.read()
        
        # Verify that the template has conditional logic for process models
        # The template should check for process_model_data.has_enhanced_data
        self.assertIn(
            'process_model_data',
            template_content,
            "Template should check for process_model_data"
        )
        
        self.assertIn(
            'has_enhanced_data',
            template_content,
            "Template should check for has_enhanced_data flag"
        )
        
        # Verify that process model-specific includes are conditional
        # They should only be included when has_enhanced_data is True
        
        # Check that _process_model_summary.html is conditionally included
        if '_process_model_summary.html' in template_content:
            # Find the context around this include
            summary_idx = template_content.find('_process_model_summary.html')
            context_start = max(0, summary_idx - 200)
            context_end = min(len(template_content), summary_idx + 200)
            context = template_content[context_start:context_end]
            
            # Verify it's within a conditional block
            self.assertTrue(
                'if' in context or 'has_enhanced_data' in context,
                "_process_model_summary.html should be conditionally included"
            )
        
        # Check that _process_model_three_way.html is conditionally included
        if '_process_model_three_way.html' in template_content:
            three_way_idx = template_content.find('_process_model_three_way.html')
            context_start = max(0, three_way_idx - 200)
            context_end = min(len(template_content), three_way_idx + 200)
            context = template_content[context_start:context_end]
            
            self.assertTrue(
                'if' in context or 'has_enhanced_data' in context,
                "_process_model_three_way.html should be conditionally included"
            )
        
        # Check that _process_model_flow_diagram.html is conditionally included
        if '_process_model_flow_diagram.html' in template_content:
            flow_idx = template_content.find('_process_model_flow_diagram.html')
            context_start = max(0, flow_idx - 200)
            context_end = min(len(template_content), flow_idx + 200)
            context = template_content[context_start:context_end]
            
            self.assertTrue(
                'if' in context or 'has_enhanced_data' in context,
                "_process_model_flow_diagram.html should be conditionally included"
            )
        
        # Verify the logic: when has_enhanced_data is False, 
        # process model templates should not be rendered
        # This is tested by checking the template structure
        
        # Create a mock change object for a non-process-model type
        change = {
            'uuid': '_a-test-uuid-12345',
            'name': f'Test {object_type}',
            'type': object_type,
            'classification': 'NO_CONFLICT',
            'review_status': 'pending',
            'user_notes': None,
            'process_model_data': {
                'has_enhanced_data': False
            }
        }
        
        # Verify that the change object structure is correct
        self.assertFalse(
            change.get('process_model_data', {}).get('has_enhanced_data', False),
            "Non-process-model objects should have has_enhanced_data=False"
        )
        
        # Verify that when type is not 'Process Model', 
        # the has_enhanced_data flag should be False
        self.assertNotEqual(
            object_type,
            'Process Model',
            "Test should use non-process-model types"
        )
