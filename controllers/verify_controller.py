"""
Verify Controller - Handle design document verification
"""
from flask import Blueprint, request
from controllers.base_controller import BaseController
from services.request.request_service import RequestService
from services.ai.q_agent_service import QAgentService
import json

verify_bp = Blueprint('verify', __name__, url_prefix='/verify')

# Create controller instance
controller = BaseController()


@verify_bp.route('/')
def index():
    """Verify design document page"""
    # Access services through base controller
    request_service = controller.get_service(RequestService)
    
    recent_requests = request_service.get_recent_requests('verify', 5)
    return controller.render('verify/index.html', recent_requests=recent_requests)


@verify_bp.route('/process', methods=['POST'])
def process_verification():
    """Process design document verification"""
    try:
        # Access services through base controller
        request_service = controller.get_service(RequestService)
        q_agent_service = controller.get_service(QAgentService)
        
        data = request.get_json()
        design_content = data.get('design_content', '').strip()

        if not design_content:
            return controller.json_error('No design content provided', status_code=400)

        # Create request
        req = request_service.create_request('verify', input_text=design_content)

        # Process with Bedrock to get context
        query_text = f"Find existing design documents similar to: {design_content[:500]}..."
        bedrock_response = request_service.process_with_bedrock(req, query_text)

        # Process with Q agent
        verification_data = q_agent_service.process_verification(req.id, design_content, bedrock_response)

        # Update request with results
        request_service.update_request_status(req.id, 'completed', json.dumps(verification_data))

        return controller.json_success(
            data={
                'request_id': req.id,
                'verification_data': verification_data
            }
        )

    except Exception as e:
        return controller.handle_error(e, return_json=True)


@verify_bp.route('/results/<int:request_id>')
def view_results(request_id):
    """View verification results"""
    # Access services through base controller
    request_service = controller.get_service(RequestService)
    
    req = request_service.get_request(request_id)
    if not req:
        return controller.json_error('Request not found', status_code=404)

    verification_data = json.loads(req.final_output) if req.final_output else None

    return controller.render('verify/results.html',
                             request=req,
                             verification_data=verification_data)
