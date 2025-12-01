"""
Integration Repository

Provides data access for Integration objects.
Handles storage of integration-specific data.
"""

from typing import Optional, List
from models import Integration
from repositories.base_repository import BaseRepository


class IntegrationRepository(BaseRepository[Integration]):
    """
    Repository for Integration entities.
    
    Manages Integration objects.
    Each integration is linked to object_lookup via object_id.
    
    Key Methods:
        - create_integration: Create integration
        - get_by_object_id: Get integration by object_lookup ID
        - get_by_uuid: Get integration by UUID
    """
    
    def __init__(self):
        """Initialize repository with Integration model."""
        super().__init__(Integration)
    
    def create_integration(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        sail_code: Optional[str] = None,
        connection_info: Optional[str] = None,
        authentication_info: Optional[str] = None,
        endpoint: Optional[str] = None,
        description: Optional[str] = None
    ) -> Integration:
        """
        Create integration.
        
        Args:
            object_id: Reference to object_lookup
            package_id: Reference to package (REQUIRED)
            uuid: Integration UUID
            name: Integration name
            version_uuid: Version UUID
            sail_code: SAIL code
            connection_info: Connection information
            authentication_info: Authentication information
            endpoint: Endpoint URL
            description: Description
        
        Returns:
            Created Integration object
        
        Example:
            >>> integration = repo.create_integration(
            ...     object_id=42,
            ...     package_id=1,
            ...     uuid="abc-123",
            ...     name="My Integration",
            ...     endpoint="https://api.example.com"
            ... )
        """
        integration = Integration(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            sail_code=sail_code,
            connection_info=connection_info,
            authentication_info=authentication_info,
            endpoint=endpoint,
            description=description
        )
        self.db.session.add(integration)
        self.db.session.flush()
        return integration
    
    def get_by_object_id(self, object_id: int) -> Optional[Integration]:
        """
        Get integration by object_lookup ID.
        
        Note: This returns the first integration found for the object.
        Use get_all_by_object_id() to get all package versions.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            Integration or None if not found
        """
        return self.find_one(object_id=object_id)
    
    def get_by_object_and_package(
        self, 
        object_id: int, 
        package_id: int
    ) -> Optional[Integration]:
        """
        Get integration by object_lookup ID and package ID.
        
        This method returns the specific version of an integration for a given package.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
        
        Returns:
            Integration or None if not found
        
        Example:
            >>> # Get the customized version of an integration
            >>> integration = repo.get_by_object_and_package(
            ...     object_id=42,
            ...     package_id=2  # Customized package
            ... )
        """
        return self.find_one(object_id=object_id, package_id=package_id)
    
    def get_all_by_object_id(self, object_id: int) -> List[Integration]:
        """
        Get all integrations for an object across all packages.
        
        This method returns all package versions of an integration.
        Useful when you need to compare versions across packages.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            List of Integration objects (one per package)
        
        Example:
            >>> # Get all versions of an integration
            >>> integrations = repo.get_all_by_object_id(object_id=42)
            >>> for integration in integrations:
            ...     print(f"Package {integration.package_id}: {integration.version_uuid}")
        """
        return self.filter_by(object_id=object_id)
    
    def get_by_package(self, package_id: int) -> List[Integration]:
        """
        Get all integrations in a package.
        
        This method returns all integrations that belong to a specific package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of Integration objects
        
        Example:
            >>> # Get all integrations in the base package
            >>> integrations = repo.get_by_package(package_id=1)
            >>> print(f"Found {len(integrations)} integrations in base package")
        """
        return self.filter_by(package_id=package_id)
    
    def get_by_uuid(self, uuid: str) -> Optional[Integration]:
        """
        Get integration by UUID.
        
        Note: This returns the first integration found with the UUID.
        Since UUIDs may exist in multiple packages, consider using
        get_by_object_and_package() for package-specific queries.
        
        Args:
            uuid: Integration UUID
        
        Returns:
            Integration or None if not found
        """
        return self.find_one(uuid=uuid)
