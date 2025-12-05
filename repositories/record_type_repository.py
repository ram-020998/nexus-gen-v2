"""
Record Type Repository

Provides data access for Record Type objects and related entities.
Handles storage of record type-specific data including fields, relationships, views, and actions.
"""

from typing import Optional, List, Dict, Any
from models import db, RecordType, RecordTypeField, RecordTypeRelationship, RecordTypeView, RecordTypeAction
from repositories.base_repository import BaseRepository


class RecordTypeRepository(BaseRepository[RecordType]):
    """
    Repository for RecordType entities.
    
    Manages Record Type objects with their fields, relationships, views, and actions.
    Each record type is linked to object_lookup via object_id.
    
    Key Methods:
        - create_record_type: Create record type with fields, relationships, views, and actions
        - get_by_object_id: Get record type by object_lookup ID
        - get_by_uuid: Get record type by UUID
    """
    
    def __init__(self):
        """Initialize repository with RecordType model."""
        super().__init__(RecordType)
    
    def create_record_type(
        self,
        object_id: int,
        package_id: int,
        uuid: str,
        name: str,
        version_uuid: Optional[str] = None,
        description: Optional[str] = None,
        source_type: Optional[str] = None,
        fields: Optional[List[Dict[str, Any]]] = None,
        relationships: Optional[List[Dict[str, Any]]] = None,
        views: Optional[List[Dict[str, Any]]] = None,
        actions: Optional[List[Dict[str, Any]]] = None
    ) -> RecordType:
        """
        Create record type with fields, relationships, views, and actions.
        
        Args:
            object_id: Reference to object_lookup
            package_id: Package ID (required)
            uuid: Record type UUID
            name: Record type name
            version_uuid: Version UUID
            description: Description
            source_type: Source type (e.g., 'database', 'process')
            fields: List of field dicts with keys:
                - field_name
                - field_type
                - is_primary_key
                - is_required
                - display_order
            relationships: List of relationship dicts with keys:
                - relationship_name
                - related_record_uuid
                - relationship_type
            views: List of view dicts with keys:
                - view_name
                - view_type
                - configuration (JSON string)
            actions: List of action dicts with keys:
                - action_name
                - action_type
                - configuration (JSON string)
        
        Returns:
            Created RecordType object
        
        Example:
            >>> rt = repo.create_record_type(
            ...     object_id=42,
            ...     package_id=1,
            ...     uuid="abc-123",
            ...     name="My Record Type",
            ...     fields=[
            ...         {"field_name": "id", "field_type": "Number", "is_primary_key": True}
            ...     ]
            ... )
        """
        # Create record type
        record_type = RecordType(
            object_id=object_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            version_uuid=version_uuid,
            description=description,
            source_type=source_type
        )
        self.db.session.add(record_type)
        self.db.session.flush()
        
        # Create fields
        if fields:
            for field_data in fields:
                field = RecordTypeField(
                    record_type_id=record_type.id,
                    field_name=field_data.get('field_name'),
                    field_type=field_data.get('field_type'),
                    is_primary_key=field_data.get('is_primary_key', False),
                    is_required=field_data.get('is_required', False),
                    display_order=field_data.get('display_order')
                )
                self.db.session.add(field)
        
        # Create relationships
        if relationships:
            for rel_data in relationships:
                rel = RecordTypeRelationship(
                    record_type_id=record_type.id,
                    relationship_name=rel_data.get('relationship_name'),
                    related_record_uuid=rel_data.get('related_record_uuid'),
                    relationship_type=rel_data.get('relationship_type')
                )
                self.db.session.add(rel)
        
        # Create views
        if views:
            for view_data in views:
                view = RecordTypeView(
                    record_type_id=record_type.id,
                    view_name=view_data.get('view_name'),
                    view_type=view_data.get('view_type'),
                    configuration=view_data.get('configuration')
                )
                self.db.session.add(view)
        
        # Create actions
        if actions:
            for action_data in actions:
                action = RecordTypeAction(
                    record_type_id=record_type.id,
                    action_name=action_data.get('action_name'),
                    action_type=action_data.get('action_type'),
                    configuration=action_data.get('configuration')
                )
                self.db.session.add(action)
        
        self.db.session.flush()
        return record_type
    
    def get_by_object_id(self, object_id: int) -> Optional[RecordType]:
        """
        Get record type by object_lookup ID.
        
        Note: This returns the first record type found for the object.
        Use get_all_by_object_id() to get all package versions.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            RecordType or None if not found
        """
        return self.find_one(object_id=object_id)
    
    def get_by_object_and_package(
        self, 
        object_id: int, 
        package_id: int
    ) -> Optional[RecordType]:
        """
        Get record type by object_lookup ID and package ID.
        
        This method returns the specific version of a record type for a given package.
        
        Args:
            object_id: Object lookup ID
            package_id: Package ID
        
        Returns:
            RecordType or None if not found
        
        Example:
            >>> # Get the customized version of a record type
            >>> record_type = repo.get_by_object_and_package(
            ...     object_id=42,
            ...     package_id=2  # Customized package
            ... )
        """
        return self.find_one(object_id=object_id, package_id=package_id)
    
    def get_all_by_object_id(self, object_id: int) -> List[RecordType]:
        """
        Get all record types for an object across all packages.
        
        This method returns all package versions of a record type.
        Useful when you need to compare versions across packages.
        
        Args:
            object_id: Object lookup ID
        
        Returns:
            List of RecordType objects (one per package)
        
        Example:
            >>> # Get all versions of a record type
            >>> record_types = repo.get_all_by_object_id(object_id=42)
            >>> for rt in record_types:
            ...     print(f"Package {rt.package_id}: {rt.version_uuid}")
        """
        return self.filter_by(object_id=object_id)
    
    def get_by_package(self, package_id: int) -> List[RecordType]:
        """
        Get all record types in a package.
        
        This method returns all record types that belong to a specific package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of RecordType objects
        
        Example:
            >>> # Get all record types in the base package
            >>> record_types = repo.get_by_package(package_id=1)
            >>> print(f"Found {len(record_types)} record types in base package")
        """
        return self.filter_by(package_id=package_id)
    
    def get_by_uuid(self, uuid: str) -> Optional[RecordType]:
        """
        Get record type by UUID.
        
        Args:
            uuid: Record type UUID
        
        Returns:
            RecordType or None if not found
        """
        return self.find_one(uuid=uuid)
    
    def get_fields(self, record_type_id: int) -> List[RecordTypeField]:
        """
        Get all fields for a record type.
        
        Args:
            record_type_id: Record type ID
        
        Returns:
            List of RecordTypeField objects
        """
        return self.db.session.query(RecordTypeField).filter_by(
            record_type_id=record_type_id
        ).order_by(RecordTypeField.display_order).all()
    
    def get_relationships(self, record_type_id: int) -> List[RecordTypeRelationship]:
        """
        Get all relationships for a record type.
        
        Args:
            record_type_id: Record type ID
        
        Returns:
            List of RecordTypeRelationship objects
        """
        return self.db.session.query(RecordTypeRelationship).filter_by(
            record_type_id=record_type_id
        ).all()
    
    def get_views(self, record_type_id: int) -> List[RecordTypeView]:
        """
        Get all views for a record type.
        
        Args:
            record_type_id: Record type ID
        
        Returns:
            List of RecordTypeView objects
        """
        return self.db.session.query(RecordTypeView).filter_by(
            record_type_id=record_type_id
        ).all()
    
    def get_actions(self, record_type_id: int) -> List[RecordTypeAction]:
        """
        Get all actions for a record type.
        
        Args:
            record_type_id: Record type ID
        
        Returns:
            List of RecordTypeAction objects
        """
        return self.db.session.query(RecordTypeAction).filter_by(
            record_type_id=record_type_id
        ).all()
