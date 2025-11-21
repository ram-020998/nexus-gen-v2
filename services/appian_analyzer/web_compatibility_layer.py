"""
Web application compatibility layer
Maps enhanced comparison results to existing web app format
"""
from typing import Dict, Any, List
from .models import (
    ImportChangeStatus,
    ComparisonResult,
    EnhancedComparisonReport
)


class StatusMapper:
    """Maps ImportChangeStatus to UI-friendly change_type"""

    @staticmethod
    def to_ui_change_type(status: ImportChangeStatus) -> str:
        """
        Convert ImportChangeStatus to existing UI change_type

        Args:
            status: ImportChangeStatus enum value

        Returns:
            UI change_type string (ADDED/MODIFIED/REMOVED) or None
        """
        mapping = {
            ImportChangeStatus.NEW: "ADDED",
            ImportChangeStatus.CHANGED: "MODIFIED",
            ImportChangeStatus.CONFLICT_DETECTED: "MODIFIED",
            ImportChangeStatus.NOT_CHANGED: None,  # Don't include
            ImportChangeStatus.NOT_CHANGED_NEW_VUUID: "MODIFIED",
            ImportChangeStatus.REMOVED: "REMOVED",
            ImportChangeStatus.UNKNOWN: "MODIFIED"
        }
        return mapping.get(status)

    @staticmethod
    def get_ui_badge_class(status: ImportChangeStatus) -> str:
        """
        Get Bootstrap badge class for status

        Args:
            status: ImportChangeStatus enum value

        Returns:
            Bootstrap badge class name
        """
        mapping = {
            ImportChangeStatus.NEW: "success",
            ImportChangeStatus.CHANGED: "warning",
            ImportChangeStatus.CONFLICT_DETECTED: "danger",
            ImportChangeStatus.NOT_CHANGED: "secondary",
            ImportChangeStatus.NOT_CHANGED_NEW_VUUID: "info",
            ImportChangeStatus.REMOVED: "danger",
            ImportChangeStatus.UNKNOWN: "secondary"
        }
        return mapping.get(status, "secondary")


class WebCompatibilityLayer:
    """Converts enhanced results to web app compatible format"""

    def __init__(self):
        """Initialize the compatibility layer"""
        self.status_mapper = StatusMapper()
        self.type_mapping = {
            "Process Model": "process_models",
            "Expression Rule": "expression_rules",
            "Interface": "interfaces",
            "Record Type": "record_types",
            "Security Group": "security_groups",
            "Constant": "constants",
            "Site": "sites",
            "Connected System": "integrations",
            "Web API": "integrations",
            "Data Type": "data_types",
            "Report": "reports"
        }

    def to_compatible_format(
        self,
        report: EnhancedComparisonReport
    ) -> Dict[str, Any]:
        """
        Convert enhanced report to backward compatible format

        Args:
            report: EnhancedComparisonReport

        Returns:
            Dictionary in existing web app format
        """
        compatible = {
            "comparison_summary": self._build_summary(report),
            "changes_by_category": {},
            "detailed_changes": []
        }

        # Process each comparison result
        for result in report.detailed_changes:
            # Skip NOT_CHANGED objects
            if result.status == ImportChangeStatus.NOT_CHANGED:
                continue

            # Map to UI change_type
            ui_change_type = self.status_mapper.to_ui_change_type(
                result.status
            )
            if not ui_change_type:
                continue

            # Build compatible change object
            change_obj = self._build_change_object(result, ui_change_type)

            # Categorize by object type
            category = self._get_category(result.obj.object_type)
            if category not in compatible["changes_by_category"]:
                compatible["changes_by_category"][category] = {
                    "added": 0,
                    "removed": 0,
                    "modified": 0,
                    "total": 0,
                    "details": []
                }

            # Update counts
            if ui_change_type == "ADDED":
                compatible["changes_by_category"][category]["added"] += 1
            elif ui_change_type == "REMOVED":
                compatible["changes_by_category"][category]["removed"] += 1
            elif ui_change_type == "MODIFIED":
                compatible["changes_by_category"][category]["modified"] += 1

            compatible["changes_by_category"][category]["total"] += 1
            compatible["changes_by_category"][category]["details"].append(
                change_obj
            )
            compatible["detailed_changes"].append(change_obj)

        return compatible

    def _build_summary(
        self,
        report: EnhancedComparisonReport
    ) -> Dict[str, Any]:
        """Build comparison summary"""
        summary = report.summary.copy()

        # Add enhanced status breakdown
        summary["change_status_breakdown"] = summary.get(
            "status_breakdown",
            {}
        )

        return summary

    def _build_change_object(
        self,
        result: ComparisonResult,
        ui_change_type: str
    ) -> Dict[str, Any]:
        """Build compatible change object"""
        change_obj = {
            "uuid": result.obj.uuid,
            "name": result.obj.name,
            "type": result.obj.object_type,
            "change_type": ui_change_type,  # Backward compatible
            "import_change_status": result.status.value,  # Enhanced
            "changes": self._format_changes(result),
            "sail_code_changed": self._has_sail_code_change(result)
        }

        # Add SAIL code if it exists (for interfaces, rules, etc.)
        # FIX: Always include SAIL code if objects have it, don't rely on content_diff check
        if ui_change_type == "MODIFIED":
            # Check if both objects have sail_code attribute
            has_old_sail = result.old_obj and hasattr(result.old_obj, 'sail_code')
            has_new_sail = hasattr(result.obj, 'sail_code')
            
            if has_old_sail and has_new_sail:
                # Both have SAIL code - include both for comparison
                old_sail = result.old_obj.sail_code if result.old_obj.sail_code else ""
                new_sail = result.obj.sail_code if result.obj.sail_code else ""
                
                # Only include if at least one has content
                if old_sail or new_sail:
                    change_obj["sail_code_before"] = old_sail
                    change_obj["sail_code_after"] = new_sail
        elif ui_change_type == "ADDED":
            if hasattr(result.obj, 'sail_code') and result.obj.sail_code:
                change_obj["sail_code_after"] = result.obj.sail_code
        elif ui_change_type == "REMOVED":
            if result.old_obj and hasattr(result.old_obj, 'sail_code') and result.old_obj.sail_code:
                change_obj["sail_code_before"] = result.old_obj.sail_code
            elif hasattr(result.obj, 'sail_code') and result.obj.sail_code:
                change_obj["sail_code_before"] = result.obj.sail_code

        # Add enhanced fields
        if result.version_info:
            change_obj["version_info"] = result.version_info

        if result.content_diff:
            change_obj["content_diff"] = result.content_diff

        if result.diagnostics:
            change_obj["diagnostics"] = result.diagnostics

        # Add diff hash info
        change_obj["diff_hash_info"] = {
            "content_identical": result.status ==
            ImportChangeStatus.NOT_CHANGED_NEW_VUUID
        }

        return change_obj

    def _format_changes(self, result: ComparisonResult) -> List[str]:
        """Format changes list"""
        if result.content_diff:
            return result.content_diff.split("; ")
        return []

    def _has_sail_code_change(self, result: ComparisonResult) -> bool:
        """Check if SAIL code changed"""
        if not result.content_diff:
            return False
        return "SAIL code" in result.content_diff

    def _get_category(self, object_type: str) -> str:
        """Map object type to category"""
        return self.type_mapping.get(object_type, "other")
