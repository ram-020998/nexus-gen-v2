"""
DocFlow - Document Intelligence Hub
Main Flask Application
"""
import json
from flask import Flask, render_template
from config import Config
from models import db, Request


def create_app():
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable sessions for chat
    app.config['SECRET_KEY'] = Config.SECRET_KEY

    # Initialize extensions
    db.init_app(app)
    
    # Add custom template filters
    @app.template_filter('from_json')
    def from_json_filter(value):
        """Parse JSON string in templates"""
        try:
            return json.loads(value) if value else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    @app.template_filter('format_json')
    def format_json_filter(value):
        """Format JSON string with proper indentation"""
        try:
            if isinstance(value, str):
                parsed = json.loads(value)
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            return json.dumps(value, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            return value

    # Initialize directories
    Config.init_directories()

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    register_blueprints(app)

    # Register routes
    register_routes(app)

    return app


def register_blueprints(app):
    """Register application blueprints"""
    from controllers.breakdown_controller import breakdown_bp
    from controllers.verify_controller import verify_bp
    from controllers.create_controller import create_bp
    from controllers.chat_controller import chat_bp
    from controllers.process_controller import process_bp
    app.register_blueprint(breakdown_bp)
    app.register_blueprint(verify_bp)
    app.register_blueprint(create_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(process_bp)


def register_routes(app):
    """Register application routes"""

    @app.route('/')
    def dashboard():
        """Dashboard with 4 action cards and statistics"""
        # Get statistics from database
        stats = {
            'documents_processed': Request.query.filter_by(action_type='breakdown').count(),
            'designs_created': Request.query.filter_by(action_type='create').count(),
            'accuracy_rate': 98  # Mock for now
        }
        return render_template('dashboard.html', stats=stats)


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5002)
