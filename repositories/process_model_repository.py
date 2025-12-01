"""
Process Model Repository

Provides data access for Process Model objects and related entities.
Handles storage of process model-specific data including nodes, flows, and variables.
"""

from typing import Optional, List, Dict, Any
from models import (
    ProcessModel,
    ProcessModelNode,
    ProcessModelFlow,
    ProcessModelVariable
)
from repositories.base_repository import BaseRepository


class ProcessModelRepository(BaseRepository[ProcessModel]):
    """
    Repository for ProcessModel entities.
    
    Manages Process Model objects with their nodes, flows, and variables.
    Each process model is linked to object_lookup via object_id.
    
    Key Methods:
        - create_process_model: Create process model with nodes, flows, and variables
        - get_by_object_id: Get process model by object_lookup ID
        - get_by_uuid: Get process model by UUID
    """
    
    def __init__(self):
        """Initialize repository with ProcessModel model."""
        super().__init__(ProcessModel)
    
    def create_process_model(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        description: Optional[str] = None,
        total_nodes: int = 0,
        total_flows: int = 0,
        complexity_score: Optional[float] = None,
        nodes: Optional[List[Dict[str, Any]]] = None,
        flows: Optional[List[Dict[str, Any]]] = None,
        variables: Optional[List[Dict[str, Any]]] = None
    ) -> ProcessModel:
        """
        Create process model with nodes, flows, and variables.
        
        Args:
            object_id: Reference to object_lookup
            package_id: Reference to package (REQUIRED)
            uuid: Process model UUID
            name: Process model name
            version_uuid: Version UUID
            description: Description
            total_nodes: Total number of nodes
            total_flows: Total number of flows
            complexity_score: Complexity score
            nodes: List of node dicts with keys:
                - node_id
                - node_type
                - node_name
                - properties (JSON string)
            flows: List of flow dicts with keys:
                - from_node_id
                - to_node_id
                - flow_label
                - flow_condition
            variables: List of variable dicts with keys:
                - variable_name
                - variable_type
                - is_parameter
                - default_value
        
        Returns:
            Created ProcessModel object
        
        Example:
            >>> pm = repo.create_process_model(
            ...     object_id=42,
            ...     package_id=1,
            ...     uuid="abc-123",
            ...     name="My Process",
            ...     nodes=[
            ...         {"node_id": "node1", "node_type": "Start", "node_name": "Start"}
            ...     ],
            ...     flows=[
            ...         {"from_node_id": 1, "to_node_id": 2, "flow_label": "Next"}
            ...     ]
            ... )
        """
        # Create process model
        process_model = ProcessModel(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            description=description,
            total_nodes=total_nodes,
            total_flows=total_flows,
            complexity_score=complexity_score
        )
        self.db.session.add(process_model)
        self.db.session.flush()
        
        # Create nodes and build node_id mapping
        node_id_map = {}
        if nodes:
            for node_data in nodes:
                node = ProcessModelNode(
                    process_model_id=process_model.id,
                    node_id=node_data.get('node_id'),
                    node_type=node_data.get('node_type'),
                    node_name=node_data.get('node_name'),
                    properties=node_data.get('properties')
                )
                self.db.session.add(node)
                self.db.session.flush()
                # Map external node_id to internal database ID
                node_id_map[node_data.get('node_id')] = node.id
        
        # Create flows (using node_id_map for foreign keys)
        if flows:
            for flow_data in flows:
                # Get the database IDs for from/to nodes
                from_node_external_id = flow_data.get('from_node_id')
                to_node_external_id = flow_data.get('to_node_id')
                
                # Look up the database IDs
                from_node_db_id = node_id_map.get(from_node_external_id)
                to_node_db_id = node_id_map.get(to_node_external_id)
                
                if from_node_db_id and to_node_db_id:
                    flow = ProcessModelFlow(
                        process_model_id=process_model.id,
                        from_node_id=from_node_db_id,
                        to_node_id=to_node_db_id,
                        flow_label=flow_data.get('flow_label'),
                        flow_condition=flow_data.get('flow_condition')
                    )
                    self.db.session.add(flow)
        
        # Create variables
        if variables:
            for var_data in variables:
                var = ProcessModelVariable(
                    process_model_id=process_model.id,
                    variable_name=var_data.get('variable_name'),
                    variable_type=var_data.get('variable_type'),
                    is_parameter=var_data.get('is_parameter', False),
                    default_value=var_data.get('default_value')
                )
                self.db.session.add(var)
        
        self.db.session.flush()
        return process_model
    
    def get_by_object_id(self, object_id: int) -> Optional[ProcessModel]:
        """
        Get process model by object_lookup ID.
        
        Note: This returns the first process model found for the object.
        Use get_all_by_object_id() to get all package versions.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            ProcessModel or None if not found
        """
        return self.find_one(object_id=object_id)
    
    def get_by_object_and_package(
        self, 
        object_id: int, 
        package_id: int
    ) -> Optional[ProcessModel]:
        """
        Get process model by object_lookup ID and package ID.
        
        This method returns the specific version of a process model for a given package.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
        
        Returns:
            ProcessModel or None if not found
        
        Example:
            >>> # Get the customized version of a process model
            >>> pm = repo.get_by_object_and_package(
            ...     object_id=42,
            ...     package_id=2  # Customized package
            ... )
        """
        return self.find_one(object_id=object_id, package_id=package_id)
    
    def get_all_by_object_id(self, object_id: int) -> List[ProcessModel]:
        """
        Get all process models for an object across all packages.
        
        This method returns all package versions of a process model.
        Useful when you need to compare versions across packages.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            List of ProcessModel objects (one per package)
        
        Example:
            >>> # Get all versions of a process model
            >>> process_models = repo.get_all_by_object_id(object_id=42)
            >>> for pm in process_models:
            ...     print(f"Package {pm.package_id}: {pm.version_uuid}")
        """
        return self.filter_by(object_id=object_id)
    
    def get_by_package(self, package_id: int) -> List[ProcessModel]:
        """
        Get all process models in a package.
        
        This method returns all process models that belong to a specific package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of ProcessModel objects
        
        Example:
            >>> # Get all process models in the base package
            >>> process_models = repo.get_by_package(package_id=1)
            >>> print(f"Found {len(process_models)} process models in base package")
        """
        return self.filter_by(package_id=package_id)
    
    def get_by_uuid(self, uuid: str) -> Optional[ProcessModel]:
        """
        Get process model by UUID.
        
        Args:
            uuid: Process model UUID
        
        Returns:
            ProcessModel or None if not found
        """
        return self.find_one(uuid=uuid)
    
    def get_nodes(self, process_model_id: int) -> List[ProcessModelNode]:
        """
        Get all nodes for a process model.
        
        Args:
            process_model_id: Process model ID
        
        Returns:
            List of ProcessModelNode objects
        """
        return self.db.session.query(ProcessModelNode).filter_by(
            process_model_id=process_model_id
        ).all()
    
    def get_flows(self, process_model_id: int) -> List[ProcessModelFlow]:
        """
        Get all flows for a process model.
        
        Args:
            process_model_id: Process model ID
        
        Returns:
            List of ProcessModelFlow objects
        """
        return self.db.session.query(ProcessModelFlow).filter_by(
            process_model_id=process_model_id
        ).all()
    
    def get_variables(self, process_model_id: int) -> List[ProcessModelVariable]:
        """
        Get all variables for a process model.
        
        Args:
            process_model_id: Process model ID
        
        Returns:
            List of ProcessModelVariable objects
        """
        return self.db.session.query(ProcessModelVariable).filter_by(
            process_model_id=process_model_id
        ).all()
