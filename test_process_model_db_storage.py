#!/usr/bin/env python3
"""
Test Process Model Database Storage

This script tests:
1. Extraction of process model from XML
2. Storage of nodes in database
3. Storage of flows in database
4. Verification of data integrity

Usage:
    python test_process_model_db_storage.py
"""

import sys
import os
import json
from pprint import pprint

# Add services to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Flask app and models
from app import create_app
from models import db, AppianObject, ProcessModelMetadata, ProcessModelNode, ProcessModelFlow
from services.appian_analyzer.parsers import ProcessModelParser
from services.appian_analyzer.sail_formatter import SAILFormatter
import xml.etree.ElementTree as ET


class ProcessModelDBTester:
    """Test harness for process model database storage"""
    
    def __init__(self, xml_file_path: str):
        self.xml_file_path = xml_file_path
        self.app = create_app()
        self.parser = ProcessModelParser()
        self.object_lookup = {}
        self.sail_formatter = SAILFormatter(self.object_lookup)
        
        # Set dependencies
        self.parser.set_object_lookup(self.object_lookup)
        self.parser.set_sail_formatter(self.sail_formatter)
        
        self.process_model = None
        self.appian_object = None
        self.pm_metadata = None
    
    def run_all_tests(self):
        """Run all database storage tests"""
        print("=" * 80)
        print("PROCESS MODEL DATABASE STORAGE TEST")
        print("=" * 80)
        print(f"XML File: {self.xml_file_path}")
        print()
        
        with self.app.app_context():
            # Test 1: Extract Process Model
            print("Test 1: Extracting Process Model...")
            if not self.extract_process_model():
                print("❌ FAILED: Could not extract process model")
                return False
            print("✅ PASSED: Process model extracted")
            print()
            
            # Test 2: Create AppianObject
            print("Test 2: Creating AppianObject record...")
            if not self.create_appian_object():
                print("❌ FAILED: Could not create AppianObject")
                return False
            print("✅ PASSED: AppianObject created")
            print()
            
            # Test 3: Create ProcessModelMetadata
            print("Test 3: Creating ProcessModelMetadata record...")
            if not self.create_process_model_metadata():
                print("❌ FAILED: Could not create ProcessModelMetadata")
                return False
            print("✅ PASSED: ProcessModelMetadata created")
            print()
            
            # Test 4: Store Nodes
            print("Test 4: Storing nodes in database...")
            nodes_stored = self.store_nodes()
            if nodes_stored == 0:
                print("❌ FAILED: No nodes stored")
                return False
            print(f"✅ PASSED: {nodes_stored} nodes stored")
            print()
            
            # Test 5: Store Flows
            print("Test 5: Storing flows in database...")
            flows_stored = self.store_flows()
            if flows_stored == 0:
                print("❌ FAILED: No flows stored")
                return False
            print(f"✅ PASSED: {flows_stored} flows stored")
            print()
            
            # Test 6: Verify Data
            print("Test 6: Verifying stored data...")
            if not self.verify_stored_data():
                print("❌ FAILED: Data verification failed")
                return False
            print("✅ PASSED: Data verified")
            print()
            
            # Test 7: Detailed Analysis
            print("Test 7: Detailed Database Analysis...")
            self.analyze_database()
            print()
            
            # Cleanup
            print("Cleanup: Removing test data...")
            self.cleanup()
            print("✅ Test data removed")
            print()
        
        print("=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        return True
    
    def extract_process_model(self):
        """Extract process model from XML"""
        try:
            tree = ET.parse(self.xml_file_path)
            root = tree.getroot()
            self.process_model = self.parser.parse(root, self.xml_file_path)
            return self.process_model is not None
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_appian_object(self):
        """Create AppianObject record"""
        try:
            # First create a test session and package
            from models import MergeSession, Package
            
            test_session = MergeSession(
                reference_id="TEST_001",
                base_package_name="Test Base",
                customized_package_name="Test Customized",
                new_vendor_package_name="Test Vendor",
                status="in_progress"
            )
            db.session.add(test_session)
            db.session.flush()
            
            test_package = Package(
                session_id=test_session.id,
                package_name="Test Package",
                package_type="base"
            )
            db.session.add(test_package)
            db.session.flush()
            
            self.appian_object = AppianObject(
                uuid=self.process_model.uuid,
                name=self.process_model.name,
                object_type=self.process_model.object_type,
                package_id=test_package.id,
                object_metadata=json.dumps({
                    'description': self.process_model.description or "",
                    'raw_xml_length': len(self.process_model.raw_xml) if hasattr(self.process_model, 'raw_xml') else 0
                })
            )
            db.session.add(self.appian_object)
            db.session.commit()
            
            self.test_session = test_session
            self.test_package = test_package
            print(f"   AppianObject ID: {self.appian_object.id}")
            return True
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False
    
    def create_process_model_metadata(self):
        """Create ProcessModelMetadata record"""
        try:
            self.pm_metadata = ProcessModelMetadata(
                appian_object_id=self.appian_object.id,
                total_nodes=len(self.process_model.nodes) if hasattr(self.process_model, 'nodes') else 0,
                total_flows=len(self.process_model.flows) if hasattr(self.process_model, 'flows') else 0,
                complexity_score=0.0  # Can be calculated later
            )
            db.session.add(self.pm_metadata)
            db.session.commit()
            
            print(f"   ProcessModelMetadata ID: {self.pm_metadata.id}")
            print(f"   Total Nodes: {self.pm_metadata.total_nodes}")
            print(f"   Total Flows: {self.pm_metadata.total_flows}")
            return True
        except Exception as e:
            print(f"   Error: {e}")
            db.session.rollback()
            return False
    
    def store_nodes(self):
        """Store nodes in database"""
        try:
            if not hasattr(self.process_model, 'nodes') or not self.process_model.nodes:
                print("   No nodes to store")
                return 0
            
            node_count = 0
            node_id_map = {}  # Map node UUID to database ID
            
            for node in self.process_model.nodes:
                pm_node = ProcessModelNode(
                    process_model_id=self.pm_metadata.id,
                    node_id=node['uuid'],
                    node_type=node['type'],
                    node_name=node['name'],
                    properties=json.dumps(node.get('properties', {}))
                )
                db.session.add(pm_node)
                db.session.flush()  # Get the ID
                
                node_id_map[node['uuid']] = pm_node.id
                node_count += 1
            
            db.session.commit()
            
            # Store mapping for flow creation
            self.node_id_map = node_id_map
            
            print(f"   Stored {node_count} nodes")
            return node_count
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return 0
    
    def store_flows(self):
        """Store flows in database"""
        try:
            if not hasattr(self.process_model, 'flows') or not self.process_model.flows:
                print("   No flows to store")
                return 0
            
            flow_count = 0
            
            for flow in self.process_model.flows:
                from_node_uuid = flow['from_node_uuid']
                to_node_uuid = flow['to_node_uuid']
                
                # Get database IDs for nodes
                from_node_id = self.node_id_map.get(from_node_uuid)
                to_node_id = self.node_id_map.get(to_node_uuid)
                
                if not from_node_id or not to_node_id:
                    print(f"   Warning: Could not find node IDs for flow {flow.get('uuid')}")
                    continue
                
                pm_flow = ProcessModelFlow(
                    process_model_id=self.pm_metadata.id,
                    from_node_id=from_node_id,
                    to_node_id=to_node_id,
                    flow_label=flow.get('label', ''),
                    flow_condition=flow.get('condition', '')
                )
                db.session.add(pm_flow)
                flow_count += 1
            
            db.session.commit()
            
            print(f"   Stored {flow_count} flows")
            return flow_count
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return 0
    
    def verify_stored_data(self):
        """Verify data was stored correctly"""
        try:
            # Verify AppianObject
            ao = AppianObject.query.get(self.appian_object.id)
            if not ao:
                print("   Error: AppianObject not found")
                return False
            
            # Verify ProcessModelMetadata
            pm = ProcessModelMetadata.query.get(self.pm_metadata.id)
            if not pm:
                print("   Error: ProcessModelMetadata not found")
                return False
            
            # Verify Nodes
            nodes = ProcessModelNode.query.filter_by(process_model_id=pm.id).all()
            if len(nodes) != pm.total_nodes:
                print(f"   Error: Expected {pm.total_nodes} nodes, found {len(nodes)}")
                return False
            
            # Verify Flows
            flows = ProcessModelFlow.query.filter_by(process_model_id=pm.id).all()
            if len(flows) != pm.total_flows:
                print(f"   Error: Expected {pm.total_flows} flows, found {len(flows)}")
                return False
            
            print(f"   ✓ AppianObject verified")
            print(f"   ✓ ProcessModelMetadata verified")
            print(f"   ✓ {len(nodes)} nodes verified")
            print(f"   ✓ {len(flows)} flows verified")
            
            return True
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    def analyze_database(self):
        """Analyze stored database data"""
        try:
            pm = ProcessModelMetadata.query.get(self.pm_metadata.id)
            
            print(f"   Process Model: {self.appian_object.name}")
            print(f"   UUID: {self.appian_object.uuid}")
            print()
            
            # Node analysis
            print("   Node Analysis:")
            nodes = ProcessModelNode.query.filter_by(process_model_id=pm.id).all()
            node_types = {}
            for node in nodes:
                node_types[node.node_type] = node_types.get(node.node_type, 0) + 1
            
            for node_type, count in sorted(node_types.items()):
                print(f"     - {node_type}: {count}")
            print()
            
            # Flow analysis
            print("   Flow Analysis:")
            flows = ProcessModelFlow.query.filter_by(process_model_id=pm.id).all()
            conditional_flows = sum(1 for f in flows if f.flow_condition)
            print(f"     - Total flows: {len(flows)}")
            print(f"     - Conditional flows: {conditional_flows}")
            print(f"     - Unconditional flows: {len(flows) - conditional_flows}")
            print()
            
            # Sample flows
            print("   Sample Flows:")
            for i, flow in enumerate(flows[:3]):
                from_node = ProcessModelNode.query.get(flow.from_node_id)
                to_node = ProcessModelNode.query.get(flow.to_node_id)
                print(f"     Flow {i+1}:")
                print(f"       From: {from_node.node_name} ({from_node.node_type})")
                print(f"       To: {to_node.node_name} ({to_node.node_type})")
                if flow.flow_condition:
                    print(f"       Condition: {flow.flow_condition[:50]}...")
                if flow.flow_label:
                    print(f"       Label: {flow.flow_label}")
                print()
            
        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
    
    def cleanup(self):
        """Remove test data from database"""
        try:
            # Delete in correct order (flows -> nodes -> metadata -> object -> package -> session)
            if self.pm_metadata:
                ProcessModelFlow.query.filter_by(process_model_id=self.pm_metadata.id).delete()
                ProcessModelNode.query.filter_by(process_model_id=self.pm_metadata.id).delete()
                db.session.delete(self.pm_metadata)
            
            if self.appian_object:
                db.session.delete(self.appian_object)
            
            if hasattr(self, 'test_package') and self.test_package:
                db.session.delete(self.test_package)
            
            if hasattr(self, 'test_session') and self.test_session:
                from models import MergeSession
                db.session.delete(self.test_session)
            
            db.session.commit()
        except Exception as e:
            print(f"   Cleanup error: {e}")
            db.session.rollback()


def main():
    """Main test execution"""
    xml_file = "applicationArtifacts/Three Way Testing Files/V2/de199b3f-b072-4438-9508-3b6594827eaf.xml"
    
    if not os.path.exists(xml_file):
        print(f"❌ ERROR: XML file not found: {xml_file}")
        return 1
    
    tester = ProcessModelDBTester(xml_file)
    success = tester.run_all_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
