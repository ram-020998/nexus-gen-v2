#!/usr/bin/env python3
"""
Test script to verify flow storage fix

This script:
1. Clears existing test data
2. Creates a new merge session with test packages
3. Verifies flows are stored in database
"""

import sys
import os
from app import create_app
from models import db, MergeSession, Package, ProcessModelMetadata, ProcessModelNode, ProcessModelFlow
from services.merge_assistant.package_service import PackageService
from services.appian_analyzer.analyzer import AppianAnalyzer

def clear_test_data():
    """Clear existing test data"""
    print("🧹 Clearing existing test data...")
    app = create_app()
    with app.app_context():
        # Delete in correct order due to foreign keys
        ProcessModelFlow.query.delete()
        ProcessModelNode.query.delete()
        ProcessModelMetadata.query.delete()
        Package.query.delete()
        MergeSession.query.delete()
        db.session.commit()
        print("✅ Test data cleared")

def test_flow_storage():
    """Test that flows are stored correctly"""
    print("\n" + "="*80)
    print("TESTING FLOW STORAGE FIX")
    print("="*80)
    
    app = create_app()
    with app.app_context():
        # Create a test session
        session = MergeSession(
            session_name="Flow Storage Test",
            base_package_path="test.zip",
            customized_package_path="test.zip",
            new_vendor_package_path="test.zip"
        )
        db.session.add(session)
        db.session.flush()
        
        print(f"\n✅ Created test session: {session.id}")
        
        # Analyze a test package
        zip_path = "applicationArtifacts/Three Way Testing Files/V2.zip"
        if not os.path.exists(zip_path):
            print(f"❌ Test file not found: {zip_path}")
            return False
        
        print(f"\n📦 Analyzing package: {zip_path}")
        analyzer = AppianAnalyzer(zip_path)
        blueprint_result = analyzer.analyze()
        
        print(f"✅ Analysis complete")
        print(f"   Total objects: {len(blueprint_result['object_lookup'])}")
        
        # Count process models
        pm_count = sum(1 for obj in blueprint_result['object_lookup'].values() 
                      if obj.get('object_type') == 'Process Model')
        print(f"   Process models: {pm_count}")
        
        # Create package with all data
        print(f"\n💾 Creating package in database...")
        package_service = PackageService()
        package = package_service.create_package_with_all_data(
            session_id=session.id,
            package_type='base',
            blueprint_result=blueprint_result
        )
        
        print(f"✅ Package created: {package.id}")
        
        # Verify flows are stored
        print(f"\n🔍 Verifying flow storage...")
        
        pm_metadata_list = ProcessModelMetadata.query.filter_by(
            appian_object_id=ProcessModelMetadata.query.join(
                'appian_object'
            ).filter_by(package_id=package.id).first().id
        ).all() if ProcessModelMetadata.query.count() > 0 else []
        
        # Simpler query
        from models import AppianObject
        process_models = AppianObject.query.filter_by(
            package_id=package.id,
            object_type='Process Model'
        ).all()
        
        print(f"   Process models in DB: {len(process_models)}")
        
        total_nodes = 0
        total_flows = 0
        
        for pm_obj in process_models:
            pm_meta = ProcessModelMetadata.query.filter_by(
                appian_object_id=pm_obj.id
            ).first()
            
            if pm_meta:
                nodes = ProcessModelNode.query.filter_by(
                    process_model_id=pm_meta.id
                ).count()
                
                flows = ProcessModelFlow.query.filter_by(
                    process_model_id=pm_meta.id
                ).count()
                
                total_nodes += nodes
                total_flows += flows
                
                print(f"\n   Process Model: {pm_obj.name}")
                print(f"      Metadata: nodes={pm_meta.total_nodes}, flows={pm_meta.total_flows}")
                print(f"      Actual DB: nodes={nodes}, flows={flows}")
                
                if flows == 0 and pm_meta.total_flows > 0:
                    print(f"      ❌ PROBLEM: Expected {pm_meta.total_flows} flows but found 0!")
                elif flows == pm_meta.total_flows:
                    print(f"      ✅ Flow count matches!")
        
        print(f"\n📊 Summary:")
        print(f"   Total nodes in DB: {total_nodes}")
        print(f"   Total flows in DB: {total_flows}")
        
        if total_flows > 0:
            print(f"\n✅ SUCCESS: Flows are being stored!")
            return True
        else:
            print(f"\n❌ FAILURE: No flows stored in database")
            return False

if __name__ == "__main__":
    clear_test_data()
    success = test_flow_storage()
    sys.exit(0 if success else 1)
