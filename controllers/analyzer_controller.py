"""
Analyzer Controller - Handle Appian application comparison requests
"""
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import json

from controllers.base_controller import BaseController
from services.comparison.comparison_service import ComparisonService
from services.appian_analyzer.logger import get_logger

# Create blueprint
analyzer_bp = Blueprint('analyzer', __name__)

# Create controller instance
controller = None


def get_controller() -> 'AnalyzerController':
    """Get or create controller singleton."""
    global controller
    if controller is None:
        controller = AnalyzerController()
    return controller


class AnalyzerController(BaseController):
    """
    Controller for Appian application comparison operations.

    Handles:
    - Displaying comparison requests
    - Processing new comparisons
    - Viewing comparison results
    - Viewing object details

    Inherits common functionality from BaseController including:
    - Service access via dependency injection
    - Response formatting (JSON, HTML, redirects)
    - Error handling and flash messaging
    - File validation
    """

    ALLOWED_EXTENSIONS = {'zip'}

    def __init__(self):
        """Initialize analyzer controller with required services."""
        super().__init__()
        self.comparison_service = self.get_service(ComparisonService)
        self.logger = get_logger()

    def analyzer_home(self):
        """
        Display analyzer home page with comparison requests.

        Returns:
            Rendered HTML template with list of comparison requests
        """
        requests = self.comparison_service.get_all_requests()
        return self.render('analyzer/home.html', requests=requests)

    def compare_versions(self):
        """
        Process comparison of two application versions.

        Handles file upload, validation, comparison processing,
        and cleanup. Provides user feedback via flash messages.

        Returns:
            Redirect to analyzer home page
        """
        self.logger.info("Comparison request received via web interface")

        # Validate files are present
        if 'old_file' not in request.files or \
           'new_file' not in request.files:
            self.logger.warning("Missing files in upload request")
            self.flash_error('Please select both files for comparison')
            return self.redirect_to('analyzer.analyzer_home')

        old_file = request.files['old_file']
        new_file = request.files['new_file']

        self.logger.info(
            f"Files received: {old_file.filename} vs {new_file.filename}"
        )

        # Validate file extensions
        old_valid = self.validate_file_extension(
            old_file.filename, self.ALLOWED_EXTENSIONS
        )
        new_valid = self.validate_file_extension(
            new_file.filename, self.ALLOWED_EXTENSIONS
        )

        if not (old_file.filename and new_file.filename and
                old_valid and new_valid):
            self.logger.warning(
                f"File validation failed: {old_file.filename}, "
                f"{new_file.filename}"
            )
            self.flash_error('Please select valid ZIP files')
            return self.redirect_to('analyzer.analyzer_home')

        old_path = None
        new_path = None

        try:
            # Ensure upload directory exists
            upload_dir = self.ensure_directory_exists('uploads')

            # Save files temporarily
            old_path = upload_dir / secure_filename(old_file.filename)
            new_path = upload_dir / secure_filename(new_file.filename)

            old_file.save(old_path)
            new_file.save(new_path)

            self.logger.debug(
                f"Files saved: {old_path} "
                f"({old_path.stat().st_size} bytes), "
                f"{new_path} ({new_path.stat().st_size} bytes)"
            )

            # Process comparison (this creates its own request logger)
            comparison_request = self.comparison_service.process_comparison(
                str(old_path),
                str(new_path)
            )
            self.logger.info(
                f"Comparison completed: {comparison_request.reference_id}"
            )

            # Clean up files
            old_path.unlink(missing_ok=True)
            new_path.unlink(missing_ok=True)
            self.logger.debug("Temporary files cleaned up")

            self.flash_success(
                f'Comparison completed successfully! '
                f'Request ID: {comparison_request.reference_id}'
            )

        except Exception as e:
            self.logger.error(
                f"Comparison request failed: {str(e)}", exc_info=True
            )
            self.flash_error(f'Comparison failed: {str(e)}')

            # Clean up files on error
            if old_path and old_path.exists():
                old_path.unlink(missing_ok=True)
            if new_path and new_path.exists():
                new_path.unlink(missing_ok=True)

        return self.redirect_to('analyzer.analyzer_home')

    def view_request(self, request_id: int):
        """
        Display detailed comparison request.

        Args:
            request_id: ID of the comparison request

        Returns:
            Rendered HTML template with request details or redirect
            if not found
        """
        comparison_request = self.comparison_service.get_request_details(
            request_id
        )
        if not comparison_request:
            self.flash_error('Request not found')
            return self.redirect_to('analyzer.analyzer_home')

        return self.render(
            'analyzer/request_details.html',
            comparison_request=comparison_request
        )

    def view_object_details(self, request_id: int, object_uuid: str):
        """
        Display detailed object comparison.

        Args:
            request_id: ID of the comparison request
            object_uuid: UUID of the object to view

        Returns:
            Rendered HTML template with object details or redirect
            if not found
        """
        comparison_request = self.comparison_service.get_request_details(
            request_id
        )
        if not comparison_request or \
           comparison_request.status != 'completed':
            self.flash_error('Request not found or not completed')
            return self.redirect_to('analyzer.analyzer_home')

        # Find the specific object in the comparison results
        comparison_data = json.loads(comparison_request.comparison_results)
        object_data = None

        for category, changes in \
                comparison_data['changes_by_category'].items():
            for detail in changes['details']:
                if detail['uuid'] == object_uuid:
                    object_data = detail
                    object_data['category'] = category
                    break
            if object_data:
                break

        if not object_data:
            self.flash_error('Object not found')
            return self.redirect_to(
                'analyzer.view_request',
                request_id=request_id
            )

        return self.render(
            'analyzer/object_details.html',
            object_data=object_data,
            request_id=request_id
        )

    def api_requests(self):
        """
        API endpoint for requests list.

        Returns:
            JSON response with list of all comparison requests
        """
        requests = self.comparison_service.get_all_requests()
        return jsonify([req.to_dict() for req in requests])


# ============================================================================
# Route Definitions
# ============================================================================

@analyzer_bp.route('/analyzer')
def analyzer_home():
    """Analyzer home page with comparison requests"""
    return get_controller().analyzer_home()


@analyzer_bp.route('/analyzer/compare', methods=['POST'])
def compare_versions():
    """Compare two application versions"""
    return get_controller().compare_versions()


@analyzer_bp.route('/analyzer/request/<int:request_id>')
def view_request(request_id):
    """View detailed comparison request"""
    return get_controller().view_request(request_id)


@analyzer_bp.route('/analyzer/object/<int:request_id>/<object_uuid>')
def view_object_details(request_id, object_uuid):
    """View detailed object comparison in separate page"""
    return get_controller().view_object_details(request_id, object_uuid)


@analyzer_bp.route('/analyzer/api/requests')
def api_requests():
    """API endpoint for requests list"""
    return get_controller().api_requests()
