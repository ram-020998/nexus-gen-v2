# NexusGen - Enterprise Document Intelligence & Appian Merge Platform

> **Version 6.0.0** | A comprehensive Flask-based platform combining document intelligence, AI-powered analysis, and advanced three-way merge capabilities for Appian applications.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3%2B-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()
[![Port](https://img.shields.io/badge/Port-5000-orange.svg)]()

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Core Features](#-core-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Quick Start](#-quick-start)
- [Database Schema](#-database-schema)
- [Development Guide](#-development-guide)
- [Testing](#-testing)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [Contributing](#-contributing)

---

## 🎉 What's New in Version 6.0.0

**December 2025 - Major Release**

This release represents a complete platform overhaul with significant improvements across all areas:

- ✅ **Complete Three-Way Merge Engine** - 10-step transactional workflow with set-based classification
- ✅ **AI-Powered Analysis** - Async AI summary generation using AWS Bedrock
- ✅ **Clean Architecture** - Dependency injection, base classes, and strict layer separation
- ✅ **50+ Database Tables** - Comprehensive schema with proper relationships and referential integrity
- ✅ **Property-Based Testing** - 18 properties tested with real Appian packages
- ✅ **Enhanced UI** - Custom dark theme with SAIL syntax highlighting
- ✅ **Performance Optimizations** - Connection pooling, query optimization, batch operations
- ✅ **RESTful API** - Complete API for all operations with session management

**Port Change:** Application now runs on **port 5000** (previously 5002)

---

## 🚀 Overview

NexusGen is an enterprise-grade platform that revolutionizes how organizations handle document intelligence and Appian application lifecycle management. Built with clean architecture principles and modern design patterns, it provides three major capabilities:

### 1. **Document Intelligence Hub**
Transform unstructured documents into actionable insights with AI-powered processing, including spec breakdown, design verification, and automated SQL conversion.

### 2. **Three-Way Merge Assistant**
Sophisticated conflict detection and resolution for Appian package merges, supporting complex vendor upgrade scenarios with AI-powered guidance.

### 3. **AI-Powered Analysis**
Leverages AWS Bedrock and Amazon Q for intelligent document processing, change analysis, and business impact assessment.


---

## ✨ Core Features

### 📄 Document Intelligence

#### Spec Breakdown
- **Automated Extraction**: Upload documents (PDF, DOCX, TXT, MD) and automatically extract user stories and acceptance criteria
- **RAG Integration**: Leverages AWS Bedrock Knowledge Base for context-aware processing
- **Excel Export**: Generate structured Excel reports with complete breakdown
- **Reference Tracking**: Unique reference IDs (RQ_BR_001 format) for all requests

#### Design Verification
- **AI-Powered Validation**: Verify design documents against best practices and standards
- **Confidence Scoring**: RAG similarity scores indicate validation confidence
- **Comprehensive Feedback**: Detailed recommendations and improvement suggestions

#### Design Creation
- **Automated Generation**: Create comprehensive design documents from acceptance criteria
- **Template-Based**: Follows industry-standard design document structures
- **Iterative Refinement**: Support for multiple revision cycles

#### SQL Conversion
- **Bidirectional Conversion**: Convert between MariaDB and Oracle SQL dialects
- **Syntax Preservation**: Maintains query structure and logic
- **Batch Processing**: Handle multiple SQL statements efficiently

#### AI Chat Assistant
- **Interactive Q&A**: Natural language interface for document-related queries
- **Context-Aware**: Maintains conversation history for coherent interactions
- **Knowledge Base Access**: Direct access to organizational knowledge via RAG


### 🔄 Three-Way Merge Assistant

#### Package Analysis
- **Multi-Package Support**: Analyze base, customized, and new vendor packages simultaneously
- **Object Extraction**: Parse and catalog all Appian objects (interfaces, process models, rules, etc.)
- **Version Tracking**: Track object versions across all three packages
- **UUID Resolution**: Maintain object identity across package versions

#### Delta Comparison (A→C)
- **Vendor Change Detection**: Identify all changes from base to new vendor version
- **Change Categorization**: Classify as NEW, MODIFIED, or DEPRECATED
- **Content Analysis**: Deep comparison of SAIL code, properties, and configurations
- **Version Tracking**: Detect version UUID changes

#### Customer Comparison (A→B)
- **Customization Detection**: Identify all customer modifications from base version
- **Parallel Analysis**: Symmetric comparison structure with delta comparison
- **Change Tracking**: Track additions, modifications, and removals

#### Conflict Classification
Implements 7 sophisticated classification rules:

1. **Rule 10a**: MODIFIED in delta AND not modified by customer → **NO_CONFLICT**
2. **Rule 10b**: MODIFIED in delta AND modified by customer (B ≠ C) → **CONFLICT**
3. **Rule 10c**: MODIFIED in delta AND removed by customer → **DELETED**
4. **Rule 10d**: NEW in delta → **NEW**
5. **Rule 10e**: DEPRECATED in delta AND not modified by customer → **NO_CONFLICT**
6. **Rule 10f**: DEPRECATED in delta AND modified by customer → **CONFLICT**
7. **Rule 10g**: DEPRECATED in delta AND removed by customer → **NO_CONFLICT**

#### AI-Powered Summaries
- **Async Generation**: Background processing for change summaries
- **Business Impact**: AI-generated analysis of change implications
- **Merge Guidance**: Intelligent recommendations for conflict resolution
- **Priority Scoring**: Automatic complexity and time estimation

#### Interactive Workflow
- **Change Navigation**: Browse changes by classification, object type, or status
- **Review Management**: Mark changes as reviewed or skipped
- **Note Taking**: Add contextual notes to changes
- **Progress Tracking**: Real-time statistics on review progress


---

## 🏗️ Architecture

NexusGen follows **Clean Architecture** principles with strict separation of concerns, dependency injection, and domain-driven design. The architecture is organized into distinct layers, each with specific responsibilities and clear boundaries.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                          │
│  Flask Controllers + Jinja2 Templates + Bootstrap UI                │
│  - Request/Response handling                                        │
│  - Input validation                                                 │
│  - View rendering                                                   │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER                           │
│  Services (Business Logic & Orchestration)                          │
│  - Three-way merge orchestration                                    │
│  - Document processing workflows                                    │
│  - AI service integration                                           │
│  - Report generation                                                │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                           DOMAIN LAYER                              │
│  Business Entities, Enums, and Strategies                           │
│  - ObjectIdentity, DeltaChange entities                             │
│  - Classification, ChangeType enums                                 │
│  - Comparison strategies                                            │
│  - NO database coupling                                             │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                           │
│  Repositories (Data Access) + Core (DI, Logging, Exceptions)        │
│  - Repository pattern for data access                               │
│  - Dependency injection container                                   │
│  - Centralized logging                                              │
│  - Exception hierarchy                                              │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         PERSISTENCE LAYER                           │
│  SQLAlchemy ORM + SQLite Database                                   │
│  - 50+ database tables                                              │
│  - Connection pooling                                               │
│  - Transaction management                                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

#### 1. Presentation Layer (`controllers/`, `templates/`, `static/`)

**Controllers** handle HTTP requests and responses:
- `breakdown_controller.py` - Document breakdown endpoints
- `verify_controller.py` - Design verification endpoints
- `create_controller.py` - Design creation endpoints
- `convert_controller.py` - SQL conversion endpoints
- `chat_controller.py` - AI chat interface
- `merge_assistant_controller.py` - Three-way merge endpoints
- `process_controller.py` - Process history and tracking
- `settings_controller.py` - Application settings
- `debug_controller.py` - Development debugging tools

**Templates** provide server-side rendering:
- Jinja2 templates with Bootstrap 5 styling
- Custom dark theme with Appian color palette
- Responsive design for mobile and desktop
- Component-based structure for reusability

**Static Assets**:
- `css/docflow.css` - Custom styling and theme
- `js/main.js` - Core JavaScript functionality
- `js/sail-highlighter.js` - SAIL code syntax highlighting
- `js/settings.js` - Settings management
- `js/upload.js` - File upload handling


#### 2. Application Layer (`services/`)

**Core Services** orchestrate business logic:

**Three-Way Merge Services**:
- `three_way_merge_orchestrator.py` - Main workflow coordinator (10-step process)
- `package_extraction_service.py` - ZIP extraction and object parsing
- `delta_comparison_service.py` - A→C vendor change detection
- `customer_comparison_service.py` - A→B customer change detection
- `classification_service.py` - 7-rule classification engine
- `merge_guidance_service.py` - AI-powered merge recommendations
- `merge_summary_service.py` - Async AI summary generation
- `comparison_persistence_service.py` - Detailed comparison storage
- `comparison_retrieval_service.py` - Comparison data retrieval
- `change_navigation_service.py` - Change browsing and filtering
- `change_action_service.py` - Review actions (mark reviewed, skip, etc.)
- `session_statistics_service.py` - Session metrics and progress
- `report_generation_service.py` - Excel/PDF report generation

**Document Processing Services**:
- `request/request_service.py` - Request lifecycle management
- `request/file_service.py` - File upload and validation
- `request/document_service.py` - Document text extraction
- `excel_service.py` - Excel report generation
- `word_service.py` - Word document generation
- `process_tracker.py` - Timeline and metrics tracking

**AI Integration Services**:
- `ai/bedrock_service.py` - AWS Bedrock RAG integration
- `ai/q_agent_service.py` - Amazon Q CLI agent integration

**Parsing Services** (`services/parsers/`):
- `xml_parser_factory.py` - Factory for object-specific parsers
- `interface_parser.py` - Interface object parsing
- `process_model_parser.py` - Process model parsing
- `expression_rule_parser.py` - Expression rule parsing
- `record_type_parser.py` - Record type parsing
- `cdt_parser.py` - CDT parsing
- `integration_parser.py` - Integration parsing
- `web_api_parser.py` - Web API parsing
- `site_parser.py` - Site parsing
- `group_parser.py` - Group parsing
- `constant_parser.py` - Constant parsing
- `connected_system_parser.py` - Connected system parsing
- `unknown_object_parser.py` - Fallback parser for unknown types

**Utility Services**:
- `sail_formatter.py` - SAIL code formatting and cleanup
- `sail_diff_service.py` - SAIL code diff generation
- `settings_service.py` - Application settings management
- `data_source_factory.py` - Data source abstraction


#### 3. Domain Layer (`domain/`)

**Pure business logic with NO infrastructure dependencies**:

**Entities** (`domain/entities.py`):
- `ObjectIdentity` - Immutable object identification
- `DeltaChange` - Represents a change in delta comparison
- `CustomerChange` - Represents a customer modification
- `ClassifiedChange` - Change with classification applied
- All entities are immutable dataclasses

**Enumerations** (`domain/enums.py`):
- `PackageType` - BASE, CUSTOMIZED, NEW_VENDOR
- `ChangeCategory` - NEW, MODIFIED, DEPRECATED
- `Classification` - NO_CONFLICT, CONFLICT, NEW, DELETED
- `ChangeType` - ADDED, MODIFIED, REMOVED
- `SessionStatus` - PROCESSING, READY, IN_PROGRESS, COMPLETED, ERROR

**Strategies** (`domain/comparison_strategies.py`):
- Pluggable comparison strategies for different object types
- Interface comparison strategy
- Process model comparison strategy
- Record type comparison strategy
- Generic object comparison strategy

#### 4. Infrastructure Layer (`repositories/`, `core/`)

**Repositories** provide data access abstraction:

**Core Repositories**:
- `request_repository.py` - Document request data access
- `chat_session_repository.py` - Chat session data access
- `change_repository.py` - Change data access with filtering
- `object_lookup_repository.py` - Global object registry access
- `package_object_mapping_repository.py` - Package-object relationships
- `delta_comparison_repository.py` - Delta comparison results
- `customer_comparison_repository.py` - Customer comparison results

**Object-Specific Repositories** (40+ repositories):
- `interface_repository.py` - Interface objects
- `process_model_repository.py` - Process models
- `expression_rule_repository.py` - Expression rules
- `record_type_repository.py` - Record types
- `cdt_repository.py` - Custom data types
- `integration_repository.py` - Integrations
- `web_api_repository.py` - Web APIs
- `site_repository.py` - Sites
- `group_repository.py` - Groups
- `constant_repository.py` - Constants
- `connected_system_repository.py` - Connected systems
- `data_store_repository.py` - Data stores
- `unknown_object_repository.py` - Unknown object types

**Comparison Repositories** (`repositories/comparison/`):
- `interface_comparison_repository.py` - Interface comparison results
- `process_model_comparison_repository.py` - Process model comparisons
- `record_type_comparison_repository.py` - Record type comparisons

**Core Infrastructure** (`core/`):
- `dependency_container.py` - Dependency injection container (singleton)
- `base_service.py` - Base class for all services
- `base_repository.py` - Generic CRUD operations for repositories
- `exceptions.py` - Custom exception hierarchy
- `logger.py` - Centralized logging configuration
- `cache.py` - Caching utilities


#### 5. Persistence Layer (`models.py`)

**SQLAlchemy ORM Models** (50+ tables):

**Application-Wide Tables**:
- `Request` - Document processing requests (breakdown, verify, create)
- `ChatSession` - AI chat conversations
- `MergeSession` - Three-way merge sessions

**Three-Way Merge Core Tables**:
- `Package` - Uploaded packages (base, customized, new_vendor)
- `ObjectLookup` - **Global object registry** (NO package_id!)
- `PackageObjectMapping` - Junction table for package-object relationships
- `DeltaComparisonResult` - A→C vendor changes (Set D)
- `CustomerComparisonResult` - A→B customer changes (Set E)
- `Change` - Working set of classified changes for review
- `ObjectVersion` - Package-specific object versions

**Object-Specific Tables** (40+ tables):
- `Interface` + `InterfaceParameter` + `InterfaceSecurity`
- `ExpressionRule` + `ExpressionRuleInput`
- `ProcessModel` + `ProcessModelNode` + `ProcessModelFlow` + `ProcessModelVariable`
- `RecordType` + `RecordTypeField` + `RecordTypeRelationship` + `RecordTypeView` + `RecordTypeAction`
- `CDT` + `CDTField`
- `Integration`
- `WebAPI`
- `Site`
- `Group`
- `Constant`
- `ConnectedSystem`
- `DataStore`
- `UnknownObject`

**Comparison Result Tables**:
- `InterfaceComparison` - Interface-specific comparison results
- `ProcessModelComparison` - Process model comparisons with Mermaid diagrams
- `RecordTypeComparison` - Record type comparison results

### Key Architectural Patterns

#### Dependency Injection

All services and repositories are managed by a centralized DI container:

```python
from core.dependency_container import DependencyContainer

# Get singleton container instance
container = DependencyContainer.get_instance()

# Register services and repositories
container.register_service(MyService)
container.register_repository(MyRepository)

# Retrieve instances (lazy initialization)
service = container.get_service(MyService)
repository = container.get_repository(MyRepository)
```

**Benefits**:
- Singleton pattern enforcement
- Lazy initialization
- Easy testing with mock dependencies
- Clear dependency graph


#### Base Classes

**BaseService** - All services inherit from this:

```python
from core.base_service import BaseService

class MyService(BaseService):
    def _initialize_dependencies(self):
        # Lazy dependency initialization
        self.my_repo = self._get_repository(MyRepository)
        self.other_service = self._get_service(OtherService)
    
    def do_something(self):
        # Use dependencies
        data = self.my_repo.find_all()
        result = self.other_service.process(data)
        return result
```

**BaseRepository** - Generic CRUD operations:

```python
from core.base_repository import BaseRepository
from models import MyModel

class MyRepository(BaseRepository[MyModel]):
    def __init__(self):
        super().__init__(MyModel)
    
    # Inherits: create, update, delete, find_by_id, find_all, etc.
    
    def find_by_custom_field(self, value):
        return self.model_class.query.filter_by(custom_field=value).all()
```

#### Exception Hierarchy

```python
NexusGenException (base)
├── ServiceException
│   ├── ValidationException
│   │   └── XMLParsingException
│   └── ThreeWayMergeException
├── RepositoryException
│   └── DatabaseTransactionException
├── TransientException
├── ConcurrencyException
└── ResourceConstraintException
```

#### Repository Pattern

All data access goes through repositories, never direct model access:

```python
# ❌ WRONG - Direct model access
from models import ObjectLookup
obj = ObjectLookup.query.filter_by(uuid=uuid).first()

# ✅ CORRECT - Through repository
from repositories.object_lookup_repository import ObjectLookupRepository
repo = container.get_repository(ObjectLookupRepository)
obj = repo.find_by_uuid(uuid)
```


### Three-Way Merge Workflow Architecture

The three-way merge follows a **10-step transactional workflow**:

```
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Create Session Record                                   │
│ - Generate reference_id (MRG_001, MRG_002, etc.)                │
│ - Set status = 'PROCESSING'                                     │
│ - Begin database transaction                                    │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2-4: Extract All Three Packages                            │
│ - Extract Package A (Base Version)                              │
│ - Extract Package B (Customer Version)                          │
│ - Extract Package C (New Vendor Version)                        │
│ - Parse XML, populate object_lookup (find_or_create)            │
│ - Create package_object_mappings                                │
│ - Store object_versions                                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: Delta Comparison (A→C)                                  │
│ - Compare base to new vendor                                    │
│ - Identify NEW, MODIFIED, DEPRECATED objects                    │
│ - Store in delta_comparison_results (Set D)                     │
│ - This defines the working set                                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 6: Customer Comparison (A→B)                               │
│ - Compare base to customer version                              │
│ - Identify customer modifications                               │
│ - Store in customer_comparison_results (Set E)                  │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 7: Classification (Apply 7 Rules)                          │
│ - For each object in Set D (delta):                             │
│   - Check if in Set E (customer changes)                        │
│   - Apply classification rules 10a-10g                          │
│   - Assign: NO_CONFLICT, CONFLICT, NEW, or DELETED              │
│ - Create Change records in working set                          │
│ - Set display_order for UI                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 8: Persist Detailed Comparisons                            │
│ - Store object-specific comparison data                         │
│ - Interface comparisons (parameters, security)                  │
│ - Process model comparisons (nodes, flows, variables)           │
│ - Record type comparisons (fields, relationships, views)        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 9: Generate Merge Guidance                                 │
│ - Calculate session statistics                                  │
│ - Estimate complexity (LOW, MEDIUM, HIGH)                       │
│ - Estimate time required                                        │
│ - Update session metadata                                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 10: Finalize Session                                       │
│ - Update session status = 'READY'                               │
│ - Commit transaction                                            │
│ - Trigger async AI summary generation (background thread)       │
│ - Return session with reference_id and total_changes            │
└─────────────────────────────────────────────────────────────────┘
```

**Key Characteristics**:
- **Transactional**: All steps 1-10 in a single database transaction
- **Rollback on Error**: Any failure rolls back entire session
- **Idempotent**: Can be retried safely
- **Async AI**: AI summaries generated after commit in background


### Set-Based Classification Logic

The classification engine uses set theory for conflict detection:

```
Set D = Vendor changes (A→C delta)
Set E = Customer changes (A→B delta)

D ∩ E = Objects changed by BOTH vendor and customer
D \ E = Objects changed by vendor ONLY
E \ D = Objects changed by customer ONLY (not in working set)

Classification Rules:

For objects in D ∩ E (both changed):
  - Compare B vs C content
  - If B == C: NO_CONFLICT (same changes)
  - If B != C: CONFLICT (different changes)

For objects in D \ E (vendor only):
  - NO_CONFLICT (safe to merge)

For objects in E \ D (customer only):
  - Not included in working set
  - Customer changes preserved automatically
```

### Critical Design Decisions

#### ❌ NO package_id in object_lookup
The `object_lookup` table is **package-agnostic**. Each unique object (by UUID) is stored exactly once, regardless of how many packages contain it. Package membership is tracked via `package_object_mappings`.

#### ❌ NO duplicate objects
Always use `ObjectLookupRepository.find_or_create()` to prevent duplicates:

```python
# This ensures idempotence
object_lookup = self.object_lookup_repo.find_or_create(
    uuid=obj_uuid,
    name=obj_name,
    object_type=obj_type,
    description=obj_description
)
```

#### ❌ NO customer-only objects in working set
The working set (`changes` table) contains **ONLY** objects from the delta (A→C comparison). Customer-only changes (E \ D) are not included because they don't conflict with vendor changes.

#### ✅ Delta-Driven Working Set
```sql
-- This should ALWAYS be true:
SELECT COUNT(*) FROM delta_comparison_results WHERE session_id = X
= 
SELECT COUNT(*) FROM changes WHERE session_id = X
```

#### ✅ Only 4 Classifications
- `NO_CONFLICT` - Auto-merge safe
- `CONFLICT` - Manual review required
- `NEW` - New vendor object
- `DELETED` - Customer removed, vendor modified

Old classifications removed: `CUSTOMER_ONLY`, `REMOVED_BUT_CUSTOMIZED`


---

## 🛠️ Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.8+ | Core programming language |
| **Flask** | 2.3+ | Web framework |
| **SQLAlchemy** | 3.0+ | ORM and database toolkit |
| **SQLite** | 3.x | Database (with connection pooling) |
| **boto3** | 1.34+ | AWS SDK for Bedrock integration |
| **python-docx** | 1.2+ | Word document processing |
| **openpyxl** | 3.1+ | Excel file generation |
| **requests** | 2.31+ | HTTP client for external APIs |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Bootstrap** | 5.3 | UI framework |
| **Font Awesome** | 6.x | Icon library |
| **Vanilla JavaScript** | ES6+ | Client-side interactivity |
| **Jinja2** | 3.x | Server-side templating |

### AI Services

| Service | Purpose |
|---------|---------|
| **AWS Bedrock** | RAG (Retrieval-Augmented Generation) |
| **Amazon Q CLI** | AI agent for document processing |
| **Knowledge Base** | WAQ6NJLGKN (Bedrock KB) |

### Development & Testing

| Tool | Version | Purpose |
|------|---------|---------|
| **pytest** | 7.4+ | Testing framework |
| **pytest-cov** | 4.1+ | Code coverage |
| **pytest-flask** | 1.3+ | Flask testing utilities |
| **hypothesis** | 6.92+ | Property-based testing |

### Database Features

- **Connection Pooling**: 10 connections, max overflow 20
- **Pool Recycling**: 1-hour connection lifetime
- **Pre-ping**: Connection health checks
- **Transaction Management**: ACID compliance
- **Cascade Deletes**: Referential integrity enforcement


---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** installed
- **AWS CLI** configured with appropriate permissions
- **Amazon Q CLI** installed and configured
- **Git** for repository cloning

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd nexusgen
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
export AWS_REGION=us-east-1
export BEDROCK_KB_ID=WAQ6NJLGKN
export SECRET_KEY=your-secret-key-here
```

5. **Initialize database**
```bash
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

6. **Run the application**
```bash
python app.py
```

The application will start on `http://localhost:5000`

### First-Time Setup

1. **Verify Installation**
```bash
# Check if app is running
curl -s http://localhost:5000/ | head -5
```

2. **Access the Dashboard**
Open your browser to `http://localhost:5000`

3. **Test Document Upload**
- Navigate to "Spec Breakdown"
- Upload a sample document
- Verify processing completes

4. **Test Three-Way Merge**
- Navigate to "Merge Assistant"
- Upload three test packages from `applicationArtifacts/Three Way Testing Files/V2/`
- Verify session creation and change detection


---

## 🗄️ Database Schema

### Schema Overview

NexusGen uses a comprehensive database schema with 50+ tables organized into logical groups:

```
Database: instance/docflow.db (SQLite)

Table Groups:
├── Application Core (3 tables)
│   ├── requests
│   ├── chat_sessions
│   └── merge_sessions
│
├── Three-Way Merge Core (7 tables)
│   ├── packages
│   ├── object_lookup (GLOBAL REGISTRY)
│   ├── package_object_mappings (JUNCTION)
│   ├── delta_comparison_results
│   ├── customer_comparison_results
│   ├── changes (WORKING SET)
│   └── object_versions
│
├── Object-Specific Tables (40+ tables)
│   ├── interfaces + interface_parameters + interface_security
│   ├── expression_rules + expression_rule_inputs
│   ├── process_models + nodes + flows + variables
│   ├── record_types + fields + relationships + views + actions
│   ├── cdts + cdt_fields
│   ├── integrations
│   ├── web_apis
│   ├── sites
│   ├── groups
│   ├── constants
│   ├── connected_systems
│   ├── data_stores
│   └── unknown_objects
│
└── Comparison Results (3 tables)
    ├── interface_comparisons
    ├── process_model_comparisons
    └── record_type_comparisons
```

### Key Tables

#### requests
Tracks all document processing requests (breakdown, verify, create, convert):

```sql
CREATE TABLE requests (
    id INTEGER PRIMARY KEY,
    action_type VARCHAR(20) NOT NULL,      -- 'breakdown', 'verify', 'create', 'convert'
    filename VARCHAR(255),                 -- For file uploads
    input_text TEXT,                       -- For pasted content
    status VARCHAR(20) DEFAULT 'processing', -- 'processing', 'completed', 'error'
    rag_query TEXT,                        -- Query sent to RAG
    rag_response TEXT,                     -- RAG API response
    final_output TEXT,                     -- Processed result (JSON)
    reference_id VARCHAR(20),              -- RQ_BR_001, RQ_VR_001, etc.
    agent_name VARCHAR(50),                -- breakdown-agent, verify-agent, etc.
    model_name VARCHAR(100),               -- amazon.nova-pro-v1:0
    parameters TEXT,                       -- JSON model parameters
    total_time INTEGER,                    -- Processing time in seconds
    step_durations TEXT,                   -- JSON step timings
    raw_agent_output TEXT,                 -- Raw Q agent response
    q_agent_prompt TEXT,                   -- Prompt sent to Q agent
    rag_similarity_avg FLOAT,              -- Average RAG similarity score
    json_valid BOOLEAN DEFAULT TRUE,       -- JSON validity flag
    error_log TEXT,                        -- Error messages
    export_path VARCHAR(500),              -- Excel file path (breakdown only)
    created_at DATETIME,
    updated_at DATETIME
);
```


#### merge_sessions
Tracks three-way merge analysis sessions:

```sql
CREATE TABLE merge_sessions (
    id INTEGER PRIMARY KEY,
    reference_id VARCHAR(50) UNIQUE NOT NULL,  -- MRG_001, MRG_002, etc.
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
        -- 'processing', 'ready', 'in_progress', 'completed', 'error'
    total_changes INTEGER DEFAULT 0,
    reviewed_count INTEGER DEFAULT 0,
    skipped_count INTEGER DEFAULT 0,
    estimated_complexity VARCHAR(20),          -- 'LOW', 'MEDIUM', 'HIGH'
    estimated_time_hours FLOAT,
    created_at DATETIME,
    updated_at DATETIME
);
```

#### object_lookup (CRITICAL: Global Registry)
**Package-agnostic** global registry of all unique objects:

```sql
CREATE TABLE object_lookup (
    id INTEGER PRIMARY KEY,
    uuid VARCHAR(255) UNIQUE NOT NULL,         -- Appian object UUID
    name VARCHAR(500) NOT NULL,
    object_type VARCHAR(50) NOT NULL,          -- 'Interface', 'Process Model', etc.
    description TEXT,
    created_at DATETIME
    
    -- CRITICAL: NO package_id column!
    -- This table is package-agnostic
);

CREATE UNIQUE INDEX idx_object_lookup_uuid ON object_lookup(uuid);
CREATE INDEX idx_object_lookup_name ON object_lookup(name);
CREATE INDEX idx_object_lookup_type ON object_lookup(object_type);
```

#### package_object_mappings (Junction Table)
Tracks which objects belong to which packages:

```sql
CREATE TABLE package_object_mappings (
    id INTEGER PRIMARY KEY,
    package_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    created_at DATETIME,
    
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    UNIQUE (package_id, object_id)
);

CREATE INDEX idx_pom_package_object ON package_object_mappings(package_id, object_id);
```

#### delta_comparison_results (Set D: A→C)
Vendor changes from base to new version:

```sql
CREATE TABLE delta_comparison_results (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    change_category VARCHAR(20) NOT NULL,      -- 'NEW', 'MODIFIED', 'DEPRECATED'
    change_type VARCHAR(20) NOT NULL,          -- 'ADDED', 'MODIFIED', 'REMOVED'
    version_changed BOOLEAN DEFAULT FALSE,
    content_changed BOOLEAN DEFAULT FALSE,
    created_at DATETIME,
    
    FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    UNIQUE (session_id, object_id)
);

CREATE INDEX idx_delta_category ON delta_comparison_results(session_id, change_category);
```

#### customer_comparison_results (Set E: A→B)
Customer changes from base to customized version:

```sql
CREATE TABLE customer_comparison_results (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    change_category VARCHAR(20) NOT NULL,      -- 'NEW', 'MODIFIED', 'DEPRECATED'
    change_type VARCHAR(20) NOT NULL,          -- 'ADDED', 'MODIFIED', 'REMOVED'
    version_changed BOOLEAN DEFAULT FALSE,
    content_changed BOOLEAN DEFAULT FALSE,
    created_at DATETIME,
    
    FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    UNIQUE (session_id, object_id)
);

CREATE INDEX idx_customer_comparison_category 
    ON customer_comparison_results(session_id, change_category);
```


#### changes (Working Set)
Classified changes for user review:

```sql
CREATE TABLE changes (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,                -- Primary object reference
    classification VARCHAR(50) NOT NULL,       -- 'NO_CONFLICT', 'CONFLICT', 'NEW', 'DELETED'
    change_type VARCHAR(20),
    vendor_change_type VARCHAR(20),            -- 'ADDED', 'MODIFIED', 'REMOVED'
    customer_change_type VARCHAR(20),          -- 'ADDED', 'MODIFIED', 'REMOVED'
    display_order INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',      -- 'pending', 'reviewed', 'skipped'
    notes TEXT,
    reviewed_at DATETIME,
    reviewed_by VARCHAR(255),
    
    -- Dual Object Tracking (for customer-only objects)
    vendor_object_id INTEGER,
    customer_object_id INTEGER,
    
    -- AI Summary fields
    ai_summary TEXT,
    ai_summary_status VARCHAR(20) DEFAULT 'pending',
        -- 'pending', 'processing', 'completed', 'failed'
    ai_summary_generated_at DATETIME,
    
    created_at DATETIME,
    
    FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    FOREIGN KEY (vendor_object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    FOREIGN KEY (customer_object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
);

CREATE INDEX idx_change_session_classification ON changes(session_id, classification);
CREATE INDEX idx_change_session_object ON changes(session_id, object_id);
CREATE INDEX idx_change_session_order ON changes(session_id, display_order);
CREATE INDEX idx_change_session_status ON changes(session_id, status);
```

#### object_versions
Package-specific versions of objects:

```sql
CREATE TABLE object_versions (
    id INTEGER PRIMARY KEY,
    object_id INTEGER NOT NULL,
    package_id INTEGER NOT NULL,
    version_uuid VARCHAR(255),
    sail_code TEXT,
    fields TEXT,                               -- JSON string
    properties TEXT,                           -- JSON string
    raw_xml TEXT,
    created_at DATETIME,
    
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    UNIQUE (object_id, package_id)
);

CREATE INDEX idx_objver_object_package ON object_versions(object_id, package_id);
```

### Database Relationships

```
merge_sessions (1) ──→ (N) packages
merge_sessions (1) ──→ (N) delta_comparison_results
merge_sessions (1) ──→ (N) customer_comparison_results
merge_sessions (1) ──→ (N) changes

packages (1) ──→ (N) package_object_mappings
packages (1) ──→ (N) object_versions

object_lookup (1) ──→ (N) package_object_mappings
object_lookup (1) ──→ (N) object_versions
object_lookup (1) ──→ (N) delta_comparison_results
object_lookup (1) ──→ (N) customer_comparison_results
object_lookup (1) ──→ (N) changes

object_lookup (1) ──→ (N) interfaces
object_lookup (1) ──→ (N) process_models
object_lookup (1) ──→ (N) expression_rules
... (40+ object-specific tables)
```

### Database Validation Queries

```sql
-- Check for duplicate objects (should return 0)
SELECT uuid, COUNT(*) as count 
FROM object_lookup 
GROUP BY uuid 
HAVING count > 1;

-- Verify delta-driven working set (counts should match)
SELECT 
    (SELECT COUNT(*) FROM delta_comparison_results WHERE session_id = 1) as delta_count,
    (SELECT COUNT(*) FROM changes WHERE session_id = 1) as change_count;

-- Check referential integrity
SELECT COUNT(*) FROM changes c
LEFT JOIN object_lookup o ON c.object_id = o.id
WHERE o.id IS NULL;  -- Should return 0
```


---

## 💻 Development Guide

### Project Structure

```
nexusgen/
├── app.py                          # Application entry point
├── config.py                       # Configuration management
├── models.py                       # SQLAlchemy ORM models (50+ tables)
├── requirements.txt                # Production dependencies
├── test_requirements.txt           # Testing dependencies
├── pytest.ini                      # Pytest configuration
│
├── controllers/                    # Flask route handlers
│   ├── breakdown_controller.py
│   ├── verify_controller.py
│   ├── create_controller.py
│   ├── convert_controller.py
│   ├── chat_controller.py
│   ├── merge_assistant_controller.py
│   ├── process_controller.py
│   ├── settings_controller.py
│   └── debug_controller.py
│
├── services/                       # Business logic layer
│   ├── ai/                         # AI service integrations
│   │   ├── bedrock_service.py
│   │   └── q_agent_service.py
│   ├── parsers/                    # XML parsers for Appian objects
│   │   ├── xml_parser_factory.py
│   │   ├── interface_parser.py
│   │   ├── process_model_parser.py
│   │   └── ... (12+ parsers)
│   ├── request/                    # Document processing
│   │   ├── request_service.py
│   │   ├── file_service.py
│   │   └── document_service.py
│   ├── schemas/                    # JSON schemas
│   │   └── appian_public_functions.json
│   ├── three_way_merge_orchestrator.py
│   ├── package_extraction_service.py
│   ├── delta_comparison_service.py
│   ├── customer_comparison_service.py
│   ├── classification_service.py
│   ├── merge_guidance_service.py
│   ├── merge_summary_service.py
│   ├── comparison_persistence_service.py
│   ├── comparison_retrieval_service.py
│   ├── change_navigation_service.py
│   ├── change_action_service.py
│   ├── session_statistics_service.py
│   ├── report_generation_service.py
│   ├── sail_formatter.py
│   ├── sail_diff_service.py
│   └── ... (utility services)
│
├── repositories/                   # Data access layer
│   ├── comparison/                 # Comparison-specific repos
│   │   ├── interface_comparison_repository.py
│   │   ├── process_model_comparison_repository.py
│   │   └── record_type_comparison_repository.py
│   ├── request_repository.py
│   ├── chat_session_repository.py
│   ├── change_repository.py
│   ├── object_lookup_repository.py
│   ├── package_object_mapping_repository.py
│   ├── delta_comparison_repository.py
│   ├── customer_comparison_repository.py
│   └── ... (40+ object-specific repositories)
│
├── domain/                         # Domain layer (pure business logic)
│   ├── entities.py                 # Immutable business entities
│   ├── enums.py                    # Type-safe enumerations
│   └── comparison_strategies.py   # Pluggable comparison strategies
│
├── core/                           # Infrastructure layer
│   ├── dependency_container.py    # DI container
│   ├── base_service.py            # Base class for services
│   ├── base_repository.py         # Generic CRUD operations
│   ├── exceptions.py              # Exception hierarchy
│   ├── logger.py                  # Centralized logging
│   └── cache.py                   # Caching utilities
│
├── templates/                      # Jinja2 templates
│   ├── base.html                  # Base template
│   ├── dashboard.html             # Main dashboard
│   ├── breakdown/                 # Spec breakdown pages
│   ├── verify/                    # Design verification pages
│   ├── create/                    # Design creation pages
│   ├── convert/                   # SQL conversion pages
│   ├── chat/                      # AI chat interface
│   ├── merge/                     # Three-way merge pages
│   │   ├── upload.html
│   │   ├── sessions.html
│   │   ├── summary.html
│   │   ├── workflow.html
│   │   ├── change_detail.html
│   │   └── comparisons/           # Object-specific comparison views
│   ├── process/                   # Process history pages
│   ├── settings/                  # Settings pages
│   └── errors/                    # Error pages
│
├── static/                         # Static assets
│   ├── css/
│   │   └── docflow.css            # Custom styling
│   └── js/
│       ├── main.js                # Core JavaScript
│       ├── sail-highlighter.js    # SAIL syntax highlighting
│       ├── settings.js            # Settings management
│       └── upload.js              # File upload handling
│
├── tests/                          # Comprehensive test suite
│   ├── conftest.py                # Pytest fixtures
│   ├── base_test.py               # Base test class
│   ├── test_three_way_merge_orchestrator.py
│   ├── test_classification_service.py
│   ├── test_integration_end_to_end.py
│   └── ... (30+ test files)
│
├── migrations/                     # Database migrations
│   ├── migrations_001_three_way_merge_schema.py
│   ├── migrations_002_ui_enhancement.py
│   ├── migrations_003_data_completeness.py
│   └── migrations_004_add_package_id_to_objects.py
│
├── applicationArtifacts/           # Test data and samples
│   ├── Three Way Testing Files/
│   │   └── V2/
│   │       ├── Test Application - Base Version.zip
│   │       ├── Test Application Customer Version.zip
│   │       └── Test Application Vendor New Version.zip
│   ├── ObjectSpecificXml/
│   └── SQL Conversion Support Files/
│
├── instance/                       # Instance-specific files
│   └── docflow.db                 # SQLite database
│
├── logs/                           # Application logs
│   ├── nexusgen.log
│   ├── merge_assistant.log
│   └── settings_service.log
│
├── uploads/                        # Temporary file uploads
│   ├── merge/                     # Merge package uploads
│   └── conversions/               # SQL conversion files
│
├── outputs/                        # Generated outputs
│   ├── reports/                   # Excel/PDF reports
│   ├── conversions/               # Converted SQL files
│   └── backups/                   # Backup files
│
└── prompts/                        # AI prompt templates
```


### Development Workflow

#### Starting the Application

**⚠️ CRITICAL: Always check for existing instances first!**

```bash
# 1. Check if app is already running
lsof -i :5000
ps aux | grep "app.py"
curl -s http://localhost:5000/ | head -5

# 2. If running, stop it first
lsof -ti :5000 | xargs kill -9

# 3. Start the app
python app.py

# OR use background process for development
# (if using Kiro IDE)
controlBashProcess(action="start", command="python app.py")
getProcessOutput(processId=<id>, lines=50)
```

#### Database Management

```bash
# Create three-way merge schema
python create_three_way_merge_schema.py

# Verify schema structure
python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    # Check for duplicates (should return 0)
    result = db.session.execute('''
        SELECT uuid, COUNT(*) as count 
        FROM object_lookup 
        GROUP BY uuid 
        HAVING count > 1
    ''')
    print(f'Duplicates: {len(result.fetchall())}')
"

# List all merge sessions
python list_sessions.py

# Clean up old sessions
python delete_old_merge_sessions.py
```

#### Using the Dependency Container

```python
from core.dependency_container import DependencyContainer

# Get singleton container instance
container = DependencyContainer.get_instance()

# Get service instances
orchestrator = container.get_service(ThreeWayMergeOrchestrator)
classification_service = container.get_service(ClassificationService)

# Get repository instances
change_repo = container.get_repository(ChangeRepository)
object_lookup_repo = container.get_repository(ObjectLookupRepository)

# Use services
session = orchestrator.create_merge_session(
    base_zip_path="path/to/base.zip",
    customized_zip_path="path/to/customized.zip",
    new_vendor_zip_path="path/to/new_vendor.zip"
)

# Get session status
status = orchestrator.get_session_status(session.reference_id)
print(f"Status: {status['status']}, Changes: {status['total_changes']}")
```

#### Database Inspection

```python
from models import db, MergeSession, ObjectLookup, Change
from app import create_app

app = create_app()
with app.app_context():
    # Check sessions
    sessions = MergeSession.query.all()
    for session in sessions:
        print(f"{session.reference_id}: {session.status}")
    
    # Check objects
    objects = ObjectLookup.query.limit(10).all()
    for obj in objects:
        print(f"{obj.uuid}: {obj.name} ({obj.object_type})")
    
    # Check changes by classification
    changes = Change.query.filter_by(
        session_id=1,
        classification='CONFLICT'
    ).all()
    for change in changes:
        print(f"{change.object.name}: {change.classification}")
```

#### Adding a New Service

1. **Create service class** in `services/`:

```python
from core.base_service import BaseService

class MyNewService(BaseService):
    def _initialize_dependencies(self):
        # Lazy dependency initialization
        self.my_repo = self._get_repository(MyRepository)
        self.other_service = self._get_service(OtherService)
    
    def do_something(self, param):
        # Business logic here
        data = self.my_repo.find_by_param(param)
        result = self.other_service.process(data)
        return result
```

2. **Register in DI container** in `app.py`:

```python
def _register_services(container):
    # ... existing registrations
    from services.my_new_service import MyNewService
    container.register_service(MyNewService)
```

3. **Use in controllers**:

```python
from core.dependency_container import DependencyContainer

container = DependencyContainer.get_instance()
my_service = container.get_service(MyNewService)
result = my_service.do_something(param)
```


#### Adding a New Repository

1. **Create repository class** in `repositories/`:

```python
from core.base_repository import BaseRepository
from models import MyModel

class MyRepository(BaseRepository[MyModel]):
    def __init__(self):
        super().__init__(MyModel)
    
    # Inherits: create, update, delete, find_by_id, find_all
    
    def find_by_custom_field(self, value):
        return self.model_class.query.filter_by(
            custom_field=value
        ).all()
    
    def find_with_relationships(self, id):
        return self.model_class.query\
            .options(db.joinedload(MyModel.related_objects))\
            .filter_by(id=id)\
            .first()
```

2. **Register in DI container** in `app.py`:

```python
def _register_repositories(container):
    # ... existing registrations
    from repositories.my_repository import MyRepository
    container.register_repository(MyRepository)
```

#### Adding a New Object Parser

1. **Create parser class** in `services/parsers/`:

```python
from services.parsers.base_parser import BaseParser

class MyObjectParser(BaseParser):
    def parse(self, xml_element, package_id, object_lookup_id):
        # Extract data from XML
        uuid = xml_element.get('uuid')
        name = xml_element.findtext('.//name')
        
        # Create object-specific record
        my_object = MyObject(
            object_id=object_lookup_id,
            package_id=package_id,
            uuid=uuid,
            name=name,
            # ... other fields
        )
        
        db.session.add(my_object)
        return my_object
```

2. **Register in parser factory** in `services/parsers/xml_parser_factory.py`:

```python
def get_parser(object_type: str) -> BaseParser:
    parsers = {
        # ... existing parsers
        'My Object Type': MyObjectParser(),
    }
    return parsers.get(object_type, UnknownObjectParser())
```


---

## 🧪 Testing

### Test Framework

NexusGen uses **pytest** with property-based testing using real Appian packages (no mocking of package data).

### Test Configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    property: Property-based tests
    slow: Slow-running tests
```

### Running Tests

**⚠️ MANDATORY: Always use the redirect-and-cat pattern!**

Direct pytest execution returns "TY=not a tty" error. Use this pattern:

```bash
# Run all tests
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run specific test file
python -m pytest tests/test_three_way_merge_orchestrator.py > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run with verbose output
python -m pytest -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run specific test by name
python -m pytest tests/test_classification_service.py::TestClassificationService::test_rule_10a -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run tests matching a pattern
python -m pytest -k "test_property" -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run with coverage
python -m pytest --cov=services --cov-report=html > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

**❌ NEVER USE THESE (THEY WILL FAIL):**
```bash
pytest tests/test_file.py                    # ❌ WRONG
python -m pytest tests/test_file.py          # ❌ WRONG
python -m pytest tests/test_file.py -v       # ❌ WRONG
```

### Test Categories

#### Unit Tests
Test individual services and repositories in isolation:

```bash
python -m pytest tests/test_classification_service.py > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
python -m pytest tests/test_delta_comparison_service.py > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
python -m pytest tests/test_repositories.py > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

#### Integration Tests
Test complete workflows end-to-end:

```bash
python -m pytest tests/test_integration_end_to_end.py > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
python -m pytest tests/test_merge_assistant_controller_integration.py > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

#### Property-Based Tests
Verify invariants across all test scenarios:

```bash
python -m pytest tests/test_classification_validation.py > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

**18 Properties Tested**:
1. No duplicate objects in object_lookup
2. Package-object mappings are consistent
3. Delta-driven working set (delta_count == change_count)
4. All delta objects are classified
5. NEW objects detected correctly
6. DEPRECATED objects detected correctly
7. MODIFIED objects detected correctly
8-14. All 7 classification rules (10a-10g)
15. Referential integrity maintained
16. find_or_create idempotence
17. Transaction rollback on error
18. Async AI summary generation


### Test Data

Real Appian packages located in `applicationArtifacts/Three Way Testing Files/V2/`:

- `Test Application - Base Version.zip` (Package A)
- `Test Application Customer Version.zip` (Package B)
- `Test Application Vendor New Version.zip` (Package C)

**Known Test UUIDs**:
```python
PROCESS_MODEL_UUID_1 = "de199b3f-b072-4438-9508-3b6594827eaf"
PROCESS_MODEL_UUID_2 = "2c8de7e9-23b9-40d6-afc2-233a963832be"
RECORD_TYPE_UUID = "57318b79-0bfd-45c4-a07e-ceae8277e0fb"
```

### Writing Tests

#### Example Unit Test

```python
from tests.base_test import BaseTest
from services.classification_service import ClassificationService

class TestClassificationService(BaseTest):
    def test_rule_10a_vendor_only_modified(self):
        """Rule 10a: MODIFIED in delta AND not modified by customer → NO_CONFLICT"""
        # Arrange
        service = self.container.get_service(ClassificationService)
        
        # Act
        classification = service.classify_change(
            delta_category='MODIFIED',
            customer_category=None,
            b_content='original',
            c_content='modified'
        )
        
        # Assert
        assert classification == 'NO_CONFLICT'
```

#### Example Integration Test

```python
from tests.base_test import BaseTest

class TestThreeWayMergeIntegration(BaseTest):
    def test_complete_workflow(self):
        """Test complete three-way merge workflow"""
        # Arrange
        orchestrator = self.container.get_service(ThreeWayMergeOrchestrator)
        
        # Act
        session = orchestrator.create_merge_session(
            base_zip_path=self.BASE_ZIP,
            customized_zip_path=self.CUSTOMIZED_ZIP,
            new_vendor_zip_path=self.NEW_VENDOR_ZIP
        )
        
        # Assert
        assert session.status == 'ready'
        assert session.total_changes > 0
        assert session.reference_id.startswith('MRG_')
```

### Test Fixtures

Common fixtures in `tests/conftest.py`:

```python
@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def db_session(app):
    """Create database session"""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()
```


---

## 📡 API Documentation

### Three-Way Merge API Endpoints

#### POST /merge/upload
Upload three packages and create merge session.

**Request**:
```bash
curl -X POST http://localhost:5000/merge/upload \
  -F "base_package=@base.zip" \
  -F "customized_package=@customized.zip" \
  -F "new_vendor_package=@new_vendor.zip"
```

**Response**:
```json
{
  "success": true,
  "reference_id": "MRG_001",
  "total_changes": 42,
  "status": "ready"
}
```

#### GET /merge/sessions
List all merge sessions.

**Response**:
```json
{
  "sessions": [
    {
      "reference_id": "MRG_001",
      "status": "ready",
      "total_changes": 42,
      "reviewed_count": 10,
      "created_at": "2025-12-03T10:30:00"
    }
  ]
}
```

#### GET /merge/{reference_id}/summary
Get session summary with statistics.

**Response**:
```json
{
  "reference_id": "MRG_001",
  "status": "ready",
  "total_changes": 42,
  "by_classification": {
    "NO_CONFLICT": 25,
    "CONFLICT": 10,
    "NEW": 5,
    "DELETED": 2
  },
  "by_object_type": {
    "Interface": 15,
    "Process Model": 10,
    "Expression Rule": 8,
    "Record Type": 5,
    "CDT": 4
  },
  "estimated_complexity": "MEDIUM",
  "estimated_time_hours": 4.5
}
```

#### GET /merge/{reference_id}/changes
Get paginated list of changes with filtering.

**Query Parameters**:
- `classification` - Filter by classification (NO_CONFLICT, CONFLICT, NEW, DELETED)
- `object_type` - Filter by object type
- `status` - Filter by review status (pending, reviewed, skipped)
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)

**Response**:
```json
{
  "changes": [
    {
      "id": 1,
      "object_name": "My Interface",
      "object_type": "Interface",
      "classification": "CONFLICT",
      "vendor_change_type": "MODIFIED",
      "customer_change_type": "MODIFIED",
      "status": "pending",
      "ai_summary": "Both vendor and customer modified the interface..."
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 42,
    "pages": 3
  }
}
```

#### GET /merge/{reference_id}/changes/{change_id}
Get detailed change information.

**Response**:
```json
{
  "change": {
    "id": 1,
    "object_name": "My Interface",
    "object_type": "Interface",
    "classification": "CONFLICT",
    "vendor_change_type": "MODIFIED",
    "customer_change_type": "MODIFIED",
    "status": "pending",
    "ai_summary": "Both vendor and customer modified...",
    "versions": {
      "base": {
        "version_uuid": "abc-123",
        "sail_code": "..."
      },
      "customized": {
        "version_uuid": "def-456",
        "sail_code": "..."
      },
      "new_vendor": {
        "version_uuid": "ghi-789",
        "sail_code": "..."
      }
    }
  }
}
```

#### POST /merge/{reference_id}/changes/{change_id}/review
Mark change as reviewed.

**Request**:
```json
{
  "status": "reviewed",
  "notes": "Reviewed and approved for merge"
}
```

**Response**:
```json
{
  "success": true,
  "change_id": 1,
  "status": "reviewed"
}
```

#### POST /merge/{reference_id}/changes/{change_id}/skip
Skip change review.

**Response**:
```json
{
  "success": true,
  "change_id": 1,
  "status": "skipped"
}
```


### Document Processing API Endpoints

#### POST /breakdown/upload
Upload document for spec breakdown.

**Request**:
```bash
curl -X POST http://localhost:5000/breakdown/upload \
  -F "file=@requirements.pdf"
```

**Response**:
```json
{
  "success": true,
  "reference_id": "RQ_BR_001",
  "status": "processing"
}
```

#### GET /breakdown/results/{reference_id}
Get breakdown results.

**Response**:
```json
{
  "reference_id": "RQ_BR_001",
  "status": "completed",
  "user_stories": [
    {
      "id": "US-001",
      "title": "User Login",
      "description": "As a user, I want to log in...",
      "acceptance_criteria": [
        "User can enter username and password",
        "System validates credentials"
      ]
    }
  ],
  "export_path": "/outputs/RQ_BR_001.xlsx"
}
```

#### POST /verify
Verify design document.

**Request**:
```json
{
  "design_text": "Design document content..."
}
```

**Response**:
```json
{
  "reference_id": "RQ_VR_001",
  "status": "completed",
  "validation_results": {
    "is_valid": true,
    "confidence_score": 0.92,
    "recommendations": [
      "Consider adding error handling section",
      "Include performance requirements"
    ]
  }
}
```

#### POST /create
Create design document from acceptance criteria.

**Request**:
```json
{
  "acceptance_criteria": "AC1: User can log in\nAC2: System validates..."
}
```

**Response**:
```json
{
  "reference_id": "RQ_CR_001",
  "status": "completed",
  "design_document": {
    "overview": "...",
    "architecture": "...",
    "components": [...]
  }
}
```

#### POST /convert
Convert SQL between dialects.

**Request**:
```json
{
  "sql_text": "SELECT * FROM users WHERE id = 1",
  "source_dialect": "mariadb",
  "target_dialect": "oracle"
}
```

**Response**:
```json
{
  "reference_id": "RQ_CV_001",
  "status": "completed",
  "converted_sql": "SELECT * FROM users WHERE id = 1",
  "conversion_notes": [
    "No changes required for this query"
  ]
}
```


---

## ⚙️ Configuration

### Environment Variables

```bash
# AWS Configuration
AWS_REGION=us-east-1                    # AWS region for Bedrock
BEDROCK_KB_ID=WAQ6NJLGKN               # Bedrock Knowledge Base ID

# Application Settings
SECRET_KEY=your-production-secret-key   # Flask secret key
FLASK_ENV=production                    # Environment (development/production)
DEBUG=False                             # Debug mode

# Database Configuration
SQLALCHEMY_DATABASE_URI=sqlite:///instance/docflow.db  # Database URI

# File Upload Limits
MAX_CONTENT_LENGTH=209715200            # 200MB for Appian packages
MERGE_MAX_FILE_SIZE=104857600           # 100MB for merge uploads

# Session Configuration
MERGE_SESSION_TIMEOUT=86400             # 24 hours in seconds

# Data Source
DATA_SOURCE=BEDROCK                     # BEDROCK, LOCAL, or MOCK
```

### Configuration File

The `config.py` file provides centralized configuration:

```python
from config import Config

# Access configuration values
secret = Config.SECRET_KEY
upload_dir = Config.UPLOAD_FOLDER
max_size = Config.MAX_CONTENT_LENGTH

# Initialize directories
Config.init_directories()

# Validate configuration
is_valid, errors = Config.validate()
if not is_valid:
    for error in errors:
        print(f"Configuration error: {error}")

# Check environment
if Config.is_production():
    # Use production settings
    pass
```

### Database Configuration

**Connection Pooling** (Requirement 11.5):

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,              # Number of connections in pool
    'pool_recycle': 3600,         # Recycle connections after 1 hour
    'pool_pre_ping': True,        # Verify connections before use
    'max_overflow': 20,           # Max connections beyond pool_size
    'pool_timeout': 30,           # Timeout for getting connection
}
```

### Logging Configuration

Centralized logging in `core/logger.py`:

```python
from core.logger import get_merge_logger, get_app_logger

# Get logger for merge operations
merge_logger = get_merge_logger()
merge_logger.info("Processing merge session")

# Get logger for general app operations
app_logger = get_app_logger()
app_logger.error("An error occurred", exc_info=True)
```

**Log Files**:
- `logs/nexusgen.log` - General application logs
- `logs/merge_assistant.log` - Three-way merge logs
- `logs/settings_service.log` - Settings management logs

**Log Rotation**:
- Max file size: 10MB
- Backup count: 5 files
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`


---

## 🚀 Deployment

### Production Deployment

#### Prerequisites

- Python 3.8+ installed on production server
- AWS credentials configured
- Amazon Q CLI installed
- Sufficient disk space for database and uploads

#### Deployment Steps

1. **Clone repository**
```bash
git clone <repository-url>
cd nexusgen
```

2. **Set up virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
export AWS_REGION=us-east-1
export BEDROCK_KB_ID=WAQ6NJLGKN
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
export FLASK_ENV=production
export DEBUG=False
```

5. **Initialize database**
```bash
python -c "from app import create_app; from models import db; app = create_app(); app.app_context().push(); db.create_all()"
```

6. **Run with production server**
```bash
# Using Gunicorn (recommended)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Or using waitress
pip install waitress
waitress-serve --port=5000 app:app
```

#### Using Gunicorn

Create `gunicorn_config.py`:

```python
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 300
keepalive = 2
errorlog = "logs/gunicorn_error.log"
accesslog = "logs/gunicorn_access.log"
loglevel = "info"
```

Run with:
```bash
gunicorn -c gunicorn_config.py app:app
```

#### Using systemd (Linux)

Create `/etc/systemd/system/nexusgen.service`:

```ini
[Unit]
Description=NexusGen Application
After=network.target

[Service]
Type=notify
User=nexusgen
Group=nexusgen
WorkingDirectory=/opt/nexusgen
Environment="PATH=/opt/nexusgen/.venv/bin"
Environment="AWS_REGION=us-east-1"
Environment="BEDROCK_KB_ID=WAQ6NJLGKN"
Environment="SECRET_KEY=your-secret-key"
ExecStart=/opt/nexusgen/.venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable nexusgen
sudo systemctl start nexusgen
sudo systemctl status nexusgen
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p instance logs uploads outputs

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  nexusgen:
    build: .
    ports:
      - "5000:5000"
    environment:
      - AWS_REGION=us-east-1
      - BEDROCK_KB_ID=WAQ6NJLGKN
      - SECRET_KEY=${SECRET_KEY}
      - FLASK_ENV=production
    volumes:
      - ./instance:/app/instance
      - ./logs:/app/logs
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
    restart: unless-stopped
```

Deploy:
```bash
docker-compose up -d
```

### Nginx Reverse Proxy

Create `/etc/nginx/sites-available/nexusgen`:

```nginx
server {
    listen 80;
    server_name nexusgen.example.com;

    client_max_body_size 200M;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    location /static {
        alias /opt/nexusgen/static;
        expires 30d;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/nexusgen /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Health Checks

Create health check endpoint in `app.py`:

```python
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'version': '6.0.0',
        'database': 'connected'
    }), 200
```

Monitor:
```bash
curl http://localhost:5000/health
```

### Backup Strategy

#### Database Backup

```bash
#!/bin/bash
# backup_db.sh

BACKUP_DIR="/backups/nexusgen"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_PATH="instance/docflow.db"

mkdir -p $BACKUP_DIR
cp $DB_PATH "$BACKUP_DIR/docflow_$TIMESTAMP.db"

# Keep only last 30 days
find $BACKUP_DIR -name "docflow_*.db" -mtime +30 -delete
```

Schedule with cron:
```bash
0 2 * * * /opt/nexusgen/backup_db.sh
```

#### Application Backup

```bash
#!/bin/bash
# backup_app.sh

BACKUP_DIR="/backups/nexusgen"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

tar -czf "$BACKUP_DIR/nexusgen_$TIMESTAMP.tar.gz" \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    /opt/nexusgen

# Keep only last 7 days
find $BACKUP_DIR -name "nexusgen_*.tar.gz" -mtime +7 -delete
```


---

## 🎨 UI/Frontend

### Design System

#### Color Palette

**Primary Colors**:
- Purple: `#8b5cf6` - Primary actions, highlights
- Teal: `#06b6d4` - Secondary actions, accents
- Dark Background: `#1a1a2e` - Main background
- Card Background: `#16213e` - Card/panel background

**Status Colors**:
- Success: `#10b981` - Completed, success states
- Warning: `#f59e0b` - Warnings, pending states
- Error: `#ef4444` - Errors, conflicts
- Info: `#3b82f6` - Information, neutral states

**Classification Colors**:
- NO_CONFLICT: `#10b981` (green)
- CONFLICT: `#ef4444` (red)
- NEW: `#3b82f6` (blue)
- DELETED: `#f59e0b` (orange)

#### Typography

- **Font Family**: System fonts (-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto)
- **Headings**: Bold, larger sizes (h1: 2.5rem, h2: 2rem, h3: 1.75rem)
- **Body**: Regular weight, 1rem base size
- **Code**: Monospace (Consolas, Monaco, 'Courier New')

#### Components

**Cards**:
```html
<div class="card">
    <div class="card-header">
        <h3>Card Title</h3>
    </div>
    <div class="card-body">
        Card content
    </div>
</div>
```

**Badges**:
```html
<span class="badge badge-success">NO_CONFLICT</span>
<span class="badge badge-danger">CONFLICT</span>
<span class="badge badge-primary">NEW</span>
<span class="badge badge-warning">DELETED</span>
```

**Buttons**:
```html
<button class="btn btn-primary">Primary Action</button>
<button class="btn btn-secondary">Secondary Action</button>
<button class="btn btn-success">Success Action</button>
<button class="btn btn-danger">Danger Action</button>
```

### JavaScript Modules

#### main.js
Core functionality:
- Sidebar toggle and persistence
- Toast notifications
- Form validation
- AJAX request handling

#### sail-highlighter.js
SAIL code syntax highlighting:
- Keyword highlighting
- Function highlighting
- String and comment highlighting
- Line numbering

#### upload.js
File upload handling:
- Drag-and-drop support
- Progress tracking
- File validation
- Multi-file upload

#### settings.js
Settings management:
- Form handling
- Validation
- Save/reset functionality

### Responsive Design

**Breakpoints**:
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

**Mobile Optimizations**:
- Collapsible sidebar
- Stacked layouts
- Touch-friendly buttons
- Simplified navigation

### Accessibility

- **ARIA Labels**: All interactive elements have proper labels
- **Keyboard Navigation**: Full keyboard support
- **Color Contrast**: WCAG AA compliant
- **Screen Reader Support**: Semantic HTML and ARIA attributes
- **Focus Indicators**: Visible focus states


---

## 🔒 Security

### Security Features

#### Input Validation
- File type whitelist enforcement
- File size limits (200MB max)
- SQL injection prevention via ORM
- XSS protection with Jinja2 auto-escaping
- CSRF protection for forms

#### Authentication & Authorization
- Secure session management
- Secret key for session encryption
- No storage of AWS credentials in code
- Environment variable-based configuration

#### Data Protection
- Automatic cleanup of temporary files
- Audit trail for all operations
- Database transaction isolation
- Secure file upload handling

#### Security Best Practices

**Environment Variables**:
```bash
# Never commit these to version control
export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
```

**File Upload Validation**:
```python
ALLOWED_EXTENSIONS = {'txt', 'md', 'docx', 'pdf', 'zip'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

**SQL Injection Prevention**:
```python
# ✅ CORRECT - Using ORM
objects = ObjectLookup.query.filter_by(uuid=user_input).all()

# ❌ WRONG - Raw SQL with user input
db.session.execute(f"SELECT * FROM object_lookup WHERE uuid = '{user_input}'")
```

**XSS Prevention**:
```html
<!-- Jinja2 auto-escapes by default -->
<p>{{ user_input }}</p>  <!-- Safe -->

<!-- Use |safe only for trusted content -->
<div>{{ trusted_html|safe }}</div>
```

### Security Checklist

- [ ] Change default SECRET_KEY in production
- [ ] Use HTTPS in production
- [ ] Configure firewall rules
- [ ] Enable database backups
- [ ] Set up log monitoring
- [ ] Implement rate limiting
- [ ] Regular security updates
- [ ] Audit AWS IAM permissions
- [ ] Review file upload limits
- [ ] Enable CORS restrictions


---

## 🐛 Troubleshooting

### Common Issues

#### Issue: "Address already in use" Error

**Symptom**: Cannot start application, port 5000 already in use

**Solution**:
```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
lsof -ti :5000 | xargs kill -9

# Verify port is free
lsof -i :5000

# Start application
python app.py
```

#### Issue: "TY=not a tty" Error in Tests

**Symptom**: Tests fail with "TY=not a tty" error

**Solution**: Always use redirect-and-cat pattern:
```bash
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

#### Issue: Duplicate Objects in object_lookup

**Symptom**: Multiple objects with same UUID

**Solution**: Always use `find_or_create()`:
```python
# ✅ CORRECT
object_lookup = self.object_lookup_repo.find_or_create(
    uuid=obj_uuid,
    name=obj_name,
    object_type=obj_type,
    description=obj_description
)

# ❌ WRONG
object_lookup = ObjectLookup(uuid=obj_uuid, name=obj_name)
db.session.add(object_lookup)
```

#### Issue: Database Locked Error

**Symptom**: "database is locked" error

**Solution**:
```bash
# Check for long-running transactions
python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    db.session.rollback()
"

# If persistent, restart application
lsof -ti :5000 | xargs kill -9
python app.py
```

#### Issue: AWS Credentials Not Found

**Symptom**: "Unable to locate credentials" error

**Solution**:
```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_REGION=us-east-1

# Verify credentials
aws sts get-caller-identity
```

#### Issue: File Upload Fails

**Symptom**: "File too large" or "Invalid file type" error

**Solution**:
```python
# Check configuration
from config import Config
print(f"Max size: {Config.MAX_CONTENT_LENGTH}")
print(f"Allowed: {Config.ALLOWED_EXTENSIONS}")

# Adjust if needed in config.py
MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200MB
ALLOWED_EXTENSIONS = {'txt', 'md', 'docx', 'pdf', 'zip'}
```

#### Issue: AI Summary Generation Fails

**Symptom**: AI summaries stuck in "processing" status

**Solution**:
```python
# Check AI summary status
from app import create_app
from models import db, Change
app = create_app()
with app.app_context():
    stuck = Change.query.filter_by(ai_summary_status='processing').all()
    print(f"Stuck summaries: {len(stuck)}")
    
    # Reset stuck summaries
    for change in stuck:
        change.ai_summary_status = 'pending'
    db.session.commit()
```

### Debug Mode

Enable debug mode for development:

```bash
export FLASK_ENV=development
export DEBUG=True
python app.py
```

**Debug Features**:
- Detailed error pages
- Auto-reload on code changes
- SQL query logging
- Request/response logging

### Logging

Check logs for detailed error information:

```bash
# Application logs
tail -f logs/nexusgen.log

# Merge assistant logs
tail -f logs/merge_assistant.log

# Settings logs
tail -f logs/settings_service.log

# Search for errors
grep -i error logs/nexusgen.log
```

### Database Inspection

```bash
# Open SQLite database
sqlite3 instance/docflow.db

# Common queries
.tables                                    # List all tables
.schema merge_sessions                     # Show table schema
SELECT COUNT(*) FROM object_lookup;        # Count objects
SELECT * FROM merge_sessions ORDER BY created_at DESC LIMIT 5;  # Recent sessions
```


---

## 📈 Performance

### Performance Characteristics

**Typical Processing Times**:
- Small applications (<500 objects): 2-3 seconds
- Medium applications (500-1500 objects): 4-5 seconds
- Large applications (1500+ objects): 6-8 seconds

**Database Performance**:
- Connection pooling: 10 connections, max overflow 20
- Query optimization with proper indexes
- Lazy loading for relationships
- Batch operations for bulk inserts

### Optimization Strategies

#### Database Optimization

**Connection Pooling**:
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 20,
    'pool_timeout': 30,
}
```

**Indexes**:
```sql
-- Critical indexes for performance
CREATE INDEX idx_object_lookup_uuid ON object_lookup(uuid);
CREATE INDEX idx_change_session_classification ON changes(session_id, classification);
CREATE INDEX idx_delta_category ON delta_comparison_results(session_id, change_category);
```

**Query Optimization**:
```python
# ✅ GOOD - Eager loading
changes = Change.query\
    .options(db.joinedload(Change.object))\
    .filter_by(session_id=session_id)\
    .all()

# ❌ BAD - N+1 queries
changes = Change.query.filter_by(session_id=session_id).all()
for change in changes:
    print(change.object.name)  # Triggers separate query each time
```

#### Service Optimization

**Lazy Initialization**:
```python
class MyService(BaseService):
    def _initialize_dependencies(self):
        # Dependencies only created when first accessed
        self._my_repo = None
    
    @property
    def my_repo(self):
        if self._my_repo is None:
            self._my_repo = self._get_repository(MyRepository)
        return self._my_repo
```

**Batch Operations**:
```python
# ✅ GOOD - Batch insert
objects = [ObjectLookup(uuid=u, name=n) for u, n in data]
db.session.bulk_save_objects(objects)
db.session.commit()

# ❌ BAD - Individual inserts
for uuid, name in data:
    obj = ObjectLookup(uuid=uuid, name=name)
    db.session.add(obj)
    db.session.commit()  # Commit each time
```

#### Frontend Optimization

**Asset Caching**:
```html
<!-- Cache static assets -->
<link rel="stylesheet" href="/static/css/docflow.css?v=6.0.0">
<script src="/static/js/main.js?v=6.0.0"></script>
```

**Lazy Loading**:
```javascript
// Load change details on demand
function loadChangeDetail(changeId) {
    fetch(`/merge/${sessionId}/changes/${changeId}`)
        .then(response => response.json())
        .then(data => renderChangeDetail(data));
}
```

### Monitoring

**Performance Metrics**:
```python
import time

start_time = time.time()
# ... operation ...
duration = time.time() - start_time

logger.info(f"Operation completed in {duration:.2f} seconds")
```

**Database Monitoring**:
```python
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - conn.info['query_start_time'].pop(-1)
    logger.debug(f"Query took {total:.4f}s: {statement}")
```


---

## 🤝 Contributing

### Development Setup

1. **Fork the repository**
2. **Clone your fork**
```bash
git clone https://github.com/your-username/nexusgen.git
cd nexusgen
```

3. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

4. **Set up development environment**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r test_requirements.txt
```

5. **Make your changes**
6. **Run tests**
```bash
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

7. **Commit your changes**
```bash
git add .
git commit -m "Add feature: your feature description"
```

8. **Push to your fork**
```bash
git push origin feature/your-feature-name
```

9. **Create a Pull Request**

### Coding Standards

#### Python Style Guide

Follow PEP 8 with these specifics:

- **Line Length**: 88 characters (Black formatter)
- **Indentation**: 4 spaces
- **Imports**: Grouped (standard library, third-party, local)
- **Docstrings**: Google style
- **Type Hints**: Use where appropriate

**Example**:
```python
from typing import List, Optional

from models import db, ObjectLookup
from core.base_service import BaseService


class MyService(BaseService):
    """
    Service for handling my operations.
    
    This service provides functionality for...
    
    Attributes:
        my_repo: Repository for data access
    """
    
    def process_items(
        self,
        items: List[str],
        filter_type: Optional[str] = None
    ) -> List[ObjectLookup]:
        """
        Process a list of items.
        
        Args:
            items: List of item identifiers
            filter_type: Optional filter to apply
            
        Returns:
            List of processed ObjectLookup instances
            
        Raises:
            ValidationException: If items are invalid
        """
        # Implementation
        pass
```

#### Commit Messages

Follow conventional commits:

```
type(scope): subject

body

footer
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Build process or auxiliary tool changes

**Examples**:
```
feat(merge): add AI summary generation for conflicts

Implement async AI summary generation using Bedrock service.
Summaries are generated in background thread after session commit.

Closes #123
```

```
fix(classification): correct rule 10b logic for conflicts

Rule 10b was incorrectly classifying some conflicts as NO_CONFLICT.
Updated comparison logic to properly detect content differences.

Fixes #456
```

### Testing Requirements

All contributions must include tests:

- **Unit tests** for new services/repositories
- **Integration tests** for new workflows
- **Property tests** for invariants
- **Minimum 80% code coverage**

### Code Review Process

1. **Automated Checks**: All tests must pass
2. **Code Review**: At least one approval required
3. **Documentation**: Update README if needed
4. **Changelog**: Add entry to CHANGELOG.md

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
```


---

## 📚 Additional Resources

### Documentation

**Core Documentation:**
- **Complete Guide**: `.kiro/steering/nexusgen-complete-guide.md` - Comprehensive development guide
- **Database Schema**: `.kiro/specs/three-way-merge-database-schema.md` - Complete schema documentation
- **Service Design**: `.kiro/specs/three-way-merge-service-design.md` - Service architecture details
- **Clean Architecture**: `.kiro/specs/three-way-merge-clean-architecture.md` - Architecture principles
- **Implementation Plan**: `.kiro/specs/three-way-merge-implementation-plan.md` - Development roadmap
- **Quick Reference**: `.kiro/specs/three-way-merge-quick-reference.md` - Quick command reference
- **Executive Summary**: `.kiro/specs/three-way-merge-executive-summary.md` - High-level overview

**Technical Guides:**
- **Logging Guide**: `docs/LOGGING.md` - Logging configuration and best practices
- **Performance Guide**: `docs/PERFORMANCE_OPTIMIZATIONS.md` - Performance tuning and optimization

**UI Documentation:**
- **UI Templates Part 1**: `.kiro/specs/three-way-merge-ui-templates.md`
- **UI Templates Part 2**: `.kiro/specs/three-way-merge-ui-templates-part2.md`
- **UI Templates Part 3**: `.kiro/specs/three-way-merge-ui-templates-part3.md`

**Architecture Diagrams:**
- **System Diagrams**: `.kiro/specs/three-way-merge-architecture-diagrams.md` - Visual architecture documentation

### Test Data

Located in `applicationArtifacts/`:
- `Three Way Testing Files/V2/` - Test Appian packages
- `ObjectSpecificXml/` - Sample XML files
- `SQL Conversion Support Files/` - SQL conversion samples

### Utility Scripts

- `list_sessions.py` - List all merge sessions
- `delete_old_merge_sessions.py` - Clean up old sessions
- `create_three_way_merge_schema.py` - Initialize database schema
- `verify_ai_summary_schema.py` - Verify AI summary schema
- `regenerate_report.py` - Regenerate session reports
- `clean_all_data.py` - Clean all database data
- `cleanup_orphaned_data.py` - Remove orphaned records

### External Links

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Amazon Q Documentation](https://docs.aws.amazon.com/amazonq/)
- [Bootstrap Documentation](https://getbootstrap.com/docs/)
- [pytest Documentation](https://docs.pytest.org/)

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 👥 Team

**Development Team**: NexusGen Engineering

**Contact**: For issues, questions, or feature requests, please contact the development team.

---

## 🙏 Acknowledgments

- **AWS Bedrock** for AI capabilities and RAG integration
- **Amazon Q CLI** for agent integration
- **Flask Community** for excellent web framework
- **Bootstrap** for responsive UI components
- **SQLAlchemy** for robust ORM and database management
- **pytest** for comprehensive testing framework
- **Font Awesome** for icon library

---

## 📊 Project Statistics

- **Version**: 6.0.0
- **Lines of Code**: ~50,000+
- **Database Tables**: 50+
- **Services**: 30+
- **Repositories**: 40+
- **Test Files**: 30+
- **Test Coverage**: 85%+
- **Supported Object Types**: 12+
- **API Endpoints**: 25+

---

## 🔄 Version History

### Version 6.0.0 (Current - December 2025)
**Major Release - Complete Platform Overhaul**

**Three-Way Merge Engine:**
- Complete 10-step transactional workflow implementation
- Set-based classification logic (D ∩ E, D \ E, E \ D)
- 7 classification rules (10a-10g) fully implemented
- Delta-driven working set architecture
- Package-agnostic object registry (no duplicate objects)
- Support for 12+ Appian object types with specialized parsers

**AI Integration:**
- AWS Bedrock RAG integration for document intelligence
- Amazon Q CLI agent integration
- Async AI summary generation in background threads
- AI-powered merge guidance and conflict analysis

**Architecture:**
- Clean architecture with strict layer separation
- Dependency injection container for all services/repositories
- Base classes for services and repositories
- Custom exception hierarchy
- Centralized logging with rotation

**Database:**
- 50+ tables with proper relationships and referential integrity
- Connection pooling (10 connections, max overflow 20)
- Package-object mapping junction table
- Object-specific tables for all Appian types
- Comprehensive indexes for performance

**UI/UX:**
- Custom dark theme with Appian color palette
- SAIL code syntax highlighting
- Interactive change navigation and filtering
- Progress tracking and session statistics
- Responsive design for mobile and desktop

**Testing:**
- Property-based testing with 18 properties
- Integration tests with real Appian packages
- 85%+ code coverage
- Comprehensive test suite (30+ test files)

**API:**
- RESTful API endpoints for all operations
- Session management and status tracking
- Change review and navigation endpoints
- Report generation endpoints

**Performance:**
- Database connection pooling
- Query optimization with proper indexes
- Lazy loading for relationships
- Batch operations for bulk inserts
- Typical processing: 2-8 seconds for 500-1500 objects

### Version 5.0.0 (November 2025)
- Three-way merge assistant foundation
- Delta and customer comparison services
- Classification engine with 7 rules
- Object-specific parsers for 12+ types
- Initial UI implementation

### Version 4.0.0 (October 2025)
- Enhanced merge assistant
- Improved dependency analysis
- Advanced conflict detection
- Migration planning features

### Version 3.0.0 (September 2025)
- SAIL code diff visualization
- UUID resolution and function mapping
- Business impact analysis
- Interactive object browser

### Version 2.0.0 (August 2025)
- Clean architecture implementation
- Dependency injection container
- Repository pattern
- Enhanced error handling

### Version 1.0.0 (July 2025)
- Initial release
- Document intelligence features
- AWS Bedrock integration
- Basic Appian analysis

---

## 🚦 Status

**Current Status**: ✅ Production Ready

**Active Development**: Yes

**Maintenance**: Active

**Support**: Available

---

**Built with ❤️ by the NexusGen Team**

*Last Updated: December 5, 2025*
