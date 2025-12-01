"""
Show all comparison data from the database in JSON format.
"""

import json
from app import create_app
from models import (
    db, InterfaceComparison, ProcessModelComparison, RecordTypeComparison,
    ExpressionRuleComparison, CDTComparison, ConstantComparison,
    Change, ObjectLookup
)


def serialize_comparison(obj, fields):
    """Serialize a comparison object to dict."""
    data = {'id': obj.id}
    for field in fields:
        value = getattr(obj, field, None)
        data[field] = value
    return data


def show_all_comparisons():
    """Show all comparison data."""
    app = create_app()
    
    with app.app_context():
        result = {
            'interface_comparisons': [],
            'process_model_comparisons': [],
            'record_type_comparisons': [],
            'expression_rule_comparisons': [],
            'cdt_comparisons': [],
            'constant_comparisons': []
        }
        
        # Interface Comparisons
        interface_comps = InterfaceComparison.query.all()
        for comp in interface_comps:
            change = Change.query.get(comp.change_id)
            obj = change.object if change else None
            data = {
                'id': comp.id,
                'change_id': comp.change_id,
                'object_name': obj.name if obj else None,
                'object_uuid': obj.uuid if obj else None,
                'sail_code_diff': comp.sail_code_diff,
                'parameters_added': comp.parameters_added,
                'parameters_removed': comp.parameters_removed,
                'parameters_modified': comp.parameters_modified,
                'security_changes': comp.security_changes
            }
            result['interface_comparisons'].append(data)
        
        # Process Model Comparisons
        pm_comps = ProcessModelComparison.query.all()
        for comp in pm_comps:
            change = Change.query.get(comp.change_id)
            obj = change.object if change else None
            data = {
                'id': comp.id,
                'change_id': comp.change_id,
                'object_name': obj.name if obj else None,
                'object_uuid': obj.uuid if obj else None,
                'nodes_added': comp.nodes_added,
                'nodes_removed': comp.nodes_removed,
                'nodes_modified': comp.nodes_modified,
                'flows_added': comp.flows_added,
                'flows_removed': comp.flows_removed,
                'flows_modified': comp.flows_modified,
                'variables_changed': comp.variables_changed,
                'mermaid_diagram': comp.mermaid_diagram
            }
            result['process_model_comparisons'].append(data)
        
        # Record Type Comparisons
        rt_comps = RecordTypeComparison.query.all()
        for comp in rt_comps:
            change = Change.query.get(comp.change_id)
            obj = change.object if change else None
            data = {
                'id': comp.id,
                'change_id': comp.change_id,
                'object_name': obj.name if obj else None,
                'object_uuid': obj.uuid if obj else None,
                'fields_changed': comp.fields_changed,
                'relationships_changed': comp.relationships_changed,
                'views_changed': comp.views_changed,
                'actions_changed': comp.actions_changed
            }
            result['record_type_comparisons'].append(data)
        
        # Expression Rule Comparisons
        er_comps = ExpressionRuleComparison.query.all()
        for comp in er_comps:
            obj = ObjectLookup.query.get(comp.object_id)
            data = {
                'id': comp.id,
                'session_id': comp.session_id,
                'object_id': comp.object_id,
                'object_name': obj.name if obj else None,
                'object_uuid': obj.uuid if obj else None,
                'input_changes': comp.input_changes,
                'return_type_change': comp.return_type_change,
                'logic_diff': comp.logic_diff,
                'created_at': comp.created_at.isoformat() if comp.created_at else None
            }
            result['expression_rule_comparisons'].append(data)
        
        # CDT Comparisons
        cdt_comps = CDTComparison.query.all()
        for comp in cdt_comps:
            obj = ObjectLookup.query.get(comp.object_id)
            data = {
                'id': comp.id,
                'session_id': comp.session_id,
                'object_id': comp.object_id,
                'object_name': obj.name if obj else None,
                'object_uuid': obj.uuid if obj else None,
                'field_changes': comp.field_changes,
                'namespace_change': comp.namespace_change,
                'created_at': comp.created_at.isoformat() if comp.created_at else None
            }
            result['cdt_comparisons'].append(data)
        
        # Constant Comparisons
        const_comps = ConstantComparison.query.all()
        for comp in const_comps:
            obj = ObjectLookup.query.get(comp.object_id)
            data = {
                'id': comp.id,
                'session_id': comp.session_id,
                'object_id': comp.object_id,
                'object_name': obj.name if obj else None,
                'object_uuid': obj.uuid if obj else None,
                'base_value': comp.base_value,
                'customer_value': comp.customer_value,
                'new_vendor_value': comp.new_vendor_value,
                'type_change': comp.type_change,
                'created_at': comp.created_at.isoformat() if comp.created_at else None
            }
            result['constant_comparisons'].append(data)
        
        # Summary
        summary = {
            'total_comparisons': sum([
                len(result['interface_comparisons']),
                len(result['process_model_comparisons']),
                len(result['record_type_comparisons']),
                len(result['expression_rule_comparisons']),
                len(result['cdt_comparisons']),
                len(result['constant_comparisons'])
            ]),
            'by_type': {
                'interfaces': len(result['interface_comparisons']),
                'process_models': len(result['process_model_comparisons']),
                'record_types': len(result['record_type_comparisons']),
                'expression_rules': len(result['expression_rule_comparisons']),
                'cdts': len(result['cdt_comparisons']),
                'constants': len(result['constant_comparisons'])
            }
        }
        
        result['summary'] = summary
        
        # Print formatted JSON
        print(json.dumps(result, indent=2))
        
        return result


if __name__ == '__main__':
    show_all_comparisons()
