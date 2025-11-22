"""
Settings Controller - Handle application settings and configuration
"""
import os
import tempfile
from flask import Blueprint, render_template, jsonify, send_file, request
from services.settings_service import SettingsService

settings_bp = Blueprint('settings', __name__)
settings_service = SettingsService()


@settings_bp.route('/settings')
def settings_page():
    """Render the settings page"""
    return render_template('settings/index.html')


@settings_bp.route('/settings/cleanup', methods=['POST'])
def cleanup_database():
    """Execute database cleanup and return results"""
    try:
        result = settings_service.cleanup_database()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/settings/backup', methods=['POST'])
def backup_database():
    """Generate and download database backup"""
    try:
        # Generate backup file
        backup_path = settings_service.backup_database()

        # Extract filename from path
        import os
        filename = os.path.basename(backup_path)

        # Send file as download
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/sql'
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@settings_bp.route('/settings/restore', methods=['POST'])
def restore_database():
    """Restore database from uploaded SQL file"""
    temp_file_path = None

    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400

        file = request.files['file']

        # Check if file was selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Validate file extension
        if not file.filename.endswith('.sql'):
            return jsonify({
                'success': False,
                'error': 'Invalid file format. Only .sql files are accepted.'
            }), 400

        # Check file size (max 100MB)
        max_size = 100 * 1024 * 1024  # 100MB in bytes
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer
        
        if file_size > max_size:
            return jsonify({
                'success': False,
                'error': f'File too large ({file_size / (1024*1024):.1f}MB). Maximum size is 100MB.'
            }), 400

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
            return jsonify({
                'success': False,
                'error': f'Failed to save uploaded file: {str(e)}'
            }), 500

        # Execute restore
        result = settings_service.restore_database(temp_file_path)

        return jsonify(result), 200

    except ValueError as e:
        # Validation errors
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

    except FileNotFoundError as e:
        # File not found errors
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404

    except Exception as e:
        # Other errors
        error_msg = str(e)
        # Provide more specific error messages
        if 'sqlite3' in error_msg.lower() or 'SQLite tools' in error_msg:
            error_msg = 'SQLite tools not available on server. Please contact administrator.'
        
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception:
                # Log but don't fail if cleanup fails
                pass
