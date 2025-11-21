"""
Enhanced comparison report generation
Aggregates comparison results into comprehensive reports
"""
from typing import List, Dict, Any
from collections import defaultdict
from .models import (
    ComparisonResult,
    EnhancedComparisonReport,
    ImportChangeStatus
)


class ComparisonReportGenerator:
    """Generates comprehensive comparison reports"""

    def __init__(self):
        """Initialize the report generator"""
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

    def generate_report(
        self,
        comparison_results: List[ComparisonResult],
        version_from: str,
        version_to: str
    ) -> EnhancedComparisonReport:
        """
        Generate comprehensive comparison report

        Args:
            comparison_results: List of comparison results
            version_from: Old version name
            version_to: New version name

        Returns:
            EnhancedComparisonReport with all aggregated data
        """
        # Aggregate by status
        changes_by_status = self._aggregate_by_status(comparison_results)

        # Aggregate by category
        changes_by_category = self._aggregate_by_category(
            comparison_results
        )

        # Generate summary
        summary = self._generate_summary(
            comparison_results,
            version_from,
            version_to,
            changes_by_status
        )

        # Generate impact assessment
        impact_assessment = self._assess_impact(
            comparison_results,
            changes_by_status
        )

        # Collect all diagnostics
        diagnostics = self._collect_diagnostics(comparison_results)

        return EnhancedComparisonReport(
            summary=summary,
            changes_by_status=changes_by_status,
            changes_by_category=changes_by_category,
            detailed_changes=comparison_results,
            impact_assessment=impact_assessment,
            diagnostics=diagnostics
        )

    def _aggregate_by_status(
        self,
        results: List[ComparisonResult]
    ) -> Dict[ImportChangeStatus, List[ComparisonResult]]:
        """Aggregate results by ImportChangeStatus"""
        aggregated = defaultdict(list)

        for result in results:
            aggregated[result.status].append(result)

        return dict(aggregated)

    def _aggregate_by_category(
        self,
        results: List[ComparisonResult]
    ) -> Dict[str, Dict[str, int]]:
        """Aggregate results by object category"""
        aggregated = defaultdict(lambda: {
            "added": 0,
            "removed": 0,
            "modified": 0,
            "unchanged": 0,
            "total": 0
        })

        for result in results:
            category = self._get_category(result.obj.object_type)

            # Count by status
            if result.status == ImportChangeStatus.NEW:
                aggregated[category]["added"] += 1
            elif result.status == ImportChangeStatus.REMOVED:
                aggregated[category]["removed"] += 1
            elif result.status in [
                ImportChangeStatus.CHANGED,
                ImportChangeStatus.CONFLICT_DETECTED,
                ImportChangeStatus.NOT_CHANGED_NEW_VUUID
            ]:
                aggregated[category]["modified"] += 1
            elif result.status == ImportChangeStatus.NOT_CHANGED:
                aggregated[category]["unchanged"] += 1

            aggregated[category]["total"] += 1

        return dict(aggregated)

    def _get_category(self, object_type: str) -> str:
        """Map object type to category"""
        return self.type_mapping.get(object_type, "other")

    def _generate_summary(
        self,
        results: List[ComparisonResult],
        version_from: str,
        version_to: str,
        changes_by_status: Dict[ImportChangeStatus, List[ComparisonResult]]
    ) -> Dict[str, Any]:
        """Generate summary statistics"""
        # Count changes (exclude NOT_CHANGED)
        total_changes = sum(
            len(results)
            for status, results in changes_by_status.items()
            if status != ImportChangeStatus.NOT_CHANGED
        )

        # Status breakdown
        status_breakdown = {
            status.value: len(results)
            for status, results in changes_by_status.items()
        }

        return {
            "version_from": version_from,
            "version_to": version_to,
            "total_objects": len(results),
            "total_changes": total_changes,
            "impact_level": self._calculate_impact_level(total_changes),
            "status_breakdown": status_breakdown,
            "has_conflicts": ImportChangeStatus.CONFLICT_DETECTED
            in changes_by_status,
            "conflict_count": len(
                changes_by_status.get(
                    ImportChangeStatus.CONFLICT_DETECTED,
                    []
                )
            )
        }

    def _calculate_impact_level(self, total_changes: int) -> str:
        """Calculate impact level based on number of changes"""
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

    def _assess_impact(
        self,
        results: List[ComparisonResult],
        changes_by_status: Dict[ImportChangeStatus, List[ComparisonResult]]
    ) -> Dict[str, Any]:
        """Generate detailed impact assessment"""
        # Count by object type
        type_counts = defaultdict(int)
        for result in results:
            if result.status != ImportChangeStatus.NOT_CHANGED:
                type_counts[result.obj.object_type] += 1

        # Identify high-impact changes
        high_impact_types = [
            "Process Model",
            "Record Type",
            "Integration",
            "Connected System"
        ]

        high_impact_changes = sum(
            count
            for obj_type, count in type_counts.items()
            if obj_type in high_impact_types
        )

        # Calculate risk factors
        risk_factors = []

        if ImportChangeStatus.CONFLICT_DETECTED in changes_by_status:
            risk_factors.append(
                f"{len(changes_by_status[ImportChangeStatus.CONFLICT_DETECTED])} "
                f"objects with version conflicts"
            )

        if high_impact_changes > 0:
            risk_factors.append(
                f"{high_impact_changes} high-impact object changes"
            )

        removed_count = len(
            changes_by_status.get(ImportChangeStatus.REMOVED, [])
        )
        if removed_count > 5:
            risk_factors.append(
                f"{removed_count} objects removed"
            )

        return {
            "high_impact_changes": high_impact_changes,
            "risk_factors": risk_factors,
            "affected_object_types": dict(type_counts),
            "requires_review": len(risk_factors) > 0
        }

    def _collect_diagnostics(
        self,
        results: List[ComparisonResult]
    ) -> List[str]:
        """Collect all diagnostic messages"""
        diagnostics = []

        for result in results:
            if result.diagnostics:
                for diagnostic in result.diagnostics:
                    diagnostics.append(
                        f"[{result.obj.name}] {diagnostic}"
                    )

        return diagnostics

    def generate_summary_text(
        self,
        report: EnhancedComparisonReport
    ) -> str:
        """
        Generate human-readable summary text

        Args:
            report: EnhancedComparisonReport

        Returns:
            Formatted summary string
        """
        lines = []
        summary = report.summary

        lines.append("=" * 60)
        lines.append("COMPARISON SUMMARY")
        lines.append("=" * 60)
        lines.append(f"From: {summary['version_from']}")
        lines.append(f"To: {summary['version_to']}")
        lines.append(f"Total Objects: {summary['total_objects']}")
        lines.append(f"Total Changes: {summary['total_changes']}")
        lines.append(f"Impact Level: {summary['impact_level']}")
        lines.append("")

        # Status breakdown
        lines.append("STATUS BREAKDOWN:")
        for status, count in summary['status_breakdown'].items():
            lines.append(f"  {status}: {count}")
        lines.append("")

        # Category breakdown
        lines.append("CHANGES BY CATEGORY:")
        for category, counts in report.changes_by_category.items():
            if counts['total'] > 0:
                lines.append(
                    f"  {category}: +{counts['added']} "
                    f"~{counts['modified']} -{counts['removed']}"
                )
        lines.append("")

        # Impact assessment
        if report.impact_assessment['requires_review']:
            lines.append("⚠️  RISK FACTORS:")
            for risk in report.impact_assessment['risk_factors']:
                lines.append(f"  - {risk}")
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)
