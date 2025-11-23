"""
Appian object repository for managing AppianObject model data access.

This module provides data access methods for the AppianObject model,
which stores normalized Appian object data from packages.
"""

from typing import List, Optional
from core.base_repository import BaseRepository
from models import AppianObject


class AppianObjectRepository(BaseRepository[AppianObject]):
    """
    Repository for AppianObject model operations.

    Provides data access methods for managing Appian objects within packages,
    including queries by UUID, name, type, and package relationships.

    Example:
        >>> repo = AppianObjectRepository()
        >>> obj = repo.create(
        ...     package_id=1,
        ...     uuid='_a-0001ed6e-54f1-8000-9df6-011c48011c48',
        ...     name='MyInterface',
        ...     object_type='Interface',
        ...     sail_code='a!localVariables(...)'
        ... )
        >>> interfaces = repo.get_by_type(1, 'Interface')
    """

    def __init__(self):
        """Initialize AppianObjectRepository with AppianObject model."""
        super().__init__(AppianObject)

    def get_by_package_id(self, package_id: int) -> List[AppianObject]:
        """
        Get all objects for a specific package.

        Args:
            package_id: ID of the package

        Returns:
            List[AppianObject]: List of objects in the package

        Example:
            >>> objects = repo.get_by_package_id(package_id=1)
        """
        return self.filter_by(package_id=package_id)

    def get_by_uuid(
        self,
        package_id: int,
        uuid: str
    ) -> Optional[AppianObject]:
        """
        Get an object by UUID within a package.

        Args:
            package_id: ID of the package
            uuid: UUID of the object

        Returns:
            Optional[AppianObject]: Object if found, None otherwise

        Example:
            >>> obj = repo.get_by_uuid(
            ...     1,
            ...     '_a-0001ed6e-54f1-8000-9df6-011c48011c48'
            ... )
        """
        return self.find_one(package_id=package_id, uuid=uuid)

    def get_by_type(
        self,
        package_id: int,
        object_type: str
    ) -> List[AppianObject]:
        """
        Get all objects of a specific type in a package.

        Args:
            package_id: ID of the package
            object_type: Type of object (e.g., 'Interface', 'Process Model')

        Returns:
            List[AppianObject]: List of objects with the specified type

        Example:
            >>> interfaces = repo.get_by_type(1, 'Interface')
            >>> process_models = repo.get_by_type(1, 'Process Model')
        """
        return (self.model_class.query
                .filter_by(package_id=package_id, object_type=object_type)
                .order_by(self.model_class.name.asc())
                .all())

    def get_by_name(
        self,
        package_id: int,
        name: str
    ) -> List[AppianObject]:
        """
        Get objects by name within a package.

        Args:
            package_id: ID of the package
            name: Name of the object

        Returns:
            List[AppianObject]: List of objects with the specified name

        Example:
            >>> objects = repo.get_by_name(1, 'MyInterface')
        """
        return self.filter_by(package_id=package_id, name=name)

    def search_by_name(
        self,
        package_id: int,
        search_term: str
    ) -> List[AppianObject]:
        """
        Search objects by name pattern within a package.

        Args:
            package_id: ID of the package
            search_term: Search term to match in object names

        Returns:
            List[AppianObject]: List of objects with matching names

        Example:
            >>> results = repo.search_by_name(1, 'Interface')
        """
        return (self.model_class.query
                .filter_by(package_id=package_id)
                .filter(self.model_class.name.contains(search_term))
                .order_by(self.model_class.name.asc())
                .all())

    def get_by_version_uuid(
        self,
        package_id: int,
        version_uuid: str
    ) -> List[AppianObject]:
        """
        Get objects by version UUID within a package.

        Args:
            package_id: ID of the package
            version_uuid: Version UUID of the object

        Returns:
            List[AppianObject]: List of objects with the specified
                version UUID

        Example:
            >>> objects = repo.get_by_version_uuid(1, 'version-uuid-123')
        """
        return self.filter_by(package_id=package_id, version_uuid=version_uuid)

    def get_objects_with_sail_code(
        self,
        package_id: int
    ) -> List[AppianObject]:
        """
        Get all objects that have SAIL code in a package.

        Args:
            package_id: ID of the package

        Returns:
            List[AppianObject]: List of objects with SAIL code

        Example:
            >>> sail_objects = repo.get_objects_with_sail_code(1)
        """
        return (self.model_class.query
                .filter_by(package_id=package_id)
                .filter(self.model_class.sail_code.isnot(None))
                .filter(self.model_class.sail_code != '')
                .order_by(self.model_class.name.asc())
                .all())

    def get_process_models(self, package_id: int) -> List[AppianObject]:
        """
        Get all process model objects in a package.

        Args:
            package_id: ID of the package

        Returns:
            List[AppianObject]: List of process model objects

        Example:
            >>> process_models = repo.get_process_models(1)
        """
        return self.get_by_type(package_id, 'Process Model')

    def get_interfaces(self, package_id: int) -> List[AppianObject]:
        """
        Get all interface objects in a package.

        Args:
            package_id: ID of the package

        Returns:
            List[AppianObject]: List of interface objects

        Example:
            >>> interfaces = repo.get_interfaces(1)
        """
        return self.get_by_type(package_id, 'Interface')

    def get_expression_rules(self, package_id: int) -> List[AppianObject]:
        """
        Get all expression rule objects in a package.

        Args:
            package_id: ID of the package

        Returns:
            List[AppianObject]: List of expression rule objects

        Example:
            >>> rules = repo.get_expression_rules(1)
        """
        return self.get_by_type(package_id, 'Expression Rule')

    def count_by_type(
        self,
        package_id: int,
        object_type: str
    ) -> int:
        """
        Count objects by type in a package.

        Args:
            package_id: ID of the package
            object_type: Type of object to count

        Returns:
            int: Number of objects with the specified type

        Example:
            >>> interface_count = repo.count_by_type(1, 'Interface')
        """
        return self.count(package_id=package_id, object_type=object_type)

    def get_type_summary(self, package_id: int) -> dict[str, int]:
        """
        Get summary of objects by type in a package.

        Args:
            package_id: ID of the package

        Returns:
            dict: Dictionary mapping object type to count

        Example:
            >>> summary = repo.get_type_summary(package_id=1)
            >>> # Returns: {'Interface': 25, 'Process Model': 10, ...}
        """
        objects = self.get_by_package_id(package_id)
        summary: dict[str, int] = {}
        for obj in objects:
            obj_type = obj.object_type
            summary[obj_type] = summary.get(obj_type, 0) + 1
        return summary

    def get_objects_by_uuids(
        self,
        package_id: int,
        uuids: List[str]
    ) -> List[AppianObject]:
        """
        Get multiple objects by their UUIDs.

        Args:
            package_id: ID of the package
            uuids: List of object UUIDs

        Returns:
            List[AppianObject]: List of objects with matching UUIDs

        Example:
            >>> uuids = ['uuid1', 'uuid2', 'uuid3']
            >>> objects = repo.get_objects_by_uuids(1, uuids)
        """
        return (self.model_class.query
                .filter_by(package_id=package_id)
                .filter(self.model_class.uuid.in_(uuids))
                .all())

    def get_objects_with_dependencies(
        self,
        package_id: int
    ) -> List[AppianObject]:
        """
        Get all objects that have dependencies (as parent or child).

        Args:
            package_id: ID of the package

        Returns:
            List[AppianObject]: List of objects with dependencies

        Example:
            >>> objects = repo.get_objects_with_dependencies(1)
        """
        return (self.model_class.query
                .filter_by(package_id=package_id)
                .filter(
                    (self.model_class.dependencies_as_parent.any()) |
                    (self.model_class.dependencies_as_child.any())
                )
                .all())

    def get_objects_with_process_metadata(
        self,
        package_id: int
    ) -> List[AppianObject]:
        """
        Get all objects that have process model metadata.

        Args:
            package_id: ID of the package

        Returns:
            List[AppianObject]: List of objects with process metadata

        Example:
            >>> process_objects = repo.get_objects_with_process_metadata(1)
        """
        return (self.model_class.query
                .filter_by(package_id=package_id)
                .filter(self.model_class.process_model_metadata.isnot(None))
                .all())

    def delete_by_package(self, package_id: int) -> int:
        """
        Delete all objects for a package.

        Args:
            package_id: ID of the package

        Returns:
            int: Number of objects deleted

        Example:
            >>> deleted = repo.delete_by_package(package_id=1)
        """
        objects = self.get_by_package_id(package_id)
        count = len(objects)
        for obj in objects:
            self.db.session.delete(obj)
        self.db.session.commit()
        return count

    def bulk_create(
        self,
        objects_data: List[dict]
    ) -> List[AppianObject]:
        """
        Create multiple objects in a single transaction.

        Args:
            objects_data: List of dictionaries with object attributes

        Returns:
            List[AppianObject]: List of created objects

        Example:
            >>> objects_data = [
            ...     {'package_id': 1, 'uuid': 'uuid1', 'name': 'Obj1',
            ...      'object_type': 'Interface'},
            ...     {'package_id': 1, 'uuid': 'uuid2', 'name': 'Obj2',
            ...      'object_type': 'Interface'}
            ... ]
            >>> objects = repo.bulk_create(objects_data)
        """
        objects = [self.model_class(**data) for data in objects_data]
        self.db.session.bulk_save_objects(objects, return_defaults=True)
        self.db.session.commit()
        return objects

    def get_paginated(
        self,
        package_id: int,
        page: int = 1,
        per_page: int = 50
    ) -> tuple[List[AppianObject], int]:
        """
        Get paginated objects for a package.

        Args:
            package_id: ID of the package
            page: Page number (1-indexed)
            per_page: Number of objects per page

        Returns:
            tuple: (list of objects, total count)

        Example:
            >>> objects, total = repo.get_paginated(1, page=2, per_page=50)
        """
        query = (self.model_class.query
                 .filter_by(package_id=package_id)
                 .order_by(self.model_class.name.asc()))

        total = query.count()
        objects = query.offset((page - 1) * per_page).limit(per_page).all()

        return (objects, total)

    def find_by_uuid_across_packages(
        self,
        uuid: str
    ) -> List[AppianObject]:
        """
        Find objects with a specific UUID across all packages.

        Args:
            uuid: UUID to search for

        Returns:
            List[AppianObject]: List of objects with the UUID

        Example:
            >>> objects = repo.find_by_uuid_across_packages(
            ...     '_a-0001ed6e-54f1-8000-9df6-011c48011c48'
            ... )
        """
        return self.filter_by(uuid=uuid)
