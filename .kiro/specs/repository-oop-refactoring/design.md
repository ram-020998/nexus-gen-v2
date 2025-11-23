# Design Document: Repository OOP Refactoring

## Overview

This design document outlines the architectural approach for refactoring the NexusGen repository to follow clean, modular, object-oriented design principles. The refactoring will transform the current mixed-pattern codebase into a well-structured application following SOLID principles while maintaining 100% backward compatibility and functional equivalence.

### Current State Analysis

**Codebase Statistics:**
- Total Python LOC: 23,350 (excluding tests/venv)
- Controllers: 8 blueprints
- Services: 13+ service modules
- Models: 20+ SQLAlchemy models
- Large files: 3 files > 1000 lines, 8 files > 500 lines

**Identified Issues:**
1. Mixed patterns: Some services are classes, others are module-level functions
2. Database operations scattered across service layer
3. Direct Config class access throughout codebase
4. Large monolithic files (process_model_enhancement.py: 3,476 lines)
5. Tight coupling between controllers and database models
6. No consistent dependency injection pattern
7. Limited use of inheritance and composition

### Refactoring Goals

1. **Consistency**: Uniform OOP patterns across all modules
2. **Separation of Concerns**: Clear boundaries between layers
3. **Testability**: Improved dependency injection for easier testing
4. **Maintainability**: Smaller, focused classes and modules
5. **Extensibility**: Base classes and interfaces for future growth
6. **Zero Functional Changes**: Preserve all existing behavior

## Architecture

### Proposed Layer Structure

```
nexus-gen-v2/
├── app.py                          # Application factory (minimal changes)
├── config.py                       # Configuration (refactored to class-based)
├── models.py                       # Database models (unchanged)
│
├── core/                           # NEW: Core infrastructure
│   ├── __init__.py
│   ├── base_service.py            # Base service class
│   ├── base_repository.py         # Base repository class
│   ├── dependency_container.py    # DI container
│   └── exceptions.py              # Custom exceptions
│
├── repositories/                   # NEW: Data access layer
│   ├── __init__.py
│   ├── request_repository.py
│   ├── comparison_repository.py
│   ├── merge_session_repository.py
│   └── ...                        # One repository per model
│
├── services/                       # REFACTORED: Business logic
│   ├── __init__.py
│   ├── request/                   # Request-related services
│   │   ├── __init__.py
│   │   ├── request_service.py
│   │   ├── file_service.py
│   │   └── document_service.py
│   ├── comparison/                # Comparison services
│   │   ├── __init__.py
│   │   ├── comparison_service.py
│   │   └── analyzer_service.py
│   ├── merge/                     # Merge assistant services
│   │   ├── __init__.py
│   │   ├── merge_service.py
│   │   ├── package_service.py
│   │   └── ...
│   ├── ai/                        # AI/ML services
│   │   ├── __init__.py
│   │   ├── bedrock_service.py
│   │   └── q_agent_service.py
│   └── appian_analyzer/           # Keep existing structure
│       └── ...                    # (already well-organized)
│
├── controllers/                    # REFACTORED: HTTP layer
│   ├── __init__.py
│   ├── base_controller.py         # NEW: Base controller
│   ├── breakdown_controller.py    # Refactored
│   ├── analyzer_controller.py     # Refactored
│   └── ...                        # Other controllers
│
├── templates/                      # Unchanged
├── static/                         # Unchanged
└── tests/                          # Unchanged (should all pass)
```


### Layer Responsibilities

**Core Layer** (`core/`):
- Base classes for services and repositories
- Dependency injection container
- Custom exception hierarchy
- Shared utilities and interfaces

**Repository Layer** (`repositories/`):
- Database access abstraction
- CRUD operations for each model
- Query encapsulation
- Transaction management

**Service Layer** (`services/`):
- Business logic implementation
- Service orchestration
- External API integration
- Data transformation

**Controller Layer** (`controllers/`):
- HTTP request/response handling
- Route definitions
- Request validation
- Template rendering

## Components and Interfaces

### Base Service Class

```python
# core/base_service.py
from abc import ABC
from typing import Optional
from core.dependency_container import DependencyContainer

class BaseService(ABC):
    """Base class for all services providing common functionality"""
    
    def __init__(self, container: Optional[DependencyContainer] = None):
        """
        Initialize service with dependency container
        
        Args:
            container: Dependency injection container
        """
        self._container = container or DependencyContainer.get_instance()
        self._initialize_dependencies()
    
    def _initialize_dependencies(self):
        """Override to inject specific dependencies"""
        pass
    
    def _get_repository(self, repository_class):
        """Get repository instance from container"""
        return self._container.get_repository(repository_class)
    
    def _get_service(self, service_class):
        """Get service instance from container"""
        return self._container.get_service(service_class)
```

### Base Repository Class

```python
# core/base_repository.py
from abc import ABC
from typing import Generic, TypeVar, List, Optional
from models import db

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Base repository providing CRUD operations"""
    
    def __init__(self, model_class: type):
        """
        Initialize repository with model class
        
        Args:
            model_class: SQLAlchemy model class
        """
        self.model_class = model_class
        self.db = db
    
    def create(self, **kwargs) -> T:
        """Create new entity"""
        entity = self.model_class(**kwargs)
        self.db.session.add(entity)
        self.db.session.commit()
        return entity
    
    def get_by_id(self, entity_id: int) -> Optional[T]:
        """Get entity by ID"""
        return self.model_class.query.get(entity_id)
    
    def get_all(self) -> List[T]:
        """Get all entities"""
        return self.model_class.query.all()
    
    def update(self, entity: T) -> T:
        """Update entity"""
        self.db.session.commit()
        return entity
    
    def delete(self, entity: T):
        """Delete entity"""
        self.db.session.delete(entity)
        self.db.session.commit()
    
    def filter_by(self, **kwargs) -> List[T]:
        """Filter entities by criteria"""
        return self.model_class.query.filter_by(**kwargs).all()
```

### Dependency Container

```python
# core/dependency_container.py
from typing import Dict, Type, Any

class DependencyContainer:
    """Simple dependency injection container"""
    
    _instance = None
    
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._repositories: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
    
    @classmethod
    def get_instance(cls) -> 'DependencyContainer':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register_service(self, service_class: Type, instance: Any = None):
        """Register service class or instance"""
        if instance:
            self._services[service_class] = instance
        else:
            self._services[service_class] = service_class
    
    def register_repository(self, repo_class: Type, instance: Any = None):
        """Register repository class or instance"""
        if instance:
            self._repositories[repo_class] = instance
        else:
            self._repositories[repo_class] = repo_class
    
    def get_service(self, service_class: Type) -> Any:
        """Get service instance"""
        if service_class not in self._singletons:
            service = self._services.get(service_class, service_class)
            if isinstance(service, type):
                service = service(self)
            self._singletons[service_class] = service
        return self._singletons[service_class]
    
    def get_repository(self, repo_class: Type) -> Any:
        """Get repository instance"""
        if repo_class not in self._singletons:
            repo = self._repositories.get(repo_class, repo_class)
            if isinstance(repo, type):
                repo = repo()
            self._singletons[repo_class] = repo
        return self._singletons[repo_class]
```


### Example Repository Implementation

```python
# repositories/request_repository.py
from typing import List, Optional
from core.base_repository import BaseRepository
from models import Request

class RequestRepository(BaseRepository[Request]):
    """Repository for Request model"""
    
    def __init__(self):
        super().__init__(Request)
    
    def get_recent_by_action(self, action_type: str, limit: int = 10) -> List[Request]:
        """Get recent requests by action type"""
        return (self.model_class.query
                .filter_by(action_type=action_type)
                .order_by(self.model_class.created_at.desc())
                .limit(limit)
                .all())
    
    def get_by_reference_id(self, reference_id: str) -> Optional[Request]:
        """Get request by reference ID"""
        return self.model_class.query.filter_by(reference_id=reference_id).first()
    
    def update_status(self, request_id: int, status: str, output_data: str = None) -> Request:
        """Update request status"""
        request = self.get_by_id(request_id)
        if request:
            request.status = status
            if output_data:
                request.final_output = output_data
            self.update(request)
        return request
```

### Example Service Refactoring

**Before (module-level functions):**
```python
# services/request_service.py (current)
def create_request(action_type, filename=None):
    request = Request(action_type=action_type, filename=filename)
    db.session.add(request)
    db.session.commit()
    return request
```

**After (class-based with DI):**
```python
# services/request/request_service.py (refactored)
from core.base_service import BaseService
from repositories.request_repository import RequestRepository
from typing import Optional

class RequestService(BaseService):
    """Service for managing requests"""
    
    def _initialize_dependencies(self):
        """Inject dependencies"""
        self.request_repo = self._get_repository(RequestRepository)
    
    def create_request(self, action_type: str, filename: str = None, 
                      input_text: str = None) -> Request:
        """
        Create a new request
        
        Args:
            action_type: Type of action (breakdown, verify, create)
            filename: Optional filename
            input_text: Optional input text
            
        Returns:
            Created Request instance
        """
        return self.request_repo.create(
            action_type=action_type,
            filename=filename,
            input_text=input_text,
            status='processing'
        )
    
    def get_request(self, request_id: int) -> Optional[Request]:
        """Get request by ID"""
        return self.request_repo.get_by_id(request_id)
    
    def get_recent_requests(self, action_type: str = None, 
                           limit: int = 10) -> List[Request]:
        """Get recent requests"""
        if action_type:
            return self.request_repo.get_recent_by_action(action_type, limit)
        return self.request_repo.get_all()[:limit]
```

### Backward Compatibility Layer

```python
# services/request_service.py (compatibility wrapper)
"""
Request Service - Backward compatibility wrapper

This module maintains the original module-level function interface
while delegating to the new class-based implementation.
"""
from services.request.request_service import RequestService

# Create singleton instance
_service_instance = None

def _get_service() -> RequestService:
    """Get service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = RequestService()
    return _service_instance

# Expose original function interface
def create_request(action_type: str, filename: str = None, input_text: str = None):
    """Create a new request (compatibility wrapper)"""
    return _get_service().create_request(action_type, filename, input_text)

def get_request(request_id: int):
    """Get request by ID (compatibility wrapper)"""
    return _get_service().get_request(request_id)

def get_recent_requests(action_type: str = None, limit: int = 10):
    """Get recent requests (compatibility wrapper)"""
    return _get_service().get_recent_requests(action_type, limit)

# Export the service class for new code
__all__ = ['RequestService', 'create_request', 'get_request', 'get_recent_requests']
```


## Data Models

The existing SQLAlchemy models in `models.py` will remain unchanged. The refactoring focuses on how these models are accessed and manipulated, not their structure.

**Models to be wrapped by repositories:**
- Request
- ComparisonRequest
- ChatSession
- MergeSession
- Package
- AppianObject
- ProcessModelMetadata
- ProcessModelNode
- ProcessModelFlow
- Change
- MergeGuidance
- ChangeReview
- ObjectDependency

Each model will have a corresponding repository class providing type-safe CRUD operations and domain-specific queries.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: File Size Analysis Completeness
*For any* Python file in the repository, if the file exceeds 500 lines, then the analysis tool should identify and report it.
**Validates: Requirements 1.1**

### Property 2: Service Class Extraction
*For any* service module after refactoring, the module should contain exactly one primary service class (excluding compatibility wrappers and helper classes).
**Validates: Requirements 2.1**

### Property 3: No Module-Level Business Logic
*For any* service module after refactoring, all business logic functions should be instance methods of a service class, not module-level functions (except compatibility wrappers).
**Validates: Requirements 2.2**

### Property 4: Function Signature Preservation
*For any* public function or method that existed before refactoring, the same function signature should be accessible after refactoring (either directly or through compatibility wrapper).
**Validates: Requirements 2.4**

### Property 5: Business Logic Equivalence
*For any* service operation with identical inputs, the output and side effects should be identical before and after refactoring.
**Validates: Requirements 2.5**

### Property 6: Flask Route Preservation
*For any* Flask route that existed before refactoring, the same route path and HTTP methods should be registered after refactoring.
**Validates: Requirements 3.1**

### Property 7: Response Format Preservation
*For any* controller endpoint with identical request inputs, the response format (status code, headers, body structure) should be identical before and after refactoring.
**Validates: Requirements 3.3**

### Property 8: Error Response Preservation
*For any* error condition that triggers an exception, the same HTTP error response (status code and error message format) should be returned before and after refactoring.
**Validates: Requirements 3.4**

### Property 9: Template Rendering Preservation
*For any* controller action that renders a template, the same template should be rendered with equivalent context data before and after refactoring.
**Validates: Requirements 3.5**

### Property 10: Database Query Isolation
*For any* service class after refactoring, the service should not directly access `db.session` but should delegate all database operations to repository classes.
**Validates: Requirements 4.1**

### Property 11: Repository CRUD Completeness
*For any* repository class, it should provide create, read (by ID and by criteria), update, and delete operations for its model.
**Validates: Requirements 4.2**

### Property 12: Query Result Equivalence
*For any* database query with identical parameters, the query results should be identical before and after refactoring.
**Validates: Requirements 4.3**

### Property 13: Transaction Behavior Preservation
*For any* operation that involves database transactions, the commit/rollback behavior should be identical before and after refactoring.
**Validates: Requirements 4.4**

### Property 14: Relationship Navigation Preservation
*For any* SQLAlchemy model relationship, navigation through the relationship should work identically before and after refactoring.
**Validates: Requirements 4.5**

### Property 15: Configuration Value Preservation
*For any* configuration value accessed in the application, the value should be identical before and after refactoring.
**Validates: Requirements 5.1**

### Property 16: Environment Variable Handling
*For any* environment variable used for configuration, the variable should be read and applied identically before and after refactoring.
**Validates: Requirements 5.2**

### Property 17: Configuration Access Pattern Preservation
*For any* code that accesses configuration (e.g., `Config.SETTING`), the access pattern should continue to work after refactoring.
**Validates: Requirements 5.4**

### Property 18: Constructor Dependency Injection
*For any* service class after refactoring, all service dependencies should be injected through the constructor or initialization method.
**Validates: Requirements 6.1**

### Property 19: Service Interaction Preservation
*For any* interaction between services with identical inputs, the interaction should produce identical results before and after refactoring.
**Validates: Requirements 6.2**

### Property 20: Singleton Pattern Preservation
*For any* service that was implemented as a singleton before refactoring, the same instance should be returned on multiple accesses after refactoring.
**Validates: Requirements 6.4**

### Property 21: Large File Decomposition
*For any* file exceeding 1000 lines before refactoring, the file should be split into multiple smaller files after refactoring, with total line count preserved.
**Validates: Requirements 7.2**

### Property 22: Import Preservation
*For any* import statement that worked before refactoring, the same import should work after refactoring (either directly or through compatibility imports).
**Validates: Requirements 7.3**

### Property 23: Class Relationship Preservation
*For any* class inheritance or composition relationship before refactoring, the same relationship should exist after refactoring.
**Validates: Requirements 7.4**

### Property 24: Method Signature Preservation
*For any* public method signature before refactoring, the same signature should be accessible after refactoring.
**Validates: Requirements 8.3**

### Property 25: Polymorphic Behavior Preservation
*For any* polymorphic method call before refactoring, the same polymorphic dispatch should occur after refactoring.
**Validates: Requirements 8.4**

### Property 26: Exception Handling Preservation
*For any* try-except block before refactoring, equivalent exception handling should exist after refactoring.
**Validates: Requirements 9.1**

### Property 27: Error Message Preservation
*For any* error condition, the error message format should be identical before and after refactoring.
**Validates: Requirements 9.2**

### Property 28: Exception Type Preservation
*For any* error condition that raises an exception, the same exception type should be raised before and after refactoring.
**Validates: Requirements 9.3**

### Property 29: Test Execution Preservation
*For any* existing test in the test suite, the test should execute successfully after refactoring without modification.
**Validates: Requirements 10.1**

### Property 30: Test Assertion Validity
*For any* test assertion before refactoring, the same assertion should pass after refactoring.
**Validates: Requirements 10.3**

### Property 31: Public Class Documentation
*For any* public class after refactoring, the class should have a docstring explaining its purpose.
**Validates: Requirements 11.1**

### Property 32: Public Method Documentation
*For any* public method after refactoring, the method should have a docstring with parameter and return value documentation.
**Validates: Requirements 11.2**

### Property 33: Type Hint Completeness
*For any* function or method after refactoring, all parameters and return values should have type hints.
**Validates: Requirements 11.3**

### Property 34: Backward Compatible Imports
*For any* module that existed before refactoring, importing from the original module path should work after refactoring.
**Validates: Requirements 12.1**

### Property 35: Public API Surface Preservation
*For any* public function, class, or constant accessible before refactoring, the same element should be accessible after refactoring.
**Validates: Requirements 12.2**

### Property 36: Entry Point Preservation
*For any* application entry point (app.py, CLI commands) before refactoring, the same entry point should work identically after refactoring.
**Validates: Requirements 12.4**


## Error Handling

Error handling will be preserved exactly as it exists in the current codebase. The refactoring will:

1. **Maintain all try-except blocks**: Every exception handler will be preserved in the refactored code
2. **Preserve error messages**: All error message strings will remain unchanged
3. **Keep exception types**: The same exception types will be raised in the same conditions
4. **Maintain error logging**: All logging statements will be preserved
5. **Preserve error recovery**: Any error recovery logic will remain unchanged

### Error Handling Strategy

**Controller Layer:**
- HTTP error responses (400, 404, 500) remain unchanged
- Error templates rendered identically
- Flash messages preserved

**Service Layer:**
- Business logic exceptions propagated identically
- Validation errors raised with same messages
- External API errors handled identically

**Repository Layer:**
- Database errors (IntegrityError, etc.) propagated unchanged
- Transaction rollback behavior preserved
- Connection errors handled identically

### Custom Exception Hierarchy (Optional Enhancement)

While preserving all existing error handling, we may introduce custom exceptions for better organization:

```python
# core/exceptions.py
class NexusGenException(Exception):
    """Base exception for NexusGen application"""
    pass

class ServiceException(NexusGenException):
    """Base exception for service layer"""
    pass

class RepositoryException(NexusGenException):
    """Base exception for repository layer"""
    pass

class ValidationException(ServiceException):
    """Validation error in service layer"""
    pass
```

These custom exceptions will only be used in new code paths and will not replace existing exception handling.

## Testing Strategy

### Unit Testing Approach

The refactoring will be validated through comprehensive unit testing:

**Test Categories:**
1. **Compatibility Tests**: Verify old imports and function calls still work
2. **Equivalence Tests**: Verify refactored code produces identical outputs
3. **Structure Tests**: Verify new OOP structure is correct
4. **Integration Tests**: Verify layers work together correctly

**Unit Test Coverage:**
- Repository CRUD operations
- Service business logic
- Controller request handling
- Dependency injection
- Backward compatibility wrappers

**Example Unit Test:**
```python
def test_request_service_backward_compatibility():
    """Test that old function interface still works"""
    # Old way (module-level function)
    from services import request_service
    request = request_service.create_request('breakdown', 'test.txt')
    
    # Should work identically
    assert request.action_type == 'breakdown'
    assert request.filename == 'test.txt'
    assert request.status == 'processing'

def test_request_service_new_interface():
    """Test that new class interface works"""
    # New way (class-based)
    from services.request.request_service import RequestService
    service = RequestService()
    request = service.create_request('breakdown', 'test.txt')
    
    # Should produce identical result
    assert request.action_type == 'breakdown'
    assert request.filename == 'test.txt'
    assert request.status == 'processing'
```

### Property-Based Testing Approach

Property-based testing will be used to verify correctness properties across many inputs using the Hypothesis library for Python.

**PBT Library:** Hypothesis (https://hypothesis.readthedocs.io/)
**Configuration:** Each property test will run a minimum of 100 iterations

**Property Test Structure:**
Each property-based test will:
1. Generate random valid inputs using Hypothesis strategies
2. Execute the operation on both old and new implementations
3. Assert that outputs and side effects are identical
4. Be tagged with the property number from this design document

**Example Property Test:**
```python
from hypothesis import given, strategies as st
import pytest

@given(
    action_type=st.sampled_from(['breakdown', 'verify', 'create']),
    filename=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
@pytest.mark.property_test
def test_property_5_business_logic_equivalence(action_type, filename):
    """
    Property 5: Business Logic Equivalence
    Feature: repository-oop-refactoring, Property 5
    
    For any service operation with identical inputs, the output and 
    side effects should be identical before and after refactoring.
    """
    # Setup: Create test database
    setup_test_db()
    
    # Old implementation
    from services import request_service as old_service
    old_request = old_service.create_request(action_type, filename)
    old_id = old_request.id
    
    # Reset database
    reset_test_db()
    
    # New implementation
    from services.request.request_service import RequestService
    new_service = RequestService()
    new_request = new_service.create_request(action_type, filename)
    new_id = new_request.id
    
    # Assert equivalence
    assert old_request.action_type == new_request.action_type
    assert old_request.filename == new_request.filename
    assert old_request.status == new_request.status
    assert old_id == new_id  # Same ID generation logic
```

**Property Test Tags:**
Each property test MUST include a comment with this exact format:
```python
"""
Property X: Property Name
Feature: repository-oop-refactoring, Property X: Property description
"""
```

**Test Organization:**
- Property tests will be in `tests/test_refactoring_properties.py`
- Unit tests will be in existing test files
- Integration tests will verify end-to-end workflows

**Test Execution:**
All existing tests must pass without modification after refactoring. This is the primary validation that functionality is preserved.

