"""
DocFlow - Document Intelligence Hub
Main Flask Application
"""
import json
from flask import Flask, render_template
from config import Config
from models import db, Request
from core.logger import LoggerConfig


def create_app():
    """Application factory"""
    # Initialize logging first
    LoggerConfig.setup()
    
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable sessions for chat
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    
    # Apply connection pooling configuration (Requirement 11.5)
    if hasattr(Config, 'SQLALCHEMY_ENGINE_OPTIONS'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = Config.SQLALCHEMY_ENGINE_OPTIONS

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

    # Add helper function for object type icons
    @app.context_processor
    def utility_processor():
        def get_object_icon(object_type):
            """Get Font Awesome icon for object type"""
            icons = {
                'Interface': 'window-maximize',
                'Expression Rule': 'function',
                'Process Model': 'project-diagram',
                'Record Type': 'database',
                'CDT': 'cube',
                'Integration': 'plug',
                'Web API': 'globe',
                'Site': 'sitemap',
                'Group': 'users',
                'Constant': 'hashtag',
                'Connected System': 'server'
            }
            return icons.get(object_type, 'file')
        return dict(get_object_icon=get_object_icon)

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
    from controllers.settings_controller import settings_bp
    from controllers.merge_assistant_controller import merge_bp
    from controllers.debug_controller import debug_bp
    
    app.register_blueprint(breakdown_bp)
    app.register_blueprint(verify_bp)
    app.register_blueprint(create_bp)
    app.register_blueprint(convert_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(process_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(merge_bp)
    app.register_blueprint(debug_bp)


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
    from repositories.chat_session_repository import (
        ChatSessionRepository
    )
    from repositories.change_repository import ChangeRepository
    from repositories.object_lookup_repository import ObjectLookupRepository
    from repositories.package_object_mapping_repository import (
        PackageObjectMappingRepository
    )
    from repositories.delta_comparison_repository import (
        DeltaComparisonRepository
    )
    from repositories.customer_comparison_repository import (
        CustomerComparisonRepository
    )
    
    # Register each repository
    container.register_repository(RequestRepository)
    container.register_repository(ChatSessionRepository)
    container.register_repository(ChangeRepository)
    container.register_repository(ObjectLookupRepository)
    container.register_repository(PackageObjectMappingRepository)
    container.register_repository(DeltaComparisonRepository)
    container.register_repository(CustomerComparisonRepository)


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
    
    # AI services
    from services.ai.bedrock_service import BedrockRAGService
    from services.ai.q_agent_service import QAgentService
    
    # Three-way merge services
    from services.three_way_merge_orchestrator import (
        ThreeWayMergeOrchestrator
    )
    from services.package_extraction_service import PackageExtractionService
    from services.delta_comparison_service import DeltaComparisonService
    from services.customer_comparison_service import (
        CustomerComparisonService
    )
    from services.classification_service import ClassificationService
    from services.merge_guidance_service import MergeGuidanceService
    from services.change_navigation_service import ChangeNavigationService
    from services.comparison_persistence_service import (
        ComparisonPersistenceService
    )
    from services.comparison_retrieval_service import (
        ComparisonRetrievalService
    )
    
    # Register request services
    container.register_service(RequestService)
    container.register_service(FileService)
    container.register_service(DocumentService)

    # Register AI services
    container.register_service(BedrockRAGService)
    container.register_service(QAgentService)
    
    # Register three-way merge services
    container.register_service(ThreeWayMergeOrchestrator)
    container.register_service(PackageExtractionService)
    container.register_service(DeltaComparisonService)
    container.register_service(CustomerComparisonService)
    container.register_service(ClassificationService)
    container.register_service(MergeGuidanceService)
    container.register_service(ChangeNavigationService)
    container.register_service(ComparisonPersistenceService)
    container.register_service(ComparisonRetrievalService)


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5002)
