"""
Merge Assistant Controller

Handles three-way merge workflow for Appian application upgrades.
"""
from flask import (
    Blueprint, request, render_template, jsonify,
    flash, redirect, url_for
)
from werkzeug.utils import secure_filename
from pathlib import Path

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

merge_assistant_bp = Blueprint('merge_assistant', __name__)
merge_service = ThreeWayMergeService()
validation_service = PackageValidationService()
export_service = ReportExportService()

ALLOWED_EXTENSIONS = {'zip'}
UPLOAD_FOLDER = Path('uploads/merge_assistant')


def allowed_file(filename):
    """Check if file has allowed extension"""
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)


@merge_assistant_bp.route('/merge-assistant')
def merge_assistant_home():
    """Display upload page for three packages"""
    return render_template('merge_assistant/upload.html')


@merge_assistant_bp.route('/merge-assistant/upload', methods=['POST'])
def upload_packages():
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
        flash(
            'Please upload all three packages: Base (A), '
            'Customized (B), and New Vendor (C)',
            'error'
        )
        return redirect(url_for('merge_assistant.merge_assistant_home'))

    base_file = request.files['base_package']
    customized_file = request.files['customized_package']
    new_vendor_file = request.files['new_vendor_package']

    # Validate filenames are present
    if not (base_file.filename and customized_file.filename and
            new_vendor_file.filename):
        flash('Please select all three package files', 'error')
        return redirect(url_for('merge_assistant.merge_assistant_home'))

    # Validate file extensions
    if not (allowed_file(base_file.filename) and
            allowed_file(customized_file.filename) and
            allowed_file(new_vendor_file.filename)):
        flash('All packages must be ZIP files', 'error')
        return redirect(url_for('merge_assistant.merge_assistant_home'))

    # Create upload directory if it doesn't exist
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

    # Save files temporarily
    base_path = UPLOAD_FOLDER / secure_filename(base_file.filename)
    customized_path = UPLOAD_FOLDER / secure_filename(
        customized_file.filename
    )
    new_vendor_path = UPLOAD_FOLDER / secure_filename(
        new_vendor_file.filename
    )

    try:
        # Save files
        base_file.save(base_path)
        customized_file.save(customized_path)
        new_vendor_file.save(new_vendor_path)

        # Validate packages
        try:
            validation_service.validate_all_packages(
                str(base_path),
                str(customized_path),
                str(new_vendor_path)
            )
        except PackageValidationError as e:
            # Generate user-friendly error message
            error_info = validation_service.generate_error_message(e)
            
            # Clean up files
            base_path.unlink(missing_ok=True)
            customized_path.unlink(missing_ok=True)
            new_vendor_path.unlink(missing_ok=True)
            
            # Return JSON response for AJAX request
            is_ajax = (request.is_json or
                       request.headers.get('X-Requested-With') ==
                       'XMLHttpRequest')
            if is_ajax:
                return jsonify({
                    'success': False,
                    'error': True,
                    'package': error_info.get('package', 'unknown'),
                    'message': error_info['message']
                }), 400
            
            # Fallback for non-AJAX requests
            flash(
                f"{error_info['title']}: {error_info['message']}",
                'error'
            )
            return redirect(url_for('merge_assistant.merge_assistant_home'))

        # Create merge session (uses normalized schema: Package, AppianObject, Change tables)
        session = merge_service.create_session(
            str(base_path),
            str(customized_path),
            str(new_vendor_path)
        )

        # Clean up files
        base_path.unlink(missing_ok=True)
        customized_path.unlink(missing_ok=True)
        new_vendor_path.unlink(missing_ok=True)

        # Return JSON response for AJAX request
        is_ajax = (request.is_json or
                   request.headers.get('X-Requested-With') ==
                   'XMLHttpRequest')
        if is_ajax:
            return jsonify({
                'success': True,
                'session_id': session.id,
                'reference_id': session.reference_id,
                'message': 'Analysis completed successfully!'
            })

        # Fallback for non-AJAX requests
        flash(
            f'Analysis completed successfully! '
            f'Session ID: {session.reference_id}',
            'success'
        )
        return redirect(
            url_for(
                'merge_assistant.view_summary',
                session_id=session.id
            )
        )

    except BlueprintGenerationError as e:
        # Clean up files
        base_path.unlink(missing_ok=True)
        customized_path.unlink(missing_ok=True)
        new_vendor_path.unlink(missing_ok=True)

        # Return JSON response for AJAX request
        is_ajax = (request.is_json or
                   request.headers.get('X-Requested-With') ==
                   'XMLHttpRequest')
        if is_ajax:
            msg = (f'Blueprint generation failed: {str(e)}. '
                   f'Please ensure all packages are valid Appian exports.')
            return jsonify({
                'success': False,
                'error': True,
                'message': msg
            }), 500

        # Fallback for non-AJAX requests
        flash(
            f'Blueprint generation failed: {str(e)}. '
            f'Please ensure all packages are valid Appian exports.',
            'error'
        )
        return redirect(url_for('merge_assistant.merge_assistant_home'))

    except Exception as e:
        # Clean up files
        base_path.unlink(missing_ok=True)
        customized_path.unlink(missing_ok=True)
        new_vendor_path.unlink(missing_ok=True)

        # Return JSON response for AJAX request
        is_ajax = (request.is_json or
                   request.headers.get('X-Requested-With') ==
                   'XMLHttpRequest')
        if is_ajax:
            return jsonify({
                'success': False,
                'error': True,
                'message': f'Merge session creation failed: {str(e)}'
            }), 500

        # Fallback for non-AJAX requests
        flash(
            f'Merge session creation failed: {str(e)}',
            'error'
        )
        return redirect(url_for('merge_assistant.merge_assistant_home'))


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/summary'
)
def view_summary(session_id):
    """Display merge summary with statistics (uses SQL aggregates on normalized schema)"""
    try:
        summary = merge_service.get_summary(session_id)
        session = merge_service.get_session(session_id)

        if not session:
            flash('Session not found', 'error')
            return redirect(url_for('merge_assistant.list_sessions'))

        return render_template(
            'merge_assistant/summary.html',
            summary=summary,
            session=session
        )

    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('merge_assistant.list_sessions'))
    except Exception as e:
        flash(f'Error loading summary: {str(e)}', 'error')
        return redirect(url_for('merge_assistant.list_sessions'))


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/workflow'
)
def start_workflow(session_id):
    """Start the guided merge workflow"""
    try:
        session = merge_service.get_session(session_id)

        if not session:
            flash('Session not found', 'error')
            return redirect(url_for('merge_assistant.list_sessions'))

        if session.status not in ['ready', 'in_progress']:
            flash(
                f'Session is not ready for workflow. '
                f'Status: {session.status}',
                'error'
            )
            return redirect(
                url_for(
                    'merge_assistant.view_summary',
                    session_id=session_id
                )
            )

        # Update session status to in_progress and reset to first change
        from models import db
        if session.status == 'ready':
            session.status = 'in_progress'
            session.current_change_index = 0
            db.session.commit()
            
            # Log workflow start
            logger = create_merge_session_logger(session.reference_id)
            logger.log_workflow_start()
        elif session.status == 'in_progress':
            # If already in progress, check if we need to restart from beginning
            # This handles the case where user clicks "Start Merge Workflow" again
            ordered_changes = merge_service.get_ordered_changes(session_id)
            if session.current_change_index >= len(ordered_changes):
                # Reset to beginning if we're past the end
                session.current_change_index = 0
                db.session.commit()

        # Redirect to current change (or first change if reset)
        return redirect(
            url_for(
                'merge_assistant.view_change',
                session_id=session_id,
                change_index=session.current_change_index
            )
        )

    except Exception as e:
        flash(f'Error starting workflow: {str(e)}', 'error')
        return redirect(url_for('merge_assistant.list_sessions'))


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/change/<int:change_index>'
)
def view_change(session_id, change_index):
    """Display specific change with three-way diff"""
    try:
        session = merge_service.get_session(session_id)

        if not session:
            flash('Session not found', 'error')
            return redirect(url_for('merge_assistant.list_sessions'))

        # Get ordered changes using JOIN queries (normalized schema)
        ordered_changes = merge_service.get_ordered_changes(session_id)
        
        # Debug logging
        print(f"🔍 DEBUG: Viewing change {change_index} of {len(ordered_changes)}")

        if change_index < 0 or change_index >= len(ordered_changes):
            print(f"❌ DEBUG: Invalid change index {change_index}, total: {len(ordered_changes)}")
            flash('Invalid change index', 'error')
            return redirect(
                url_for(
                    'merge_assistant.view_summary',
                    session_id=session_id
                )
            )

        # Update session's current change index for navigation state
        from models import db
        session.current_change_index = change_index
        db.session.commit()

        # Get the specific change (already includes review status from JOIN)
        change = ordered_changes[change_index]
        print(f"📋 DEBUG: Change name: {change.get('name')}, type: {change.get('type')}")
        print(f"📋 DEBUG: Review status: {change.get('review_status')}")

        # Calculate navigation info
        has_previous = change_index > 0
        has_next = change_index < len(ordered_changes) - 1
        is_last = change_index == len(ordered_changes) - 1

        print(f"✅ DEBUG: Rendering template for change {change_index}")
        return render_template(
            'merge_assistant/change_detail.html',
            session=session,
            change=change,
            change_index=change_index,
            total_changes=len(ordered_changes),
            has_previous=has_previous,
            has_next=has_next,
            is_last=is_last
        )

    except Exception as e:
        print(f"💥 DEBUG: Exception in view_change: {str(e)}")
        import traceback
        traceback.print_exc()
        flash(f'Error loading change: {str(e)}', 'error')
        return redirect(
            url_for(
                'merge_assistant.view_summary',
                session_id=session_id
            )
        )


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/change/'
    '<int:change_index>/review',
    methods=['POST']
)
def review_change(session_id, change_index):
    """
    Record user review action (updates ChangeReview table in normalized schema)

    Expected JSON:
    {
        'action': 'reviewed' | 'skipped',
        'notes': 'optional user notes'
    }
    """
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
        merge_service.update_progress(
            session_id,
            change_index,
            action,
            notes
        )

        # Get session to check if complete
        session = merge_service.get_session(session_id)
        ordered_changes = merge_service.get_ordered_changes(session_id)

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


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/report'
)
def generate_report(session_id):
    """Generate and display final merge report (uses JOIN queries on normalized schema)"""
    try:
        report = merge_service.generate_report(session_id)
        session = merge_service.get_session(session_id)

        if not session:
            flash('Session not found', 'error')
            return redirect(url_for('merge_assistant.list_sessions'))

        return render_template(
            'merge_assistant/report.html',
            report=report,
            session=session
        )

    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('merge_assistant.list_sessions'))
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('merge_assistant.list_sessions'))


@merge_assistant_bp.route('/merge-assistant/sessions')
def list_sessions():
    """List all merge sessions"""
    try:
        from models import MergeSession
        sessions = MergeSession.query.order_by(
            MergeSession.created_at.desc()
        ).all()

        return render_template(
            'merge_assistant/sessions.html',
            sessions=sessions
        )

    except Exception as e:
        flash(f'Error loading sessions: {str(e)}', 'error')
        return render_template('merge_assistant/sessions.html', sessions=[])


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/delete',
    methods=['POST']
)
def delete_session(session_id):
    """Delete a merge session and all related data (cascade deletes handle normalized tables)"""
    try:
        from models import db, MergeSession

        # Get the session
        session = MergeSession.query.get(session_id)
        if not session:
            return jsonify({
                'success': False,
                'message': 'Session not found'
            }), 404

        reference_id = session.reference_id

        # Delete the session (cascade deletes will handle all related records:
        # - Packages
        # - AppianObjects
        # - ProcessModelMetadata, ProcessModelNodes, ProcessModelFlows
        # - Changes
        # - MergeGuidance, MergeConflicts, MergeChanges
        # - ChangeReviews
        # - ObjectDependencies)
        db.session.delete(session)
        db.session.commit()

        # Vacuum database to reclaim space (run in background to avoid timeout)
        try:
            db.session.execute(db.text("VACUUM"))
        except Exception as vacuum_error:
            # Log but don't fail the deletion if vacuum fails
            print(f"Warning: VACUUM failed: {vacuum_error}")

        return jsonify({
            'success': True,
            'message': f'Session {reference_id} deleted successfully'
        })

    except Exception as e:
        from models import db
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting session: {str(e)}'
        }), 500


@merge_assistant_bp.route(
    '/merge-assistant/api/session/<int:session_id>/summary'
)
def api_session_summary(session_id):
    """API endpoint for session summary"""
    try:
        summary = merge_service.get_summary(session_id)
        return jsonify(summary)
    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@merge_assistant_bp.route(
    '/merge-assistant/api/session/<int:session_id>/changes'
)
def api_session_changes(session_id):
    """API endpoint for session changes (uses indexed SQL WHERE clauses on normalized schema)"""
    try:
        # Get filter parameters
        classification = request.args.get('classification')
        object_type = request.args.get('object_type')
        review_status = request.args.get('review_status')
        search_term = request.args.get('search')

        # Get filtered changes using SQL WHERE clauses on indexed columns
        changes = merge_service.filter_changes(
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


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/export/json'
)
def export_report_json(session_id):
    """Export report as JSON file"""
    try:
        # Generate report
        report = merge_service.generate_report(session_id)
        session = merge_service.get_session(session_id)

        if not session:
            flash('Session not found', 'error')
            return redirect(url_for('merge_assistant.list_sessions'))
        
        # Log export
        logger = create_merge_session_logger(session.reference_id)
        logger.log_report_export('json')

        # Export to JSON
        json_content = export_service.export_json(report)

        # Create response with JSON file
        from flask import Response
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
        flash(str(e), 'error')
        return redirect(url_for('merge_assistant.list_sessions'))
    except Exception as e:
        flash(f'Error exporting report: {str(e)}', 'error')
        return redirect(
            url_for(
                'merge_assistant.generate_report',
                session_id=session_id
            )
        )


@merge_assistant_bp.route(
    '/merge-assistant/session/<int:session_id>/export/pdf'
)
def export_report_pdf(session_id):
    """Export report as PDF (HTML for printing)"""
    try:
        # Generate report
        report = merge_service.generate_report(session_id)
        session = merge_service.get_session(session_id)

        if not session:
            flash('Session not found', 'error')
            return redirect(url_for('merge_assistant.list_sessions'))
        
        # Log export
        logger = create_merge_session_logger(session.reference_id)
        logger.log_report_export('pdf')

        # Generate PDF-ready HTML
        html_content = export_service.export_pdf_html(report)

        # Return HTML that can be printed to PDF
        from flask import Response
        response = Response(
            html_content,
            mimetype='text/html'
        )

        return response

    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('merge_assistant.list_sessions'))
    except Exception as e:
        flash(f'Error exporting report: {str(e)}', 'error')
        return redirect(
            url_for(
                'merge_assistant.generate_report',
                session_id=session_id
            )
        )
