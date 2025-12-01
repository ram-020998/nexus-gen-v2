"""
Site Repository

Provides data access for Site objects.
Handles storage of site-specific data.
"""

from typing import Optional, List
from models import Site
from repositories.base_repository import BaseRepository


class SiteRepository(BaseRepository[Site]):
    """
    Repository for Site entities.
    
    Manages Site objects.
    Each site is linked to object_lookup via object_id.
    
    Key Methods:
        - create_site: Create site
        - get_by_object_id: Get site by object_lookup ID
        - get_by_uuid: Get site by UUID
    """
    
    def __init__(self):
        """Initialize repository with Site model."""
        super().__init__(Site)
    
    def create_site(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        page_hierarchy: Optional[str] = None,
        description: Optional[str] = None
    ) -> Site:
        """
        Create site.
        
        Args:
            object_id: Reference to object_lookup
            package_id: Reference to package (REQUIRED)
            uuid: Site UUID
            name: Site name
            version_uuid: Version UUID
            page_hierarchy: Page hierarchy (JSON string)
            description: Description
        
        Returns:
            Created Site object
        
        Example:
            >>> site = repo.create_site(
            ...     object_id=42,
            ...     package_id=1,
            ...     uuid="abc-123",
            ...     name="My Site",
            ...     page_hierarchy='{"pages": [...]}'
            ... )
        """
        site = Site(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            page_hierarchy=page_hierarchy,
            description=description
        )
        self.db.session.add(site)
        self.db.session.flush()
        return site
    
    def get_by_object_id(self, object_id: int) -> Optional[Site]:
        """
        Get site by object_lookup ID.
        
        Note: This returns the first site found for the object.
        Use get_all_by_object_id() to get all package versions.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            Site or None if not found
        """
        return self.find_one(object_id=object_id)
    
    def get_by_object_and_package(
        self, 
        object_id: int, 
        package_id: int
    ) -> Optional[Site]:
        """
        Get site by object_lookup ID and package ID.
        
        This method returns the specific version of a site for a given package.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
        
        Returns:
            Site or None if not found
        
        Example:
            >>> # Get the customized version of a site
            >>> site = repo.get_by_object_and_package(
            ...     object_id=42,
            ...     package_id=2  # Customized package
            ... )
        """
        return self.find_one(object_id=object_id, package_id=package_id)
    
    def get_all_by_object_id(self, object_id: int) -> List[Site]:
        """
        Get all sites for an object across all packages.
        
        This method returns all package versions of a site.
        Useful when you need to compare versions across packages.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            List of Site objects (one per package)
        
        Example:
            >>> # Get all versions of a site
            >>> sites = repo.get_all_by_object_id(object_id=42)
            >>> for site in sites:
            ...     print(f"Package {site.package_id}: {site.version_uuid}")
        """
        return self.filter_by(object_id=object_id)
    
    def get_by_package(self, package_id: int) -> List[Site]:
        """
        Get all sites in a package.
        
        This method returns all sites that belong to a specific package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of Site objects
        
        Example:
            >>> # Get all sites in the base package
            >>> sites = repo.get_by_package(package_id=1)
            >>> print(f"Found {len(sites)} sites in base package")
        """
        return self.filter_by(package_id=package_id)
    
    def get_by_uuid(self, uuid: str) -> Optional[Site]:
        """
        Get site by UUID.
        
        Note: This returns the first site found with the UUID.
        Since UUIDs may exist in multiple packages, consider using
        get_by_object_and_package() for package-specific queries.
        
        Args:
            uuid: Site UUID
        
        Returns:
            Site or None if not found
        """
        return self.find_one(uuid=uuid)
