"""
Classification Service

Applies the 7 classification rules to delta objects combined with customer
modification data to generate the working set of changes.
"""

import logging
from typing import List, Dict, Any

from core.base_service import BaseService
from repositories.change_repository import ChangeRepository
from domain.entities import DeltaChange, CustomerModification, ClassifiedChange
from domain.enums import ChangeCategory, Classification, ChangeType


class ClassificationRuleEngine:
    """
    Engine for applying the 7 classification rules.

    Rules:
    - Rule 10a: MODIFIED in delta AND not modified in customer → NO_CONFLICT
    - Rule 10b: MODIFIED in delta AND modified in customer → CONFLICT
    - Rule 10c: MODIFIED in delta AND removed in customer → DELETED
    - Rule 10d: NEW in delta → NEW
    - Rule 10e: DEPRECATED in delta AND not modified in customer → NO_CONFLICT
    - Rule 10f: DEPRECATED in delta AND modified in customer → CONFLICT
    - Rule 10g: DEPRECATED in delta AND removed in customer → NO_CONFLICT
    """

    def __init__(self):
        """Initialize rule engine."""
        self.logger = logging.getLogger(__name__)

    def classify(
        self,
        delta_change: DeltaChange,
        customer_modification: CustomerModification
    ) -> Classification:
        """
        Apply classification rules to determine classification.

        Args:
            delta_change: DeltaChange entity from delta comparison
            customer_modification: CustomerModification entity from customer
                                  comparison

        Returns:
            Classification enum value

        Raises:
            ValueError: If delta_category is unknown

        Example:
            >>> engine = ClassificationRuleEngine()
            >>> classification = engine.classify(
            ...     delta_change=DeltaChange(
            ...         object_id=1,
            ...         change_category=ChangeCategory.MODIFIED,
            ...         version_changed=True,
            ...         content_changed=False
            ...     ),
            ...     customer_modification=CustomerModification(
            ...         object_id=1,
            ...         exists_in_customer=True,
            ...         customer_modified=True,
            ...         version_changed=True,
            ...         content_changed=False
            ...     )
            ... )
            >>> print(classification)  # Classification.CONFLICT
        """
        delta_category = delta_change.change_category
        exists_in_customer = customer_modification.exists_in_customer
        customer_modified = customer_modification.customer_modified

        # Rule 10d: NEW in delta → NEW
        if delta_category == ChangeCategory.NEW:
            self.logger.debug(
                f"Object {delta_change.object_id}: Rule 10d - NEW"
            )
            return Classification.NEW

        # Rules for MODIFIED in delta
        elif delta_category == ChangeCategory.MODIFIED:
            # Rule 10c: MODIFIED in delta AND removed in customer
            # → DELETED
            if not exists_in_customer:
                self.logger.debug(
                    f"Object {delta_change.object_id}: "
                    f"Rule 10c - DELETED "
                    f"(vendor modified, customer removed)"
                )
                return Classification.DELETED

            # Rule 10b: MODIFIED in delta AND modified in customer
            # → CONFLICT
            elif customer_modified:
                self.logger.debug(
                    f"Object {delta_change.object_id}: "
                    f"Rule 10b - CONFLICT (both modified)"
                )
                return Classification.CONFLICT

            # Rule 10a: MODIFIED in delta AND not modified in customer
            # → NO_CONFLICT
            else:
                self.logger.debug(
                    f"Object {delta_change.object_id}: "
                    f"Rule 10a - NO_CONFLICT (vendor modified only)"
                )
                return Classification.NO_CONFLICT

        # Rules for DEPRECATED in delta
        elif delta_category == ChangeCategory.DEPRECATED:
            # Rule 10g: DEPRECATED in delta AND removed in customer
            # → NO_CONFLICT
            if not exists_in_customer:
                self.logger.debug(
                    f"Object {delta_change.object_id}: "
                    f"Rule 10g - NO_CONFLICT (both removed)"
                )
                return Classification.NO_CONFLICT

            # Rule 10f: DEPRECATED in delta AND modified in customer
            # → CONFLICT
            elif customer_modified:
                self.logger.debug(
                    f"Object {delta_change.object_id}: "
                    f"Rule 10f - CONFLICT "
                    f"(vendor deprecated, customer modified)"
                )
                return Classification.CONFLICT

            # Rule 10e: DEPRECATED in delta AND not modified in customer
            # → NO_CONFLICT
            else:
                self.logger.debug(
                    f"Object {delta_change.object_id}: "
                    f"Rule 10e - NO_CONFLICT (vendor deprecated, "
                    f"customer unchanged)"
                )
                return Classification.NO_CONFLICT

        else:
            raise ValueError(
                f"Unknown delta category: {delta_category}"
            )

    def determine_vendor_change_type(
        self,
        delta_change: DeltaChange
    ) -> ChangeType:
        """
        Determine vendor change type from delta change.

        Args:
            delta_change: DeltaChange entity

        Returns:
            ChangeType enum value

        Example:
            >>> change_type = engine.determine_vendor_change_type(
            ...     delta_change
            ... )
        """
        if delta_change.change_category == ChangeCategory.NEW:
            return ChangeType.ADDED
        elif delta_change.change_category == ChangeCategory.DEPRECATED:
            return ChangeType.REMOVED
        else:  # MODIFIED
            return ChangeType.MODIFIED

    def determine_customer_change_type(
        self,
        customer_modification: CustomerModification
    ) -> ChangeType:
        """
        Determine customer change type from customer modification.

        Args:
            customer_modification: CustomerModification entity

        Returns:
            ChangeType enum value or None if no change

        Example:
            >>> change_type = engine.determine_customer_change_type(
            ...     customer_modification
            ... )
        """
        if not customer_modification.exists_in_customer:
            return ChangeType.REMOVED
        elif customer_modification.customer_modified:
            return ChangeType.MODIFIED
        else:
            return None  # No customer change


class ClassificationService(BaseService):
    """
    Service for classifying changes using the 7 classification rules.

    This service:
    1. Takes delta comparison results and customer comparison data
    2. Applies classification rules to each delta object
    3. Creates Change records in the working set
    4. Sets display_order for consistent presentation

    Key Design Principles:
    - Working set contains ONLY delta objects (delta-driven)
    - Each delta object gets exactly one Change record
    - Classification is deterministic based on rules
    - Display order ensures consistent presentation
    """

    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)

    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.change_repo = self._get_repository(ChangeRepository)
        self.rule_engine = ClassificationRuleEngine()

    def classify(
        self,
        session_id: int,
        delta_changes: List[DeltaChange],
        customer_modifications: Dict[int, CustomerModification]
    ) -> List[ClassifiedChange]:
        """
        Classify changes using the 7 classification rules.

        This is the main entry point for classification. It follows:
        1. For each delta object:
           a. Get delta change category (NEW, MODIFIED, DEPRECATED)
           b. Get customer comparison data
           c. Apply classification rule
           d. Determine vendor and customer change types
           e. Create ClassifiedChange entity
        2. Sort by classification priority for display order
        3. Create Change records in database
        4. Return list of ClassifiedChange entities

        Args:
            session_id: Merge session ID
            delta_changes: List of DeltaChange entities from delta comparison
            customer_modifications: Dict mapping object_id to
                                   CustomerModification

        Returns:
            List of ClassifiedChange entities

        Example:
            >>> service = ClassificationService()
            >>> classified = service.classify(
            ...     session_id=1,
            ...     delta_changes=delta_changes,
            ...     customer_modifications=customer_mods
            ... )
            >>> print(f"Created {len(classified)} changes")
        """
        self.logger.info(
            f"Starting classification for session {session_id}: "
            f"{len(delta_changes)} delta objects"
        )

        # Classify each delta object
        classified_changes = []

        for delta_change in delta_changes:
            object_id = delta_change.object_id

            # Get customer modification data
            customer_mod = customer_modifications.get(object_id)

            if not customer_mod:
                # This shouldn't happen - every delta object should have
                # customer comparison data
                self.logger.warning(
                    f"No customer modification data for object {object_id}, "
                    f"treating as not in customer package"
                )
                customer_mod = CustomerModification(
                    object_id=object_id,
                    exists_in_customer=False,
                    customer_modified=False,
                    version_changed=False,
                    content_changed=False
                )

            # Apply classification rule
            classification = self.rule_engine.classify(
                delta_change,
                customer_mod
            )

            # Determine change types
            vendor_change_type = (
                self.rule_engine.determine_vendor_change_type(delta_change)
            )
            customer_change_type = (
                self.rule_engine.determine_customer_change_type(customer_mod)
            )

            # Create ClassifiedChange entity
            classified_change = ClassifiedChange(
                object_id=object_id,
                classification=classification,
                vendor_change_type=vendor_change_type,
                customer_change_type=customer_change_type,
                display_order=0  # Will be set later
            )

            classified_changes.append(classified_change)

        # Sort by classification priority for display order
        # Priority: CONFLICT > NEW > DELETED > NO_CONFLICT
        classified_changes = self._sort_by_priority(classified_changes)

        # Assign display order
        for i, change in enumerate(classified_changes, start=1):
            change.display_order = i

        # Create Change records in database
        self._create_change_records(session_id, classified_changes)

        # Log statistics
        stats = self._get_classification_stats(classified_changes)
        self.logger.info(
            f"Classification complete for session {session_id}: "
            f"NO_CONFLICT={stats['NO_CONFLICT']}, "
            f"CONFLICT={stats['CONFLICT']}, "
            f"NEW={stats['NEW']}, "
            f"DELETED={stats['DELETED']}"
        )

        return classified_changes

    def _sort_by_priority(
        self,
        classified_changes: List[ClassifiedChange]
    ) -> List[ClassifiedChange]:
        """
        Sort classified changes by priority.

        Priority order:
        1. CONFLICT (highest priority - requires manual review)
        2. NEW (new objects from vendor)
        3. DELETED (objects removed by customer but modified by vendor)
        4. NO_CONFLICT (lowest priority - can be auto-merged)

        Args:
            classified_changes: List of ClassifiedChange entities

        Returns:
            Sorted list of ClassifiedChange entities
        """
        priority_map = {
            Classification.CONFLICT: 1,
            Classification.NEW: 2,
            Classification.DELETED: 3,
            Classification.NO_CONFLICT: 4
        }

        return sorted(
            classified_changes,
            key=lambda c: priority_map[c.classification]
        )

    def _create_change_records(
        self,
        session_id: int,
        classified_changes: List[ClassifiedChange]
    ) -> None:
        """
        Create Change records in database.

        Uses bulk_create_changes for performance.

        Args:
            session_id: Merge session ID
            classified_changes: List of ClassifiedChange entities
        """
        # Convert to dict format for bulk creation
        changes_data = []

        for classified_change in classified_changes:
            change_data = {
                'session_id': session_id,
                'object_id': classified_change.object_id,
                'vendor_object_id': classified_change.object_id,  # Vendor changed this object
                'customer_object_id': classified_change.object_id,  # Customer may have changed same object
                'classification': classified_change.classification.value,
                'display_order': classified_change.display_order,
                'vendor_change_type': (
                    classified_change.vendor_change_type.value
                    if classified_change.vendor_change_type
                    else None
                ),
                'customer_change_type': (
                    classified_change.customer_change_type.value
                    if classified_change.customer_change_type
                    else None
                )
            }
            changes_data.append(change_data)

        # Bulk create
        self.change_repo.bulk_create_changes(changes_data)

        self.logger.info(
            f"Created {len(changes_data)} change records for "
            f"session {session_id}"
        )

    def _get_classification_stats(
        self,
        classified_changes: List[ClassifiedChange]
    ) -> Dict[str, int]:
        """
        Get statistics for classified changes.

        Args:
            classified_changes: List of ClassifiedChange entities

        Returns:
            Dict mapping classification to count
        """
        stats = {
            'NO_CONFLICT': 0,
            'CONFLICT': 0,
            'NEW': 0,
            'DELETED': 0
        }

        for change in classified_changes:
            classification_str = change.classification.value
            stats[classification_str] = stats.get(classification_str, 0) + 1

        return stats

    def get_working_set_statistics(
        self,
        session_id: int
    ) -> Dict[str, Any]:
        """
        Get comprehensive statistics for the working set.

        Args:
            session_id: Merge session ID

        Returns:
            Dict with statistics:
                - total: Total changes
                - by_classification: Count by classification
                - conflicts: Count of conflicts
                - no_conflicts: Count of no conflicts
                - new: Count of new objects
                - deleted: Count of deleted objects

        Example:
            >>> stats = service.get_working_set_statistics(session_id=1)
            >>> print(f"Total: {stats['total']}")
            >>> print(f"Conflicts: {stats['conflicts']}")
        """
        return self.change_repo.get_statistics(session_id)

    def reclassify(
        self,
        session_id: int,
        delta_changes: List[DeltaChange],
        customer_modifications: Dict[int, CustomerModification]
    ) -> List[ClassifiedChange]:
        """
        Reclassify changes for a session.

        This deletes existing changes and creates new ones.
        Useful for reprocessing after changes to classification rules.

        Args:
            session_id: Merge session ID
            delta_changes: List of DeltaChange entities
            customer_modifications: Dict of CustomerModification entities

        Returns:
            List of ClassifiedChange entities

        Example:
            >>> classified = service.reclassify(
            ...     session_id=1,
            ...     delta_changes=delta_changes,
            ...     customer_modifications=customer_mods
            ... )
        """
        self.logger.info(
            f"Reclassifying changes for session {session_id}"
        )

        # Delete existing changes
        deleted_count = self.change_repo.delete_by_session(session_id)
        self.logger.info(
            f"Deleted {deleted_count} existing changes"
        )

        # Classify and create new changes
        return self.classify(
            session_id,
            delta_changes,
            customer_modifications
        )
