"""
Three-Way Comparison Service

Performs three-way comparison analysis (A→B and A→C) using the existing
EnhancedVersionComparator infrastructure.
"""
from typing import Dict, Any, Tuple
from services.appian_analyzer.enhanced_version_comparator import (
    EnhancedVersionComparator
)
from services.appian_analyzer.models import AppianObject, ImportChangeStatus
from services.appian_analyzer.process_model_enhancement import NodeComparator


class ThreeWayComparisonService:
    """
    Performs three-way comparison analysis

    Compares:
    - A→C: Vendor changes (base to new vendor)
    - A→B: Customer changes (base to customized)
    """

    def __init__(self):
        """Initialize the three-way comparison service"""
        self.comparator = EnhancedVersionComparator()
        self.node_comparator = NodeComparator()

    def compare_vendor_changes(
        self,
        base_blueprint: Dict[str, Any],
        new_vendor_blueprint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare A→C to identify vendor changes

        Args:
            base_blueprint: Blueprint from base package (A)
            new_vendor_blueprint: Blueprint from new vendor package (C)

        Returns:
            Dictionary with:
            {
                'added': [list of added objects],
                'modified': [list of modified objects],
                'removed': [list of removed objects]
            }
        """
        return self._perform_comparison(
            base_blueprint,
            new_vendor_blueprint,
            "vendor"
        )

    def compare_customer_changes(
        self,
        base_blueprint: Dict[str, Any],
        customized_blueprint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare A→B to identify customer changes

        Args:
            base_blueprint: Blueprint from base package (A)
            customized_blueprint: Blueprint from customized package (B)

        Returns:
            Dictionary with:
            {
                'added': [list of added objects],
                'modified': [list of modified objects],
                'removed': [list of removed objects]
            }
        """
        return self._perform_comparison(
            base_blueprint,
            customized_blueprint,
            "customer"
        )

    def perform_three_way_comparison(
        self,
        base_blueprint: Dict[str, Any],
        customized_blueprint: Dict[str, Any],
        new_vendor_blueprint: Dict[str, Any],
        logger=None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Perform both comparisons (A→C and A→B)

        Args:
            base_blueprint: Blueprint from base package (A)
            customized_blueprint: Blueprint from customized package (B)
            new_vendor_blueprint: Blueprint from new vendor package (C)
            logger: Optional logger instance

        Returns:
            Tuple of (vendor_changes, customer_changes)
        """
        # Vendor changes (A→C)
        if logger:
            logger.log_comparison_start('vendor')
        vendor_changes = self.compare_vendor_changes(
            base_blueprint,
            new_vendor_blueprint
        )
        if logger:
            logger.log_comparison_complete(
                'vendor',
                len(vendor_changes.get('added', [])),
                len(vendor_changes.get('modified', [])),
                len(vendor_changes.get('removed', []))
            )
        
        # Customer changes (A→B)
        if logger:
            logger.log_comparison_start('customer')
        customer_changes = self.compare_customer_changes(
            base_blueprint,
            customized_blueprint
        )
        if logger:
            logger.log_comparison_complete(
                'customer',
                len(customer_changes.get('added', [])),
                len(customer_changes.get('modified', [])),
                len(customer_changes.get('removed', []))
            )

        return (vendor_changes, customer_changes)

    def _perform_comparison(
        self,
        base_blueprint: Dict[str, Any],
        target_blueprint: Dict[str, Any],
        comparison_type: str
    ) -> Dict[str, Any]:
        """
        Perform comparison between two blueprints

        Args:
            base_blueprint: Base blueprint (A)
            target_blueprint: Target blueprint (B or C)
            comparison_type: "vendor" or "customer"

        Returns:
            Dictionary with added, modified, removed objects
        """
        # Extract object lookups
        base_lookup = base_blueprint.get('object_lookup', {})
        target_lookup = target_blueprint.get('object_lookup', {})

        if not base_lookup or not target_lookup:
            raise ValueError(
                f"Object lookup missing in {comparison_type} comparison"
            )

        # Convert lookups to AppianObject instances for comparison
        base_objects = self._convert_to_appian_objects(base_lookup)
        target_objects = self._convert_to_appian_objects(target_lookup)

        # Perform comparison using EnhancedVersionComparator
        comparison_results = self.comparator.compare_by_uuid(
            base_objects,
            target_objects
        )

        # Categorize results
        added = []
        modified = []
        removed = []

        for result in comparison_results:
            change_obj = self._build_change_object(result, target_lookup)

            if result.status == ImportChangeStatus.NEW:
                added.append(change_obj)
            elif result.status == ImportChangeStatus.REMOVED:
                removed.append(change_obj)
            elif result.status in [
                ImportChangeStatus.CHANGED,
                ImportChangeStatus.CONFLICT_DETECTED,
                ImportChangeStatus.NOT_CHANGED_NEW_VUUID  # Version changed even if content identical
            ]:
                modified.append(change_obj)
            # Only NOT_CHANGED is excluded

        return {
            'added': added,
            'modified': modified,
            'removed': removed
        }

    def _convert_to_appian_objects(
        self,
        object_lookup: Dict[str, Any]
    ) -> Dict[str, AppianObject]:
        """
        Convert object lookup dictionary to AppianObject instances

        Args:
            object_lookup: Dictionary of UUID -> object data

        Returns:
            Dictionary of UUID -> AppianObject
        """
        appian_objects = {}

        for uuid, obj_data in object_lookup.items():
            # Create AppianObject with necessary attributes
            appian_obj = AppianObject(
                uuid=uuid,
                name=obj_data.get('name', 'Unknown'),
                object_type=obj_data.get('object_type', 'Unknown'),
                description=obj_data.get('description', '')
            )

            # Add version information if available
            if 'version_uuid' in obj_data:
                appian_obj.version_uuid = obj_data['version_uuid']
            if 'version_history' in obj_data:
                appian_obj.version_history = obj_data['version_history']

            # Add SAIL code if available
            if 'sail_code' in obj_data:
                appian_obj.sail_code = obj_data['sail_code']

            # Add business logic if available
            if 'business_logic' in obj_data:
                appian_obj.business_logic = obj_data['business_logic']

            # Add fields if available (for record types)
            if 'fields' in obj_data:
                appian_obj.fields = obj_data['fields']

            # Add raw XML if available
            if 'raw_xml' in obj_data:
                appian_obj.raw_xml = obj_data['raw_xml']

            # Add properties if available
            if 'properties' in obj_data:
                appian_obj.properties = obj_data['properties']

            appian_objects[uuid] = appian_obj

        return appian_objects

    def _build_change_object(
        self,
        comparison_result,
        target_lookup: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build change object from comparison result

        Args:
            comparison_result: ComparisonResult from comparator
            target_lookup: Object lookup for target blueprint

        Returns:
            Dictionary with change details
        """
        obj = comparison_result.obj
        old_obj = comparison_result.old_obj

        change_obj = {
            'uuid': obj.uuid,
            'name': obj.name,
            'type': obj.object_type,
            'change_type': comparison_result.status.value
        }

        # Add change details if modified
        if comparison_result.content_diff:
            change_obj['changes'] = [comparison_result.content_diff]

        # Add SAIL code if available
        if hasattr(obj, 'sail_code') and obj.sail_code:
            change_obj['sail_code_after'] = obj.sail_code

        if old_obj and hasattr(old_obj, 'sail_code') and old_obj.sail_code:
            change_obj['sail_code_before'] = old_obj.sail_code

        # Add business logic if available
        if hasattr(obj, 'business_logic') and obj.business_logic:
            change_obj['business_logic_after'] = obj.business_logic

        if (old_obj and hasattr(old_obj, 'business_logic') and
                old_obj.business_logic):
            change_obj['business_logic_before'] = old_obj.business_logic

        # Add fields if available
        if hasattr(obj, 'fields') and obj.fields:
            change_obj['fields_after'] = obj.fields

        if old_obj and hasattr(old_obj, 'fields') and old_obj.fields:
            change_obj['fields_before'] = old_obj.fields

        # Add properties if available
        if hasattr(obj, 'properties') and obj.properties:
            change_obj['properties_after'] = obj.properties

        if old_obj and hasattr(old_obj, 'properties') and old_obj.properties:
            change_obj['properties_before'] = old_obj.properties

        # Add version information
        if comparison_result.version_info:
            change_obj['version_info'] = comparison_result.version_info

        # Add enhanced process model data if this is a process model
        # Requirements: 9.3
        if obj.object_type == 'Process Model':
            change_obj['process_model_data'] = self._extract_process_model_data(
                obj, old_obj, target_lookup
            )

        return change_obj

    def _extract_process_model_data(
        self,
        obj: AppianObject,
        old_obj: AppianObject,
        target_lookup: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract enhanced process model data for comparison
        
        This method extracts node and flow information from process models
        and performs detailed comparison using NodeComparator.
        
        Requirements: 9.3
        
        Args:
            obj: Current version of process model object
            old_obj: Previous version of process model object
            target_lookup: Object lookup for target blueprint
            
        Returns:
            Dictionary containing enhanced process model comparison data
        """
        process_model_data = {
            'has_enhanced_data': False,
            'node_comparison': None,
            'flow_comparison': None,
            'node_summary': None,
            'flow_graph': None
        }
        
        try:
            # Get enhanced data from target lookup
            target_obj_data = target_lookup.get(obj.uuid, {})
            
            # Check if enhanced node data is available
            target_nodes = target_obj_data.get('nodes', [])
            target_flows = target_obj_data.get('flows', [])
            target_flow_graph = target_obj_data.get('flow_graph', {})
            target_node_summary = target_obj_data.get('node_summary', {})
            
            if not target_nodes:
                # No enhanced data available
                return process_model_data
            
            process_model_data['has_enhanced_data'] = True
            process_model_data['node_summary'] = target_node_summary
            process_model_data['flow_graph'] = target_flow_graph
            
            # If we have old_obj, perform comparison
            if old_obj:
                # Try to get old object's enhanced data
                # Note: This assumes the base blueprint also has enhanced data
                # If not available, we'll just include the target data

                # Check if old_obj has enhanced attributes
                if hasattr(old_obj, 'nodes'):
                    old_nodes = (
                        old_obj.nodes
                        if isinstance(old_obj.nodes, list)
                        else []
                    )
                else:
                    old_nodes = []

                if hasattr(old_obj, 'flows'):
                    old_flows = (
                        old_obj.flows
                        if isinstance(old_obj.flows, list)
                        else []
                    )
                else:
                    old_flows = []
                
                # Perform node comparison (even if one side is empty)
                if old_nodes or target_nodes:
                    node_comparison = self.node_comparator.compare_nodes(
                        old_nodes if old_nodes else [],
                        target_nodes if target_nodes else []
                    )
                    process_model_data['node_comparison'] = node_comparison
                else:
                    # No nodes on either side
                    process_model_data['node_comparison'] = {
                        'added': [],
                        'removed': [],
                        'modified': [],
                        'unchanged': []
                    }
                
                # Perform flow comparison (even if one side is empty)
                if old_flows or target_flows:
                    flow_comparison = self.node_comparator.compare_flows(
                        old_flows if old_flows else [],
                        target_flows if target_flows else []
                    )
                    process_model_data['flow_comparison'] = flow_comparison
                else:
                    # No flows on either side
                    process_model_data['flow_comparison'] = {
                        'added_flows': [],
                        'removed_flows': [],
                        'modified_flows': [],
                        'unchanged_flows': []
                    }
            else:
                # No old object, so all nodes and flows are "added"
                process_model_data['node_comparison'] = {
                    'added': target_nodes,
                    'removed': [],
                    'modified': [],
                    'unchanged': []
                }
                process_model_data['flow_comparison'] = {
                    'added_flows': target_flows,
                    'removed_flows': [],
                    'modified_flows': [],
                    'unchanged_flows': []
                }
            
        except Exception as e:
            # Log error but don't fail the entire comparison
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Error extracting process model data for {obj.name}: {e}",
                exc_info=True
            )
        
        return process_model_data
