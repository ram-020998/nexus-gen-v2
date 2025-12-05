"""
Connected System Repository

Provides data access for Connected System objects.
Handles storage of connected system-specific data.
"""

from typing import Optional, List
from models import ConnectedSystem
from repositories.base_repository import BaseRepository


class ConnectedSystemRepository(BaseRepository[ConnectedSystem]):
    """
    Repository for ConnectedSystem entities.
    
    Manages Connected System objects.
    Each connected system is linked to object_lookup via object_id.
    
    Key Methods:
        - create_connected_system: Create connected system
        - get_by_object_id: Get connected system by object_lookup ID
        - get_by_uuid: Get connected system by UUID
    """
    
    def __init__(self):
        """Initialize repository with ConnectedSystem model."""
        super().__init__(ConnectedSystem)
    
    def create_connected_system(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        system_type: Optional[str] = None,
        properties: Optional[str] = None,
        description: Optional[str] = None
    ) -> ConnectedSystem:
        """
        Create connected system.
        
        Args:
            object_id: Reference to object_lookup
            package_id: Reference to package (REQUIRED)
            uuid: Connected system UUID
            name: Connected system name
            version_uuid: Version UUID
            system_type: System type (e.g., 'HTTP', 'Database')
            properties: Properties (JSON string)
            description: Description
        
        Returns:
            Created ConnectedSystem object
        
        Example:
            >>> cs = repo.create_connected_system(
            ...     object_id=42,
            ...     package_id=1,
            ...     uuid="abc-123",
            ...     name="My Connected System",
            ...     system_type="HTTP",
            ...     properties='{"url": "https://api.example.com"}'
            ... )
        """
        connected_system = ConnectedSystem(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            system_type=system_type,
            properties=properties,
            description=description
        )
        self.db.session.add(connected_system)
        self.db.session.flush()
        return connected_system
    
    def get_by_object_id(self, object_id: int) -> Optional[ConnectedSystem]:
        """
        Get connected system by object_lookup ID.
        
        Note: This returns the first connected system found for the object.
        Use get_all_by_object_id() to get all package versions.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            ConnectedSystem or None if not found
        """
        return self.find_one(object_id=object_id)
    
    def get_by_object_and_package(
        self, 
        object_id: int, 
        package_id: int
    ) -> Optional[ConnectedSystem]:
        """
        Get connected system by object_lookup ID and package ID.
        
        This method returns the specific version of a connected system for a given package.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
        
        Returns:
            ConnectedSystem or None if not found
        
        Example:
            >>> # Get the customized version of a connected system
            >>> cs = repo.get_by_object_and_package(
            ...     object_id=42,
            ...     package_id=2  # Customized package
            ... )
        """
        return self.find_one(object_id=object_id, package_id=package_id)
    
    def get_all_by_object_id(self, object_id: int) -> List[ConnectedSystem]:
        """
        Get all connected systems for an object across all packages.
        
        This method returns all package versions of a connected system.
        Useful when you need to compare versions across packages.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            List of ConnectedSystem objects (one per package)
        
        Example:
            >>> # Get all versions of a connected system
            >>> systems = repo.get_all_by_object_id(object_id=42)
            >>> for system in systems:
            ...     print(f"Package {system.package_id}: {system.version_uuid}")
        """
        return self.filter_by(object_id=object_id)
    
    def get_by_package(self, package_id: int) -> List[ConnectedSystem]:
        """
        Get all connected systems in a package.
        
        This method returns all connected systems that belong to a specific package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of ConnectedSystem objects
        
        Example:
            >>> # Get all connected systems in the base package
            >>> systems = repo.get_by_package(package_id=1)
            >>> print(f"Found {len(systems)} connected systems in base package")
        """
        return self.filter_by(package_id=package_id)
    
    def get_by_uuid(self, uuid: str) -> Optional[ConnectedSystem]:
        """
        Get connected system by UUID.
        
        Note: This returns the first connected system found with the UUID.
        Since UUIDs may exist in multiple packages, consider using
        get_by_object_and_package() for package-specific queries.
        
        Args:
            uuid: Connected system UUID
        
        Returns:
            ConnectedSystem or None if not found
        """
        return self.find_one(uuid=uuid)
