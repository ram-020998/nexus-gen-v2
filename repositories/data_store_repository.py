"""
Data Store Repository

Provides data access for Data Store objects.
Handles storage of data store-specific data.
"""

from typing import Optional, List
from models import DataStore
from repositories.base_repository import BaseRepository


class DataStoreRepository(BaseRepository[DataStore]):
    """
    Repository for DataStore entities.
    
    Manages Data Store objects.
    Each data store is linked to object_lookup via object_id.
    
    Key Methods:
        - create_data_store: Create data store
        - get_by_object_id: Get data store by object_lookup ID
        - get_by_uuid: Get data store by UUID
    """
    
    def __init__(self):
        """Initialize repository with DataStore model."""
        super().__init__(DataStore)
    
    def create_data_store(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        description: Optional[str] = None,
        connection_reference: Optional[str] = None,
        configuration: Optional[str] = None
    ) -> DataStore:
        """
        Create data store.
        
        Args:
            object_id: Reference to object_lookup
            package_id: Reference to package (REQUIRED)
            uuid: Data store UUID
            name: Data store name
            version_uuid: Version UUID
            description: Description
            connection_reference: Connection reference
            configuration: Configuration (JSON string)
        
        Returns:
            Created DataStore object
        
        Example:
            >>> ds = repo.create_data_store(
            ...     object_id=42,
            ...     package_id=1,
            ...     uuid="abc-123",
            ...     name="My Data Store",
            ...     connection_reference="cs_abc",
            ...     configuration='{"entities": [...]}'
            ... )
        """
        data_store = DataStore(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            description=description,
            connection_reference=connection_reference,
            configuration=configuration
        )
        self.db.session.add(data_store)
        self.db.session.flush()
        return data_store
    
    def get_by_object_id(self, object_id: int) -> Optional[DataStore]:
        """
        Get data store by object_lookup ID.
        
        Note: This returns the first data store found for the object.
        Use get_all_by_object_id() to get all package versions.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            DataStore or None if not found
        """
        return self.find_one(object_id=object_id)
    
    def get_by_object_and_package(
        self, 
        object_id: int, 
        package_id: int
    ) -> Optional[DataStore]:
        """
        Get data store by object_lookup ID and package ID.
        
        This method returns the specific version of a data store for a given package.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
        
        Returns:
            DataStore or None if not found
        
        Example:
            >>> # Get the customized version of a data store
            >>> ds = repo.get_by_object_and_package(
            ...     object_id=42,
            ...     package_id=2  # Customized package
            ... )
        """
        return self.find_one(object_id=object_id, package_id=package_id)
    
    def get_all_by_object_id(self, object_id: int) -> List[DataStore]:
        """
        Get all data stores for an object across all packages.
        
        This method returns all package versions of a data store.
        Useful when you need to compare versions across packages.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            List of DataStore objects (one per package)
        
        Example:
            >>> # Get all versions of a data store
            >>> stores = repo.get_all_by_object_id(object_id=42)
            >>> for store in stores:
            ...     print(f"Package {store.package_id}: {store.version_uuid}")
        """
        return self.filter_by(object_id=object_id)
    
    def get_by_package(self, package_id: int) -> List[DataStore]:
        """
        Get all data stores in a package.
        
        This method returns all data stores that belong to a specific package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of DataStore objects
        
        Example:
            >>> # Get all data stores in the base package
            >>> stores = repo.get_by_package(package_id=1)
            >>> print(f"Found {len(stores)} data stores in base package")
        """
        return self.filter_by(package_id=package_id)
    
    def get_by_uuid(self, uuid: str) -> Optional[DataStore]:
        """
        Get data store by UUID.
        
        Note: This returns the first data store found with the UUID.
        Since UUIDs may exist in multiple packages, consider using
        get_by_object_and_package() for package-specific queries.
        
        Args:
            uuid: Data store UUID
        
        Returns:
            DataStore or None if not found
        """
        return self.find_one(uuid=uuid)
