"""
Web API Repository

Provides data access for Web API objects.
Handles storage of web API-specific data.
"""

from typing import Optional, List
from models import WebAPI
from repositories.base_repository import BaseRepository


class WebAPIRepository(BaseRepository[WebAPI]):
    """
    Repository for WebAPI entities.
    
    Manages Web API objects.
    Each web API is linked to object_lookup via object_id.
    
    Key Methods:
        - create_web_api: Create web API
        - get_by_object_id: Get web API by object_lookup ID
        - get_by_uuid: Get web API by UUID
    """
    
    def __init__(self):
        """Initialize repository with WebAPI model."""
        super().__init__(WebAPI)
    
    def create_web_api(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        sail_code: Optional[str] = None,
        endpoint: Optional[str] = None,
        http_methods: Optional[str] = None,
        description: Optional[str] = None
    ) -> WebAPI:
        """
        Create web API.
        
        Args:
            object_id: Reference to object_lookup
            package_id: Reference to package (REQUIRED)
            uuid: Web API UUID
            name: Web API name
            version_uuid: Version UUID
            sail_code: SAIL code
            endpoint: Endpoint path
            http_methods: HTTP methods (JSON string)
            description: Description
        
        Returns:
            Created WebAPI object
        
        Example:
            >>> api = repo.create_web_api(
            ...     object_id=42,
            ...     package_id=1,
            ...     uuid="abc-123",
            ...     name="My API",
            ...     endpoint="/api/users",
            ...     http_methods='["GET", "POST"]'
            ... )
        """
        web_api = WebAPI(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            sail_code=sail_code,
            endpoint=endpoint,
            http_methods=http_methods,
            description=description
        )
        self.db.session.add(web_api)
        self.db.session.flush()
        return web_api
    
    def get_by_object_id(self, object_id: int) -> Optional[WebAPI]:
        """
        Get web API by object_lookup ID.
        
        Note: This returns the first web API found for the object.
        Use get_all_by_object_id() to get all package versions.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            WebAPI or None if not found
        """
        return self.find_one(object_id=object_id)
    
    def get_by_object_and_package(
        self, 
        object_id: int, 
        package_id: int
    ) -> Optional[WebAPI]:
        """
        Get web API by object_lookup ID and package ID.
        
        This method returns the specific version of a web API for a given package.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
        
        Returns:
            WebAPI or None if not found
        
        Example:
            >>> # Get the customized version of a web API
            >>> api = repo.get_by_object_and_package(
            ...     object_id=42,
            ...     package_id=2  # Customized package
            ... )
        """
        return self.find_one(object_id=object_id, package_id=package_id)
    
    def get_all_by_object_id(self, object_id: int) -> List[WebAPI]:
        """
        Get all web APIs for an object across all packages.
        
        This method returns all package versions of a web API.
        Useful when you need to compare versions across packages.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            List of WebAPI objects (one per package)
        
        Example:
            >>> # Get all versions of a web API
            >>> apis = repo.get_all_by_object_id(object_id=42)
            >>> for api in apis:
            ...     print(f"Package {api.package_id}: {api.version_uuid}")
        """
        return self.filter_by(object_id=object_id)
    
    def get_by_package(self, package_id: int) -> List[WebAPI]:
        """
        Get all web APIs in a package.
        
        This method returns all web APIs that belong to a specific package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of WebAPI objects
        
        Example:
            >>> # Get all web APIs in the base package
            >>> apis = repo.get_by_package(package_id=1)
            >>> print(f"Found {len(apis)} web APIs in base package")
        """
        return self.filter_by(package_id=package_id)
    
    def get_by_uuid(self, uuid: str) -> Optional[WebAPI]:
        """
        Get web API by UUID.
        
        Note: This returns the first web API found with the UUID.
        Since UUIDs may exist in multiple packages, consider using
        get_by_object_and_package() for package-specific queries.
        
        Args:
            uuid: Web API UUID
        
        Returns:
            WebAPI or None if not found
        """
        return self.find_one(uuid=uuid)
