"""
Customer Comparison Service

Handles comparison between Package A (Base) and Package B (Customer)
to identify customer changes (Set E).
"""

import logging
from typing import List, Dict, Any, Tuple, Optional

from core.base_service import BaseService
from models import db, ObjectLookup, ObjectVersion
from repositories.object_lookup_repository import ObjectLookupRepository
from repositories.package_object_mapping_repository import PackageObjectMappingRepository
from repositories.customer_comparison_repository import CustomerComparisonRepository
from domain.entities import CustomerChange
from domain.enums import ChangeCategory, ChangeType
from domain.comparison_strategies import (
    SimpleVersionComparisonStrategy,
    SAILCodeComparisonStrategy
)


class CustomerComparisonService(BaseService):
    """
    Service for comparing Package A (Base) to Package B (Customer).
    
    This service identifies customer changes (Set E) by comparing two packages:
    - NEW objects: In B but not in A (customer added)
    - DEPRECATED objects: In A but not in B (customer removed)
    - MODIFIED objects: In both A and B with differences (customer modified)
    
    This is SYMMETRIC with DeltaComparisonService (vendor changes).
    
    Results are stored in customer_comparison_results table.
    """
    
    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.object_lookup_repo = self._get_repository(ObjectLookupRepository)
        self.package_object_mapping_repo = self._get_repository(
            PackageObjectMappingRepository
        )
        self.customer_comparison_repo = self._get_repository(
            CustomerComparisonRepository
        )
        
        # Initialize comparison strategies
        self.version_strategy = SimpleVersionComparisonStrategy()
        self.content_strategy = SAILCodeComparisonStrategy(
            critical_fields=['sail_code', 'fields', 'properties']
        )
    
    def compare(
        self,
        session_id: int,
        base_package_id: int,
        customer_package_id: int
    ) -> List[CustomerChange]:
        """
        Compare Package A (Base) to Package B (Customer) to identify customer changes.
        
        This performs a FULL comparison, symmetric with delta comparison.
        
        Steps:
        1. Get objects in package A
        2. Get objects in package B
        3. Identify NEW objects (in B, not in A)
        4. Identify DEPRECATED objects (in A, not in B)
        5. Identify MODIFIED objects (in both A and B with differences)
        6. Store results in customer_comparison_results
        
        Args:
            session_id: Merge session ID
            base_package_id: Package A (Base) ID
            customer_package_id: Package B (Customer) ID
            
        Returns:
            List of CustomerChange domain entities (Set E)
        """
        self.logger.info(
            f"Starting customer comparison for session {session_id}: "
            f"Package A (id={base_package_id}) → Package B (id={customer_package_id})"
        )
        
        # Get objects in both packages
        base_objects = self.package_object_mapping_repo.get_objects_in_package(
            base_package_id
        )
        customer_objects = self.package_object_mapping_repo.get_objects_in_package(
            customer_package_id
        )
        
        self.logger.info(
            f"Package A has {len(base_objects)} objects, "
            f"Package B has {len(customer_objects)} objects"
        )
        
        # Create lookup maps by UUID
        base_map = {obj.uuid: obj for obj in base_objects}
        customer_map = {obj.uuid: obj for obj in customer_objects}
        
        customer_results = []
        
        # Find NEW objects (in B, not in A)
        new_objects = [
            obj for uuid, obj in customer_map.items()
            if uuid not in base_map
        ]
        
        for obj in new_objects:
            customer_results.append({
                'session_id': session_id,
                'object_id': obj.id,
                'change_category': ChangeCategory.NEW.value,
                'change_type': ChangeType.ADDED.value,
                'version_changed': False,
                'content_changed': False
            })
        
        self.logger.info(f"Found {len(new_objects)} NEW objects (customer added)")
        
        # Find DEPRECATED objects (in A, not in B)
        deprecated_objects = [
            obj for uuid, obj in base_map.items()
            if uuid not in customer_map
        ]
        
        for obj in deprecated_objects:
            customer_results.append({
                'session_id': session_id,
                'object_id': obj.id,
                'change_category': ChangeCategory.DEPRECATED.value,
                'change_type': ChangeType.REMOVED.value,
                'version_changed': False,
                'content_changed': False
            })
        
        self.logger.info(
            f"Found {len(deprecated_objects)} DEPRECATED objects (customer removed)"
        )
        
        # Find MODIFIED objects (in both A and B)
        common_uuids = set(base_map.keys()) & set(customer_map.keys())
        modified_count = 0
        
        for uuid in common_uuids:
            base_obj = base_map[uuid]
            
            # Compare versions
            version_changed, content_changed = self._compare_versions(
                base_obj,
                base_package_id,
                customer_package_id
            )
            
            # Only store if content actually changed
            if content_changed:
                customer_results.append({
                    'session_id': session_id,
                    'object_id': base_obj.id,
                    'change_category': ChangeCategory.MODIFIED.value,
                    'change_type': ChangeType.MODIFIED.value,
                    'version_changed': version_changed,
                    'content_changed': content_changed
                })
                modified_count += 1
        
        self.logger.info(
            f"Found {modified_count} MODIFIED objects (customer modified)"
        )
        
        # Store results in customer_comparison_results
        if customer_results:
            self.customer_comparison_repo.bulk_create_results(customer_results)
            self.logger.info(
                f"Stored {len(customer_results)} customer comparison results"
            )
        
        # Convert to domain entities
        domain_entities = [
            CustomerChange(
                object_id=result['object_id'],
                change_category=ChangeCategory(result['change_category']),
                change_type=ChangeType(result['change_type']),
                version_changed=result['version_changed'],
                content_changed=result['content_changed']
            )
            for result in customer_results
        ]
        
        self.logger.info(
            f"Customer comparison complete: {len(new_objects)} NEW, "
            f"{modified_count} MODIFIED, {len(deprecated_objects)} DEPRECATED"
        )
        
        return domain_entities
    
    def _compare_versions(
        self,
        obj_lookup: ObjectLookup,
        base_package_id: int,
        customer_package_id: int
    ) -> Tuple[bool, bool]:
        """Compare versions between base and customer packages."""
        base_version = self._get_object_version(obj_lookup.id, base_package_id)
        customer_version = self._get_object_version(obj_lookup.id, customer_package_id)
        
        if not base_version or not customer_version:
            return False, False
        
        version_changed = self.version_strategy.compare(
            base_version.version_uuid,
            customer_version.version_uuid
        )
        
        base_content = self._extract_content(base_version)
        customer_content = self._extract_content(customer_version)
        
        content_changed = self.content_strategy.compare(
            base_content,
            customer_content
        )
        
        # CRITICAL FIX: Also check object-specific tables
        # Same fix as DeltaComparisonService
        object_specific_changed = self._compare_object_specific_content(
            obj_lookup,
            base_package_id,
            customer_package_id
        )
        
        # Content is changed if EITHER object_versions OR object-specific tables differ
        content_changed = content_changed or object_specific_changed
        
        return version_changed, content_changed
    
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
    
    def _extract_content(self, version: ObjectVersion) -> Dict[str, Any]:
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
    
    def _compare_object_specific_content(
        self,
        obj_lookup: ObjectLookup,
        base_package_id: int,
        customer_package_id: int
    ) -> bool:
        """
        Compare object-specific table content between base and customer packages.
        Same logic as DeltaComparisonService but for A→B comparison.
        """
        object_type = obj_lookup.object_type
        
        if object_type == "Process Model":
            return self._compare_process_model_content(obj_lookup.id, base_package_id, customer_package_id)
        elif object_type == "Constant":
            return self._compare_constant_content(obj_lookup.id, base_package_id, customer_package_id)
        elif object_type == "Record Type":
            return self._compare_record_type_content(obj_lookup.id, base_package_id, customer_package_id)
        elif object_type == "Interface":
            return self._compare_interface_content(obj_lookup.id, base_package_id, customer_package_id)
        elif object_type == "Expression Rule":
            return self._compare_expression_rule_content(obj_lookup.id, base_package_id, customer_package_id)
        elif object_type == "Data Type":
            return self._compare_cdt_content(obj_lookup.id, base_package_id, customer_package_id)
        
        return False
    
    def _compare_process_model_content(self, object_id: int, base_package_id: int, customer_package_id: int) -> bool:
        """Compare process model nodes, flows, and variables."""
        from models import ProcessModel
        
        base_pm = db.session.query(ProcessModel).filter_by(object_id=object_id, package_id=base_package_id).first()
        customer_pm = db.session.query(ProcessModel).filter_by(object_id=object_id, package_id=customer_package_id).first()
        
        if not base_pm or not customer_pm:
            return False
        
        if base_pm.nodes.count() != customer_pm.nodes.count():
            return True
        if base_pm.flows.count() != customer_pm.flows.count():
            return True
        if base_pm.variables.count() != customer_pm.variables.count():
            return True
        
        base_vars = {(v.variable_name, v.variable_type) for v in base_pm.variables}
        customer_vars = {(v.variable_name, v.variable_type) for v in customer_pm.variables}
        if base_vars != customer_vars:
            return True
        
        return False
    
    def _compare_constant_content(self, object_id: int, base_package_id: int, customer_package_id: int) -> bool:
        """Compare constant value and type."""
        from models import Constant
        
        base_const = db.session.query(Constant).filter_by(object_id=object_id, package_id=base_package_id).first()
        customer_const = db.session.query(Constant).filter_by(object_id=object_id, package_id=customer_package_id).first()
        
        if not base_const or not customer_const:
            return False
        
        if base_const.constant_value != customer_const.constant_value:
            return True
        if base_const.constant_type != customer_const.constant_type:
            return True
        
        return False
    
    def _compare_record_type_content(self, object_id: int, base_package_id: int, customer_package_id: int) -> bool:
        """Compare record type fields, relationships, views, and actions."""
        from models import RecordType
        
        base_rt = db.session.query(RecordType).filter_by(object_id=object_id, package_id=base_package_id).first()
        customer_rt = db.session.query(RecordType).filter_by(object_id=object_id, package_id=customer_package_id).first()
        
        if not base_rt or not customer_rt:
            return False
        
        if base_rt.fields.count() != customer_rt.fields.count():
            return True
        if base_rt.relationships.count() != customer_rt.relationships.count():
            return True
        if base_rt.views.count() != customer_rt.views.count():
            return True
        if base_rt.actions.count() != customer_rt.actions.count():
            return True
        
        return False
    
    def _compare_interface_content(self, object_id: int, base_package_id: int, customer_package_id: int) -> bool:
        """Compare interface parameters and security."""
        from models import Interface
        
        base_intf = db.session.query(Interface).filter_by(object_id=object_id, package_id=base_package_id).first()
        customer_intf = db.session.query(Interface).filter_by(object_id=object_id, package_id=customer_package_id).first()
        
        if not base_intf or not customer_intf:
            return False
        
        if base_intf.parameters.count() != customer_intf.parameters.count():
            return True
        if base_intf.security.count() != customer_intf.security.count():
            return True
        
        return False
    
    def _compare_expression_rule_content(self, object_id: int, base_package_id: int, customer_package_id: int) -> bool:
        """Compare expression rule inputs."""
        from models import ExpressionRule
        
        base_er = db.session.query(ExpressionRule).filter_by(object_id=object_id, package_id=base_package_id).first()
        customer_er = db.session.query(ExpressionRule).filter_by(object_id=object_id, package_id=customer_package_id).first()
        
        if not base_er or not customer_er:
            return False
        
        if base_er.inputs.count() != customer_er.inputs.count():
            return True
        
        return False
    
    def _compare_cdt_content(self, object_id: int, base_package_id: int, customer_package_id: int) -> bool:
        """Compare CDT fields."""
        from models import CDT
        
        base_cdt = db.session.query(CDT).filter_by(object_id=object_id, package_id=base_package_id).first()
        customer_cdt = db.session.query(CDT).filter_by(object_id=object_id, package_id=customer_package_id).first()
        
        if not base_cdt or not customer_cdt:
            return False
        
        if base_cdt.fields.count() != customer_cdt.fields.count():
            return True
        
        return False
