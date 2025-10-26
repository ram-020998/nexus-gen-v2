"""
Breakdown Controller - Handle spec document breakdown
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from services.file_service import FileService
from services.request_service import RequestService
from services.q_agent_service import QAgentService
from services.document_service import DocumentService
from services.excel_service import ExcelService
import json
from pathlib import Path

breakdown_bp = Blueprint('breakdown', __name__, url_prefix='/breakdown')

file_service = FileService()
request_service = RequestService()
q_agent_service = QAgentService()
document_service = DocumentService()
excel_service = ExcelService()


@breakdown_bp.route('/')
def index():
    """Upload page with recent uploads"""
    recent_uploads = file_service.get_recent_uploads()
    recent_requests = request_service.get_recent_requests('breakdown', 5)

    return render_template('breakdown/upload.html',
                           recent_uploads=recent_uploads,
                           recent_requests=recent_requests)


@breakdown_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Create request first to get ID
        req = request_service.create_request('breakdown', file.filename)

        # Save file
        file_path = file_service.save_upload(file, req.id)

        # Extract document content
        file_content = document_service.extract_content(file_path)

        # Process with Bedrock to get context
        query_text = f"Find similar spec breakdowns for: {file_content[:500]}..."
        bedrock_response = request_service.process_with_bedrock(req, query_text)

        # Process with Q agent
        breakdown_data = q_agent_service.process_breakdown(req.id, file_content, bedrock_response)

        # Update request with results
        request_service.update_request_status(req.id, 'completed', json.dumps(breakdown_data))

        return jsonify({
            'success': True,
            'request_id': req.id,
            'breakdown_data': breakdown_data
        })

    except Exception as e:

        return jsonify({'error': str(e)}), 500


@breakdown_bp.route('/results/<int:request_id>')
def view_results(request_id):
    """View breakdown results"""
    req = request_service.get_request(request_id)
    if not req:
        flash('Request not found', 'error')
        return redirect(url_for('breakdown.index'))

    breakdown_data = json.loads(req.final_output) if req.final_output else None

    return render_template('breakdown/results.html',
                           request=req,
                           breakdown_data=breakdown_data)


@breakdown_bp.route('/export/<int:request_id>')
def export_excel(request_id):
    """Export breakdown to Excel"""
    try:
        req = request_service.get_request(request_id)
        if not req or not req.final_output:
            return jsonify({'error': 'Request not found or no data available'}), 404

        breakdown_data = json.loads(req.final_output)

        # Generate Excel file
        excel_path = excel_service.create_breakdown_excel(
            request_id,
            breakdown_data,
            req.filename
        )

        # Update request with export path
        req.export_path = excel_path
        request_service.update_request_status(request_id, 'completed')

        # Send file
        return send_file(
            excel_path,
            as_attachment=True,
            download_name=Path(excel_path).name,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:

        return jsonify({'error': str(e)}), 500
