"""
Analyzer Controller - Handle Appian application comparison requests
"""
from flask import Blueprint, request, render_template, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from pathlib import Path
import json

from services.comparison_service import ComparisonService

analyzer_bp = Blueprint('analyzer', __name__)
comparison_service = ComparisonService()

ALLOWED_EXTENSIONS = {'zip'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@analyzer_bp.route('/analyzer')
def analyzer_home():
    """Analyzer home page with comparison requests"""
    requests = comparison_service.get_all_requests()
    return render_template('analyzer/home.html', requests=requests)

@analyzer_bp.route('/analyzer/compare', methods=['POST'])
def compare_versions():
    """Compare two application versions"""
    print("DEBUG: Compare request received")
    
    if 'old_file' not in request.files or 'new_file' not in request.files:
        print("DEBUG: Missing files in request")
        flash('Please select both files for comparison', 'error')
        return redirect(url_for('analyzer.analyzer_home'))
    
    old_file = request.files['old_file']
    new_file = request.files['new_file']
    
    print(f"DEBUG: Old file: {old_file.filename}")
    print(f"DEBUG: New file: {new_file.filename}")
    
    if not (old_file.filename and new_file.filename and 
            allowed_file(old_file.filename) and allowed_file(new_file.filename)):
        print("DEBUG: File validation failed")
        flash('Please select valid ZIP files', 'error')
        return redirect(url_for('analyzer.analyzer_home'))
    
    try:
        # Save files temporarily
        old_path = Path('uploads') / secure_filename(old_file.filename)
        new_path = Path('uploads') / secure_filename(new_file.filename)
        
        old_path.parent.mkdir(exist_ok=True)
        old_file.save(old_path)
        new_file.save(new_path)
        print(f"DEBUG: Files saved to {old_path} and {new_path}")
        print(f"DEBUG: Old file size: {old_path.stat().st_size} bytes")
        print(f"DEBUG: New file size: {new_path.stat().st_size} bytes")
        
        # Process comparison
        comparison_request = comparison_service.process_comparison(str(old_path), str(new_path))
        print(f"DEBUG: Comparison completed with request ID: {comparison_request.id}")
        
        # Clean up files
        old_path.unlink(missing_ok=True)
        new_path.unlink(missing_ok=True)
        print("DEBUG: Files cleaned up")
        
        flash(f'Comparison completed successfully! Request ID: {comparison_request.reference_id}', 'success')
        
    except Exception as e:
        print(f"DEBUG: Comparison failed: {str(e)}")
        flash(f'Comparison failed: {str(e)}', 'error')
        
        # Clean up files on error
        if 'old_path' in locals():
            old_path.unlink(missing_ok=True)
        if 'new_path' in locals():
            new_path.unlink(missing_ok=True)
    
    return redirect(url_for('analyzer.analyzer_home'))

@analyzer_bp.route('/analyzer/request/<int:request_id>')
def view_request(request_id):
    """View detailed comparison request"""
    comparison_request = comparison_service.get_request_details(request_id)
    if not comparison_request:
        flash('Request not found', 'error')
        return redirect(url_for('analyzer.analyzer_home'))
    
    return render_template('analyzer/request_details.html', comparison_request=comparison_request)

@analyzer_bp.route('/analyzer/object/<int:request_id>/<object_uuid>')
def view_object_details(request_id, object_uuid):
    """View detailed object comparison in separate page"""
    comparison_request = comparison_service.get_request_details(request_id)
    if not comparison_request or comparison_request.status != 'completed':
        flash('Request not found or not completed', 'error')
        return redirect(url_for('analyzer.analyzer_home'))
    
    # Find the specific object in the comparison results
    comparison_data = json.loads(comparison_request.comparison_results)
    object_data = None
    
    for category, changes in comparison_data['changes_by_category'].items():
        for detail in changes['details']:
            if detail['uuid'] == object_uuid:
                object_data = detail
                object_data['category'] = category
                break
        if object_data:
            break
    
    if not object_data:
        flash('Object not found', 'error')
        return redirect(url_for('analyzer.view_request', request_id=request_id))
    
    return render_template('analyzer/object_details.html', object_data=object_data, request_id=request_id)

@analyzer_bp.route('/analyzer/api/requests')
def api_requests():
    """API endpoint for requests list"""
    requests = comparison_service.get_all_requests()
    return jsonify([req.to_dict() for req in requests])
