# Implementation Plan: Repository OOP Refactoring

## Phase 1: Foundation and Core Infrastructure

- [x] 1. Create core infrastructure
  - Create `core/` directory structure
  - Implement `BaseService` class with dependency injection support
  - Implement `BaseRepository` class with generic CRUD operations
  - Implement `DependencyContainer` for service/repository management
  - Create custom exception hierarchy in `core/exceptions.py`
  - _Requirements: 2.1, 4.1, 6.1_

- [ ]* 1.1 Write property test for dependency injection
  - **Property 18: Constructor Dependency Injection**
  - **Validates: Requirements 6.1**

- [x] 2. Set up testing infrastructure
  - Create `tests/test_refactoring_properties.py` for property-based tests
  - Set up Hypothesis configuration (100 iterations minimum)
  - Create test fixtures for database setup/teardown
  - Create helper functions for comparing old vs new implementations
  - _Requirements: 10.1, 10.2, 10.3_

## Phase 2: Repository Layer Implementation

- [x] 3. Implement core repositories
  - Create `repositories/` directory structure
  - Implement `RequestRepository` with all query methods
  - Implement `ComparisonRepository` with comparison-specific queries
  - Implement `ChatSessionRepository` for chat operations
  - _Requirements: 4.1, 4.2, 4.3_

- [ ]* 3.1 Write property test for repository CRUD operations
  - **Property 11: Repository CRUD Completeness**
  - **Validates: Requirements 4.2**

- [ ]* 3.2 Write property test for query result equivalence
  - **Property 12: Query Result Equivalence**
  - **Validates: Requirements 4.3**

- [x] 4. Implement merge assistant repositories
  - Implement `MergeSessionRepository` with session management
  - Implement `PackageRepository` for package operations
  - Implement `ChangeRepository` for change tracking
  - Implement `AppianObjectRepository` for object queries
  - _Requirements: 4.1, 4.2, 4.3_

- [ ]* 4.1 Write property test for relationship navigation
  - **Property 14: Relationship Navigation Preservation**
  - **Validates: Requirements 4.5**

- [ ]* 4.2 Write property test for transaction behavior
  - **Property 13: Transaction Behavior Preservation**
  - **Validates: Requirements 4.4**

## Phase 3: Service Layer Refactoring

- [x] 5. Refactor request services
  - Create `services/request/` directory
  - Refactor `RequestService` to class-based with DI
  - Refactor `FileService` to class-based with DI
  - Refactor `DocumentService` to class-based with DI
  - Create backward compatibility wrapper in `services/request_service.py`
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 5.1 Write property test for business logic equivalence
  - **Property 5: Business Logic Equivalence**
  - **Validates: Requirements 2.5**

- [ ]* 5.2 Write property test for function signature preservation
  - **Property 4: Function Signature Preservation**
  - **Validates: Requirements 2.4**

- [ ]* 5.3 Write property test for service interaction preservation
  - **Property 19: Service Interaction Preservation**
  - **Validates: Requirements 6.2**

- [x] 6. Refactor comparison services
  - Create `services/comparison/` directory
  - Refactor `ComparisonService` to use repository pattern
  - Refactor `BlueprintAnalyzer` to class-based service
  - Refactor `ComparisonEngine` to use DI
  - Create backward compatibility wrapper in `services/comparison_service.py`
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 6.1 Write property test for comparison result equivalence
  - **Property 5: Business Logic Equivalence** (comparison-specific)
  - **Validates: Requirements 2.5**

- [x] 7. Refactor AI services
  - Create `services/ai/` directory
  - Refactor `BedrockRAGService` to class-based with DI
  - Refactor `QAgentService` to class-based with DI
  - Create backward compatibility wrappers
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 7.1 Write property test for AI service equivalence
  - **Property 5: Business Logic Equivalence** (AI-specific)
  - **Validates: Requirements 2.5**

- [x] 8. Refactor merge assistant services
  - Create `services/merge/` directory
  - Refactor `MergeService` to use repository pattern
  - Refactor `PackageService` to class-based with DI
  - Refactor `ChangeService` to class-based with DI
  - Create backward compatibility wrappers
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ]* 8.1 Write property test for merge service equivalence
  - **Property 5: Business Logic Equivalence** (merge-specific)
  - **Validates: Requirements 2.5**

## Phase 4: Large File Decomposition

- [x] 9. Decompose process_model_enhancement.py (3,476 lines)
  - Analyze logical boundaries in process model enhancement
  - Extract `NodeParser` class to separate file
  - Extract `FlowParser` class to separate file
  - Extract `ProcessModelAnalyzer` class to separate file
  - Create compatibility imports in original file
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 9.1 Write property test for decomposed file equivalence
  - **Property 23: Class Relationship Preservation**
  - **Validates: Requirements 7.4**

- [x] 10. Decompose three_way_merge_service.py (1,327 lines)
  - Analyze logical boundaries in three-way merge
  - Extract `ConflictDetector` class to separate file
  - Extract `MergeStrategy` class to separate file
  - Extract `ChangeClassifier` class to separate file
  - Create compatibility imports in original file
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 10.1 Write property test for merge decomposition equivalence
  - **Property 22: Import Preservation**
  - **Validates: Requirements 7.3**

- [x] 11. Decompose parsers.py (927 lines)
  - Analyze parser types and boundaries
  - Extract each parser type to separate file (XMLParser, JSONParser, etc.)
  - Create base `Parser` class for common functionality
  - Create compatibility imports in original file
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 11.1 Write property test for parser equivalence
  - **Property 21: Large File Decomposition**
  - **Validates: Requirements 7.2**

## Phase 5: Controller Layer Refactoring

- [x] 12. Create base controller
  - Implement `BaseController` class with common functionality
  - Add helper methods for response formatting
  - Add helper methods for error handling
  - Add helper methods for service access
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 13. Refactor breakdown controller
  - Update `breakdown_controller.py` to use service classes
  - Replace direct database access with service calls
  - Maintain all route definitions unchanged
  - Preserve all request/response formats
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 13.1 Write property test for route preservation
  - **Property 6: Flask Route Preservation**
  - **Validates: Requirements 3.1**

- [ ]* 13.2 Write property test for response format preservation
  - **Property 7: Response Format Preservation**
  - **Validates: Requirements 3.3**

- [x] 14. Refactor analyzer controller
  - Update `analyzer_controller.py` to use service classes
  - Replace direct database access with service calls
  - Maintain all route definitions unchanged
  - Preserve all request/response formats
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 14.1 Write property test for error response preservation
  - **Property 8: Error Response Preservation**
  - **Validates: Requirements 3.4**

- [x] 15. Refactor merge assistant controller
  - Update `merge_assistant_controller.py` to use service classes
  - Replace direct database access with service calls
  - Maintain all route definitions unchanged
  - Preserve all request/response formats
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 15.1 Write property test for template rendering preservation
  - **Property 9: Template Rendering Preservation**
  - **Validates: Requirements 3.5**

- [x] 16. Refactor remaining controllers
  - Update `create_controller.py` to use service classes
  - Update `convert_controller.py` to use service classes
  - Update `verify_controller.py` to use service classes
  - Update `chat_controller.py` to use service classes
  - Update `process_controller.py` to use service classes
  - Update `settings_controller.py` to use service classes
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

## Phase 6: Configuration and Dependency Management

- [x] 17. Refactor configuration management
  - Keep `Config` class structure unchanged
  - Add configuration validation methods
  - Add type hints to all configuration properties
  - Ensure all environment variables are handled identically
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ]* 17.1 Write property test for configuration preservation
  - **Property 15: Configuration Value Preservation**
  - **Validates: Requirements 5.1**

- [ ]* 17.2 Write property test for environment variable handling
  - **Property 16: Environment Variable Handling**
  - **Validates: Requirements 5.2**

- [x] 18. Initialize dependency container
  - Update `app.py` to initialize DependencyContainer
  - Register all services in container
  - Register all repositories in container
  - Ensure singleton patterns are preserved
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 18.1 Write property test for singleton preservation
  - **Property 20: Singleton Pattern Preservation**
  - **Validates: Requirements 6.4**

## Phase 7: Documentation and Type Hints

- [x] 19. Add comprehensive documentation
  - Add docstrings to all new classes
  - Add docstrings to all new methods
  - Add type hints to all function signatures
  - Document all class attributes
  - Add comments explaining structural changes
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ]* 19.1 Write property test for documentation completeness
  - **Property 31: Public Class Documentation**
  - **Validates: Requirements 11.1**

- [ ]* 19.2 Write property test for type hint completeness
  - **Property 33: Type Hint Completeness**
  - **Validates: Requirements 11.3**

## Phase 8: Backward Compatibility Verification

- [x] 20. Create compatibility test suite
  - Test all old import paths still work
  - Test all old function calls still work
  - Test all old class instantiations still work
  - Test all module-level constants are accessible
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ]* 20.1 Write property test for backward compatible imports
  - **Property 34: Backward Compatible Imports**
  - **Validates: Requirements 12.1**

- [ ]* 20.2 Write property test for public API preservation
  - **Property 35: Public API Surface Preservation**
  - **Validates: Requirements 12.2**

- [ ]* 20.3 Write property test for entry point preservation
  - **Property 36: Entry Point Preservation**
  - **Validates: Requirements 12.4**

## Phase 9: Integration Testing and Validation

- [ ] 21. Run existing test suite
  - Execute all existing unit tests without modification
  - Verify all tests pass
  - Document any test failures and root causes
  - Fix any issues found (without changing test code)
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ]* 21.1 Write property test for test execution preservation
  - **Property 29: Test Execution Preservation**
  - **Validates: Requirements 10.1**

- [ ] 22. Run property-based test suite
  - Execute all property tests (100+ iterations each)
  - Verify all properties hold
  - Document any property violations
  - Fix any issues found
  - _Requirements: All requirements_

- [ ] 23. Perform end-to-end testing
  - Test document breakdown workflow
  - Test SQL conversion workflow
  - Test design creation workflow
  - Test Appian analyzer workflow
  - Test merge assistant workflow
  - Test chat assistant workflow
  - Verify all workflows produce identical results
  - _Requirements: 2.5, 3.3, 3.4, 3.5_

- [ ] 24. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Phase 10: Documentation and Migration Guide

- [ ] 25. Create migration documentation
  - Document new architecture and structure
  - Create guide for using new service classes
  - Create guide for using repository pattern
  - Document backward compatibility approach
  - Create examples of old vs new code patterns
  - _Requirements: 11.5, 12.1, 12.2_

- [ ] 26. Update README and technical documentation
  - Update README with new architecture overview
  - Update TECHNICAL_DESIGN.md with refactoring details
  - Create REFACTORING_GUIDE.md with migration instructions
  - Document all breaking changes (should be none)
  - _Requirements: 11.5_
