"""
Delta Comparison Service

Handles comparison between Package A (Base) and Package C (New Vendor)
to identify the vendor delta (NEW, MODIFIED, DEPRECATED objects).
"""

import logging
from typing import List, Dict, Any, Tuple, Optional

from core.base_service import BaseService
from models import db, ObjectLookup, ObjectVersion
from repositories.object_lookup_repository import ObjectLookupRepository
from repositories.package_object_mapping_repository import PackageObjectMappingRepository
from repositories.delta_comparison_repository import DeltaComparisonRepository
from domain.entities import DeltaChange
from domain.enums import ChangeCategory, ChangeType
from domain.comparison_strategies import (
    SimpleVersionComparisonStrategy,
    SAILCodeComparisonStrategy
)


class DeltaComparisonService(BaseService):
    """
    Service for comparing Package A (Base) to Package C (New Vendor).
    
    This service identifies the vendor delta by comparing two packages:
    - NEW objects: In C but not in A
    - DEPRECATED objects: In A but not in C
    - MODIFIED objects: In both A and C with differences
    
    For MODIFIED objects, it determines:
    - version_changed: Whether version UUID changed
    - content_changed: Whether content changed (when version is same)
    
    Results are stored in delta_comparison_results table.
    
    Key Design Principles:
    - Uses package_object_mappings to find objects in each package
    - Compares version UUIDs first (fast)
    - Falls back to content comparison if versions are same
    - Stores all results for later classification
    """
    
    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.object_lookup_repo = self._get_repository(ObjectLookupRepository)
        self.package_object_mapping_repo = self._get_repository(PackageObjectMappingRepository)
        self.delta_comparison_repo = self._get_repository(DeltaComparisonRepository)
        
        # Initialize comparison strategies
        self.version_strategy = SimpleVersionComparisonStrategy()
        self.content_strategy = SAILCodeComparisonStrategy(
            critical_fields=['sail_code', 'fields', 'properties']
        )
    
    def compare(
        self,
        session_id: int,
        base_package_id: int,
        new_vendor_package_id: int
    ) -> List[DeltaChange]:
        """
        Compare Package A (Base) to Package C (New Vendor) to identify vendor delta.
        
        This is the main entry point for delta comparison. It follows these steps:
        1. Get objects in package A (via package_object_mappings)
        2. Get objects in package C (via package_object_mappings)
        3. Identify NEW objects (in C, not in A) → change_category='NEW'
        4. Identify DEPRECATED objects (in A, not in C) → change_category='DEPRECATED'
        5. Identify MODIFIED objects (in both A and C):
           a. Compare version UUIDs
           b. If version changed, mark version_changed=True
           c. If version same, compare content
           d. If content changed, mark content_changed=True
        6. Store results in delta_comparison_results
        
        Args:
            session_id: Merge session ID
            base_package_id: Package A (Base) ID
            new_vendor_package_id: Package C (New Vendor) ID
            
        Returns:
            List of DeltaChange domain entities
            
        Example:
            >>> service = DeltaComparisonService()
            >>> delta_changes = service.compare(
            ...     session_id=1,
            ...     base_package_id=1,
            ...     new_vendor_package_id=3
            ... )
            >>> print(f"Found {len(delta_changes)} vendor changes")
        """
        self.logger.info(
            f"Starting delta comparison for session {session_id}: "
            f"Package A (id={base_package_id}) → Package C (id={new_vendor_package_id})"
        )
        
        # Step 1 & 2: Get objects in both packages
        base_objects = self.package_object_mapping_repo.get_objects_in_package(base_package_id)
        new_vendor_objects = self.package_object_mapping_repo.get_objects_in_package(new_vendor_package_id)
        
        self.logger.info(
            f"Package A has {len(base_objects)} objects, "
            f"Package C has {len(new_vendor_objects)} objects"
        )
        
        # Create lookup maps by UUID for efficient comparison
        base_map = {obj.uuid: obj for obj in base_objects}
        new_vendor_map = {obj.uuid: obj for obj in new_vendor_objects}
        
        delta_results = []
        
        # Step 3: Identify NEW objects (in C, not in A)
        new_objects = [
            obj for uuid, obj in new_vendor_map.items()
            if uuid not in base_map
        ]
        
        for obj in new_objects:
            delta_results.append({
                'session_id': session_id,
                'object_id': obj.id,
                'change_category': ChangeCategory.NEW.value,
                'change_type': ChangeType.ADDED.value,
                'version_changed': False,
                'content_changed': False
            })
        
        self.logger.info(f"Found {len(new_objects)} NEW objects")
        
        # Step 4: Identify DEPRECATED objects (in A, not in C)
        deprecated_objects = [
            obj for uuid, obj in base_map.items()
            if uuid not in new_vendor_map
        ]
        
        for obj in deprecated_objects:
            delta_results.append({
                'session_id': session_id,
                'object_id': obj.id,
                'change_category': ChangeCategory.DEPRECATED.value,
                'change_type': ChangeType.REMOVED.value,
                'version_changed': False,
                'content_changed': False
            })
        
        self.logger.info(f"Found {len(deprecated_objects)} DEPRECATED objects")
        
        # Step 5: Identify MODIFIED objects (in both A and C)
        common_uuids = set(base_map.keys()) & set(new_vendor_map.keys())
        modified_count = 0
        
        for uuid in common_uuids:
            base_obj = base_map[uuid]

            # Compare versions
            version_changed, content_changed = self._compare_versions(
                base_obj,
                base_package_id,
                new_vendor_package_id
            )
            
            # Only store if there's an actual change
            if version_changed or content_changed:
                delta_results.append({
                    'session_id': session_id,
                    'object_id': base_obj.id,
                    'change_category': ChangeCategory.MODIFIED.value,
                    'change_type': ChangeType.MODIFIED.value,
                    'version_changed': version_changed,
                    'content_changed': content_changed
                })
                modified_count += 1
        
        self.logger.info(f"Found {modified_count} MODIFIED objects")
        
        # Step 6: Store results in delta_comparison_results
        if delta_results:
            self.delta_comparison_repo.bulk_create_results(delta_results)
            self.logger.info(f"Stored {len(delta_results)} delta comparison results")
        
        # Convert to domain entities
        domain_entities = [
            DeltaChange(
                object_id=result['object_id'],
                change_category=ChangeCategory(result['change_category']),
                version_changed=result['version_changed'],
                content_changed=result['content_changed']
            )
            for result in delta_results
        ]
        
        self.logger.info(
            f"Delta comparison complete: {len(new_objects)} NEW, "
            f"{modified_count} MODIFIED, {len(deprecated_objects)} DEPRECATED"
        )
        
        return domain_entities
    
    def _compare_versions(
        self,
        obj_lookup: ObjectLookup,
        base_package_id: int,
        new_package_id: int
    ) -> Tuple[bool, bool]:
        """
        Compare versions of an object between two packages.
        
        This method:
        1. Fetches object_versions for both packages
        2. Compares version UUIDs using version comparison strategy
        3. If versions are same, compares content using content comparison strategy
        
        Args:
            obj_lookup: ObjectLookup entity
            base_package_id: Package A (Base) ID
            new_package_id: Package C (New Vendor) ID
            
        Returns:
            Tuple of (version_changed, content_changed)
            
        Example:
            >>> version_changed, content_changed = service._compare_versions(
            ...     obj_lookup=obj,
            ...     base_package_id=1,
            ...     new_package_id=3
            ... )
            >>> if version_changed:
            ...     print("Version UUID changed")
            >>> elif content_changed:
            ...     print("Content changed but version is same")
        """
        # Fetch object versions for both packages
        base_version = self._get_object_version(obj_lookup.id, base_package_id)
        new_version = self._get_object_version(obj_lookup.id, new_package_id)
        
        # If either version is missing, treat as no change
        # (This shouldn't happen in normal operation)
        if not base_version or not new_version:
            self.logger.warning(
                f"Missing version data for object {obj_lookup.uuid} "
                f"(base: {base_version is not None}, new: {new_version is not None})"
            )
            return False, False
        
        # Compare version UUIDs
        version_changed = self.version_strategy.compare(
            base_version.version_uuid,
            new_version.version_uuid
        )
        
        if version_changed:
            # Version changed, no need to check content
            return True, False
        
        # Version is same, compare content
        base_content = self._extract_content(base_version)
        new_content = self._extract_content(new_version)
        
        content_changed = self.content_strategy.compare(
            base_content,
            new_content
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
    
    def get_delta_statistics(
        self,
        session_id: int
    ) -> Dict[str, Any]:
        """
        Get statistics for delta comparison results.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Dict with statistics:
                - total: Total delta results
                - by_category: Count by category (NEW, MODIFIED, DEPRECATED)
                - version_changes: Count with version changes
                - content_changes: Count with content changes
                
        Example:
            >>> stats = service.get_delta_statistics(session_id=1)
            >>> print(f"Total changes: {stats['total']}")
            >>> print(f"NEW: {stats['by_category']['NEW']}")
        """
        return self.delta_comparison_repo.get_statistics(session_id)
