"""
Merge Statistics Calculator

Handles calculation of merge statistics, complexity estimation,
and summary generation for three-way merge sessions.
"""
from typing import Dict, Any, Optional
from sqlalchemy import func, case
from models import db, Change, ChangeReview, Package


class MergeStatisticsCalculator:
    """
    Calculates statistics and summaries for merge sessions
    
    Provides methods for computing merge complexity, estimated time,
    and generating summary reports with optimized SQL queries.
    """
    
    def calculate_summary(
        self,
        session_id: int,
        session
    ) -> Dict[str, Any]:
        """
        Get merge summary with statistics using optimized SQL aggregates

        Uses a single GROUP BY query instead of multiple COUNT queries
        for better performance.

        Args:
            session_id: Session ID
            session: MergeSession instance

        Returns:
            Dictionary with summary information
        """
        # Get package information
        packages = Package.query.filter_by(session_id=session_id).all()
        package_info = {}
        for pkg in packages:
            package_info[pkg.package_type] = pkg.package_name

        # Calculate all statistics in a single optimized query using CASE
        stats_query = db.session.query(
            func.count(Change.id).label('total'),
            func.sum(case((Change.classification == 'NO_CONFLICT', 1), else_=0)).label('no_conflict'),
            func.sum(case((Change.classification == 'CONFLICT', 1), else_=0)).label('conflict'),
            func.sum(case((Change.classification == 'CUSTOMER_ONLY', 1), else_=0)).label('customer_only'),
            func.sum(case((Change.classification == 'REMOVED_BUT_CUSTOMIZED', 1), else_=0)).label('removed_but_customized')
        ).filter(Change.session_id == session_id).first()

        statistics = {
            'total_changes': stats_query.total or 0,
            'no_conflict': stats_query.no_conflict or 0,
            'conflict': stats_query.conflict or 0,
            'customer_only': stats_query.customer_only or 0,
            'removed_but_customized': stats_query.removed_but_customized or 0
        }

        # Calculate breakdown by type using optimized GROUP BY
        breakdown_query = (
            db.session.query(
                Change.object_type,
                Change.classification,
                func.count(Change.id)
            )
            .filter(Change.session_id == session_id)
            .group_by(Change.object_type, Change.classification)
            .all()
        )

        # Build breakdown dictionary
        breakdown_by_type = {}
        for obj_type, classification, count in breakdown_query:
            if obj_type not in breakdown_by_type:
                breakdown_by_type[obj_type] = {
                    'no_conflict': 0,
                    'conflict': 0,
                    'customer_only': 0,
                    'removed_but_customized': 0
                }

            # Map classification to lowercase key
            classification_key = classification.lower()
            if classification_key in breakdown_by_type[obj_type]:
                breakdown_by_type[obj_type][classification_key] = count

        # Estimate complexity and time
        complexity, estimated_hours = self.estimate_complexity(statistics)

        return {
            'session_id': session.id,
            'reference_id': session.reference_id,
            'packages': {
                'base': package_info.get('base', 'Unknown'),
                'customized': package_info.get('customized', 'Unknown'),
                'new_vendor': package_info.get('new_vendor', 'Unknown')
            },
            'statistics': statistics,
            'breakdown_by_type': breakdown_by_type,
            'estimated_complexity': complexity,
            'estimated_time_hours': estimated_hours,
            'status': session.status,
            'created_at': session.created_at.isoformat(),
            'reviewed_count': session.reviewed_count,
            'skipped_count': session.skipped_count
        }

    def estimate_complexity(
        self,
        statistics: Dict[str, int]
    ) -> tuple[str, int]:
        """
        Estimate merge complexity and time

        Args:
            statistics: Statistics dictionary with counts

        Returns:
            Tuple of (complexity_level, estimated_hours)
        """
        conflicts = statistics.get('conflict', 0)
        total = statistics.get('total_changes', 0)

        # Calculate complexity based on conflict ratio
        if total == 0:
            return 'LOW', 0

        conflict_ratio = conflicts / total

        if conflict_ratio < 0.1:
            complexity = 'LOW'
            estimated_hours = max(1, int((total * 2) / 60))
        elif conflict_ratio < 0.3:
            complexity = 'MEDIUM'
            estimated_hours = max(2, int((total * 5) / 60))
        else:
            complexity = 'HIGH'
            estimated_hours = max(4, int((total * 10) / 60))

        return complexity, estimated_hours

    def calculate_report_statistics(
        self,
        session,
        changes_by_category: Dict[str, list]
    ) -> Dict[str, Any]:
        """
        Calculate final statistics for report generation

        Args:
            session: MergeSession instance
            changes_by_category: Dictionary of changes grouped by classification

        Returns:
            Dictionary with report statistics
        """
        return {
            'total_changes': session.total_changes,
            'reviewed': session.reviewed_count,
            'skipped': session.skipped_count,
            'pending': (
                session.total_changes -
                session.reviewed_count -
                session.skipped_count
            ),
            'conflicts': len(changes_by_category.get('CONFLICT', [])),
            'processing_time_seconds': session.total_time,
            'completed_at': (
                session.completed_at.isoformat()
                if session.completed_at else None
            )
        }
