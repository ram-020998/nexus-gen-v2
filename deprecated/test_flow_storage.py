"""Test that process model flows are stored correctly after the fix."""
from app import create_app
from models import db, MergeSession, ProcessModel, ProcessModelNode, ProcessModelFlow
from core.dependency_container import DependencyContainer
from services.three_way_merge_orchestrator import ThreeWayMergeOrchestrator

app = create_app()

with app.app_context():
    # Clean up
    db.session.query(ProcessModelFlow).delete()
    db.session.query(ProcessModelNode).delete()
    db.session.query(ProcessModel).delete()
    db.session.commit()
    
    # Get orchestrator
    container = DependencyContainer.get_instance()
    orchestrator = container.get_service(ThreeWayMergeOrchestrator)
    
    # Run merge with test packages
    base_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application - Base Version.zip"
    customized_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application Customer Version.zip"
    new_vendor_path = "applicationArtifacts/Three Way Testing Files/V2/Test Application Vendor New Version.zip"
    
    print("Creating merge session...")
    session = orchestrator.create_merge_session(
        base_zip_path=base_path,
        customized_zip_path=customized_path,
        new_vendor_zip_path=new_vendor_path
    )
    
    print(f"Session created: {session.reference_id}")
    
    # Check results
    pm_count = db.session.query(ProcessModel).count()
    node_count = db.session.query(ProcessModelNode).count()
    flow_count = db.session.query(ProcessModelFlow).count()
    
    print(f"\nResults:")
    print(f"  Process Models: {pm_count}")
    print(f"  Nodes: {node_count}")
    print(f"  Flows: {flow_count}")
    
    if flow_count > 0:
        print(f"\n✓ SUCCESS: Flows are being stored!")
        
        # Show some flow details
        flows = db.session.query(ProcessModelFlow).limit(5).all()
        print(f"\nFirst {len(flows)} flows:")
        for flow in flows:
            from_node = db.session.query(ProcessModelNode).get(flow.from_node_id)
            to_node = db.session.query(ProcessModelNode).get(flow.to_node_id)
            print(f"  {from_node.node_id} -> {to_node.node_id}")
            if flow.flow_label:
                print(f"    Label: {flow.flow_label}")
    else:
        print(f"\n✗ FAILED: No flows stored")
