"""
Create Controller - Handle design document creation
"""
from flask import Blueprint, request, send_file
from controllers.base_controller import BaseController
from services.request.request_service import RequestService
from services.ai.q_agent_service import QAgentService
from services.word_service import WordService
import json
from pathlib import Path

create_bp = Blueprint('create', __name__, url_prefix='/create')

# Create controller instance
controller = BaseController()


@create_bp.route('/')
def index():
    """Create design document page"""
    # Access services through base controller
    request_service = controller.get_service(RequestService)
    
    recent_requests = request_service.get_recent_requests('create', 5)
    return controller.render('create/index.html', recent_requests=recent_requests)


@create_bp.route('/generate', methods=['POST'])
def generate_design():
    """Generate design document from acceptance criteria"""
    try:
        # Access services through base controller
        request_service = controller.get_service(RequestService)
        q_agent_service = controller.get_service(QAgentService)
        
        data = request.get_json()
        acceptance_criteria = data.get('acceptance_criteria', '').strip()

        if not acceptance_criteria:
            return controller.json_error('No acceptance criteria provided', status_code=400)

        # Create request
        req = request_service.create_request('create', input_text=acceptance_criteria)

        # Process with Bedrock to get context - ask specifically for objects to modify
        query_text = (f"What objects need to be modified for: {acceptance_criteria}? "
                      "List the specific components, forms, rules, and services that require changes.")
        bedrock_response = request_service.process_with_bedrock(req, query_text)

        # Process with Q agent
        design_data = q_agent_service.process_creation(req.id, acceptance_criteria, bedrock_response)

        # Update request with results
        request_service.update_request_status(req.id, 'completed', json.dumps(design_data))

        return controller.json_success(
            data={
                'request_id': req.id,
                'design_data': design_data
            }
        )

    except Exception as e:
        return controller.handle_error(e, return_json=True)


@create_bp.route('/export/<int:request_id>')
def export_word(request_id):
    """Export design document to Word"""
    try:
        # Access services through base controller
        request_service = controller.get_service(RequestService)
        word_service = controller.get_service(WordService)
        
        req = request_service.get_request(request_id)
        if not req or not req.final_output:
            return controller.json_error('Request not found or no data available', status_code=404)

        design_data = json.loads(req.final_output)

        # Generate Word document
        word_path = word_service.create_design_document(
            request_id,
            design_data
        )

        # Update request with export path
        req.export_path = word_path
        request_service.update_request_status(request_id, 'completed')

        # Send file
        return send_file(
            word_path,
            as_attachment=True,
            download_name=Path(word_path).name,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        return controller.handle_error(e, return_json=True)


@create_bp.route('/results/<int:request_id>')
def view_results(request_id):
    """View creation results"""
    # Access services through base controller
    request_service = controller.get_service(RequestService)
    
    req = request_service.get_request(request_id)
    if not req:
        return controller.json_error('Request not found', status_code=404)

    design_data = json.loads(req.final_output) if req.final_output else None

    return controller.render('create/results.html',
                             request=req,
                             design_data=design_data)
