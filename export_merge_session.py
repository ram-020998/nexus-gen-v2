#!/usr/bin/env python3
"""
Export Merge Session Data
Exports all merge assistant related data for a given session in nested JSON format.

Usage:
    python export_merge_session.py <session_reference_id>
    python export_merge_session.py MS_000001
"""

import sys
import json
import os
from datetime import datetime
from app import create_app
from models import (
    db, MergeSession, Package, ObjectLookup, PackageObjectMapping,
    DeltaComparisonResult, Change, ObjectVersion,
    Interface, InterfaceParameter, InterfaceSecurity,
    ExpressionRule, ExpressionRuleInput,
    ProcessModel, ProcessModelNode, ProcessModelFlow, ProcessModelVariable,
    RecordType, RecordTypeField, RecordTypeRelationship, RecordTypeView, RecordTypeAction,
    CDT, CDTField,
    Integration, WebAPI, Site, Group, Constant, ConnectedSystem, UnknownObject,
    InterfaceComparison, ProcessModelComparison, RecordTypeComparison
)


def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def export_interface_details(interface_id, package_id=None):
    """
    Export interface with parameters and security.
    
    Args:
        interface_id: Interface ID (optional if using package_id)
        package_id: Package ID to filter by (optional)
    
    Returns:
        Interface data dict or None if not found
    """
    interface = Interface.query.get(interface_id)
    if not interface:
        return None
    
    return {
        'id': interface.id,
        'object_id': interface.object_id,
        'package_id': interface.package_id,
        'uuid': interface.uuid,
        'name': interface.name,
        'version_uuid': interface.version_uuid,
        'description': interface.description,
        'created_at': interface.created_at.isoformat(),
        'parameters': [
            {
                'id': p.id,
                'parameter_name': p.parameter_name,
                'parameter_type': p.parameter_type,
                'is_required': p.is_required,
                'default_value': p.default_value,
                'display_order': p.display_order
            }
            for p in interface.parameters.all()
        ],
        'security': [
            {
                'id': s.id,
                'role_name': s.role_name,
                'permission_type': s.permission_type
            }
            for s in interface.security.all()
        ]
    }


def export_expression_rule_details(rule_id, package_id=None):
    """
    Export expression rule with inputs.
    
    Args:
        rule_id: Expression rule ID (optional if using package_id)
        package_id: Package ID to filter by (optional)
    
    Returns:
        Expression rule data dict or None if not found
    """
    rule = ExpressionRule.query.get(rule_id)
    if not rule:
        return None
    
    return {
        'id': rule.id,
        'object_id': rule.object_id,
        'package_id': rule.package_id,
        'uuid': rule.uuid,
        'name': rule.name,
        'version_uuid': rule.version_uuid,
        'output_type': rule.output_type,
        'description': rule.description,
        'created_at': rule.created_at.isoformat(),
        'inputs': [
            {
                'id': i.id,
                'input_name': i.input_name,
                'input_type': i.input_type,
                'is_required': i.is_required,
                'default_value': i.default_value,
                'display_order': i.display_order
            }
            for i in rule.inputs.all()
        ]
    }


def export_process_model_details(pm_id, package_id=None):
    """
    Export process model with nodes, flows, and variables.
    
    Args:
        pm_id: Process model ID (optional if using package_id)
        package_id: Package ID to filter by (optional)
    
    Returns:
        Process model data dict or None if not found
    """
    pm = ProcessModel.query.get(pm_id)
    if not pm:
        return None
    
    return {
        'id': pm.id,
        'object_id': pm.object_id,
        'package_id': pm.package_id,
        'uuid': pm.uuid,
        'name': pm.name,
        'version_uuid': pm.version_uuid,
        'description': pm.description,
        'total_nodes': pm.total_nodes,
        'total_flows': pm.total_flows,
        'complexity_score': pm.complexity_score,
        'created_at': pm.created_at.isoformat(),
        'nodes': [
            {
                'id': n.id,
                'node_id': n.node_id,
                'node_type': n.node_type,
                'node_name': n.node_name,
                'properties': n.properties,
                'created_at': n.created_at.isoformat()
            }
            for n in pm.nodes.all()
        ],
        'flows': [
            {
                'id': f.id,
                'from_node_id': f.from_node_id,
                'to_node_id': f.to_node_id,
                'flow_label': f.flow_label,
                'flow_condition': f.flow_condition,
                'created_at': f.created_at.isoformat()
            }
            for f in pm.flows.all()
        ],
        'variables': [
            {
                'id': v.id,
                'variable_name': v.variable_name,
                'variable_type': v.variable_type,
                'is_parameter': v.is_parameter,
                'default_value': v.default_value
            }
            for v in pm.variables.all()
        ]
    }


def export_record_type_details(rt_id, package_id=None):
    """
    Export record type with fields, relationships, views, and actions.
    
    Args:
        rt_id: Record type ID (optional if using package_id)
        package_id: Package ID to filter by (optional)
    
    Returns:
        Record type data dict or None if not found
    """
    rt = RecordType.query.get(rt_id)
    if not rt:
        return None
    
    return {
        'id': rt.id,
        'object_id': rt.object_id,
        'package_id': rt.package_id,
        'uuid': rt.uuid,
        'name': rt.name,
        'version_uuid': rt.version_uuid,
        'description': rt.description,
        'source_type': rt.source_type,
        'created_at': rt.created_at.isoformat(),
        'fields': [
            {
                'id': f.id,
                'field_name': f.field_name,
                'field_type': f.field_type,
                'is_primary_key': f.is_primary_key,
                'is_required': f.is_required,
                'display_order': f.display_order
            }
            for f in rt.fields.all()
        ],
        'relationships': [
            {
                'id': r.id,
                'relationship_name': r.relationship_name,
                'related_record_uuid': r.related_record_uuid,
                'relationship_type': r.relationship_type
            }
            for r in rt.relationships.all()
        ],
        'views': [
            {
                'id': v.id,
                'view_name': v.view_name,
                'view_type': v.view_type,
                'configuration': v.configuration
            }
            for v in rt.views.all()
        ],
        'actions': [
            {
                'id': a.id,
                'action_name': a.action_name,
                'action_type': a.action_type,
                'configuration': a.configuration
            }
            for a in rt.actions.all()
        ]
    }


def export_cdt_details(cdt_id, package_id=None):
    """
    Export CDT with fields.
    
    Args:
        cdt_id: CDT ID (optional if using package_id)
        package_id: Package ID to filter by (optional)
    
    Returns:
        CDT data dict or None if not found
    """
    cdt = CDT.query.get(cdt_id)
    if not cdt:
        return None
    
    return {
        'id': cdt.id,
        'object_id': cdt.object_id,
        'package_id': cdt.package_id,
        'uuid': cdt.uuid,
        'name': cdt.name,
        'version_uuid': cdt.version_uuid,
        'namespace': cdt.namespace,
        'description': cdt.description,
        'created_at': cdt.created_at.isoformat(),
        'fields': [
            {
                'id': f.id,
                'field_name': f.field_name,
                'field_type': f.field_type,
                'is_list': f.is_list,
                'is_required': f.is_required,
                'display_order': f.display_order
            }
            for f in cdt.fields.all()
        ]
    }


def export_object_specific_data(object_lookup, package_id=None):
    """
    Export object-specific data based on object type.
    
    Args:
        object_lookup: ObjectLookup instance
        package_id: Optional package ID to filter by specific version
    
    Returns:
        Object-specific data dict or list of dicts (if package_id not provided)
    """
    object_type = object_lookup.object_type.lower()
    object_id = object_lookup.id
    
    # Query the appropriate table based on object type
    if object_type == 'interface':
        if package_id:
            # Get specific package version
            interface = Interface.query.filter_by(object_id=object_id, package_id=package_id).first()
            return export_interface_details(interface.id, package_id) if interface else None
        else:
            # Get all versions
            interfaces = Interface.query.filter_by(object_id=object_id).all()
            return [export_interface_details(i.id) for i in interfaces] if interfaces else None
    
    elif object_type == 'expressionrule':
        if package_id:
            rule = ExpressionRule.query.filter_by(object_id=object_id, package_id=package_id).first()
            return export_expression_rule_details(rule.id, package_id) if rule else None
        else:
            rules = ExpressionRule.query.filter_by(object_id=object_id).all()
            return [export_expression_rule_details(r.id) for r in rules] if rules else None
    
    elif object_type == 'processmodel':
        if package_id:
            pm = ProcessModel.query.filter_by(object_id=object_id, package_id=package_id).first()
            return export_process_model_details(pm.id, package_id) if pm else None
        else:
            pms = ProcessModel.query.filter_by(object_id=object_id).all()
            return [export_process_model_details(pm.id) for pm in pms] if pms else None
    
    elif object_type == 'recordtype':
        if package_id:
            rt = RecordType.query.filter_by(object_id=object_id, package_id=package_id).first()
            return export_record_type_details(rt.id, package_id) if rt else None
        else:
            rts = RecordType.query.filter_by(object_id=object_id).all()
            return [export_record_type_details(rt.id) for rt in rts] if rts else None
    
    elif object_type == 'cdt':
        if package_id:
            cdt = CDT.query.filter_by(object_id=object_id, package_id=package_id).first()
            return export_cdt_details(cdt.id, package_id) if cdt else None
        else:
            cdts = CDT.query.filter_by(object_id=object_id).all()
            return [export_cdt_details(cdt.id) for cdt in cdts] if cdts else None
    
    elif object_type == 'integration':
        if package_id:
            integration = Integration.query.filter_by(object_id=object_id, package_id=package_id).first()
            if integration:
                return {
                    'id': integration.id,
                    'object_id': integration.object_id,
                    'package_id': integration.package_id,
                    'uuid': integration.uuid,
                    'name': integration.name,
                    'version_uuid': integration.version_uuid,
                    'connection_info': integration.connection_info,
                    'authentication_info': integration.authentication_info,
                    'endpoint': integration.endpoint,
                    'description': integration.description,
                    'created_at': integration.created_at.isoformat()
                }
        else:
            integrations = Integration.query.filter_by(object_id=object_id).all()
            return [{
                'id': integration.id,
                'object_id': integration.object_id,
                'package_id': integration.package_id,
                'uuid': integration.uuid,
                'name': integration.name,
                'version_uuid': integration.version_uuid,
                'connection_info': integration.connection_info,
                'authentication_info': integration.authentication_info,
                'endpoint': integration.endpoint,
                'description': integration.description,
                'created_at': integration.created_at.isoformat()
            } for integration in integrations] if integrations else None
    
    elif object_type == 'webapi':
        if package_id:
            webapi = WebAPI.query.filter_by(object_id=object_id, package_id=package_id).first()
            if webapi:
                return {
                    'id': webapi.id,
                    'object_id': webapi.object_id,
                    'package_id': webapi.package_id,
                    'uuid': webapi.uuid,
                    'name': webapi.name,
                    'version_uuid': webapi.version_uuid,
                    'endpoint': webapi.endpoint,
                    'http_methods': webapi.http_methods,
                    'description': webapi.description,
                    'created_at': webapi.created_at.isoformat()
                }
        else:
            webapis = WebAPI.query.filter_by(object_id=object_id).all()
            return [{
                'id': webapi.id,
                'object_id': webapi.object_id,
                'package_id': webapi.package_id,
                'uuid': webapi.uuid,
                'name': webapi.name,
                'version_uuid': webapi.version_uuid,
                'endpoint': webapi.endpoint,
                'http_methods': webapi.http_methods,
                'description': webapi.description,
                'created_at': webapi.created_at.isoformat()
            } for webapi in webapis] if webapis else None
    
    elif object_type == 'site':
        if package_id:
            site = Site.query.filter_by(object_id=object_id, package_id=package_id).first()
            if site:
                return {
                    'id': site.id,
                    'object_id': site.object_id,
                    'package_id': site.package_id,
                    'uuid': site.uuid,
                    'name': site.name,
                    'version_uuid': site.version_uuid,
                    'page_hierarchy': site.page_hierarchy,
                    'description': site.description,
                    'created_at': site.created_at.isoformat()
                }
        else:
            sites = Site.query.filter_by(object_id=object_id).all()
            return [{
                'id': site.id,
                'object_id': site.object_id,
                'package_id': site.package_id,
                'uuid': site.uuid,
                'name': site.name,
                'version_uuid': site.version_uuid,
                'page_hierarchy': site.page_hierarchy,
                'description': site.description,
                'created_at': site.created_at.isoformat()
            } for site in sites] if sites else None
    
    elif object_type == 'group':
        if package_id:
            group = Group.query.filter_by(object_id=object_id, package_id=package_id).first()
            if group:
                return {
                    'id': group.id,
                    'object_id': group.object_id,
                    'package_id': group.package_id,
                    'uuid': group.uuid,
                    'name': group.name,
                    'version_uuid': group.version_uuid,
                    'members': group.members,
                    'parent_group_uuid': group.parent_group_uuid,
                    'description': group.description,
                    'created_at': group.created_at.isoformat()
                }
        else:
            groups = Group.query.filter_by(object_id=object_id).all()
            return [{
                'id': group.id,
                'object_id': group.object_id,
                'package_id': group.package_id,
                'uuid': group.uuid,
                'name': group.name,
                'version_uuid': group.version_uuid,
                'members': group.members,
                'parent_group_uuid': group.parent_group_uuid,
                'description': group.description,
                'created_at': group.created_at.isoformat()
            } for group in groups] if groups else None
    
    elif object_type == 'constant':
        if package_id:
            constant = Constant.query.filter_by(object_id=object_id, package_id=package_id).first()
            if constant:
                return {
                    'id': constant.id,
                    'object_id': constant.object_id,
                    'package_id': constant.package_id,
                    'uuid': constant.uuid,
                    'name': constant.name,
                    'version_uuid': constant.version_uuid,
                    'constant_value': constant.constant_value,
                    'constant_type': constant.constant_type,
                    'scope': constant.scope,
                    'description': constant.description,
                    'created_at': constant.created_at.isoformat()
                }
        else:
            constants = Constant.query.filter_by(object_id=object_id).all()
            return [{
                'id': constant.id,
                'object_id': constant.object_id,
                'package_id': constant.package_id,
                'uuid': constant.uuid,
                'name': constant.name,
                'version_uuid': constant.version_uuid,
                'constant_value': constant.constant_value,
                'constant_type': constant.constant_type,
                'scope': constant.scope,
                'description': constant.description,
                'created_at': constant.created_at.isoformat()
            } for constant in constants] if constants else None
    
    elif object_type == 'connectedsystem':
        if package_id:
            cs = ConnectedSystem.query.filter_by(object_id=object_id, package_id=package_id).first()
            if cs:
                return {
                    'id': cs.id,
                    'object_id': cs.object_id,
                    'package_id': cs.package_id,
                    'uuid': cs.uuid,
                    'name': cs.name,
                    'version_uuid': cs.version_uuid,
                    'system_type': cs.system_type,
                    'properties': cs.properties,
                    'description': cs.description,
                    'created_at': cs.created_at.isoformat()
                }
        else:
            css = ConnectedSystem.query.filter_by(object_id=object_id).all()
            return [{
                'id': cs.id,
                'object_id': cs.object_id,
                'package_id': cs.package_id,
                'uuid': cs.uuid,
                'name': cs.name,
                'version_uuid': cs.version_uuid,
                'system_type': cs.system_type,
                'properties': cs.properties,
                'description': cs.description,
                'created_at': cs.created_at.isoformat()
            } for cs in css] if css else None
    
    else:  # unknown object
        if package_id:
            unknown = UnknownObject.query.filter_by(object_id=object_id, package_id=package_id).first()
            if unknown:
                return {
                    'id': unknown.id,
                    'object_id': unknown.object_id,
                    'package_id': unknown.package_id,
                    'uuid': unknown.uuid,
                    'name': unknown.name,
                    'version_uuid': unknown.version_uuid,
                    'raw_xml': unknown.raw_xml,
                    'description': unknown.description,
                    'created_at': unknown.created_at.isoformat()
                }
        else:
            unknowns = UnknownObject.query.filter_by(object_id=object_id).all()
            return [{
                'id': unknown.id,
                'object_id': unknown.object_id,
                'package_id': unknown.package_id,
                'uuid': unknown.uuid,
                'name': unknown.name,
                'version_uuid': unknown.version_uuid,
                'raw_xml': unknown.raw_xml,
                'description': unknown.description,
                'created_at': unknown.created_at.isoformat()
            } for unknown in unknowns] if unknowns else None
    
    return None


def export_merge_session(reference_id):
    """Export complete merge session data in nested JSON format"""
    
    # Get the merge session
    session = MergeSession.query.filter_by(reference_id=reference_id).first()
    if not session:
        return {'error': f'Session {reference_id} not found'}
    
    # Build the nested structure
    session_data = {
        'session': {
            'id': session.id,
            'reference_id': session.reference_id,
            'status': session.status,
            'total_changes': session.total_changes,
            'reviewed_count': session.reviewed_count,
            'skipped_count': session.skipped_count,
            'estimated_complexity': session.estimated_complexity,
            'estimated_time_hours': session.estimated_time_hours,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat()
        },
        'packages': [],
        'objects': [],
        'delta_comparison_results': [],
        'changes': []
    }
    
    # Export packages with their mappings and versions
    for package in session.packages.all():
        package_data = {
            'id': package.id,
            'package_type': package.package_type,
            'filename': package.filename,
            'total_objects': package.total_objects,
            'created_at': package.created_at.isoformat(),
            'object_mappings': [],
            'object_versions': []
        }
        
        # Get object mappings for this package
        for mapping in package.object_mappings.all():
            package_data['object_mappings'].append({
                'id': mapping.id,
                'object_id': mapping.object_id,
                'created_at': mapping.created_at.isoformat()
            })
        
        # Get object versions for this package
        for version in package.object_versions.all():
            package_data['object_versions'].append({
                'id': version.id,
                'object_id': version.object_id,
                'version_uuid': version.version_uuid,
                'sail_code': version.sail_code,
                'fields': version.fields,
                'properties': version.properties,
                'raw_xml': version.raw_xml,
                'created_at': version.created_at.isoformat()
            })
        
        session_data['packages'].append(package_data)
    
    # Get all unique objects involved in this session
    # Objects are linked through package_object_mappings
    package_ids = [p.id for p in session.packages.all()]
    object_ids = set()
    
    for package_id in package_ids:
        mappings = PackageObjectMapping.query.filter_by(package_id=package_id).all()
        for mapping in mappings:
            object_ids.add(mapping.object_id)
    
    # Export object lookup data with object-specific details
    for object_id in object_ids:
        obj = ObjectLookup.query.get(object_id)
        if obj:
            object_data = {
                'id': obj.id,
                'uuid': obj.uuid,
                'name': obj.name,
                'object_type': obj.object_type,
                'description': obj.description,
                'created_at': obj.created_at.isoformat(),
                'object_specific_data': export_object_specific_data(obj)
            }
            session_data['objects'].append(object_data)
    
    # Export delta comparison results
    for delta in session.delta_results.all():
        session_data['delta_comparison_results'].append({
            'id': delta.id,
            'object_id': delta.object_id,
            'change_category': delta.change_category,
            'change_type': delta.change_type,
            'version_changed': delta.version_changed,
            'content_changed': delta.content_changed,
            'created_at': delta.created_at.isoformat()
        })
    
    # Export changes (working set) with comparison details
    for change in session.changes.all():
        change_data = {
            'id': change.id,
            'object_id': change.object_id,
            'classification': change.classification,
            'change_type': change.change_type,
            'vendor_change_type': change.vendor_change_type,
            'customer_change_type': change.customer_change_type,
            'display_order': change.display_order,
            'status': change.status,
            'notes': change.notes,
            'reviewed_at': change.reviewed_at.isoformat() if change.reviewed_at else None,
            'reviewed_by': change.reviewed_by,
            'created_at': change.created_at.isoformat(),
            'comparison_details': {}
        }
        
        # Add object-specific comparison details
        interface_comp = InterfaceComparison.query.filter_by(change_id=change.id).first()
        if interface_comp:
            change_data['comparison_details']['interface'] = {
                'id': interface_comp.id,
                'sail_code_diff': interface_comp.sail_code_diff,
                'parameters_added': interface_comp.parameters_added,
                'parameters_removed': interface_comp.parameters_removed,
                'parameters_modified': interface_comp.parameters_modified,
                'security_changes': interface_comp.security_changes
            }
        
        pm_comp = ProcessModelComparison.query.filter_by(change_id=change.id).first()
        if pm_comp:
            change_data['comparison_details']['process_model'] = {
                'id': pm_comp.id,
                'nodes_added': pm_comp.nodes_added,
                'nodes_removed': pm_comp.nodes_removed,
                'nodes_modified': pm_comp.nodes_modified,
                'flows_added': pm_comp.flows_added,
                'flows_removed': pm_comp.flows_removed,
                'flows_modified': pm_comp.flows_modified,
                'variables_changed': pm_comp.variables_changed,
                'mermaid_diagram': pm_comp.mermaid_diagram
            }
        
        rt_comp = RecordTypeComparison.query.filter_by(change_id=change.id).first()
        if rt_comp:
            change_data['comparison_details']['record_type'] = {
                'id': rt_comp.id,
                'fields_changed': rt_comp.fields_changed,
                'relationships_changed': rt_comp.relationships_changed,
                'views_changed': rt_comp.views_changed,
                'actions_changed': rt_comp.actions_changed
            }
        
        session_data['changes'].append(change_data)
    
    return session_data


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python export_merge_session.py <session_reference_id>")
        print("Example: python export_merge_session.py MS_000001")
        sys.exit(1)
    
    reference_id = sys.argv[1]
    
    # Create Flask app context
    app = create_app()
    with app.app_context():
        print(f"Exporting merge session: {reference_id}")
        
        # Export the session data
        data = export_merge_session(reference_id)
        
        if 'error' in data:
            print(f"Error: {data['error']}")
            sys.exit(1)
        
        # Ensure outputs folder exists
        output_dir = 'outputs'
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        output_file = os.path.join(output_dir, f"merge_session_{reference_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=serialize_datetime)
        
        print(f"\nExport completed successfully!")
        print(f"Output file: {output_file}")
        print(f"\nSummary:")
        print(f"  - Session: {data['session']['reference_id']}")
        print(f"  - Status: {data['session']['status']}")
        print(f"  - Packages: {len(data['packages'])}")
        print(f"  - Objects: {len(data['objects'])}")
        print(f"  - Delta Results: {len(data['delta_comparison_results'])}")
        print(f"  - Changes: {len(data['changes'])}")
        print(f"  - Total Changes: {data['session']['total_changes']}")
        print(f"  - Reviewed: {data['session']['reviewed_count']}")
        print(f"  - Skipped: {data['session']['skipped_count']}")


if __name__ == '__main__':
    main()

# Method 1: Direct execution (since it's already executable)
# ./export_merge_session.py MS_000001

# Method 2: Using python explicitly
# python export_merge_session.py MS_F033F0
