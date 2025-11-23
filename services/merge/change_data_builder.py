"""
Change Data Builder

Handles building dictionary representations of changes and related objects
for the three-way merge service.
"""
import json
from typing import Dict, Any, Optional, List


class ChangeDataBuilder:
    """
    Builds dictionary representations of changes and objects
    
    Responsible for converting database models into dictionaries
    with enriched data for display and processing.
    """
    
    def build_change_dict(self, change) -> Dict[str, Any]:
        """
        Build a dictionary representation of a Change with related objects

        Args:
            change: Change model instance with eager-loaded relationships

        Returns:
            Dictionary with complete change information
        """
        change_dict = {
            'id': change.id,
            'uuid': change.object_uuid,
            'name': change.object_name,
            'type': change.object_type,
            'classification': change.classification,
            'change_type': change.change_type,
            'vendor_change_type': change.vendor_change_type,
            'customer_change_type': change.customer_change_type,
            'display_order': change.display_order
        }

        # Add base object data
        if change.base_object:
            change_dict['base_object'] = self.build_object_dict(
                change.base_object,
                object_type=change.object_type
            )

        # Add customer object data
        if change.customer_object:
            change_dict['customer_object'] = self.build_object_dict(
                change.customer_object,
                object_type=change.object_type
            )

        # Add vendor object data
        if change.vendor_object:
            change_dict['vendor_object'] = self.build_object_dict(
                change.vendor_object,
                object_type=change.object_type
            )

        # Add merge guidance data
        if change.merge_guidance:
            change_dict['merge_guidance'] = {
                'recommendation': change.merge_guidance.recommendation,
                'reason': change.merge_guidance.reason,
                'conflicts': [
                    {
                        'field_name': c.field_name,
                        'conflict_type': c.conflict_type,
                        'description': c.description
                    }
                    for c in change.merge_guidance.conflicts
                ],
                'changes': [
                    {
                        'field_name': c.field_name,
                        'description': c.change_description,
                        'old_value': c.old_value,
                        'new_value': c.new_value
                    }
                    for c in change.merge_guidance.changes
                ]
            }

        # Add review status
        if change.review:
            change_dict['review_status'] = change.review.review_status
            change_dict['user_notes'] = change.review.user_notes
            change_dict['reviewed_at'] = (
                change.review.reviewed_at.isoformat()
                if change.review.reviewed_at else None
            )
        else:
            change_dict['review_status'] = 'pending'
            change_dict['user_notes'] = None
            change_dict['reviewed_at'] = None

        # Add process model comparison data if this is a Process Model
        if change.object_type == 'Process Model':
            change_dict['process_model_data'] = self.build_process_model_comparison(
                change_dict.get('base_object'),
                change_dict.get('customer_object'),
                change_dict.get('vendor_object')
            )

        return change_dict

    def build_object_dict(
        self,
        obj,
        object_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a dictionary representation of an AppianObject

        Args:
            obj: AppianObject model instance
            object_type: Optional object type override (from Change table)

        Returns:
            Dictionary with object information
        """
        # Use provided object_type or fall back to obj.object_type
        effective_type = object_type or obj.object_type
        
        obj_dict = {
            'uuid': obj.uuid,
            'name': obj.name,
            'type': effective_type,
            'sail_code': obj.sail_code,
            'fields': (
                json.loads(obj.fields) if obj.fields else None
            ),
            'properties': (
                json.loads(obj.properties) if obj.properties else None
            )
        }
        
        # Add process model data if this is a Process Model
        if effective_type == 'Process Model' and obj.process_model_metadata:
            pm_meta = obj.process_model_metadata
            obj_dict['process_model_data'] = {
                'has_enhanced_data': True,
                'total_nodes': pm_meta.total_nodes,
                'total_flows': pm_meta.total_flows,
                'complexity_score': pm_meta.complexity_score,
                'nodes': [
                    {
                        'uuid': node.node_id,
                        'type': node.node_type,
                        'name': node.node_name,
                        'properties': json.loads(node.properties) if node.properties else {}
                    }
                    for node in pm_meta.nodes
                ],
                'flows': [
                    {
                        'from_node_uuid': flow.from_node.node_id if flow.from_node else None,
                        'to_node_uuid': flow.to_node.node_id if flow.to_node else None,
                        'condition': flow.flow_condition,
                        'label': flow.flow_label
                    }
                    for flow in pm_meta.flows
                ]
            }
        
        return obj_dict

    def build_process_model_comparison(
        self,
        base_obj: Optional[Dict[str, Any]],
        customer_obj: Optional[Dict[str, Any]],
        vendor_obj: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build process model comparison data for flow diagram visualization

        Args:
            base_obj: Base version object dict
            customer_obj: Customer version object dict
            vendor_obj: Vendor version object dict

        Returns:
            Dictionary with process model comparison data
        """
        # If no process model data exists, return empty structure
        if not vendor_obj or 'process_model_data' not in vendor_obj:
            return {'has_enhanced_data': False}

        vendor_pm = vendor_obj['process_model_data']
        customer_pm = customer_obj.get('process_model_data') if customer_obj else None
        base_pm = base_obj.get('process_model_data') if base_obj else None

        # Build node comparison
        vendor_nodes = {n['uuid']: n for n in vendor_pm.get('nodes', [])}
        customer_nodes = {n['uuid']: n for n in customer_pm.get('nodes', [])} if customer_pm else {}
        base_nodes = {n['uuid']: n for n in base_pm.get('nodes', [])} if base_pm else {}

        added_nodes = []
        removed_nodes = []
        modified_nodes = []
        unchanged_nodes = []

        # Find added nodes (in vendor but not in base)
        for uuid, node in vendor_nodes.items():
            if uuid not in base_nodes:
                added_nodes.append(node)
            elif uuid in customer_nodes:
                # Check if modified
                if self._nodes_differ(base_nodes[uuid], vendor_nodes[uuid]):
                    modified_nodes.append({
                        'node': node,
                        'changes': ['Modified by vendor']
                    })
                else:
                    unchanged_nodes.append(node)
            else:
                unchanged_nodes.append(node)

        # Find removed nodes (in base but not in vendor)
        for uuid, node in base_nodes.items():
            if uuid not in vendor_nodes:
                removed_nodes.append(node)

        # Build flow comparison
        vendor_flows = vendor_pm.get('flows', [])
        base_flows = base_pm.get('flows', []) if base_pm else []

        # Create flow signatures for comparison
        def flow_signature(flow):
            return f"{flow.get('from_node_uuid')}→{flow.get('to_node_uuid')}"

        vendor_flow_sigs = {flow_signature(f): f for f in vendor_flows}
        base_flow_sigs = {flow_signature(f): f for f in base_flows}

        added_flows = [f for sig, f in vendor_flow_sigs.items() if sig not in base_flow_sigs]
        unchanged_flows = [f for sig, f in vendor_flow_sigs.items() if sig in base_flow_sigs]

        return {
            'has_enhanced_data': True,
            'total_nodes': vendor_pm.get('total_nodes', 0),
            'total_flows': vendor_pm.get('total_flows', 0),
            'complexity_score': vendor_pm.get('complexity_score'),
            'node_comparison': {
                'added': added_nodes,
                'removed': removed_nodes,
                'modified': modified_nodes,
                'unchanged': unchanged_nodes
            },
            'flow_comparison': {
                'added_flows': added_flows,
                'unchanged_flows': unchanged_flows
            },
            'flow_graph': {
                'nodes': list(vendor_nodes.values()),
                'flows': vendor_flows
            }
        }

    def _nodes_differ(self, node1: Dict[str, Any], node2: Dict[str, Any]) -> bool:
        """
        Check if two nodes are different

        Args:
            node1: First node dict
            node2: Second node dict

        Returns:
            True if nodes differ, False otherwise
        """
        # Compare name and type
        if node1.get('name') != node2.get('name'):
            return True
        if node1.get('type') != node2.get('type'):
            return True
        return False
