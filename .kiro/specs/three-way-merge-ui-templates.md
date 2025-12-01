# Three-Way Merge UI & Template Specification

**Part of:** Three-Way Merge Clean Architecture Specification  
**Version:** 1.0  
**Date:** 2025-11-30

---

## Table of Contents

1. [Overview](#overview)
2. [Template Structure](#template-structure)
3. [Page Specifications](#page-specifications)
4. [Component Library](#component-library)
5. [Styling Guidelines](#styling-guidelines)
6. [JavaScript Interactions](#javascript-interactions)
7. [Data Binding](#data-binding)

---

## 1. Overview

### Purpose

This document specifies all UI templates for the three-way merge assistant, including layouts, components, styling, and interactions.

### Technology Stack

- **Template Engine**: Jinja2
- **CSS Framework**: Bootstrap 5
- **Icons**: Font Awesome 6
- **JavaScript**: Vanilla JS + jQuery
- **Syntax Highlighting**: Prism.js (for SAIL code)
- **Diagrams**: Mermaid.js (for process models)

### Design Principles

1. **Consistency**: Uniform styling across all pages
2. **Clarity**: Clear visual hierarchy and information architecture
3. **Responsiveness**: Mobile-friendly layouts
4. **Accessibility**: WCAG 2.1 AA compliance
5. **Performance**: Optimized loading and rendering

---

## 2. Template Structure

### Base Template Hierarchy

```
base.html (Root template)
├── merge_assistant/
│   ├── upload.html (Package upload)
│   ├── sessions.html (Session list)
│   ├── summary.html (Merge summary)
│   ├── change_detail.html (Change review)
│   ├── report.html (Report generation)
│   ├── unknown_objects.html (Unknown object list)
│   ├── unknown_object_detail.html (Unknown object detail)
│   └── comparisons/
│       ├── _base_comparison.html (Base comparison template)
│       ├── interface_comparison.html
│       ├── expression_rule_comparison.html
│       ├── process_model_comparison.html
│       ├── record_type_comparison.html
│       ├── cdt_comparison.html
│       ├── integration_comparison.html
│       ├── web_api_comparison.html
│       ├── site_comparison.html
│       ├── group_comparison.html
│       ├── constant_comparison.html
│       └── connected_system_comparison.html
```

### Template Inheritance

```jinja2
{% extends "base.html" %}

{% block title %}Page Title{% endblock %}

{% block breadcrumbs %}
<!-- Breadcrumb navigation -->
{% endblock %}

{% block page_title %}Page Title{% endblock %}
{% block page_subtitle %}Page subtitle{% endblock %}

{% block content %}
<!-- Page content -->
{% endblock %}

{% block extra_js %}
<!-- Page-specific JavaScript -->
{% endblock %}
```

---

## 3. Page Specifications

### 3.1 Upload Page (`upload.html`)

**Purpose**: Upload three packages (A, B, C) to start merge analysis

**URL**: `/merge/upload`

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Breadcrumbs: Home > Merge Assistant                     │
├─────────────────────────────────────────────────────────┤
│ Three-Way Merge Assistant                               │
│ Upload three application packages to analyze...         │
├─────────────────────────────────────────────────────────┤
│ [Info Banner: How It Works]                             │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│ │ Package A   │ │ Package B   │ │ Package C   │       │
│ │ (Base)      │ │ (Customer)  │ │ (New Vendor)│       │
│ │             │ │             │ │             │       │
│ │ [Upload     │ │ [Upload     │ │ [Upload     │       │
│ │  Zone]      │ │  Zone]      │ │  Zone]      │       │
│ │             │ │             │ │             │       │
│ │ Drop file   │ │ Drop file   │ │ Drop file   │       │
│ │ or click    │ │ or click    │ │ or click    │       │
│ └─────────────┘ └─────────────┘ └─────────────┘       │
├─────────────────────────────────────────────────────────┤
│                    [Start Analysis]                      │
└─────────────────────────────────────────────────────────┘
```

**Key Components**:
- Info banner with instructions
- Three upload zones (drag & drop + click to browse)
- File validation (ZIP only, max 16MB)
- Progress indicators
- Start analysis button (enabled when all 3 files uploaded)

**Data Requirements**:
```python
# No initial data required
# Form submits to: POST /merge/create
```

**Interactions**:
- Drag & drop file upload
- Click to browse file
- File validation on selection
- Remove uploaded file
- Submit form with all three files

---

### 3.2 Sessions Page (`sessions.html`)

**Purpose**: List all merge sessions with status and actions

**URL**: `/merge/sessions`

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Breadcrumbs: Home > Merge Assistant                     │
├─────────────────────────────────────────────────────────┤
│ Merge Sessions                                          │
│ View and manage your three-way merge sessions          │
├─────────────────────────────────────────────────────────┤
│ [+ New Merge Session]                                   │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ MRG_001                          [Ready] 2025-11-30 │ │
│ │ Base: v2.4.0 | Customer: v2.4.0-custom | New: v2.6.0│ │
│ │ 78 changes | 45 conflicts | 20 no-conflict | 13 new│ │
│ │ [View Summary] [Continue] [Export Report] [Delete] │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ MRG_002                    [In Progress] 2025-11-29 │ │
│ │ ...                                                  │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Key Components**:
- New session button
- Session cards with:
  - Reference ID
  - Status badge
  - Package names
  - Statistics (total changes, conflicts, etc.)
  - Action buttons
- Pagination (if many sessions)

**Data Requirements**:
```python
{
    'sessions': [
        {
            'id': 1,
            'reference_id': 'MRG_001',
            'status': 'ready',  # processing, ready, in_progress, completed, error
            'base_package_name': 'v2.4.0',
            'customized_package_name': 'v2.4.0-custom',
            'new_vendor_package_name': 'v2.6.0',
            'total_changes': 78,
            'conflict_count': 45,
            'no_conflict_count': 20,
            'new_count': 13,
            'created_at': datetime,
            'updated_at': datetime
        }
    ]
}
```

---

### 3.3 Summary Page (`summary.html`)

**Purpose**: Display merge analysis results and statistics

**URL**: `/merge/<reference_id>/summary`

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Breadcrumbs: Home > Merge Assistant > MRG_001          │
├─────────────────────────────────────────────────────────┤
│ Merge Summary                                           │
│ Review the analysis results and start guided workflow  │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ MRG_001                    [Ready] [Generate Report]│ │
│ │ Created: 2025-11-30 10:00 | Processing: 45s        │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Package Information                                     │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│ │ Package A   │ │ Package B   │ │ Package C   │       │
│ │ v2.4.0      │ │ v2.4.0-cust │ │ v2.6.0      │       │
│ │ 150 objects │ │ 155 objects │ │ 165 objects │       │
│ └─────────────┘ └─────────────┘ └─────────────┘       │
├─────────────────────────────────────────────────────────┤
│ Change Statistics                                       │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│ │ 78 Total    │ │ 45 Conflicts│ │ 20 No Conf. │       │
│ │ Changes     │ │             │ │             │       │
│ └─────────────┘ └─────────────┘ └─────────────┘       │
├─────────────────────────────────────────────────────────┤
│ Changes by Category                                     │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Interfaces (25)                                     │ │
│ │ ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ │
│ │ 15 Conflicts | 8 No Conflict | 2 New               │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Process Models (12)                                 │ │
│ │ ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │ │
│ │ 8 Conflicts | 3 No Conflict | 1 New                │ │
│ └─────────────────────────────────────────────────────┘ │
│ ... (other object types)                                │
├─────────────────────────────────────────────────────────┤
│                  [Start Merge Workflow]                 │
└─────────────────────────────────────────────────────────┘
```

**Key Components**:
- Session info card
- Package information cards
- Statistics cards (total, conflicts, no-conflict, new, deleted)
- Changes by category (expandable sections)
- Progress indicators
- Start workflow button

**Data Requirements**:
```python
{
    'session': {
        'id': 1,
        'reference_id': 'MRG_001',
        'status': 'ready',
        'base_package_name': 'v2.4.0',
        'customized_package_name': 'v2.4.0-custom',
        'new_vendor_package_name': 'v2.6.0',
        'total_changes': 78,
        'created_at': datetime,
        'total_time': 45
    },
    'statistics': {
        'total_changes': 78,
        'conflict_count': 45,
        'no_conflict_count': 20,
        'new_count': 13,
        'deleted_count': 0
    },
    'changes_by_category': {
        'Interface': {
            'total': 25,
            'conflict': 15,
            'no_conflict': 8,
            'new': 2,
            'deleted': 0
        },
        'Process Model': {
            'total': 12,
            'conflict': 8,
            'no_conflict': 3,
            'new': 1,
            'deleted': 0
        }
        # ... other categories
    }
}
```

---

### 3.4 Change Detail Page (`change_detail.html`)

**Purpose**: Review individual change with detailed comparison

**URL**: `/merge/<reference_id>/change/<change_id>`

**Layout**:
```
┌─────────────────────────────────────────────────────────┐
│ Breadcrumbs: Home > Merge > MRG_001 > Change 1 of 78   │
├─────────────────────────────────────────────────────────┤
│ Change Detail                                           │
│ Review and merge vendor changes                         │
├─────────────────────────────────────────────────────────┤
│ Progress: [████████████░░░░░░░░░░░░░░░░░░░░] 1 of 78  │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [Icon] AS_GSS_HCL_vendorsTab                        │ │
│ │ Interface | CONFLICT                                │ │
│ │ [Jump to Change ▼]                                  │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Merge Guidance                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ⚠️ CONFLICT DETECTED                                │ │
│ │ Both vendor and customer modified this interface    │ │
│ │ Recommendation: Manual merge required               │ │
│ │ • SAIL code changed in both versions                │ │
│ │ • Parameters modified differently                   │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ [Object-Specific Comparison Content]                    │
│ (Loaded from comparison template)                       │
├─────────────────────────────────────────────────────────┤
│ User Notes                                              │
│ [Text area for notes]                                   │
├─────────────────────────────────────────────────────────┤
│ [◀ Previous] [Skip] [Mark as Reviewed] [Next ▶]       │
└─────────────────────────────────────────────────────────┘
```

**Key Components**:
- Progress bar
- Object header with icon and classification
- Jump to change dropdown
- Merge guidance card
- Object-specific comparison (loaded from sub-template)
- User notes textarea
- Navigation buttons

**Data Requirements**:
```python
{
    'session': {...},
    'change': {
        'id': 1,
        'object_id': 123,
        'name': 'AS_GSS_HCL_vendorsTab',
        'type': 'Interface',
        'classification': 'CONFLICT',
        'vendor_change_type': 'MODIFIED',
        'customer_change_type': 'MODIFIED',
        'review_status': 'pending'
    },
    'change_index': 0,
    'total_changes': 78,
    'merge_guidance': {
        'recommendation': 'MANUAL_MERGE',
        'reason': 'Both vendor and customer modified...',
        'conflicts': [
            {'field': 'sail_code', 'description': '...'},
            {'field': 'parameters', 'description': '...'}
        ]
    },
    'comparison_data': {
        # Object-specific comparison data
    }
}
```

---

*Continued in next section...*
