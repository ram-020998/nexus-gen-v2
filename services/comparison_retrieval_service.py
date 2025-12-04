"""
Comparison Retrieval Service

Retrieves detailed object comparison data for display in the merge workflow UI.
This service fetches comparison results from comparison tables and formats them
for presentation with proper highlighting of differences.
"""

import logging
from typing import Dict, Any, Optional, List

from core.base_service import BaseService
from models import (
    db, ObjectVersion, Change,
    Interface, InterfaceParameter,
    ProcessModel, ProcessModelNode, ProcessModelFlow, ProcessModelVariable,
    ExpressionRule, ExpressionRuleInput,
    RecordType, RecordTypeField, RecordTypeRelationship,
    RecordTypeView, RecordTypeAction,
    CDT, CDTField,
    Constant, Group, ConnectedSystem, Integration, WebAPI, Site
)


class ComparisonRetrievalService(BaseService):
    """
    Service for retrieving detailed object comparison data.
    
    This service:
    1. Fetches comparison data from comparison tables
    2. Retrieves version-specific object details
    3. Formats data for UI display with highlighting
    4. Handles all supported object types
    """
    
    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)
    
    def get_comparison_details(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """
        Get detailed comparison data for a change.
        
        Args:
            change: Change entity
            base_package_id: Package A (Base) ID
            customer_package_id: Package B (Customer) ID
            new_vendor_package_id: Package C (New Vendor) ID
            
        Returns:
            Dict with comparison details specific to object type
        """
        obj = change.object
        object_type = obj.object_type
        
        self.logger.debug(
            f"Getting comparison details for {object_type}: {obj.name}"
        )
        
        # Route to appropriate handler based on object type
        handlers = {
            'Constant': self._get_constant_comparison,
            'Expression Rule': self._get_expression_rule_comparison,
            'Interface': self._get_interface_comparison,
            'Process Model': self._get_process_model_comparison,
            'CDT': self._get_cdt_comparison,
            'Record Type': self._get_record_type_comparison,
            'Group': self._get_group_comparison,
            'Connected System': self._get_connected_system_comparison,
            'Integration': self._get_integration_comparison,
            'Web API': self._get_web_api_comparison,
            'Site': self._get_site_comparison
        }
        
        handler = handlers.get(object_type)
        if handler:
            return handler(
                change,
                base_package_id,
                customer_package_id,
                new_vendor_package_id
            )
        
        # Default: return basic version info
        return self._get_basic_comparison(
            change,
            base_package_id,
            customer_package_id,
            new_vendor_package_id
        )
    
    def _get_constant_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Get constant comparison details."""
        obj_id = change.object_id
        
        # For NO_CONFLICT: compare base vs vendor
        # For CONFLICT: compare vendor vs customer
        # "vendor" field = new vendor package (C)
        # "customer" field = base package (A) for NO_CONFLICT, customer package (B) for CONFLICT
        compare_package_id = base_package_id if change.classification == 'NO_CONFLICT' else customer_package_id
        
        # Get constants from packages
        vendor_constant = self._get_constant(obj_id, new_vendor_package_id)
        compare_constant = self._get_constant(obj_id, compare_package_id)
        
        return {
            'object_type': 'Constant',
            'vendor': {
                'type': vendor_constant.constant_type if vendor_constant else None,
                'value': vendor_constant.constant_value if vendor_constant else None
            },
            'customer': {
                'type': compare_constant.constant_type if compare_constant else None,
                'value': compare_constant.constant_value if compare_constant else None
            },
            'has_changes': (
                vendor_constant and compare_constant and
                (vendor_constant.constant_value != compare_constant.constant_value or
                 vendor_constant.constant_type != compare_constant.constant_type)
            )
        }
    
    def _get_expression_rule_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Get expression rule comparison details."""
        obj_id = change.object_id
        
        # For NO_CONFLICT: compare base vs vendor
        # For CONFLICT: compare vendor vs customer
        compare_package_id = base_package_id if change.classification == 'NO_CONFLICT' else customer_package_id
        
        # Get expression rules
        vendor_er = self._get_expression_rule(obj_id, new_vendor_package_id)
        compare_er = self._get_expression_rule(obj_id, compare_package_id)
        
        # Get inputs
        vendor_inputs = self._get_expression_rule_inputs(vendor_er.id) if vendor_er else []
        compare_inputs = self._get_expression_rule_inputs(compare_er.id) if compare_er else []
        
        # Generate SAIL code diff
        from services.sail_diff_service import SailDiffService
        diff_service = SailDiffService()
        
        old_code = compare_er.sail_code if compare_er else None
        new_code = vendor_er.sail_code if vendor_er else None
        
        # Use appropriate labels based on classification
        old_label = 'Vendor Base' if change.classification == 'NO_CONFLICT' else 'Customer'
        
        diff_hunks = diff_service.generate_unified_diff(
            old_code,
            new_code,
            old_label=old_label,
            new_label='Vendor Latest'
        )
        
        diff_stats = diff_service.get_change_stats(old_code, new_code)
        
        return {
            'object_type': 'Expression Rule',
            'vendor': {
                'sail_code': vendor_er.sail_code if vendor_er else None,
                'inputs': vendor_inputs,
                'output_type': vendor_er.output_type if vendor_er else None
            },
            'customer': {
                'sail_code': compare_er.sail_code if compare_er else None,
                'inputs': compare_inputs,
                'output_type': compare_er.output_type if compare_er else None
            },
            'diff_hunks': diff_hunks,
            'diff_stats': diff_stats,
            'has_changes': vendor_er and compare_er and (
                vendor_er.sail_code != compare_er.sail_code or
                vendor_inputs != compare_inputs
            )
        }
    
    def _get_interface_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Get interface comparison details."""
        obj_id = change.object_id
        
        # For NO_CONFLICT: compare base vs vendor
        # For CONFLICT: compare vendor vs customer
        compare_package_id = base_package_id if change.classification == 'NO_CONFLICT' else customer_package_id
        
        # Get interfaces
        vendor_interface = self._get_interface(obj_id, new_vendor_package_id)
        compare_interface = self._get_interface(obj_id, compare_package_id)
        
        # Get parameters
        vendor_params = self._get_interface_parameters(vendor_interface.id) if vendor_interface else []
        compare_params = self._get_interface_parameters(compare_interface.id) if compare_interface else []
        
        # Get SAIL code from object_versions
        vendor_version = self._get_object_version(obj_id, new_vendor_package_id)
        compare_version = self._get_object_version(obj_id, compare_package_id)
        
        # Generate SAIL code diff
        from services.sail_diff_service import SailDiffService
        diff_service = SailDiffService()
        
        old_code = compare_version.sail_code if compare_version else None
        new_code = vendor_version.sail_code if vendor_version else None
        
        # Use appropriate labels based on classification
        old_label = 'Vendor Base' if change.classification == 'NO_CONFLICT' else 'Customer'
        
        diff_hunks = diff_service.generate_unified_diff(
            old_code,
            new_code,
            old_label=old_label,
            new_label='Vendor Latest'
        )
        
        diff_stats = diff_service.get_change_stats(old_code, new_code)
        
        return {
            'object_type': 'Interface',
            'vendor': {
                'sail_code': vendor_version.sail_code if vendor_version else None,
                'parameters': vendor_params
            },
            'customer': {
                'sail_code': compare_version.sail_code if compare_version else None,
                'parameters': compare_params
            },
            'diff_hunks': diff_hunks,
            'diff_stats': diff_stats,
            'has_changes': vendor_version and compare_version and (
                vendor_version.sail_code != compare_version.sail_code or
                vendor_params != compare_params
            )
        }
    
    def _get_process_model_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Get process model comparison details."""
        obj_id = change.object_id
        
        # For NO_CONFLICT: compare base vs vendor
        # For CONFLICT: compare vendor vs customer
        compare_package_id = base_package_id if change.classification == 'NO_CONFLICT' else customer_package_id
        
        # Get process models
        vendor_pm = self._get_process_model(obj_id, new_vendor_package_id)
        compare_pm = self._get_process_model(obj_id, compare_package_id)
        
        # Get nodes
        vendor_nodes = self._get_process_model_nodes(vendor_pm.id) if vendor_pm else []
        compare_nodes = self._get_process_model_nodes(compare_pm.id) if compare_pm else []
        
        # Get flows
        vendor_flows = self._get_process_model_flows(vendor_pm.id) if vendor_pm else []
        compare_flows = self._get_process_model_flows(compare_pm.id) if compare_pm else []
        
        # Get variables
        vendor_variables = self._get_process_model_variables(vendor_pm.id) if vendor_pm else []
        compare_variables = self._get_process_model_variables(compare_pm.id) if compare_pm else []
        
        # Generate Mermaid diagrams with color coding
        vendor_mermaid = self._generate_mermaid_diagram_with_diff(
            vendor_nodes, vendor_flows, compare_nodes, is_vendor=True
        )
        compare_mermaid = self._generate_mermaid_diagram_with_diff(
            compare_nodes, compare_flows, vendor_nodes, is_vendor=False
        )
        
        return {
            'object_type': 'Process Model',
            'vendor': {
                'nodes': vendor_nodes,
                'flows': vendor_flows,
                'variables': vendor_variables,
                'mermaid_diagram': vendor_mermaid
            },
            'customer': {
                'nodes': compare_nodes,
                'flows': compare_flows,
                'variables': compare_variables,
                'mermaid_diagram': compare_mermaid
            },
            'has_changes': vendor_nodes != compare_nodes or vendor_flows != compare_flows or vendor_variables != compare_variables
        }
    
    def _get_cdt_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Get CDT comparison details."""
        obj_id = change.object_id
        
        # For NO_CONFLICT: compare base vs vendor
        # For CONFLICT: compare vendor vs customer
        compare_package_id = base_package_id if change.classification == 'NO_CONFLICT' else customer_package_id
        
        # Get CDTs
        vendor_cdt = self._get_cdt(obj_id, new_vendor_package_id)
        compare_cdt = self._get_cdt(obj_id, compare_package_id)
        
        # Get fields
        vendor_fields = self._get_cdt_fields(vendor_cdt.id) if vendor_cdt else []
        compare_fields = self._get_cdt_fields(compare_cdt.id) if compare_cdt else []
        
        return {
            'object_type': 'CDT',
            'vendor': {
                'fields': vendor_fields,
                'namespace': vendor_cdt.namespace if vendor_cdt else None
            },
            'customer': {
                'fields': compare_fields,
                'namespace': compare_cdt.namespace if compare_cdt else None
            },
            'has_changes': vendor_fields != compare_fields
        }
    
    def _get_record_type_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Get record type comparison details."""
        obj_id = change.object_id
        
        # For NO_CONFLICT: compare base vs vendor
        # For CONFLICT: compare vendor vs customer
        compare_package_id = base_package_id if change.classification == 'NO_CONFLICT' else customer_package_id
        
        # Get record types
        vendor_rt = self._get_record_type(obj_id, new_vendor_package_id)
        compare_rt = self._get_record_type(obj_id, compare_package_id)
        
        # Get fields
        vendor_fields = self._get_record_type_fields(vendor_rt.id) if vendor_rt else []
        compare_fields = self._get_record_type_fields(compare_rt.id) if compare_rt else []
        
        # Get relationships
        vendor_relationships = self._get_record_type_relationships(vendor_rt.id) if vendor_rt else []
        compare_relationships = self._get_record_type_relationships(compare_rt.id) if compare_rt else []
        
        # Get views
        vendor_views = self._get_record_type_views(vendor_rt.id) if vendor_rt else []
        compare_views = self._get_record_type_views(compare_rt.id) if compare_rt else []
        
        # Get actions
        vendor_actions = self._get_record_type_actions(vendor_rt.id) if vendor_rt else []
        compare_actions = self._get_record_type_actions(compare_rt.id) if compare_rt else []
        
        return {
            'object_type': 'Record Type',
            'vendor': {
                'fields': vendor_fields,
                'relationships': vendor_relationships,
                'views': vendor_views,
                'actions': vendor_actions
            },
            'customer': {
                'fields': compare_fields,
                'relationships': compare_relationships,
                'views': compare_views,
                'actions': compare_actions
            },
            'has_changes': (
                vendor_fields != compare_fields or
                vendor_relationships != compare_relationships or
                vendor_views != compare_views or
                vendor_actions != compare_actions
            )
        }
    
    def _get_group_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Get group comparison details."""
        obj_id = change.object_id
        
        # For NO_CONFLICT: compare base vs vendor
        # For CONFLICT: compare vendor vs customer
        compare_package_id = base_package_id if change.classification == 'NO_CONFLICT' else customer_package_id
        
        vendor_group = self._get_group(obj_id, new_vendor_package_id)
        compare_group = self._get_group(obj_id, compare_package_id)
        
        return {
            'object_type': 'Group',
            'vendor': {
                'description': vendor_group.description if vendor_group else None,
                'parent_group': vendor_group.parent_group_uuid if vendor_group else None,
                'members': vendor_group.members if vendor_group else None
            },
            'customer': {
                'description': compare_group.description if compare_group else None,
                'parent_group': compare_group.parent_group_uuid if compare_group else None,
                'members': compare_group.members if compare_group else None
            },
            'has_changes': vendor_group and compare_group and (
                vendor_group.description != compare_group.description or
                vendor_group.members != compare_group.members
            )
        }
    
    def _get_connected_system_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Get connected system comparison details."""
        obj_id = change.object_id
        
        # For NO_CONFLICT: compare base vs vendor
        # For CONFLICT: compare vendor vs customer
        compare_package_id = base_package_id if change.classification == 'NO_CONFLICT' else customer_package_id
        
        vendor_cs = self._get_connected_system(obj_id, new_vendor_package_id)
        compare_cs = self._get_connected_system(obj_id, compare_package_id)
        
        return {
            'object_type': 'Connected System',
            'vendor': {
                'description': vendor_cs.description if vendor_cs else None,
                'base_url': vendor_cs.base_url if vendor_cs else None,
                'authentication': vendor_cs.authentication_type if vendor_cs else None
            },
            'customer': {
                'description': compare_cs.description if compare_cs else None,
                'base_url': compare_cs.base_url if compare_cs else None,
                'authentication': compare_cs.authentication_type if compare_cs else None
            },
            'has_changes': vendor_cs and compare_cs and (
                vendor_cs.description != compare_cs.description or
                vendor_cs.base_url != compare_cs.base_url
            )
        }
    
    def _get_integration_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Get integration comparison details."""
        obj_id = change.object_id
        
        # For NO_CONFLICT: compare base vs vendor
        # For CONFLICT: compare vendor vs customer
        compare_package_id = base_package_id if change.classification == 'NO_CONFLICT' else customer_package_id
        
        vendor_int = self._get_integration(obj_id, new_vendor_package_id)
        compare_int = self._get_integration(obj_id, compare_package_id)
        
        return {
            'object_type': 'Integration',
            'vendor': {
                'description': vendor_int.description if vendor_int else None,
                'endpoint': vendor_int.endpoint if vendor_int else None,
                'method': vendor_int.http_method if vendor_int else None
            },
            'customer': {
                'description': compare_int.description if compare_int else None,
                'endpoint': compare_int.endpoint if compare_int else None,
                'method': compare_int.http_method if compare_int else None
            },
            'has_changes': vendor_int and compare_int and (
                vendor_int.description != compare_int.description or
                vendor_int.endpoint != compare_int.endpoint
            )
        }
    
    def _get_web_api_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Get web API comparison details."""
        obj_id = change.object_id
        
        # For NO_CONFLICT: compare base vs vendor
        # For CONFLICT: compare vendor vs customer
        compare_package_id = base_package_id if change.classification == 'NO_CONFLICT' else customer_package_id
        
        vendor_api = self._get_web_api(obj_id, new_vendor_package_id)
        compare_api = self._get_web_api(obj_id, compare_package_id)
        
        # Get SAIL code from object_versions
        vendor_version = self._get_object_version(obj_id, new_vendor_package_id)
        compare_version = self._get_object_version(obj_id, compare_package_id)
        
        return {
            'object_type': 'Web API',
            'vendor': {
                'sail_code': vendor_version.sail_code if vendor_version else None,
                'endpoint': vendor_api.endpoint if vendor_api else None,
                'method': vendor_api.http_method if vendor_api else None
            },
            'customer': {
                'sail_code': compare_version.sail_code if compare_version else None,
                'endpoint': compare_api.endpoint if compare_api else None,
                'method': compare_api.http_method if compare_api else None
            },
            'has_changes': vendor_version and compare_version and (
                vendor_version.sail_code != compare_version.sail_code or
                (vendor_api and compare_api and vendor_api.endpoint != compare_api.endpoint)
            )
        }
    
    def _get_site_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Get site comparison details."""
        obj_id = change.object_id
        
        # For NO_CONFLICT: compare base vs vendor
        # For CONFLICT: compare vendor vs customer
        compare_package_id = base_package_id if change.classification == 'NO_CONFLICT' else customer_package_id
        
        vendor_site = self._get_site(obj_id, new_vendor_package_id)
        compare_site = self._get_site(obj_id, compare_package_id)
        
        return {
            'object_type': 'Site',
            'vendor': {
                'description': vendor_site.description if vendor_site else None,
                'url_stub': vendor_site.url_stub if vendor_site else None
            },
            'customer': {
                'description': compare_site.description if compare_site else None,
                'url_stub': compare_site.url_stub if compare_site else None
            },
            'has_changes': vendor_site and compare_site and (
                vendor_site.description != compare_site.description or
                vendor_site.url_stub != compare_site.url_stub
            )
        }
    
    def _get_basic_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Get basic comparison for unsupported object types."""
        obj_id = change.object_id
        
        # For NO_CONFLICT: compare base vs vendor
        # For CONFLICT: compare vendor vs customer
        compare_package_id = base_package_id if change.classification == 'NO_CONFLICT' else customer_package_id
        
        vendor_version = self._get_object_version(obj_id, new_vendor_package_id)
        compare_version = self._get_object_version(obj_id, compare_package_id)
        
        return {
            'object_type': change.object.object_type,
            'vendor': {
                'version_uuid': vendor_version.version_uuid if vendor_version else None
            },
            'customer': {
                'version_uuid': compare_version.version_uuid if compare_version else None
            },
            'has_changes': vendor_version and compare_version and (
                vendor_version.version_uuid != compare_version.version_uuid
            )
        }
    
    # Helper methods to fetch data
    
    def _get_object_version(self, object_id: int, package_id: int) -> Optional[ObjectVersion]:
        """Get object version."""
        return db.session.query(ObjectVersion).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _get_constant(self, object_id: int, package_id: int) -> Optional[Constant]:
        """Get constant."""
        return db.session.query(Constant).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _get_expression_rule(self, object_id: int, package_id: int) -> Optional[ExpressionRule]:
        """Get expression rule."""
        return db.session.query(ExpressionRule).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _get_expression_rule_inputs(self, expression_rule_id: int) -> List[Dict[str, Any]]:
        """Get expression rule inputs."""
        inputs = db.session.query(ExpressionRuleInput).filter_by(
            rule_id=expression_rule_id
        ).all()
        return [
            {
                'name': inp.input_name,
                'type': inp.input_type
            }
            for inp in inputs
        ]
    
    def _get_interface(self, object_id: int, package_id: int) -> Optional[Interface]:
        """Get interface."""
        return db.session.query(Interface).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _get_interface_parameters(self, interface_id: int) -> List[Dict[str, Any]]:
        """Get interface parameters."""
        params = db.session.query(InterfaceParameter).filter_by(
            interface_id=interface_id
        ).all()
        return [
            {
                'name': p.parameter_name,
                'type': p.parameter_type
            }
            for p in params
        ]
    
    def _get_process_model(self, object_id: int, package_id: int) -> Optional[ProcessModel]:
        """Get process model."""
        return db.session.query(ProcessModel).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _get_process_model_nodes(self, process_model_id: int) -> List[Dict[str, Any]]:
        """Get process model nodes."""
        nodes = db.session.query(ProcessModelNode).filter_by(
            process_model_id=process_model_id
        ).all()
        return [
            {
                'id': n.id,  # Database primary key for flow connections
                'node_id': n.node_id,  # UUID from Appian
                'name': n.node_name,
                'type': n.node_type
            }
            for n in nodes
        ]
    
    def _get_process_model_flows(self, process_model_id: int) -> List[Dict[str, Any]]:
        """Get process model flows."""
        flows = db.session.query(ProcessModelFlow).filter_by(
            process_model_id=process_model_id
        ).all()
        return [
            {
                'from_node': f.from_node_id,
                'to_node': f.to_node_id,
                'label': f.flow_label
            }
            for f in flows
        ]
    
    def _get_process_model_variables(self, process_model_id: int) -> List[Dict[str, Any]]:
        """Get process model variables."""
        from models import ProcessModelVariable
        variables = db.session.query(ProcessModelVariable).filter_by(
            process_model_id=process_model_id
        ).all()
        return [
            {
                'variable_name': v.variable_name,
                'variable_type': v.variable_type,
                'is_parameter': v.is_parameter,
                'default_value': v.default_value
            }
            for v in variables
        ]
    
    def _generate_mermaid_diagram(
        self,
        nodes: List[Dict[str, Any]],
        flows: List[Dict[str, Any]]
    ) -> str:
        """Generate Mermaid diagram from nodes and flows."""
        if not nodes:
            return "graph LR\n  Start[No nodes]"
        
        lines = ["graph LR"]
        
        # Create a mapping of database ID to node for flow connections
        node_map = {node['id']: node for node in nodes}
        
        # Add nodes using database ID as identifier
        for node in nodes:
            db_id = f"node_{node['id']}"  # Use database ID for Mermaid node identifier
            node_name = node['name'] or 'Unnamed Node'
            # Escape special characters in node name
            node_name = node_name.replace('"', '\\"')
            lines.append(f'  {db_id}["{node_name}"]')
        
        # Add flows using database IDs
        for flow in flows:
            from_id = f"node_{flow['from_node']}"
            to_id = f"node_{flow['to_node']}"
            label = flow.get('label', '')
            if label:
                # Escape special characters in label
                label = label.replace('"', '\\"')
                lines.append(f'  {from_id} -->|"{label}"| {to_id}')
            else:
                lines.append(f"  {from_id} --> {to_id}")
        
        return '\n'.join(lines)
    
    def _generate_mermaid_diagram_with_diff(
        self,
        nodes: List[Dict[str, Any]],
        flows: List[Dict[str, Any]],
        comparison_nodes: List[Dict[str, Any]],
        is_vendor: bool
    ) -> str:
        """
        Generate Mermaid diagram with color-coded differences.
        
        Color coding:
        - Green: Nodes added by customer (only in customer, not in vendor)
        - Red: Nodes removed by vendor (only in vendor, not in customer)
        - Blue: Nodes modified (name changed between versions)
        - Default: Unchanged nodes
        """
        if not nodes:
            return "graph LR\n  Start[No nodes]"
        
        lines = ["graph LR"]
        
        # Create mappings by node_id (UUID) for comparison
        comparison_map = {n['node_id']: n for n in comparison_nodes}
        current_map = {n['node_id']: n for n in nodes}
        
        # Add nodes with styling based on differences
        for node in nodes:
            db_id = f"node_{node['id']}"
            node_name = node['name'] or 'Unnamed Node'
            node_name = node_name.replace('"', '\\"')
            node_uuid = node['node_id']
            
            # Determine node status
            if node_uuid not in comparison_map:
                # Node exists in current but not in comparison
                if is_vendor:
                    # Vendor has it, customer doesn't = removed by customer (show as red in vendor)
                    lines.append(f'  {db_id}["{node_name}"]:::removed')
                else:
                    # Customer has it, vendor doesn't = added by customer (show as green)
                    lines.append(f'  {db_id}["{node_name}"]:::added')
            else:
                # Node exists in both, check if modified
                comparison_node = comparison_map[node_uuid]
                if node['name'] != comparison_node['name']:
                    # Name changed = modified (show as blue)
                    lines.append(f'  {db_id}["{node_name}"]:::modified')
                else:
                    # Unchanged
                    lines.append(f'  {db_id}["{node_name}"]')
        
        # Add flows
        for flow in flows:
            from_id = f"node_{flow['from_node']}"
            to_id = f"node_{flow['to_node']}"
            label = flow.get('label', '')
            if label:
                label = label.replace('"', '\\"')
                lines.append(f'  {from_id} -->|"{label}"| {to_id}')
            else:
                lines.append(f"  {from_id} --> {to_id}")
        
        # Add style definitions
        lines.append("")
        lines.append("  classDef added fill:#10b981,stroke:#059669,color:#fff")
        lines.append("  classDef removed fill:#ef4444,stroke:#dc2626,color:#fff")
        lines.append("  classDef modified fill:#3b82f6,stroke:#2563eb,color:#fff")
        
        return '\n'.join(lines)
    
    def _get_cdt(self, object_id: int, package_id: int) -> Optional[CDT]:
        """Get CDT."""
        return db.session.query(CDT).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _get_cdt_fields(self, cdt_id: int) -> List[Dict[str, Any]]:
        """Get CDT fields."""
        fields = db.session.query(CDTField).filter_by(
            cdt_id=cdt_id
        ).all()
        return [
            {
                'name': f.field_name,
                'type': f.field_type
            }
            for f in fields
        ]
    
    def _get_record_type(self, object_id: int, package_id: int) -> Optional[RecordType]:
        """Get record type."""
        return db.session.query(RecordType).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _get_record_type_fields(self, record_type_id: int) -> List[Dict[str, Any]]:
        """Get record type fields."""
        fields = db.session.query(RecordTypeField).filter_by(
            record_type_id=record_type_id
        ).all()
        return [
            {
                'name': f.field_name,
                'type': f.field_type
            }
            for f in fields
        ]
    
    def _get_record_type_relationships(self, record_type_id: int) -> List[Dict[str, Any]]:
        """Get record type relationships."""
        relationships = db.session.query(RecordTypeRelationship).filter_by(
            record_type_id=record_type_id
        ).all()
        return [
            {
                'name': r.relationship_name,
                'target': r.related_record_uuid
            }
            for r in relationships
        ]
    
    def _get_record_type_views(self, record_type_id: int) -> List[Dict[str, Any]]:
        """Get record type views."""
        views = db.session.query(RecordTypeView).filter_by(
            record_type_id=record_type_id
        ).all()
        return [
            {
                'name': v.view_name,
                'type': v.view_type,
                'configuration': v.configuration
            }
            for v in views
        ]
    
    def _get_record_type_actions(self, record_type_id: int) -> List[Dict[str, Any]]:
        """Get record type actions."""
        actions = db.session.query(RecordTypeAction).filter_by(
            record_type_id=record_type_id
        ).all()
        return [
            {
                'name': a.action_name,
                'type': a.action_type,
                'configuration': a.configuration
            }
            for a in actions
        ]
    
    def _get_group(self, object_id: int, package_id: int) -> Optional[Group]:
        """Get group."""
        return db.session.query(Group).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _get_connected_system(self, object_id: int, package_id: int) -> Optional[ConnectedSystem]:
        """Get connected system."""
        return db.session.query(ConnectedSystem).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _get_integration(self, object_id: int, package_id: int) -> Optional[Integration]:
        """Get integration."""
        return db.session.query(Integration).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _get_web_api(self, object_id: int, package_id: int) -> Optional[WebAPI]:
        """Get web API."""
        return db.session.query(WebAPI).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _get_site(self, object_id: int, package_id: int) -> Optional[Site]:
        """Get site."""
        return db.session.query(Site).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
