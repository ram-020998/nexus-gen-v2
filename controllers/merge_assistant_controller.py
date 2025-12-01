"""
Merge Assistant Controller - Handle three-way merge operations

This controller provides REST API endpoints for the three-way merge workflow:
- Create merge session from 3 packages
- Get merge session summary
- Get working set of changes
- Get individual change details
"""

import os
from flask import Blueprint, request
from werkzeug.utils import secure_filename

from controllers.base_controller import BaseController
from services.three_way_merge_orchestrator import ThreeWayMergeOrchestrator
from models import db, MergeSession, Change
from core.exceptions import ThreeWayMergeException
from core.logger import get_merge_logger, LoggerConfig

# Create blueprint
merge_bp = Blueprint('merge', __name__, url_prefix='/merge')

# Create controller instance
controller = BaseController()

# Configure logging
logger = get_merge_logger()


@merge_bp.route('/create', methods=['POST'])
def create_merge_session():
    """
    Create a new merge session from three uploaded packages.
    
    Expects multipart/form-data with three files:
    - base_package: Package A (Base Version)
    - customized_package: Package B (Customer Version)
    - new_vendor_package: Package C (New Vendor Version)
    
    Returns:
        JSON response with session information:
        {
            "success": true,
            "message": "Merge session created successfully",
            "data": {
                "reference_id": "MS_A1B2C3",
                "status": "ready",
                "total_changes": 42,
                "session_id": 1
            }
        }
        
    Status Codes:
        201: Session created successfully
        400: Invalid request (missing files, invalid file types)
        500: Server error during processing
        
    Example:
        >>> import requests
        >>> files = {
        ...     'base_package': open('base.zip', 'rb'),
        ...     'customized_package': open('customized.zip', 'rb'),
        ...     'new_vendor_package': open('new_vendor.zip', 'rb')
        ... }
        >>> response = requests.post(
        ...     'http://localhost:5002/merge/create',
        ...     files=files
        ... )
        >>> print(response.json())
    """
    try:
        # Validate request has files
        if 'base_package' not in request.files:
            return controller.json_error(
                'Missing base_package file',
                status_code=400
            )
        
        if 'customized_package' not in request.files:
            return controller.json_error(
                'Missing customized_package file',
                status_code=400
            )
        
        if 'new_vendor_package' not in request.files:
            return controller.json_error(
                'Missing new_vendor_package file',
                status_code=400
            )
        
        # Get uploaded files
        base_file = request.files['base_package']
        customized_file = request.files['customized_package']
        new_vendor_file = request.files['new_vendor_package']
        
        # Validate filenames
        if not base_file.filename:
            return controller.json_error(
                'base_package has no filename',
                status_code=400
            )
        
        if not customized_file.filename:
            return controller.json_error(
                'customized_package has no filename',
                status_code=400
            )
        
        if not new_vendor_file.filename:
            return controller.json_error(
                'new_vendor_package has no filename',
                status_code=400
            )
        
        # Validate file extensions (must be ZIP)
        allowed_extensions = {'zip'}
        
        if not controller.validate_file_extension(
            base_file.filename, allowed_extensions
        ):
            return controller.json_error(
                'base_package must be a ZIP file',
                status_code=400
            )
        
        if not controller.validate_file_extension(
            customized_file.filename, allowed_extensions
        ):
            return controller.json_error(
                'customized_package must be a ZIP file',
                status_code=400
            )
        
        if not controller.validate_file_extension(
            new_vendor_file.filename, allowed_extensions
        ):
            return controller.json_error(
                'new_vendor_package must be a ZIP file',
                status_code=400
            )
        
        # Create upload directory if it doesn't exist
        upload_dir = controller.ensure_directory_exists('uploads/merge')
        
        # Save uploaded files with secure filenames
        base_filename = secure_filename(base_file.filename)
        customized_filename = secure_filename(customized_file.filename)
        new_vendor_filename = secure_filename(new_vendor_file.filename)
        
        base_path = upload_dir / base_filename
        customized_path = upload_dir / customized_filename
        new_vendor_path = upload_dir / new_vendor_filename
        
        base_file.save(str(base_path))
        customized_file.save(str(customized_path))
        new_vendor_file.save(str(new_vendor_path))
        
        LoggerConfig.log_separator(logger, char="-")
        logger.info("FILES UPLOADED SUCCESSFULLY")
        logger.info(f"  Base Package: {base_filename} ({os.path.getsize(base_path)} bytes)")
        logger.info(f"  Customized Package: {customized_filename} ({os.path.getsize(customized_path)} bytes)")
        logger.info(f"  New Vendor Package: {new_vendor_filename} ({os.path.getsize(new_vendor_path)} bytes)")
        LoggerConfig.log_separator(logger, char="-")
        
        # Get orchestrator service
        orchestrator = controller.get_service(ThreeWayMergeOrchestrator)
        
        # Create merge session (this runs the entire workflow)
        logger.info("Initiating three-way merge workflow via orchestrator")
        
        session = orchestrator.create_merge_session(
            base_zip_path=str(base_path),
            customized_zip_path=str(customized_path),
            new_vendor_zip_path=str(new_vendor_path)
        )
        
        LoggerConfig.log_separator(logger, char="-")
        logger.info("MERGE SESSION CREATED SUCCESSFULLY")
        logger.info(f"  Reference ID: {session.reference_id}")
        logger.info(f"  Total Changes: {session.total_changes}")
        logger.info(f"  Status: {session.status}")
        LoggerConfig.log_separator(logger, char="-")
        
        # Return success response
        return controller.json_success(
            data={
                'reference_id': session.reference_id,
                'status': session.status,
                'total_changes': session.total_changes,
                'session_id': session.id
            },
            message='Merge session created successfully',
            status_code=201
        )
        
    except ThreeWayMergeException as e:
        LoggerConfig.log_error_with_context(
            logger,
            e,
            'Create merge session endpoint',
            base_filename=base_file.filename if 'base_file' in locals() else None,
            customized_filename=customized_file.filename if 'customized_file' in locals() else None,
            new_vendor_filename=new_vendor_file.filename if 'new_vendor_file' in locals() else None
        )
        
        # Check if this is a file-related error
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ['file', 'zip', 'corrupt', 'invalid', 'parse']):
            return controller.json_error(
                f"File upload error: {str(e)}",
                status_code=400
            )
        
        return controller.json_error(
            f"Failed to create merge session: {str(e)}",
            status_code=500
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        
        # Check if this is a database error
        if 'database' in str(e).lower() or 'sqlite' in str(e).lower():
            return controller.json_error(
                'Database error occurred. Please try again or contact support.',
                status_code=500
            )
        
        return controller.json_error(
            f"An unexpected error occurred: {str(e)}",
            status_code=500
        )


@merge_bp.route('/api/<reference_id>/summary', methods=['GET'])
def get_merge_summary(reference_id):
    """
    Get summary information for a merge session (API endpoint).
    
    Returns session metadata, package information, and statistics
    broken down by classification and object type.
    
    Args:
        reference_id: Session reference ID (e.g., MS_A1B2C3)
        
    Returns:
        JSON response with summary information:
        {
            "success": true,
            "data": {
                "session": {
                    "reference_id": "MS_A1B2C3",
                    "status": "ready",
                    "total_changes": 42,
                    "created_at": "2024-01-15T10:30:00"
                },
                "packages": {
                    "base": {
                        "filename": "base.zip",
                        "total_objects": 100
                    },
                    "customized": {...},
                    "new_vendor": {...}
                },
                "statistics": {
                    "by_classification": {
                        "NO_CONFLICT": 20,
                        "CONFLICT": 15,
                        "NEW": 5,
                        "DELETED": 2
                    },
                    "by_object_type": {
                        "Interface": 10,
                        "Process Model": 8,
                        ...
                    }
                }
            }
        }
        
    Status Codes:
        200: Success
        404: Session not found
        500: Server error
        
    Example:
        >>> response = requests.get(
        ...     'http://localhost:5002/merge/api/MS_A1B2C3/summary'
        ... )
        >>> summary = response.json()['data']
        >>> print(f"Status: {summary['session']['status']}")
        >>> print(f"Conflicts: {summary['statistics']['by_classification']['CONFLICT']}")
    """
    try:
        # Get orchestrator service
        orchestrator = controller.get_service(ThreeWayMergeOrchestrator)
        
        # Get session status (includes all summary information)
        try:
            status_info = orchestrator.get_session_status(reference_id)
        except ValueError as e:
            return controller.json_error(
                str(e),
                status_code=404
            )
        
        # Return success response
        return controller.json_success(
            data=status_info
        )
        
    except Exception as e:
        logger.error(f"Error getting merge summary: {e}", exc_info=True)
        return controller.json_error(
            f"Failed to get merge summary: {str(e)}",
            status_code=500
        )


@merge_bp.route('/<reference_id>/changes', methods=['GET'])
def get_working_set(reference_id):
    """
    Get working set of changes for a merge session.
    
    Returns all changes in the working set, optionally filtered by
    classification. Changes are ordered by display_order.
    
    Args:
        reference_id: Session reference ID (e.g., MS_A1B2C3)
        
    Query Parameters:
        classification: Optional comma-separated list of classifications
                       to filter (e.g., "CONFLICT,NEW")
        
    Returns:
        JSON response with changes:
        {
            "success": true,
            "data": {
                "changes": [
                    {
                        "change_id": 1,
                        "display_order": 1,
                        "classification": "CONFLICT",
                        "vendor_change_type": "MODIFIED",
                        "customer_change_type": "MODIFIED",
                        "object": {
                            "id": 123,
                            "uuid": "abc-123",
                            "name": "MyInterface",
                            "object_type": "Interface",
                            "description": "..."
                        }
                    },
                    ...
                ],
                "total": 42,
                "filtered": 15
            }
        }
        
    Status Codes:
        200: Success
        404: Session not found
        500: Server error
        
    Example:
        >>> # Get all changes
        >>> response = requests.get(
        ...     'http://localhost:5002/merge/MS_A1B2C3/changes'
        ... )
        
        >>> # Get only conflicts
        >>> response = requests.get(
        ...     'http://localhost:5002/merge/MS_A1B2C3/changes',
        ...     params={'classification': 'CONFLICT'}
        ... )
    """
    try:
        # Get classification filter from query params
        classification_param = request.args.get('classification', '')
        classification_filter = None
        
        if classification_param:
            # Split comma-separated values and strip whitespace
            classification_filter = [
                c.strip() for c in classification_param.split(',')
                if c.strip()
            ]
        
        # Get orchestrator service
        orchestrator = controller.get_service(ThreeWayMergeOrchestrator)
        
        # Get working set
        try:
            changes = orchestrator.get_working_set(
                reference_id=reference_id,
                classification_filter=classification_filter
            )
        except ValueError as e:
            return controller.json_error(
                str(e),
                status_code=404
            )
        
        # Get total count (without filter)
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()
        
        total_count = session.total_changes if session else 0
        
        # Return success response
        return controller.json_success(
            data={
                'changes': changes,
                'total': total_count,
                'filtered': len(changes)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting working set: {e}", exc_info=True)
        return controller.json_error(
            f"Failed to get working set: {str(e)}",
            status_code=500
        )


@merge_bp.route('/<reference_id>/changes/<int:change_id>', methods=['GET'])
def get_change_detail(reference_id, change_id):
    """
    Get detailed information for a specific change (renders template).
    
    Uses ChangeNavigationService to get comprehensive change details
    including navigation, position, progress, and object versions.
    
    Args:
        reference_id: Session reference ID (e.g., MS_A1B2C3)
        change_id: Change ID
        
    Returns:
        Rendered change detail template
        
    Status Codes:
        200: Success
        404: Session or change not found
        500: Server error
        
    Example:
        Navigate to: http://localhost:5002/merge/MS_A1B2C3/changes/1
    """
    from flask import render_template
    from services.change_navigation_service import ChangeNavigationService
    
    try:
        # Get navigation service
        nav_service = controller.get_service(ChangeNavigationService)
        
        # Get change details
        try:
            detail = nav_service.get_change_detail(reference_id, change_id)
        except ValueError as e:
            # Return 404 page for not found errors
            return render_template(
                'errors/404.html',
                message=str(e),
                back_url=f'/merge/{reference_id}/workflow'
            ), 404
        
        # Helper function for object icons
        def get_object_icon(object_type):
            icons = {
                'Interface': 'window-maximize',
                'Expression Rule': 'function',
                'Process Model': 'project-diagram',
                'Record Type': 'database',
                'CDT': 'cube',
                'Integration': 'plug',
                'Web API': 'globe',
                'Site': 'sitemap',
                'Group': 'users',
                'Constant': 'hashtag',
                'Connected System': 'server'
            }
            return icons.get(object_type, 'file')
        
        # Render template
        return render_template(
            'merge/change_detail.html',
            detail=detail,
            get_object_icon=get_object_icon
        )
        
    except Exception as e:
        logger.error(f"Error getting change detail: {e}", exc_info=True)
        return controller.json_error(
            f"Failed to get change detail: {str(e)}",
            status_code=500
        )


@merge_bp.route(
    '/<reference_id>/changes/<int:change_id>/review',
    methods=['POST']
)
def mark_change_reviewed(reference_id, change_id):
    """
    Mark a change as reviewed.
    
    Uses ChangeActionService to update the change status to 'reviewed',
    set the reviewed_at timestamp, and increment the session's
    reviewed_count.
    
    Args:
        reference_id: Session reference ID (e.g., MS_A1B2C3)
        change_id: Change ID
        
    Returns:
        JSON response with updated change information
        
    Status Codes:
        200: Success
        404: Session or change not found
        500: Server error
        
    Example:
        >>> response = requests.post(
        ...     'http://localhost:5002/merge/MS_A1B2C3/changes/1/review'
        ... )
    """
    from services.change_action_service import ChangeActionService
    
    try:
        # Get action service
        action_service = controller.get_service(ChangeActionService)
        
        # Mark as reviewed
        try:
            change = action_service.mark_as_reviewed(
                reference_id,
                change_id
            )
        except ValueError as e:
            return controller.json_error(
                str(e),
                status_code=404
            )
        
        # Return success response
        return controller.json_success(
            data={
                'change_id': change.id,
                'status': change.status,
                'reviewed_at': (
                    change.reviewed_at.isoformat()
                    if change.reviewed_at
                    else None
                )
            },
            message='Change marked as reviewed'
        )
        
    except Exception as e:
        logger.error(f"Error marking change as reviewed: {e}", exc_info=True)
        return controller.json_error(
            f"Failed to mark change as reviewed: {str(e)}",
            status_code=500
        )


@merge_bp.route(
    '/<reference_id>/changes/<int:change_id>/skip',
    methods=['POST']
)
def skip_change_route(reference_id, change_id):
    """
    Mark a change as skipped.
    
    Uses ChangeActionService to update the change status to 'skipped'
    and increment the session's skipped_count.
    
    Args:
        reference_id: Session reference ID (e.g., MS_A1B2C3)
        change_id: Change ID
        
    Returns:
        JSON response with updated change information
        
    Status Codes:
        200: Success
        404: Session or change not found
        500: Server error
        
    Example:
        >>> response = requests.post(
        ...     'http://localhost:5002/merge/MS_A1B2C3/changes/1/skip'
        ... )
    """
    from services.change_action_service import ChangeActionService
    
    try:
        # Get action service
        action_service = controller.get_service(ChangeActionService)
        
        # Skip change
        try:
            change = action_service.skip_change(reference_id, change_id)
        except ValueError as e:
            return controller.json_error(
                str(e),
                status_code=404
            )
        
        # Return success response
        return controller.json_success(
            data={
                'change_id': change.id,
                'status': change.status
            },
            message='Change skipped'
        )
        
    except Exception as e:
        logger.error(f"Error skipping change: {e}", exc_info=True)
        return controller.json_error(
            f"Failed to skip change: {str(e)}",
            status_code=500
        )


@merge_bp.route(
    '/<reference_id>/changes/<int:change_id>/notes',
    methods=['POST']
)
def save_change_notes(reference_id, change_id):
    """
    Save notes for a change.
    
    Uses ChangeActionService to update the change's notes field.
    
    Args:
        reference_id: Session reference ID (e.g., MS_A1B2C3)
        change_id: Change ID
        
    Request Body:
        JSON with 'notes' field containing the notes text
        
    Returns:
        JSON response with updated change information
        
    Status Codes:
        200: Success
        400: Invalid request (missing notes)
        404: Session or change not found
        500: Server error
        
    Example:
        >>> response = requests.post(
        ...     'http://localhost:5002/merge/MS_A1B2C3/changes/1/notes',
        ...     json={'notes': 'This requires manual merge'}
        ... )
    """
    from services.change_action_service import ChangeActionService
    
    try:
        # Validate request
        if not request.json or 'notes' not in request.json:
            return controller.json_error(
                'Missing notes in request body',
                status_code=400
            )
        
        notes = request.json['notes']
        
        # Validate notes length (max 10,000 characters)
        if len(notes) > 10000:
            return controller.json_error(
                'Notes exceed maximum length of 10,000 characters',
                status_code=400
            )
        
        # Get action service
        action_service = controller.get_service(ChangeActionService)
        
        # Save notes
        try:
            change = action_service.save_notes(
                reference_id,
                change_id,
                notes
            )
        except ValueError as e:
            return controller.json_error(
                str(e),
                status_code=404
            )
        
        # Return success response
        return controller.json_success(
            data={
                'change_id': change.id,
                'notes': change.notes
            },
            message='Notes saved'
        )
        
    except Exception as e:
        logger.error(f"Error saving notes: {e}", exc_info=True)
        return controller.json_error(
            f"Failed to save notes: {str(e)}",
            status_code=500
        )


@merge_bp.route(
    '/<reference_id>/changes/<int:change_id>/undo',
    methods=['POST']
)
def undo_change_action(reference_id, change_id):
    """
    Undo a review or skip action on a change.
    
    Uses ChangeActionService to reset the change status to 'pending',
    clear the reviewed_at timestamp, and decrement the appropriate
    session counter.
    
    Args:
        reference_id: Session reference ID (e.g., MS_A1B2C3)
        change_id: Change ID
        
    Returns:
        JSON response with updated change information
        
    Status Codes:
        200: Success
        404: Session or change not found
        500: Server error
        
    Example:
        >>> response = requests.post(
        ...     'http://localhost:5002/merge/MS_A1B2C3/changes/1/undo'
        ... )
    """
    from services.change_action_service import ChangeActionService
    
    try:
        # Get action service
        action_service = controller.get_service(ChangeActionService)
        
        # Undo action
        try:
            change = action_service.undo_action(reference_id, change_id)
        except ValueError as e:
            return controller.json_error(
                str(e),
                status_code=404
            )
        
        # Return success response
        return controller.json_success(
            data={
                'change_id': change.id,
                'status': change.status
            },
            message='Action undone'
        )
        
    except Exception as e:
        logger.error(f"Error undoing action: {e}", exc_info=True)
        return controller.json_error(
            f"Failed to undo action: {str(e)}",
            status_code=500
        )


@merge_bp.route('/<reference_id>/report', methods=['POST'])
def generate_report(reference_id):
    """
    Generate a merge report.
    
    Uses ReportGenerationService to create a downloadable report
    containing session information, statistics, and change details.
    
    Args:
        reference_id: Session reference ID (e.g., MS_A1B2C3)
        
    Query Parameters:
        format: Report format ('xlsx', default: 'xlsx')
        
    Returns:
        File download response with generated report
        
    Status Codes:
        200: Success (file download)
        400: Invalid format
        404: Session not found
        500: Server error
        
    Example:
        >>> response = requests.post(
        ...     'http://localhost:5002/merge/MS_A1B2C3/report',
        ...     params={'format': 'xlsx'}
        ... )
    """
    from flask import send_file
    from services.report_generation_service import ReportGenerationService
    
    try:
        # Get format from query params (default to xlsx)
        report_format = request.args.get('format', 'xlsx')
        
        # Validate format
        if report_format not in ['xlsx']:
            return controller.json_error(
                f"Invalid format: {report_format}. Must be 'xlsx'",
                status_code=400
            )
        
        # Get report service
        report_service = controller.get_service(ReportGenerationService)
        
        # Generate report
        try:
            report_path = report_service.generate_report(
                reference_id,
                format=report_format
            )
        except ValueError as e:
            return controller.json_error(
                str(e),
                status_code=404
            )
        
        # Return file download
        return send_file(
            report_path,
            as_attachment=True,
            download_name=f"{reference_id}_report.{report_format}",
            mimetype=(
                'application/vnd.openxmlformats-officedocument.'
                'spreadsheetml.sheet'
            )
        )
        
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        return controller.json_error(
            f"Failed to generate report: {str(e)}",
            status_code=500
        )


@merge_bp.route('/<reference_id>/objects/<object_type>', methods=['GET'])
def get_objects_by_type(reference_id, object_type):
    """
    Get all changes filtered by object type.
    
    Returns detailed information about all objects of a specific type
    in the merge session, including their classification and complexity.
    
    Args:
        reference_id: Session reference ID (e.g., MS_A1B2C3)
        object_type: Object type to filter by (e.g., 'Interface')
        
    Returns:
        JSON response with object details:
        {
            "success": true,
            "data": {
                "object_type": "Interface",
                "objects": [
                    {
                        "change_id": 1,
                        "object_name": "MyInterface",
                        "object_uuid": "abc-123",
                        "classification": "CONFLICT",
                        "vendor_change_type": "MODIFIED",
                        "customer_change_type": "MODIFIED",
                        "complexity": "Medium"
                    },
                    ...
                ],
                "total": 5
            }
        }
        
    Status Codes:
        200: Success
        404: Session not found
        500: Server error
        
    Example:
        >>> response = requests.get(
        ...     'http://localhost:5002/merge/MS_A1B2C3/objects/Interface'
        ... )
    """
    from sqlalchemy.orm import joinedload
    
    try:
        # Find session
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()
        
        if not session:
            return controller.json_error(
                f"Session not found: {reference_id}",
                status_code=404
            )
        
        # Query changes filtered by object type
        changes = db.session.query(Change).options(
            joinedload(Change.object)
        ).join(
            Change.object
        ).filter(
            Change.session_id == session.id,
            Change.object.has(object_type=object_type)
        ).order_by(
            Change.display_order
        ).all()
        
        # Build response
        objects = []
        for change in changes:
            obj = change.object
            
            # Determine complexity based on classification
            complexity = 'Low'
            if change.classification == 'CONFLICT':
                complexity = 'High'
            elif change.classification in ['NEW', 'DELETED']:
                complexity = 'Medium'
            
            objects.append({
                'change_id': change.id,
                'object_name': obj.name,
                'object_uuid': obj.uuid,
                'classification': change.classification,
                'vendor_change_type': change.vendor_change_type,
                'customer_change_type': change.customer_change_type,
                'complexity': complexity,
                'status': change.status,
                'display_order': change.display_order
            })
        
        # Return success response
        return controller.json_success(
            data={
                'object_type': object_type,
                'objects': objects,
                'total': len(objects)
            }
        )
        
    except Exception as e:
        logger.error(
            f"Error getting objects by type: {e}",
            exc_info=True
        )
        return controller.json_error(
            f"Failed to get objects by type: {str(e)}",
            status_code=500
        )


# Template routes for UI

@merge_bp.route('/upload', methods=['GET'])
def upload():
    """Render the upload page for three packages"""
    from flask import render_template
    return render_template('merge/upload.html')


@merge_bp.route('/sessions', methods=['GET'])
def sessions():
    """Render the sessions list page"""
    from flask import render_template
    
    # Get all sessions ordered by created_at desc
    sessions = db.session.query(MergeSession).order_by(
        MergeSession.created_at.desc()
    ).all()
    
    return render_template('merge/sessions.html', sessions=sessions)


@merge_bp.route('/<reference_id>/summary', methods=['GET'])
def summary(reference_id):
    """Render the session summary page"""
    from flask import render_template
    from services.session_statistics_service import SessionStatisticsService
    
    try:
        # Get orchestrator service
        orchestrator = controller.get_service(ThreeWayMergeOrchestrator)
        
        # Get session status (includes all summary information)
        try:
            status_info = orchestrator.get_session_status(reference_id)
        except ValueError as e:
            return render_template(
                'errors/404.html',
                message=str(e),
                back_url='/merge/sessions'
            ), 404
        
        # Helper function for object icons
        def get_object_icon(object_type):
            icons = {
                'Interface': 'window-maximize',
                'Expression Rule': 'function',
                'Process Model': 'project-diagram',
                'Record Type': 'database',
                'CDT': 'cube',
                'Integration': 'plug',
                'Web API': 'globe',
                'Site': 'sitemap',
                'Group': 'users',
                'Constant': 'hashtag',
                'Connected System': 'server'
            }
            return icons.get(object_type, 'file')
        
        # Get the actual session object for the template
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()
        
        # Get statistics service for complexity and time estimation
        stats_service = controller.get_service(SessionStatisticsService)
        
        # Calculate complexity and time if not already set
        if not session.estimated_complexity:
            complexity = stats_service.calculate_complexity(session.id)
            session.estimated_complexity = complexity
            db.session.commit()
        
        if not session.estimated_time_hours:
            time_hours = stats_service.estimate_review_time(session.id)
            session.estimated_time_hours = time_hours
            db.session.commit()
        
        # Add helper to template context
        return render_template(
            'merge/summary.html',
            session=session,
            packages=status_info['packages'],
            statistics=status_info['statistics'],
            get_object_icon=get_object_icon
        )
        
    except Exception as e:
        logger.error(f"Error rendering summary: {e}", exc_info=True)
        return controller.json_error(
            f"Failed to render summary: {str(e)}",
            status_code=500
        )


@merge_bp.route('/<reference_id>/workflow', methods=['GET'])
def workflow(reference_id):
    """Render the merge workflow page with changes"""
    from flask import render_template
    
    try:
        # Get session
        session = db.session.query(MergeSession).filter_by(
            reference_id=reference_id
        ).first()
        
        if not session:
            return render_template(
                'errors/404.html',
                message=f"Session not found: {reference_id}",
                back_url='/merge/sessions'
            ), 404
        
        # Get orchestrator service
        orchestrator = controller.get_service(ThreeWayMergeOrchestrator)
        
        # Get working set
        changes = orchestrator.get_working_set(reference_id=reference_id)
        
        # Helper function for object icons
        def get_object_icon(object_type):
            icons = {
                'Interface': 'window-maximize',
                'Expression Rule': 'function',
                'Process Model': 'project-diagram',
                'Record Type': 'database',
                'CDT': 'cube',
                'Integration': 'plug',
                'Web API': 'globe',
                'Site': 'sitemap',
                'Group': 'users',
                'Constant': 'hashtag',
                'Connected System': 'server'
            }
            return icons.get(object_type, 'file')
        
        return render_template(
            'merge/workflow.html',
            session=session,
            changes=changes,
            get_object_icon=get_object_icon
        )
        
    except Exception as e:
        logger.error(f"Error rendering workflow: {e}", exc_info=True)
        return controller.json_error(
            f"Failed to render workflow: {str(e)}",
            status_code=500
        )


@merge_bp.route('/components-demo', methods=['GET'])
def components_demo():
    """Render the UI components demo page"""
    from flask import render_template
    return render_template('merge/components_demo.html')


# Error Handlers

@merge_bp.errorhandler(404)
def handle_404(error):
    """
    Handle 404 Not Found errors.
    
    Returns a user-friendly 404 page with navigation options.
    """
    from flask import render_template, request
    
    # Determine appropriate back URL based on request path
    back_url = None
    if '/changes/' in request.path:
        # Extract reference_id from path
        parts = request.path.split('/')
        if len(parts) >= 3:
            reference_id = parts[2]
            back_url = f'/merge/{reference_id}/workflow'
    elif '/merge/' in request.path:
        back_url = '/merge/sessions'
    
    return render_template(
        'errors/404.html',
        message='The requested resource was not found.',
        back_url=back_url
    ), 404


@merge_bp.errorhandler(500)
def handle_500(error):
    """
    Handle 500 Internal Server Error.
    
    Logs the error details and returns a user-friendly error page.
    """
    from flask import render_template
    
    # Log the error
    logger.error(f"Internal server error: {error}", exc_info=True)
    
    # Rollback any pending database transactions
    try:
        db.session.rollback()
    except Exception as e:
        logger.error(f"Error rolling back transaction: {e}")
    
    return render_template(
        'errors/500.html',
        message='An internal server error occurred. Please try again later.'
    ), 500


@merge_bp.errorhandler(400)
def handle_400(error):
    """
    Handle 400 Bad Request errors.
    
    Returns a JSON error response for API endpoints or renders
    an error page for template routes.
    """
    from flask import request, render_template
    
    # Log the error
    logger.warning(f"Bad request: {error}")
    
    # Check if this is an API request (JSON expected)
    if request.path.startswith('/merge/api/') or request.is_json:
        return controller.json_error(
            str(error),
            status_code=400
        )
    
    # Otherwise render error page
    return render_template(
        'errors/400.html',
        message=str(error)
    ), 400


@merge_bp.errorhandler(Exception)
def handle_exception(error):
    """
    Handle all uncaught exceptions.
    
    Logs the error and returns appropriate response based on
    request type (JSON for API, HTML for templates).
    """
    from flask import request, render_template
    
    # Log the error
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    
    # Rollback any pending database transactions
    try:
        db.session.rollback()
    except Exception as e:
        logger.error(f"Error rolling back transaction: {e}")
    
    # Check if this is an API request
    if request.path.startswith('/merge/api/') or request.is_json:
        return controller.json_error(
            'An unexpected error occurred',
            status_code=500
        )
    
    # Otherwise render error page
    return render_template(
        'errors/500.html',
        message='An unexpected error occurred. Please try again later.'
    ), 500
