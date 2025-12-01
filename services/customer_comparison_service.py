"""
Customer Comparison Service

Handles comparison of delta objects against Package B (Customer Customized)
to identify customer modifications and potential conflicts.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional

from core.base_service import BaseService
from models import db, ObjectLookup, ObjectVersion
from repositories.object_lookup_repository import ObjectLookupRepository
from repositories.package_object_mapping_repository import (
    PackageObjectMappingRepository
)
from domain.entities import CustomerModification, DeltaChange
from domain.comparison_strategies import (
    SimpleVersionComparisonStrategy,
    SAILCodeComparisonStrategy
)


class CustomerComparisonService(BaseService):
    """
    Service for comparing delta objects against Package B (Customer).

    This service checks if the customer modified the same objects that
    the vendor changed. For each object in the delta:
    - Check if it exists in Package B
    - If it exists, compare it to Package A to detect modifications
    - Return comparison data for classification

    Key Design Principles:
    - Only analyzes objects from the delta (not all objects in Package B)
    - Compares customer package (B) to base package (A)
    - Uses same comparison strategies as delta comparison
    - Returns CustomerModification domain entities
    """

    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)

    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.object_lookup_repo = self._get_repository(
            ObjectLookupRepository
        )
        self.package_object_mapping_repo = self._get_repository(
            PackageObjectMappingRepository
        )

        # Initialize comparison strategies
        self.version_strategy = SimpleVersionComparisonStrategy()
        self.content_strategy = SAILCodeComparisonStrategy(
            critical_fields=['sail_code', 'fields', 'properties']
        )

    def compare(
        self,
        base_package_id: int,
        customer_package_id: int,
        delta_changes: List[DeltaChange]
    ) -> Dict[int, CustomerModification]:
        """
        Compare delta objects against customer package.

        This is the main entry point for customer comparison. It follows:
        1. Get objects in Package B (customer package)
        2. For each delta object:
           a. Check if it exists in Package B
           b. If exists, compare B to A to detect customer modifications
           c. Create CustomerModification entity
        3. Return dict mapping object_id to CustomerModification

        Args:
            base_package_id: Package A (Base) ID
            customer_package_id: Package B (Customer) ID
            delta_changes: List of DeltaChange entities from delta comparison

        Returns:
            Dict mapping object_id to CustomerModification

        Example:
            >>> service = CustomerComparisonService()
            >>> customer_mods = service.compare(
            ...     base_package_id=1,
            ...     customer_package_id=2,
            ...     delta_changes=delta_changes
            ... )
            >>> for obj_id, mod in customer_mods.items():
            ...     if mod.customer_modified:
            ...         print(f"Object {obj_id} was modified by customer")
        """
        self.logger.info(
            f"Starting customer comparison: "
            f"Package A (id={base_package_id}) vs "
            f"Package B (id={customer_package_id}) "
            f"for {len(delta_changes)} delta objects"
        )

        # Get objects in customer package
        customer_objects = (
            self.package_object_mapping_repo.get_objects_in_package(
                customer_package_id
            )
        )

        # Create lookup map by object_id for efficient comparison
        customer_map = {obj.id: obj for obj in customer_objects}

        self.logger.info(
            f"Package B has {len(customer_objects)} objects"
        )

        # Compare each delta object against customer package
        customer_modifications = {}

        for delta_change in delta_changes:
            object_id = delta_change.object_id

            # Check if object exists in customer package
            exists_in_customer = object_id in customer_map

            if not exists_in_customer:
                # Object doesn't exist in customer package
                customer_modifications[object_id] = CustomerModification(
                    object_id=object_id,
                    exists_in_customer=False,
                    customer_modified=False,
                    version_changed=False,
                    content_changed=False
                )
            else:
                # Object exists, check if customer modified it
                obj_lookup = customer_map[object_id]
                version_changed, content_changed = self._compare_versions(
                    obj_lookup,
                    base_package_id,
                    customer_package_id
                )

                customer_modified = version_changed or content_changed

                customer_modifications[object_id] = CustomerModification(
                    object_id=object_id,
                    exists_in_customer=True,
                    customer_modified=customer_modified,
                    version_changed=version_changed,
                    content_changed=content_changed
                )

        exists_count = sum(
            1 for m in customer_modifications.values()
            if m.exists_in_customer
        )
        modified_count = sum(
            1 for m in customer_modifications.values()
            if m.customer_modified
        )

        self.logger.info(
            f"Customer comparison complete: "
            f"{exists_count} exist in customer, "
            f"{modified_count} modified by customer"
        )

        return customer_modifications

    def _compare_versions(
        self,
        obj_lookup: ObjectLookup,
        base_package_id: int,
        customer_package_id: int
    ) -> Tuple[bool, bool]:
        """
        Compare versions of an object between base and customer packages.

        This method:
        1. Fetches object_versions for both packages
        2. Compares version UUIDs using version comparison strategy
        3. If versions are same, compares content using content strategy

        Args:
            obj_lookup: ObjectLookup entity
            base_package_id: Package A (Base) ID
            customer_package_id: Package B (Customer) ID

        Returns:
            Tuple of (version_changed, content_changed)

        Example:
            >>> version_changed, content_changed = (
            ...     service._compare_versions(
            ...         obj_lookup=obj,
            ...         base_package_id=1,
            ...         customer_package_id=2
            ...     )
            ... )
            >>> if version_changed:
            ...     print("Customer changed version UUID")
            >>> elif content_changed:
            ...     print("Customer changed content but not version")
        """
        # Fetch object versions for both packages
        base_version = self._get_object_version(
            obj_lookup.id,
            base_package_id
        )
        customer_version = self._get_object_version(
            obj_lookup.id,
            customer_package_id
        )

        # If either version is missing, treat as no change
        # (This shouldn't happen in normal operation)
        if not base_version or not customer_version:
            self.logger.warning(
                f"Missing version data for object {obj_lookup.uuid} "
                f"(base: {base_version is not None}, "
                f"customer: {customer_version is not None})"
            )
            return False, False

        # Compare version UUIDs
        version_changed = self.version_strategy.compare(
            base_version.version_uuid,
            customer_version.version_uuid
        )

        if version_changed:
            # Version changed, no need to check content
            return True, False

        # Version is same, compare content
        base_content = self._extract_content(base_version)
        customer_content = self._extract_content(customer_version)

        content_changed = self.content_strategy.compare(
            base_content,
            customer_content
        )

        return False, content_changed

    def _get_object_version(
        self,
        object_id: int,
        package_id: int
    ) -> Optional[ObjectVersion]:
        """
        Get object version for a specific package.

        Args:
            object_id: Object ID from object_lookup
            package_id: Package ID

        Returns:
            ObjectVersion if found, None otherwise
        """
        return db.session.query(ObjectVersion).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()

    def _extract_content(self, version: ObjectVersion) -> Dict[str, Any]:
        """
        Extract content from ObjectVersion for comparison.

        Args:
            version: ObjectVersion entity

        Returns:
            Dict with content fields (sail_code, fields, properties)
        """
        import json

        content = {}

        # Add SAIL code if present
        if version.sail_code:
            content['sail_code'] = version.sail_code

        # Add fields if present (parse JSON)
        if version.fields:
            try:
                content['fields'] = json.loads(version.fields)
            except json.JSONDecodeError:
                content['fields'] = version.fields

        # Add properties if present (parse JSON)
        if version.properties:
            try:
                content['properties'] = json.loads(version.properties)
            except json.JSONDecodeError:
                content['properties'] = version.properties

        return content

    def get_customer_statistics(
        self,
        customer_modifications: Dict[int, CustomerModification]
    ) -> Dict[str, Any]:
        """
        Get statistics for customer modifications.

        Args:
            customer_modifications: Dict of CustomerModification entities

        Returns:
            Dict with statistics:
                - total: Total objects analyzed
                - exists_in_customer: Count existing in customer package
                - customer_modified: Count modified by customer
                - version_changes: Count with version changes
                - content_changes: Count with content changes

        Example:
            >>> stats = service.get_customer_statistics(customer_mods)
            >>> print(f"Total: {stats['total']}")
            >>> print(f"Modified: {stats['customer_modified']}")
        """
        total = len(customer_modifications)
        exists_in_customer = sum(
            1 for m in customer_modifications.values()
            if m.exists_in_customer
        )
        customer_modified = sum(
            1 for m in customer_modifications.values()
            if m.customer_modified
        )
        version_changes = sum(
            1 for m in customer_modifications.values()
            if m.version_changed
        )
        content_changes = sum(
            1 for m in customer_modifications.values()
            if m.content_changed
        )

        return {
            'total': total,
            'exists_in_customer': exists_in_customer,
            'customer_modified': customer_modified,
            'version_changes': version_changes,
            'content_changes': content_changes
        }
