"""
Constant Repository

Provides data access for Constant objects.
Handles storage of constant-specific data.
"""

from typing import Optional, List
from models import Constant
from repositories.base_repository import BaseRepository


class ConstantRepository(BaseRepository[Constant]):
    """
    Repository for Constant entities.
    
    Manages Constant objects.
    Each constant is linked to object_lookup via object_id.
    
    Key Methods:
        - create_constant: Create constant
        - get_by_object_id: Get constant by object_lookup ID
        - get_by_uuid: Get constant by UUID
    """
    
    def __init__(self):
        """Initialize repository with Constant model."""
        super().__init__(Constant)
    
    def create_constant(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        constant_value: Optional[str] = None,
        constant_type: Optional[str] = None,
        scope: Optional[str] = None,
        description: Optional[str] = None
    ) -> Constant:
        """
        Create constant.
        
        Args:
            object_id: Reference to object_lookup
            package_id: Reference to package (REQUIRED)
            uuid: Constant UUID
            name: Constant name
            version_uuid: Version UUID
            constant_value: Constant value
            constant_type: Constant type
            scope: Scope (e.g., 'global', 'application')
            description: Description
        
        Returns:
            Created Constant object
        
        Example:
            >>> constant = repo.create_constant(
            ...     object_id=42,
            ...     package_id=1,
            ...     uuid="abc-123",
            ...     name="MY_CONSTANT",
            ...     constant_value="100",
            ...     constant_type="Number"
            ... )
        """
        constant = Constant(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            constant_value=constant_value,
            constant_type=constant_type,
            scope=scope,
            description=description
        )
        self.db.session.add(constant)
        self.db.session.flush()
        return constant
    
    def get_by_object_id(self, object_id: int) -> Optional[Constant]:
        """
        Get constant by object_lookup ID.
        
        Note: This returns the first constant found for the object.
        Use get_all_by_object_id() to get all package versions.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            Constant or None if not found
        """
        return self.find_one(object_id=object_id)
    
    def get_by_object_and_package(
        self, 
        object_id: int, 
        package_id: int
    ) -> Optional[Constant]:
        """
        Get constant by object_lookup ID and package ID.
        
        This method returns the specific version of a constant for a given package.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
        
        Returns:
            Constant or None if not found
        
        Example:
            >>> # Get the customized version of a constant
            >>> constant = repo.get_by_object_and_package(
            ...     object_id=42,
            ...     package_id=2  # Customized package
            ... )
        """
        return self.find_one(object_id=object_id, package_id=package_id)
    
    def get_all_by_object_id(self, object_id: int) -> List[Constant]:
        """
        Get all constants for an object across all packages.
        
        This method returns all package versions of a constant.
        Useful when you need to compare versions across packages.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            List of Constant objects (one per package)
        
        Example:
            >>> # Get all versions of a constant
            >>> constants = repo.get_all_by_object_id(object_id=42)
            >>> for constant in constants:
            ...     print(f"Package {constant.package_id}: {constant.version_uuid}")
        """
        return self.filter_by(object_id=object_id)
    
    def get_by_package(self, package_id: int) -> List[Constant]:
        """
        Get all constants in a package.
        
        This method returns all constants that belong to a specific package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of Constant objects
        
        Example:
            >>> # Get all constants in the base package
            >>> constants = repo.get_by_package(package_id=1)
            >>> print(f"Found {len(constants)} constants in base package")
        """
        return self.filter_by(package_id=package_id)
    
    def get_by_uuid(self, uuid: str) -> Optional[Constant]:
        """
        Get constant by UUID.
        
        Note: This returns the first constant found with the UUID.
        Since UUIDs may exist in multiple packages, consider using
        get_by_object_and_package() for package-specific queries.
        
        Args:
            uuid: Constant UUID
        
        Returns:
            Constant or None if not found
        """
        return self.find_one(uuid=uuid)
