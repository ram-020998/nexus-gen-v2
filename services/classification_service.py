"""
Classification Service

Applies set-based classification logic to determine merge conflicts.

Key Concept:
- Set D: Vendor changes (Base → New Vendor, A→C)
- Set E: Customer changes (Base → Customer, A→B)
- Conflict: Object in D ∩ E with B != C (both parties modified differently)
- No Conflict: Object in D \ E (vendor only) or E \ D (customer only) or B == C (same changes)
"""

import logging
from typing import List, Dict, Optional

from core.base_service import BaseService
from repositories.change_repository import ChangeRepository
from models import db, ObjectVersion
from domain.entities import VendorChange, CustomerChange, MergeAnalysis, ClassifiedChange
from domain.enums import Classification, ChangeCategory
from domain.comparison_strategies import SAILCodeComparisonStrategy


class ContentComparator:
    """
    Compares content between customer version (B) and new vendor version (C).
    
    This is used to determine if objects in D ∩ E are truly conflicting
    or if both parties made the same changes.
    """
    
    def __init__(self, customer_package_id: int, new_vendor_package_id: int):
        """
        Initialize comparator.
        
        Args:
            customer_package_id: Package B (Customer) ID
            new_vendor_package_id: Package C (New Vendor) ID
        """
        self.customer_package_id = customer_package_id
        self.new_vendor_package_id = new_vendor_package_id
        self.logger = logging.getLogger(__name__)
        
        # Use same comparison strategy as other services
        self.content_strategy = SAILCodeComparisonStrategy(
            critical_fields=['sail_code', 'fields', 'properties']
        )
    
    def compare_customer_vs_new_vendor(self, object_id: int) -> bool:
        """
        Compare customer version (B) vs new vendor version (C).
        
        Args:
            object_id: Object ID to compare
            
        Returns:
            True if versions are different, False if they're the same
        """
        # Get versions from both packages
        customer_version = self._get_object_version(
            object_id,
            self.customer_package_id
        )
        new_vendor_version = self._get_object_version(
            object_id,
            self.new_vendor_package_id
        )
        
        if not customer_version or not new_vendor_version:
            # If we can't get versions, assume they're different (conservative)
            self.logger.warning(
                f"Could not get versions for object {object_id} "
                f"(customer={customer_version is not None}, "
                f"new_vendor={new_vendor_version is not None})"
            )
            return True
        
        # First check: version UUIDs
        if customer_version.version_uuid != new_vendor_version.version_uuid:
            # Different version UUIDs - need to check content
            customer_content = self._extract_content(customer_version)
            new_vendor_content = self._extract_content(new_vendor_version)
            
            content_changed = self.content_strategy.compare(
                customer_content,
                new_vendor_content
            )
            
            # CRITICAL FIX: Also check object-specific tables
            # Get object_lookup to determine object type
            from models import ObjectLookup
            obj_lookup = db.session.query(ObjectLookup).filter_by(id=object_id).first()
            if obj_lookup:
                object_specific_changed = self._compare_object_specific_content(
                    obj_lookup,
                    self.customer_package_id,
                    self.new_vendor_package_id
                )
                content_changed = content_changed or object_specific_changed
            
            if content_changed:
                self.logger.debug(
                    f"Object {object_id}: B != C (different content)"
                )
                return True
            else:
                self.logger.debug(
                    f"Object {object_id}: B == C (same content despite different version UUIDs)"
                )
                return False
        else:
            # Same version UUIDs - they're identical
            self.logger.debug(
                f"Object {object_id}: B == C (same version UUID)"
            )
            return False
    
    def _get_object_version(
        self,
        object_id: int,
        package_id: int
    ) -> Optional[ObjectVersion]:
        """Get object version for a specific package."""
        return db.session.query(ObjectVersion).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _extract_content(self, version: ObjectVersion) -> Dict:
        """Extract content from ObjectVersion for comparison."""
        import json
        
        content = {}
        
        if version.sail_code:
            content['sail_code'] = version.sail_code
        
        if version.fields:
            try:
                content['fields'] = json.loads(version.fields)
            except json.JSONDecodeError:
                content['fields'] = version.fields
        
        if version.properties:
            try:
                content['properties'] = json.loads(version.properties)
            except json.JSONDecodeError:
                content['properties'] = version.properties
        
        return content
    
    def _compare_object_specific_content(self, obj_lookup, customer_package_id: int, new_vendor_package_id: int) -> bool:
        """Compare object-specific table content between customer and new vendor packages."""
        object_type = obj_lookup.object_type
        
        if object_type == "Process Model":
            return self._compare_process_model_content(obj_lookup.id, customer_package_id, new_vendor_package_id)
        elif object_type == "Constant":
            return self._compare_constant_content(obj_lookup.id, customer_package_id, new_vendor_package_id)
        elif object_type == "Record Type":
            return self._compare_record_type_content(obj_lookup.id, customer_package_id, new_vendor_package_id)
        elif object_type == "Interface":
            return self._compare_interface_content(obj_lookup.id, customer_package_id, new_vendor_package_id)
        elif object_type == "Expression Rule":
            return self._compare_expression_rule_content(obj_lookup.id, customer_package_id, new_vendor_package_id)
        elif object_type == "Data Type":
            return self._compare_cdt_content(obj_lookup.id, customer_package_id, new_vendor_package_id)
        
        return False
    
    def _compare_process_model_content(self, object_id: int, customer_package_id: int, new_vendor_package_id: int) -> bool:
        from models import ProcessModel
        customer_pm = db.session.query(ProcessModel).filter_by(object_id=object_id, package_id=customer_package_id).first()
        new_vendor_pm = db.session.query(ProcessModel).filter_by(object_id=object_id, package_id=new_vendor_package_id).first()
        if not customer_pm or not new_vendor_pm:
            return False
        if customer_pm.nodes.count() != new_vendor_pm.nodes.count():
            return True
        if customer_pm.flows.count() != new_vendor_pm.flows.count():
            return True
        if customer_pm.variables.count() != new_vendor_pm.variables.count():
            return True
        customer_vars = {(v.variable_name, v.variable_type) for v in customer_pm.variables}
        new_vendor_vars = {(v.variable_name, v.variable_type) for v in new_vendor_pm.variables}
        return customer_vars != new_vendor_vars
    
    def _compare_constant_content(self, object_id: int, customer_package_id: int, new_vendor_package_id: int) -> bool:
        from models import Constant
        customer_const = db.session.query(Constant).filter_by(object_id=object_id, package_id=customer_package_id).first()
        new_vendor_const = db.session.query(Constant).filter_by(object_id=object_id, package_id=new_vendor_package_id).first()
        if not customer_const or not new_vendor_const:
            return False
        return customer_const.constant_value != new_vendor_const.constant_value or customer_const.constant_type != new_vendor_const.constant_type
    
    def _compare_record_type_content(self, object_id: int, customer_package_id: int, new_vendor_package_id: int) -> bool:
        from models import RecordType
        customer_rt = db.session.query(RecordType).filter_by(object_id=object_id, package_id=customer_package_id).first()
        new_vendor_rt = db.session.query(RecordType).filter_by(object_id=object_id, package_id=new_vendor_package_id).first()
        if not customer_rt or not new_vendor_rt:
            return False
        return (customer_rt.fields.count() != new_vendor_rt.fields.count() or
                customer_rt.relationships.count() != new_vendor_rt.relationships.count() or
                customer_rt.views.count() != new_vendor_rt.views.count() or
                customer_rt.actions.count() != new_vendor_rt.actions.count())
    
    def _compare_interface_content(self, object_id: int, customer_package_id: int, new_vendor_package_id: int) -> bool:
        from models import Interface
        customer_intf = db.session.query(Interface).filter_by(object_id=object_id, package_id=customer_package_id).first()
        new_vendor_intf = db.session.query(Interface).filter_by(object_id=object_id, package_id=new_vendor_package_id).first()
        if not customer_intf or not new_vendor_intf:
            return False
        return (customer_intf.parameters.count() != new_vendor_intf.parameters.count() or
                customer_intf.security.count() != new_vendor_intf.security.count())
    
    def _compare_expression_rule_content(self, object_id: int, customer_package_id: int, new_vendor_package_id: int) -> bool:
        from models import ExpressionRule
        customer_er = db.session.query(ExpressionRule).filter_by(object_id=object_id, package_id=customer_package_id).first()
        new_vendor_er = db.session.query(ExpressionRule).filter_by(object_id=object_id, package_id=new_vendor_package_id).first()
        if not customer_er or not new_vendor_er:
            return False
        return customer_er.inputs.count() != new_vendor_er.inputs.count()
    
    def _compare_cdt_content(self, object_id: int, customer_package_id: int, new_vendor_package_id: int) -> bool:
        from models import CDT
        customer_cdt = db.session.query(CDT).filter_by(object_id=object_id, package_id=customer_package_id).first()
        new_vendor_cdt = db.session.query(CDT).filter_by(object_id=object_id, package_id=new_vendor_package_id).first()
        if not customer_cdt or not new_vendor_cdt:
            return False
        return customer_cdt.fields.count() != new_vendor_cdt.fields.count()


class SetBasedClassifier:
    """
    Set-based classifier for three-way merge.
    
    Uses set theory to determine conflicts:
    - D ∩ E → Check if B and C differ:
        - If B == C: NO_CONFLICT (same changes)
        - If B != C: CONFLICT (different changes)
    - D \ E → NO_CONFLICT (vendor only)
    - E \ D → NO_CONFLICT (customer only)
    """
    
    def __init__(self, content_comparator=None):
        """Initialize classifier."""
        self.logger = logging.getLogger(__name__)
        self.content_comparator = content_comparator
    
    def classify(
        self,
        vendor_changes: List[VendorChange],
        customer_changes: List[CustomerChange]
    ) -> List[MergeAnalysis]:
        """
        Classify changes using set-based logic.
        
        Args:
            vendor_changes: List of vendor changes (Set D)
            customer_changes: List of customer changes (Set E)
            
        Returns:
            List of MergeAnalysis entities with classifications
        """
        # Build sets of object IDs
        vendor_set = {change.object_id for change in vendor_changes}
        customer_set = {change.object_id for change in customer_changes}
        
        # Build lookup maps
        vendor_map = {change.object_id: change for change in vendor_changes}
        customer_map = {change.object_id: change for change in customer_changes}
        
        # Get all objects (union of both sets)
        all_objects = vendor_set | customer_set
        
        self.logger.info(
            f"Classifying {len(all_objects)} objects: "
            f"Vendor={len(vendor_set)}, Customer={len(customer_set)}, "
            f"Intersection={len(vendor_set & customer_set)}"
        )
        
        analyses = []
        
        for object_id in all_objects:
            in_vendor = object_id in vendor_set
            in_customer = object_id in customer_set
            
            vendor_change = vendor_map.get(object_id)
            customer_change = customer_map.get(object_id)
            
            # Determine classification
            classification = self._determine_classification(
                in_vendor,
                in_customer,
                vendor_change,
                customer_change
            )
            
            analysis = MergeAnalysis(
                object_id=object_id,
                in_vendor_changes=in_vendor,
                in_customer_changes=in_customer,
                vendor_change=vendor_change,
                customer_change=customer_change,
                classification=classification
            )
            
            analyses.append(analysis)
        
        # Log statistics
        stats = self._get_classification_stats(analyses)
        self.logger.info(
            f"Classification complete: "
            f"CONFLICT={stats['CONFLICT']}, "
            f"NO_CONFLICT={stats['NO_CONFLICT']}, "
            f"DELETED={stats['DELETED']}"
        )
        
        return analyses
    
    def _determine_classification(
        self,
        in_vendor: bool,
        in_customer: bool,
        vendor_change: VendorChange,
        customer_change: CustomerChange
    ) -> Classification:
        """
        Determine classification based on set membership and content comparison.
        
        Logic:
        1. If in both D and E → Check for special cases and content differences
        2. If in D only or E only → NO_CONFLICT
        
        Special cases:
        - Vendor deleted (DEPRECATED) + Customer modified → DELETED
        - Both modified but B == C (same content) → NO_CONFLICT
        - Both modified and B != C (different content) → CONFLICT
        """
        if in_vendor and in_customer:
            # Both parties modified the same object
            # Check for special case: vendor deleted, customer modified
            if (vendor_change.change_category == ChangeCategory.DEPRECATED and
                customer_change.change_category == ChangeCategory.MODIFIED):
                self.logger.debug(
                    f"Object {vendor_change.object_id}: DELETED "
                    f"(vendor removed, customer modified)"
                )
                return Classification.DELETED
            
            # Check if customer version (B) and new vendor version (C) are actually different
            if self.content_comparator:
                are_different = self.content_comparator.compare_customer_vs_new_vendor(
                    vendor_change.object_id
                )
                
                if not are_different:
                    # Both modified the same way - no conflict
                    self.logger.debug(
                        f"Object {vendor_change.object_id}: NO_CONFLICT "
                        f"(both modified but B == C)"
                    )
                    return Classification.NO_CONFLICT
            
            # True conflict - both modified differently
            self.logger.debug(
                f"Object {vendor_change.object_id}: CONFLICT "
                f"(both modified and B != C)"
            )
            return Classification.CONFLICT
        
        elif in_vendor:
            # Only vendor changed this object
            self.logger.debug(
                f"Object {vendor_change.object_id}: NO_CONFLICT (vendor only)"
            )
            return Classification.NO_CONFLICT
        
        elif in_customer:
            # Only customer changed this object
            self.logger.debug(
                f"Object {customer_change.object_id}: NO_CONFLICT (customer only)"
            )
            return Classification.NO_CONFLICT
        
        else:
            # This shouldn't happen
            raise ValueError("Object not in vendor or customer changes")
    
    def _get_classification_stats(
        self,
        analyses: List[MergeAnalysis]
    ) -> Dict[str, int]:
        """Get statistics for classifications."""
        stats = {
            'CONFLICT': 0,
            'NO_CONFLICT': 0,
            'DELETED': 0
        }
        
        for analysis in analyses:
            classification_str = analysis.classification.value
            stats[classification_str] = stats.get(classification_str, 0) + 1
        
        return stats


class ClassificationService(BaseService):
    """
    Service for classifying changes using set-based logic.
    
    This service:
    1. Takes vendor changes (Set D) and customer changes (Set E)
    2. Applies set-based classification logic
    3. Creates Change records in the working set
    4. Sets display_order for consistent presentation
    """
    
    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.change_repo = self._get_repository(ChangeRepository)
        self.classifier = SetBasedClassifier()
    
    def classify(
        self,
        session_id: int,
        vendor_changes: List[VendorChange],
        customer_changes: List[CustomerChange],
        customer_package_id: int,
        new_vendor_package_id: int
    ) -> List[ClassifiedChange]:
        """
        Classify changes using set-based logic with content comparison.
        
        Args:
            session_id: Merge session ID
            vendor_changes: List of VendorChange entities (Set D)
            customer_changes: List of CustomerChange entities (Set E)
            customer_package_id: Package B (Customer) ID
            new_vendor_package_id: Package C (New Vendor) ID
            
        Returns:
            List of ClassifiedChange entities
        """
        self.logger.info(
            f"Starting classification for session {session_id}: "
            f"Vendor changes={len(vendor_changes)}, "
            f"Customer changes={len(customer_changes)}"
        )
        
        # Create content comparator for B vs C comparison
        content_comparator = ContentComparator(
            customer_package_id,
            new_vendor_package_id
        )
        
        # Update classifier with content comparator
        self.classifier.content_comparator = content_comparator
        
        # Apply set-based classification
        analyses = self.classifier.classify(vendor_changes, customer_changes)
        
        # Convert to ClassifiedChange entities
        classified_changes = []
        
        for analysis in analyses:
            vendor_change_type = (
                analysis.vendor_change.change_type
                if analysis.vendor_change
                else None
            )
            
            customer_change_type = (
                analysis.customer_change.change_type
                if analysis.customer_change
                else None
            )
            
            classified_change = ClassifiedChange(
                object_id=analysis.object_id,
                classification=analysis.classification,
                vendor_change_type=vendor_change_type,
                customer_change_type=customer_change_type,
                display_order=0
            )
            
            classified_changes.append(classified_change)
        
        # Sort by classification priority for display order
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
            f"CONFLICT={stats['CONFLICT']}, "
            f"NO_CONFLICT={stats['NO_CONFLICT']}, "
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
        2. DELETED (vendor deleted, customer modified)
        3. NO_CONFLICT (lowest priority - can be auto-merged)
        """
        priority_map = {
            Classification.CONFLICT: 1,
            Classification.DELETED: 2,
            Classification.NO_CONFLICT: 3
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
        """Create Change records in database."""
        changes_data = []
        
        for classified_change in classified_changes:
            change_data = {
                'session_id': session_id,
                'object_id': classified_change.object_id,
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
            f"Created {len(changes_data)} change records for session {session_id}"
        )
    
    def _get_classification_stats(
        self,
        classified_changes: List[ClassifiedChange]
    ) -> Dict[str, int]:
        """Get statistics for classified changes."""
        stats = {
            'CONFLICT': 0,
            'NO_CONFLICT': 0,
            'DELETED': 0
        }
        
        for change in classified_changes:
            classification_str = change.classification.value
            stats[classification_str] = stats.get(classification_str, 0) + 1
        
        return stats
