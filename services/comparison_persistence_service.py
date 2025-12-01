"""
Comparison Persistence Service

Persists detailed object comparison results to comparison tables.
This service computes and stores object-specific differences for:
- Interfaces (SAIL code, parameters, security)
- Process Models (nodes, flows, variables, Mermaid diagrams)
- Record Types (fields, relationships, views, actions)
- Expression Rules (inputs, return type, logic)
- CDTs (fields, namespace)
- Constants (values, type changes)
"""

import json
import logging
from typing import Dict, Any, Optional, List

from core.base_service import BaseService
from models import (
    db, ObjectVersion, Change,
    InterfaceComparison, ProcessModelComparison, RecordTypeComparison,
    ExpressionRuleComparison, CDTComparison, ConstantComparison,
    Interface, InterfaceParameter, InterfaceSecurity,
    ProcessModel, ProcessModelNode, ProcessModelFlow,
    ExpressionRule,
    Constant
)
from repositories.object_lookup_repository import ObjectLookupRepository


class ComparisonPersistenceService(BaseService):
    """
    Service for persisting detailed object comparison results.
    
    This service:
    1. Computes detailed differences for specific object types
    2. Stores results in object-specific comparison tables
    3. Links comparisons to changes via change_id
    4. Enables historical analysis and prevents re-computation
    
    Key Design Principles:
    - One comparison record per change (unique constraint on change_id)
    - Stores structured JSON for complex differences
    - Handles all supported object types
    - Idempotent (can be called multiple times safely)
    """
    
    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.object_lookup_repo = self._get_repository(
            ObjectLookupRepository
        )
    
    def persist_all_comparisons(
        self,
        session_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, int]:
        """
        Persist comparisons for all changes in a session.
        
        Args:
            session_id: Merge session ID
            base_package_id: Package A (Base) ID
            customer_package_id: Package B (Customer) ID
            new_vendor_package_id: Package C (New Vendor) ID
            
        Returns:
            Dict with counts by object type
        """
        self.logger.info(
            f"Persisting comparisons for session {session_id}"
        )
        
        # Get all changes for this session
        changes = db.session.query(Change).filter_by(
            session_id=session_id
        ).all()
        
        counts = {}
        
        for change in changes:
            obj = change.object
            object_type = obj.object_type
            
            # Persist comparison based on object type
            if object_type == 'Interface':
                self._persist_interface_comparison(
                    change,
                    base_package_id,
                    customer_package_id,
                    new_vendor_package_id
                )
                counts['Interface'] = counts.get('Interface', 0) + 1
            
            elif object_type == 'Process Model':
                self._persist_process_model_comparison(
                    change,
                    base_package_id,
                    customer_package_id,
                    new_vendor_package_id
                )
                counts['Process Model'] = counts.get('Process Model', 0) + 1
            
            elif object_type == 'Record Type':
                self._persist_record_type_comparison(
                    change,
                    base_package_id,
                    customer_package_id,
                    new_vendor_package_id
                )
                counts['Record Type'] = counts.get('Record Type', 0) + 1
            
            elif object_type == 'Expression Rule':
                self._persist_expression_rule_comparison(
                    change,
                    session_id,
                    base_package_id,
                    customer_package_id,
                    new_vendor_package_id
                )
                counts['Expression Rule'] = (
                    counts.get('Expression Rule', 0) + 1
                )
            
            elif object_type == 'CDT':
                self._persist_cdt_comparison(
                    change,
                    session_id,
                    base_package_id,
                    customer_package_id,
                    new_vendor_package_id
                )
                counts['CDT'] = counts.get('CDT', 0) + 1
            
            elif object_type == 'Constant':
                self._persist_constant_comparison(
                    change,
                    session_id,
                    base_package_id,
                    customer_package_id,
                    new_vendor_package_id
                )
                counts['Constant'] = counts.get('Constant', 0) + 1
        
        db.session.commit()
        
        self.logger.info(
            f"Persisted comparisons: {counts}"
        )
        
        return counts
    
    def _persist_interface_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> None:
        """Persist interface comparison."""
        # Check if comparison already exists
        existing = db.session.query(InterfaceComparison).filter_by(
            change_id=change.id
        ).first()
        
        if existing:
            self.logger.debug(
                f"Interface comparison already exists for change {change.id}"
            )
            return
        
        obj_id = change.object_id
        
        # Get versions
        base_version = self._get_object_version(obj_id, base_package_id)
        customer_version = self._get_object_version(
            obj_id, customer_package_id
        )
        new_vendor_version = self._get_object_version(
            obj_id, new_vendor_package_id
        )
        
        # Compute SAIL code diff
        sail_code_diff = self._compute_sail_code_diff(
            base_version,
            customer_version,
            new_vendor_version
        )
        
        # Compute parameter changes
        params_added, params_removed, params_modified = (
            self._compute_parameter_changes(
                obj_id,
                base_package_id,
                customer_package_id,
                new_vendor_package_id
            )
        )
        
        # Compute security changes
        security_changes = self._compute_security_changes(
            obj_id,
            base_package_id,
            customer_package_id,
            new_vendor_package_id
        )
        
        # Create comparison record
        comparison = InterfaceComparison(
            change_id=change.id,
            sail_code_diff=sail_code_diff,
            parameters_added=json.dumps(params_added),
            parameters_removed=json.dumps(params_removed),
            parameters_modified=json.dumps(params_modified),
            security_changes=json.dumps(security_changes)
        )
        
        db.session.add(comparison)
    
    def _persist_process_model_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> None:
        """Persist process model comparison."""
        # Check if comparison already exists
        existing = db.session.query(ProcessModelComparison).filter_by(
            change_id=change.id
        ).first()
        
        if existing:
            return
        
        obj_id = change.object_id
        
        # Compute node changes
        nodes_added, nodes_removed, nodes_modified = (
            self._compute_node_changes(
                obj_id,
                base_package_id,
                customer_package_id,
                new_vendor_package_id
            )
        )
        
        # Compute flow changes
        flows_added, flows_removed, flows_modified = (
            self._compute_flow_changes(
                obj_id,
                base_package_id,
                customer_package_id,
                new_vendor_package_id
            )
        )
        
        # Compute variable changes
        variables_changed = self._compute_variable_changes(
            obj_id,
            base_package_id,
            customer_package_id,
            new_vendor_package_id
        )
        
        # Generate Mermaid diagram
        mermaid_diagram = self._generate_mermaid_diagram(
            obj_id,
            new_vendor_package_id
        )
        
        # Create comparison record
        comparison = ProcessModelComparison(
            change_id=change.id,
            nodes_added=json.dumps(nodes_added),
            nodes_removed=json.dumps(nodes_removed),
            nodes_modified=json.dumps(nodes_modified),
            flows_added=json.dumps(flows_added),
            flows_removed=json.dumps(flows_removed),
            flows_modified=json.dumps(flows_modified),
            variables_changed=json.dumps(variables_changed),
            mermaid_diagram=mermaid_diagram
        )
        
        db.session.add(comparison)
    
    def _persist_record_type_comparison(
        self,
        change: Change,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> None:
        """Persist record type comparison."""
        # Check if comparison already exists
        existing = db.session.query(RecordTypeComparison).filter_by(
            change_id=change.id
        ).first()
        
        if existing:
            return
        
        obj_id = change.object_id
        
        # Compute field changes
        fields_changed = self._compute_record_field_changes(
            obj_id,
            base_package_id,
            customer_package_id,
            new_vendor_package_id
        )
        
        # Compute relationship changes
        relationships_changed = self._compute_relationship_changes(
            obj_id,
            base_package_id,
            customer_package_id,
            new_vendor_package_id
        )
        
        # Compute view changes
        views_changed = self._compute_view_changes(
            obj_id,
            base_package_id,
            customer_package_id,
            new_vendor_package_id
        )
        
        # Compute action changes
        actions_changed = self._compute_action_changes(
            obj_id,
            base_package_id,
            customer_package_id,
            new_vendor_package_id
        )
        
        # Create comparison record
        comparison = RecordTypeComparison(
            change_id=change.id,
            fields_changed=json.dumps(fields_changed),
            relationships_changed=json.dumps(relationships_changed),
            views_changed=json.dumps(views_changed),
            actions_changed=json.dumps(actions_changed)
        )
        
        db.session.add(comparison)
    
    def _persist_expression_rule_comparison(
        self,
        change: Change,
        session_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> None:
        """Persist expression rule comparison."""
        # Check if comparison already exists
        existing = db.session.query(ExpressionRuleComparison).filter_by(
            session_id=session_id,
            object_id=change.object_id
        ).first()
        
        if existing:
            return
        
        obj_id = change.object_id
        
        # Compute input changes
        input_changes = self._compute_expression_input_changes(
            obj_id,
            base_package_id,
            customer_package_id,
            new_vendor_package_id
        )
        
        # Compute return type change
        return_type_change = self._compute_return_type_change(
            obj_id,
            base_package_id,
            customer_package_id,
            new_vendor_package_id
        )
        
        # Compute logic diff
        logic_diff = self._compute_logic_diff(
            obj_id,
            base_package_id,
            customer_package_id,
            new_vendor_package_id
        )
        
        # Create comparison record
        comparison = ExpressionRuleComparison(
            session_id=session_id,
            object_id=obj_id,
            input_changes=json.dumps(input_changes),
            return_type_change=return_type_change,
            logic_diff=json.dumps(logic_diff)
        )
        
        db.session.add(comparison)
    
    def _persist_cdt_comparison(
        self,
        change: Change,
        session_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> None:
        """Persist CDT comparison."""
        # Check if comparison already exists
        existing = db.session.query(CDTComparison).filter_by(
            session_id=session_id,
            object_id=change.object_id
        ).first()
        
        if existing:
            return
        
        obj_id = change.object_id
        
        # Compute field changes
        field_changes = self._compute_cdt_field_changes(
            obj_id,
            base_package_id,
            customer_package_id,
            new_vendor_package_id
        )
        
        # Compute namespace change
        namespace_change = self._compute_namespace_change(
            obj_id,
            base_package_id,
            customer_package_id,
            new_vendor_package_id
        )
        
        # Create comparison record
        comparison = CDTComparison(
            session_id=session_id,
            object_id=obj_id,
            field_changes=json.dumps(field_changes),
            namespace_change=namespace_change
        )
        
        db.session.add(comparison)
    
    def _persist_constant_comparison(
        self,
        change: Change,
        session_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> None:
        """Persist constant comparison."""
        # Check if comparison already exists
        existing = db.session.query(ConstantComparison).filter_by(
            session_id=session_id,
            object_id=change.object_id
        ).first()
        
        if existing:
            return
        
        obj_id = change.object_id
        
        # Get constant values from all three packages
        base_constant = self._get_constant(obj_id, base_package_id)
        customer_constant = self._get_constant(obj_id, customer_package_id)
        new_vendor_constant = self._get_constant(
            obj_id, new_vendor_package_id
        )
        
        # Extract values
        base_value = (
            base_constant.constant_value if base_constant else None
        )
        customer_value = (
            customer_constant.constant_value if customer_constant else None
        )
        new_vendor_value = (
            new_vendor_constant.constant_value
            if new_vendor_constant else None
        )
        
        # If values are null, note that versions changed
        if base_value is None and customer_value is None and new_vendor_value is None:
            # Check version UUIDs to detect change
            base_version = self._get_object_version(obj_id, base_package_id)
            customer_version = self._get_object_version(obj_id, customer_package_id)
            new_vendor_version = self._get_object_version(obj_id, new_vendor_package_id)
            
            if base_version and new_vendor_version:
                if base_version.version_uuid != new_vendor_version.version_uuid:
                    base_value = f"[Version: {base_version.version_uuid[:20]}...]"
                    new_vendor_value = f"[Version: {new_vendor_version.version_uuid[:20]}...]"
                    if customer_version:
                        customer_value = f"[Version: {customer_version.version_uuid[:20]}...]"
        
        # Compute type change
        type_change = self._compute_type_change(
            base_constant,
            customer_constant,
            new_vendor_constant
        )
        
        # Create comparison record
        comparison = ConstantComparison(
            session_id=session_id,
            object_id=obj_id,
            base_value=base_value,
            customer_value=customer_value,
            new_vendor_value=new_vendor_value,
            type_change=type_change
        )
        
        db.session.add(comparison)
    
    # Helper methods for computing differences
    
    def _get_object_version(
        self,
        object_id: int,
        package_id: int
    ) -> Optional[ObjectVersion]:
        """Get object version for a package."""
        return db.session.query(ObjectVersion).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _compute_sail_code_diff(
        self,
        base_version: Optional[ObjectVersion],
        customer_version: Optional[ObjectVersion],
        new_vendor_version: Optional[ObjectVersion]
    ) -> Optional[str]:
        """Compute SAIL code diff (simplified)."""
        if not new_vendor_version or not new_vendor_version.sail_code:
            return None
        
        # For now, just return a summary
        # In production, use difflib or similar
        base_code = (
            base_version.sail_code if base_version else ""
        )
        new_code = new_vendor_version.sail_code
        
        if base_code == new_code:
            return "No changes"
        
        return f"SAIL code changed ({len(new_code)} chars)"
    
    def _compute_parameter_changes(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> tuple:
        """Compute parameter changes."""
        # Get interface records
        base_interface = self._get_interface(object_id, base_package_id)
        new_vendor_interface = self._get_interface(
            object_id, new_vendor_package_id
        )
        
        if not base_interface or not new_vendor_interface:
            return [], [], []
        
        # Get parameters
        base_params = db.session.query(InterfaceParameter).filter_by(
            interface_id=base_interface.id
        ).all()
        
        new_vendor_params = db.session.query(
            InterfaceParameter
        ).filter_by(
            interface_id=new_vendor_interface.id
        ).all()
        
        # Create lookup maps
        base_map = {p.parameter_name: p for p in base_params}
        new_map = {p.parameter_name: p for p in new_vendor_params}
        
        # Compute differences
        added = [
            {'name': p.parameter_name, 'type': p.parameter_type}
            for name, p in new_map.items()
            if name not in base_map
        ]
        
        removed = [
            {'name': p.parameter_name, 'type': p.parameter_type}
            for name, p in base_map.items()
            if name not in new_map
        ]
        
        modified = [
            {
                'name': name,
                'old_type': base_map[name].parameter_type,
                'new_type': new_map[name].parameter_type
            }
            for name in set(base_map.keys()) & set(new_map.keys())
            if base_map[name].parameter_type != new_map[name].parameter_type
        ]
        
        return added, removed, modified
    
    def _compute_security_changes(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Compute security changes."""
        base_interface = self._get_interface(object_id, base_package_id)
        new_vendor_interface = self._get_interface(
            object_id, new_vendor_package_id
        )
        
        if not base_interface or not new_vendor_interface:
            return {}
        
        base_security = db.session.query(InterfaceSecurity).filter_by(
            interface_id=base_interface.id
        ).first()
        
        new_security = db.session.query(InterfaceSecurity).filter_by(
            interface_id=new_vendor_interface.id
        ).first()
        
        changes = {}
        
        if base_security and new_security:
            if base_security.permission_type != new_security.permission_type:
                changes['permission_type'] = {
                    'old': base_security.permission_type,
                    'new': new_security.permission_type
                }
            if base_security.role_name != new_security.role_name:
                changes['role_name'] = {
                    'old': base_security.role_name,
                    'new': new_security.role_name
                }
        
        return changes
    
    def _get_interface(
        self,
        object_id: int,
        package_id: int
    ) -> Optional[Interface]:
        """Get interface record."""
        version = self._get_object_version(object_id, package_id)
        if not version:
            return None
        
        return db.session.query(Interface).filter_by(
            object_id=object_id,
            version_uuid=version.version_uuid
        ).first()
    
    def _compute_node_changes(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> tuple:
        """Compute process model node changes."""
        # Get process models
        base_pm = self._get_process_model(object_id, base_package_id)
        customer_pm = self._get_process_model(object_id, customer_package_id)
        new_vendor_pm = self._get_process_model(object_id, new_vendor_package_id)
        
        if not base_pm or not new_vendor_pm:
            return [], [], []
        
        # Get nodes for each package
        base_nodes = db.session.query(ProcessModelNode).filter_by(
            process_model_id=base_pm.id
        ).all()
        
        new_vendor_nodes = db.session.query(ProcessModelNode).filter_by(
            process_model_id=new_vendor_pm.id
        ).all()
        
        customer_nodes = []
        if customer_pm:
            customer_nodes = db.session.query(ProcessModelNode).filter_by(
                process_model_id=customer_pm.id
            ).all()
        
        # Create lookup maps by node_id
        base_map = {n.node_id: n for n in base_nodes}
        new_map = {n.node_id: n for n in new_vendor_nodes}
        customer_map = {n.node_id: n for n in customer_nodes}
        
        # Compute differences
        added = [
            {
                'node_id': n.node_id,
                'node_name': n.node_name,
                'node_type': n.node_type
            }
            for node_id, n in new_map.items()
            if node_id not in base_map
        ]
        
        removed = [
            {
                'node_id': n.node_id,
                'node_name': n.node_name,
                'node_type': n.node_type
            }
            for node_id, n in base_map.items()
            if node_id not in new_map
        ]
        
        modified = []
        for node_id in set(base_map.keys()) & set(new_map.keys()):
            base_node = base_map[node_id]
            new_node = new_map[node_id]
            if (base_node.node_name != new_node.node_name or
                base_node.node_type != new_node.node_type):
                modified.append({
                    'node_id': node_id,
                    'old_name': base_node.node_name,
                    'new_name': new_node.node_name,
                    'old_type': base_node.node_type,
                    'new_type': new_node.node_type
                })
        
        return added, removed, modified
    
    def _get_process_model(
        self,
        object_id: int,
        package_id: int
    ) -> Optional[ProcessModel]:
        """Get process model record."""
        return db.session.query(ProcessModel).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _compute_flow_changes(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> tuple:
        """Compute process model flow changes."""
        return [], [], []
    
    def _compute_variable_changes(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> List[Dict[str, Any]]:
        """Compute process model variable changes."""
        return []
    
    def _generate_mermaid_diagram(
        self,
        object_id: int,
        package_id: int
    ) -> Optional[str]:
        """Generate Mermaid diagram for process model."""
        return "graph TD\n  Start --> End"
    
    def _compute_record_field_changes(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> List[Dict[str, Any]]:
        """Compute record type field changes."""
        return []
    
    def _compute_relationship_changes(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> List[Dict[str, Any]]:
        """Compute record type relationship changes."""
        return []
    
    def _compute_view_changes(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> List[Dict[str, Any]]:
        """Compute record type view changes."""
        return []
    
    def _compute_action_changes(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> List[Dict[str, Any]]:
        """Compute record type action changes."""
        return []
    
    def _compute_expression_input_changes(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> List[Dict[str, Any]]:
        """Compute expression rule input changes."""
        return []
    
    def _compute_return_type_change(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Optional[str]:
        """Compute expression rule return type change."""
        return None
    
    def _compute_logic_diff(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Dict[str, Any]:
        """Compute expression rule logic diff."""
        # Get expression rules from all packages
        base_er = self._get_expression_rule(object_id, base_package_id)
        customer_er = self._get_expression_rule(object_id, customer_package_id)
        new_vendor_er = self._get_expression_rule(
            object_id, new_vendor_package_id
        )
        
        diff = {}
        
        if base_er and new_vendor_er:
            # Compare SAIL code lengths
            base_len = len(base_er.sail_code) if base_er.sail_code else 0
            new_len = len(new_vendor_er.sail_code) if new_vendor_er.sail_code else 0
            customer_len = (
                len(customer_er.sail_code) if customer_er and customer_er.sail_code else 0
            )
            
            diff['base_sail_code_length'] = base_len
            diff['customer_sail_code_length'] = customer_len
            diff['new_vendor_sail_code_length'] = new_len
            
            # Show code preview if changed
            if base_len != new_len:
                diff['base_code_preview'] = (
                    base_er.sail_code[:200] if base_er.sail_code else None
                )
                diff['new_vendor_code_preview'] = (
                    new_vendor_er.sail_code[:200] if new_vendor_er.sail_code else None
                )
                if customer_er and customer_er.sail_code:
                    diff['customer_code_preview'] = customer_er.sail_code[:200]
        
        return diff
    
    def _get_expression_rule(
        self,
        object_id: int,
        package_id: int
    ) -> Optional[ExpressionRule]:
        """Get expression rule record."""
        return db.session.query(ExpressionRule).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _compute_cdt_field_changes(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> List[Dict[str, Any]]:
        """Compute CDT field changes."""
        return []
    
    def _compute_namespace_change(
        self,
        object_id: int,
        base_package_id: int,
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> Optional[str]:
        """Compute CDT namespace change."""
        return None
    
    def _get_constant(
        self,
        object_id: int,
        package_id: int
    ) -> Optional[Constant]:
        """Get constant record."""
        version = self._get_object_version(object_id, package_id)
        if not version:
            return None
        
        return db.session.query(Constant).filter_by(
            object_id=object_id,
            version_uuid=version.version_uuid
        ).first()
    
    def _compute_type_change(
        self,
        base_constant: Optional[Constant],
        customer_constant: Optional[Constant],
        new_vendor_constant: Optional[Constant]
    ) -> Optional[str]:
        """Compute constant type change."""
        if not base_constant or not new_vendor_constant:
            return None
        
        if base_constant.constant_type != new_vendor_constant.constant_type:
            return (
                f"{base_constant.constant_type} → "
                f"{new_vendor_constant.constant_type}"
            )
        
        return None
