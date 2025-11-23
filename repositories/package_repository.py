"""
Package repository for managing Package model data access.

This module provides data access methods for the Package model,
which stores individual package information (base, customized, new_vendor).
"""

from typing import List, Optional
from core.base_repository import BaseRepository
from models import Package


class PackageRepository(BaseRepository[Package]):
    """
    Repository for Package model operations.

    Provides data access methods for managing packages within merge sessions,
    including package creation, retrieval by type, and metadata management.

    Example:
        >>> repo = PackageRepository()
        >>> package = repo.create(
        ...     session_id=1,
        ...     package_type='base',
        ...     package_name='AppV1.0',
        ...     total_objects=500
        ... )
        >>> base_pkg = repo.get_by_session_and_type(1, 'base')
    """

    def __init__(self):
        """Initialize PackageRepository with Package model."""
        super().__init__(Package)

    def get_by_session_id(self, session_id: int) -> List[Package]:
        """
        Get all packages for a specific session.

        Args:
            session_id: ID of the merge session

        Returns:
            List[Package]: List of packages in the session

        Example:
            >>> packages = repo.get_by_session_id(session_id=1)
        """
        return self.filter_by(session_id=session_id)

    def get_by_session_and_type(
        self,
        session_id: int,
        package_type: str
    ) -> Optional[Package]:
        """
        Get a specific package by session and type.

        Args:
            session_id: ID of the merge session
            package_type: Type of package ('base', 'customized',
                'new_vendor')

        Returns:
            Optional[Package]: Package if found, None otherwise

        Example:
            >>> base = repo.get_by_session_and_type(1, 'base')
            >>> custom = repo.get_by_session_and_type(1, 'customized')
        """
        return self.find_one(session_id=session_id, package_type=package_type)

    def get_base_package(self, session_id: int) -> Optional[Package]:
        """
        Get the base package for a session.

        Args:
            session_id: ID of the merge session

        Returns:
            Optional[Package]: Base package if found, None otherwise

        Example:
            >>> base = repo.get_base_package(session_id=1)
        """
        return self.get_by_session_and_type(session_id, 'base')

    def get_customized_package(self, session_id: int) -> Optional[Package]:
        """
        Get the customized package for a session.

        Args:
            session_id: ID of the merge session

        Returns:
            Optional[Package]: Customized package if found, None otherwise

        Example:
            >>> custom = repo.get_customized_package(session_id=1)
        """
        return self.get_by_session_and_type(session_id, 'customized')

    def get_new_vendor_package(self, session_id: int) -> Optional[Package]:
        """
        Get the new vendor package for a session.

        Args:
            session_id: ID of the merge session

        Returns:
            Optional[Package]: New vendor package if found, None otherwise

        Example:
            >>> vendor = repo.get_new_vendor_package(session_id=1)
        """
        return self.get_by_session_and_type(session_id, 'new_vendor')

    def get_all_three_packages(
        self,
        session_id: int
    ) -> tuple[Optional[Package], Optional[Package], Optional[Package]]:
        """
        Get all three packages for a session (base, customized, new_vendor).

        Args:
            session_id: ID of the merge session

        Returns:
            tuple: (base_package, customized_package, new_vendor_package)

        Example:
            >>> base, custom, vendor = repo.get_all_three_packages(1)
        """
        base = self.get_base_package(session_id)
        customized = self.get_customized_package(session_id)
        new_vendor = self.get_new_vendor_package(session_id)
        return (base, customized, new_vendor)

    def update_metadata(
        self,
        package_id: int,
        total_objects: Optional[int] = None,
        generation_time: Optional[float] = None
    ) -> Optional[Package]:
        """
        Update package metadata.

        Args:
            package_id: ID of the package to update
            total_objects: Total number of objects in package
            generation_time: Time taken to generate blueprint

        Returns:
            Optional[Package]: Updated package if found, None otherwise

        Example:
            >>> package = repo.update_metadata(
            ...     package_id=1,
            ...     total_objects=500,
            ...     generation_time=12.5
            ... )
        """
        package = self.get_by_id(package_id)
        if package:
            if total_objects is not None:
                package.total_objects = total_objects
            if generation_time is not None:
                package.generation_time = generation_time
            self.update(package)
        return package

    def get_by_package_name(self, package_name: str) -> List[Package]:
        """
        Get all packages with a specific name.

        Args:
            package_name: Name of the package

        Returns:
            List[Package]: List of packages with the specified name

        Example:
            >>> packages = repo.get_by_package_name('AppV1.0')
        """
        return self.filter_by(package_name=package_name)

    def count_by_session(self, session_id: int) -> int:
        """
        Count packages in a session.

        Args:
            session_id: ID of the merge session

        Returns:
            int: Number of packages in the session

        Example:
            >>> count = repo.count_by_session(session_id=1)
        """
        return self.count(session_id=session_id)

    def get_package_types_in_session(
        self,
        session_id: int
    ) -> List[str]:
        """
        Get list of package types present in a session.

        Args:
            session_id: ID of the merge session

        Returns:
            List[str]: List of package types in the session

        Example:
            >>> types = repo.get_package_types_in_session(session_id=1)
            >>> # Returns: ['base', 'customized', 'new_vendor']
        """
        packages = self.get_by_session_id(session_id)
        return [pkg.package_type for pkg in packages]

    def has_all_packages(self, session_id: int) -> bool:
        """
        Check if a session has all three required packages.

        Args:
            session_id: ID of the merge session

        Returns:
            bool: True if all three packages exist, False otherwise

        Example:
            >>> if repo.has_all_packages(session_id=1):
            ...     print("Ready to compare")
        """
        types = self.get_package_types_in_session(session_id)
        required = {'base', 'customized', 'new_vendor'}
        return required.issubset(set(types))

    def get_total_objects_by_session(self, session_id: int) -> int:
        """
        Get total number of objects across all packages in a session.

        Args:
            session_id: ID of the merge session

        Returns:
            int: Total number of objects

        Example:
            >>> total = repo.get_total_objects_by_session(session_id=1)
        """
        packages = self.get_by_session_id(session_id)
        return sum(pkg.total_objects or 0 for pkg in packages)

    def delete_by_session(self, session_id: int) -> int:
        """
        Delete all packages for a session.

        Args:
            session_id: ID of the merge session

        Returns:
            int: Number of packages deleted

        Example:
            >>> deleted = repo.delete_by_session(session_id=1)
        """
        packages = self.get_by_session_id(session_id)
        count = len(packages)
        for package in packages:
            self.db.session.delete(package)
        self.db.session.commit()
        return count
