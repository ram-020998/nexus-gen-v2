"""
Integration tests for report export endpoints

Tests the controller endpoints for JSON and PDF export.
"""
import json
import pytest
from flask import Flask
from models import db, MergeSession
from controllers.merge_assistant_controller import merge_assistant_bp


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(merge_assistant_bp)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def sample_session(app):
    """Create a sample merge session with data"""
    with app.app_context():
        session = MergeSession(
            reference_id='MRG_TEST_001',
            base_package_name='Test App v1.0',
            customized_package_name='Test App v1.0 Custom',
            new_vendor_package_name='Test App v2.0',
            status='completed',
            base_blueprint=json.dumps({'object_lookup': {}}),
            customized_blueprint=json.dumps({'object_lookup': {}}),
            new_vendor_blueprint=json.dumps({'object_lookup': {}}),
            vendor_changes=json.dumps({}),
            customer_changes=json.dumps({}),
            classification_results=json.dumps({
                'NO_CONFLICT': [],
                'CONFLICT': [],
                'CUSTOMER_ONLY': [],
                'REMOVED_BUT_CUSTOMIZED': []
            }),
            ordered_changes=json.dumps([]),
            total_changes=0,
            reviewed_count=0,
            skipped_count=0,
            total_time=120
        )
        db.session.add(session)
        db.session.commit()

        return session.id


def test_export_json_endpoint(client, sample_session):
    """Test JSON export endpoint returns valid JSON"""
    response = client.get(
        f'/merge-assistant/session/{sample_session}/export/json'
    )

    assert response.status_code == 200
    assert response.mimetype == 'application/json'

    # Verify Content-Disposition header
    assert 'Content-Disposition' in response.headers
    assert 'attachment' in response.headers['Content-Disposition']
    assert 'MRG_TEST_001_report.json' in (
        response.headers['Content-Disposition']
    )

    # Verify JSON is valid
    data = json.loads(response.data)
    assert 'metadata' in data
    assert 'session' in data
    assert 'statistics' in data


def test_export_pdf_endpoint(client, sample_session):
    """Test PDF export endpoint returns HTML"""
    response = client.get(
        f'/merge-assistant/session/{sample_session}/export/pdf'
    )

    assert response.status_code == 200
    assert response.mimetype == 'text/html'

    # Verify HTML content
    html = response.data.decode('utf-8')
    assert '<!DOCTYPE html>' in html
    assert 'MRG_TEST_001' in html
    assert 'Three-Way Merge Report' in html


def test_export_json_nonexistent_session(client):
    """Test JSON export with nonexistent session returns error"""
    response = client.get(
        '/merge-assistant/session/99999/export/json'
    )

    # Should redirect with error
    assert response.status_code == 302


def test_export_pdf_nonexistent_session(client):
    """Test PDF export with nonexistent session returns error"""
    response = client.get(
        '/merge-assistant/session/99999/export/pdf'
    )

    # Should redirect with error
    assert response.status_code == 302
