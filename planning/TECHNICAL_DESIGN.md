# Appian Version Merge Helper Tool - Technical Design Document

> **Project**: NexusGen Appian Version Merge Helper  
> **Version**: 1.0.0  
> **Date**: November 18, 2025  
> **Status**: Technical Design Phase

## 🏗️ System Architecture Overview

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
├─────────────────────────────────────────────────────────────┤
│  Package Upload │ Analysis Dashboard │ Guided Workflow     │
│  Progress Track │ Change Viewer      │ Reporting           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Controller Layer                           │
├─────────────────────────────────────────────────────────────┤
│  merge_controller.py │ analysis_controller.py              │
│  workflow_controller.py │ reporting_controller.py          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                             │
├─────────────────────────────────────────────────────────────┤
│  Package Manager │ Change Analyzer │ Workflow Engine       │
│  Conflict Detector │ Dependency Mapper │ Progress Tracker  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                               │
├─────────────────────────────────────────────────────────────┤
│  Package Storage │ Analysis Results │ Session Data          │
│  Progress State  │ User Decisions   │ Audit Logs           │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
nexus-gen-v2/
├── controllers/
│   ├── merge_controller.py              # Package upload and management
│   ├── analysis_controller.py           # Change analysis endpoints
│   ├── workflow_controller.py           # Guided implementation workflow
│   └── reporting_controller.py          # Progress and final reports
├── services/
│   ├── merge_helper/                    # New merge helper service directory
│   │   ├── __init__.py
│   │   ├── package_manager.py           # Package upload, validation, storage
│   │   ├── change_analyzer.py           # Three-way change analysis
│   │   ├── conflict_detector.py         # Conflict identification
│   │   ├── dependency_mapper.py         # Object relationship analysis
│   │   ├── workflow_engine.py           # Guided workflow management
│   │   ├── progress_tracker.py          # Implementation progress tracking
│   │   ├── guidance_generator.py        # Implementation guidance creation
│   │   └── models/                      # Data models for merge operations
│   │       ├── __init__.py
│   │       ├── package_models.py        # Package and object models
│   │       ├── change_models.py         # Change and conflict models
│   │       ├── workflow_models.py       # Workflow and progress models
│   │       └── session_models.py        # User session models
│   └── appian_analyzer/                 # Enhanced existing analyzer
│       ├── enhanced_parsers.py          # Extended XML parsing capabilities
│       ├── three_way_comparator.py      # Three-way comparison logic
│       └── dependency_analyzer.py       # Object dependency analysis
├── templates/
│   ├── merge/                           # New merge helper templates
│   │   ├── upload_packages.html         # Package upload interface
│   │   ├── analysis_dashboard.html      # Analysis results overview
│   │   ├── workflow_wizard.html         # Step-by-step implementation
│   │   ├── change_detail.html           # Individual change view
│   │   ├── progress_dashboard.html      # Progress tracking
│   │   └── final_report.html            # Implementation report
│   └── components/
│       ├── package_info.html            # Package information component
│       ├── change_diff.html             # Enhanced diff viewer
│       ├── dependency_graph.html        # Dependency visualization
│       └── progress_indicator.html      # Progress tracking component
├── static/
│   ├── js/
│   │   ├── merge-workflow.js            # Workflow management
│   │   ├── dependency-graph.js          # Dependency visualization
│   │   └── progress-tracker.js          # Progress tracking
│   └── css/
│       └── merge-helper.css             # Merge helper specific styles
└── database/
    └── migrations/
        └── add_merge_tables.sql         # Database schema for merge operations
```

## 🗄️ Database Schema Design

### Core Tables

```sql
-- Package Management
CREATE TABLE merge_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'created',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) NOT NULL,
    package_type VARCHAR(20) NOT NULL, -- 'base', 'customer', 'new_version'
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    object_count INTEGER,
    version_info TEXT, -- JSON metadata
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES merge_sessions(session_id)
);

-- Change Analysis
CREATE TABLE detected_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) NOT NULL,
    object_uuid VARCHAR(36) NOT NULL,
    object_name VARCHAR(255) NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    change_type VARCHAR(20) NOT NULL, -- 'added', 'modified', 'deleted'
    impact_level VARCHAR(20) NOT NULL, -- 'safe', 'moderate', 'critical'
    parent_objects TEXT, -- JSON array of parent UUIDs
    child_objects TEXT, -- JSON array of child UUIDs
    change_details TEXT, -- JSON with detailed change information
    implementation_guidance TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES merge_sessions(session_id)
);

CREATE TABLE conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) NOT NULL,
    change_id INTEGER NOT NULL,
    conflict_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high'
    description TEXT NOT NULL,
    resolution_guidance TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES merge_sessions(session_id),
    FOREIGN KEY (change_id) REFERENCES detected_changes(id)
);

-- Workflow Management
CREATE TABLE implementation_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) NOT NULL,
    change_id INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'pending', 'in_progress', 'completed', 'skipped'
    user_notes TEXT,
    implementation_time INTEGER, -- seconds spent on this change
    completed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES merge_sessions(session_id),
    FOREIGN KEY (change_id) REFERENCES detected_changes(id)
);

CREATE TABLE user_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id VARCHAR(36) NOT NULL,
    change_id INTEGER NOT NULL,
    decision_type VARCHAR(50) NOT NULL,
    decision_value TEXT NOT NULL,
    reasoning TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES merge_sessions(session_id),
    FOREIGN KEY (change_id) REFERENCES detected_changes(id)
);
```

## 🔧 Core Service Components

### 1. Package Manager Service

```python
class PackageManager:
    """Handles package upload, validation, and storage"""
    
    def upload_package(self, session_id: str, package_type: str, file: FileStorage) -> Package:
        """Upload and validate Appian package"""
        
    def validate_package(self, file_path: str) -> PackageValidation:
        """Validate package structure and extract metadata"""
        
    def extract_metadata(self, file_path: str) -> PackageMetadata:
        """Extract version info and object counts"""
        
    def get_package_objects(self, package_id: int) -> List[AppianObject]:
        """Get all objects from a package"""
        
    def cleanup_session_files(self, session_id: str) -> None:
        """Clean up temporary files for a session"""
```

### 2. Change Analyzer Service

```python
class ChangeAnalyzer:
    """Performs three-way analysis to identify changes"""
    
    def analyze_changes(self, session_id: str) -> AnalysisResult:
        """Main entry point for change analysis"""
        
    def compare_base_to_new(self, base_package: Package, new_package: Package) -> List[Change]:
        """Identify vendor changes (base → new version)"""
        
    def compare_base_to_customer(self, base_package: Package, customer_package: Package) -> List[Change]:
        """Identify customer customizations (base → customer)"""
        
    def classify_change_impact(self, change: Change) -> ImpactLevel:
        """Classify change as safe, moderate, or critical"""
        
    def generate_implementation_guidance(self, change: Change) -> str:
        """Generate step-by-step implementation guidance"""
```

### 3. Conflict Detector Service

```python
class ConflictDetector:
    """Identifies potential conflicts between vendor and customer changes"""
    
    def detect_conflicts(self, vendor_changes: List[Change], customer_changes: List[Change]) -> List[Conflict]:
        """Identify conflicts between vendor and customer changes"""
        
    def analyze_object_conflicts(self, object_uuid: str, vendor_change: Change, customer_change: Change) -> Optional[Conflict]:
        """Analyze conflicts for a specific object"""
        
    def assess_conflict_severity(self, conflict: Conflict) -> ConflictSeverity:
        """Assess the severity of a detected conflict"""
        
    def generate_resolution_guidance(self, conflict: Conflict) -> str:
        """Generate guidance for resolving the conflict"""
```

### 4. Dependency Mapper Service

```python
class DependencyMapper:
    """Maps object relationships and dependencies"""
    
    def build_dependency_graph(self, objects: List[AppianObject]) -> DependencyGraph:
        """Build complete dependency graph for all objects"""
        
    def find_object_dependencies(self, object_uuid: str) -> ObjectDependencies:
        """Find all dependencies for a specific object"""
        
    def calculate_change_order(self, changes: List[Change], dependency_graph: DependencyGraph) -> List[Change]:
        """Order changes based on dependencies (parents first)"""
        
    def analyze_change_impact(self, change: Change, dependency_graph: DependencyGraph) -> ChangeImpact:
        """Analyze downstream impact of a change"""
```

### 5. Workflow Engine Service

```python
class WorkflowEngine:
    """Manages the guided implementation workflow"""
    
    def initialize_workflow(self, session_id: str) -> WorkflowSession:
        """Initialize workflow with ordered changes"""
        
    def get_next_change(self, session_id: str) -> Optional[Change]:
        """Get the next change to implement"""
        
    def mark_change_completed(self, session_id: str, change_id: int, notes: str) -> None:
        """Mark a change as completed"""
        
    def skip_change(self, session_id: str, change_id: int, reason: str) -> None:
        """Skip a change with reason"""
        
    def get_workflow_progress(self, session_id: str) -> WorkflowProgress:
        """Get current workflow progress"""
```

## 🎨 Frontend Components

### 1. Package Upload Interface

```html
<!-- templates/merge/upload_packages.html -->
<div class="package-upload-container">
    <div class="upload-section">
        <h3>Base Package (Original Version)</h3>
        <div class="upload-zone" data-package-type="base">
            <i class="fas fa-cloud-upload-alt"></i>
            <p>Drop Appian export ZIP file here or click to browse</p>
        </div>
    </div>
    
    <div class="upload-section">
        <h3>Customer Package (Customized Version)</h3>
        <div class="upload-zone" data-package-type="customer">
            <i class="fas fa-cloud-upload-alt"></i>
            <p>Drop Appian export ZIP file here or click to browse</p>
        </div>
    </div>
    
    <div class="upload-section">
        <h3>New Version Package (Latest Release)</h3>
        <div class="upload-zone" data-package-type="new_version">
            <i class="fas fa-cloud-upload-alt"></i>
            <p>Drop Appian export ZIP file here or click to browse</p>
        </div>
    </div>
</div>
```

### 2. Analysis Dashboard

```html
<!-- templates/merge/analysis_dashboard.html -->
<div class="analysis-dashboard">
    <div class="summary-cards">
        <div class="card">
            <h4>Total Changes</h4>
            <span class="metric">{{ total_changes }}</span>
        </div>
        <div class="card">
            <h4>Critical Changes</h4>
            <span class="metric critical">{{ critical_changes }}</span>
        </div>
        <div class="card">
            <h4>Conflicts Detected</h4>
            <span class="metric warning">{{ conflicts_count }}</span>
        </div>
    </div>
    
    <div class="change-breakdown">
        <h3>Changes by Object Type</h3>
        <canvas id="changeChart"></canvas>
    </div>
    
    <div class="conflict-summary">
        <h3>Potential Conflicts</h3>
        <div class="conflict-list">
            {% for conflict in conflicts %}
            <div class="conflict-item {{ conflict.severity }}">
                <h5>{{ conflict.object_name }}</h5>
                <p>{{ conflict.description }}</p>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
```

### 3. Workflow Wizard

```html
<!-- templates/merge/workflow_wizard.html -->
<div class="workflow-wizard">
    <div class="progress-header">
        <div class="progress-bar">
            <div class="progress-fill" style="width: {{ progress_percentage }}%"></div>
        </div>
        <span class="progress-text">{{ completed_changes }} of {{ total_changes }} changes completed</span>
    </div>
    
    <div class="current-change">
        <div class="change-header">
            <h3>{{ current_change.object_name }}</h3>
            <span class="change-type {{ current_change.impact_level }}">{{ current_change.change_type }}</span>
        </div>
        
        <div class="change-content">
            <div class="change-diff">
                <!-- Enhanced diff viewer component -->
                {% include 'components/change_diff.html' %}
            </div>
            
            <div class="implementation-guidance">
                <h4>Implementation Steps</h4>
                <div class="guidance-content">
                    {{ current_change.implementation_guidance | markdown }}
                </div>
            </div>
            
            <div class="conflict-warnings">
                {% if current_change.conflicts %}
                <h4>⚠️ Potential Conflicts</h4>
                {% for conflict in current_change.conflicts %}
                <div class="conflict-warning">
                    <p>{{ conflict.description }}</p>
                    <p><strong>Resolution:</strong> {{ conflict.resolution_guidance }}</p>
                </div>
                {% endfor %}
                {% endif %}
            </div>
        </div>
        
        <div class="change-actions">
            <button class="btn btn-success" onclick="markCompleted()">Mark as Completed</button>
            <button class="btn btn-warning" onclick="skipChange()">Skip This Change</button>
            <button class="btn btn-secondary" onclick="addNotes()">Add Notes</button>
        </div>
    </div>
    
    <div class="navigation">
        <button class="btn btn-outline" onclick="previousChange()" {{ 'disabled' if is_first_change }}>Previous</button>
        <button class="btn btn-outline" onclick="nextChange()" {{ 'disabled' if is_last_change }}>Next</button>
    </div>
</div>
```

## 🔄 API Endpoints

### Package Management
```python
POST /merge/sessions                    # Create new merge session
POST /merge/sessions/{id}/packages      # Upload package to session
GET  /merge/sessions/{id}/packages      # Get session packages
DELETE /merge/sessions/{id}             # Delete session and cleanup files
```

### Analysis
```python
POST /merge/sessions/{id}/analyze       # Start change analysis
GET  /merge/sessions/{id}/analysis      # Get analysis results
GET  /merge/sessions/{id}/changes       # Get detected changes
GET  /merge/sessions/{id}/conflicts     # Get detected conflicts
```

### Workflow
```python
POST /merge/sessions/{id}/workflow/start    # Initialize workflow
GET  /merge/sessions/{id}/workflow/current  # Get current change
POST /merge/sessions/{id}/workflow/complete # Mark change completed
POST /merge/sessions/{id}/workflow/skip     # Skip current change
GET  /merge/sessions/{id}/workflow/progress # Get workflow progress
```

### Reporting
```python
GET  /merge/sessions/{id}/report        # Get implementation report
GET  /merge/sessions/{id}/export        # Export session data
```

## 🔒 Security Considerations

### File Upload Security
- Validate file types and sizes
- Scan uploaded files for malware
- Store files in secure temporary location
- Automatic cleanup after session completion

### Data Protection
- Encrypt sensitive package data at rest
- Secure session management with UUIDs
- Audit logging for all user actions
- Data retention policies for temporary files

### Access Control
- Session-based access control
- User authentication for sensitive operations
- Rate limiting for API endpoints
- Input validation and sanitization

## 📊 Performance Considerations

### Scalability
- Asynchronous processing for large packages
- Pagination for large change lists
- Caching for frequently accessed data
- Background processing for analysis tasks

### Optimization
- Streaming XML parsing for large files
- Efficient diff algorithms for code comparison
- Database indexing for fast queries
- Client-side caching for UI components

### Resource Management
- Memory-efficient processing of large packages
- Temporary file cleanup and management
- Connection pooling for database operations
- Monitoring and alerting for resource usage

## 🧪 Testing Strategy

### Unit Testing
- Service layer components (95% coverage target)
- Data models and validation logic
- Utility functions and helpers
- API endpoint functionality

### Integration Testing
- End-to-end workflow testing
- Package upload and analysis pipeline
- Database operations and transactions
- External service integrations

### User Acceptance Testing
- Real customer package scenarios
- Workflow usability testing
- Performance testing with large packages
- Cross-browser compatibility testing

## 🚀 Deployment Strategy

### Development Environment
- Local development with SQLite database
- Mock data for testing scenarios
- Hot reloading for rapid development
- Comprehensive logging and debugging

### Staging Environment
- Production-like environment for testing
- Real customer data (anonymized)
- Performance and load testing
- User acceptance testing

### Production Environment
- Scalable infrastructure for multiple users
- Secure file storage and processing
- Monitoring and alerting systems
- Backup and disaster recovery procedures

## 📈 Monitoring & Analytics

### Application Metrics
- Session creation and completion rates
- Average time per change implementation
- Most common conflict types
- User workflow patterns

### Performance Metrics
- Package processing times
- API response times
- Database query performance
- File upload/download speeds

### Business Metrics
- User adoption and engagement
- Time savings compared to manual process
- Error reduction and accuracy improvements
- Customer satisfaction scores

## 🔄 Future Enhancements

### Phase 2 Features
- **Automated Testing**: Generate test scripts for changed objects
- **Deployment Integration**: Create Appian deployment packages
- **Collaboration**: Multi-user review and approval workflows
- **Version Control**: Track changes over time

### Advanced Capabilities
- **Machine Learning**: Learn from user decisions to improve guidance
- **Semantic Analysis**: Understand functional impact of changes
- **Cloud Processing**: Handle very large packages with cloud resources
- **API Integration**: Connect with customer development workflows

## 📋 Implementation Checklist

### Phase 1: Foundation
- [ ] Set up new directory structure
- [ ] Create database schema and migrations
- [ ] Implement package manager service
- [ ] Build basic change analyzer
- [ ] Create package upload interface
- [ ] Implement basic change detection

### Phase 2: Intelligence
- [ ] Implement conflict detector service
- [ ] Build dependency mapper
- [ ] Create analysis dashboard
- [ ] Implement change classification
- [ ] Add implementation guidance generation
- [ ] Build conflict resolution recommendations

### Phase 3: Workflow
- [ ] Implement workflow engine service
- [ ] Create guided workflow interface
- [ ] Build progress tracking system
- [ ] Implement user decision capture
- [ ] Create change detail views
- [ ] Add workflow navigation

### Phase 4: Polish
- [ ] Implement reporting system
- [ ] Add export capabilities
- [ ] Performance optimization
- [ ] User experience improvements
- [ ] Comprehensive testing
- [ ] Documentation and training materials

This technical design provides a comprehensive blueprint for implementing the Appian Version Merge Helper Tool while maintaining the existing NexusGen architecture and following established patterns.
