"""
Convert Controller - Handle SQL conversion from MariaDB to Oracle
"""
from flask import Blueprint, request
from controllers.base_controller import BaseController
from services.request.request_service import RequestService
from services.ai.q_agent_service import QAgentService
import json

convert_bp = Blueprint('convert', __name__, url_prefix='/convert')

# Create controller instance
controller = BaseController()


@convert_bp.route('/')
def index():
    """Convert SQL page"""
    # Access services through base controller
    request_service = controller.get_service(RequestService)
    
    recent_requests = request_service.get_recent_requests('convert', 5)
    return controller.render('convert/index.html', recent_requests=recent_requests)


@convert_bp.route('/process', methods=['POST'])
def convert_sql():
    """Convert MariaDB SQL to Oracle format"""
    try:
        # Access services through base controller
        request_service = controller.get_service(RequestService)
        q_agent_service = controller.get_service(QAgentService)
        
        data = request.get_json()
        maria_sql = data.get('maria_sql', '').strip()

        if not maria_sql:
            return controller.json_error('No SQL script provided', status_code=400)

        # Create request
        req = request_service.create_request('convert', input_text=maria_sql)

        # Process with Q agent
        oracle_sql = q_agent_service.process_conversion(req.id, maria_sql)

        # Update request with results
        request_service.update_request_status(req.id, 'completed', oracle_sql)

        return controller.json_success(
            data={
                'request_id': req.id,
                'oracle_sql': oracle_sql
            }
        )

    except Exception as e:
        return controller.handle_error(e, return_json=True)
