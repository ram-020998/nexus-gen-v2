"""
Settings Controller - Handle application settings and configuration
"""
import os
import tempfile
from flask import Blueprint, send_file, request
from controllers.base_controller import BaseController
from services.settings_service import SettingsService

settings_bp = Blueprint('settings', __name__)

# Create controller instance
controller = BaseController()


@settings_bp.route('/settings')
def settings_page():
    """Render the settings page"""
    return controller.render('settings/index.html')


@settings_bp.route('/settings/cleanup', methods=['POST'])
def cleanup_database():
    """Execute database cleanup and return results"""
    try:
        # Access services through base controller
        settings_service = controller.get_service(SettingsService)
        
        result = settings_service.cleanup_database()
        return controller.json_success(data=result)
    except Exception as e:
        return controller.handle_error(e, return_json=True)


@settings_bp.route('/settings/backup', methods=['POST'])
def backup_database():
    """Generate and download database backup"""
    try:
        # Access services through base controller
        settings_service = controller.get_service(SettingsService)
        
        # Generate backup file
        backup_path = settings_service.backup_database()

        # Extract filename from path
        filename = os.path.basename(backup_path)

        # Send file as download
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/sql'
        )

    except Exception as e:
        return controller.handle_error(e, return_json=True)


@settings_bp.route('/settings/restore', methods=['POST'])
def restore_database():
    """Restore database from uploaded SQL file"""
    temp_file_path = None

    try:
        # Access services through base controller
        settings_service = controller.get_service(SettingsService)
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return controller.json_error('No file uploaded', status_code=400)

        file = request.files['file']

        # Check if file was selected
        if file.filename == '':
            return controller.json_error('No file selected', status_code=400)

        # Validate file extension
        if not controller.validate_file_extension(file.filename, {'sql'}):
            return controller.json_error(
                'Invalid file format. Only .sql files are accepted.',
                status_code=400
            )

        # Check file size (max 100MB)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if not controller.validate_file_size(file_size, max_size_mb=100):
            size_mb = file_size / (1024*1024)
            return controller.json_error(
                f'File too large ({size_mb:.1f}MB). Maximum size is 100MB.',
                status_code=400
            )

        # Save uploaded file temporarily
        try:
            with tempfile.NamedTemporaryFile(
                mode='wb',
                suffix='.sql',
                delete=False
            ) as temp_file:
                file.save(temp_file.name)
                temp_file_path = temp_file.name
        except IOError as e:
            return controller.json_error(
                f'Failed to save uploaded file: {str(e)}',
                status_code=500
            )

        # Execute restore
        result = settings_service.restore_database(temp_file_path)

        return controller.json_success(data=result)

    except ValueError as e:
        # Validation errors
        return controller.json_error(str(e), status_code=400)

    except FileNotFoundError as e:
        # File not found errors
        return controller.json_error(str(e), status_code=404)

    except Exception as e:
        # Other errors
        error_msg = str(e)
        # Provide more specific error messages
        if 'sqlite3' in error_msg.lower() or 'SQLite tools' in error_msg:
            error_msg = (
                'SQLite tools not available on server. '
                'Please contact administrator.'
            )
        
        return controller.json_error(error_msg, status_code=500)

    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                # Log but don't fail if cleanup fails
                pass
