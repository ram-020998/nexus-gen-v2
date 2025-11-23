"""
Example Controller - Demonstrates BaseController usage

This is an example showing how to use BaseController in a real controller.
This file can be used as a reference when refactoring other controllers.
"""

from flask import Blueprint, request
from controllers.base_controller import BaseController
from services.request.request_service import RequestService

# Create blueprint
example_bp = Blueprint('example', __name__, url_prefix='/example')

# Create controller instance
controller = BaseController()


@example_bp.route('/')
def index():
    """Example index route"""
    # Access service through base controller
    request_service = controller.get_service(RequestService)
    recent_requests = request_service.get_recent_requests('example', 5)
    
    # Render template using base controller
    return controller.render(
        'example/index.html',
        requests=recent_requests
    )


@example_bp.route('/create', methods=['POST'])
def create_item():
    """Example create route with validation"""
    try:
        # Get JSON data
        data = request.get_json()
        
        # Validate required fields
        error = controller.validate_required_fields(
            data,
            ['name', 'description']
        )
        if error:
            return error
        
        # Access service
        request_service = controller.get_service(RequestService)
        
        # Create item
        item = request_service.create_request(
            'example',
            input_text=data['description']
        )
        
        # Return success response
        return controller.json_success(
            data={'id': item.id, 'name': data['name']},
            message='Item created successfully',
            status_code=201
        )
        
    except Exception as e:
        # Handle error
        return controller.handle_error(
            e,
            user_message='Failed to create item',
            return_json=True
        )


@example_bp.route('/upload', methods=['POST'])
def upload_file():
    """Example file upload route"""
    try:
        # Check if file exists
        if 'file' not in request.files:
            return controller.json_error(
                'No file provided',
                status_code=400
            )
        
        file = request.files['file']
        
        # Validate file
        if not file.filename:
            return controller.json_error(
                'No file selected',
                status_code=400
            )
        
        # Validate extension
        if not controller.validate_file_extension(
            file.filename,
            {'zip', 'pdf'}
        ):
            return controller.json_error(
                'Invalid file type. Only ZIP and PDF allowed',
                status_code=400
            )
        
        # Process file...
        controller.flash_success('File uploaded successfully')
        return controller.redirect_to('example.index')
        
    except Exception as e:
        return controller.handle_error(
            e,
            user_message='File upload failed',
            return_json=controller.is_ajax_request(request)
        )


@example_bp.route('/items')
def list_items():
    """Example list route with pagination"""
    try:
        # Get pagination params
        page, per_page = controller.get_pagination_params(request)
        
        # Access service
        request_service = controller.get_service(RequestService)
        
        # Get paginated items (example)
        items = request_service.get_recent_requests('example', per_page)
        
        # Return appropriate response based on request type
        if controller.is_ajax_request(request):
            return controller.json_success(
                data={
                    'items': [item.to_dict() for item in items],
                    'page': page,
                    'per_page': per_page
                }
            )
        else:
            return controller.render(
                'example/list.html',
                items=items,
                page=page,
                per_page=per_page
            )
            
    except Exception as e:
        return controller.handle_error(
            e,
            user_message='Failed to load items',
            return_json=controller.is_ajax_request(request)
        )
