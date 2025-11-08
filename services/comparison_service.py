"""
Comparison Service - Use local appian_analyzer copy
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from models import db, ComparisonRequest

# Import from local copy
try:
    from services.appian_analyzer.analyzer import AppianAnalyzer
    from services.appian_analyzer.version_comparator import AppianVersionComparator
    APPIAN_ANALYZER_AVAILABLE = True
except ImportError:
    APPIAN_ANALYZER_AVAILABLE = False


class ComparisonRequestManager:
    """Manages comparison request lifecycle"""
    
    @staticmethod
    def create_request(old_app_name: str, new_app_name: str) -> ComparisonRequest:
        """Create new comparison request"""
        # Generate reference ID
        count = ComparisonRequest.query.count() + 1
        reference_id = f"CMP_{count:03d}"
        
        request = ComparisonRequest(
            reference_id=reference_id,
            old_app_name=old_app_name,
            new_app_name=new_app_name,
            status='processing'
        )
        
        db.session.add(request)
        db.session.commit()
        return request
    
    @staticmethod
    def update_status(request_id: int, status: str, error_msg: str = None):
        """Update request status"""
        request = ComparisonRequest.query.get(request_id)
        if request:
            request.status = status
            request.updated_at = datetime.utcnow()
            if error_msg:
                request.error_log = error_msg
            db.session.commit()
    
    @staticmethod
    def save_results(request_id: int, old_blueprint: dict, new_blueprint: dict, 
                    comparison: dict, processing_time: int):
        """Save analysis results"""
        request = ComparisonRequest.query.get(request_id)
        if request:
            request.old_app_blueprint = json.dumps(old_blueprint)
            request.new_app_blueprint = json.dumps(new_blueprint)
            request.comparison_results = json.dumps(comparison)
            request.total_time = processing_time
            request.status = 'completed'
            request.updated_at = datetime.utcnow()
            db.session.commit()


class BlueprintAnalyzer:
    """Analyzes Appian application blueprints using local appian_analyzer"""
    
    def analyze_application(self, zip_path: str) -> Dict[str, Any]:
        """Analyze single application using local analyzer"""
        if not APPIAN_ANALYZER_AVAILABLE:
            raise Exception("Local appian_analyzer not available")
        
        try:
            analyzer = AppianAnalyzer(zip_path)
            result = analyzer.analyze()
            return result
        except Exception as e:
            raise Exception(f"Blueprint analysis failed: {str(e)}")


class ComparisonEngine:
    """Compares two application blueprints using exact appianAnalyser logic"""
    
    def __init__(self, version1_name: str, version2_name: str):
        self.version1_name = version1_name
        self.version2_name = version2_name
    
    def compare_results(self, result1: dict, result2: dict) -> Dict[str, Any]:
        """Compare two analysis results - exact copy from appianAnalyser"""
        
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
                    change_obj["sail_code_before"] = sail1
                    change_obj["sail_code_after"] = sail2
                
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


class ComparisonService:
    """Main service orchestrating the comparison process using local appian_analyzer"""
    
    def __init__(self):
        self.request_manager = ComparisonRequestManager()
        self.blueprint_analyzer = BlueprintAnalyzer()


class ComparisonService:
    """Main service orchestrating the comparison process"""
    
    def __init__(self):
        self.request_manager = ComparisonRequestManager()
        self.blueprint_analyzer = BlueprintAnalyzer()
        # ComparisonEngine will be created per request with specific version names
    
    def process_comparison(self, old_zip_path: str, new_zip_path: str) -> ComparisonRequest:
        """Process complete comparison workflow using local appian_analyzer"""
        start_time = time.time()
        
        # Extract app names from file paths
        old_app_name = Path(old_zip_path).stem
        new_app_name = Path(new_zip_path).stem
        
        # Create request
        request = self.request_manager.create_request(old_app_name, new_app_name)
        
        try:
            if not APPIAN_ANALYZER_AVAILABLE:
                raise Exception("Local appian_analyzer not available")
            
            # Use local appian_analyzer version comparator directly
            print(f"DEBUG: Using local appian_analyzer for comparison")
            comparator = AppianVersionComparator(old_zip_path, new_zip_path)
            comparison = comparator.compare_versions()
            
            print(f"DEBUG: Original analyzer found {comparison.get('comparison_summary', {}).get('total_changes', 0)} changes")
            
            # Get individual blueprints for storage
            old_analyzer = AppianAnalyzer(old_zip_path)
            new_analyzer = AppianAnalyzer(new_zip_path)
            
            old_result = old_analyzer.analyze()
            new_result = new_analyzer.analyze()
            
            # Calculate processing time
            processing_time = int(time.time() - start_time)
            
            # Save results
            self.request_manager.save_results(
                request.id, old_result["blueprint"], new_result["blueprint"], comparison, processing_time
            )
            
            return request
            
        except Exception as e:
            self.request_manager.update_status(request.id, 'error', str(e))
            raise e
    
    def get_request_details(self, request_id: int) -> Optional[ComparisonRequest]:
        """Get detailed request information"""
        return ComparisonRequest.query.get(request_id)
    
    def get_all_requests(self) -> list:
        """Get all comparison requests"""
        return ComparisonRequest.query.order_by(ComparisonRequest.created_at.desc()).all()
