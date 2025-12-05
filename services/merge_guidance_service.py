"""
Merge Guidance Service

Generates merge recommendations and identifies conflicts for each change
in the working set.
"""

import logging
from typing import List, Dict, Any, Optional

from core.base_service import BaseService
from models import db


class ConflictAnalyzer:
    """
    Analyzer for identifying specific conflicts in changes.

    This component examines CONFLICT-classified changes to identify:
    - What specifically changed in vendor version
    - What specifically changed in customer version
    - Areas of overlap that require manual review
    """

    def __init__(self):
        """Initialize conflict analyzer."""
        self.logger = logging.getLogger(__name__)

    def analyze(
        self,
        change: Any,
        object_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a conflict to identify specific areas of concern.

        Args:
            change: Change entity with CONFLICT classification
            object_data: Object data including versions from all packages

        Returns:
            Dict with conflict analysis:
                - conflict_type: Type of conflict
                - vendor_changes: List of vendor modifications
                - customer_changes: List of customer modifications
                - overlap_areas: Areas where both modified same thing
                - severity: LOW, MEDIUM, HIGH

        Example:
            >>> analyzer = ConflictAnalyzer()
            >>> analysis = analyzer.analyze(change, object_data)
            >>> print(analysis['severity'])  # 'HIGH'
        """
        self.logger.debug(
            f"Analyzing conflict for object {change.object_id}"
        )

        # Default conflict analysis
        analysis = {
            'conflict_type': 'GENERAL',
            'vendor_changes': [],
            'customer_changes': [],
            'overlap_areas': [],
            'severity': 'MEDIUM'
        }

        # Analyze based on object type
        object_type = object_data.get('object_type', 'Unknown')

        if object_type in ['Interface', 'Expression Rule']:
            analysis['conflict_type'] = 'SAIL_CODE'
            analysis['vendor_changes'].append('SAIL code modified')
            analysis['customer_changes'].append('SAIL code modified')
            analysis['overlap_areas'].append('SAIL code')
            analysis['severity'] = 'HIGH'

        elif object_type == 'Process Model':
            analysis['conflict_type'] = 'PROCESS_STRUCTURE'
            analysis['vendor_changes'].append('Process structure modified')
            analysis['customer_changes'].append(
                'Process structure modified'
            )
            analysis['overlap_areas'].append('Process nodes/flows')
            analysis['severity'] = 'HIGH'

        elif object_type == 'Record Type':
            analysis['conflict_type'] = 'DATA_MODEL'
            analysis['vendor_changes'].append('Data model modified')
            analysis['customer_changes'].append('Data model modified')
            analysis['overlap_areas'].append('Fields/relationships')
            analysis['severity'] = 'MEDIUM'

        else:
            analysis['conflict_type'] = 'GENERAL'
            analysis['vendor_changes'].append('Object modified')
            analysis['customer_changes'].append('Object modified')
            analysis['severity'] = 'MEDIUM'

        return analysis


class RecommendationEngine:
    """
    Engine for generating merge recommendations.

    This component generates actionable recommendations for each change:
    - AUTO_MERGE: Can be automatically merged
    - MANUAL_MERGE: Requires manual review and merge
    - ACCEPT_VENDOR: Accept vendor version
    - KEEP_CUSTOMER: Keep customer version
    - CUSTOM_MERGE: Requires custom merge strategy
    """

    def __init__(self):
        """Initialize recommendation engine."""
        self.logger = logging.getLogger(__name__)

    def generate_recommendation(
        self,
        change: Any,
        conflict_analysis: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate merge recommendation for a change.

        Args:
            change: Change entity
            conflict_analysis: Optional conflict analysis for CONFLICT

        Returns:
            Dict with recommendation:
                - action: Recommended action
                - reason: Explanation for recommendation
                - confidence: Confidence level (LOW, MEDIUM, HIGH)
                - steps: List of suggested steps

        Example:
            >>> engine = RecommendationEngine()
            >>> rec = engine.generate_recommendation(change)
            >>> print(rec['action'])  # 'AUTO_MERGE'
        """
        self.logger.debug(
            f"Generating recommendation for change {change.id}"
        )

        classification = change.classification

        # NO_CONFLICT: Auto-merge
        if classification == 'NO_CONFLICT':
            return {
                'action': 'AUTO_MERGE',
                'reason': (
                    'No customer modifications detected. '
                    'Vendor changes can be safely applied.'
                ),
                'confidence': 'HIGH',
                'steps': [
                    'Accept vendor version',
                    'Deploy to customer environment',
                    'Test functionality'
                ]
            }

        # NEW: Accept vendor
        elif classification == 'NEW':
            return {
                'action': 'ACCEPT_VENDOR',
                'reason': (
                    'New object from vendor. '
                    'No customer version exists.'
                ),
                'confidence': 'HIGH',
                'steps': [
                    'Review new object functionality',
                    'Accept vendor version',
                    'Deploy to customer environment',
                    'Test integration with existing objects'
                ]
            }

        # DELETED: Keep customer or remove
        elif classification == 'DELETED':
            return {
                'action': 'MANUAL_REVIEW',
                'reason': (
                    'Vendor modified object that customer removed. '
                    'Decide whether to restore with vendor changes '
                    'or keep removed.'
                ),
                'confidence': 'MEDIUM',
                'steps': [
                    'Review why customer removed object',
                    'Review vendor modifications',
                    'Decide: restore with changes or keep removed',
                    'Document decision'
                ]
            }

        # CONFLICT: Manual merge required
        elif classification == 'CONFLICT':
            severity = 'MEDIUM'
            if conflict_analysis:
                severity = conflict_analysis.get('severity', 'MEDIUM')

            return {
                'action': 'MANUAL_MERGE',
                'reason': (
                    'Both vendor and customer modified this object. '
                    'Manual merge required to preserve both changes.'
                ),
                'confidence': 'HIGH',
                'severity': severity,
                'steps': [
                    'Review vendor changes in detail',
                    'Review customer changes in detail',
                    'Identify overlapping modifications',
                    'Manually merge both sets of changes',
                    'Test merged version thoroughly',
                    'Document merge decisions'
                ]
            }

        else:
            return {
                'action': 'MANUAL_REVIEW',
                'reason': 'Unknown classification. Manual review required.',
                'confidence': 'LOW',
                'steps': [
                    'Review change details',
                    'Determine appropriate action'
                ]
            }


class MergeGuidanceService(BaseService):
    """
    Service for generating merge guidance and recommendations.

    This service:
    1. Analyzes each change in the working set
    2. For CONFLICT changes, performs detailed conflict analysis
    3. Generates actionable recommendations
    4. Provides guidance for merge workflow

    Key Design Principles:
    - Guidance is generated for all changes
    - CONFLICT changes get detailed analysis
    - Recommendations are actionable and specific
    - Confidence levels help prioritize review
    """

    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)

    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.conflict_analyzer = ConflictAnalyzer()
        self.recommendation_engine = RecommendationEngine()

    def generate_guidance(
        self,
        session_id: int,
        changes: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate merge guidance for all changes in a session.

        This is the main entry point for guidance generation. It:
        1. Iterates through all changes
        2. For CONFLICT changes, performs conflict analysis
        3. Generates recommendations for each change
        4. Returns list of guidance records

        Args:
            session_id: Merge session ID
            changes: List of Change entities from classification

        Returns:
            List of guidance dicts with recommendations

        Example:
            >>> service = MergeGuidanceService()
            >>> guidance = service.generate_guidance(
            ...     session_id=1,
            ...     changes=changes
            ... )
            >>> print(f"Generated {len(guidance)} guidance records")
        """
        self.logger.info(
            f"Generating merge guidance for session {session_id}: "
            f"{len(changes)} changes"
        )

        guidance_records = []

        for change in changes:
            # Get object data (would normally fetch from database)
            object_data = self._get_object_data(change.object_id)

            # Analyze conflicts if CONFLICT classification
            conflict_analysis = None
            if change.classification == 'CONFLICT':
                conflict_analysis = self.conflict_analyzer.analyze(
                    change,
                    object_data
                )

            # Generate recommendation
            recommendation = (
                self.recommendation_engine.generate_recommendation(
                    change,
                    conflict_analysis
                )
            )

            # Create guidance record
            guidance = {
                'session_id': session_id,
                'change_id': change.id,
                'object_id': change.object_id,
                'classification': change.classification,
                'recommendation': recommendation,
                'conflict_analysis': conflict_analysis
            }

            guidance_records.append(guidance)

        # Log statistics
        stats = self._get_guidance_stats(guidance_records)
        self.logger.info(
            f"Guidance generation complete for session {session_id}: "
            f"AUTO_MERGE={stats['AUTO_MERGE']}, "
            f"MANUAL_MERGE={stats['MANUAL_MERGE']}, "
            f"ACCEPT_VENDOR={stats['ACCEPT_VENDOR']}, "
            f"MANUAL_REVIEW={stats['MANUAL_REVIEW']}"
        )

        return guidance_records

    def _get_object_data(self, object_id: int) -> Dict[str, Any]:
        """
        Get object data for analysis.

        Fetches from database including:
        - Object lookup data
        - Versions from all packages (via object_versions)
        - Object-specific data (using package_id filter)

        Args:
            object_id: Object ID

        Returns:
            Dict with object data including:
                - object_id: Object ID
                - object_type: Object type
                - uuid: Object UUID
                - name: Object name
                - versions: Dict mapping package_id to version data
        """
        from models import ObjectLookup, ObjectVersion
        
        # Get object lookup data
        obj_lookup = db.session.query(ObjectLookup).filter_by(
            id=object_id
        ).first()
        
        if not obj_lookup:
            self.logger.warning(f"Object {object_id} not found in object_lookup")
            return {
                'object_id': object_id,
                'object_type': 'Unknown'
            }
        
        # Get all versions from object_versions (package-specific)
        versions = db.session.query(ObjectVersion).filter_by(
            object_id=object_id
        ).all()
        
        # Build versions dict mapping package_id to version data
        versions_dict = {}
        for version in versions:
            versions_dict[version.package_id] = {
                'version_uuid': version.version_uuid,
                'sail_code': version.sail_code,
                'fields': version.fields,
                'properties': version.properties,
                'raw_xml': version.raw_xml
            }
        
        return {
            'object_id': object_id,
            'object_type': obj_lookup.object_type,
            'uuid': obj_lookup.uuid,
            'name': obj_lookup.name,
            'versions': versions_dict
        }
    
    def _get_object_specific_data(
        self,
        object_id: int,
        package_id: int,
        object_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get object-specific data for a particular package version.
        
        This method queries object-specific tables (interfaces, expression_rules,
        process_models, etc.) using package_id filter to get the correct version.
        
        Args:
            object_id: Object ID from object_lookup
            package_id: Package ID to filter by
            object_type: Object type (Interface, Expression Rule, etc.)
        
        Returns:
            Dict with object-specific data or None if not found
            
        Example:
            >>> data = service._get_object_specific_data(
            ...     object_id=1,
            ...     package_id=2,
            ...     object_type='Interface'
            ... )
            >>> if data:
            ...     print(data['sail_code'])
        """
        from models import (
            Interface, ExpressionRule, ProcessModel, RecordType, CDT,
            Integration, WebAPI, Site, Group, Constant, ConnectedSystem,
            DataStore, UnknownObject
        )
        
        # Map object type to model class
        type_to_model = {
            'Interface': Interface,
            'Expression Rule': ExpressionRule,
            'Process Model': ProcessModel,
            'Record Type': RecordType,
            'CDT': CDT,
            'Integration': Integration,
            'Web API': WebAPI,
            'Site': Site,
            'Group': Group,
            'Constant': Constant,
            'Connected System': ConnectedSystem,
            'Data Store': DataStore,
            'Unknown Object': UnknownObject
        }
        
        model_class = type_to_model.get(object_type)
        if not model_class:
            self.logger.warning(
                f"Unknown object type: {object_type}"
            )
            return None
        
        # Query object-specific table with package_id filter
        obj_specific = db.session.query(model_class).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
        
        if not obj_specific:
            self.logger.debug(
                f"No {object_type} found for object_id={object_id}, "
                f"package_id={package_id}"
            )
            return None
        
        # Convert to dict (basic serialization)
        result = {
            'id': obj_specific.id,
            'object_id': obj_specific.object_id,
            'package_id': obj_specific.package_id,
            'uuid': obj_specific.uuid,
            'name': obj_specific.name,
            'version_uuid': getattr(obj_specific, 'version_uuid', None)
        }
        
        # Add type-specific fields
        if hasattr(obj_specific, 'sail_code'):
            result['sail_code'] = obj_specific.sail_code
        if hasattr(obj_specific, 'description'):
            result['description'] = obj_specific.description
        if hasattr(obj_specific, 'expression'):
            result['expression'] = obj_specific.expression
        
        return result

    def _get_guidance_stats(
        self,
        guidance_records: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Get statistics for guidance records.

        Args:
            guidance_records: List of guidance dicts

        Returns:
            Dict mapping action to count
        """
        stats = {
            'AUTO_MERGE': 0,
            'MANUAL_MERGE': 0,
            'ACCEPT_VENDOR': 0,
            'KEEP_CUSTOMER': 0,
            'MANUAL_REVIEW': 0
        }

        for guidance in guidance_records:
            action = guidance['recommendation']['action']
            stats[action] = stats.get(action, 0) + 1

        return stats

    def get_guidance_for_change(
        self,
        change_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get guidance for a specific change.

        Args:
            change_id: Change ID

        Returns:
            Guidance dict or None if not found

        Example:
            >>> guidance = service.get_guidance_for_change(change_id=1)
            >>> print(guidance['recommendation']['action'])
        """
        # Placeholder - would fetch from database or cache
        self.logger.debug(f"Getting guidance for change {change_id}")
        return None

    def get_conflict_summary(
        self,
        session_id: int
    ) -> Dict[str, Any]:
        """
        Get summary of conflicts for a session.

        Args:
            session_id: Merge session ID

        Returns:
            Dict with conflict summary:
                - total_conflicts: Total number of conflicts
                - by_severity: Count by severity (HIGH, MEDIUM, LOW)
                - by_type: Count by conflict type
                - high_priority: List of high-priority conflicts

        Example:
            >>> summary = service.get_conflict_summary(session_id=1)
            >>> print(f"Total conflicts: {summary['total_conflicts']}")
        """
        self.logger.info(
            f"Getting conflict summary for session {session_id}"
        )

        # Placeholder - would fetch from database
        return {
            'total_conflicts': 0,
            'by_severity': {
                'HIGH': 0,
                'MEDIUM': 0,
                'LOW': 0
            },
            'by_type': {},
            'high_priority': []
        }

    def regenerate_guidance(
        self,
        session_id: int,
        changes: List[Any]
    ) -> List[Dict[str, Any]]:
        """
        Regenerate guidance for a session.

        Useful for reprocessing after changes to recommendation logic.

        Args:
            session_id: Merge session ID
            changes: List of Change entities

        Returns:
            List of guidance dicts

        Example:
            >>> guidance = service.regenerate_guidance(
            ...     session_id=1,
            ...     changes=changes
            ... )
        """
        self.logger.info(
            f"Regenerating guidance for session {session_id}"
        )

        # Delete existing guidance (if stored in database)
        # Then generate new guidance
        return self.generate_guidance(session_id, changes)
