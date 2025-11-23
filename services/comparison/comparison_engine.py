"""
Comparison Engine Service.

This module compares two Appian application blueprints and identifies
changes between versions.
"""

from typing import Dict, Any
from datetime import datetime

from core.base_service import BaseService


class ComparisonEngine(BaseService):
    """
    Compares two application blueprints.
    
    This service analyzes two Appian application blueprints and identifies
    added, removed, and modified objects, including SAIL code changes.
    
    Example:
        >>> engine = ComparisonEngine('v2.4.0', 'v2.6.0')
        >>> comparison = engine.compare_results(old_result, new_result)
        >>> print(comparison['comparison_summary']['total_changes'])
    """
    
    def __init__(self, version1_name: str, version2_name: str, container=None):
        """
        Initialize comparison engine.
        
        Args:
            version1_name: Name of the old version
            version2_name: Name of the new version
            container: Optional dependency container
        """
        super().__init__(container)
        self.version1_name = version1_name
        self.version2_name = version2_name
    
    def compare_results(
        self,
        result1: dict,
        result2: dict
    ) -> Dict[str, Any]:
        """
        Compare two analysis results.
        
        Performs a comprehensive comparison of two application blueprints,
        identifying all changes including SAIL code modifications.
        
        Args:
            result1: Analysis result for old version
            result2: Analysis result for new version
            
        Returns:
            Dict[str, Any]: Comparison results containing:
                - comparison_summary: Overall statistics
                - changes_by_category: Changes grouped by object type
                - detailed_changes: List of all individual changes
                
        Example:
            >>> comparison = engine.compare_results(
            ...     old_analyzer.analyze(),
            ...     new_analyzer.analyze()
            ... )
        """
        changes = {
            "comparison_summary": {
                "version_from": self.version1_name,
                "version_to": self.version2_name,
                "comparison_date": datetime.utcnow().isoformat(),
                "total_changes": 0,
                "impact_level": "LOW"
            },
            "changes_by_category": {},
            "detailed_changes": []
        }
        
        # Get object lookups for direct comparison
        lookup1 = result1.get("object_lookup", {})
        lookup2 = result2.get("object_lookup", {})
        
        if not lookup1 or not lookup2:
            print("⚠️  Object lookup data not available for comparison")
            return changes
        
        # Find added and removed objects
        uuids1 = set(lookup1.keys())
        uuids2 = set(lookup2.keys())
        
        added_uuids = uuids2 - uuids1
        removed_uuids = uuids1 - uuids2
        common_uuids = uuids1 & uuids2
        
        # Process added objects
        added_objects = self._process_added_objects(lookup2, added_uuids)
        
        # Process removed objects
        removed_objects = self._process_removed_objects(lookup1, removed_uuids)
        
        # Process modified objects (including SAIL code changes)
        modified_objects = self._process_modified_objects(
            lookup1,
            lookup2,
            common_uuids
        )
        
        # Categorize by object type
        all_changes = added_objects + removed_objects + modified_objects
        changes["changes_by_category"] = self._categorize_changes(all_changes)
        changes["detailed_changes"] = all_changes
        
        total_changes = len(all_changes)
        changes["comparison_summary"]["total_changes"] = total_changes
        changes["comparison_summary"]["impact_level"] = self._assess_impact(
            total_changes
        )
        
        return changes
    
    def _process_added_objects(
        self,
        lookup: dict,
        uuids: set
    ) -> list:
        """
        Process added objects.
        
        Args:
            lookup: Object lookup dictionary
            uuids: Set of UUIDs for added objects
            
        Returns:
            list: List of added object change records
        """
        added_objects = []
        for uuid in uuids:
            obj = lookup[uuid]
            added_objects.append({
                "uuid": uuid,
                "name": obj.get("name", "Unknown"),
                "type": obj.get("object_type", "Unknown"),
                "change_type": "ADDED"
            })
        return added_objects
    
    def _process_removed_objects(
        self,
        lookup: dict,
        uuids: set
    ) -> list:
        """
        Process removed objects.
        
        Args:
            lookup: Object lookup dictionary
            uuids: Set of UUIDs for removed objects
            
        Returns:
            list: List of removed object change records
        """
        removed_objects = []
        for uuid in uuids:
            obj = lookup[uuid]
            removed_objects.append({
                "uuid": uuid,
                "name": obj.get("name", "Unknown"),
                "type": obj.get("object_type", "Unknown"),
                "change_type": "REMOVED"
            })
        return removed_objects
    
    def _process_modified_objects(
        self,
        lookup1: dict,
        lookup2: dict,
        common_uuids: set
    ) -> list:
        """
        Process modified objects.
        
        Args:
            lookup1: Object lookup for old version
            lookup2: Object lookup for new version
            common_uuids: Set of UUIDs present in both versions
            
        Returns:
            list: List of modified object change records
        """
        modified_objects = []
        
        for uuid in common_uuids:
            obj1 = lookup1[uuid]
            obj2 = lookup2[uuid]
            
            changes_found = []
            
            # Check basic properties
            if obj1.get("name") != obj2.get("name"):
                changes_found.append(
                    f"Name: '{obj1.get('name')}' → '{obj2.get('name')}'"
                )
            if obj1.get("description") != obj2.get("description"):
                changes_found.append("Description modified")
            
            # Check SAIL code changes
            sail1 = obj1.get("sail_code", "")
            sail2 = obj2.get("sail_code", "")
            sail_changed = False
            
            if sail1 != sail2:
                sail_changed = True
                if sail1 and sail2:
                    # Calculate rough change size
                    len_diff = len(sail2) - len(sail1)
                    if len_diff > 0:
                        changes_found.append(
                            f"SAIL code modified (+{len_diff} characters)"
                        )
                    elif len_diff < 0:
                        changes_found.append(
                            f"SAIL code modified ({len_diff} characters)"
                        )
                    else:
                        changes_found.append(
                            "SAIL code modified (content changed)"
                        )
                elif sail2 and not sail1:
                    changes_found.append("SAIL code added")
                elif sail1 and not sail2:
                    changes_found.append("SAIL code removed")
            
            # Check business logic changes
            logic1 = obj1.get("business_logic", "")
            logic2 = obj2.get("business_logic", "")
            if logic1 != logic2:
                changes_found.append("Business logic modified")
            
            # Check field changes for record types
            fields1 = obj1.get("fields", [])
            fields2 = obj2.get("fields", [])
            if len(fields1) != len(fields2):
                changes_found.append(
                    f"Field count changed: {len(fields1)} → {len(fields2)}"
                )
            
            if changes_found:
                change_obj = {
                    "uuid": uuid,
                    "name": obj2.get("name", "Unknown"),
                    "type": obj2.get("object_type", "Unknown"),
                    "change_type": "MODIFIED",
                    "changes": changes_found,
                    "sail_code_changed": sail_changed
                }
                
                # Add actual SAIL code if it changed
                if sail_changed:
                    change_obj["sail_code_before"] = sail1
                    change_obj["sail_code_after"] = sail2
                
                modified_objects.append(change_obj)
        
        return modified_objects
    
    def _categorize_changes(self, all_changes: list) -> dict:
        """
        Categorize changes by object type.
        
        Args:
            all_changes: List of all change records
            
        Returns:
            dict: Changes grouped by category
        """
        type_mapping = {
            "Process Model": "process_models",
            "Expression Rule": "expression_rules",
            "Interface": "interfaces",
            "Record Type": "record_types",
            "Security Group": "security_groups",
            "Constant": "constants",
            "Site": "sites",
            "Connected System": "integrations",
            "Web API": "integrations"
        }
        
        changes_by_category = {}
        
        for change in all_changes:
            obj_type = change["type"]
            category = type_mapping.get(obj_type, "other")
            
            if category not in changes_by_category:
                changes_by_category[category] = {
                    "added": 0,
                    "removed": 0,
                    "modified": 0,
                    "total": 0,
                    "details": []
                }
            
            if change["change_type"] == "ADDED":
                changes_by_category[category]["added"] += 1
            elif change["change_type"] == "REMOVED":
                changes_by_category[category]["removed"] += 1
            elif change["change_type"] == "MODIFIED":
                changes_by_category[category]["modified"] += 1
            
            changes_by_category[category]["total"] += 1
            changes_by_category[category]["details"].append(change)
        
        return changes_by_category
    
    def _assess_impact(self, total_changes: int) -> str:
        """
        Assess impact level based on number of changes.
        
        Args:
            total_changes: Total number of changes detected
            
        Returns:
            str: Impact level (NONE, LOW, MEDIUM, HIGH, VERY_HIGH)
        """
        if total_changes == 0:
            return "NONE"
        elif total_changes <= 10:
            return "LOW"
        elif total_changes <= 50:
            return "MEDIUM"
        elif total_changes <= 100:
            return "HIGH"
        else:
            return "VERY_HIGH"
