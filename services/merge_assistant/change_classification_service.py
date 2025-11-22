"""
Change Classification Service

Classifies changes into categories based on conflict analysis:
- NO_CONFLICT: Only vendor changed
- CONFLICT: Both vendor and customer changed
- CUSTOMER_ONLY: Only customer changed
- REMOVED_BUT_CUSTOMIZED: Vendor removed, customer modified
"""
from typing import Dict, Any, List
from enum import Enum


class ChangeClassification(Enum):
    """Change classification types"""
    NO_CONFLICT = "NO_CONFLICT"
    CONFLICT = "CONFLICT"
    CUSTOMER_ONLY = "CUSTOMER_ONLY"
    REMOVED_BUT_CUSTOMIZED = "REMOVED_BUT_CUSTOMIZED"


class ChangeClassificationService:
    """
    Classifies changes based on conflict analysis

    Analyzes vendor changes (A→C) and customer changes (A→B) to determine
    which objects have conflicts and how they should be categorized.
    """

    def classify_changes(
        self,
        vendor_changes: Dict[str, Any],
        customer_changes: Dict[str, Any],
        logger=None
    ) -> Dict[str, List[Dict]]:
        """
        Classify all changes into categories

        Args:
            vendor_changes: Dictionary with 'added', 'modified', 'removed'
                           lists from A→C comparison
            customer_changes: Dictionary with 'added', 'modified', 'removed'
                             lists from A→B comparison
            logger: Optional logger instance

        Returns:
            Dictionary with classification categories:
            {
                'NO_CONFLICT': [...],
                'CONFLICT': [...],
                'CUSTOMER_ONLY': [...],
                'REMOVED_BUT_CUSTOMIZED': [...]
            }
        """
        # Initialize result categories
        results = {
            ChangeClassification.NO_CONFLICT.value: [],
            ChangeClassification.CONFLICT.value: [],
            ChangeClassification.CUSTOMER_ONLY.value: [],
            ChangeClassification.REMOVED_BUT_CUSTOMIZED.value: []
        }

        # Build lookup maps for quick access
        vendor_added_map = {
            obj['uuid']: obj for obj in vendor_changes.get('added', [])
        }
        vendor_modified_map = {
            obj['uuid']: obj for obj in vendor_changes.get('modified', [])
        }
        vendor_removed_map = {
            obj['uuid']: obj for obj in vendor_changes.get('removed', [])
        }

        customer_added_map = {
            obj['uuid']: obj for obj in customer_changes.get('added', [])
        }
        customer_modified_map = {
            obj['uuid']: obj for obj in customer_changes.get('modified', [])
        }
        customer_removed_map = {
            obj['uuid']: obj for obj in customer_changes.get('removed', [])
        }

        # Get all unique object UUIDs from both change sets
        all_uuids = set()
        all_uuids.update(vendor_added_map.keys())
        all_uuids.update(vendor_modified_map.keys())
        all_uuids.update(vendor_removed_map.keys())
        all_uuids.update(customer_added_map.keys())
        all_uuids.update(customer_modified_map.keys())
        all_uuids.update(customer_removed_map.keys())

        # Classify each object
        for uuid in all_uuids:
            classification = self._classify_single_object(
                uuid,
                vendor_added_map,
                vendor_modified_map,
                vendor_removed_map,
                customer_added_map,
                customer_modified_map,
                customer_removed_map
            )

            # Get the change object with most complete information
            change_obj = self._get_change_object(
                uuid,
                classification,
                vendor_added_map,
                vendor_modified_map,
                vendor_removed_map,
                customer_added_map,
                customer_modified_map,
                customer_removed_map
            )

            # Add classification to the object
            change_obj['classification'] = classification

            # Add to appropriate category
            results[classification].append(change_obj)

        return results

    def _classify_single_object(
        self,
        uuid: str,
        vendor_added_map: Dict[str, Any],
        vendor_modified_map: Dict[str, Any],
        vendor_removed_map: Dict[str, Any],
        customer_added_map: Dict[str, Any],
        customer_modified_map: Dict[str, Any],
        customer_removed_map: Dict[str, Any]
    ) -> str:
        """
        Classify a single object based on its presence in change sets

        Classification logic:
        1. REMOVED_BUT_CUSTOMIZED: Vendor removed AND customer modified
        2. CONFLICT: Both vendor and customer modified the same object
        3. CUSTOMER_ONLY: Only customer changed (added/modified/removed)
        4. NO_CONFLICT: Only vendor changed (added/modified/removed)

        Args:
            uuid: Object UUID
            vendor_*_map: Maps of vendor changes
            customer_*_map: Maps of customer changes

        Returns:
            Classification string
        """
        # Check if object is in each change type
        in_vendor_added = uuid in vendor_added_map
        in_vendor_modified = uuid in vendor_modified_map
        in_vendor_removed = uuid in vendor_removed_map
        in_customer_added = uuid in customer_added_map
        in_customer_modified = uuid in customer_modified_map
        in_customer_removed = uuid in customer_removed_map

        # Determine if vendor or customer changed the object
        vendor_changed = (
            in_vendor_added or in_vendor_modified or in_vendor_removed
        )
        customer_changed = (
            in_customer_added or in_customer_modified or in_customer_removed
        )

        # Classification logic based on requirements

        # REMOVED_BUT_CUSTOMIZED: Vendor removed but customer modified
        if in_vendor_removed and in_customer_modified:
            return ChangeClassification.REMOVED_BUT_CUSTOMIZED.value

        # CONFLICT: Both modified the same object
        # This includes cases where both added, both modified, or
        # one added and one modified
        if vendor_changed and customer_changed:
            return ChangeClassification.CONFLICT.value

        # CUSTOMER_ONLY: Only customer changed
        if customer_changed and not vendor_changed:
            return ChangeClassification.CUSTOMER_ONLY.value

        # NO_CONFLICT: Only vendor changed
        if vendor_changed and not customer_changed:
            return ChangeClassification.NO_CONFLICT.value

        # This should never happen if all_uuids is built correctly
        raise ValueError(
            f"Object {uuid} not found in any change set"
        )

    def _get_change_object(
        self,
        uuid: str,
        classification: str,
        vendor_added_map: Dict[str, Any],
        vendor_modified_map: Dict[str, Any],
        vendor_removed_map: Dict[str, Any],
        customer_added_map: Dict[str, Any],
        customer_modified_map: Dict[str, Any],
        customer_removed_map: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get the change object with most complete information

        For conflicts, we want to include information from both
        vendor and customer changes.

        Args:
            uuid: Object UUID
            classification: The classification assigned
            vendor_*_map: Maps of vendor changes
            customer_*_map: Maps of customer changes

        Returns:
            Change object dictionary
        """
        # Start with basic structure
        change_obj = {
            'uuid': uuid,
            'name': 'Unknown',
            'type': 'Unknown'
        }

        # Try to get object from vendor changes first
        vendor_obj = (
            vendor_added_map.get(uuid) or
            vendor_modified_map.get(uuid) or
            vendor_removed_map.get(uuid)
        )

        # Try to get object from customer changes
        customer_obj = (
            customer_added_map.get(uuid) or
            customer_modified_map.get(uuid) or
            customer_removed_map.get(uuid)
        )

        # Use vendor object as base if available
        if vendor_obj:
            change_obj.update(vendor_obj)

        # For conflicts and customer-only, prefer customer object info
        if classification in [
            ChangeClassification.CONFLICT.value,
            ChangeClassification.CUSTOMER_ONLY.value,
            ChangeClassification.REMOVED_BUT_CUSTOMIZED.value
        ]:
            if customer_obj:
                # Update with customer object info
                change_obj['name'] = customer_obj.get(
                    'name', change_obj['name']
                )
                change_obj['type'] = customer_obj.get(
                    'type', change_obj['type']
                )

                # Add customer-specific change details
                if 'sail_code_after' in customer_obj:
                    change_obj['customer_sail_code'] = \
                        customer_obj['sail_code_after']
                if 'fields_after' in customer_obj:
                    change_obj['customer_fields'] = \
                        customer_obj['fields_after']
                if 'properties_after' in customer_obj:
                    change_obj['customer_properties'] = \
                        customer_obj['properties_after']

        # For conflicts, also include vendor change details
        if classification == ChangeClassification.CONFLICT.value:
            if vendor_obj:
                if 'sail_code_after' in vendor_obj:
                    change_obj['vendor_sail_code'] = \
                        vendor_obj['sail_code_after']
                if 'fields_after' in vendor_obj:
                    change_obj['vendor_fields'] = \
                        vendor_obj['fields_after']
                if 'properties_after' in vendor_obj:
                    change_obj['vendor_properties'] = \
                        vendor_obj['properties_after']

        return change_obj

    def _is_conflict(
        self,
        object_uuid: str,
        vendor_changes: Dict[str, Any],
        customer_changes: Dict[str, Any]
    ) -> bool:
        """
        Check if object has conflicting changes

        An object has a conflict if it was modified in both
        vendor changes (A→C) and customer changes (A→B).

        Args:
            object_uuid: UUID of the object to check
            vendor_changes: Vendor changes dictionary
            customer_changes: Customer changes dictionary

        Returns:
            True if object has conflicting changes, False otherwise
        """
        # Build lookup sets for quick checking
        vendor_uuids = set()
        for change_list in vendor_changes.values():
            vendor_uuids.update(obj['uuid'] for obj in change_list)

        customer_uuids = set()
        for change_list in customer_changes.values():
            customer_uuids.update(obj['uuid'] for obj in change_list)

        # Object has conflict if it appears in both change sets
        return object_uuid in vendor_uuids and object_uuid in customer_uuids
