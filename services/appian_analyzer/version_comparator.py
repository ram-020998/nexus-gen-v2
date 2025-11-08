#!/usr/bin/env python3
"""
Appian Version Comparator - Compare two Appian application versions
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from .analyzer import AppianAnalyzer
from .sail_formatter import SAILFormatter

class AppianVersionComparator:
    def __init__(self, version1_zip: str, version2_zip: str):
        self.version1_zip = version1_zip
        self.version2_zip = version2_zip
        self.version1_name = Path(version1_zip).stem
        self.version2_name = Path(version2_zip).stem
        
    def compare_versions(self) -> Dict[str, Any]:
        """Compare two Appian application versions"""
        print(f"🔍 Comparing {self.version1_name} vs {self.version2_name}")
        
        # Generate blueprints for both versions
        analyzer1 = AppianAnalyzer(self.version1_zip)
        analyzer2 = AppianAnalyzer(self.version2_zip)
        
        result1 = analyzer1.analyze()
        result2 = analyzer2.analyze()
        
        # Save individual blueprint files
        Path("output").mkdir(exist_ok=True)
        
        # Save v1 blueprint and lookup
        with open(f"output/{self.version1_name}_blueprint.json", 'w') as f:
            json.dump(result1["blueprint"], f, indent=2)
        with open(f"output/{self.version1_name}_object_lookup.json", 'w') as f:
            json.dump(result1["object_lookup"], f, indent=2)
            
        # Save v2 blueprint and lookup  
        with open(f"output/{self.version2_name}_blueprint.json", 'w') as f:
            json.dump(result2["blueprint"], f, indent=2)
        with open(f"output/{self.version2_name}_object_lookup.json", 'w') as f:
            json.dump(result2["object_lookup"], f, indent=2)
        
        # Perform comparison using both blueprint and object lookup
        comparison = self._compare_results(result1, result2)
        
        # Save comparison result
        comparison_file = f"output/{self.version1_name}_vs_{self.version2_name}_comparison.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=2)
            
        print(f"📊 Comparison saved to {comparison_file}")
        print(f"📄 Individual blueprints saved to output/ folder")
        return comparison
    
    def _compare_results(self, result1: Dict, result2: Dict) -> Dict[str, Any]:
        """Compare two analysis results"""
        
        changes = {
            "comparison_summary": {
                "version_from": self.version1_name,
                "version_to": self.version2_name,
                "comparison_date": "2025-11-07",
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
        added_objects = []
        for uuid in added_uuids:
            obj = lookup2[uuid]
            added_objects.append({
                "uuid": uuid,
                "name": obj.get("name", "Unknown"),
                "type": obj.get("object_type", "Unknown"),
                "change_type": "ADDED"
            })
        
        # Process removed objects
        removed_objects = []
        for uuid in removed_uuids:
            obj = lookup1[uuid]
            removed_objects.append({
                "uuid": uuid,
                "name": obj.get("name", "Unknown"),
                "type": obj.get("object_type", "Unknown"),
                "change_type": "REMOVED"
            })
        
        # Process modified objects (including SAIL code changes)
        modified_objects = []
        for uuid in common_uuids:
            obj1 = lookup1[uuid]
            obj2 = lookup2[uuid]
            
            changes_found = []
            
            # Check basic properties
            if obj1.get("name") != obj2.get("name"):
                changes_found.append(f"Name: '{obj1.get('name')}' → '{obj2.get('name')}'")
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
                        changes_found.append(f"SAIL code modified (+{len_diff} characters)")
                    elif len_diff < 0:
                        changes_found.append(f"SAIL code modified ({len_diff} characters)")
                    else:
                        changes_found.append("SAIL code modified (content changed)")
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
                changes_found.append(f"Field count changed: {len(fields1)} → {len(fields2)}")
            
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
                    # Create formatters for both versions
                    formatter1 = SAILFormatter(lookup1)
                    formatter2 = SAILFormatter(lookup2)
                    
                    # Format SAIL code with UUID replacement
                    change_obj["sail_code_before"] = formatter1.format_sail_code(sail1)
                    change_obj["sail_code_after"] = formatter2.format_sail_code(sail2)
                
                modified_objects.append(change_obj)
        
        # Categorize by object type
        all_changes = added_objects + removed_objects + modified_objects
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
        
        for change in all_changes:
            obj_type = change["type"]
            category = type_mapping.get(obj_type, "other")
            
            if category not in changes["changes_by_category"]:
                changes["changes_by_category"][category] = {
                    "added": 0, "removed": 0, "modified": 0, "total": 0, "details": []
                }
            
            if change["change_type"] == "ADDED":
                changes["changes_by_category"][category]["added"] += 1
            elif change["change_type"] == "REMOVED":
                changes["changes_by_category"][category]["removed"] += 1
            elif change["change_type"] == "MODIFIED":
                changes["changes_by_category"][category]["modified"] += 1
            
            changes["changes_by_category"][category]["total"] += 1
            changes["changes_by_category"][category]["details"].append(change)
        
        changes["detailed_changes"] = all_changes
        total_changes = len(all_changes)
        changes["comparison_summary"]["total_changes"] = total_changes
        changes["comparison_summary"]["impact_level"] = self._assess_impact(total_changes)
        
        return changes
    
    def _compare_component_type(self, comp1: Dict, comp2: Dict, comp_type: str) -> Dict:
        """Compare components of a specific type"""
        
        # Get object lists
        objects1 = comp1.get("objects", []) if isinstance(comp1, dict) else []
        objects2 = comp2.get("objects", []) if isinstance(comp2, dict) else []
        
        # Create UUID mappings
        uuid_map1 = {obj.get("uuid", obj.get("id", "")): obj for obj in objects1}
        uuid_map2 = {obj.get("uuid", obj.get("id", "")): obj for obj in objects2}
        
        added = []
        removed = []
        modified = []
        
        # Find added objects
        for uuid, obj in uuid_map2.items():
            if uuid not in uuid_map1:
                added.append({
                    "uuid": uuid,
                    "name": obj.get("name", "Unknown"),
                    "type": comp_type,
                    "change_type": "ADDED"
                })
        
        # Find removed objects
        for uuid, obj in uuid_map1.items():
            if uuid not in uuid_map2:
                removed.append({
                    "uuid": uuid,
                    "name": obj.get("name", "Unknown"),
                    "type": comp_type,
                    "change_type": "REMOVED"
                })
        
        # Find modified objects
        for uuid in set(uuid_map1.keys()) & set(uuid_map2.keys()):
            obj1 = uuid_map1[uuid]
            obj2 = uuid_map2[uuid]
            
            changes = self._compare_objects(obj1, obj2)
            if changes:
                modified.append({
                    "uuid": uuid,
                    "name": obj2.get("name", "Unknown"),
                    "type": comp_type,
                    "change_type": "MODIFIED",
                    "changes": changes
                })
        
        return {
            "added": len(added),
            "removed": len(removed),
            "modified": len(modified),
            "total": len(added) + len(removed) + len(modified),
            "details": added + removed + modified
        }
    
    def _compare_objects(self, obj1: Dict, obj2: Dict) -> List[str]:
        """Compare two objects and return list of changes"""
        changes = []
        
        # Compare basic properties
        if obj1.get("name") != obj2.get("name"):
            changes.append(f"Name changed: '{obj1.get('name')}' → '{obj2.get('name')}'")
        
        if obj1.get("description") != obj2.get("description"):
            changes.append("Description modified")
        
        # Compare fields/properties
        fields1 = obj1.get("fields", [])
        fields2 = obj2.get("fields", [])
        
        if len(fields1) != len(fields2):
            changes.append(f"Field count changed: {len(fields1)} → {len(fields2)}")
        
        # Compare business logic if present
        logic1 = obj1.get("business_logic", "")
        logic2 = obj2.get("business_logic", "")
        
        if logic1 != logic2:
            changes.append("Business logic modified")
        
        return changes
    
    def _assess_impact(self, total_changes: int) -> str:
        """Assess impact level based on number of changes"""
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

def main():
    """CLI entry point for version comparison"""
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python -m services.appian_analyzer.version_comparator <version1.zip> <version2.zip>")
        sys.exit(1)
    
    version1_zip = sys.argv[1]
    version2_zip = sys.argv[2]
    
    comparator = AppianVersionComparator(version1_zip, version2_zip)
    result = comparator.compare_versions()
    
    # Print summary
    summary = result["comparison_summary"]
    print(f"\n🎯 Comparison Summary:")
    print(f"  📊 Total Changes: {summary['total_changes']}")
    print(f"  📈 Impact Level: {summary['impact_level']}")
    
    if result["changes_by_category"]:
        print(f"\n📋 Changes by Category:")
        for category, changes in result["changes_by_category"].items():
            print(f"  • {category}: +{changes['added']} ~{changes['modified']} -{changes['removed']}")

if __name__ == "__main__":
    main()
