"""
Tests for object-specific repositories.

Validates that all object-specific repositories can create and retrieve objects correctly.
"""

import pytest
from tests.base_test import BaseTestCase
from models import db
from repositories import (
    ObjectLookupRepository,
    InterfaceRepository,
    ExpressionRuleRepository,
    ProcessModelRepository,
    RecordTypeRepository,
    CDTRepository,
    IntegrationRepository,
    WebAPIRepository,
    SiteRepository,
    GroupRepository,
    ConstantRepository,
    ConnectedSystemRepository,
    UnknownObjectRepository
)


class TestObjectRepositories(BaseTestCase):
    """Test object-specific repositories."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        self.object_lookup_repo = ObjectLookupRepository()
        self.interface_repo = InterfaceRepository()
        self.expression_rule_repo = ExpressionRuleRepository()
        self.process_model_repo = ProcessModelRepository()
        self.record_type_repo = RecordTypeRepository()
        self.cdt_repo = CDTRepository()
        self.integration_repo = IntegrationRepository()
        self.web_api_repo = WebAPIRepository()
        self.site_repo = SiteRepository()
        self.group_repo = GroupRepository()
        self.constant_repo = ConstantRepository()
        self.connected_system_repo = ConnectedSystemRepository()
        self.unknown_object_repo = UnknownObjectRepository()
    
    def test_interface_repository_create_and_retrieve(self):
        """Test creating and retrieving an interface."""
        # Create object in object_lookup
        obj_lookup = self.object_lookup_repo.find_or_create(
            uuid="test-interface-uuid",
            name="Test Interface",
            object_type="Interface"
        )
        
        # Create interface with parameters and security
        interface = self.interface_repo.create_interface(
            object_id=obj_lookup.id,
            uuid="test-interface-uuid",
            name="Test Interface",
            version_uuid="v1",
            sail_code="a!localVariables()",
            parameters=[
                {
                    "parameter_name": "input1",
                    "parameter_type": "Text",
                    "is_required": True,
                    "display_order": 1
                }
            ],
            security=[
                {
                    "role_name": "Admin",
                    "permission_type": "EDIT"
                }
            ]
        )
        db.session.commit()
        
        # Retrieve and verify
        retrieved = self.interface_repo.get_by_object_id(obj_lookup.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Interface")
        self.assertEqual(retrieved.uuid, "test-interface-uuid")
        
        # Verify parameters
        params = self.interface_repo.get_parameters(interface.id)
        self.assertEqual(len(params), 1)
        self.assertEqual(params[0].parameter_name, "input1")
        
        # Verify security
        security = self.interface_repo.get_security_settings(interface.id)
        self.assertEqual(len(security), 1)
        self.assertEqual(security[0].role_name, "Admin")
    
    def test_process_model_repository_create_and_retrieve(self):
        """Test creating and retrieving a process model."""
        # Create object in object_lookup
        obj_lookup = self.object_lookup_repo.find_or_create(
            uuid="test-pm-uuid",
            name="Test Process Model",
            object_type="Process Model"
        )
        
        # Create process model with nodes, flows, and variables
        pm = self.process_model_repo.create_process_model(
            object_id=obj_lookup.id,
            uuid="test-pm-uuid",
            name="Test Process Model",
            version_uuid="v1",
            total_nodes=2,
            total_flows=1,
            complexity_score=3.0,
            nodes=[
                {
                    "node_id": "node1",
                    "node_type": "Start",
                    "node_name": "Start Node"
                },
                {
                    "node_id": "node2",
                    "node_type": "End",
                    "node_name": "End Node"
                }
            ],
            flows=[
                {
                    "from_node_id": "node1",
                    "to_node_id": "node2",
                    "flow_label": "Next"
                }
            ],
            variables=[
                {
                    "variable_name": "var1",
                    "variable_type": "Text",
                    "is_parameter": True
                }
            ]
        )
        db.session.commit()
        
        # Retrieve and verify
        retrieved = self.process_model_repo.get_by_object_id(obj_lookup.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Process Model")
        self.assertEqual(retrieved.total_nodes, 2)
        self.assertEqual(retrieved.total_flows, 1)
        
        # Verify nodes
        nodes = self.process_model_repo.get_nodes(pm.id)
        self.assertEqual(len(nodes), 2)
        
        # Verify flows
        flows = self.process_model_repo.get_flows(pm.id)
        self.assertEqual(len(flows), 1)
        
        # Verify variables
        variables = self.process_model_repo.get_variables(pm.id)
        self.assertEqual(len(variables), 1)
        self.assertEqual(variables[0].variable_name, "var1")
    
    def test_record_type_repository_create_and_retrieve(self):
        """Test creating and retrieving a record type."""
        # Create object in object_lookup
        obj_lookup = self.object_lookup_repo.find_or_create(
            uuid="test-rt-uuid",
            name="Test Record Type",
            object_type="Record Type"
        )
        
        # Create record type with fields
        rt = self.record_type_repo.create_record_type(
            object_id=obj_lookup.id,
            uuid="test-rt-uuid",
            name="Test Record Type",
            version_uuid="v1",
            source_type="database",
            fields=[
                {
                    "field_name": "id",
                    "field_type": "Number",
                    "is_primary_key": True,
                    "is_required": True,
                    "display_order": 1
                }
            ]
        )
        db.session.commit()
        
        # Retrieve and verify
        retrieved = self.record_type_repo.get_by_object_id(obj_lookup.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Record Type")
        
        # Verify fields
        fields = self.record_type_repo.get_fields(rt.id)
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0].field_name, "id")
        self.assertTrue(fields[0].is_primary_key)
    
    def test_expression_rule_repository_create_and_retrieve(self):
        """Test creating and retrieving an expression rule."""
        # Create object in object_lookup
        obj_lookup = self.object_lookup_repo.find_or_create(
            uuid="test-er-uuid",
            name="Test Expression Rule",
            object_type="Expression Rule"
        )
        
        # Create expression rule using new method signature
        er = self.expression_rule_repo.create_expression_rule(
            object_id=obj_lookup.id,
            data={
                "uuid": "test-er-uuid",
                "name": "Test Expression Rule",
                "version_uuid": "v1",
                "sail_code": "a!localVariables()",
                "output_type": "Text",
                "description": "Test rule"
            }
        )
        
        # Create inputs using separate method
        self.expression_rule_repo.create_expression_rule_input(
            rule_id=er.id,
            data={
                "input_name": "input1",
                "input_type": "Text",
                "is_required": True,
                "display_order": 1
            }
        )
        db.session.commit()
        
        # Retrieve and verify
        retrieved = self.expression_rule_repo.get_by_object_id(obj_lookup.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Expression Rule")
        self.assertEqual(retrieved.uuid, "test-er-uuid")
        
        # Verify inputs are eager loaded
        # Access inputs directly from the relationship
        inputs_from_relationship = list(retrieved.inputs)
        self.assertEqual(len(inputs_from_relationship), 1)
        self.assertEqual(inputs_from_relationship[0].input_name, "input1")
        
        # Also verify get_inputs method still works
        inputs = self.expression_rule_repo.get_inputs(er.id)
        self.assertEqual(len(inputs), 1)
        self.assertEqual(inputs[0].input_name, "input1")
    
    def test_cdt_repository_create_and_retrieve(self):
        """Test creating and retrieving a CDT."""
        # Create object in object_lookup
        obj_lookup = self.object_lookup_repo.find_or_create(
            uuid="test-cdt-uuid",
            name="Test CDT",
            object_type="CDT"
        )
        
        # Create CDT with fields
        cdt = self.cdt_repo.create_cdt(
            object_id=obj_lookup.id,
            uuid="test-cdt-uuid",
            name="Test CDT",
            version_uuid="v1",
            namespace="com.example",
            fields=[
                {
                    "field_name": "field1",
                    "field_type": "Text",
                    "is_list": False,
                    "is_required": True,
                    "display_order": 1
                }
            ]
        )
        db.session.commit()
        
        # Retrieve and verify
        retrieved = self.cdt_repo.get_by_object_id(obj_lookup.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test CDT")
        self.assertEqual(retrieved.namespace, "com.example")
        
        # Verify fields
        fields = self.cdt_repo.get_fields(cdt.id)
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0].field_name, "field1")
    
    def test_simple_object_repositories(self):
        """Test simple object repositories (no child tables)."""
        # Test Integration
        obj_lookup = self.object_lookup_repo.find_or_create(
            uuid="test-integration-uuid",
            name="Test Integration",
            object_type="Integration"
        )
        integration = self.integration_repo.create_integration(
            object_id=obj_lookup.id,
            uuid="test-integration-uuid",
            name="Test Integration",
            endpoint="https://api.example.com"
        )
        db.session.commit()
        retrieved = self.integration_repo.get_by_object_id(obj_lookup.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Integration")
        
        # Test Web API
        obj_lookup = self.object_lookup_repo.find_or_create(
            uuid="test-webapi-uuid",
            name="Test Web API",
            object_type="Web API"
        )
        web_api = self.web_api_repo.create_web_api(
            object_id=obj_lookup.id,
            uuid="test-webapi-uuid",
            name="Test Web API",
            endpoint="/api/test"
        )
        db.session.commit()
        retrieved = self.web_api_repo.get_by_object_id(obj_lookup.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Web API")
        
        # Test Site
        obj_lookup = self.object_lookup_repo.find_or_create(
            uuid="test-site-uuid",
            name="Test Site",
            object_type="Site"
        )
        site = self.site_repo.create_site(
            object_id=obj_lookup.id,
            uuid="test-site-uuid",
            name="Test Site"
        )
        db.session.commit()
        retrieved = self.site_repo.get_by_object_id(obj_lookup.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Site")
        
        # Test Group
        obj_lookup = self.object_lookup_repo.find_or_create(
            uuid="test-group-uuid",
            name="Test Group",
            object_type="Group"
        )
        group = self.group_repo.create_group(
            object_id=obj_lookup.id,
            uuid="test-group-uuid",
            name="Test Group"
        )
        db.session.commit()
        retrieved = self.group_repo.get_by_object_id(obj_lookup.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Group")
        
        # Test Constant
        obj_lookup = self.object_lookup_repo.find_or_create(
            uuid="test-constant-uuid",
            name="Test Constant",
            object_type="Constant"
        )
        constant = self.constant_repo.create_constant(
            object_id=obj_lookup.id,
            uuid="test-constant-uuid",
            name="Test Constant",
            constant_value="100"
        )
        db.session.commit()
        retrieved = self.constant_repo.get_by_object_id(obj_lookup.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Constant")
        
        # Test Connected System
        obj_lookup = self.object_lookup_repo.find_or_create(
            uuid="test-cs-uuid",
            name="Test Connected System",
            object_type="Connected System"
        )
        cs = self.connected_system_repo.create_connected_system(
            object_id=obj_lookup.id,
            uuid="test-cs-uuid",
            name="Test Connected System",
            system_type="HTTP"
        )
        db.session.commit()
        retrieved = self.connected_system_repo.get_by_object_id(obj_lookup.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Connected System")
        
        # Test Unknown Object
        obj_lookup = self.object_lookup_repo.find_or_create(
            uuid="test-unknown-uuid",
            name="Test Unknown",
            object_type="Unknown"
        )
        unknown = self.unknown_object_repo.create_unknown_object(
            object_id=obj_lookup.id,
            uuid="test-unknown-uuid",
            name="Test Unknown",
            raw_xml="<xml>test</xml>"
        )
        db.session.commit()
        retrieved = self.unknown_object_repo.get_by_object_id(obj_lookup.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Unknown")
