"""
Interface Repository

Provides data access for Interface objects and related entities.
Handles storage of interface-specific data including parameters and security settings.
"""

from typing import Optional, List, Dict, Any
from models import Interface, InterfaceParameter, InterfaceSecurity
from repositories.base_repository import BaseRepository


class InterfaceRepository(BaseRepository[Interface]):
    """
    Repository for Interface entities.
    
    Manages Interface objects with their parameters and security settings.
    Each interface is linked to object_lookup via object_id.
    
    Key Methods:
        - create_interface: Create interface with parameters and security
        - get_by_object_id: Get interface by object_lookup ID
        - get_by_uuid: Get interface by UUID
    """
    
    def __init__(self):
        """Initialize repository with Interface model."""
        super().__init__(Interface)
    
    def create_interface(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        sail_code: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[List[Dict[str, Any]]] = None,
        security: Optional[List[Dict[str, Any]]] = None
    ) -> Interface:
        """
        Create interface with parameters and security settings.
        
        Args:
            object_id: Reference to object_lookup
            package_id: Reference to package (REQUIRED)
            uuid: Interface UUID
            name: Interface name
            version_uuid: Version UUID
            sail_code: SAIL code
            description: Description
            parameters: List of parameter dicts with keys:
                - parameter_name
                - parameter_type
                - is_required
                - default_value
                - display_order
            security: List of security dicts with keys:
                - role_name
                - permission_type
        
        Returns:
            Created Interface object
        
        Example:
            >>> interface = repo.create_interface(
            ...     object_id=42,
            ...     package_id=1,
            ...     uuid="abc-123",
            ...     name="My Interface",
            ...     parameters=[
            ...         {"parameter_name": "input1", "parameter_type": "Text", "is_required": True}
            ...     ],
            ...     security=[
            ...         {"role_name": "Admin", "permission_type": "EDIT"}
            ...     ]
            ... )
        """
        # Create interface
        interface = Interface(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            sail_code=sail_code,
            description=description
        )
        self.db.session.add(interface)
        self.db.session.flush()
        
        # Create parameters
        if parameters:
            for param_data in parameters:
                param = InterfaceParameter(
                    interface_id=interface.id,
                    parameter_name=param_data.get('parameter_name'),
                    parameter_type=param_data.get('parameter_type'),
                    is_required=param_data.get('is_required', False),
                    default_value=param_data.get('default_value'),
                    display_order=param_data.get('display_order')
                )
                self.db.session.add(param)
        
        # Create security settings
        if security:
            for sec_data in security:
                sec = InterfaceSecurity(
                    interface_id=interface.id,
                    role_name=sec_data.get('role_name'),
                    permission_type=sec_data.get('permission_type')
                )
                self.db.session.add(sec)
        
        self.db.session.flush()
        return interface
    
    def get_by_object_id(self, object_id: int) -> Optional[Interface]:
        """
        Get interface by object_lookup ID.
        
        Note: This returns the first interface found for the object.
        Use get_all_by_object_id() to get all package versions.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            Interface or None if not found
        """
        return self.find_one(object_id=object_id)
    
    def get_by_object_and_package(
        self, 
        object_id: int, 
        package_id: int
    ) -> Optional[Interface]:
        """
        Get interface by object_lookup ID and package ID.
        
        This method returns the specific version of an interface for a given package.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
        
        Returns:
            Interface or None if not found
        
        Example:
            >>> # Get the customized version of an interface
            >>> interface = repo.get_by_object_and_package(
            ...     object_id=42,
            ...     package_id=2  # Customized package
            ... )
        """
        return self.find_one(object_id=object_id, package_id=package_id)
    
    def get_all_by_object_id(self, object_id: int) -> List[Interface]:
        """
        Get all interfaces for an object across all packages.
        
        This method returns all package versions of an interface.
        Useful when you need to compare versions across packages.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            List of Interface objects (one per package)
        
        Example:
            >>> # Get all versions of an interface
            >>> interfaces = repo.get_all_by_object_id(object_id=42)
            >>> for interface in interfaces:
            ...     print(f"Package {interface.package_id}: {interface.version_uuid}")
        """
        return self.filter_by(object_id=object_id)
    
    def get_by_package(self, package_id: int) -> List[Interface]:
        """
        Get all interfaces in a package.
        
        This method returns all interfaces that belong to a specific package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of Interface objects
        
        Example:
            >>> # Get all interfaces in the base package
            >>> interfaces = repo.get_by_package(package_id=1)
            >>> print(f"Found {len(interfaces)} interfaces in base package")
        """
        return self.filter_by(package_id=package_id)
    
    def get_by_uuid(self, uuid: str) -> Optional[Interface]:
        """
        Get interface by UUID.
        
        Note: This returns the first interface found with the UUID.
        Since UUIDs may exist in multiple packages, consider using
        get_by_object_and_package() for package-specific queries.
        
        Args:
            uuid: Interface UUID
        
        Returns:
            Interface or None if not found
        """
        return self.find_one(uuid=uuid)
    
    def get_parameters(self, interface_id: int) -> List[InterfaceParameter]:
        """
        Get all parameters for an interface.
        
        Args:
            interface_id: Interface ID
        
        Returns:
            List of InterfaceParameter objects
        """
        return self.db.session.query(InterfaceParameter).filter_by(
            interface_id=interface_id
        ).order_by(InterfaceParameter.display_order).all()
    
    def get_security_settings(self, interface_id: int) -> List[InterfaceSecurity]:
        """
        Get all security settings for an interface.
        
        Args:
            interface_id: Interface ID
        
        Returns:
            List of InterfaceSecurity objects
        """
        return self.db.session.query(InterfaceSecurity).filter_by(
            interface_id=interface_id
        ).all()
