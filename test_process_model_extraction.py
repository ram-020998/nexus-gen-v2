#!/usr/bin/env python3
"""
Comprehensive test for Process Model extraction from XML

This script tests the entire flow of process model extraction:
1. Parse XML file
2. Extract nodes with all properties
3. Extract flows (connections between nodes)
4. Verify data structure and completeness
5. Test database storage (optional)

Usage:
    python test_process_model_extraction.py
"""

import sys
import os
import json
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from pprint import pprint

# Add services to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from services.appian_analyzer.parsers import ProcessModelParser
from services.appian_analyzer.process_model_enhancement import (
    NodeExtractor, FlowExtractor, log_parsing_start, log_parsing_complete
)
from services.appian_analyzer.sail_formatter import SAILFormatter


class ProcessModelExtractionTester:
    """Test harness for process model extraction"""
    
    def __init__(self, xml_file_path: str):
        self.xml_file_path = xml_file_path
        self.parser = ProcessModelParser()
        self.object_lookup = {}  # Empty for now, can be populated if needed
        self.sail_formatter = SAILFormatter(self.object_lookup)
        
        # Set dependencies
        self.parser.set_object_lookup(self.object_lookup)
        self.parser.set_sail_formatter(self.sail_formatter)
        
        self.test_results = {
            'xml_parsing': False,
            'node_extraction': False,
            'flow_extraction': False,
            'data_structure': False,
            'errors': []
        }
    
    def run_all_tests(self):
        """Run all extraction tests"""
        print("=" * 80)
        print("PROCESS MODEL EXTRACTION TEST")
        print("=" * 80)
        print(f"XML File: {self.xml_file_path}")
        print()
        
        # Test 1: Parse XML
        print("Test 1: Parsing XML file...")
        root = self.test_xml_parsing()
        if not root:
            print("❌ FAILED: Could not parse XML")
            return False
        print("✅ PASSED: XML parsed successfully")
        print()
        
        # Test 2: Extract Process Model
        print("Test 2: Extracting Process Model...")
        process_model = self.test_process_model_extraction(root)
        if not process_model:
            print("❌ FAILED: Could not extract process model")
            return False
        print("✅ PASSED: Process model extracted")
        print()
        
        # Test 3: Verify Nodes
        print("Test 3: Verifying Node Extraction...")
        nodes_ok = self.test_node_extraction(process_model)
        if not nodes_ok:
            print("❌ FAILED: Node extraction issues")
        else:
            print("✅ PASSED: Nodes extracted correctly")
        print()
        
        # Test 4: Verify Flows
        print("Test 4: Verifying Flow Extraction...")
        flows_ok = self.test_flow_extraction(process_model)
        if not flows_ok:
            print("❌ FAILED: Flow extraction issues")
        else:
            print("✅ PASSED: Flows extracted correctly")
        print()
        
        # Test 5: Verify Data Structure
        print("Test 5: Verifying Data Structure...")
        structure_ok = self.test_data_structure(process_model)
        if not structure_ok:
            print("❌ FAILED: Data structure issues")
        else:
            print("✅ PASSED: Data structure is correct")
        print()
        
        # Test 6: Detailed Analysis
        print("Test 6: Detailed Analysis...")
        self.detailed_analysis(process_model)
        print()
        
        # Summary
        self.print_summary()
        
        return all([
            self.test_results['xml_parsing'],
            self.test_results['node_extraction'],
            self.test_results['flow_extraction'],
            self.test_results['data_structure']
        ])
    
    def test_xml_parsing(self) -> ET.Element:
        """Test XML file parsing"""
        try:
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()
            self.test_results['xml_parsing'] = True
            return root
        except Exception as e:
            self.test_results['errors'].append(f"XML Parsing: {str(e)}")
            return None
    
    def test_process_model_extraction(self, root: ET.Element):
        """Test process model extraction"""
        try:
            process_model = self.parser.parse(root, self.xml_file_path)
            if process_model:
                self.test_results['node_extraction'] = True
                return process_model
            else:
                self.test_results['errors'].append("Process model extraction returned None")
                return None
        except Exception as e:
            self.test_results['errors'].append(f"Process Model Extraction: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def test_node_extraction(self, process_model) -> bool:
        """Test node extraction"""
        try:
            if not hasattr(process_model, 'nodes'):
                self.test_results['errors'].append("Process model has no 'nodes' attribute")
                return False
            
            nodes = process_model.nodes
            if not nodes:
                self.test_results['errors'].append("No nodes extracted")
                return False
            
            print(f"   Total nodes extracted: {len(nodes)}")
            
            # Verify node structure
            for i, node in enumerate(nodes):
                if isinstance(node, dict):
                    required_fields = ['uuid', 'name', 'type']
                    missing = [f for f in required_fields if f not in node]
                    if missing:
                        self.test_results['errors'].append(
                            f"Node {i} missing fields: {missing}"
                        )
                        return False
                else:
                    self.test_results['errors'].append(
                        f"Node {i} is not a dictionary: {type(node)}"
                    )
                    return False
            
            return True
        except Exception as e:
            self.test_results['errors'].append(f"Node Extraction Test: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_flow_extraction(self, process_model) -> bool:
        """Test flow extraction"""
        try:
            if not hasattr(process_model, 'flows'):
                self.test_results['errors'].append("Process model has no 'flows' attribute")
                return False
            
            flows = process_model.flows
            if not flows:
                self.test_results['errors'].append("No flows extracted")
                return False
            
            print(f"   Total flows extracted: {len(flows)}")
            
            # Verify flow structure
            for i, flow in enumerate(flows):
                if isinstance(flow, dict):
                    required_fields = ['from_node_uuid', 'to_node_uuid']
                    missing = [f for f in required_fields if f not in flow]
                    if missing:
                        self.test_results['errors'].append(
                            f"Flow {i} missing fields: {missing}"
                        )
                        return False
                else:
                    self.test_results['errors'].append(
                        f"Flow {i} is not a dictionary: {type(flow)}"
                    )
                    return False
            
            self.test_results['flow_extraction'] = True
            return True
        except Exception as e:
            self.test_results['errors'].append(f"Flow Extraction Test: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_data_structure(self, process_model) -> bool:
        """Test overall data structure"""
        try:
            # Check basic attributes
            required_attrs = ['uuid', 'name', 'object_type', 'nodes', 'flows']
            missing = [attr for attr in required_attrs if not hasattr(process_model, attr)]
            
            if missing:
                self.test_results['errors'].append(f"Missing attributes: {missing}")
                return False
            
            # Check optional enhanced attributes
            if hasattr(process_model, 'flow_graph'):
                print("   ✓ Flow graph present")
            else:
                print("   ⚠ Flow graph not present")
            
            if hasattr(process_model, 'node_summary'):
                print("   ✓ Node summary present")
            else:
                print("   ⚠ Node summary not present")
            
            self.test_results['data_structure'] = True
            return True
        except Exception as e:
            self.test_results['errors'].append(f"Data Structure Test: {str(e)}")
            return False
    
    def detailed_analysis(self, process_model):
        """Perform detailed analysis of extracted data"""
        print("   Process Model Details:")
        print(f"   - UUID: {process_model.uuid}")
        print(f"   - Name: {process_model.name}")
        print(f"   - Type: {process_model.object_type}")
        print()
        
        # Node analysis
        print("   Node Analysis:")
        if process_model.nodes:
            node_types = {}
            for node in process_model.nodes:
                node_type = node.get('type', 'UNKNOWN')
                node_types[node_type] = node_types.get(node_type, 0) + 1
            
            for node_type, count in sorted(node_types.items()):
                print(f"   - {node_type}: {count}")
            
            print()
            print("   Sample Nodes:")
            for i, node in enumerate(process_model.nodes[:3]):
                print(f"   Node {i+1}:")
                print(f"     - UUID: {node.get('uuid', 'N/A')}")
                print(f"     - Name: {node.get('name', 'N/A')}")
                print(f"     - Type: {node.get('type', 'N/A')}")
                if 'properties' in node:
                    props = node['properties']
                    if isinstance(props, dict):
                        for prop_cat, prop_data in props.items():
                            if prop_data:
                                print(f"     - {prop_cat}: {len(prop_data)} properties")
                print()
        
        # Flow analysis
        print("   Flow Analysis:")
        if process_model.flows:
            print(f"   Total flows: {len(process_model.flows)}")
            
            # Count conditional flows
            conditional_flows = sum(1 for f in process_model.flows if f.get('condition'))
            print(f"   Conditional flows: {conditional_flows}")
            print(f"   Unconditional flows: {len(process_model.flows) - conditional_flows}")
            
            print()
            print("   Sample Flows:")
            for i, flow in enumerate(process_model.flows[:5]):
                print(f"   Flow {i+1}:")
                print(f"     - From: {flow.get('from_node_name', 'N/A')} ({flow.get('from_node_uuid', 'N/A')[:20]}...)")
                print(f"     - To: {flow.get('to_node_name', 'N/A')} ({flow.get('to_node_uuid', 'N/A')[:20]}...)")
                if flow.get('condition'):
                    print(f"     - Condition: {flow.get('condition')[:50]}...")
                if flow.get('label'):
                    print(f"     - Label: {flow.get('label')}")
                print()
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for v in self.test_results.values() if isinstance(v, bool) and v)
        total = sum(1 for v in self.test_results.values() if isinstance(v, bool))
        
        print(f"Tests Passed: {passed}/{total}")
        print()
        
        if self.test_results['errors']:
            print("ERRORS:")
            for error in self.test_results['errors']:
                print(f"  - {error}")
        else:
            print("✅ All tests passed successfully!")
        
        print("=" * 80)


def main():
    """Main test execution"""
    xml_file = "applicationArtifacts/Three Way Testing Files/V2/de199b3f-b072-4438-9508-3b6594827eaf.xml"
    
    if not os.path.exists(xml_file):
        print(f"❌ ERROR: XML file not found: {xml_file}")
        return 1
    
    tester = ProcessModelExtractionTester(xml_file)
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
