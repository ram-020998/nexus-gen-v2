"""
CDT Repository

Provides data access for CDT (Custom Data Type) objects and related entities.
Handles storage of CDT-specific data including fields.
"""

from typing import Optional, List, Dict, Any
from models import CDT, CDTField
from repositories.base_repository import BaseRepository


class CDTRepository(BaseRepository[CDT]):
    """
    Repository for CDT entities.
    
    Manages CDT objects with their fields.
    Each CDT is linked to object_lookup via object_id.
    
    Key Methods:
        - create_cdt: Create CDT with fields
        - get_by_object_id: Get CDT by object_lookup ID
        - get_by_uuid: Get CDT by UUID
    """
    
    def __init__(self):
        """Initialize repository with CDT model."""
        super().__init__(CDT)
    
    def create_cdt(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        namespace: Optional[str] = None,
        description: Optional[str] = None,
        fields: Optional[List[Dict[str, Any]]] = None
    ) -> CDT:
        """
        Create CDT with fields.
        
        Args:
            object_id: Reference to object_lookup
            package_id: Reference to package (REQUIRED)
            uuid: CDT UUID
            name: CDT name
            version_uuid: Version UUID
            namespace: Namespace
            description: Description
            fields: List of field dicts with keys:
                - field_name
                - field_type
                - is_list
                - is_required
                - display_order
        
        Returns:
            Created CDT object
        
        Example:
            >>> cdt = repo.create_cdt(
            ...     object_id=42,
            ...     package_id=1,
            ...     uuid="abc-123",
            ...     name="My CDT",
            ...     fields=[
            ...         {"field_name": "id", "field_type": "Number", "is_required": True}
            ...     ]
            ... )
        """
        # Create CDT
        cdt = CDT(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            namespace=namespace,
            description=description
        )
        self.db.session.add(cdt)
        self.db.session.flush()
        
        # Create fields
        if fields:
            for field_data in fields:
                field = CDTField(
                    cdt_id=cdt.id,
                    field_name=field_data.get('field_name'),
                    field_type=field_data.get('field_type'),
                    is_list=field_data.get('is_list', False),
                    is_required=field_data.get('is_required', False),
                    display_order=field_data.get('display_order')
                )
                self.db.session.add(field)
        
        self.db.session.flush()
        return cdt
    
    def get_by_object_id(self, object_id: int) -> Optional[CDT]:
        """
        Get CDT by object_lookup ID.
        
        Note: This returns the first CDT found for the object.
        Use get_all_by_object_id() to get all package versions.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            CDT or None if not found
        """
        return self.find_one(object_id=object_id)
    
    def get_by_object_and_package(
        self, 
        object_id: int, 
        package_id: int
    ) -> Optional[CDT]:
        """
        Get CDT by object_lookup ID and package ID.
        
        This method returns the specific version of a CDT for a given package.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
        
        Returns:
            CDT or None if not found
        
        Example:
            >>> # Get the customized version of a CDT
            >>> cdt = repo.get_by_object_and_package(
            ...     object_id=42,
            ...     package_id=2  # Customized package
            ... )
        """
        return self.find_one(object_id=object_id, package_id=package_id)
    
    def get_all_by_object_id(self, object_id: int) -> List[CDT]:
        """
        Get all CDTs for an object across all packages.
        
        This method returns all package versions of a CDT.
        Useful when you need to compare versions across packages.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            List of CDT objects (one per package)
        
        Example:
            >>> # Get all versions of a CDT
            >>> cdts = repo.get_all_by_object_id(object_id=42)
            >>> for cdt in cdts:
            ...     print(f"Package {cdt.package_id}: {cdt.version_uuid}")
        """
        return self.filter_by(object_id=object_id)
    
    def get_by_package(self, package_id: int) -> List[CDT]:
        """
        Get all CDTs in a package.
        
        This method returns all CDTs that belong to a specific package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of CDT objects
        
        Example:
            >>> # Get all CDTs in the base package
            >>> cdts = repo.get_by_package(package_id=1)
            >>> print(f"Found {len(cdts)} CDTs in base package")
        """
        return self.filter_by(package_id=package_id)
    
    def get_by_uuid(self, uuid: str) -> Optional[CDT]:
        """
        Get CDT by UUID.
        
        Note: This returns the first CDT found with the UUID.
        Since UUIDs may exist in multiple packages, consider using
        get_by_object_and_package() for package-specific queries.
        
        Args:
            uuid: CDT UUID
        
        Returns:
            CDT or None if not found
        """
        return self.find_one(uuid=uuid)
    
    def get_fields(self, cdt_id: int) -> List[CDTField]:
        """
        Get all fields for a CDT.
        
        Args:
            cdt_id: CDT ID
        
        Returns:
            List of CDTField objects
        """
        return self.db.session.query(CDTField).filter_by(
            cdt_id=cdt_id
        ).order_by(CDTField.display_order).all()
