"""
Tests for dependency container initialization in app.py

Verifies that all services and repositories are properly registered
and that singleton patterns are preserved.
"""
import pytest
from app import create_app, _initialize_dependency_container
from core.dependency_container import DependencyContainer


class TestDependencyContainerInitialization:
    """Test dependency container initialization"""

    def setup_method(self):
        """Reset container before each test"""
        DependencyContainer.reset_instance()

    def test_container_is_initialized_on_app_creation(self):
        """Test that container is initialized when app is created"""
        # Reset container
        DependencyContainer.reset_instance()

        # Create app (should initialize container)
        app = create_app()

        # Get container instance
        container = DependencyContainer.get_instance()

        # Verify container exists
        assert container is not None

    def test_all_repositories_are_registered(self):
        """Test that all repository classes are registered"""
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

        # Initialize container
        _initialize_dependency_container()
        container = DependencyContainer.get_instance()

        # Verify each repository can be retrieved
        assert container.get_repository(RequestRepository) is not None
        assert container.get_repository(
            ComparisonRepository
        ) is not None
        assert container.get_repository(
            ChatSessionRepository
        ) is not None
        assert container.get_repository(
            MergeSessionRepository
        ) is not None
        assert container.get_repository(PackageRepository) is not None
        assert container.get_repository(ChangeRepository) is not None
        assert container.get_repository(
            AppianObjectRepository
        ) is not None

    def test_all_services_are_registered(self):
        """Test that all service classes are registered"""
        from services.request.request_service import RequestService
        from services.request.file_service import FileService
        from services.request.document_service import DocumentService
        from services.comparison.comparison_service import (
            ComparisonService
        )
        from services.comparison.blueprint_analyzer import (
            BlueprintAnalyzer
        )

        from services.comparison.comparison_request_manager import (
            ComparisonRequestManager
        )
        from services.ai.bedrock_service import BedrockRAGService
        from services.ai.q_agent_service import QAgentService
        from services.merge.package_service import PackageService
        from services.merge.change_service import ChangeService
        from services.merge.three_way_merge_service import (
            ThreeWayMergeService
        )

        # Initialize container
        _initialize_dependency_container()
        container = DependencyContainer.get_instance()

        # Verify each service can be retrieved
        assert container.get_service(RequestService) is not None
        assert container.get_service(FileService) is not None
        assert container.get_service(DocumentService) is not None
        assert container.get_service(ComparisonService) is not None
        assert container.get_service(BlueprintAnalyzer) is not None
        assert container.get_service(
            ComparisonRequestManager
        ) is not None
        assert container.get_service(BedrockRAGService) is not None
        assert container.get_service(QAgentService) is not None
        assert container.get_service(PackageService) is not None
        assert container.get_service(ChangeService) is not None
        assert container.get_service(ThreeWayMergeService) is not None
        # Note: ComparisonEngine not registered as it requires
        # version parameters

    def test_singleton_pattern_is_preserved(self):
        """Test that singleton pattern is preserved for services"""
        from services.request.request_service import RequestService

        # Initialize container
        _initialize_dependency_container()
        container = DependencyContainer.get_instance()

        # Get service twice
        service1 = container.get_service(RequestService)
        service2 = container.get_service(RequestService)

        # Verify same instance is returned
        assert service1 is service2

    def test_repository_singleton_pattern_is_preserved(self):
        """Test that singleton pattern is preserved for repositories"""
        from repositories.request_repository import RequestRepository

        # Initialize container
        _initialize_dependency_container()
        container = DependencyContainer.get_instance()

        # Get repository twice
        repo1 = container.get_repository(RequestRepository)
        repo2 = container.get_repository(RequestRepository)

        # Verify same instance is returned
        assert repo1 is repo2

    def test_services_can_access_repositories_via_container(self):
        """Test that services can access repositories through container"""
        from services.request.request_service import RequestService
        from repositories.request_repository import RequestRepository

        # Initialize container
        _initialize_dependency_container()
        container = DependencyContainer.get_instance()

        # Get service
        service = container.get_service(RequestService)

        # Verify service has access to repository
        assert hasattr(service, 'request_repo')
        assert service.request_repo is not None

        # Verify it's the same instance as from container
        repo_from_container = container.get_repository(
            RequestRepository
        )
        assert service.request_repo is repo_from_container

    def test_container_initialization_is_idempotent(self):
        """Test that initializing container multiple times is safe"""
        # Initialize container multiple times
        _initialize_dependency_container()
        _initialize_dependency_container()
        _initialize_dependency_container()

        # Get container
        container = DependencyContainer.get_instance()

        # Verify it still works
        from services.request.request_service import RequestService
        service = container.get_service(RequestService)
        assert service is not None

    def test_container_persists_across_app_context(self):
        """Test that container persists across app context"""
        from services.request.request_service import RequestService

        # Create app
        app = create_app()

        # Get service in app context
        with app.app_context():
            container = DependencyContainer.get_instance()
            service1 = container.get_service(RequestService)

        # Get service outside app context
        container = DependencyContainer.get_instance()
        service2 = container.get_service(RequestService)

        # Verify same instance
        assert service1 is service2
