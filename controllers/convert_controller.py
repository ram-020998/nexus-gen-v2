"""
Convert Controller - Handle SQL conversion from MariaDB to Oracle
"""
from flask import Blueprint, render_template, request, jsonify
from services.request_service import RequestService
from services.q_agent_service import QAgentService
import json

convert_bp = Blueprint('convert', __name__, url_prefix='/convert')

request_service = RequestService()
q_agent_service = QAgentService()


@convert_bp.route('/')
def index():
    """Convert SQL page"""
    recent_requests = request_service.get_recent_requests('convert', 5)
    return render_template('convert/index.html', recent_requests=recent_requests)


@convert_bp.route('/process', methods=['POST'])
def convert_sql():
    """Convert MariaDB SQL to Oracle format"""
    try:
        data = request.get_json()
        maria_sql = data.get('maria_sql', '').strip()

        if not maria_sql:
            return jsonify({'error': 'No SQL script provided'}), 400

        # Create request
        req = request_service.create_request('convert', input_text=maria_sql)

        # Process with Q agent
        oracle_sql = q_agent_service.process_conversion(req.id, maria_sql)

        # Update request with results
        request_service.update_request_status(req.id, 'completed', oracle_sql)

        return jsonify({
            'success': True,
            'request_id': req.id,
            'oracle_sql': oracle_sql
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
