"""
Verify Controller - Handle design document verification
"""
from flask import Blueprint, render_template, request, jsonify
from services.request_service import RequestService
from services.q_agent_service import QAgentService
import json

verify_bp = Blueprint('verify', __name__, url_prefix='/verify')

request_service = RequestService()
q_agent_service = QAgentService()


@verify_bp.route('/')
def index():
    """Verify design document page"""
    recent_requests = request_service.get_recent_requests('verify', 5)
    return render_template('verify/index.html', recent_requests=recent_requests)


@verify_bp.route('/process', methods=['POST'])
def process_verification():
    """Process design document verification"""
    try:
        data = request.get_json()
        design_content = data.get('design_content', '').strip()

        if not design_content:
            return jsonify({'error': 'No design content provided'}), 400

        # Create request
        req = request_service.create_request('verify', input_text=design_content)

        # Process with Bedrock to get context
        query_text = f"Find existing design documents similar to: {design_content[:500]}..."
        bedrock_response = request_service.process_with_bedrock(req, query_text)

        # Process with Q agent (now returns result and tracker)
        verification_data, tracker = q_agent_service.process_verification(req.id, design_content, bedrock_response)

        # Update request with results and process metadata
        tracker_data = tracker.get_summary_data()
        request_service.update_request_with_tracking(req.id, 'completed', json.dumps(verification_data), tracker_data)

        return jsonify({
            'success': True,
            'request_id': req.id,
            'verification_data': verification_data,
            'process_info': {
                'reference_id': tracker_data['reference_id'],
                'total_time': tracker_data['total_time'],
                'confidence_badges': tracker.get_confidence_badges()
            }
        })

    except Exception as e:

        return jsonify({'error': str(e)}), 500


@verify_bp.route('/results/<int:request_id>')
def view_results(request_id):
    """View verification results"""
    req = request_service.get_request(request_id)
    if not req:
        return jsonify({'error': 'Request not found'}), 404

    verification_data = json.loads(req.final_output) if req.final_output else None

    return render_template('verify/results.html',
                           request=req,
                           verification_data=verification_data)
