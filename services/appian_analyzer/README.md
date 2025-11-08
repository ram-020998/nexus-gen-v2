# Appian Application Analyzer

A professional Python tool for analyzing Appian application zip files and generating detailed technical blueprints with advanced version comparison capabilities.

## Features

- **🏗️ Professional OOP Architecture**: Clean, maintainable code structure
- **📊 Enhanced Accuracy**: Improved parsing with detailed component analysis
- **🎯 Smart Classification**: Automatic categorization of components by business domain
- **📈 Complexity Analysis**: Sophisticated scoring and maintainability assessment
- **🔍 Deep Insights**: Process automation levels, security patterns, integration analysis
- **📋 Object Lookup**: Complete UUID-to-name mapping for all objects
- **🔄 Version Comparison**: Compare two application versions to identify technical changes
- **💻 SAIL Code Analysis**: Extract and format SAIL code with syntax highlighting
- **📊 Business Intelligence**: Automated business summary generation
- **🔍 Change Detection**: Deep content-level change analysis including SAIL code modifications

## Quick Start

### Single Application Analysis
```bash
# Analyze an Appian application using module
python3 -m src.appian_analyzer applicationZips/RequirementsManagementv2.3.0.zip

# Or install and use as command
pip install -e .
appian-analyzer applicationZips/RequirementsManagementv2.3.0.zip

# This generates in output/ folder:
# - RequirementsManagementv2.3.0_blueprint.json (detailed technical analysis)
# - RequirementsManagementv2.3.0_object_lookup.json (UUID-to-name mapping)
```

### Version Comparison
```bash
# Compare two application versions
python3 compare_versions.py applicationZips/SourceSelectionv2.4.0.zip applicationZips/SourceSelectionv2.6.0.zip

# This generates:
# - Individual blueprints for both versions
# - Detailed comparison with SAIL code changes
# - SourceSelectionv2.4.0_vs_SourceSelectionv2.6.0_comparison.json
```

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd appianAnalyser

# Install dependencies (optional - uses only standard library by default)
pip install -r requirements.txt

# Or install as package
pip install -e .
```

## What Gets Analyzed

### 1. Data Architecture
- **Record Types** with field-level analysis and relationships
- **Data Types (CDTs)** with complete metadata
- **Business Domain Classification**
- **Relationship Mapping** and complexity scoring

### 2. Business Processes
- **Process Models** with node-level analysis and SAIL code extraction
- **Automation Level Assessment**
- **Business Function Mapping**
- **Complexity Scoring** based on node types and patterns

### 3. Integration Architecture
- **Connected Systems** with pattern classification
- **Web APIs** and endpoint analysis
- **Security Level Assessment**
- **Integration Point Classification**

### 4. Security Model
- **Security Groups** with type classification
- **Business Function Mapping**
- **Role-Based Access Analysis**

### 5. User Interface
- **Sites** with page hierarchy analysis
- **Interfaces** with component mapping and SAIL code extraction
- **Expression Rules** for business logic with formatted code
- **Constants** for configuration management

### 6. Application Intelligence
- **Application Type Detection**
- **Complexity Assessment** (Low, Medium, High, Very High)
- **Maintainability Scoring**
- **Actionable Recommendations**
- **Business Summary Generation**

## New Features in v1.2.0

### 🔄 Version Comparison Framework
Compare two Appian application versions to identify technical changes:

**Features:**
- **Object-level comparison**: Detects added, removed, and modified objects
- **SAIL code analysis**: Identifies code changes with character-level precision
- **Business logic tracking**: Monitors expression rule and process model changes
- **Impact assessment**: Automatic categorization (NONE/LOW/MEDIUM/HIGH/VERY_HIGH)
- **Structured output**: JSON format for easy integration

**Usage:**
```bash
python3 compare_versions.py app_v1.zip app_v2.zip
```

**Output Structure:**
```json
{
  "comparison_summary": {
    "version_from": "AppV1.0",
    "version_to": "AppV2.0",
    "total_changes": 27,
    "impact_level": "MEDIUM"
  },
  "changes_by_category": {
    "interfaces": {"added": 5, "modified": 12, "removed": 2}
  },
  "detailed_changes": [
    {
      "name": "MyInterface",
      "change_type": "MODIFIED",
      "changes": ["SAIL code modified (+663 characters)"],
      "sail_code_before": "original code...",
      "sail_code_after": "modified code..."
    }
  ]
}
```

### 💻 SAIL Code Analysis
Enhanced SAIL code extraction and formatting:

**Features:**
- **Complete code extraction** from interfaces, expression rules, and process models
- **Syntax formatting** with proper indentation
- **Code change detection** in version comparisons
- **Character-level diff analysis**

### 📊 Business Intelligence
Automated business summary generation:

**Features:**
- **Application type detection** (Data-Centric, Process-Heavy, Integration-Focused)
- **Complexity assessment** with detailed scoring
- **Maintainability analysis**
- **Actionable recommendations**
- **Component relationship mapping**

### 🔍 Enhanced Object Analysis
Comprehensive object parsing with improved accuracy:

**Features:**
- **Complete object lookup** with UUID-to-name mapping
- **Relationship tracking** across all component types
- **Security configuration analysis**
- **Field-level metadata extraction**

## Project Structure

```
appianAnalyser/
├── src/appian_analyzer/           # Main package
│   ├── analyzer.py                # Core analysis engine
│   ├── parsers.py                 # XML parsing components
│   ├── models.py                  # Data models
│   ├── sail_formatter.py          # SAIL code formatting
│   ├── business_summary_generator.py # Business intelligence
│   └── version_comparator.py      # Version comparison engine
├── compare_versions.py            # Version comparison CLI
├── applicationZips/               # Input zip files
├── output/                        # Generated output files
├── schemas/                       # XML schema documentation
└── tests/                         # Test suite
```

## Analysis Results Example

For the SourceSelection v2.4.0 vs v2.6.0 comparison:

```
🎯 Version Comparison Complete:
  📦 From: SourceSelectionv2.4.0
  📦 To: SourceSelectionv2.6.0
  📊 Total Changes: 239
  📈 Impact Level: VERY_HIGH

🎯 Component Breakdown:
  • Interfaces: 73 changes (22 added, 51 modified)
  • Expression Rules: 72 changes (50 added, 19 modified, 3 removed)
  • Process Models: 16 changes (13 added, 3 modified)
  • Constants: 57 changes (55 added, 2 modified)
  • Security Groups: 5 changes (2 added, 2 modified, 1 removed)
```

## Output Files

### Technical Blueprint JSON
Comprehensive structured analysis including:
- Executive summary with intelligent metrics
- Component-wise detailed breakdown
- Business domain classifications
- Complexity and maintainability assessments
- Actionable recommendations
- Complete SAIL code extraction

### Object Lookup JSON
Complete UUID-to-name mapping for:
- Easy object reference resolution
- Cross-component relationship tracking
- Development and maintenance support

### Version Comparison JSON
Detailed change analysis including:
- Object-level changes (added/removed/modified)
- SAIL code differences with full content
- Business logic modifications
- Impact assessment and categorization

## Advanced Usage

### Python API
```python
from appian_analyzer import AppianAnalyzer, AppianVersionComparator

# Single application analysis
analyzer = AppianAnalyzer("app.zip")
result = analyzer.analyze()
blueprint = result["blueprint"]
object_lookup = result["object_lookup"]

# Version comparison
comparator = AppianVersionComparator("app_v1.zip", "app_v2.zip")
comparison = comparator.compare_versions()
```

### CLI Commands
```bash
# Single analysis
python3 -m src.appian_analyzer path/to/application.zip

# Version comparison
python3 compare_versions.py app_v1.zip app_v2.zip

# List output files
ls output/
```

## Requirements

- Python 3.7+
- Standard library (no external dependencies for basic usage)

## Key Improvements in v1.2.0

✅ **Version Comparison Framework**: Complete change detection across versions  
✅ **SAIL Code Analysis**: Full code extraction and formatting  
✅ **Enhanced Accuracy**: Improved parsing with 99%+ object detection  
✅ **Business Intelligence**: Automated summary and recommendations  
✅ **Deep Change Detection**: Content-level analysis including code modifications  
✅ **Professional Output**: Structured JSON for easy integration  
✅ **Impact Assessment**: Automatic categorization of change severity  

## Use Cases

### For Development Teams
- **Code Review**: Analyze SAIL code changes between versions
- **Impact Assessment**: Understand upgrade implications
- **Documentation**: Generate technical blueprints automatically

### For Project Managers
- **Change Management**: Track modifications across releases
- **Risk Assessment**: Identify high-impact changes
- **Planning**: Use complexity scores for effort estimation

### For System Integrators
- **Application Analysis**: Understand existing system architecture
- **Migration Planning**: Assess modernization requirements
- **Integration Design**: Map data flows and dependencies

This tool transforms raw Appian exports into intelligent architectural documentation, enabling better decision-making for development, maintenance, and optimization strategies.
