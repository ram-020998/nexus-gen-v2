"""
Integration Tests for Process Model Visualization

Tests the complete end-to-end workflow of process model parsing,
comparison, and visualization using real Appian packages.
"""
import os
import json
import zipfile
import xml.etree.ElementTree as ET
from tests.base_test import BaseTestCase
from services.appian_analyzer.analyzer import AppianAnalyzer
from services.appian_analyzer.parsers import ProcessModelParser
from services.appian_analyzer.process_model_enhancement import (
    NodeExtractor,
    FlowExtractor,
    NodeComparator
)
from services.appian_analyzer.sail_formatter import SAILFormatter
from services.merge_assistant.three_way_comparison_service import ThreeWayComparisonService


class TestProcessModelIntegration(BaseTestCase):
    """Integration tests for process model visualization with real packages"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.test_files_dir = 'applicationArtifacts/Testing Files'
        self.old_package = os.path.join(self.test_files_dir, 'SourceSelectionv2.4.0.zip')
        self.new_package = os.path.join(self.test_files_dir, 'SourceSelectionv2.6.0.zip')
    
    def test_real_package_blueprint_generation(self):
        """
        Test blueprint generation with real Appian packages
        Validates that enhanced parser works with actual process models
        """
        # Check if test files exist
        if not os.path.exists(self.old_package):
            self.skipTest(f"Test package not found: {self.old_package}")
        
        # Generate blueprint for old package
        analyzer = AppianAnalyzer(self.old_package)
        result = analyzer.analyze()
        blueprint = result['blueprint']
        
        # Verify blueprint structure
        self.assertIsNotNone(blueprint)
        self.assertIn('metadata', blueprint)
        self.assertIn('process_models', blueprint)
        
        # Get process models from blueprint
        process_models = blueprint['process_models']
        
        # Verify process models were found and parsed
        if len(process_models) > 0:
            pm = process_models[0]
            
            # Verify enhanced fields are present
            self.assertIn('nodes', pm)
            self.assertIn('flows', pm)
            self.assertIn('flow_graph', pm)
            self.assertIn('node_summary', pm)
            
            # Verify backward compatibility
            self.assertIn('business_logic', pm)
            
            # Verify nodes have enhanced structure
            if len(pm['nodes']) > 0:
                node = pm['nodes'][0]
                self.assertIn('uuid', node)
                self.assertIn('name', node)
                self.assertIn('type', node)
                self.assertIn('properties', node)
                self.assertIn('dependencies', node)

    
    def test_process_model_size_categories(self):
        """
        Test with process models of different sizes
        - Small: < 10 nodes
        - Medium: 10-50 nodes
        - Large: 50+ nodes
        """
        if not os.path.exists(self.old_package):
            self.skipTest(f"Test package not found: {self.old_package}")
        
        analyzer = AppianAnalyzer(self.old_package)
        result = analyzer.analyze()
        blueprint = result['blueprint']
        
        process_models = blueprint['process_models']
        
        # Categorize by size
        small_models = []
        medium_models = []
        large_models = []
        
        for pm in process_models:
            node_count = len(pm.get('nodes', []))
            if node_count < 10:
                small_models.append(pm)
            elif node_count < 50:
                medium_models.append(pm)
            else:
                large_models.append(pm)
        
        # Test small models
        for pm in small_models:
            self._verify_process_model_structure(pm)
            self._verify_flow_graph_correctness(pm)
        
        # Test medium models
        for pm in medium_models:
            self._verify_process_model_structure(pm)
            self._verify_flow_graph_correctness(pm)
        
        # Test large models
        for pm in large_models:
            self._verify_process_model_structure(pm)
            self._verify_flow_graph_correctness(pm)
        
        # Log results
        print(f"\nProcess Model Size Distribution:")
        print(f"  Small (< 10 nodes): {len(small_models)}")
        print(f"  Medium (10-50 nodes): {len(medium_models)}")
        print(f"  Large (50+ nodes): {len(large_models)}")
    
    def test_node_type_coverage(self):
        """
        Test that all node types are handled correctly
        """
        if not os.path.exists(self.old_package):
            self.skipTest(f"Test package not found: {self.old_package}")
        
        analyzer = AppianAnalyzer(self.old_package)
        result = analyzer.analyze()
        blueprint = result['blueprint']
        
        process_models = blueprint['process_models']
        
        # Collect all node types found
        node_types_found = set()
        
        for pm in process_models:
            for node in pm.get('nodes', []):
                node_type = node.get('type')
                if node_type:
                    node_types_found.add(node_type)
                
                # Verify node has required structure
                self.assertIn('uuid', node)
                self.assertIn('name', node)
                self.assertIn('type', node)
                self.assertIn('properties', node)
                
                # Verify properties have all categories
                props = node['properties']
                self.assertIn('basic', props)
                self.assertIn('assignment', props)
                self.assertIn('forms', props)
                self.assertIn('expressions', props)
                self.assertIn('escalation', props)
        
        # Log node types found
        print(f"\nNode Types Found: {sorted(node_types_found)}")
        
        # Verify we found at least some common types
        # (This will vary by package, so we just check structure)
        self.assertGreater(len(node_types_found), 0)

    
    def test_three_way_comparison_with_process_models(self):
        """
        Test three-way comparison with process models
        """
        if not os.path.exists(self.old_package) or not os.path.exists(self.new_package):
            self.skipTest("Test packages not found")
        
        # Generate blueprints
        old_analyzer = AppianAnalyzer(self.old_package)
        old_result = old_analyzer.analyze()
        old_blueprint = old_result['blueprint']
        
        new_analyzer = AppianAnalyzer(self.new_package)
        new_result = new_analyzer.analyze()
        new_blueprint = new_result['blueprint']
        
        # Use old as base and customer, new as vendor
        comparison_service = ThreeWayComparisonService()
        
        # Perform comparison
        changes = comparison_service.compare_three_way(
            old_blueprint,
            old_blueprint,  # Customer = base (no customization)
            new_blueprint   # Vendor = new version
        )
        
        # Verify comparison results
        self.assertIsNotNone(changes)
        self.assertIsInstance(changes, list)
        
        # Find process model changes
        pm_changes = [
            change for change in changes
            if change.get('object_type') == 'Process Model'
        ]
        
        # Verify process model changes have enhanced data
        for change in pm_changes:
            if change.get('change_type') == 'MODIFIED':
                # Should have node-level comparison data
                self.assertIn('base_version', change)
                self.assertIn('customer_version', change)
                self.assertIn('vendor_version', change)
                
                # Verify versions have enhanced structure
                for version_key in ['base_version', 'customer_version', 'vendor_version']:
                    version = change.get(version_key)
                    if version:
                        self.assertIn('nodes', version)
                        self.assertIn('flows', version)
    
    def test_error_recovery_with_malformed_xml(self):
        """
        Test error recovery with malformed XML
        Validates that parser falls back gracefully
        """
        # Create a malformed process model XML
        malformed_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <root>
            <process_model_port xmlns="http://www.appian.com/ae/types/2009">
                <pm>
                    <meta>
                        <uuid>_a-test-uuid</uuid>
                        <name>
                            <string-map>
                                <pair>
                                    <locale lang="en"/>
                                    <value>Test Process</value>
                                </pair>
                            </string-map>
                        </name>
                    </meta>
                    <nodes>
                        <node>
                            <!-- Missing AC element - should trigger fallback -->
                            <uuid>_a-node-uuid</uuid>
                        </node>
                    </nodes>
                </pm>
            </process_model_port>
        </root>
        """
        
        # Parse malformed XML
        root = ET.fromstring(malformed_xml)
        
        parser = ProcessModelParser()
        object_lookup = {}
        sail_formatter = SAILFormatter(object_lookup)
        parser.set_object_lookup(object_lookup)
        parser.set_sail_formatter(sail_formatter)
        
        # Should not raise exception
        result = parser.parse(root, 'test.xml')
        
        # Verify result is returned (even if partial)
        self.assertIsNotNone(result)
        self.assertEqual(result.object_type, "Process Model")

    
    def test_performance_with_large_process_models(self):
        """
        Test performance with large process models
        Measures parsing and comparison time
        """
        import time
        
        if not os.path.exists(self.old_package):
            self.skipTest(f"Test package not found: {self.old_package}")
        
        # Measure blueprint generation time
        start_time = time.time()
        analyzer = AppianAnalyzer(self.old_package)
        result = analyzer.analyze()
        blueprint = result['blueprint']
        generation_time = time.time() - start_time
        
        # Find largest process model
        process_models = blueprint['process_models']
        
        if len(process_models) == 0:
            self.skipTest("No process models found in package")
        
        # Sort by node count
        process_models.sort(key=lambda pm: len(pm.get('nodes', [])), reverse=True)
        largest_pm = process_models[0]
        
        node_count = len(largest_pm.get('nodes', []))
        flow_count = len(largest_pm.get('flows', []))
        
        print(f"\nPerformance Metrics:")
        print(f"  Total blueprint generation time: {generation_time:.2f}s")
        print(f"  Largest process model: {largest_pm.get('name')}")
        print(f"    Nodes: {node_count}")
        print(f"    Flows: {flow_count}")
        
        # Verify reasonable performance
        # Target: < 10 seconds for full blueprint generation
        self.assertLess(generation_time, 10.0,
                       f"Blueprint generation took {generation_time:.2f}s, expected < 10s")
    
    def test_memory_usage_with_complex_models(self):
        """
        Test memory usage with complex process models
        """
        import sys
        
        if not os.path.exists(self.old_package):
            self.skipTest(f"Test package not found: {self.old_package}")
        
        # Get initial memory usage
        initial_size = sys.getsizeof(self)
        
        # Generate blueprint
        analyzer = AppianAnalyzer(self.old_package)
        result = analyzer.analyze()
        blueprint = result['blueprint']
        
        # Get blueprint size
        blueprint_json = json.dumps(blueprint)
        blueprint_size = sys.getsizeof(blueprint_json)
        
        print(f"\nMemory Usage:")
        print(f"  Blueprint size: {blueprint_size / 1024 / 1024:.2f} MB")
        
        # Verify reasonable memory usage
        # Target: < 100 MB for blueprint
        self.assertLess(blueprint_size, 100 * 1024 * 1024,
                       f"Blueprint size {blueprint_size / 1024 / 1024:.2f} MB exceeds 100 MB")
    
    def _verify_process_model_structure(self, pm):
        """Helper to verify process model structure"""
        # Verify required fields
        self.assertIn('uuid', pm)
        self.assertIn('name', pm)
        self.assertIn('object_type', pm)
        self.assertIn('nodes', pm)
        self.assertIn('flows', pm)
        self.assertIn('flow_graph', pm)
        self.assertIn('node_summary', pm)
        self.assertIn('business_logic', pm)
        
        # Verify types
        self.assertIsInstance(pm['nodes'], list)
        self.assertIsInstance(pm['flows'], list)
        self.assertIsInstance(pm['flow_graph'], dict)
        self.assertIsInstance(pm['node_summary'], dict)
        self.assertIsInstance(pm['business_logic'], str)
    
    def _verify_flow_graph_correctness(self, pm):
        """Helper to verify flow graph correctness"""
        flow_graph = pm.get('flow_graph', {})
        nodes = pm.get('nodes', [])
        flows = pm.get('flows', [])
        
        if not flow_graph:
            return  # Empty flow graph is valid for models with no flows
        
        # Verify flow graph structure
        self.assertIn('start_nodes', flow_graph)
        self.assertIn('end_nodes', flow_graph)
        self.assertIn('node_connections', flow_graph)
        
        # Verify node connections
        node_connections = flow_graph.get('node_connections', {})
        
        # All nodes should be in node_connections
        node_uuids = {node['uuid'] for node in nodes}
        connection_uuids = set(node_connections.keys())
        
        # Connection UUIDs should be subset of node UUIDs
        # (Some nodes might not have connections)
        self.assertTrue(connection_uuids.issubset(node_uuids))
        
        # Verify start nodes have no incoming flows
        for start_node_uuid in flow_graph.get('start_nodes', []):
            if start_node_uuid in node_connections:
                incoming = node_connections[start_node_uuid].get('incoming', [])
                self.assertEqual(len(incoming), 0,
                               f"Start node {start_node_uuid} has incoming flows")
        
        # Verify end nodes have no outgoing flows
        for end_node_uuid in flow_graph.get('end_nodes', []):
            if end_node_uuid in node_connections:
                outgoing = node_connections[end_node_uuid].get('outgoing', [])
                self.assertEqual(len(outgoing), 0,
                               f"End node {end_node_uuid} has outgoing flows")


class TestProcessModelComparison(BaseTestCase):
    """Integration tests for process model comparison"""
    
    def setUp(self):
        """Set up test fixtures"""
        super().setUp()
        self.object_lookup = {}
        self.node_comparator = NodeComparator()
    
    def test_node_comparison_with_real_data(self):
        """Test node comparison with realistic node data"""
        # Create base nodes
        base_nodes = [
            {
                'uuid': '_a-node-001',
                'name': 'Start Node',
                'type': 'START_NODE',
                'properties': {
                    'basic': {'description': 'Start of process'},
                    'assignment': {'type': 'NONE', 'assignees': []},
                    'forms': {},
                    'expressions': {},
                    'escalation': {'enabled': False}
                }
            },
            {
                'uuid': '_a-node-002',
                'name': 'User Task',
                'type': 'USER_INPUT_TASK',
                'properties': {
                    'basic': {'description': 'User input'},
                    'assignment': {'type': 'USER', 'assignees': ['john.doe']},
                    'forms': {'interface_uuid': '_a-interface-001'},
                    'expressions': {},
                    'escalation': {'enabled': False}
                }
            }
        ]
        
        # Create target nodes (modified)
        target_nodes = [
            {
                'uuid': '_a-node-001',
                'name': 'Start Node',
                'type': 'START_NODE',
                'properties': {
                    'basic': {'description': 'Start of process'},
                    'assignment': {'type': 'NONE', 'assignees': []},
                    'forms': {},
                    'expressions': {},
                    'escalation': {'enabled': False}
                }
            },
            {
                'uuid': '_a-node-002',
                'name': 'User Task',
                'type': 'USER_INPUT_TASK',
                'properties': {
                    'basic': {'description': 'Updated user input'},  # Changed
                    'assignment': {'type': 'GROUP', 'assignees': ['Administrators']},  # Changed
                    'forms': {'interface_uuid': '_a-interface-002'},  # Changed
                    'expressions': {},
                    'escalation': {'enabled': True, 'escalation_time': '1 day'}  # Changed
                }
            },
            {
                'uuid': '_a-node-003',
                'name': 'New Node',
                'type': 'SCRIPT_TASK',
                'properties': {
                    'basic': {'description': 'New script task'},
                    'assignment': {'type': 'NONE', 'assignees': []},
                    'forms': {},
                    'expressions': {'output_expressions': {'pv!result': 'true'}},
                    'escalation': {'enabled': False}
                }
            }
        ]
        
        # Compare nodes
        result = self.node_comparator.compare_nodes(base_nodes, target_nodes)
        
        # Verify comparison results
        self.assertIn('added', result)
        self.assertIn('removed', result)
        self.assertIn('modified', result)
        self.assertIn('unchanged', result)
        
        # Verify added nodes
        self.assertEqual(len(result['added']), 1)
        self.assertEqual(result['added'][0]['uuid'], '_a-node-003')
        
        # Verify removed nodes
        self.assertEqual(len(result['removed']), 0)
        
        # Verify modified nodes
        self.assertEqual(len(result['modified']), 1)
        modified = result['modified'][0]
        self.assertEqual(modified['node']['uuid'], '_a-node-002')
        self.assertGreater(len(modified['changes']), 0)
        
        # Verify unchanged nodes
        self.assertEqual(len(result['unchanged']), 1)
        self.assertEqual(result['unchanged'][0]['uuid'], '_a-node-001')
