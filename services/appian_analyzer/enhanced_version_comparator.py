"""
Enhanced version comparator with dual-layer comparison logic
Implements Appian-grade comparison: version history + content diff hash
"""
from typing import Optional, Dict, Any, List
from .models import (
    AppianObject,
    ComparisonResult,
    ImportChangeStatus
)
from .diff_hash_generator import DiffHashGenerator
from .version_history_extractor import VersionHistoryExtractor
from .logger import get_logger


class EnhancedVersionComparator:
    """
    Dual-layer version comparison system

    Layer 1: Version History Comparison (Primary)
    Layer 2: Content Diff Hash Comparison (Secondary)
    """

    def __init__(self):
        """Initialize the enhanced version comparator"""
        self.diff_hash_generator = DiffHashGenerator()
        self.version_history_extractor = VersionHistoryExtractor()
        self.logger = get_logger()

    def compare_objects(
        self,
        obj1: Optional[AppianObject],
        obj2: Optional[AppianObject]
    ) -> ComparisonResult:
        """
        Compare two objects using dual-layer approach

        Args:
            obj1: Object from old version (can be None)
            obj2: Object from new version (can be None)

        Returns:
            ComparisonResult with status and details
        """
        # Handle NEW and REMOVED cases
        if obj1 is None and obj2 is not None:
            return ComparisonResult(
                status=ImportChangeStatus.NEW,
                obj=obj2,
                old_obj=None,
                diagnostics=["Object added in new version"]
            )

        if obj1 is not None and obj2 is None:
            return ComparisonResult(
                status=ImportChangeStatus.REMOVED,
                obj=obj1,
                old_obj=obj1,  # For removed objects, old_obj is the same
                diagnostics=["Object removed in new version"]
            )

        if obj1 is None and obj2 is None:
            raise ValueError("Both objects cannot be None")

        # Layer 1: Version History Comparison
        status = self._compare_version_history(obj1, obj2)
        diagnostics = []
        version_info = self._extract_version_details(obj1, obj2)

        # Layer 2: Diff Hash Comparison (if versions differ)
        if status in [
            ImportChangeStatus.CHANGED,
            ImportChangeStatus.CONFLICT_DETECTED
        ]:
            refined_status, hash_diagnostics = self._refine_with_diff_hash(
                obj1,
                obj2,
                status
            )
            if refined_status != status:
                diagnostics.append(
                    f"Status refined from {status.value} to "
                    f"{refined_status.value} using diff hash"
                )
            status = refined_status
            diagnostics.extend(hash_diagnostics)

        # Generate content diff if changed
        content_diff = None
        if status not in [
            ImportChangeStatus.NOT_CHANGED,
            ImportChangeStatus.NOT_CHANGED_NEW_VUUID
        ]:
            content_diff = self._generate_content_diff(obj1, obj2)

        return ComparisonResult(
            status=status,
            obj=obj2,
            old_obj=obj1,  # Store old object for SAIL code comparison
            version_info=version_info,
            content_diff=content_diff,
            diagnostics=diagnostics
        )

    def _compare_version_history(
        self,
        obj1: AppianObject,
        obj2: AppianObject
    ) -> ImportChangeStatus:
        """
        Layer 1: Compare using version history

        Args:
            obj1: Object from old version
            obj2: Object from new version

        Returns:
            ImportChangeStatus based on version history
        """
        v1_uuid = obj1.version_uuid if hasattr(
            obj1,
            'version_uuid'
        ) else None
        v2_uuid = obj2.version_uuid if hasattr(
            obj2,
            'version_uuid'
        ) else None
        v2_history = obj2.version_history if hasattr(
            obj2,
            'version_history'
        ) else []

        # Missing version info
        if not v1_uuid or not v2_uuid:
            return ImportChangeStatus.UNKNOWN

        # Identical versions
        if v1_uuid == v2_uuid:
            return ImportChangeStatus.NOT_CHANGED

        # Check if v1 is in v2's history
        if self.version_history_extractor.find_version_in_history(
            v1_uuid,
            v2_history
        ):
            return ImportChangeStatus.CHANGED

        # Version conflict - v1 not in v2's history
        return ImportChangeStatus.CONFLICT_DETECTED

    def _refine_with_diff_hash(
        self,
        obj1: AppianObject,
        obj2: AppianObject,
        current_status: ImportChangeStatus
    ) -> tuple:
        """
        Layer 2: Refine status using content diff hash

        Args:
            obj1: Object from old version
            obj2: Object from new version
            current_status: Status from Layer 1

        Returns:
            Tuple of (refined_status, diagnostics)
        """
        diagnostics = []

        raw_xml1 = obj1.raw_xml if hasattr(obj1, 'raw_xml') else None
        raw_xml2 = obj2.raw_xml if hasattr(obj2, 'raw_xml') else None

        if not raw_xml1 or not raw_xml2:
            diagnostics.append(
                "Raw XML not available, cannot compute diff hash"
            )
            return (current_status, diagnostics)

        # Generate diff hashes
        hash1 = self.diff_hash_generator.generate(raw_xml1)
        hash2 = self.diff_hash_generator.generate(raw_xml2)

        if hash1 is None or hash2 is None:
            diagnostics.append(
                "Diff hash generation failed or XML too large, "
                "using version-only comparison"
            )
            return (current_status, diagnostics)

        # Compare hashes
        if hash1 == hash2:
            # Content is identical despite version difference
            diagnostics.append(
                "Content hashes match - version change only"
            )
            return (ImportChangeStatus.NOT_CHANGED_NEW_VUUID, diagnostics)

        diagnostics.append("Content hashes differ - real content change")
        return (current_status, diagnostics)

    def _extract_version_details(
        self,
        obj1: AppianObject,
        obj2: AppianObject
    ) -> Dict[str, Any]:
        """
        Extract version information for comparison result

        Args:
            obj1: Object from old version
            obj2: Object from new version

        Returns:
            Dictionary with version details
        """
        version_info = {
            'old_version_uuid': obj1.version_uuid if hasattr(
                obj1,
                'version_uuid'
            ) else None,
            'new_version_uuid': obj2.version_uuid if hasattr(
                obj2,
                'version_uuid'
            ) else None,
            'old_version_history_count': len(
                obj1.version_history
            ) if hasattr(obj1, 'version_history') else 0,
            'new_version_history_count': len(
                obj2.version_history
            ) if hasattr(obj2, 'version_history') else 0,
            'in_version_history': self._check_in_history(obj1, obj2)
        }
        
        # Add SAIL code for web compatibility
        if hasattr(obj1, 'sail_code'):
            version_info['old_sail_code'] = obj1.sail_code
        if hasattr(obj2, 'sail_code'):
            version_info['new_sail_code'] = obj2.sail_code
        
        return version_info

    def _check_in_history(
        self,
        obj1: AppianObject,
        obj2: AppianObject
    ) -> bool:
        """Check if obj1's version is in obj2's history"""
        v1_uuid = obj1.version_uuid if hasattr(
            obj1,
            'version_uuid'
        ) else None
        v2_history = obj2.version_history if hasattr(
            obj2,
            'version_history'
        ) else []

        if not v1_uuid or not v2_history:
            return False

        return self.version_history_extractor.find_version_in_history(
            v1_uuid,
            v2_history
        )

    def _generate_content_diff(
        self,
        obj1: AppianObject,
        obj2: AppianObject
    ) -> Optional[str]:
        """
        Generate content diff summary

        Args:
            obj1: Object from old version
            obj2: Object from new version

        Returns:
            Content diff summary string
        """
        changes = []

        # Check basic properties
        if obj1.name != obj2.name:
            changes.append(f"Name: '{obj1.name}' → '{obj2.name}'")

        if obj1.description != obj2.description:
            changes.append("Description modified")

        # Check SAIL code if present
        if hasattr(obj1, 'sail_code') and hasattr(obj2, 'sail_code'):
            if obj1.sail_code != obj2.sail_code:
                len_diff = len(obj2.sail_code) - len(obj1.sail_code)
                if len_diff > 0:
                    changes.append(
                        f"SAIL code modified (+{len_diff} characters)"
                    )
                elif len_diff < 0:
                    changes.append(
                        f"SAIL code modified ({len_diff} characters)"
                    )
                else:
                    changes.append("SAIL code modified (content changed)")

        # Check business logic if present
        if hasattr(obj1, 'business_logic') and hasattr(
            obj2,
            'business_logic'
        ):
            if obj1.business_logic != obj2.business_logic:
                changes.append("Business logic modified")

        # Check fields for record types
        if hasattr(obj1, 'fields') and hasattr(obj2, 'fields'):
            if len(obj1.fields) != len(obj2.fields):
                changes.append(
                    f"Field count changed: {len(obj1.fields)} → "
                    f"{len(obj2.fields)}"
                )

        return "; ".join(changes) if changes else None

    def compare_by_uuid(
        self,
        objects1: Dict[str, AppianObject],
        objects2: Dict[str, AppianObject]
    ) -> List[ComparisonResult]:
        """
        Compare two sets of objects by UUID

        Args:
            objects1: Dictionary of UUID -> AppianObject from old version
            objects2: Dictionary of UUID -> AppianObject from new version

        Returns:
            List of ComparisonResult objects
        """
        self.logger.debug(f"Comparing objects: {len(objects1)} vs {len(objects2)}")
        
        results = []

        # Get all UUIDs
        all_uuids = set(objects1.keys()) | set(objects2.keys())
        
        self.logger.debug(f"Total unique UUIDs to compare: {len(all_uuids)}")

        for uuid in all_uuids:
            obj1 = objects1.get(uuid)
            obj2 = objects2.get(uuid)

            result = self.compare_objects(obj1, obj2)
            results.append(result)
        
        # Log summary
        status_counts = {}
        for result in results:
            status = result.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        self.logger.info(f"Comparison complete: {dict(status_counts)}")

        return results
