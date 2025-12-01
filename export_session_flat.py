#!/usr/bin/env python3
"""
Export Merge Session Data - Flat Structure
Shows how data is actually stored in each table for a given session.

Usage:
    python export_session_flat.py <session_reference_id>
    python export_session_flat.py MS_F033F0
"""

import sys
import json
import os
from datetime import datetime
from app import create_app
from models import (
    MergeSession, Package, ObjectLookup, PackageObjectMapping,
    DeltaComparisonResult, Change, ObjectVersion,
    Interface, InterfaceParameter, InterfaceSecurity,
    ExpressionRule, ExpressionRuleInput,
    ProcessModel, ProcessModelNode, ProcessModelFlow, ProcessModelVariable,
    RecordType, RecordTypeField, RecordTypeRelationship, 
    RecordTypeView, RecordTypeAction,
    CDT, CDTField,
    Integration, WebAPI, Site, Group, Constant, ConnectedSystem, UnknownObject,
    InterfaceComparison, ProcessModelComparison, RecordTypeComparison
)


def serialize_model(obj):
    """Convert SQLAlchemy model to dict"""
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            result[column.name] = value.isoformat()
        else:
            result[column.name] = value
    return result


def export_session_flat(reference_id):
    """Export session data showing actual table structure"""
    
    session = MergeSession.query.filter_by(reference_id=reference_id).first()
    if not session:
        return {'error': f'Session {reference_id} not found'}
    
    session_id = session.id
    
    # Get all package IDs for this session
    package_ids = [p.id for p in Package.query.filter_by(session_id=session_id).all()]
    
    # Get all object IDs involved in this session
    object_ids = set()
    for package_id in package_ids:
        mappings = PackageObjectMapping.query.filter_by(package_id=package_id).all()
        for mapping in mappings:
            object_ids.add(mapping.object_id)
    
    # Build flat export structure
    export_data = {
        'merge_sessions': [serialize_model(session)],
        'packages': [serialize_model(p) for p in Package.query.filter_by(session_id=session_id).all()],
        'object_lookup': [serialize_model(obj) for obj in ObjectLookup.query.filter(ObjectLookup.id.in_(object_ids)).all()],
        'package_object_mappings': [],
        'object_versions': [],
        'delta_comparison_results': [serialize_model(d) for d in DeltaComparisonResult.query.filter_by(session_id=session_id).all()],
        'changes': [serialize_model(c) for c in Change.query.filter_by(session_id=session_id).all()],
        
        # Object-specific tables
        'interfaces': [],
        'interface_parameters': [],
        'interface_security': [],
        'expression_rules': [],
        'expression_rule_inputs': [],
        'process_models': [],
        'process_model_nodes': [],
        'process_model_flows': [],
        'process_model_variables': [],
        'record_types': [],
        'record_type_fields': [],
        'record_type_relationships': [],
        'record_type_views': [],
        'record_type_actions': [],
        'cdts': [],
        'cdt_fields': [],
        'integrations': [],
        'web_apis': [],
        'sites': [],
        'groups': [],
        'constants': [],
        'connected_systems': [],
        'unknown_objects': [],
        
        # Comparison tables
        'interface_comparisons': [],
        'process_model_comparisons': [],
        'record_type_comparisons': []
    }
    
    # Package object mappings
    for package_id in package_ids:
        mappings = PackageObjectMapping.query.filter_by(package_id=package_id).all()
        export_data['package_object_mappings'].extend([serialize_model(m) for m in mappings])
    
    # Object versions
    for package_id in package_ids:
        versions = ObjectVersion.query.filter_by(package_id=package_id).all()
        export_data['object_versions'].extend([serialize_model(v) for v in versions])
    
    # Object-specific data
    for object_id in object_ids:
        obj = ObjectLookup.query.get(object_id)
        if not obj:
            continue
            
        object_type = obj.object_type.lower()
        
        if object_type == 'interface':
            interfaces = Interface.query.filter_by(object_id=object_id).all()
            for interface in interfaces:
                export_data['interfaces'].append(serialize_model(interface))
                params = InterfaceParameter.query.filter_by(interface_id=interface.id).all()
                export_data['interface_parameters'].extend([serialize_model(p) for p in params])
                security = InterfaceSecurity.query.filter_by(interface_id=interface.id).all()
                export_data['interface_security'].extend([serialize_model(s) for s in security])
        
        elif object_type == 'expressionrule':
            rules = ExpressionRule.query.filter_by(object_id=object_id).all()
            for rule in rules:
                export_data['expression_rules'].append(serialize_model(rule))
                inputs = ExpressionRuleInput.query.filter_by(expression_rule_id=rule.id).all()
                export_data['expression_rule_inputs'].extend([serialize_model(i) for i in inputs])
        
        elif object_type == 'processmodel':
            pms = ProcessModel.query.filter_by(object_id=object_id).all()
            for pm in pms:
                export_data['process_models'].append(serialize_model(pm))
                nodes = ProcessModelNode.query.filter_by(process_model_id=pm.id).all()
                export_data['process_model_nodes'].extend([serialize_model(n) for n in nodes])
                flows = ProcessModelFlow.query.filter_by(process_model_id=pm.id).all()
                export_data['process_model_flows'].extend([serialize_model(f) for f in flows])
                variables = ProcessModelVariable.query.filter_by(process_model_id=pm.id).all()
                export_data['process_model_variables'].extend([serialize_model(v) for v in variables])
        
        elif object_type == 'recordtype':
            rts = RecordType.query.filter_by(object_id=object_id).all()
            for rt in rts:
                export_data['record_types'].append(serialize_model(rt))
                fields = RecordTypeField.query.filter_by(record_type_id=rt.id).all()
                export_data['record_type_fields'].extend([serialize_model(f) for f in fields])
                rels = RecordTypeRelationship.query.filter_by(record_type_id=rt.id).all()
                export_data['record_type_relationships'].extend([serialize_model(r) for r in rels])
                views = RecordTypeView.query.filter_by(record_type_id=rt.id).all()
                export_data['record_type_views'].extend([serialize_model(v) for v in views])
                actions = RecordTypeAction.query.filter_by(record_type_id=rt.id).all()
                export_data['record_type_actions'].extend([serialize_model(a) for a in actions])
        
        elif object_type == 'cdt':
            cdts = CDT.query.filter_by(object_id=object_id).all()
            for cdt in cdts:
                export_data['cdts'].append(serialize_model(cdt))
                fields = CDTField.query.filter_by(cdt_id=cdt.id).all()
                export_data['cdt_fields'].extend([serialize_model(f) for f in fields])
        
        elif object_type == 'integration':
            integrations = Integration.query.filter_by(object_id=object_id).all()
            export_data['integrations'].extend([serialize_model(i) for i in integrations])
        
        elif object_type == 'webapi':
            webapis = WebAPI.query.filter_by(object_id=object_id).all()
            export_data['web_apis'].extend([serialize_model(w) for w in webapis])
        
        elif object_type == 'site':
            sites = Site.query.filter_by(object_id=object_id).all()
            export_data['sites'].extend([serialize_model(s) for s in sites])
        
        elif object_type == 'group':
            groups = Group.query.filter_by(object_id=object_id).all()
            export_data['groups'].extend([serialize_model(g) for g in groups])
        
        elif object_type == 'constant':
            constants = Constant.query.filter_by(object_id=object_id).all()
            export_data['constants'].extend([serialize_model(c) for c in constants])
        
        elif object_type == 'connectedsystem':
            css = ConnectedSystem.query.filter_by(object_id=object_id).all()
            export_data['connected_systems'].extend([serialize_model(cs) for cs in css])
        
        else:
            unknowns = UnknownObject.query.filter_by(object_id=object_id).all()
            export_data['unknown_objects'].extend([serialize_model(u) for u in unknowns])
    
    # Comparison results
    change_ids = [c.id for c in Change.query.filter_by(session_id=session_id).all()]
    for change_id in change_ids:
        ic = InterfaceComparison.query.filter_by(change_id=change_id).first()
        if ic:
            export_data['interface_comparisons'].append(serialize_model(ic))
        
        pmc = ProcessModelComparison.query.filter_by(change_id=change_id).first()
        if pmc:
            export_data['process_model_comparisons'].append(serialize_model(pmc))
        
        rtc = RecordTypeComparison.query.filter_by(change_id=change_id).first()
        if rtc:
            export_data['record_type_comparisons'].append(serialize_model(rtc))
    
    return export_data


def main():
    if len(sys.argv) < 2:
        print("Usage: python export_session_flat.py <session_reference_id>")
        print("Example: python export_session_flat.py MS_F033F0")
        sys.exit(1)
    
    reference_id = sys.argv[1]
    
    app = create_app()
    with app.app_context():
        print(f"Exporting session: {reference_id}")
        
        data = export_session_flat(reference_id)
        
        if 'error' in data:
            print(f"Error: {data['error']}")
            sys.exit(1)
        
        # Create output directory
        output_dir = 'outputs'
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f"session_flat_{reference_id}_{timestamp}.json")
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nExport completed!")
        print(f"Output: {output_file}")
        print(f"\nTable Summary:")
        for table_name, records in data.items():
            if isinstance(records, list) and len(records) > 0:
                print(f"  {table_name}: {len(records)} records")


if __name__ == '__main__':
    main()
