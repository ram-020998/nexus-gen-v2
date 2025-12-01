"""
Unknown Object Repository

Provides data access for Unknown Object types.
Handles storage of objects that don't match known types.
"""

from typing import Optional, List
from models import UnknownObject
from repositories.base_repository import BaseRepository


class UnknownObjectRepository(BaseRepository[UnknownObject]):
    """
    Repository for UnknownObject entities.
    
    Manages Unknown Object types.
    Each unknown object is linked to object_lookup via object_id.
    
    Key Methods:
        - create_unknown_object: Create unknown object
        - get_by_object_id: Get unknown object by object_lookup ID
        - get_by_uuid: Get unknown object by UUID
    """
    
    def __init__(self):
        """Initialize repository with UnknownObject model."""
        super().__init__(UnknownObject)
    
    def create_unknown_object(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        raw_xml: Optional[str] = None,
        description: Optional[str] = None
    ) -> UnknownObject:
        """
        Create unknown object.
        
        Args:
            object_id: Reference to object_lookup
            package_id: Reference to package (REQUIRED)
            uuid: Object UUID
            name: Object name
            version_uuid: Version UUID
            raw_xml: Raw XML content
            description: Description
        
        Returns:
            Created UnknownObject object
        
        Example:
            >>> obj = repo.create_unknown_object(
            ...     object_id=42,
            ...     package_id=1,
            ...     uuid="abc-123",
            ...     name="Unknown Type Object",
            ...     raw_xml="<xml>...</xml>"
            ... )
        """
        unknown_object = UnknownObject(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            raw_xml=raw_xml,
            description=description
        )
        self.db.session.add(unknown_object)
        self.db.session.flush()
        return unknown_object
    
    def get_by_object_id(self, object_id: int) -> Optional[UnknownObject]:
        """
        Get unknown object by object_lookup ID.
        
        Note: This returns the first unknown object found for the object.
        Use get_all_by_object_id() to get all package versions.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            UnknownObject or None if not found
        """
        return self.find_one(object_id=object_id)
    
    def get_by_object_and_package(
        self, 
        object_id: int, 
        package_id: int
    ) -> Optional[UnknownObject]:
        """
        Get unknown object by object_lookup ID and package ID.
        
        This method returns the specific version of an unknown object for a given package.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
        
        Returns:
            UnknownObject or None if not found
        
        Example:
            >>> # Get the customized version of an unknown object
            >>> obj = repo.get_by_object_and_package(
            ...     object_id=42,
            ...     package_id=2  # Customized package
            ... )
        """
        return self.find_one(object_id=object_id, package_id=package_id)
    
    def get_all_by_object_id(self, object_id: int) -> List[UnknownObject]:
        """
        Get all unknown objects for an object across all packages.
        
        This method returns all package versions of an unknown object.
        Useful when you need to compare versions across packages.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            List of UnknownObject objects (one per package)
        
        Example:
            >>> # Get all versions of an unknown object
            >>> objects = repo.get_all_by_object_id(object_id=42)
            >>> for obj in objects:
            ...     print(f"Package {obj.package_id}: {obj.version_uuid}")
        """
        return self.filter_by(object_id=object_id)
    
    def get_by_package(self, package_id: int) -> List[UnknownObject]:
        """
        Get all unknown objects in a package.
        
        This method returns all unknown objects that belong to a specific package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of UnknownObject objects
        
        Example:
            >>> # Get all unknown objects in the base package
            >>> objects = repo.get_by_package(package_id=1)
            >>> print(f"Found {len(objects)} unknown objects in base package")
        """
        return self.filter_by(package_id=package_id)
    
    def get_by_uuid(self, uuid: str) -> Optional[UnknownObject]:
        """
        Get unknown object by UUID.
        
        Note: This returns the first unknown object found with the UUID.
        Since UUIDs may exist in multiple packages, consider using
        get_by_object_and_package() for package-specific queries.
        
        Args:
            uuid: Object UUID
        
        Returns:
            UnknownObject or None if not found
        """
        return self.find_one(uuid=uuid)
