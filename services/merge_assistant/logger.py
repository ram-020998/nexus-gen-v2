"""
Logging configuration for Three-Way Merge Assistant

Extends the existing Appian Analyzer logging system with merge-specific
functionality for tracking merge sessions, stage transitions, and user actions.
"""
from services.appian_analyzer.logger import (
    get_logger,
    RequestLogger
)


class MergeSessionLogger(RequestLogger):
    """
    Context-aware logger for tracking merge sessions
    
    Extends RequestLogger with merge-specific logging methods for
    tracking stage transitions, metrics, and user actions.
    """
    
    def __init__(self, session_id, logger=None):
        """
        Initialize merge session logger
        
        Args:
            session_id: Merge session reference ID (e.g., "MRG_001")
            logger: Base logger instance (creates new if not provided)
        """
        super().__init__(session_id, logger)
        self.session_id = session_id
    
    def log_upload(self, base_name, customized_name, new_vendor_name):
        """
        Log package upload stage
        
        Args:
            base_name: Base package filename
            customized_name: Customized package filename
            new_vendor_name: New vendor package filename
        """
        self.log_stage('Upload', {
            'base_package': base_name,
            'customized_package': customized_name,
            'new_vendor_package': new_vendor_name
        })
    
    def log_blueprint_generation_start(self, package_type):
        """
        Log start of blueprint generation for a package
        
        Args:
            package_type: 'base', 'customized', or 'new_vendor'
        """
        self.info(f"Starting blueprint generation for {package_type} package")
    
    def log_blueprint_generation_complete(
        self,
        package_type,
        total_objects,
        elapsed_time
    ):
        """
        Log completion of blueprint generation
        
        Args:
            package_type: 'base', 'customized', or 'new_vendor'
            total_objects: Number of objects in blueprint
            elapsed_time: Time taken in seconds
        """
        self.info(
            f"Blueprint generation complete for {package_type}: "
            f"{total_objects} objects in {elapsed_time:.2f}s"
        )
    
    def log_blueprint_generation_error(self, package_type, error):
        """
        Log blueprint generation error
        
        Args:
            package_type: 'base', 'customized', or 'new_vendor'
            error: Error message or exception
        """
        self.error(
            f"Blueprint generation failed for {package_type}: {error}",
            exc_info=True
        )
    
    def log_comparison_start(self, comparison_type):
        """
        Log start of comparison
        
        Args:
            comparison_type: 'vendor' (A→C) or 'customer' (A→B)
        """
        self.log_stage(
            'Comparison',
            {'type': comparison_type}
        )
    
    def log_comparison_complete(
        self,
        comparison_type,
        added_count,
        modified_count,
        removed_count
    ):
        """
        Log completion of comparison
        
        Args:
            comparison_type: 'vendor' or 'customer'
            added_count: Number of added objects
            modified_count: Number of modified objects
            removed_count: Number of removed objects
        """
        self.log_metrics({
            f'{comparison_type}_added': added_count,
            f'{comparison_type}_modified': modified_count,
            f'{comparison_type}_removed': removed_count,
            f'{comparison_type}_total': (
                added_count + modified_count + removed_count
            )
        })
    
    def log_classification_start(self):
        """Log start of change classification"""
        self.log_stage('Classification', {})
    
    def log_classification_complete(
        self,
        no_conflict_count,
        conflict_count,
        customer_only_count,
        removed_but_customized_count
    ):
        """
        Log completion of change classification
        
        Args:
            no_conflict_count: Number of NO_CONFLICT changes
            conflict_count: Number of CONFLICT changes
            customer_only_count: Number of CUSTOMER_ONLY changes
            removed_but_customized_count: Number of REMOVED_BUT_CUSTOMIZED
        """
        self.log_metrics({
            'no_conflict': no_conflict_count,
            'conflict': conflict_count,
            'customer_only': customer_only_count,
            'removed_but_customized': removed_but_customized_count,
            'total_changes': (
                no_conflict_count + conflict_count +
                customer_only_count + removed_but_customized_count
            )
        })
    
    def log_ordering_start(self):
        """Log start of change ordering"""
        self.log_stage('Ordering', {})
    
    def log_ordering_complete(self, total_ordered):
        """
        Log completion of change ordering
        
        Args:
            total_ordered: Number of changes ordered
        """
        self.info(f"Change ordering complete: {total_ordered} changes ordered")
    
    def log_circular_dependency_detected(self, cycle_info):
        """
        Log detection of circular dependencies
        
        Args:
            cycle_info: Information about the circular dependency
        """
        self.warning(
            f"Circular dependency detected and broken: {cycle_info}"
        )
    
    def log_guidance_generation_start(self):
        """Log start of merge guidance generation"""
        self.log_stage('Guidance Generation', {})
    
    def log_guidance_generation_complete(self, total_changes):
        """
        Log completion of merge guidance generation
        
        Args:
            total_changes: Number of changes with guidance
        """
        self.info(
            f"Merge guidance generation complete for {total_changes} changes"
        )
    
    def log_session_ready(self, total_time):
        """
        Log session ready for workflow
        
        Args:
            total_time: Total processing time in seconds
        """
        self.log_completion(
            status='success',
            total_time=f"{total_time}s",
            session_status='ready'
        )
    
    def log_workflow_start(self):
        """Log start of guided workflow"""
        self.log_stage('Workflow', {'action': 'start'})
    
    def log_user_action(
        self,
        action,
        change_index,
        object_name,
        object_type,
        classification
    ):
        """
        Log user review action
        
        Args:
            action: 'reviewed' or 'skipped'
            change_index: Index of the change
            object_name: Name of the object
            object_type: Type of the object
            classification: Classification category
        """
        self.info(
            f"User action: {action} | "
            f"Change {change_index} | "
            f"{object_type}: {object_name} | "
            f"Classification: {classification}"
        )
    
    def log_workflow_complete(self, reviewed_count, skipped_count):
        """
        Log completion of workflow
        
        Args:
            reviewed_count: Number of reviewed changes
            skipped_count: Number of skipped changes
        """
        self.log_completion(
            status='success',
            reviewed=reviewed_count,
            skipped=skipped_count,
            session_status='completed'
        )
    
    def log_report_generation(self):
        """Log report generation"""
        self.log_stage('Report Generation', {})
    
    def log_report_export(self, format_type):
        """
        Log report export
        
        Args:
            format_type: 'json' or 'pdf'
        """
        self.info(f"Report exported as {format_type}")
    
    def log_filter_applied(
        self,
        classification=None,
        object_type=None,
        review_status=None,
        search_term=None,
        result_count=0
    ):
        """
        Log filter application
        
        Args:
            classification: Classification filter
            object_type: Object type filter
            review_status: Review status filter
            search_term: Search term
            result_count: Number of results after filtering
        """
        filters = []
        if classification:
            filters.append(f"classification={classification}")
        if object_type:
            filters.append(f"type={object_type}")
        if review_status:
            filters.append(f"status={review_status}")
        if search_term:
            filters.append(f"search='{search_term}'")
        
        filter_str = ", ".join(filters) if filters else "none"
        self.info(
            f"Filters applied: {filter_str} | Results: {result_count}"
        )
    
    def log_error(self, phase, error, context=None):
        """
        Log error with full context
        
        Args:
            phase: Phase where error occurred
            error: Error message or exception
            context: Additional context dictionary
        """
        context_str = ""
        if context:
            context_str = " | " + ", ".join(
                f"{k}={v}" for k, v in context.items()
            )
        
        self.error(
            f"Error in {phase}: {error}{context_str}",
            exc_info=True
        )


def create_merge_session_logger(session_id):
    """
    Create a merge session-specific logger
    
    Args:
        session_id: Merge session reference ID (e.g., "MRG_001")
    
    Returns:
        MergeSessionLogger instance
    """
    return MergeSessionLogger(session_id, get_logger())
