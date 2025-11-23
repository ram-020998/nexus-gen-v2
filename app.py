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
    
    # Initialize dependency container
    _initialize_dependency_container()

    # Add custom template filters for process history
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
                # First try to parse as JSON
                try:
                    parsed = json.loads(value)
                    return json.dumps(
                        parsed, indent=2, ensure_ascii=False
                    )
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to evaluate as
                    # Python dict string
                    try:
                        import ast
                        parsed = ast.literal_eval(value)
                        return json.dumps(
                            parsed, indent=2, ensure_ascii=False
                        )
                    except (ValueError, SyntaxError):
                        return value
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
    from controllers.convert_controller import convert_bp
    from controllers.chat_controller import chat_bp
    from controllers.process_controller import process_bp
    from controllers.analyzer_controller import analyzer_bp
    from controllers.merge_assistant_controller import (
        merge_assistant_bp
    )
    from controllers.settings_controller import settings_bp
    
    app.register_blueprint(breakdown_bp)
    app.register_blueprint(verify_bp)
    app.register_blueprint(create_bp)
    app.register_blueprint(convert_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(process_bp)
    app.register_blueprint(analyzer_bp)
    app.register_blueprint(merge_assistant_bp)
    app.register_blueprint(settings_bp)


def register_routes(app):
    """Register application routes"""

    @app.route('/')
    def dashboard():
        """Dashboard with 5 action cards and statistics"""
        # Get statistics from database
        stats = {
            'documents_processed': Request.query.filter_by(
                action_type='breakdown'
            ).count(),
            'designs_created': Request.query.filter_by(
                action_type='create'
            ).count(),
            'sql_converted': Request.query.filter_by(
                action_type='convert'
            ).count(),
            'accuracy_rate': 98  # Mock for now
        }
        return render_template('dashboard.html', stats=stats)


def _initialize_dependency_container():
    """
    Initialize and configure the dependency injection container.
    
    Registers all repositories and services with the container to enable
    dependency injection throughout the application. This ensures singleton
    patterns are preserved and dependencies are properly managed.
    """
    from core.dependency_container import DependencyContainer
    
    # Get container instance
    container = DependencyContainer.get_instance()
    
    # Register all repositories
    _register_repositories(container)
    
    # Register all services
    _register_services(container)


def _register_repositories(container):
    """
    Register all repository classes with the dependency container.

    Args:
        container: DependencyContainer instance
    """
    from repositories.request_repository import RequestRepository
    from repositories.comparison_repository import (
        ComparisonRepository
    )
    from repositories.chat_session_repository import (
        ChatSessionRepository
    )
    from repositories.merge_session_repository import (
        MergeSessionRepository
    )
    from repositories.package_repository import PackageRepository
    from repositories.change_repository import ChangeRepository
    from repositories.appian_object_repository import (
        AppianObjectRepository
    )
    
    # Register each repository
    container.register_repository(RequestRepository)
    container.register_repository(ComparisonRepository)
    container.register_repository(ChatSessionRepository)
    container.register_repository(MergeSessionRepository)
    container.register_repository(PackageRepository)
    container.register_repository(ChangeRepository)
    container.register_repository(AppianObjectRepository)


def _register_services(container):
    """
    Register all service classes with the dependency container.

    Args:
        container: DependencyContainer instance
    """
    # Request services
    from services.request.request_service import RequestService
    from services.request.file_service import FileService
    from services.request.document_service import DocumentService

    # Comparison services
    from services.comparison.comparison_service import (
        ComparisonService
    )
    from services.comparison.blueprint_analyzer import (
        BlueprintAnalyzer
    )
    from services.comparison.comparison_request_manager import (
        ComparisonRequestManager
    )
    
    # AI services
    from services.ai.bedrock_service import BedrockRAGService
    from services.ai.q_agent_service import QAgentService

    # Merge services
    from services.merge.package_service import PackageService
    from services.merge.change_service import ChangeService
    from services.merge.three_way_merge_service import (
        ThreeWayMergeService
    )
    
    # Register request services
    container.register_service(RequestService)
    container.register_service(FileService)
    container.register_service(DocumentService)

    # Register comparison services
    container.register_service(ComparisonService)
    container.register_service(BlueprintAnalyzer)
    container.register_service(ComparisonRequestManager)
    # Note: ComparisonEngine is not registered as it requires
    # version parameters and is instantiated per-comparison

    # Register AI services
    container.register_service(BedrockRAGService)
    container.register_service(QAgentService)

    # Register merge services
    container.register_service(PackageService)
    container.register_service(ChangeService)
    container.register_service(ThreeWayMergeService)


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5002)
