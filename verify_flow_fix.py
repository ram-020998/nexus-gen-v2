#!/usr/bin/env python3
"""
Simple test to verify flow storage fix
"""

from app import create_app
from models import db, ProcessModelFlow, ProcessModelNode, ProcessModelMetadata
from models import AppianObject, Package, MergeSession
from services.merge_assistant.package_service import PackageService
from services.appian_analyzer.analyzer import AppianAnalyzer
import os

def main():
    print("="*80)
    print("VERIFYING FLOW STORAGE FIX")
    print("="*80)
    
    app = create_app()
    with app.app_context():
        # Step 1: Clear old data
        print("\n1. Clearing old test data...")
        ProcessModelFlow.query.delete()
        ProcessModelNode.query.delete()
        ProcessModelMetadata.query.delete()
        AppianObject.query.delete()
        Package.query.delete()
        MergeSession.query.delete()
        db.session.commit()
        print("   ✅ Cleared")
        
        # Step 2: Create a test session
        print("\n2. Creating test session...")
        session = MergeSession(
            reference_id="TEST_001",
            base_package_name="Test Base",
            customized_package_name="Test Custom",
            new_vendor_package_name="Test Vendor"
        )
        db.session.add(session)
        db.session.commit()
        print(f"   ✅ Session created: {session.reference_id}")
        
        # Step 3: Analyze package
        zip_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip"
        if not os.path.exists(zip_path):
            print(f"   ❌ Test file not found: {zip_path}")
            return False
        
        print(f"\n3. Analyzing package: {zip_path}")
        analyzer = AppianAnalyzer(zip_path)
        blueprint_result = analyzer.analyze()
        
        pm_count = sum(1 for obj in blueprint_result['object_lookup'].values() 
                      if obj.get('object_type') == 'Process Model')
        print(f"   ✅ Found {pm_count} process models")
        
        # Step 4: Store in database (skip dependencies to avoid unrelated error)
        print(f"\n4. Storing package in database...")
        package_service = PackageService()
        
        # Create package
        package = package_service.create_package_from_blueprint(
            session_id=session.id,
            package_type='base',
            blueprint_result=blueprint_result
        )
        
        # Extract objects
        object_lookup = blueprint_result.get('object_lookup', {})
        package_service.extract_and_create_objects(package, object_lookup)
        
        # Extract process models (this is what we're testing!)
        pm_count = package_service.extract_and_create_process_models(package, object_lookup)
        
        db.session.commit()
        print(f"   ✅ Package stored: {package.id}, {pm_count} process models")
        
        # Step 5: Verify flows
        print(f"\n5. Verifying flow storage...")
        
        total_flows_expected = 0
        total_flows_actual = 0
        
        pms = ProcessModelMetadata.query.all()
        print(f"   Process models in DB: {len(pms)}")
        
        for pm in pms:
            flows_actual = ProcessModelFlow.query.filter_by(process_model_id=pm.id).count()
            total_flows_expected += pm.total_flows
            total_flows_actual += flows_actual
            
            status = "✅" if flows_actual == pm.total_flows else "❌"
            print(f"   {status} PM {pm.id}: expected {pm.total_flows} flows, got {flows_actual}")
        
        print(f"\n📊 RESULTS:")
        print(f"   Expected total flows: {total_flows_expected}")
        print(f"   Actual total flows:   {total_flows_actual}")
        
        if total_flows_actual > 0 and total_flows_actual == total_flows_expected:
            print(f"\n✅ SUCCESS! Flows are being stored correctly!")
            return True
        elif total_flows_actual > 0:
            print(f"\n⚠️  PARTIAL SUCCESS: Some flows stored but count mismatch")
            return False
        else:
            print(f"\n❌ FAILURE: No flows stored!")
            return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
