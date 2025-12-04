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
    
    def _determine_comparison_strategy(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """
        Determine which packages to compare based on classification and change types.
        
        Returns:
            Dict with keys:
            - old_package_id: Package ID for left side
            - new_package_id: Package ID for right side
            - old_label: Label for left side
            - new_label: Label for right side
            - comparison_type: 'customer_only', 'vendor_changes', or 'conflict'
        """
        if change.classification == 'NO_CONFLICT':
            # NO_CONFLICT logic:
            # 1. If vendor change is None AND customer change is Modified/Added → Show Customer vs Base
            # 2. If vendor change is Modified/Added → Show Vendor Base vs Vendor Latest
            if not change.vendor_change_type and change.customer_change_type in ['MODIFIED', 'ADDED']:
                # Customer-only changes: compare base vs customer
                return {
                    'old_package_id': base_package_id,
                    'new_package_id': customer_package_id,
                    'old_label': 'Vendor Base',
                    'new_label': 'Customer',
                    'comparison_type': 'customer_only'
                }
            else:
                # Vendor changes: compare base vs vendor latest
                return {
                    'old_package_id': base_package_id,
                    'new_package_id': new_vendor_package_id,
                    'old_label': 'Vendor Base',
                    'new_label': 'Vendor Latest',
                    'comparison_type': 'vendor_changes'
                }
        else:
            # CONFLICT: compare vendor vs customer
            return {
                'old_package_id': new_vendor_package_id,
                'new_package_id': customer_package_id,
                'old_label': 'Vendor Latest',
                'new_label': 'Customer',
                'comparison_type': 'conflict'
            }
    
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
        
        # Determine comparison strategy
        strategy = self._determine_comparison_strategy(
            change, base_package_id, customer_package_id, new_vendor_package_id
        )
        
        # Get constants from packages
        old_constant = self._get_constant(obj_id, strategy['old_package_id'])
        new_constant = self._get_constant(obj_id, strategy['new_package_id'])
        
        return {
            'object_type': 'Constant',
            'vendor': {
                'type': new_constant.constant_type if new_constant else None,
                'value': new_constant.constant_value if new_constant else None
            },
            'customer': {
                'type': old_constant.constant_type if old_constant else None,
                'value': old_constant.constant_value if old_constant else None
            },
            'comparison_type': strategy['comparison_type'],
            'old_label': strategy['old_label'],
            'new_label': strategy['new_label'],
            'has_changes': (
                old_constant and new_constant and
                (old_constant.constant_value != new_constant.constant_value or
                 old_constant.constant_type != new_constant.constant_type)
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
        
        # Determine comparison strategy
        strategy = self._determine_comparison_strategy(
            change, base_package_id, customer_package_id, new_vendor_package_id
        )
        
        # Get expression rules
        old_er = self._get_expression_rule(obj_id, strategy['old_package_id'])
        new_er = self._get_expression_rule(obj_id, strategy['new_package_id'])
        
        # Get inputs
        old_inputs = self._get_expression_rule_inputs(old_er.id) if old_er else []
        new_inputs = self._get_expression_rule_inputs(new_er.id) if new_er else []
        
        # Generate SAIL code diff
        from services.sail_diff_service import SailDiffService
        diff_service = SailDiffService()
        
        old_code = old_er.sail_code if old_er else None
        new_code = new_er.sail_code if new_er else None
        
        diff_hunks = diff_service.generate_unified_diff(
            old_code,
            new_code,
            old_label=strategy['old_label'],
            new_label=strategy['new_label']
        )
        
        diff_stats = diff_service.get_change_stats(old_code, new_code)
        
        return {
            'object_type': 'Expression Rule',
            'vendor': {
                'sail_code': new_er.sail_code if new_er else None,
                'inputs': new_inputs,
                'output_type': new_er.output_type if new_er else None
            },
            'customer': {
                'sail_code': old_er.sail_code if old_er else None,
                'inputs': old_inputs,
                'output_type': old_er.output_type if old_er else None
            },
            'diff_hunks': diff_hunks,
            'diff_stats': diff_stats,
            'comparison_type': strategy['comparison_type'],
            'old_label': strategy['old_label'],
            'new_label': strategy['new_label'],
            'has_changes': old_er and new_er and (
                old_er.sail_code != new_er.sail_code or
                old_inputs != new_inputs
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
        
        # Determine comparison strategy
        strategy = self._determine_comparison_strategy(
            change, base_package_id, customer_package_id, new_vendor_package_id
        )
        
        # Get interfaces
        old_interface = self._get_interface(obj_id, strategy['old_package_id'])
        new_interface = self._get_interface(obj_id, strategy['new_package_id'])
        
        # Get parameters
        old_params = self._get_interface_parameters(old_interface.id) if old_interface else []
        new_params = self._get_interface_parameters(new_interface.id) if new_interface else []
        
        # Get SAIL code from object_versions
        old_version = self._get_object_version(obj_id, strategy['old_package_id'])
        new_version = self._get_object_version(obj_id, strategy['new_package_id'])
        
        # Generate SAIL code diff
        from services.sail_diff_service import SailDiffService
        diff_service = SailDiffService()
        
        old_code = old_version.sail_code if old_version else None
        new_code = new_version.sail_code if new_version else None
        
        diff_hunks = diff_service.generate_unified_diff(
            old_code,
            new_code,
            old_label=strategy['old_label'],
            new_label=strategy['new_label']
        )
        
        diff_stats = diff_service.get_change_stats(old_code, new_code)
        
        return {
            'object_type': 'Interface',
            'vendor': {
                'sail_code': new_version.sail_code if new_version else None,
                'parameters': new_params
            },
            'customer': {
                'sail_code': old_version.sail_code if old_version else None,
                'parameters': old_params
            },
            'diff_hunks': diff_hunks,
            'diff_stats': diff_stats,
            'comparison_type': strategy['comparison_type'],
            'old_label': strategy['old_label'],
            'new_label': strategy['new_label'],
            'has_changes': old_version and new_version and (
                old_version.sail_code != new_version.sail_code or
                old_params != new_params
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
        
        # Determine comparison strategy
        strategy = self._determine_comparison_strategy(
            change, base_package_id, customer_package_id, new_vendor_package_id
        )
        
        # Get process models
        old_pm = self._get_process_model(obj_id, strategy['old_package_id'])
        new_pm = self._get_process_model(obj_id, strategy['new_package_id'])
        
        # Get nodes
        old_nodes = self._get_process_model_nodes(old_pm.id) if old_pm else []
        new_nodes = self._get_process_model_nodes(new_pm.id) if new_pm else []
        
        # Get flows
        old_flows = self._get_process_model_flows(old_pm.id) if old_pm else []
        new_flows = self._get_process_model_flows(new_pm.id) if new_pm else []
        
        # Get variables
        old_variables = self._get_process_model_variables(old_pm.id) if old_pm else []
        new_variables = self._get_process_model_variables(new_pm.id) if new_pm else []
        
        # Generate Mermaid diagrams with color coding
        new_mermaid = self._generate_mermaid_diagram_with_diff(
            new_nodes, new_flows, old_nodes, is_vendor=True
        )
        old_mermaid = self._generate_mermaid_diagram_with_diff(
            old_nodes, old_flows, new_nodes, is_vendor=False
        )
        
        return {
            'object_type': 'Process Model',
            'vendor': {
                'nodes': new_nodes,
                'flows': new_flows,
                'variables': new_variables,
                'mermaid_diagram': new_mermaid
            },
            'customer': {
                'nodes': old_nodes,
                'flows': old_flows,
                'variables': old_variables,
                'mermaid_diagram': old_mermaid
            },
            'comparison_type': strategy['comparison_type'],
            'old_label': strategy['old_label'],
            'new_label': strategy['new_label'],
            'has_changes': old_nodes != new_nodes or old_flows != new_flows or old_variables != new_variables
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
        
        # Determine comparison strategy
        strategy = self._determine_comparison_strategy(
            change, base_package_id, customer_package_id, new_vendor_package_id
        )
        
        # Get CDTs
        old_cdt = self._get_cdt(obj_id, strategy['old_package_id'])
        new_cdt = self._get_cdt(obj_id, strategy['new_package_id'])
        
        # Get fields
        old_fields = self._get_cdt_fields(old_cdt.id) if old_cdt else []
        new_fields = self._get_cdt_fields(new_cdt.id) if new_cdt else []
        
        return {
            'object_type': 'CDT',
            'vendor': {
                'fields': new_fields,
                'namespace': new_cdt.namespace if new_cdt else None
            },
            'customer': {
                'fields': old_fields,
                'namespace': old_cdt.namespace if old_cdt else None
            },
            'comparison_type': strategy['comparison_type'],
            'old_label': strategy['old_label'],
            'new_label': strategy['new_label'],
            'has_changes': old_fields != new_fields
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
        
        # Determine comparison strategy
        strategy = self._determine_comparison_strategy(
            change, base_package_id, customer_package_id, new_vendor_package_id
        )
        
        # Get record types
        old_rt = self._get_record_type(obj_id, strategy['old_package_id'])
        new_rt = self._get_record_type(obj_id, strategy['new_package_id'])
        
        # Get fields
        old_fields = self._get_record_type_fields(old_rt.id) if old_rt else []
        new_fields = self._get_record_type_fields(new_rt.id) if new_rt else []
        
        # Get relationships
        old_relationships = self._get_record_type_relationships(old_rt.id) if old_rt else []
        new_relationships = self._get_record_type_relationships(new_rt.id) if new_rt else []
        
        # Get views
        old_views = self._get_record_type_views(old_rt.id) if old_rt else []
        new_views = self._get_record_type_views(new_rt.id) if new_rt else []
        
        # Get actions
        old_actions = self._get_record_type_actions(old_rt.id) if old_rt else []
        new_actions = self._get_record_type_actions(new_rt.id) if new_rt else []
        
        return {
            'object_type': 'Record Type',
            'vendor': {
                'fields': new_fields,
                'relationships': new_relationships,
                'views': new_views,
                'actions': new_actions
            },
            'customer': {
                'fields': old_fields,
                'relationships': old_relationships,
                'views': old_views,
                'actions': old_actions
            },
            'comparison_type': strategy['comparison_type'],
            'old_label': strategy['old_label'],
            'new_label': strategy['new_label'],
            'has_changes': (
                old_fields != new_fields or
                old_relationships != new_relationships or
                old_views != new_views or
                old_actions != new_actions
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
        
        # Determine comparison strategy
        strategy = self._determine_comparison_strategy(
            change, base_package_id, customer_package_id, new_vendor_package_id
        )
        
        old_group = self._get_group(obj_id, strategy['old_package_id'])
        new_group = self._get_group(obj_id, strategy['new_package_id'])
        
        return {
            'object_type': 'Group',
            'vendor': {
                'description': new_group.description if new_group else None,
                'parent_group': new_group.parent_group_uuid if new_group else None,
                'members': new_group.members if new_group else None
            },
            'customer': {
                'description': old_group.description if old_group else None,
                'parent_group': old_group.parent_group_uuid if old_group else None,
                'members': old_group.members if old_group else None
            },
            'comparison_type': strategy['comparison_type'],
            'old_label': strategy['old_label'],
            'new_label': strategy['new_label'],
            'has_changes': old_group and new_group and (
                old_group.description != new_group.description or
                old_group.members != new_group.members
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
        
        # Determine comparison strategy
        strategy = self._determine_comparison_strategy(
            change, base_package_id, customer_package_id, new_vendor_package_id
        )
        
        old_cs = self._get_connected_system(obj_id, strategy['old_package_id'])
        new_cs = self._get_connected_system(obj_id, strategy['new_package_id'])
        
        return {
            'object_type': 'Connected System',
            'vendor': {
                'description': new_cs.description if new_cs else None,
                'base_url': new_cs.base_url if new_cs else None,
                'authentication': new_cs.authentication_type if new_cs else None
            },
            'customer': {
                'description': old_cs.description if old_cs else None,
                'base_url': old_cs.base_url if old_cs else None,
                'authentication': old_cs.authentication_type if old_cs else None
            },
            'comparison_type': strategy['comparison_type'],
            'old_label': strategy['old_label'],
            'new_label': strategy['new_label'],
            'has_changes': old_cs and new_cs and (
                old_cs.description != new_cs.description or
                old_cs.base_url != new_cs.base_url
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
        
        # Determine comparison strategy
        strategy = self._determine_comparison_strategy(
            change, base_package_id, customer_package_id, new_vendor_package_id
        )
        
        old_int = self._get_integration(obj_id, strategy['old_package_id'])
        new_int = self._get_integration(obj_id, strategy['new_package_id'])
        
        return {
            'object_type': 'Integration',
            'vendor': {
                'description': new_int.description if new_int else None,
                'endpoint': new_int.endpoint if new_int else None,
                'method': new_int.http_method if new_int else None
            },
            'customer': {
                'description': old_int.description if old_int else None,
                'endpoint': old_int.endpoint if old_int else None,
                'method': old_int.http_method if old_int else None
            },
            'comparison_type': strategy['comparison_type'],
            'old_label': strategy['old_label'],
            'new_label': strategy['new_label'],
            'has_changes': old_int and new_int and (
                old_int.description != new_int.description or
                old_int.endpoint != new_int.endpoint
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
        
        # Determine comparison strategy
        strategy = self._determine_comparison_strategy(
            change, base_package_id, customer_package_id, new_vendor_package_id
        )
        
        old_api = self._get_web_api(obj_id, strategy['old_package_id'])
        new_api = self._get_web_api(obj_id, strategy['new_package_id'])
        
        # Get SAIL code from object_versions
        old_version = self._get_object_version(obj_id, strategy['old_package_id'])
        new_version = self._get_object_version(obj_id, strategy['new_package_id'])
        
        return {
            'object_type': 'Web API',
            'vendor': {
                'sail_code': new_version.sail_code if new_version else None,
                'endpoint': new_api.endpoint if new_api else None,
                'method': new_api.http_method if new_api else None
            },
            'customer': {
                'sail_code': old_version.sail_code if old_version else None,
                'endpoint': old_api.endpoint if old_api else None,
                'method': old_api.http_method if old_api else None
            },
            'comparison_type': strategy['comparison_type'],
            'old_label': strategy['old_label'],
            'new_label': strategy['new_label'],
            'has_changes': old_version and new_version and (
                old_version.sail_code != new_version.sail_code or
                (old_api and new_api and old_api.endpoint != new_api.endpoint)
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
        
        # Determine comparison strategy
        strategy = self._determine_comparison_strategy(
            change, base_package_id, customer_package_id, new_vendor_package_id
        )
        
        old_site = self._get_site(obj_id, strategy['old_package_id'])
        new_site = self._get_site(obj_id, strategy['new_package_id'])
        
        return {
            'object_type': 'Site',
            'vendor': {
                'description': new_site.description if new_site else None,
                'url_stub': new_site.url_stub if new_site else None
            },
            'customer': {
                'description': old_site.description if old_site else None,
                'url_stub': old_site.url_stub if old_site else None
            },
            'comparison_type': strategy['comparison_type'],
            'old_label': strategy['old_label'],
            'new_label': strategy['new_label'],
            'has_changes': old_site and new_site and (
                old_site.description != new_site.description or
                old_site.url_stub != new_site.url_stub
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
        
        # Determine comparison strategy
        strategy = self._determine_comparison_strategy(
            change, base_package_id, customer_package_id, new_vendor_package_id
        )
        
        old_version = self._get_object_version(obj_id, strategy['old_package_id'])
        new_version = self._get_object_version(obj_id, strategy['new_package_id'])
        
        return {
            'object_type': change.object.object_type,
            'vendor': {
                'version_uuid': new_version.version_uuid if new_version else None
            },
            'customer': {
                'version_uuid': old_version.version_uuid if old_version else None
            },
            'comparison_type': strategy['comparison_type'],
            'old_label': strategy['old_label'],
            'new_label': strategy['new_label'],
            'has_changes': old_version and new_version and (
                old_version.version_uuid != new_version.version_uuid
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
