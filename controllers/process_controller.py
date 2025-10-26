"""
Process Controller - Handle process history and details
"""
import json
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, Response
from services.request_service import RequestService

process_bp = Blueprint('process', __name__, url_prefix='/process')
request_service = RequestService()


@process_bp.route('/history')
def history():
    """View process history with filters"""
    # Get filter parameters
    action_type = request.args.get('type', '')
    status = request.args.get('status', '')
    search = request.args.get('search', '')
    
    # Get all requests
    all_requests = request_service.get_recent_requests(limit=100)
    
    # Apply filters
    filtered_requests = all_requests
    
    if action_type:
        filtered_requests = [r for r in filtered_requests if r.action_type == action_type]
    
    if status:
        filtered_requests = [r for r in filtered_requests if r.status == status]
    
    if search:
        filtered_requests = [r for r in filtered_requests 
                           if search.lower() in (r.reference_id or '').lower() 
                           or search.lower() in (r.filename or '').lower()]
    
    return render_template('process/history.html',
                         requests=filtered_requests,
                         current_type=action_type,
                         current_status=status,
                         current_search=search)


@process_bp.route('/details/<int:request_id>')
def details(request_id):
    """View detailed process information"""
    req = request_service.get_request(request_id)
    if not req:
        flash('Request not found', 'error')
        return redirect(url_for('process.history'))

    # Parse timeline data if available
    timeline_data = None
    if req.step_durations:
        try:
            timeline_data = json.loads(req.step_durations)
        except json.JSONDecodeError:
            timeline_data = None

    return render_template('process_details.html',
                         request=req,
                         timeline_data=timeline_data)


@process_bp.route('/download/<artifact_type>/<int:request_id>')
def download_artifact(artifact_type, request_id):
    """Download process artifacts"""
    req = request_service.get_request(request_id)
    if not req:
        return jsonify({'error': 'Request not found'}), 404
    
    if artifact_type == 'bedrock':
        content = req.rag_response or '{}'
        filename = f'bedrock_response_{request_id}.json'
    elif artifact_type == 'agent':
        content = req.raw_agent_output or '{}'
        filename = f'agent_output_{request_id}.txt'
    else:
        return jsonify({'error': 'Invalid artifact type'}), 400
    
    return Response(
        content,
        mimetype='application/json' if artifact_type == 'bedrock' else 'text/plain',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


@process_bp.route('/reprocess/<int:request_id>', methods=['POST'])
def reprocess_request(request_id):
    """Reprocess a request with the same input"""
    req = request_service.get_request(request_id)
    if not req:
        return jsonify({'error': 'Request not found'}), 404
    
    try:
        # Create a new request with the same input
        if req.action_type == 'breakdown':
            # For breakdown, we need the original file - this would need file handling
            return jsonify({'error': 'Breakdown reprocessing not supported yet'}), 400
        elif req.action_type == 'verify':
            # For verify, use the input_text
            new_req = request_service.create_request(
                action_type='verify',
                input_text=req.input_text
            )
        elif req.action_type == 'create':
            # For create, use the input_text
            new_req = request_service.create_request(
                action_type='create',
                input_text=req.input_text
            )
        else:
            return jsonify({'error': 'Unknown action type'}), 400
        
        return jsonify({
            'success': True,
            'new_request_id': new_req.id,
            'message': 'Reprocessing started'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
