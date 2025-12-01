"""
Group Repository

Provides data access for Group objects.
Handles storage of group-specific data.
"""

from typing import Optional, List
from models import Group
from repositories.base_repository import BaseRepository


class GroupRepository(BaseRepository[Group]):
    """
    Repository for Group entities.
    
    Manages Group objects.
    Each group is linked to object_lookup via object_id.
    
    Key Methods:
        - create_group: Create group
        - get_by_object_id: Get group by object_lookup ID
        - get_by_uuid: Get group by UUID
    """
    
    def __init__(self):
        """Initialize repository with Group model."""
        super().__init__(Group)
    
    def create_group(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        members: Optional[str] = None,
        parent_group_uuid: Optional[str] = None,
        description: Optional[str] = None
    ) -> Group:
        """
        Create group.
        
        Args:
            object_id: Reference to object_lookup
            package_id: Reference to package (REQUIRED)
            uuid: Group UUID
            name: Group name
            version_uuid: Version UUID
            members: Members (JSON string)
            parent_group_uuid: Parent group UUID
            description: Description
        
        Returns:
            Created Group object
        
        Example:
            >>> group = repo.create_group(
            ...     object_id=42,
            ...     package_id=1,
            ...     uuid="abc-123",
            ...     name="My Group",
            ...     members='["user1", "user2"]'
            ... )
        """
        group = Group(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            members=members,
            parent_group_uuid=parent_group_uuid,
            description=description
        )
        self.db.session.add(group)
        self.db.session.flush()
        return group
    
    def get_by_object_id(self, object_id: int) -> Optional[Group]:
        """
        Get group by object_lookup ID.
        
        Note: This returns the first group found for the object.
        Use get_all_by_object_id() to get all package versions.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            Group or None if not found
        """
        return self.find_one(object_id=object_id)
    
    def get_by_object_and_package(
        self, 
        object_id: int, 
        package_id: int
    ) -> Optional[Group]:
        """
        Get group by object_lookup ID and package ID.
        
        This method returns the specific version of a group for a given package.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
        
        Returns:
            Group or None if not found
        
        Example:
            >>> # Get the customized version of a group
            >>> group = repo.get_by_object_and_package(
            ...     object_id=42,
            ...     package_id=2  # Customized package
            ... )
        """
        return self.find_one(object_id=object_id, package_id=package_id)
    
    def get_all_by_object_id(self, object_id: int) -> List[Group]:
        """
        Get all groups for an object across all packages.
        
        This method returns all package versions of a group.
        Useful when you need to compare versions across packages.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            List of Group objects (one per package)
        
        Example:
            >>> # Get all versions of a group
            >>> groups = repo.get_all_by_object_id(object_id=42)
            >>> for group in groups:
            ...     print(f"Package {group.package_id}: {group.version_uuid}")
        """
        return self.filter_by(object_id=object_id)
    
    def get_by_package(self, package_id: int) -> List[Group]:
        """
        Get all groups in a package.
        
        This method returns all groups that belong to a specific package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of Group objects
        
        Example:
            >>> # Get all groups in the base package
            >>> groups = repo.get_by_package(package_id=1)
            >>> print(f"Found {len(groups)} groups in base package")
        """
        return self.filter_by(package_id=package_id)
    
    def get_by_uuid(self, uuid: str) -> Optional[Group]:
        """
        Get group by UUID.
        
        Note: This returns the first group found with the UUID.
        Since UUIDs may exist in multiple packages, consider using
        get_by_object_and_package() for package-specific queries.
        
        Args:
            uuid: Group UUID
        
        Returns:
            Group or None if not found
        """
        return self.find_one(uuid=uuid)
