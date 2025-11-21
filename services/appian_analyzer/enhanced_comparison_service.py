"""
Enhanced comparison service
Integrates all enhanced comparison components
"""
from typing import Dict, Any
from .enhanced_version_comparator import EnhancedVersionComparator
from .comparison_report_generator import ComparisonReportGenerator
from .web_compatibility_layer import WebCompatibilityLayer
from .logger import get_logger


class EnhancedComparisonService:
    """
    Enhanced comparison service that integrates:
    - Dual-layer comparison logic
    - Report generation
    - Web compatibility
    """

    def __init__(self):
        """Initialize the enhanced comparison service"""
        self.comparator = EnhancedVersionComparator()
        self.report_generator = ComparisonReportGenerator()
        self.compatibility_layer = WebCompatibilityLayer()
        self.logger = get_logger()

    def compare_applications(
        self,
        result1: Dict[str, Any],
        result2: Dict[str, Any],
        version1_name: str,
        version2_name: str
    ) -> Dict[str, Any]:
        """
        Compare two application analysis results

        Args:
            result1: Analysis result from old version
            result2: Analysis result from new version
            version1_name: Name of old version
            version2_name: Name of new version

        Returns:
            Backward compatible comparison result dictionary
        """
        self.logger.info(f"Enhanced comparison: {version1_name} vs {version2_name}")
        
        # Get object lookups
        lookup1 = result1.get("object_lookup", {})
        lookup2 = result2.get("object_lookup", {})
        
        self.logger.debug(f"Object counts: {len(lookup1)} vs {len(lookup2)}")

        if not lookup1 or not lookup2:
            self.logger.error("Object lookup data not available")
            raise ValueError("Object lookup data not available")

        # Convert lookups to AppianObject dictionaries
        self.logger.debug("Converting lookups to AppianObject instances")
        objects1 = self._convert_lookup_to_objects(lookup1)
        objects2 = self._convert_lookup_to_objects(lookup2)

        # Perform enhanced comparison
        self.logger.debug("Performing dual-layer comparison")
        comparison_results = self.comparator.compare_by_uuid(
            objects1,
            objects2
        )

        # Generate enhanced report
        self.logger.debug("Generating comparison report")
        enhanced_report = self.report_generator.generate_report(
            comparison_results,
            version1_name,
            version2_name
        )

        # Convert to backward compatible format
        self.logger.debug("Converting to web-compatible format")
        compatible_result = self.compatibility_layer.to_compatible_format(
            enhanced_report
        )

        # Log summary
        summary = compatible_result.get('comparison_summary', {})
        self.logger.info(f"Comparison complete: {summary.get('total_changes', 0)} changes, "
                        f"impact: {summary.get('impact_level', 'UNKNOWN')}")

        return compatible_result

    def _convert_lookup_to_objects(
        self,
        lookup: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Convert object lookup to dictionary of AppianObject instances

        Args:
            lookup: Object lookup dictionary

        Returns:
            Dictionary of UUID -> AppianObject instances
        """
        from .models import (
            AppianObject,
            SimpleObject,
            ProcessModel,
            RecordType,
            Site
        )

        objects = {}
        for uuid, obj_data in lookup.items():
            try:
                # Create AppianObject or subclass based on object type
                obj_type = obj_data.get("object_type", "Unknown")

                # Extract common fields with safe defaults
                common_fields = {
                    "uuid": uuid,
                    "name": obj_data.get("name", "Unknown"),
                    "object_type": obj_type,
                    "description": obj_data.get("description", ""),
                    "raw_xml": obj_data.get("raw_xml", ""),
                    "version_uuid": obj_data.get("version_uuid", ""),
                    "version_history": obj_data.get("version_history", []),
                    "raw_xml_data": obj_data.get("raw_xml_data", {}),
                    "diff_hash": obj_data.get("diff_hash", "")
                }

                # Create appropriate object type
                if obj_type == "Process Model":
                    obj = ProcessModel(
                        **common_fields,
                        variables=obj_data.get("variables", []),
                        nodes=obj_data.get("nodes", []),
                        flows=obj_data.get("flows", []),
                        interfaces=obj_data.get("interfaces", []),
                        rules=obj_data.get("rules", []),
                        business_logic=obj_data.get("business_logic", ""),
                        security=obj_data.get("security", {"roles": []})
                    )
                elif obj_type == "Record Type":
                    obj = RecordType(
                        **common_fields,
                        fields=obj_data.get("fields", []),
                        relationships=obj_data.get("relationships", []),
                        actions=obj_data.get("actions", []),
                        views=obj_data.get("views", []),
                        security=obj_data.get("security", {"roles": []})
                    )
                elif obj_type == "Site":
                    obj = Site(
                        **common_fields,
                        pages=obj_data.get("pages", []),
                        security=obj_data.get("security", {"roles": []})
                    )
                elif "sail_code" in obj_data or obj_type in [
                    "Interface",
                    "Expression Rule",
                    "Constant"
                ]:
                    sail_code_value = obj_data.get("sail_code", "")
                    obj = SimpleObject(
                        **common_fields,
                        sail_code=sail_code_value,
                        security=obj_data.get("security", {"roles": []})
                    )
                else:
                    # Use base AppianObject for other types
                    obj = AppianObject(**common_fields)

                objects[uuid] = obj

            except Exception as e:
                self.logger.warning(f"Error converting object {uuid}: {str(e)}")
                # Create a basic AppianObject as fallback
                objects[uuid] = AppianObject(
                    uuid=uuid,
                    name=obj_data.get("name", "Unknown"),
                    object_type=obj_data.get("object_type", "Unknown"),
                    description=obj_data.get("description", "")
                )

        return objects
