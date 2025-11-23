# NexusGen - Document Intelligence & Appian Analysis Platform

> **Version 4.0.0** | A comprehensive Flask-based platform for document intelligence, AI-powered analysis, and advanced Appian application comparison with SAIL code visualization.

## 🚀 Overview

NexusGen is a modern enterprise platform that combines document intelligence with advanced Appian application analysis. Built with Flask and featuring a professional dark-themed UI, it provides comprehensive functionality for document processing, AI-powered insights, and detailed Appian application version comparison with SAIL code diff visualization.

## ✨ Core Features

### 📄 Document Intelligence
- **Spec Breakdown**: Upload documents and automatically generate structured user stories and acceptance criteria
- **Design Verification**: AI-powered validation and recommendations for design documents
- **Design Creation**: Generate comprehensive design documents from acceptance criteria
- **SQL Conversion**: Convert between MariaDB and Oracle SQL dialects
- **💬 AI Chat Assistant**: Interactive chat interface for document-related queries

### 🏢 Appian Application Analyzer
- **Version Comparison**: Compare two versions of Appian applications with detailed change tracking
- **SAIL Code Diff**: Side-by-side SAIL code comparison with GitHub-style diff visualization
- **Object Analysis**: Parse and analyze interfaces, process models, rules, constants, and more
- **UUID Resolution**: Replace UUIDs with readable object names for better comprehension
- **Business Impact Analysis**: AI-powered summaries of changes and their implications
- **Interactive Browser**: Navigate application structure with expandable tree views

### 🔄 Three-Way Merge Assistant
- **Package Comparison**: Compare base, source, and target Appian packages
- **Conflict Detection**: Identify conflicts and dependencies between changes
- **Merge Guidance**: AI-powered recommendations for resolving conflicts
- **Migration Planning**: Generate migration strategies and deployment plans

### 📊 Process Transparency
- **Complete History**: Track all processing requests with timeline and metrics
- **Confidence Indicators**: RAG similarity scores, JSON validity, processing time badges
- **Error Recovery**: Robust error handling with fallback mechanisms
- **Database-First**: All data stored in database with no file dependencies

## 🏗️ Architecture

### Technology Stack
- **Backend**: Flask 2.3+ (Python 3.8+)
- **Database**: SQLite with SQLAlchemy ORM
- **AI Services**: AWS Bedrock, Amazon Q CLI Agents
- **Frontend**: Bootstrap 5, Font Awesome 6, Custom Dark Theme
- **Document Processing**: python-docx, openpyxl, PyPDF2

### Project Structure

```
nexus-gen-v2/
├── 🎮 controllers/              # Flask route handlers
│   ├── analyzer_controller.py   # Appian analyzer routes
│   ├── breakdown_controller.py  # Spec breakdown routes
│   ├── verify_controller.py     # Design verification routes
│   ├── create_controller.py     # Design creation routes
│   ├── merge_assistant_controller.py  # Merge assistant routes
│   └── base_controller.py       # Base controller with common functionality
│
├── ⚙️ services/                 # Business logic layer
│   ├── ai/                      # AI service integrations
│   │   ├── bedrock_service.py   # AWS Bedrock RAG service
│   │   └── q_agent_service.py   # Amazon Q CLI agent integration
│   │
│   ├── appian_analyzer/         # Appian analysis engine
│   │   ├── analyzer.py          # Main analyzer with OOP design
│   │   ├── parsers.py           # XML parsers for Appian objects
│   │   ├── version_comparator.py  # Version comparison logic
│   │   ├── sail_formatter.py    # SAIL code formatting & cleanup
│   │   ├── enhanced_comparison_service.py  # Dual-layer comparison
│   │   ├── business_summary_generator.py   # AI-powered summaries
│   │   ├── logger.py            # Request-specific logging
│   │   └── models.py            # Appian object data models
│   │
│   ├── comparison/              # Comparison orchestration
│   │   ├── comparison_service.py  # Main comparison workflow
│   │   ├── blueprint_analyzer.py  # Blueprint generation
│   │   └── comparison_engine.py   # Comparison logic
│   │
│   ├── merge/                   # Three-way merge services
│   │   ├── three_way_merge_service.py  # Merge orchestration
│   │   ├── package_service.py   # Package analysis
│   │   └── change_service.py    # Change tracking
│   │
│   ├── request/                 # Request management
│   │   ├── request_service.py   # Request lifecycle management
│   │   ├── file_service.py      # File handling & validation
│   │   └── document_service.py  # Document extraction
│   │
│   ├── excel_service.py         # Excel report generation
│   ├── word_service.py          # Word document generation
│   └── process_tracker.py       # Timeline & metrics tracking
│
├── 🗄️ repositories/             # Data access layer
│   ├── request_repository.py    # Request data access
│   ├── comparison_repository.py # Comparison data access
│   ├── chat_session_repository.py  # Chat data access
│   └── merge_session_repository.py # Merge session data access
│
├── 🏛️ core/                     # Clean architecture foundation
│   ├── interfaces.py            # Abstract base classes
│   ├── exceptions.py            # Custom exception hierarchy
│   ├── dependency_container.py  # Dependency injection
│   └── base_service.py          # Base service class
│
├── 🗄️ models.py                 # SQLAlchemy database models
├── ⚙️ config.py                 # Application configuration
├── 🎨 templates/                # Jinja2 HTML templates
├── 📁 static/                   # CSS, JavaScript, images
├── 🧪 tests/                    # Comprehensive test suite
└── 📝 logs/                     # Application logs
```

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
cd nexus-gen-v2
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

7. **Access the application**
```
Open browser to: http://localhost:5002
```

## 📖 Usage Guide

### Appian Application Comparison

1. **Navigate to Analyzer**
   - Click "Appian Analyzer" in the sidebar
   - Or go to `http://localhost:5002/analyzer`

2. **Upload Application Versions**
   - Select old version ZIP file
   - Select new version ZIP file
   - Click "Start Comparison"

3. **View Results**
   - Summary shows total changes by category
   - Click on any object to see detailed diff
   - SAIL code displayed side-by-side with highlighting

4. **Analyze Changes**
   - Added objects (green)
   - Modified objects (yellow)
   - Removed objects (red)
   - Unchanged objects (gray)

### Document Breakdown

1. **Upload Document**
   - Navigate to "Spec Breakdown"
   - Upload PDF, DOCX, TXT, or MD file
   - Click "Process Document"

2. **Review Results**
   - View generated user stories
   - Check acceptance criteria
   - Export to Excel if needed

### Three-Way Merge

1. **Upload Packages**
   - Navigate to "Merge Assistant"
   - Upload base, source, and target packages
   - Click "Analyze Merge"

2. **Review Conflicts**
   - View detected conflicts
   - Check dependency analysis
   - Follow AI-powered recommendations

## 🔧 Configuration

### Environment Variables

```bash
# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_KB_ID=WAQ6NJLGKN

# Application Settings
SECRET_KEY=your-production-secret-key
FLASK_ENV=production
DEBUG=False

# Database (SQLite by default)
SQLALCHEMY_DATABASE_URI=sqlite:///instance/docflow.db

# File Upload Limits
MAX_CONTENT_LENGTH=16777216  # 16MB
```

### Supported File Types

- **Documents**: PDF, DOCX, TXT, MD
- **Appian Exports**: ZIP files containing XML objects
- **SQL Files**: SQL, TXT

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install -r test_requirements.txt

# Run all tests
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run specific test file
python -m pytest tests/test_analyzer.py -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run with coverage
python -m pytest --cov=services --cov-report=html > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

### Test Categories

- **Unit Tests**: Individual service and model testing
- **Integration Tests**: End-to-end workflow validation
- **Controller Tests**: API endpoint testing
- **Performance Tests**: Memory and concurrent request handling

## 📊 Database Schema

### ComparisonRequest
Tracks Appian application comparisons:
```sql
CREATE TABLE comparison_requests (
    id INTEGER PRIMARY KEY,
    reference_id VARCHAR(20),           -- CMP_001 format
    old_app_name VARCHAR(255),
    new_app_name VARCHAR(255),
    status VARCHAR(20),                 -- processing/completed/error
    old_app_blueprint TEXT,             -- JSON blueprint
    new_app_blueprint TEXT,             -- JSON blueprint
    comparison_results TEXT,            -- JSON comparison data
    total_time INTEGER,                 -- Processing time in seconds
    created_at DATETIME,
    updated_at DATETIME
);
```

### Request
Tracks document processing requests:
```sql
CREATE TABLE requests (
    id INTEGER PRIMARY KEY,
    action_type VARCHAR(20),            -- breakdown/verify/create
    filename VARCHAR(255),
    input_text TEXT,
    status VARCHAR(20),
    rag_query TEXT,
    rag_response TEXT,
    final_output TEXT,                  -- JSON format
    reference_id VARCHAR(20),           -- RQ_BR_001 format
    total_time INTEGER,
    created_at DATETIME,
    updated_at DATETIME
);
```

### ChatSession
Manages AI chat conversations:
```sql
CREATE TABLE chat_sessions (
    id INTEGER PRIMARY KEY,
    session_id VARCHAR(36),             -- UUID
    question TEXT,
    rag_response TEXT,
    answer TEXT,
    created_at DATETIME
);
```

## 🎨 UI Features

### Dark Theme
- Custom color palette with purple (#8b5cf6) and teal (#06b6d4) accents
- Optimized for readability with high contrast
- Consistent styling across all pages

### Responsive Design
- Mobile-friendly interface
- Collapsible sidebar with persistent state
- Adaptive layouts for different screen sizes

### Interactive Components
- Real-time file upload progress
- Animated loading states
- Toast notifications for user feedback
- Expandable code diff viewers

## 🔒 Security

### Input Validation
- File type whitelist enforcement
- File size limits (16MB max)
- SQL injection prevention via ORM
- XSS protection with Jinja2 auto-escaping

### Data Protection
- Secure session management
- No storage of AWS credentials in code
- Automatic cleanup of temporary files
- Audit trail for all operations

## 📈 Performance

### Optimization Strategies
- Database connection pooling
- Lazy service initialization
- Efficient file streaming
- Browser caching for static assets

### Typical Processing Times
- Small applications (<500 objects): 2-3 seconds
- Medium applications (500-1500 objects): 4-5 seconds
- Large applications (1500+ objects): 6-8 seconds

## 🔄 Version History

### Version 4.0.0 (Current)
- Enhanced three-way merge assistant
- Improved dependency analysis
- Advanced conflict detection
- Migration planning features

### Version 3.0.0
- Appian analyzer with SAIL code diff
- UUID resolution and function mapping
- Business impact analysis
- Interactive object browser

### Version 2.0.0
- Clean architecture implementation
- Dependency injection container
- Repository pattern
- Enhanced error handling

### Version 1.0.0
- Initial release
- Document intelligence features
- AWS Bedrock integration
- Basic Appian analysis

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📝 License

This project is proprietary software. All rights reserved.

## 📞 Support

For issues, questions, or feature requests:
- Check the logs at `logs/appian_analyzer.log`
- Review the development log at `.kiro/DEVELOPMENT_LOG.md`
- Contact the development team

## 🙏 Acknowledgments

- AWS Bedrock for AI capabilities
- Amazon Q CLI for agent integration
- Flask community for excellent framework
- Bootstrap for UI components

---

**Built with ❤️ by the NexusGen Team**
