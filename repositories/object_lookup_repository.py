"""
Object Lookup Repository

Provides data access for the global object registry (object_lookup table).
Implements find_or_create to prevent duplicate objects.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy import func
from models import db, ObjectLookup
from repositories.base_repository import BaseRepository
from core.cache import ObjectLookupCache


class ObjectLookupRepository(BaseRepository[ObjectLookup]):
    """
    Repository for ObjectLookup entities.
    
    Manages the global object registry ensuring each UUID appears exactly once.
    This is the single source of truth for all objects across all packages.
    
    Key Methods:
        - find_or_create: Ensures no duplicate objects (CRITICAL)
        - find_by_uuid: Find object by UUID
        - bulk_find_or_create: Optimized bulk operation
    """
    
    def __init__(self):
        """Initialize repository with ObjectLookup model and cache."""
        super().__init__(ObjectLookup)
        self.cache = ObjectLookupCache()
    
    def find_by_uuid(self, uuid: str) -> Optional[ObjectLookup]:
        """
        Find object by UUID with caching.
        
        Checks cache first, then queries database if not found.
        Caches result for 5 minutes.
        
        Args:
            uuid: Object UUID
            
        Returns:
            ObjectLookup if found, None otherwise
            
        Example:
            >>> obj = repo.find_by_uuid("abc-123-def")
        """
        # Check cache first
        cached_obj = self.cache.get_by_uuid(uuid)
        if cached_obj is not None:
            return cached_obj
        
        # Query database
        obj = self.find_one(uuid=uuid)
        
        # Cache result if found
        if obj is not None:
            self.cache.set_by_uuid(uuid, obj)
        
        return obj
    
    def find_or_create(
        self,
        uuid: str,
        name: str,
        object_type: str,
        description: Optional[str] = None
    ) -> ObjectLookup:
        """
        Find existing object or create new one with caching.
        
        CRITICAL: This method ensures no duplicates in object_lookup.
        Always use this method instead of create() to prevent duplicate UUIDs.
        
        Args:
            uuid: Object UUID (unique identifier)
            name: Object name
            object_type: Object type (Interface, Process Model, etc.)
            description: Optional description
            
        Returns:
            ObjectLookup: Existing or newly created object
            
        Example:
            >>> obj = repo.find_or_create(
            ...     uuid="abc-123",
            ...     name="My Interface",
            ...     object_type="Interface"
            ... )
            >>> # Calling again with same UUID returns same object
            >>> obj2 = repo.find_or_create(
            ...     uuid="abc-123",
            ...     name="My Interface",
            ...     object_type="Interface"
            ... )
            >>> assert obj.id == obj2.id  # Same object!
        """
        # Ensure name is never None (NOT NULL constraint)
        if name is None or name == '':
            name = 'Unknown'
        
        # Try to find existing object (uses cache)
        existing = self.find_by_uuid(uuid)
        
        if existing:
            # Ensure object is bound to current session
            existing = self.db.session.merge(existing)
            
            # Update name and description if they've changed
            if existing.name != name:
                existing.name = name
                # Invalidate cache since object changed
                self.cache.invalidate_by_uuid(uuid)
            if description and existing.description != description:
                existing.description = description
                # Invalidate cache since object changed
                self.cache.invalidate_by_uuid(uuid)
            self.db.session.flush()
            return existing
        
        # Create new object
        new_object = ObjectLookup(
            uuid=uuid,
            name=name,
            object_type=object_type,
            description=description
        )
        self.db.session.add(new_object)
        self.db.session.flush()
        
        # Cache the new object
        self.cache.set_by_uuid(uuid, new_object)
        
        return new_object
    
    def bulk_find_or_create(
        self,
        objects: List[Dict[str, Any]]
    ) -> List[ObjectLookup]:
        """
        Optimized bulk find_or_create operation.
        
        Processes multiple objects efficiently by:
        1. Fetching all existing objects in one query
        2. Creating only new objects
        3. Returning all objects in order
        
        Args:
            objects: List of dicts with keys: uuid, name, object_type, description
            
        Returns:
            List of ObjectLookup objects in same order as input
            
        Example:
            >>> objects = [
            ...     {"uuid": "abc-1", "name": "Obj1", "object_type": "Interface"},
            ...     {"uuid": "abc-2", "name": "Obj2", "object_type": "Process Model"}
            ... ]
            >>> results = repo.bulk_find_or_create(objects)
        """
        if not objects:
            return []
        
        # Extract UUIDs
        uuids = [obj['uuid'] for obj in objects]
        
        # Fetch all existing objects in one query
        existing_objects = self.db.session.query(ObjectLookup).filter(
            ObjectLookup.uuid.in_(uuids)
        ).all()
        
        # Create lookup map
        existing_map = {obj.uuid: obj for obj in existing_objects}
        
        # Identify new objects
        new_objects = []
        for obj_data in objects:
            if obj_data['uuid'] not in existing_map:
                new_obj = ObjectLookup(
                    uuid=obj_data['uuid'],
                    name=obj_data['name'],
                    object_type=obj_data['object_type'],
                    description=obj_data.get('description')
                )
                new_objects.append(new_obj)
                existing_map[obj_data['uuid']] = new_obj
        
        # Bulk insert new objects
        if new_objects:
            self.db.session.bulk_save_objects(new_objects, return_defaults=True)
            self.db.session.flush()
        
        # Return objects in original order
        return [existing_map[obj['uuid']] for obj in objects]
    
    def get_by_type(self, object_type: str) -> List[ObjectLookup]:
        """
        Get all objects of a specific type.
        
        Args:
            object_type: Object type to filter by
            
        Returns:
            List of ObjectLookup objects
            
        Example:
            >>> interfaces = repo.get_by_type("Interface")
        """
        return self.filter_by(object_type=object_type)
    
    def search_by_name(self, name_pattern: str) -> List[ObjectLookup]:
        """
        Search objects by name pattern.
        
        Args:
            name_pattern: Name pattern to search (case-insensitive)
            
        Returns:
            List of matching ObjectLookup objects
            
        Example:
            >>> results = repo.search_by_name("%user%")
        """
        return self.db.session.query(ObjectLookup).filter(
            ObjectLookup.name.ilike(f"%{name_pattern}%")
        ).all()
    
    def get_duplicate_uuids(self) -> List[tuple]:
        """
        Find duplicate UUIDs (should always return empty list).
        
        This is a validation query to ensure data integrity.
        Should always return empty list if find_or_create is used correctly.
        
        Returns:
            List of tuples (uuid, count) for duplicates
            
        Example:
            >>> duplicates = repo.get_duplicate_uuids()
            >>> assert len(duplicates) == 0, "Found duplicate UUIDs!"
        """
        return self.db.session.query(
            ObjectLookup.uuid,
            func.count(ObjectLookup.id).label('count')
        ).group_by(
            ObjectLookup.uuid
        ).having(
            func.count(ObjectLookup.id) > 1
        ).all()
    
    def count_by_type(self) -> List[tuple]:
        """
        Count objects by type.
        
        Returns:
            List of tuples (object_type, count)
            
        Example:
            >>> counts = repo.count_by_type()
            >>> for obj_type, count in counts:
            ...     print(f"{obj_type}: {count}")
        """
        return self.db.session.query(
            ObjectLookup.object_type,
            func.count(ObjectLookup.id).label('count')
        ).group_by(
            ObjectLookup.object_type
        ).all()
