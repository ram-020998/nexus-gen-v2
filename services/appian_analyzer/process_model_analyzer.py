"""
Process Model Analyzer

This module provides analysis and rendering capabilities for Appian Process Models,
including node comparison, HTML rendering, and flow diagram generation.

Extracted from process_model_enhancement.py as part of repository refactoring.
Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""
from typing import List, Dict, Any, Optional
from .logger import get_logger

# Initialize logger
logger = get_logger()

# Import data classes from process_model_enhancement
from .process_model_enhancement import (
    NodeType,
    EnhancedNode,
    Flow,
    FlowGraph,
    NodeComparison,
    FlowComparison,
    ProcessModelComparison
)


class NodeComparator:
    """
    Compares nodes between process model versions
    
    This class performs node-by-node comparison between two versions of a
    process model, identifying added, removed, and modified nodes, and
    generating property-level diffs for modified nodes.
    
    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    def __init__(self):
        """Initialize NodeComparator"""
        pass
    
    def compare_nodes(
        self,
        base_nodes: List[Dict[str, Any]],
        target_nodes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare nodes between two process model versions
        
        Compares nodes by UUID to identify which nodes were added, removed,
        or modified between versions. For modified nodes, generates detailed
        property-level diffs showing what changed.
        
        Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
        
        Args:
            base_nodes: List of node dictionaries from base version
            target_nodes: List of node dictionaries from target version
            
        Returns:
            Dictionary containing comparison results with structure:
            {
                'added': [node],
                'removed': [node],
                'modified': [
                    {
                        'node': node,
                        'changes': [
                            {
                                'property': str,
                                'before': Any,
                                'after': Any
                            }
                        ]
                    }
                ],
                'unchanged': [node]
            }
        """
        try:
            # Create UUID-indexed lookups for efficient comparison
            base_lookup = {node['uuid']: node for node in base_nodes}
            target_lookup = {node['uuid']: node for node in target_nodes}
            
            base_uuids = set(base_lookup.keys())
            target_uuids = set(target_lookup.keys())
            
            # Identify added nodes (in target but not in base)
            added_uuids = target_uuids - base_uuids
            added_nodes = [target_lookup[uuid] for uuid in added_uuids]
            
            # Identify removed nodes (in base but not in target)
            removed_uuids = base_uuids - target_uuids
            removed_nodes = [base_lookup[uuid] for uuid in removed_uuids]
            
            # Identify potentially modified nodes (in both versions)
            common_uuids = base_uuids & target_uuids
            
            modified_nodes = []
            unchanged_nodes = []
            
            for uuid in common_uuids:
                base_node = base_lookup[uuid]
                target_node = target_lookup[uuid]
                
                # Compare nodes to find property changes
                changes = self._compare_node_properties(base_node, target_node)
                
                if changes:
                    # Node has changes
                    modified_nodes.append({
                        'node': target_node,
                        'changes': changes
                    })
                else:
                    # Node is unchanged
                    unchanged_nodes.append(target_node)
            
            result = {
                'added': added_nodes,
                'removed': removed_nodes,
                'modified': modified_nodes,
                'unchanged': unchanged_nodes
            }
            
            logger.info(
                f"Node comparison: {len(added_nodes)} added, "
                f"{len(removed_nodes)} removed, {len(modified_nodes)} modified, "
                f"{len(unchanged_nodes)} unchanged"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error comparing nodes: {e}", exc_info=True)
            # Return empty comparison on error
            return {
                'added': [],
                'removed': [],
                'modified': [],
                'unchanged': []
            }
    
    def _compare_node_properties(
        self,
        base_node: Dict[str, Any],
        target_node: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Compare properties between two versions of the same node
        
        Performs deep comparison of node properties to identify all changes
        at the property level, including changes in basic info, assignments,
        forms, expressions, and escalations.
        
        Requirements: 4.5
        
        Args:
            base_node: Node dictionary from base version
            target_node: Node dictionary from target version
            
        Returns:
            List of property change dictionaries with structure:
            [
                {
                    'property': str,  # Property path (e.g., 'properties.basic.description')
                    'before': Any,
                    'after': Any
                }
            ]
        """
        changes = []
        
        try:
            # Compare node name
            if base_node.get('name') != target_node.get('name'):
                changes.append({
                    'property': 'name',
                    'before': base_node.get('name'),
                    'after': target_node.get('name')
                })
            
            # Compare node type
            if base_node.get('type') != target_node.get('type'):
                changes.append({
                    'property': 'type',
                    'before': base_node.get('type'),
                    'after': target_node.get('type')
                })
            
            # Compare properties by category
            base_props = base_node.get('properties', {})
            target_props = target_node.get('properties', {})
            
            # Compare each property category
            for category in ['basic', 'assignment', 'forms', 'expressions', 'escalation']:
                base_category = base_props.get(category, {})
                target_category = target_props.get(category, {})
                
                # Find all keys in either version
                all_keys = set(base_category.keys()) | set(target_category.keys())
                
                for key in all_keys:
                    base_value = base_category.get(key)
                    target_value = target_category.get(key)
                    
                    # Compare values
                    if base_value != target_value:
                        changes.append({
                            'property': f'properties.{category}.{key}',
                            'before': base_value,
                            'after': target_value
                        })
            
            # Compare dependencies
            base_deps = base_node.get('dependencies', {})
            target_deps = target_node.get('dependencies', {})
            
            for dep_type in ['interfaces', 'rules', 'groups']:
                base_dep_list = base_deps.get(dep_type, [])
                target_dep_list = target_deps.get(dep_type, [])
                
                # Convert to sets of UUIDs for comparison
                base_dep_uuids = {dep['uuid'] for dep in base_dep_list}
                target_dep_uuids = {dep['uuid'] for dep in target_dep_list}
                
                if base_dep_uuids != target_dep_uuids:
                    changes.append({
                        'property': f'dependencies.{dep_type}',
                        'before': base_dep_list,
                        'after': target_dep_list
                    })
            
        except Exception as e:
            logger.warning(f"Error comparing node properties: {e}")
        
        return changes
    
    def compare_flows(
        self,
        base_flows: List[Dict[str, Any]],
        target_flows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare flows between two process model versions
        
        Compares flow lists to identify which flows were added, removed,
        or modified between versions. Flows are compared by their source
        and target node UUIDs.
        
        Requirements: 5.8
        
        Args:
            base_flows: List of flow dictionaries from base version
            target_flows: List of flow dictionaries from target version
            
        Returns:
            Dictionary containing flow comparison results with structure:
            {
                'added_flows': [flow],
                'removed_flows': [flow],
                'modified_flows': [
                    {
                        'flow': flow,
                        'changes': [
                            {
                                'property': str,
                                'before': Any,
                                'after': Any
                            }
                        ]
                    }
                ],
                'unchanged_flows': [flow]
            }
        """
        try:
            # Create flow identifiers based on source and target nodes
            # A flow is uniquely identified by (from_node_uuid, to_node_uuid)
            def flow_key(flow):
                return (flow['from_node_uuid'], flow['to_node_uuid'])
            
            # Create lookups indexed by flow key
            base_lookup = {flow_key(flow): flow for flow in base_flows}
            target_lookup = {flow_key(flow): flow for flow in target_flows}
            
            base_keys = set(base_lookup.keys())
            target_keys = set(target_lookup.keys())
            
            # Identify added flows (in target but not in base)
            added_keys = target_keys - base_keys
            added_flows = [target_lookup[key] for key in added_keys]
            
            # Identify removed flows (in base but not in target)
            removed_keys = base_keys - target_keys
            removed_flows = [base_lookup[key] for key in removed_keys]
            
            # Identify potentially modified flows (in both versions)
            common_keys = base_keys & target_keys
            
            modified_flows = []
            unchanged_flows = []
            
            for key in common_keys:
                base_flow = base_lookup[key]
                target_flow = target_lookup[key]
                
                # Compare flow properties
                changes = self._compare_flow_properties(base_flow, target_flow)
                
                if changes:
                    # Flow has changes
                    modified_flows.append({
                        'flow': target_flow,
                        'changes': changes
                    })
                else:
                    # Flow is unchanged
                    unchanged_flows.append(target_flow)
            
            result = {
                'added_flows': added_flows,
                'removed_flows': removed_flows,
                'modified_flows': modified_flows,
                'unchanged_flows': unchanged_flows
            }
            
            logger.info(
                f"Flow comparison: {len(added_flows)} added, "
                f"{len(removed_flows)} removed, {len(modified_flows)} modified, "
                f"{len(unchanged_flows)} unchanged"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error comparing flows: {e}", exc_info=True)
            # Return empty comparison on error
            return {
                'added_flows': [],
                'removed_flows': [],
                'modified_flows': [],
                'unchanged_flows': []
            }
    
    def _compare_flow_properties(
        self,
        base_flow: Dict[str, Any],
        target_flow: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Compare properties between two versions of the same flow
        
        Compares flow properties to identify changes in conditions,
        labels, or other flow attributes.
        
        Requirements: 5.8
        
        Args:
            base_flow: Flow dictionary from base version
            target_flow: Flow dictionary from target version
            
        Returns:
            List of property change dictionaries
        """
        changes = []
        
        try:
            # Compare condition
            if base_flow.get('condition') != target_flow.get('condition'):
                changes.append({
                    'property': 'condition',
                    'before': base_flow.get('condition'),
                    'after': target_flow.get('condition')
                })
            
            # Compare is_default flag
            if base_flow.get('is_default') != target_flow.get('is_default'):
                changes.append({
                    'property': 'is_default',
                    'before': base_flow.get('is_default'),
                    'after': target_flow.get('is_default')
                })
            
            # Compare label
            if base_flow.get('label') != target_flow.get('label'):
                changes.append({
                    'property': 'label',
                    'before': base_flow.get('label'),
                    'after': target_flow.get('label')
                })
            
            # Compare node names (in case nodes were renamed)
            if base_flow.get('from_node_name') != target_flow.get('from_node_name'):
                changes.append({
                    'property': 'from_node_name',
                    'before': base_flow.get('from_node_name'),
                    'after': target_flow.get('from_node_name')
                })
            
            if base_flow.get('to_node_name') != target_flow.get('to_node_name'):
                changes.append({
                    'property': 'to_node_name',
                    'before': base_flow.get('to_node_name'),
                    'after': target_flow.get('to_node_name')
                })
            
        except Exception as e:
            logger.warning(f"Error comparing flow properties: {e}")
        
        return changes


class ProcessModelRenderer:
    """
    Renders process model data as HTML for display
    
    This class formats process model nodes, properties, and comparisons
    as HTML for display in the web interface. It provides structured,
    human-readable views of process model information.
    
    Requirements: 7.1, 7.2, 7.3, 7.4
    """
    
    def __init__(self):
        """Initialize ProcessModelRenderer"""
        pass
    
    def render_node_summary(self, node: Dict[str, Any]) -> str:
        """
        Render a single node as HTML summary
        
        Creates an HTML representation of a process model node with all
        its properties organized by category for easy reading.
        
        Requirements: 7.1, 7.2
        
        Args:
            node: Node dictionary containing all node information
            
        Returns:
            HTML string representing the node summary
        """
        try:
            import html
            
            # Extract node information
            node_name = html.escape(str(node.get('name', 'Unknown')))
            node_type = html.escape(str(node.get('type', 'UNKNOWN')))
            node_uuid = html.escape(str(node.get('uuid', '')))
            
            # Start building HTML
            html_parts = []
            
            # Node header
            html_parts.append(f'<div class="node-summary" data-node-uuid="{node_uuid}">')
            html_parts.append(f'  <div class="node-header">')
            html_parts.append(f'    <h4 class="node-name">{node_name}</h4>')
            html_parts.append(f'    <span class="node-type badge badge-info">{node_type}</span>')
            html_parts.append(f'  </div>')
            
            # Render property groups
            properties = node.get('properties', {})
            
            # Basic properties
            if properties.get('basic'):
                html_parts.append(self.render_property_group('Basic', properties['basic']))
            
            # Assignment properties
            if properties.get('assignment'):
                html_parts.append(self.render_property_group('Assignment', properties['assignment']))
            
            # Forms properties
            if properties.get('forms'):
                html_parts.append(self.render_property_group('Forms', properties['forms']))
            
            # Expressions properties
            if properties.get('expressions'):
                html_parts.append(self.render_property_group('Expressions', properties['expressions']))
            
            # Escalation properties
            if properties.get('escalation') and properties['escalation'].get('enabled'):
                html_parts.append(self.render_property_group('Escalation', properties['escalation']))
            
            # Dependencies
            dependencies = node.get('dependencies', {})
            if any(dependencies.get(dep_type) for dep_type in ['interfaces', 'rules', 'groups']):
                html_parts.append(self._render_dependencies(dependencies))
            
            html_parts.append('</div>')
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.error(f"Error rendering node summary: {e}", exc_info=True)
            return f'<div class="alert alert-danger">Error rendering node: {html.escape(str(e))}</div>'
    
    def render_property_group(
        self,
        group_name: str,
        properties: Dict[str, Any]
    ) -> str:
        """
        Render a property group as HTML
        
        Creates an HTML representation of a group of related properties
        (e.g., Basic, Assignment, Forms) with proper formatting and escaping.
        
        Requirements: 7.1, 7.2
        
        Args:
            group_name: Name of the property group (e.g., "Basic", "Assignment")
            properties: Dictionary of properties in this group
            
        Returns:
            HTML string representing the property group
        """
        try:
            import html
            
            # Filter out empty properties
            non_empty_props = {
                k: v for k, v in properties.items()
                if v is not None and v != '' and v != [] and v != {}
            }
            
            if not non_empty_props:
                return ''
            
            html_parts = []
            
            # Group header
            html_parts.append(f'  <div class="property-group">')
            html_parts.append(f'    <h5 class="property-group-name">{html.escape(group_name)}</h5>')
            html_parts.append(f'    <div class="property-list">')
            
            # Render each property
            for key, value in non_empty_props.items():
                # Format property name (convert snake_case to Title Case)
                prop_name = key.replace('_', ' ').title()
                
                # Format property value
                formatted_value = self._format_property_value(value)
                
                html_parts.append(f'      <div class="property-item">')
                html_parts.append(f'        <span class="property-name">{html.escape(prop_name)}:</span>')
                html_parts.append(f'        <span class="property-value">{formatted_value}</span>')
                html_parts.append(f'      </div>')
            
            html_parts.append(f'    </div>')
            html_parts.append(f'  </div>')
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.error(f"Error rendering property group: {e}", exc_info=True)
            return ''
    
    def render_node_comparison(
        self,
        base_node: Optional[Dict[str, Any]],
        target_node: Optional[Dict[str, Any]],
        changes: List[Dict[str, Any]]
    ) -> str:
        """
        Render a three-way node comparison as HTML
        
        Creates an HTML representation showing the differences between
        two versions of a node, highlighting changed properties with
        before and after values.
        
        Requirements: 7.3, 7.4
        
        Args:
            base_node: Node dictionary from base version (can be None if added)
            target_node: Node dictionary from target version (can be None if removed)
            changes: List of property changes with before/after values
            
        Returns:
            HTML string representing the node comparison
        """
        try:
            import html
            
            html_parts = []
            
            # Determine comparison type
            if base_node is None and target_node is not None:
                # Node was added
                comparison_type = 'added'
                node_name = html.escape(str(target_node.get('name', 'Unknown')))
                html_parts.append(f'<div class="node-comparison node-added">')
                html_parts.append(f'  <div class="comparison-header">')
                html_parts.append(f'    <h4>{node_name} <span class="badge badge-success">ADDED</span></h4>')
                html_parts.append(f'  </div>')
                html_parts.append(self.render_node_summary(target_node))
                html_parts.append('</div>')
                
            elif base_node is not None and target_node is None:
                # Node was removed
                comparison_type = 'removed'
                node_name = html.escape(str(base_node.get('name', 'Unknown')))
                html_parts.append(f'<div class="node-comparison node-removed">')
                html_parts.append(f'  <div class="comparison-header">')
                html_parts.append(f'    <h4>{node_name} <span class="badge badge-danger">REMOVED</span></h4>')
                html_parts.append(f'  </div>')
                html_parts.append(self.render_node_summary(base_node))
                html_parts.append('</div>')
                
            elif base_node is not None and target_node is not None:
                # Node was modified
                comparison_type = 'modified'
                node_name = html.escape(str(target_node.get('name', 'Unknown')))
                html_parts.append(f'<div class="node-comparison node-modified">')
                html_parts.append(f'  <div class="comparison-header">')
                html_parts.append(f'    <h4>{node_name} <span class="badge badge-warning">MODIFIED</span></h4>')
                html_parts.append(f'  </div>')
                
                # Render side-by-side comparison
                html_parts.append(f'  <div class="comparison-content">')
                html_parts.append(f'    <div class="row">')
                
                # Before column
                html_parts.append(f'      <div class="col-md-6">')
                html_parts.append(f'        <h5>Before</h5>')
                html_parts.append(self.render_node_summary(base_node))
                html_parts.append(f'      </div>')
                
                # After column
                html_parts.append(f'      <div class="col-md-6">')
                html_parts.append(f'        <h5>After</h5>')
                html_parts.append(self.render_node_summary(target_node))
                html_parts.append(f'      </div>')
                
                html_parts.append(f'    </div>')
                
                # Render changes summary
                if changes:
                    html_parts.append(self._render_changes_summary(changes))
                
                html_parts.append(f'  </div>')
                html_parts.append('</div>')
            
            else:
                # Invalid comparison
                return '<div class="alert alert-warning">Invalid node comparison</div>'
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.error(f"Error rendering node comparison: {e}", exc_info=True)
            return f'<div class="alert alert-danger">Error rendering comparison: {html.escape(str(e))}</div>'
    
    def _format_property_value(self, value: Any) -> str:
        """
        Format a property value for HTML display
        
        Converts various property value types (strings, lists, dicts, etc.)
        into properly formatted and escaped HTML.
        
        Args:
            value: Property value to format
            
        Returns:
            HTML-formatted string
        """
        import html
        
        try:
            if value is None:
                return '<span class="text-muted">None</span>'
            
            elif isinstance(value, bool):
                return '<span class="badge badge-secondary">' + str(value) + '</span>'
            
            elif isinstance(value, (int, float)):
                return html.escape(str(value))
            
            elif isinstance(value, str):
                # Escape HTML and preserve line breaks
                escaped = html.escape(value)
                # If it's a long expression, format it in a code block
                if len(escaped) > 100 or '\n' in escaped:
                    return f'<pre class="code-block">{escaped}</pre>'
                else:
                    return escaped
            
            elif isinstance(value, list):
                if not value:
                    return '<span class="text-muted">[]</span>'
                
                # Format list items
                items = []
                for item in value:
                    if isinstance(item, dict):
                        # For dependency objects, show name
                        item_name = item.get('name', str(item))
                        items.append(f'<li>{html.escape(str(item_name))}</li>')
                    else:
                        items.append(f'<li>{html.escape(str(item))}</li>')
                
                return '<ul class="property-list-value">' + ''.join(items) + '</ul>'
            
            elif isinstance(value, dict):
                if not value:
                    return '<span class="text-muted">{}</span>'
                
                # Format dict as nested properties
                items = []
                for k, v in value.items():
                    formatted_v = self._format_property_value(v)
                    items.append(f'<div><strong>{html.escape(str(k))}:</strong> {formatted_v}</div>')
                
                return '<div class="nested-properties">' + ''.join(items) + '</div>'
            
            else:
                return html.escape(str(value))
                
        except Exception as e:
            logger.warning(f"Error formatting property value: {e}")
            return html.escape(str(value))
    
    def _render_dependencies(self, dependencies: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Render node dependencies as HTML
        
        Args:
            dependencies: Dictionary of dependency lists by type
            
        Returns:
            HTML string representing dependencies
        """
        import html
        
        html_parts = []
        html_parts.append('  <div class="property-group">')
        html_parts.append('    <h5 class="property-group-name">Dependencies</h5>')
        html_parts.append('    <div class="property-list">')
        
        # Render each dependency type
        for dep_type, dep_list in dependencies.items():
            if dep_list:
                # Format dependency type name
                dep_type_name = dep_type.replace('_', ' ').title()
                
                # Create list of dependency names
                dep_names = [html.escape(dep.get('name', 'Unknown')) for dep in dep_list]
                
                html_parts.append('      <div class="property-item">')
                html_parts.append(f'        <span class="property-name">{dep_type_name}:</span>')
                html_parts.append('        <span class="property-value">')
                html_parts.append('          <ul class="dependency-list">')
                for name in dep_names:
                    html_parts.append(f'            <li>{name}</li>')
                html_parts.append('          </ul>')
                html_parts.append('        </span>')
                html_parts.append('      </div>')
        
        html_parts.append('    </div>')
        html_parts.append('  </div>')
        
        return '\n'.join(html_parts)
    
    def _render_changes_summary(self, changes: List[Dict[str, Any]]) -> str:
        """
        Render a summary of changes between node versions
        
        Args:
            changes: List of property changes
            
        Returns:
            HTML string representing changes summary
        """
        import html
        
        html_parts = []
        html_parts.append('    <div class="changes-summary">')
        html_parts.append('      <h5>Changes Summary</h5>')
        html_parts.append('      <table class="table table-sm table-bordered">')
        html_parts.append('        <thead>')
        html_parts.append('          <tr>')
        html_parts.append('            <th>Property</th>')
        html_parts.append('            <th>Before</th>')
        html_parts.append('            <th>After</th>')
        html_parts.append('          </tr>')
        html_parts.append('        </thead>')
        html_parts.append('        <tbody>')
        
        for change in changes:
            prop_name = html.escape(str(change.get('property', 'Unknown')))
            before_value = self._format_change_value(change.get('before'))
            after_value = self._format_change_value(change.get('after'))
            
            html_parts.append('          <tr>')
            html_parts.append(f'            <td><strong>{prop_name}</strong></td>')
            html_parts.append(f'            <td class="before-value">{before_value}</td>')
            html_parts.append(f'            <td class="after-value">{after_value}</td>')
            html_parts.append('          </tr>')
        
        html_parts.append('        </tbody>')
        html_parts.append('      </table>')
        html_parts.append('    </div>')
        
        return '\n'.join(html_parts)
    
    def _format_change_value(self, value: Any) -> str:
        """
        Format a change value for display in comparison table
        
        Args:
            value: Value to format
            
        Returns:
            HTML-formatted string
        """
        import html
        
        try:
            if value is None or value == '':
                return '<span class="text-muted">None</span>'
            
            elif isinstance(value, bool):
                return str(value)
            
            elif isinstance(value, (int, float)):
                return html.escape(str(value))
            
            elif isinstance(value, str):
                # Truncate long strings
                if len(value) > 100:
                    return html.escape(value[:100]) + '...'
                else:
                    return html.escape(value)
            
            elif isinstance(value, list):
                if not value:
                    return '<span class="text-muted">[]</span>'
                
                # Show count for lists
                return f'{len(value)} items'
            
            elif isinstance(value, dict):
                if not value:
                    return '<span class="text-muted">{}</span>'
                
                # Show count for dicts
                return f'{len(value)} properties'
            
            else:
                return html.escape(str(value))
                
        except Exception as e:
            logger.warning(f"Error formatting change value: {e}")
            return html.escape(str(value))



class FlowDiagramGenerator:
    """
    Generates flow diagram data for visual representation
    
    This class creates Mermaid.js compatible data structures from process
    model nodes and flows for visual flow diagram rendering. It handles
    node positioning, shape selection based on node type, and edge formatting.
    
    Requirements: 7.5, 7.6, 7.9
    """
    
    def __init__(self):
        """Initialize FlowDiagramGenerator"""
        # Map node types to Mermaid shapes
        self.node_shapes = {
            NodeType.USER_INPUT_TASK: ('rect', '[', ']'),  # Rectangle
            NodeType.SCRIPT_TASK: ('rect', '[', ']'),  # Rectangle
            NodeType.GATEWAY: ('diamond', '{', '}'),  # Diamond
            NodeType.SUBPROCESS: ('subroutine', '[[', ']]'),  # Subroutine
            NodeType.START_NODE: ('circle', '((', '))'),  # Circle
            NodeType.END_NODE: ('circle', '((', '))'),  # Circle
            NodeType.UNKNOWN: ('rect', '[', ']')  # Rectangle
        }
    
    def generate_diagram_data(
        self,
        nodes: List[Dict[str, Any]],
        flows: List[Dict[str, Any]],
        flow_graph: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate data structure for flow diagram visualization
        
        Creates a Mermaid.js compatible data structure from process model
        nodes and flows. The structure includes node definitions with
        appropriate shapes based on node type, and edge definitions with
        conditions.
        
        Requirements: 7.5, 7.6, 7.9
        
        Args:
            nodes: List of node dictionaries with complete node information
            flows: List of flow dictionaries with connection information
            flow_graph: Flow graph structure with start/end nodes
            
        Returns:
            Dictionary containing diagram data with structure:
            {
                'mermaid_syntax': str,  # Complete Mermaid.js syntax
                'nodes': [
                    {
                        'id': str,  # Node UUID (sanitized for Mermaid)
                        'label': str,  # Node name
                        'type': str,  # Node type
                        'shape': str,  # Mermaid shape type
                        'properties': {...}  # Full node properties
                    }
                ],
                'edges': [
                    {
                        'id': str,  # Flow UUID
                        'source': str,  # Source node ID
                        'target': str,  # Target node ID
                        'label': str,  # Condition or 'default'
                        'type': str  # 'default' or 'conditional'
                    }
                ],
                'start_nodes': [str],  # IDs of start nodes
                'end_nodes': [str]  # IDs of end nodes
            }
        """
        try:
            logger.info(f"Generating diagram data for {len(nodes)} nodes and {len(flows)} flows")
            
            # Generate node data
            diagram_nodes = []
            node_id_map = {}  # Map UUIDs to sanitized IDs
            
            for node in nodes:
                node_id = self._sanitize_id(node['uuid'])
                node_id_map[node['uuid']] = node_id
                
                # Determine node shape based on type
                node_type_enum = NodeType(node.get('type', 'UNKNOWN'))
                shape_info = self.node_shapes.get(node_type_enum, self.node_shapes[NodeType.UNKNOWN])
                
                diagram_node = {
                    'id': node_id,
                    'label': node.get('name', 'Unknown'),
                    'type': node.get('type', 'UNKNOWN'),
                    'shape': shape_info[0],
                    'shape_open': shape_info[1],
                    'shape_close': shape_info[2],
                    'properties': node.get('properties', {})
                }
                
                diagram_nodes.append(diagram_node)
            
            # Generate edge data
            diagram_edges = []
            
            for flow in flows:
                source_id = node_id_map.get(flow['from_node_uuid'])
                target_id = node_id_map.get(flow['to_node_uuid'])
                
                if not source_id or not target_id:
                    logger.warning(
                        f"Flow {flow['uuid']} references unknown nodes: "
                        f"{flow['from_node_uuid']} -> {flow['to_node_uuid']}"
                    )
                    continue
                
                # Create edge label from condition
                edge_label = flow.get('label', '')
                if not edge_label:
                    edge_label = 'default' if flow.get('is_default', True) else ''
                
                # Truncate long labels for diagram readability
                if len(edge_label) > 30:
                    edge_label = edge_label[:27] + '...'
                
                diagram_edge = {
                    'id': self._sanitize_id(flow['uuid']),
                    'source': source_id,
                    'target': target_id,
                    'label': edge_label,
                    'type': 'default' if flow.get('is_default', True) else 'conditional',
                    'condition': flow.get('condition', '')
                }
                
                diagram_edges.append(diagram_edge)
            
            # Get start and end nodes from flow graph
            start_node_ids = [
                node_id_map.get(uuid) for uuid in flow_graph.get('start_nodes', [])
                if uuid in node_id_map
            ]
            
            end_node_ids = [
                node_id_map.get(uuid) for uuid in flow_graph.get('end_nodes', [])
                if uuid in node_id_map
            ]
            
            # Generate Mermaid syntax
            mermaid_syntax = self._generate_mermaid_syntax(
                diagram_nodes,
                diagram_edges,
                start_node_ids,
                end_node_ids
            )
            
            diagram_data = {
                'mermaid_syntax': mermaid_syntax,
                'nodes': diagram_nodes,
                'edges': diagram_edges,
                'start_nodes': start_node_ids,
                'end_nodes': end_node_ids
            }
            
            logger.info(
                f"Generated diagram data: {len(diagram_nodes)} nodes, "
                f"{len(diagram_edges)} edges, {len(start_node_ids)} start nodes, "
                f"{len(end_node_ids)} end nodes"
            )
            
            return diagram_data
            
        except Exception as e:
            logger.error(f"Error generating diagram data: {e}", exc_info=True)
            # Return empty diagram data on error
            return {
                'mermaid_syntax': 'graph TD\n  Error[Error generating diagram]',
                'nodes': [],
                'edges': [],
                'start_nodes': [],
                'end_nodes': []
            }
    
    def _sanitize_id(self, uuid: str) -> str:
        """
        Sanitize UUID for use as Mermaid node ID
        
        Mermaid.js has restrictions on node IDs. This method converts
        UUIDs to valid Mermaid IDs by replacing invalid characters.
        
        Args:
            uuid: Original UUID string
            
        Returns:
            Sanitized ID string safe for Mermaid
        """
        # Replace hyphens and other special characters with underscores
        # Keep only alphanumeric and underscores
        import re
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', uuid)
        
        # Ensure it starts with a letter (Mermaid requirement)
        if sanitized and not sanitized[0].isalpha():
            sanitized = 'n' + sanitized
        
        return sanitized
    
    def _generate_mermaid_syntax(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        start_node_ids: List[str],
        end_node_ids: List[str]
    ) -> str:
        """
        Generate Mermaid.js syntax from diagram data
        
        Creates the complete Mermaid.js flowchart syntax string that can
        be rendered by the Mermaid.js library in the browser.
        
        Args:
            nodes: List of diagram node dictionaries
            edges: List of diagram edge dictionaries
            start_node_ids: List of start node IDs
            end_node_ids: List of end node IDs
            
        Returns:
            Complete Mermaid.js syntax string
        """
        try:
            lines = []
            
            # Start with flowchart declaration (TD = Top Down)
            lines.append('graph TD')
            
            # Add node definitions
            for node in nodes:
                node_id = node['id']
                label = node['label'].replace('"', '\\"')  # Escape quotes
                shape_open = node['shape_open']
                shape_close = node['shape_close']
                
                # Create node definition with shape
                node_def = f'  {node_id}{shape_open}"{label}"{shape_close}'
                lines.append(node_def)
                
                # Add styling for special nodes
                if node_id in start_node_ids:
                    lines.append(f'  style {node_id} fill:#90EE90')  # Light green
                elif node_id in end_node_ids:
                    lines.append(f'  style {node_id} fill:#FFB6C1')  # Light pink
            
            # Add edge definitions
            for edge in edges:
                source = edge['source']
                target = edge['target']
                label = edge['label'].replace('"', '\\"')  # Escape quotes
                
                # Choose arrow style based on edge type
                if edge['type'] == 'conditional':
                    # Conditional flow with label
                    if label:
                        edge_def = f'  {source} -->|"{label}"| {target}'
                    else:
                        edge_def = f'  {source} --> {target}'
                else:
                    # Default flow
                    if label and label != 'default':
                        edge_def = f'  {source} -->|"{label}"| {target}'
                    else:
                        edge_def = f'  {source} --> {target}'
                
                lines.append(edge_def)
            
            # Join all lines
            mermaid_syntax = '\n'.join(lines)
            
            return mermaid_syntax
            
        except Exception as e:
            logger.error(f"Error generating Mermaid syntax: {e}", exc_info=True)
            return 'graph TD\n  Error[Error generating syntax]'
    
    def generate_comparison_diagram(
        self,
        base_diagram: Dict[str, Any],
        target_diagram: Dict[str, Any],
        node_changes: Dict[str, Any],
        flow_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate diagram with change highlighting for comparison view
        
        Creates a flow diagram that highlights changes between two versions
        of a process model. Added nodes are shown in green, removed nodes
        in red, and modified nodes in yellow.
        
        Requirements: 7.7
        
        Args:
            base_diagram: Diagram data from base version
            target_diagram: Diagram data from target version
            node_changes: Node comparison results with added/removed/modified
            flow_changes: Flow comparison results
            
        Returns:
            Dictionary containing comparison diagram data with structure:
            {
                'mermaid_syntax': str,  # Mermaid syntax with change highlighting
                'nodes': [...],  # All nodes with change_type annotation
                'edges': [...],  # All edges with change_type annotation
                'changes_summary': {
                    'nodes_added': int,
                    'nodes_removed': int,
                    'nodes_modified': int,
                    'flows_added': int,
                    'flows_removed': int,
                    'flows_modified': int
                }
            }
        """
        try:
            logger.info("Generating comparison diagram with change highlighting")
            
            # Create sets of node UUIDs by change type
            added_node_uuids = {node['uuid'] for node in node_changes.get('added', [])}
            removed_node_uuids = {node['uuid'] for node in node_changes.get('removed', [])}
            modified_node_uuids = {
                mod['node']['uuid'] for mod in node_changes.get('modified', [])
            }
            
            # Create sets of flow keys by change type
            def flow_key(flow):
                return (flow['from_node_uuid'], flow['to_node_uuid'])
            
            added_flow_keys = {
                flow_key(flow) for flow in flow_changes.get('added_flows', [])
            }
            removed_flow_keys = {
                flow_key(flow) for flow in flow_changes.get('removed_flows', [])
            }
            modified_flow_keys = {
                flow_key(mod['flow']) for mod in flow_changes.get('modified_flows', [])
            }
            
            # Combine nodes from both versions
            all_nodes = []
            processed_uuids = set()
            
            # Add target nodes (added and modified)
            for node in target_diagram.get('nodes', []):
                # Find original UUID from node properties
                original_uuid = self._find_original_uuid(node, target_diagram)
                
                if original_uuid in added_node_uuids:
                    node['change_type'] = 'ADDED'
                    node['change_color'] = '#90EE90'  # Light green
                elif original_uuid in modified_node_uuids:
                    node['change_type'] = 'MODIFIED'
                    node['change_color'] = '#FFD700'  # Gold/yellow
                else:
                    node['change_type'] = 'UNCHANGED'
                    node['change_color'] = None
                
                all_nodes.append(node)
                processed_uuids.add(original_uuid)
            
            # Add removed nodes from base
            for node in base_diagram.get('nodes', []):
                original_uuid = self._find_original_uuid(node, base_diagram)
                
                if original_uuid in removed_node_uuids and original_uuid not in processed_uuids:
                    node['change_type'] = 'REMOVED'
                    node['change_color'] = '#FFB6C1'  # Light red/pink
                    all_nodes.append(node)
                    processed_uuids.add(original_uuid)
            
            # Combine edges from both versions
            all_edges = []
            processed_flow_keys = set()
            
            # Add target edges (added and modified)
            for edge in target_diagram.get('edges', []):
                # Reconstruct flow key from edge
                edge_key = self._edge_to_flow_key(edge, target_diagram)
                
                if edge_key in added_flow_keys:
                    edge['change_type'] = 'ADDED'
                    edge['change_style'] = 'stroke:#90EE90,stroke-width:3px'
                elif edge_key in modified_flow_keys:
                    edge['change_type'] = 'MODIFIED'
                    edge['change_style'] = 'stroke:#FFD700,stroke-width:3px'
                else:
                    edge['change_type'] = 'UNCHANGED'
                    edge['change_style'] = None
                
                all_edges.append(edge)
                processed_flow_keys.add(edge_key)
            
            # Add removed edges from base
            for edge in base_diagram.get('edges', []):
                edge_key = self._edge_to_flow_key(edge, base_diagram)
                
                if edge_key in removed_flow_keys and edge_key not in processed_flow_keys:
                    edge['change_type'] = 'REMOVED'
                    edge['change_style'] = 'stroke:#FFB6C1,stroke-width:3px,stroke-dasharray: 5 5'
                    all_edges.append(edge)
                    processed_flow_keys.add(edge_key)
            
            # Generate Mermaid syntax with change highlighting
            mermaid_syntax = self._generate_comparison_mermaid_syntax(all_nodes, all_edges)
            
            # Create changes summary
            changes_summary = {
                'nodes_added': len(added_node_uuids),
                'nodes_removed': len(removed_node_uuids),
                'nodes_modified': len(modified_node_uuids),
                'flows_added': len(added_flow_keys),
                'flows_removed': len(removed_flow_keys),
                'flows_modified': len(modified_flow_keys)
            }
            
            comparison_diagram = {
                'mermaid_syntax': mermaid_syntax,
                'nodes': all_nodes,
                'edges': all_edges,
                'changes_summary': changes_summary
            }
            
            logger.info(
                f"Generated comparison diagram: "
                f"{changes_summary['nodes_added']} nodes added, "
                f"{changes_summary['nodes_removed']} nodes removed, "
                f"{changes_summary['nodes_modified']} nodes modified"
            )
            
            return comparison_diagram
            
        except Exception as e:
            logger.error(f"Error generating comparison diagram: {e}", exc_info=True)
            # Return empty comparison diagram on error
            return {
                'mermaid_syntax': 'graph TD\n  Error[Error generating comparison diagram]',
                'nodes': [],
                'edges': [],
                'changes_summary': {
                    'nodes_added': 0,
                    'nodes_removed': 0,
                    'nodes_modified': 0,
                    'flows_added': 0,
                    'flows_removed': 0,
                    'flows_modified': 0
                }
            }
    
    def _find_original_uuid(
        self,
        node: Dict[str, Any],
        diagram: Dict[str, Any]
    ) -> str:
        """
        Find the original UUID for a diagram node
        
        Diagram nodes use sanitized IDs, this method finds the original
        UUID from the node properties or by reverse lookup.
        
        Args:
            node: Diagram node dictionary
            diagram: Complete diagram data
            
        Returns:
            Original UUID string
        """
        # Try to get UUID from properties if available
        if 'uuid' in node:
            return node['uuid']
        
        # Otherwise, try to find it in the original nodes list
        # This is a fallback and may not always work
        node_id = node.get('id', '')
        
        # Look through all nodes in the diagram to find matching ID
        for n in diagram.get('nodes', []):
            if n.get('id') == node_id and 'uuid' in n.get('properties', {}):
                return n['properties']['uuid']
        
        # If all else fails, return the sanitized ID
        return node_id
    
    def _edge_to_flow_key(
        self,
        edge: Dict[str, Any],
        diagram: Dict[str, Any]
    ) -> tuple:
        """
        Convert an edge to a flow key for comparison
        
        Args:
            edge: Diagram edge dictionary
            diagram: Complete diagram data
            
        Returns:
            Tuple of (from_uuid, to_uuid)
        """
        # Get source and target node IDs
        source_id = edge.get('source', '')
        target_id = edge.get('target', '')
        
        # Find original UUIDs for these nodes
        source_uuid = source_id
        target_uuid = target_id
        
        for node in diagram.get('nodes', []):
            if node.get('id') == source_id:
                source_uuid = self._find_original_uuid(node, diagram)
            if node.get('id') == target_id:
                target_uuid = self._find_original_uuid(node, diagram)
        
        return (source_uuid, target_uuid)
    
    def _generate_comparison_mermaid_syntax(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> str:
        """
        Generate Mermaid syntax with change highlighting
        
        Creates Mermaid.js syntax that includes color coding for added,
        removed, and modified nodes and flows.
        
        Args:
            nodes: List of nodes with change_type annotations
            edges: List of edges with change_type annotations
            
        Returns:
            Mermaid.js syntax string with change highlighting
        """
        try:
            lines = []
            
            # Start with flowchart declaration
            lines.append('graph TD')
            
            # Add node definitions with change highlighting
            for node in nodes:
                node_id = node['id']
                label = node['label'].replace('"', '\\"')
                shape_open = node.get('shape_open', '[')
                shape_close = node.get('shape_close', ']')
                
                # Create node definition
                node_def = f'  {node_id}{shape_open}"{label}"{shape_close}'
                lines.append(node_def)
                
                # Add styling based on change type
                change_color = node.get('change_color')
                if change_color:
                    lines.append(f'  style {node_id} fill:{change_color}')
            
            # Add edge definitions with change highlighting
            for edge in edges:
                source = edge['source']
                target = edge['target']
                label = edge.get('label', '').replace('"', '\\"')
                
                # Create edge definition
                if label and label != 'default':
                    edge_def = f'  {source} -->|"{label}"| {target}'
                else:
                    edge_def = f'  {source} --> {target}'
                
                lines.append(edge_def)
                
                # Note: Mermaid.js doesn't support per-edge styling directly
                # Edge styling would need to be handled differently in the UI
            
            # Add legend
            lines.append('')
            lines.append('  %% Legend')
            lines.append('  Legend["Legend"]')
            lines.append('  Added["Added"]')
            lines.append('  Modified["Modified"]')
            lines.append('  Removed["Removed"]')
            lines.append('  style Added fill:#90EE90')
            lines.append('  style Modified fill:#FFD700')
            lines.append('  style Removed fill:#FFB6C1')
            
            mermaid_syntax = '\n'.join(lines)
            
            return mermaid_syntax
            
        except Exception as e:
            logger.error(f"Error generating comparison Mermaid syntax: {e}", exc_info=True)
            return 'graph TD\n  Error[Error generating comparison syntax]'

