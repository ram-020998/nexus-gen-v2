"""
Inspect actual object data to understand what's available for comparison.
"""

from app import create_app
from models import (
    db, Change, ObjectLookup, ObjectVersion, ExpressionRule, Constant,
    ProcessModel, ProcessModelNode, ProcessModelFlow
)
import json


def inspect_objects():
    """Inspect object data for comparison."""
    app = create_app()
    
    with app.app_context():
        # Get all changes
        changes = Change.query.filter_by(session_id=1).all()
        
        print("=" * 80)
        print("INSPECTING OBJECT DATA FOR ACCURATE COMPARISONS")
        print("=" * 80)
        
        for change in changes:
            obj = change.object
            print(f"\n{'=' * 80}")
            print(f"Object: {obj.name} ({obj.object_type})")
            print(f"UUID: {obj.uuid}")
            print(f"Change Classification: {change.classification}")
            print(f"Vendor Change: {change.vendor_change_type}")
            print(f"Customer Change: {change.customer_change_type}")
            print(f"{'=' * 80}")
            
            # Get versions from all three packages
            versions = ObjectVersion.query.filter_by(object_id=obj.id).all()
            
            print(f"\nFound {len(versions)} versions:")
            for v in versions:
                print(f"  Package {v.package_id}: version_uuid={v.version_uuid[:20]}...")
                
            if obj.object_type == 'Expression Rule':
                print("\n--- Expression Rule Details ---")
                for v in versions:
                    er = ExpressionRule.query.filter_by(
                        object_id=obj.id,
                        package_id=v.package_id
                    ).first()
                    if er:
                        print(f"\nPackage {v.package_id}:")
                        print(f"  Output Type: {er.output_type}")
                        print(f"  SAIL Code Length: {len(er.sail_code) if er.sail_code else 0} chars")
                        if er.sail_code:
                            print(f"  SAIL Code Preview: {er.sail_code[:200]}...")
                    else:
                        print(f"\nPackage {v.package_id}: No ExpressionRule record found")
            
            elif obj.object_type == 'Constant':
                print("\n--- Constant Details ---")
                for v in versions:
                    const = Constant.query.filter_by(
                        object_id=obj.id,
                        package_id=v.package_id
                    ).first()
                    if const:
                        print(f"\nPackage {v.package_id}:")
                        print(f"  Type: {const.constant_type}")
                        print(f"  Value: {const.constant_value}")
                        print(f"  Scope: {const.scope}")
                    else:
                        print(f"\nPackage {v.package_id}: No Constant record found")
            
            elif obj.object_type == 'Process Model':
                print("\n--- Process Model Details ---")
                for v in versions:
                    pm = ProcessModel.query.filter_by(
                        object_id=obj.id,
                        version_uuid=v.version_uuid
                    ).first()
                    if pm:
                        print(f"\nPackage {v.package_id}:")
                        
                        # Get nodes
                        nodes = ProcessModelNode.query.filter_by(
                            process_model_id=pm.id
                        ).all()
                        print(f"  Nodes: {len(nodes)}")
                        for node in nodes[:3]:  # Show first 3
                            print(f"    - {node.node_name} ({node.node_type})")
                        
                        # Get flows
                        flows = ProcessModelFlow.query.filter_by(
                            process_model_id=pm.id
                        ).all()
                        print(f"  Flows: {len(flows)}")
                        
                        # Check for SAIL code in ObjectVersion
                        if v.sail_code:
                            print(f"  SAIL Code Length: {len(v.sail_code)} chars")


if __name__ == '__main__':
    inspect_objects()
