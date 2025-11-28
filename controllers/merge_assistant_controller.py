"""
Merge Assistant Controller

Handles three-way merge workflow for Appian application upgrades.
"""
from flask import Blueprint, request, Response
from werkzeug.utils import secure_filename
from pathlib import Path

from controllers.base_controller import BaseController
from services.merge_assistant.three_way_merge_service import (
    ThreeWayMergeService
)
from services.merge_assistant.package_validation_service import (
    PackageValidationService,
    PackageValidationError
)
from services.merge_assistant.blueprint_generation_service import (
    BlueprintGenerationError
)
from services.merge_assistant.report_export_service import (
    ReportExportService
)
from services.merge_assistant.logger import create_merge_session_logger
from models import db, MergeSession

# Create blueprint
merge_assistant_bp = Blueprint('merge_assistant', __name__)

# Controller instance
controller = None

# Constants
ALLOWED_EXTENSIONS = {'zip'}
UPLOAD_FOLDER = Path('uploads/merge_assistant')


def get_controller() -> 'MergeAssistantController':
    """Get or create controller instance"""
    global controller
    if controller is None:
        controller = MergeAssistantController()
    return controller


class MergeAssistantController(BaseController):
    """
    Controller for merge assistant functionality
    
    Handles three-way merge workflow including package upload,
    session management, change review, and report generation.
    """
    
    def __init__(self):
        """Initialize merge assistant controller with services"""
        super().__init__()
        self.merge_service = ThreeWayMergeService()
        self.validation_service = PackageValidationService()
        self.export_service = ReportExportService()
    
    def validate_file_extension_zip(self, filename: str) -> bool:
        """
        Validate that file has .zip extension
        
        Args:
            filename: Name of file to validate
            
        Returns:
            True if valid ZIP file, False otherwise
        """
        return self.validate_file_extension(filename, ALLOWED_EXTENSIONS)
    
    def home(self):
        """Display upload page for three packages"""
        return self.render('merge_assistant/upload.html')
    
    def upload_packages_handler(self):
        """
        Handle three package uploads and create session
        
        Expected form data:
        - base_package: ZIP file (A)
        - customized_package: ZIP file (B)
        - new_vendor_package: ZIP file (C)
        """
        # Validate all three files are present
        if ('base_package' not in request.files or
                'customized_package' not in request.files or
                'new_vendor_package' not in request.files):
            self.flash_error(
                'Please upload all three packages: Base (A), '
                'Customized (B), and New Vendor (C)'
            )
            return self.redirect_to('merge_assistant.merge_assistant_home')
        
        base_file = request.files['base_package']
        customized_file = request.files['customized_package']
        new_vendor_file = request.files['new_vendor_package']
        
        # Validate filenames are present
        if not (base_file.filename and customized_file.filename and
                new_vendor_file.filename):
            self.flash_error('Please select all three package files')
            return self.redirect_to('merge_assistant.merge_assistant_home')
        
        # Validate file extensions
        if not (self.validate_file_extension_zip(base_file.filename) and
                self.validate_file_extension_zip(customized_file.filename) and
                self.validate_file_extension_zip(new_vendor_file.filename)):
            self.flash_error('All packages must be ZIP files')
            return self.redirect_to('merge_assistant.merge_assistant_home')
        
        # Create upload directory if it doesn't exist
        upload_dir = self.ensure_directory_exists(UPLOAD_FOLDER)
        
        # Save files temporarily
        base_path = upload_dir / secure_filename(base_file.filename)
        customized_path = upload_dir / secure_filename(customized_file.filename)
        new_vendor_path = upload_dir / secure_filename(new_vendor_file.filename)
        
        try:
            # Save files
            base_file.save(base_path)
            customized_file.save(customized_path)
            new_vendor_file.save(new_vendor_path)
            
            # Validate packages
            try:
                self.validation_service.validate_all_packages(
                    str(base_path),
                    str(customized_path),
                    str(new_vendor_path)
                )
            except PackageValidationError as e:
                # Generate user-friendly error message
                error_info = self.validation_service.generate_error_message(e)
                
                # Clean up files
                base_path.unlink(missing_ok=True)
                customized_path.unlink(missing_ok=True)
                new_vendor_path.unlink(missing_ok=True)
                
                # Return JSON response for AJAX request
                if self.is_ajax_request(request):
                    return self.json_error(
                        error_info['message'],
                        status_code=400,
                        package=error_info.get('package', 'unknown')
                    )
                
                # Fallback for non-AJAX requests
                self.flash_error(f"{error_info['title']}: {error_info['message']}")
                return self.redirect_to('merge_assistant.merge_assistant_home')
            
            # Create merge session
            session = self.merge_service.create_session(
                str(base_path),
                str(customized_path),
                str(new_vendor_path)
            )
            
            # Clean up files
            base_path.unlink(missing_ok=True)
            customized_path.unlink(missing_ok=True)
            new_vendor_path.unlink(missing_ok=True)
            
            # Return JSON response for AJAX request
            if self.is_ajax_request(request):
                return self.json_success(
                    data={
                        'session_id': session.id,
                        'reference_id': session.reference_id
                    },
                    message='Analysis completed successfully!'
                )
            
            # Fallback for non-AJAX requests
            self.flash_success(
                f'Analysis completed successfully! '
                f'Session ID: {session.reference_id}'
            )
            return self.redirect_to(
                'merge_assistant.view_summary',
                session_id=session.id
            )
        
        except BlueprintGenerationError as e:
            # Clean up files
            base_path.unlink(missing_ok=True)
            customized_path.unlink(missing_ok=True)
            new_vendor_path.unlink(missing_ok=True)
            
            # Return JSON response for AJAX request
            msg = (f'Blueprint generation failed: {str(e)}. '
                   f'Please ensure all packages are valid Appian exports.')
            
            if self.is_ajax_request(request):
                return self.json_error(msg, status_code=500)
            
            # Fallback for non-AJAX requests
            self.flash_error(msg)
            return self.redirect_to('merge_assistant.merge_assistant_home')
        
        except Exception as e:
            # Clean up files
            base_path.unlink(missing_ok=True)
            customized_path.unlink(missing_ok=True)
            new_vendor_path.unlink(missing_ok=True)
            
            # Return JSON response for AJAX request
            msg = f'Merge session creation failed: {str(e)}'
            
            if self.is_ajax_request(request):
                return self.json_error(msg, status_code=500)
            
            # Fallback for non-AJAX requests
            self.flash_error(msg)
            return self.redirect_to('merge_assistant.merge_assistant_home')
    
    def view_summary_handler(self, session_id: int):
        """Display merge summary with statistics"""
        try:
            summary = self.merge_service.get_summary(session_id)
            session = self.merge_service.get_session(session_id)
            
            if not session:
                self.flash_error('Session not found')
                return self.redirect_to('merge_assistant.list_sessions')
            
            return self.render(
                'merge_assistant/summary.html',
                summary=summary,
                session=session
            )
        
        except ValueError as e:
            self.flash_error(str(e))
            return self.redirect_to('merge_assistant.list_sessions')
        except Exception as e:
            self.flash_error(f'Error loading summary: {str(e)}')
            return self.redirect_to('merge_assistant.list_sessions')
    
    def start_workflow_handler(self, session_id: int):
        """Start the guided merge workflow"""
        try:
            session = self.merge_service.get_session(session_id)
            
            if not session:
                self.flash_error('Session not found')
                return self.redirect_to('merge_assistant.list_sessions')
            
            if session.status not in ['ready', 'in_progress']:
                self.flash_error(
                    f'Session is not ready for workflow. '
                    f'Status: {session.status}'
                )
                return self.redirect_to(
                    'merge_assistant.view_summary',
                    session_id=session_id
                )
            
            # Update session status to in_progress and reset to first change
            if session.status == 'ready':
                session.status = 'in_progress'
                session.current_change_index = 0
                db.session.commit()
                
                # Log workflow start
                logger = create_merge_session_logger(session.reference_id)
                logger.log_workflow_start()
            elif session.status == 'in_progress':
                # If already in progress, check if we need to restart from beginning
                # Use simple count query instead of loading all changes
                from models import Change
                workflow_count = Change.query.filter(
                    Change.session_id == session_id,
                    Change.classification != 'CUSTOMER_ONLY'
                ).count()
                if session.current_change_index >= workflow_count:
                    # Reset to beginning if we're past the end
                    session.current_change_index = 0
                    db.session.commit()
            
            # Redirect to current change (or first change if reset)
            return self.redirect_to(
                'merge_assistant.view_change',
                session_id=session_id,
                change_index=session.current_change_index
            )
        
        except Exception as e:
            self.flash_error(f'Error starting workflow: {str(e)}')
            return self.redirect_to('merge_assistant.list_sessions')
    
    def view_change_handler(self, session_id: int, change_index: int):
        """Display specific change with three-way diff"""
        try:
            session = self.merge_service.get_session(session_id)
            
            if not session:
                self.flash_error('Session not found')
                return self.redirect_to('merge_assistant.list_sessions')
            
            # Get total count first (fast query)
            from models import Change
            total_changes = Change.query.filter(
                Change.session_id == session_id,
                Change.classification != 'CUSTOMER_ONLY'
            ).count()
            
            # Debug logging
            print(f"🔍 DEBUG: Viewing change {change_index} of {total_changes}")
            
            if change_index < 0 or change_index >= total_changes:
                print(f"❌ DEBUG: Invalid change index {change_index}, total: {total_changes}")
                self.flash_error('Invalid change index')
                return self.redirect_to(
                    'merge_assistant.view_summary',
                    session_id=session_id
                )
            
            # Update session's current change index for navigation state
            session.current_change_index = change_index
            db.session.commit()
            
            # Get the specific change (paginated - just one change)
            ordered_changes = self.merge_service.get_ordered_changes(
                session_id, 
                page=change_index + 1,  # 1-indexed
                page_size=1
            )
            
            if not ordered_changes:
                self.flash_error('Change not found')
                return self.redirect_to(
                    'merge_assistant.view_summary',
                    session_id=session_id
                )
            
            change = ordered_changes[0]
            print(f"📋 DEBUG: Change name: {change.get('name')}, type: {change.get('type')}")
            print(f"📋 DEBUG: Review status: {change.get('review_status')}")
            
            # Calculate navigation info
            has_previous = change_index > 0
            has_next = change_index < total_changes - 1
            is_last = change_index == total_changes - 1
            
            print(f"✅ DEBUG: Rendering template for change {change_index}")
            return self.render(
                'merge_assistant/change_detail.html',
                session=session,
                change=change,
                change_index=change_index,
                total_changes=total_changes,
                has_previous=has_previous,
                has_next=has_next,
                is_last=is_last
            )
        
        except Exception as e:
            print(f"💥 DEBUG: Exception in view_change: {str(e)}")
            import traceback
            traceback.print_exc()
            self.flash_error(f'Error loading change: {str(e)}')
            return self.redirect_to(
                'merge_assistant.view_summary',
                session_id=session_id
            )
    
    def review_change_handler(self, session_id: int, change_index: int):
        """
        Record user review action
        
        Expected JSON:
        {
            'action': 'reviewed' | 'skipped',
            'notes': 'optional user notes'
        }
        """
        from flask import jsonify
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'No data provided'
                }), 400
            
            action = data.get('action')
            notes = data.get('notes', '')
            
            if action not in ['reviewed', 'skipped']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid action. Must be "reviewed" or "skipped"'
                }), 400
            
            # Update progress
            self.merge_service.update_progress(
                session_id,
                change_index,
                action,
                notes
            )
            
            # Get session to check if complete
            session = self.merge_service.get_session(session_id)
            ordered_changes = self.merge_service.get_ordered_changes(session_id)
            
            is_complete = (change_index == len(ordered_changes) - 1)
            
            return jsonify({
                'success': True,
                'action': action,
                'is_complete': is_complete,
                'next_index': change_index + 1 if not is_complete else None,
                'reviewed_count': session.reviewed_count,
                'skipped_count': session.skipped_count
            })
        
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error recording review: {str(e)}'
            }), 500
    
    def generate_report_handler(self, session_id: int):
        """Generate and display final merge report"""
        try:
            report = self.merge_service.generate_report(session_id)
            session = self.merge_service.get_session(session_id)
            
            if not session:
                self.flash_error('Session not found')
                return self.redirect_to('merge_assistant.list_sessions')
            
            return self.render(
                'merge_assistant/report.html',
                report=report,
                session=session
            )
        
        except ValueError as e:
            self.flash_error(str(e))
            return self.redirect_to('merge_assistant.list_sessions')
        except Exception as e:
            self.flash_error(f'Error generating report: {str(e)}')
            return self.redirect_to('merge_assistant.list_sessions')
    
    def list_sessions_handler(self):
        """List all merge sessions"""
        try:
            sessions = MergeSession.query.order_by(
                MergeSession.created_at.desc()
            ).all()
            
            return self.render(
                'merge_assistant/sessions.html',
                sessions=sessions
            )
        
        except Exception as e:
            self.flash_error(f'Error loading sessions: {str(e)}')
            return self.render('merge_assistant/sessions.html', sessions=[])
    
    def delete_session_handler(self, session_id: int):
        """Delete a merge session and all related data"""
        try:
            # Get the session
            session = MergeSession.query.get(session_id)
            if not session:
                return self.json_error('Session not found', status_code=404)
            
            reference_id = session.reference_id
            
            # Delete the session (cascade deletes will handle all related records)
            db.session.delete(session)
            db.session.commit()
            
            # Vacuum database to reclaim space (run in background to avoid timeout)
            try:
                db.session.execute(db.text("VACUUM"))
            except Exception as vacuum_error:
                # Log but don't fail the deletion if vacuum fails
                print(f"Warning: VACUUM failed: {vacuum_error}")
            
            return self.json_success(
                message=f'Session {reference_id} deleted successfully'
            )
        
        except Exception as e:
            db.session.rollback()
            return self.json_error(
                f'Error deleting session: {str(e)}',
                status_code=500
            )
    
    def api_session_summary_handler(self, session_id: int):
        """API endpoint for session summary"""
        from flask import jsonify
        try:
            summary = self.merge_service.get_summary(session_id)
            return jsonify(summary)
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def api_session_changes_handler(self, session_id: int):
        """API endpoint for session changes"""
        from flask import jsonify
        try:
            # Get filter parameters
            classification = request.args.get('classification')
            object_type = request.args.get('object_type')
            review_status = request.args.get('review_status')
            search_term = request.args.get('search')
            
            # Get filtered changes
            changes = self.merge_service.filter_changes(
                session_id,
                classification=classification,
                object_type=object_type,
                review_status=review_status,
                search_term=search_term
            )
            
            return jsonify({
                'changes': changes,
                'total': len(changes)
            })
        
        except ValueError as e:
            return jsonify({'error': str(e)}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def export_report_json_handler(self, session_id: int):
        """Export report as JSON file"""
        try:
            # Generate report
            report = self.merge_service.generate_report(session_id)
            session = self.merge_service.get_session(session_id)
            
            if not session:
                self.flash_error('Session not found')
                return self.redirect_to('merge_assistant.list_sessions')
            
            # Log export
            logger = create_merge_session_logger(session.reference_id)
            logger.log_report_export('json')
            
            # Export to JSON
            json_content = self.export_service.export_json(report)
            
            # Create response with JSON file
            response = Response(
                json_content,
                mimetype='application/json',
                headers={
                    'Content-Disposition': (
                        f'attachment; '
                        f'filename={session.reference_id}_report.json'
                    )
                }
            )
            
            return response
        
        except ValueError as e:
            self.flash_error(str(e))
            return self.redirect_to('merge_assistant.list_sessions')
        except Exception as e:
            self.flash_error(f'Error exporting report: {str(e)}')
            return self.redirect_to(
                'merge_assistant.generate_report',
                session_id=session_id
            )
    
    def export_report_pdf_handler(self, session_id: int):
        """Export report as PDF (HTML for printing)"""
        try:
            # Generate report
            report = self.merge_service.generate_report(session_id)
            session = self.merge_service.get_session(session_id)
            
            if not session:
                self.flash_error('Session not found')
                return self.redirect_to('merge_assistant.list_sessions')
            
            # Log export
            logger = create_merge_session_logger(session.reference_id)
            logger.log_report_export('pdf')
            
            # Generate PDF-ready HTML
            html_content = self.export_service.export_pdf_html(report)
            
            # Return HTML that can be printed to PDF
            response = Response(
                html_content,
                mimetype='text/html'
            )
            
            return response
        
        except ValueError as e:
            self.flash_error(str(e))
            return self.redirect_to('merge_assistant.list_sessions')
        except Exception as e:
            self.flash_error(f'Error exporting report: {str(e)}')
            return self.redirect_to(
                'merge_assistant.generate_report',
                session_id=session_id
            )
    
    def export_report_excel_handler(self, session_id: int):
        """
        Generate and download Excel report.
        
        This endpoint generates a comprehensive Excel report containing:
        - All changes with complexity analysis
        - Time estimates
        - Change descriptions
        - SAIL code changes
        
        The report is generated using ReportExportService and returned
        as a downloadable Excel file.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Excel file download response or error response
        """
        try:
            # Verify session exists
            session = self.merge_service.get_session(session_id)
            
            if not session:
                if self.is_ajax_request(request):
                    return self.json_error('Session not found', status_code=404)
                self.flash_error('Session not found')
                return self.redirect_to('merge_assistant.list_sessions')
            
            # Log report generation start
            logger = create_merge_session_logger(session.reference_id)
            logger.info(f"Starting Excel report generation for session {session_id}")
            
            # Generate report
            try:
                report_path = self.export_service.generate_report(
                    session_id,
                    self.merge_service
                )
            except ValueError as e:
                # Handle no changes or session not found
                error_msg = str(e)
                logger.error(f"Report generation failed: {error_msg}")
                
                if self.is_ajax_request(request):
                    return self.json_error(error_msg, status_code=400)
                
                self.flash_error(error_msg)
                return self.redirect_to(
                    'merge_assistant.view_summary',
                    session_id=session_id
                )
            
            # Log successful generation
            logger.info(f"Excel report generated successfully: {report_path}")
            logger.log_report_export('excel')
            
            # Read file and create response
            import os
            from flask import send_file
            
            if not os.path.exists(report_path):
                error_msg = 'Report file not found after generation'
                logger.error(error_msg)
                
                if self.is_ajax_request(request):
                    return self.json_error(error_msg, status_code=500)
                
                self.flash_error(error_msg)
                return self.redirect_to(
                    'merge_assistant.view_summary',
                    session_id=session_id
                )
            
            # Generate download filename
            filename = os.path.basename(report_path)
            
            # Return file for download
            return send_file(
                report_path,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        
        except Exception as e:
            # Log unexpected error
            error_msg = f'Error generating Excel report: {str(e)}'
            
            if session:
                logger = create_merge_session_logger(session.reference_id)
                logger.error(error_msg)
            
            print(f"❌ ERROR in export_report_excel_handler: {str(e)}")
            import traceback
            traceback.print_exc()
            
            if self.is_ajax_request(request):
                return self.json_error(error_msg, status_code=500)
            
            self.flash_error(error_msg)
            return self.redirect_to(
                'merge_assistant.view_summary',
                session_id=session_id
            )
    
    def get_objects_by_type_handler(self, session_id: int, object_type: str):
        """
        API endpoint for filtered object list.
        
        This endpoint supports the interactive breakdown section where users
        can click on object type cards to see detailed lists of objects.
        
        Query parameters:
        - classification: Optional classification filter
        - page: Page number (default: 1)
        - page_size: Items per page (default: 5)
        
        Args:
            session_id: Merge session ID
            object_type: Object type to filter by
            
        Returns:
            JSON response with objects and pagination info
        """
        from flask import jsonify
        
        try:
            # Get query parameters
            classification = request.args.get('classification')
            page = int(request.args.get('page', 1))
            page_size = int(request.args.get('page_size', 5))
            
            # Validate page and page_size
            if page < 1:
                return self.json_error(
                    'Page number must be positive',
                    status_code=400
                )
            
            if page_size < 1 or page_size > 100:
                return self.json_error(
                    'Page size must be between 1 and 100',
                    status_code=400
                )
            
            # Verify session exists
            session = self.merge_service.get_session(session_id)
            if not session:
                return self.json_error('Session not found', status_code=404)
            
            # Log request
            logger = create_merge_session_logger(session.reference_id)
            logger.info(
                f"Fetching objects by type: {object_type}, "
                f"classification: {classification}, page: {page}"
            )
            
            # Get objects by type
            try:
                result = self.merge_service.get_objects_by_type(
                    session_id=session_id,
                    object_type=object_type,
                    classification=classification,
                    page=page,
                    page_size=page_size
                )
            except ValueError as e:
                return self.json_error(str(e), status_code=404)
            
            # Log success
            logger.info(
                f"Retrieved {len(result['objects'])} objects "
                f"(page {result['page']} of {result['total_pages']})"
            )
            
            # Return JSON response
            return jsonify({
                'success': True,
                'data': result
            })
        
        except ValueError as e:
            # Handle invalid parameter types
            return self.json_error(
                f'Invalid parameter: {str(e)}',
                status_code=400
            )
        except Exception as e:
            # Log unexpected error
            error_msg = f'Error fetching objects: {str(e)}'
            
            if session:
                logger = create_merge_session_logger(session.reference_id)
                logger.error(error_msg)
            
            print(f"❌ ERROR in get_objects_by_type_handler: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return self.json_error(error_msg, status_code=500)


@merge_assistant_bp.route('/merge-assistant')
def merge_assistant_home():
    """Display upload page for three packages"""
    return get_controller().home()


@merge_assistant_bp.route('/merge-assistant/upload', methods=['POST'])
def upload_packages():
    """Handle three package uploads and create session"""
    return get_controller().upload_packages_handler()


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/summary'
)
def view_summary(session_id):
    """Display merge summary with statistics"""
    return get_controller().view_summary_handler(session_id)


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/workflow'
)
def start_workflow(session_id):
    """Start the guided merge workflow"""
    return get_controller().start_workflow_handler(session_id)


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/change/<int:change_index>'
)
def view_change(session_id, change_index):
    """Display specific change with three-way diff"""
    return get_controller().view_change_handler(session_id, change_index)


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/change/'
    '<int:change_index>/review',
    methods=['POST']
)
def review_change(session_id, change_index):
    """Record user review action"""
    return get_controller().review_change_handler(session_id, change_index)


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/report'
)
def generate_report(session_id):
    """Generate and display final merge report"""
    return get_controller().generate_report_handler(session_id)


@merge_assistant_bp.route('/merge-assistant/sessions')
def list_sessions():
    """List all merge sessions"""
    return get_controller().list_sessions_handler()


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/delete',
    methods=['POST']
)
def delete_session(session_id):
    """Delete a merge session and all related data"""
    return get_controller().delete_session_handler(session_id)


@merge_assistant_bp.route(
    '/merge-assistant/api/session/<int:session_id>/summary'
)
def api_session_summary(session_id):
    """API endpoint for session summary"""
    return get_controller().api_session_summary_handler(session_id)


@merge_assistant_bp.route(
    '/merge-assistant/api/session/<int:session_id>/changes'
)
def api_session_changes(session_id):
    """API endpoint for session changes"""
    return get_controller().api_session_changes_handler(session_id)


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/export/json'
)
def export_report_json(session_id):
    """Export report as JSON file"""
    return get_controller().export_report_json_handler(session_id)


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/export/pdf'
)
def export_report_pdf(session_id):
    """Export report as PDF (HTML for printing)"""
    return get_controller().export_report_pdf_handler(session_id)


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/export/excel-report'
)
def export_report_excel(session_id):
    """Generate and download Excel report"""
    return get_controller().export_report_excel_handler(session_id)


@merge_assistant_bp.route(
    '/merge-assistant/api/session/<int:session_id>/objects/<object_type>'
)
def get_objects_by_type(session_id, object_type):
    """API endpoint for filtered object list"""
    return get_controller().get_objects_by_type_handler(session_id, object_type)
