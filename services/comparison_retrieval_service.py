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
    ProcessModel, ProcessModelNode, ProcessModelFlow,
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
        
        # Get constants from all packages
        vendor_constant = self._get_constant(obj_id, new_vendor_package_id)
        customer_constant = self._get_constant(obj_id, customer_package_id)
        
        return {
            'object_type': 'Constant',
            'vendor': {
                'type': vendor_constant.constant_type if vendor_constant else None,
                'value': vendor_constant.constant_value if vendor_constant else None
            },
            'customer': {
                'type': customer_constant.constant_type if customer_constant else None,
                'value': customer_constant.constant_value if customer_constant else None
            },
            'has_changes': (
                vendor_constant and customer_constant and
                (vendor_constant.constant_value != customer_constant.constant_value or
                 vendor_constant.constant_type != customer_constant.constant_type)
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
        
        # Get expression rules
        vendor_er = self._get_expression_rule(obj_id, new_vendor_package_id)
        customer_er = self._get_expression_rule(obj_id, customer_package_id)
        
        # Get inputs
        vendor_inputs = self._get_expression_rule_inputs(vendor_er.id) if vendor_er else []
        customer_inputs = self._get_expression_rule_inputs(customer_er.id) if customer_er else []
        
        return {
            'object_type': 'Expression Rule',
            'vendor': {
                'sail_code': vendor_er.sail_code if vendor_er else None,
                'inputs': vendor_inputs,
                'output_type': vendor_er.output_type if vendor_er else None
            },
            'customer': {
                'sail_code': customer_er.sail_code if customer_er else None,
                'inputs': customer_inputs,
                'output_type': customer_er.output_type if customer_er else None
            },
            'has_changes': vendor_er and customer_er and (
                vendor_er.sail_code != customer_er.sail_code or
                vendor_inputs != customer_inputs
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
        
        # Get interfaces
        vendor_interface = self._get_interface(obj_id, new_vendor_package_id)
        customer_interface = self._get_interface(obj_id, customer_package_id)
        
        # Get parameters
        vendor_params = self._get_interface_parameters(vendor_interface.id) if vendor_interface else []
        customer_params = self._get_interface_parameters(customer_interface.id) if customer_interface else []
        
        # Get SAIL code from object_versions
        vendor_version = self._get_object_version(obj_id, new_vendor_package_id)
        customer_version = self._get_object_version(obj_id, customer_package_id)
        
        return {
            'object_type': 'Interface',
            'vendor': {
                'sail_code': vendor_version.sail_code if vendor_version else None,
                'parameters': vendor_params
            },
            'customer': {
                'sail_code': customer_version.sail_code if customer_version else None,
                'parameters': customer_params
            },
            'has_changes': vendor_version and customer_version and (
                vendor_version.sail_code != customer_version.sail_code or
                vendor_params != customer_params
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
        
        # Get process models
        vendor_pm = self._get_process_model(obj_id, new_vendor_package_id)
        customer_pm = self._get_process_model(obj_id, customer_package_id)
        
        # Get nodes
        vendor_nodes = self._get_process_model_nodes(vendor_pm.id) if vendor_pm else []
        customer_nodes = self._get_process_model_nodes(customer_pm.id) if customer_pm else []
        
        # Get flows
        vendor_flows = self._get_process_model_flows(vendor_pm.id) if vendor_pm else []
        customer_flows = self._get_process_model_flows(customer_pm.id) if customer_pm else []
        
        # Generate Mermaid diagrams with color coding
        vendor_mermaid = self._generate_mermaid_diagram_with_diff(
            vendor_nodes, vendor_flows, customer_nodes, is_vendor=True
        )
        customer_mermaid = self._generate_mermaid_diagram_with_diff(
            customer_nodes, customer_flows, vendor_nodes, is_vendor=False
        )
        
        return {
            'object_type': 'Process Model',
            'vendor': {
                'nodes': vendor_nodes,
                'flows': vendor_flows,
                'mermaid_diagram': vendor_mermaid
            },
            'customer': {
                'nodes': customer_nodes,
                'flows': customer_flows,
                'mermaid_diagram': customer_mermaid
            },
            'has_changes': vendor_nodes != customer_nodes or vendor_flows != customer_flows
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
        
        # Get CDTs
        vendor_cdt = self._get_cdt(obj_id, new_vendor_package_id)
        customer_cdt = self._get_cdt(obj_id, customer_package_id)
        
        # Get fields
        vendor_fields = self._get_cdt_fields(vendor_cdt.id) if vendor_cdt else []
        customer_fields = self._get_cdt_fields(customer_cdt.id) if customer_cdt else []
        
        return {
            'object_type': 'CDT',
            'vendor': {
                'fields': vendor_fields,
                'namespace': vendor_cdt.namespace if vendor_cdt else None
            },
            'customer': {
                'fields': customer_fields,
                'namespace': customer_cdt.namespace if customer_cdt else None
            },
            'has_changes': vendor_fields != customer_fields
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
        
        # Get record types
        vendor_rt = self._get_record_type(obj_id, new_vendor_package_id)
        customer_rt = self._get_record_type(obj_id, customer_package_id)
        
        # Get fields
        vendor_fields = self._get_record_type_fields(vendor_rt.id) if vendor_rt else []
        customer_fields = self._get_record_type_fields(customer_rt.id) if customer_rt else []
        
        # Get relationships
        vendor_relationships = self._get_record_type_relationships(vendor_rt.id) if vendor_rt else []
        customer_relationships = self._get_record_type_relationships(customer_rt.id) if customer_rt else []
        
        # Get views
        vendor_views = self._get_record_type_views(vendor_rt.id) if vendor_rt else []
        customer_views = self._get_record_type_views(customer_rt.id) if customer_rt else []
        
        # Get actions
        vendor_actions = self._get_record_type_actions(vendor_rt.id) if vendor_rt else []
        customer_actions = self._get_record_type_actions(customer_rt.id) if customer_rt else []
        
        return {
            'object_type': 'Record Type',
            'vendor': {
                'fields': vendor_fields,
                'relationships': vendor_relationships,
                'views': vendor_views,
                'actions': vendor_actions
            },
            'customer': {
                'fields': customer_fields,
                'relationships': customer_relationships,
                'views': customer_views,
                'actions': customer_actions
            },
            'has_changes': (
                vendor_fields != customer_fields or
                vendor_relationships != customer_relationships or
                vendor_views != customer_views or
                vendor_actions != customer_actions
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
        
        vendor_group = self._get_group(obj_id, new_vendor_package_id)
        customer_group = self._get_group(obj_id, customer_package_id)
        
        return {
            'object_type': 'Group',
            'vendor': {
                'description': vendor_group.description if vendor_group else None,
                'parent_group': vendor_group.parent_group_uuid if vendor_group else None,
                'members': vendor_group.members if vendor_group else None
            },
            'customer': {
                'description': customer_group.description if customer_group else None,
                'parent_group': customer_group.parent_group_uuid if customer_group else None,
                'members': customer_group.members if customer_group else None
            },
            'has_changes': vendor_group and customer_group and (
                vendor_group.description != customer_group.description or
                vendor_group.members != customer_group.members
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
        
        vendor_cs = self._get_connected_system(obj_id, new_vendor_package_id)
        customer_cs = self._get_connected_system(obj_id, customer_package_id)
        
        return {
            'object_type': 'Connected System',
            'vendor': {
                'description': vendor_cs.description if vendor_cs else None,
                'base_url': vendor_cs.base_url if vendor_cs else None,
                'authentication': vendor_cs.authentication_type if vendor_cs else None
            },
            'customer': {
                'description': customer_cs.description if customer_cs else None,
                'base_url': customer_cs.base_url if customer_cs else None,
                'authentication': customer_cs.authentication_type if customer_cs else None
            },
            'has_changes': vendor_cs and customer_cs and (
                vendor_cs.description != customer_cs.description or
                vendor_cs.base_url != customer_cs.base_url
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
        
        vendor_int = self._get_integration(obj_id, new_vendor_package_id)
        customer_int = self._get_integration(obj_id, customer_package_id)
        
        return {
            'object_type': 'Integration',
            'vendor': {
                'description': vendor_int.description if vendor_int else None,
                'endpoint': vendor_int.endpoint if vendor_int else None,
                'method': vendor_int.http_method if vendor_int else None
            },
            'customer': {
                'description': customer_int.description if customer_int else None,
                'endpoint': customer_int.endpoint if customer_int else None,
                'method': customer_int.http_method if customer_int else None
            },
            'has_changes': vendor_int and customer_int and (
                vendor_int.description != customer_int.description or
                vendor_int.endpoint != customer_int.endpoint
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
        
        vendor_api = self._get_web_api(obj_id, new_vendor_package_id)
        customer_api = self._get_web_api(obj_id, customer_package_id)
        
        # Get SAIL code from object_versions
        vendor_version = self._get_object_version(obj_id, new_vendor_package_id)
        customer_version = self._get_object_version(obj_id, customer_package_id)
        
        return {
            'object_type': 'Web API',
            'vendor': {
                'sail_code': vendor_version.sail_code if vendor_version else None,
                'endpoint': vendor_api.endpoint if vendor_api else None,
                'method': vendor_api.http_method if vendor_api else None
            },
            'customer': {
                'sail_code': customer_version.sail_code if customer_version else None,
                'endpoint': customer_api.endpoint if customer_api else None,
                'method': customer_api.http_method if customer_api else None
            },
            'has_changes': vendor_version and customer_version and (
                vendor_version.sail_code != customer_version.sail_code or
                (vendor_api and customer_api and vendor_api.endpoint != customer_api.endpoint)
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
        
        vendor_site = self._get_site(obj_id, new_vendor_package_id)
        customer_site = self._get_site(obj_id, customer_package_id)
        
        return {
            'object_type': 'Site',
            'vendor': {
                'description': vendor_site.description if vendor_site else None,
                'url_stub': vendor_site.url_stub if vendor_site else None
            },
            'customer': {
                'description': customer_site.description if customer_site else None,
                'url_stub': customer_site.url_stub if customer_site else None
            },
            'has_changes': vendor_site and customer_site and (
                vendor_site.description != customer_site.description or
                vendor_site.url_stub != customer_site.url_stub
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
        
        vendor_version = self._get_object_version(obj_id, new_vendor_package_id)
        customer_version = self._get_object_version(obj_id, customer_package_id)
        
        return {
            'object_type': change.object.object_type,
            'vendor': {
                'version_uuid': vendor_version.version_uuid if vendor_version else None
            },
            'customer': {
                'version_uuid': customer_version.version_uuid if customer_version else None
            },
            'has_changes': vendor_version and customer_version and (
                vendor_version.version_uuid != customer_version.version_uuid
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
                'target': r.target_record_type
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
                'interface': v.interface_uuid,
                'context': v.context,
                'security': v.security
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
                'process_model': a.process_model_uuid,
                'interface': a.interface_uuid,
                'security': a.security
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
