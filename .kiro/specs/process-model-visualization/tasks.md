# Implementation Plan

- [x] 1. Set up enhanced process model parsing infrastructure
  - Create new module `services/appian_analyzer/process_model_enhancement.py` for enhanced parsing components
  - Define enhanced data structures for nodes, flows, and flow graphs
  - Set up logging for process model parsing operations
  - _Requirements: 9.1, 9.2_

- [x] 2. Implement NodeExtractor class
- [x] 2.1 Create NodeExtractor with basic node extraction
  - Implement `extract_node()` method to parse node XML elements
  - Implement `determine_node_type()` to identify node types from AC element structure
  - Extract basic node properties (uuid, name, type)
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2.2 Write property test for complete node extraction
  - **Property 1: Complete node extraction**
  - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

- [x] 2.3 Implement property extraction methods
  - Implement `extract_assignment()` for assignment configuration
  - Implement `extract_escalation()` for escalation configuration
  - Implement `extract_form_config()` for interface/form configuration
  - Implement `extract_expressions()` for all node expressions
  - _Requirements: 1.4, 1.5, 3.1, 3.2_

- [x] 2.4 Write property test for assignment extraction
  - **Property 5: Assignment extraction**
  - **Validates: Requirements 3.1, 3.4**

- [x] 2.5 Write property test for escalation extraction
  - **Property 6: Escalation extraction**
  - **Validates: Requirements 3.2**

- [x] 2.6 Implement UUID resolution in NodeExtractor
  - Integrate with ObjectLookup for UUID to name resolution
  - Resolve interface UUIDs, rule UUIDs, and group UUIDs
  - Handle resolution failures gracefully
  - _Requirements: 2.2, 2.4, 3.3, 10.2_

- [x] 2.7 Write property test for UUID resolution
  - **Property 2: UUID resolution consistency**
  - **Validates: Requirements 2.2, 2.4, 3.3, 10.2**

- [x] 2.8 Implement node type-specific extraction
  - Implement User Input Task extraction (form config, assignment)
  - Implement Script Task extraction (expressions, output mappings)
  - Implement Gateway extraction (branching conditions)
  - Implement Subprocess extraction (subprocess reference, parameters)
  - Handle unknown node types gracefully
  - _Requirements: 2.1, 2.3, 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 2.9 Write property tests for node type handling
  - **Property 3: User Input Task extraction**
  - **Validates: Requirements 2.1, 8.1**
  - **Property 4: Script Task extraction**
  - **Validates: Requirements 2.3, 2.5, 8.2**
  - **Property 21: Gateway extraction**
  - **Validates: Requirements 8.3**
  - **Property 22: Subprocess extraction**
  - **Validates: Requirements 8.4**
  - **Property 23: Unknown node type handling**
  - **Validates: Requirements 8.5**

- [x] 2.10 Integrate SAIL formatter with NodeExtractor
  - Format SAIL expressions using existing SAILFormatter
  - Convert internal Appian function names to public API names
  - Preserve expression structure for readability
  - _Requirements: 10.1, 10.3, 10.5_

- [x] 2.11 Write property tests for expression formatting
  - **Property 28: SAIL expression formatting**
  - **Validates: Requirements 10.1, 10.3**
  - **Property 29: Output expression display**
  - **Validates: Requirements 10.4**
  - **Property 30: Appian function conversion**
  - **Validates: Requirements 10.5**

- [x] 3. Implement FlowExtractor class
- [x] 3.1 Create FlowExtractor with flow extraction
  - Implement `extract_flows()` to parse flow elements from XML
  - Extract source node UUID, target node UUID, and conditions
  - Identify conditional vs unconditional flows
  - _Requirements: 5.1, 5.2, 5.3, 5.5_

- [x] 3.2 Write property tests for flow extraction
  - **Property 10: Complete flow extraction**
  - **Validates: Requirements 5.1, 5.2, 5.3**
  - **Property 11: Flow display format**
  - **Validates: Requirements 5.4, 5.5**

- [x] 3.3 Implement flow graph construction
  - Implement `build_flow_graph()` to create graph structure
  - Identify start nodes (no incoming flows)
  - Identify end nodes (no outgoing flows)
  - Build node connection mappings (incoming/outgoing)
  - _Requirements: 5.6, 5.7_

- [x] 3.4 Write property test for flow graph construction
  - **Property 12: Flow graph construction**
  - **Validates: Requirements 5.6, 5.7**

- [x] 4. Enhance ProcessModelParser to use new extractors
- [x] 4.1 Update ProcessModelParser.parse() method
  - Integrate NodeExtractor for node parsing
  - Integrate FlowExtractor for flow parsing
  - Add flow_graph field to ProcessModel
  - Add node_summary field to ProcessModel
  - Maintain existing business_logic field for backward compatibility
  - _Requirements: 9.1, 9.2_

- [x] 4.2 Write property test for backward compatibility
  - **Property 24: Blueprint structure compatibility**
  - **Validates: Requirements 9.1, 9.2**

- [x] 4.3 Implement error handling in enhanced parser
  - Handle malformed XML gracefully
  - Fall back to raw XML on parsing failures
  - Log parsing errors with details
  - Continue processing other nodes on individual node failures
  - _Requirements: 9.5_

- [x] 4.4 Write property test for parser failure fallback
  - **Property 27: Parser failure fallback**
  - **Validates: Requirements 9.5**

- [x] 5. Implement variable tracking
- [x] 5.1 Add variable usage tracking to NodeExtractor
  - Track which nodes reference each variable in expressions
  - Track which nodes modify variables through output expressions
  - Mark parameter variables as process inputs
  - _Requirements: 6.3, 6.4, 6.5_

- [x] 5.2 Write property tests for variable tracking
  - **Property 14: Variable extraction completeness**
  - **Validates: Requirements 6.1, 6.2**
  - **Property 15: Variable usage tracking**
  - **Validates: Requirements 6.3, 6.4**
  - **Property 16: Parameter variable marking**
  - **Validates: Requirements 6.5**

- [x] 6. Checkpoint - Ensure all parsing tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement NodeComparator class
- [x] 7.1 Create NodeComparator with node comparison
  - Implement `compare_nodes()` to compare node lists by UUID
  - Identify added, removed, and modified nodes
  - Generate property-level diffs for modified nodes
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 7.2 Write property tests for node comparison
  - **Property 7: Node comparison by UUID**
  - **Validates: Requirements 4.1, 4.2**
  - **Property 8: Node addition and removal detection**
  - **Validates: Requirements 4.3, 4.4**
  - **Property 9: Property diff completeness**
  - **Validates: Requirements 4.5**

- [x] 7.3 Implement flow comparison
  - Implement `compare_flows()` to compare flow lists
  - Identify added, removed, and modified flows
  - Compare flow conditions and targets
  - _Requirements: 5.8_

- [x] 7.4 Write property test for flow comparison
  - **Property 13: Flow comparison**
  - **Validates: Requirements 5.8**

- [x] 8. Update ThreeWayComparisonService
- [x] 8.1 Integrate NodeComparator into comparison service
  - Update `_build_change_object()` to include enhanced node data
  - Add node-level comparison results to change objects
  - Add flow comparison results to change objects
  - Maintain existing comparison functionality
  - _Requirements: 9.3_

- [x] 8.2 Write property test for comparison data usage
  - **Property 25: Comparison data usage**
  - **Validates: Requirements 9.3**

- [x] 9. Implement ProcessModelRenderer class
- [x] 9.1 Create ProcessModelRenderer with node rendering
  - Implement `render_node_summary()` for single node display
  - Implement `render_property_group()` for categorized properties
  - Group properties by category (Basic, Assignment, Forms, Expressions, Escalation)
  - Generate HTML with proper escaping for XSS prevention
  - _Requirements: 7.1, 7.2_

- [x] 9.2 Write property tests for structured display
  - **Property 17: Structured display over raw XML**
  - **Validates: Requirements 7.1, 7.2**

- [x] 9.3 Implement comparison rendering
  - Implement `render_node_comparison()` for three-way comparison
  - Highlight changed properties in comparison view
  - Show before and after values for changes
  - _Requirements: 7.3, 7.4_

- [x] 9.4 Write property test for comparison display
  - **Property 18: Three-way comparison display**
  - **Validates: Requirements 7.3, 7.4**

- [x] 10. Implement FlowDiagramGenerator class
- [x] 10.1 Create FlowDiagramGenerator with diagram data generation
  - Implement `generate_diagram_data()` to create Mermaid.js compatible data
  - Generate node data with types and labels
  - Generate edge data with conditions
  - Use different node shapes for different types (rectangles for tasks, diamonds for gateways)
  - _Requirements: 7.5, 7.6, 7.9_

- [x] 10.2 Write property tests for diagram generation
  - **Property 19: Flow diagram generation**
  - **Validates: Requirements 7.5, 7.6, 7.9**

- [x] 10.3 Implement comparison diagram generation
  - Implement `generate_comparison_diagram()` with change highlighting
  - Mark added nodes with green styling
  - Mark removed nodes with red styling
  - Mark modified nodes with yellow styling
  - _Requirements: 7.7_

- [x] 10.4 Write property test for comparison diagram highlighting
  - **Property 20: Comparison diagram highlighting**
  - **Validates: Requirements 7.7**

- [x] 11. Update change_detail.html template
- [x] 11.1 Add process model detection and conditional rendering
  - Check if change object is a process model
  - Conditionally render enhanced view for process models
  - Fall back to existing display for non-process-models
  - _Requirements: 9.4_

- [x] 11.2 Write property test for non-process-model display
  - **Property 26: Non-process-model display**
  - **Validates: Requirements 9.4**

- [x] 11.3 Add process model node summary section
  - Display structured node information instead of raw XML
  - Show nodes grouped by type
  - Display properties in categorized sections
  - Add collapsible sections for large process models
  - _Requirements: 7.1, 7.2_

- [x] 11.4 Add three-way comparison view for process models
  - Display base, customer, and vendor node summaries side-by-side
  - Highlight changed properties with visual indicators
  - Show added/removed nodes clearly
  - _Requirements: 7.3, 7.4_

- [x] 11.5 Integrate Mermaid.js for flow visualization
  - Add Mermaid.js library to template
  - Generate Mermaid syntax from flow diagram data
  - Render flow diagram in dedicated section
  - Add zoom and pan controls for complex diagrams
  - _Requirements: 7.5, 7.6, 7.9, 7.10_

- [x] 11.6 Add flow comparison visualization
  - Display comparison flow diagram with change highlighting
  - Use color coding for added (green), removed (red), modified (yellow) nodes
  - Show flow condition changes
  - _Requirements: 7.7_

- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Integration testing and refinement
- [x] 13.1 Test with real Appian packages
  - Test with small process models (< 10 nodes)
  - Test with medium process models (10-50 nodes)
  - Test with large process models (50+ nodes)
  - Verify all node types are handled correctly
  - Verify flow graphs are constructed correctly
  - _Requirements: All_

- [x] 13.2 Write integration tests for end-to-end workflows
  - Test blueprint generation with enhanced parser
  - Test three-way comparison with process models
  - Test change detail page rendering
  - Test error recovery scenarios

- [x] 13.3 Performance testing and optimization
  - Measure parsing time for large process models
  - Measure comparison time for complex process models
  - Optimize slow operations if needed
  - Verify memory usage is reasonable
  - _Requirements: All_

- [x] 13.4 Error handling refinement
  - Test with malformed XML
  - Test with missing required elements
  - Test with invalid node structures
  - Verify fallback behavior works correctly
  - _Requirements: 9.5_

- [x] 14. Documentation and deployment
- [x] 14.1 Update code documentation
  - Add docstrings to all new classes and methods
  - Document data structures and formats
  - Add usage examples
  - _Requirements: All_

- [x] 14.2 Update user documentation
  - Document new process model visualization features
  - Add screenshots of enhanced display
  - Provide guidance on interpreting flow diagrams
  - _Requirements: All_

- [x] 14.3 Add logging and monitoring
  - Log parsing errors with process model details
  - Log performance metrics (parsing time, comparison time)
  - Track feature usage
  - Set up alerts for high failure rates
  - _Requirements: All_

- [ ] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
