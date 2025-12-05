"""
Package Object Mapping Repository

Provides data access for package_object_mappings junction table.
Tracks which objects belong to which packages.
"""

from typing import List, Dict, Optional
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from models import db, PackageObjectMapping, ObjectLookup, Package
from repositories.base_repository import BaseRepository


class PackageObjectMappingRepository(BaseRepository[PackageObjectMapping]):
    """
    Repository for PackageObjectMapping entities.
    
    Manages the junction table that tracks which objects belong to which packages.
    This enables the package-agnostic object_lookup design.
    
    Key Methods:
        - create_mapping: Create single package-object mapping
        - bulk_create_mappings: Optimized bulk creation
        - get_objects_in_package: Get all objects for a package
        - get_packages_for_object: Get all packages containing an object
    """
    
    def __init__(self):
        """Initialize repository with PackageObjectMapping model."""
        super().__init__(PackageObjectMapping)
    
    def create_mapping(
        self,
        package_id: int,
        object_id: int
    ) -> PackageObjectMapping:
        """
        Create a package-object mapping.
        
        Args:
            package_id: Package ID
            object_id: Object ID (from object_lookup)
            
        Returns:
            PackageObjectMapping: Created mapping
            
        Raises:
            IntegrityError: If mapping already exists (unique constraint)
            
        Example:
            >>> mapping = repo.create_mapping(package_id=1, object_id=42)
        """
        mapping = PackageObjectMapping(
            package_id=package_id,
            object_id=object_id
        )
        self.db.session.add(mapping)
        self.db.session.flush()
        return mapping
    
    def bulk_create_mappings(
        self,
        mappings: List[Dict[str, int]]
    ) -> None:
        """
        Optimized bulk creation of package-object mappings.
        
        Creates multiple mappings efficiently using bulk insert.
        Ignores duplicates (unique constraint violations).
        
        Args:
            mappings: List of dicts with keys: package_id, object_id
            
        Example:
            >>> mappings = [
            ...     {"package_id": 1, "object_id": 10},
            ...     {"package_id": 1, "object_id": 11},
            ...     {"package_id": 1, "object_id": 12}
            ... ]
            >>> repo.bulk_create_mappings(mappings)
        """
        if not mappings:
            return
        
        # Create mapping objects
        mapping_objects = [
            PackageObjectMapping(
                package_id=m['package_id'],
                object_id=m['object_id']
            )
            for m in mappings
        ]
        
        # Bulk insert
        self.db.session.bulk_save_objects(mapping_objects)
        self.db.session.flush()
    
    def get_objects_in_package(
        self,
        package_id: int
    ) -> List[ObjectLookup]:
        """
        Get all objects in a package with optimized query.
        
        Joins package_object_mappings with object_lookup to return
        full object details for all objects in the package.
        Uses efficient join to minimize query overhead.
        
        Args:
            package_id: Package ID
            
        Returns:
            List of ObjectLookup objects
            
        Example:
            >>> objects = repo.get_objects_in_package(package_id=1)
            >>> for obj in objects:
            ...     print(f"{obj.name} ({obj.object_type})")
        """
        return self.db.session.query(ObjectLookup).join(
            PackageObjectMapping,
            ObjectLookup.id == PackageObjectMapping.object_id
        ).filter(
            PackageObjectMapping.package_id == package_id
        ).all()
    
    def get_objects_in_package_by_type(
        self,
        package_id: int,
        object_type: str
    ) -> List[ObjectLookup]:
        """
        Get objects in a package filtered by type.
        
        Args:
            package_id: Package ID
            object_type: Object type to filter by
            
        Returns:
            List of ObjectLookup objects
            
        Example:
            >>> interfaces = repo.get_objects_in_package_by_type(
            ...     package_id=1,
            ...     object_type="Interface"
            ... )
        """
        return self.db.session.query(ObjectLookup).join(
            PackageObjectMapping,
            ObjectLookup.id == PackageObjectMapping.object_id
        ).filter(
            and_(
                PackageObjectMapping.package_id == package_id,
                ObjectLookup.object_type == object_type
            )
        ).all()
    
    def get_packages_for_object(
        self,
        object_id: int
    ) -> List[Package]:
        """
        Get all packages containing an object.
        
        Useful for determining which packages share a common object.
        
        Args:
            object_id: Object ID (from object_lookup)
            
        Returns:
            List of Package objects
            
        Example:
            >>> packages = repo.get_packages_for_object(object_id=42)
            >>> print(f"Object appears in {len(packages)} packages")
        """
        return self.db.session.query(Package).join(
            PackageObjectMapping,
            Package.id == PackageObjectMapping.package_id
        ).filter(
            PackageObjectMapping.object_id == object_id
        ).all()
    
    def mapping_exists(
        self,
        package_id: int,
        object_id: int
    ) -> bool:
        """
        Check if a mapping exists.
        
        Args:
            package_id: Package ID
            object_id: Object ID
            
        Returns:
            True if mapping exists, False otherwise
            
        Example:
            >>> if repo.mapping_exists(package_id=1, object_id=42):
            ...     print("Object already in package")
        """
        return self.exists(package_id=package_id, object_id=object_id)
    
    def get_object_count_by_package(
        self,
        package_id: int
    ) -> int:
        """
        Count objects in a package.
        
        Args:
            package_id: Package ID
            
        Returns:
            Number of objects in package
            
        Example:
            >>> count = repo.get_object_count_by_package(package_id=1)
            >>> print(f"Package contains {count} objects")
        """
        return self.count(package_id=package_id)
    
    def get_shared_objects(
        self,
        package_id_1: int,
        package_id_2: int
    ) -> List[ObjectLookup]:
        """
        Get objects that exist in both packages.
        
        Useful for finding common objects between packages.
        
        Args:
            package_id_1: First package ID
            package_id_2: Second package ID
            
        Returns:
            List of ObjectLookup objects present in both packages
            
        Example:
            >>> shared = repo.get_shared_objects(
            ...     package_id_1=1,  # Base package
            ...     package_id_2=2   # Customized package
            ... )
            >>> print(f"Found {len(shared)} shared objects")
        """
        # Subquery for objects in package 1
        pkg1_objects = self.db.session.query(
            PackageObjectMapping.object_id
        ).filter(
            PackageObjectMapping.package_id == package_id_1
        ).subquery()
        
        # Query for objects in package 2 that are also in package 1
        return self.db.session.query(ObjectLookup).join(
            PackageObjectMapping,
            ObjectLookup.id == PackageObjectMapping.object_id
        ).filter(
            and_(
                PackageObjectMapping.package_id == package_id_2,
                PackageObjectMapping.object_id.in_(pkg1_objects)
            )
        ).all()
    
    def get_unique_objects(
        self,
        package_id: int,
        other_package_id: int
    ) -> List[ObjectLookup]:
        """
        Get objects unique to a package (not in other package).
        
        Useful for finding NEW or DEPRECATED objects.
        
        Args:
            package_id: Package to get unique objects from
            other_package_id: Package to compare against
            
        Returns:
            List of ObjectLookup objects only in package_id
            
        Example:
            >>> new_objects = repo.get_unique_objects(
            ...     package_id=3,      # New vendor package
            ...     other_package_id=1 # Base package
            ... )
            >>> print(f"Found {len(new_objects)} NEW objects")
        """
        # Subquery for objects in other package
        other_objects = self.db.session.query(
            PackageObjectMapping.object_id
        ).filter(
            PackageObjectMapping.package_id == other_package_id
        ).subquery()
        
        # Query for objects in package that are NOT in other package
        return self.db.session.query(ObjectLookup).join(
            PackageObjectMapping,
            ObjectLookup.id == PackageObjectMapping.object_id
        ).filter(
            and_(
                PackageObjectMapping.package_id == package_id,
                ~PackageObjectMapping.object_id.in_(other_objects)
            )
        ).all()
    
    def delete_mappings_for_package(
        self,
        package_id: int
    ) -> int:
        """
        Delete all mappings for a package.
        
        Args:
            package_id: Package ID
            
        Returns:
            Number of mappings deleted
            
        Example:
            >>> deleted = repo.delete_mappings_for_package(package_id=1)
            >>> print(f"Deleted {deleted} mappings")
        """
        count = self.count(package_id=package_id)
        self.db.session.query(PackageObjectMapping).filter(
            PackageObjectMapping.package_id == package_id
        ).delete()
        self.db.session.flush()
        return count
