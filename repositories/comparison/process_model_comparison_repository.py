"""
Process Model Comparison Repository

Provides data access for Process Model comparison results.
Stores detailed differences including nodes, flows, variables,
and Mermaid diagrams.
"""

import json
from typing import Optional, Dict, Any, List
from models import ProcessModelComparison
from repositories.base_repository import BaseRepository


class ProcessModelComparisonRepository(
    BaseRepository[ProcessModelComparison]
):
    """
    Repository for ProcessModelComparison entities.

    Manages comparison results for Process Model objects, storing detailed
    differences between versions including nodes, flows, variables, and
    visual diagrams.

    Key Methods:
        - create_comparison: Create comparison with all difference data
        - get_by_change_id: Get comparison by change ID
        - update_comparison: Update existing comparison
    """

    def __init__(self):
        """Initialize repository with ProcessModelComparison model."""
        super().__init__(ProcessModelComparison)

    def create_comparison(
        self,
        change_id: int,
        nodes_added: Optional[List[Dict[str, Any]]] = None,
        nodes_removed: Optional[List[Dict[str, Any]]] = None,
        nodes_modified: Optional[List[Dict[str, Any]]] = None,
        flows_added: Optional[List[Dict[str, Any]]] = None,
        flows_removed: Optional[List[Dict[str, Any]]] = None,
        flows_modified: Optional[List[Dict[str, Any]]] = None,
        variables_changed: Optional[List[Dict[str, Any]]] = None,
        mermaid_diagram: Optional[str] = None
    ) -> ProcessModelComparison:
        """
        Create process model comparison with difference data.

        Args:
            change_id: Reference to changes table
            nodes_added: List of added nodes
            nodes_removed: List of removed nodes
            nodes_modified: List of modified nodes
            flows_added: List of added flows
            flows_removed: List of removed flows
            flows_modified: List of modified flows
            variables_changed: List of variable changes
            mermaid_diagram: Mermaid diagram syntax for visualization

        Returns:
            Created ProcessModelComparison object

        Example:
            >>> comparison = repo.create_comparison(
            ...     change_id=42,
            ...     nodes_added=[
            ...         {
            ...             "node_id": "node_5",
            ...             "node_type": "SCRIPT_TASK",
            ...             "node_name": "Calculate Total"
            ...         }
            ...     ],
            ...     flows_added=[
            ...         {
            ...             "from_node_id": "node_4",
            ...             "to_node_id": "node_5",
            ...             "flow_label": "Success"
            ...         }
            ...     ],
            ...     mermaid_diagram="graph TD\\n  A-->B"
            ... )
        """
        comparison = ProcessModelComparison(
            change_id=change_id,
            nodes_added=json.dumps(nodes_added) if nodes_added else None,
            nodes_removed=json.dumps(nodes_removed)
            if nodes_removed else None,
            nodes_modified=json.dumps(nodes_modified)
            if nodes_modified else None,
            flows_added=json.dumps(flows_added) if flows_added else None,
            flows_removed=json.dumps(flows_removed)
            if flows_removed else None,
            flows_modified=json.dumps(flows_modified)
            if flows_modified else None,
            variables_changed=json.dumps(variables_changed)
            if variables_changed else None,
            mermaid_diagram=mermaid_diagram
        )

        self.db.session.add(comparison)
        self.db.session.flush()
        return comparison

    def get_by_change_id(
        self,
        change_id: int
    ) -> Optional[ProcessModelComparison]:
        """
        Get process model comparison by change ID.

        Args:
            change_id: Change ID

        Returns:
            ProcessModelComparison or None if not found
        """
        return self.find_one(change_id=change_id)

    def update_comparison(
        self,
        change_id: int,
        nodes_added: Optional[List[Dict[str, Any]]] = None,
        nodes_removed: Optional[List[Dict[str, Any]]] = None,
        nodes_modified: Optional[List[Dict[str, Any]]] = None,
        flows_added: Optional[List[Dict[str, Any]]] = None,
        flows_removed: Optional[List[Dict[str, Any]]] = None,
        flows_modified: Optional[List[Dict[str, Any]]] = None,
        variables_changed: Optional[List[Dict[str, Any]]] = None,
        mermaid_diagram: Optional[str] = None
    ) -> Optional[ProcessModelComparison]:
        """
        Update existing process model comparison.

        Args:
            change_id: Change ID
            nodes_added: List of added nodes
            nodes_removed: List of removed nodes
            nodes_modified: List of modified nodes
            flows_added: List of added flows
            flows_removed: List of removed flows
            flows_modified: List of modified flows
            variables_changed: List of variable changes
            mermaid_diagram: Mermaid diagram syntax

        Returns:
            Updated ProcessModelComparison or None if not found
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison:
            return None

        if nodes_added is not None:
            comparison.nodes_added = json.dumps(nodes_added)
        if nodes_removed is not None:
            comparison.nodes_removed = json.dumps(nodes_removed)
        if nodes_modified is not None:
            comparison.nodes_modified = json.dumps(nodes_modified)
        if flows_added is not None:
            comparison.flows_added = json.dumps(flows_added)
        if flows_removed is not None:
            comparison.flows_removed = json.dumps(flows_removed)
        if flows_modified is not None:
            comparison.flows_modified = json.dumps(flows_modified)
        if variables_changed is not None:
            comparison.variables_changed = json.dumps(variables_changed)
        if mermaid_diagram is not None:
            comparison.mermaid_diagram = mermaid_diagram

        self.db.session.flush()
        return comparison

    def get_nodes_added(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get added nodes for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of added nodes or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.nodes_added:
            return None
        return json.loads(comparison.nodes_added)

    def get_nodes_removed(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get removed nodes for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of removed nodes or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.nodes_removed:
            return None
        return json.loads(comparison.nodes_removed)

    def get_nodes_modified(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get modified nodes for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of modified nodes or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.nodes_modified:
            return None
        return json.loads(comparison.nodes_modified)

    def get_flows_added(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get added flows for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of added flows or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.flows_added:
            return None
        return json.loads(comparison.flows_added)

    def get_flows_removed(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get removed flows for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of removed flows or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.flows_removed:
            return None
        return json.loads(comparison.flows_removed)

    def get_flows_modified(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get modified flows for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of modified flows or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.flows_modified:
            return None
        return json.loads(comparison.flows_modified)

    def get_variables_changed(
        self,
        change_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get variable changes for a comparison.

        Args:
            change_id: Change ID

        Returns:
            List of variable changes or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison or not comparison.variables_changed:
            return None
        return json.loads(comparison.variables_changed)

    def get_mermaid_diagram(
        self,
        change_id: int
    ) -> Optional[str]:
        """
        Get Mermaid diagram for a comparison.

        Args:
            change_id: Change ID

        Returns:
            Mermaid diagram syntax or None
        """
        comparison = self.get_by_change_id(change_id)
        if not comparison:
            return None
        return comparison.mermaid_diagram
