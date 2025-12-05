# Three-Way Merge UI & Template Specification - Part 2

**Comparison Templates**

---

## 4. Comparison Templates

### 4.1 Base Comparison Template (`_base_comparison.html`)

**Purpose**: Base template for all object-specific comparisons

**Structure**:
```jinja2
{% extends "base.html" %}

{% block content %}
<!-- Progress Bar (inherited) -->
<!-- Object Header (inherited) -->
<!-- Merge Guidance (inherited) -->

<!-- Object-Specific Comparison Content -->
{% block comparison_content %}
<!-- Override in child templates -->
{% endblock %}

<!-- User Notes (inherited) -->
<!-- Navigation Buttons (inherited) -->
{% endblock %}
```

**Shared Components**:
- Progress bar
- Object header with icon
- Merge guidance card
- User notes section
- Navigation buttons

---

### 4.2 Interface Comparison (`interface_comparison.html`)

**Purpose**: Compare interface SAIL code, parameters, and security

**Sections**:

#### SAIL Code Comparison
```
┌─────────────────────────────────────────────────────────┐
│ SAIL Code Comparison                                    │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐ ┌─────────────────────┐        │
│ │ Before (Base/Cust)  │ │ After (Vendor)      │        │
│ │ ─────────────────── │ │ ─────────────────── │        │
│ │ a!localVariables(   │ │ a!localVariables(   │        │
│ │   local!data: {...},│ │   local!data: {...},│        │
│ │ - local!old: null,  │ │ + local!new: null,  │        │
│ │   a!sectionLayout(  │ │   a!sectionLayout(  │        │
│ │     ...             │ │     ...             │        │
│ │ )                   │ │ )                   │        │
│ └─────────────────────┘ └─────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

#### Parameters Comparison
```
┌─────────────────────────────────────────────────────────┐
│ Parameters                                              │
├─────────────────────────────────────────────────────────┤
│ Added Parameters (2)                                    │
│ • newParam1 (Text) - Required                          │
│ • newParam2 (Number) - Optional, Default: 0            │
├─────────────────────────────────────────────────────────┤
│ Removed Parameters (1)                                  │
│ • oldParam (Text)                                       │
├─────────────────────────────────────────────────────────┤
│ Modified Parameters (1)                                 │
│ • existingParam                                         │
│   Before: Text, Optional                                │
│   After: Text, Required                                 │
└─────────────────────────────────────────────────────────┘
```

#### Security Comparison
```
┌─────────────────────────────────────────────────────────┐
│ Security Settings                                       │
├─────────────────────────────────────────────────────────┤
│ Added Roles (1)                                         │
│ • Admin - View & Edit                                   │
├─────────────────────────────────────────────────────────┤
│ Removed Roles (0)                                       │
└─────────────────────────────────────────────────────────┘
```

**Data Requirements**:
```python
{
    'change': {...},
    'base_object': {
        'sail_code': '...',
        'parameters': [
            {'name': 'param1', 'type': 'Text', 'required': True}
        ],
        'security': [
            {'role': 'User', 'permission': 'View'}
        ]
    },
    'customer_object': {...},  # Same structure
    'vendor_object': {...},    # Same structure
    'interface_comparison': {
        'sail_code_diff': '...',  # Diff HTML
        'parameters_added': [...],
        'parameters_removed': [...],
        'parameters_modified': [...],
        'security_changes': [...]
    }
}
```

---

### 4.3 Expression Rule Comparison (`expression_rule_comparison.html`)

**Purpose**: Compare expression rule SAIL code, inputs, and output type

**Sections**:

#### SAIL Code Comparison
(Same as interface)

#### Inputs Comparison
```
┌─────────────────────────────────────────────────────────┐
│ Rule Inputs                                             │
├─────────────────────────────────────────────────────────┤
│ Added Inputs (1)                                        │
│ • newInput (Text) - Required                            │
├─────────────────────────────────────────────────────────┤
│ Modified Inputs (1)                                     │
│ • existingInput                                         │
│   Before: Number, Optional, Default: 0                  │
│   After: Number, Required                               │
└─────────────────────────────────────────────────────────┘
```

#### Output Type
```
┌─────────────────────────────────────────────────────────┐
│ Output Type                                             │
├─────────────────────────────────────────────────────────┤
│ Before: Text                                            │
│ After: List of Text                                     │
└─────────────────────────────────────────────────────────┘
```

---

### 4.4 Process Model Comparison (`process_model_comparison.html`)

**Purpose**: Compare process model nodes, flows, and variables

**Sections**:

#### Summary Statistics
```
┌─────────────────────────────────────────────────────────┐
│ Process Model Summary                                   │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│ │ 15 Nodes    │ │ 18 Flows    │ │ 5 Variables │       │
│ │ +2 -1       │ │ +3 -1       │ │ +1 -0       │       │
│ └─────────────┘ └─────────────┘ └─────────────┘       │
└─────────────────────────────────────────────────────────┘
```

#### Mermaid Diagram
```
┌─────────────────────────────────────────────────────────┐
│ Process Flow Diagram                                    │
├─────────────────────────────────────────────────────────┤
│ [Tabs: Base | Customer | Vendor | Diff]                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│     ┌─────────┐                                        │
│     │  Start  │                                        │
│     └────┬────┘                                        │
│          │                                             │
│          ▼                                             │
│     ┌─────────┐                                        │
│     │ Task 1  │ (Added)                                │
│     └────┬────┘                                        │
│          │                                             │
│          ▼                                             │
│     ┌─────────┐                                        │
│     │  End    │                                        │
│     └─────────┘                                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Nodes Comparison
```
┌─────────────────────────────────────────────────────────┐
│ Nodes                                                   │
├─────────────────────────────────────────────────────────┤
│ Added Nodes (2)                                         │
│ • Task_NewApproval (User Input Task)                   │
│ • Gateway_CheckStatus (XOR Gateway)                     │
├─────────────────────────────────────────────────────────┤
│ Removed Nodes (1)                                       │
│ • Task_OldValidation (Script Task)                      │
├─────────────────────────────────────────────────────────┤
│ Modified Nodes (3)                                      │
│ • Task_Submit                                           │
│   Properties changed: assignee, form                    │
└─────────────────────────────────────────────────────────┘
```

#### Flows Comparison
```
┌─────────────────────────────────────────────────────────┐
│ Flows                                                   │
├─────────────────────────────────────────────────────────┤
│ Added Flows (3)                                         │
│ • Start → Task_NewApproval                              │
│ • Task_NewApproval → Gateway_CheckStatus                │
│ • Gateway_CheckStatus → End (condition: approved)       │
└─────────────────────────────────────────────────────────┘
```

#### Variables Comparison
```
┌─────────────────────────────────────────────────────────┐
│ Variables                                               │
├─────────────────────────────────────────────────────────┤
│ Added Variables (1)                                     │
│ • approvalStatus (Text) - Parameter                     │
└─────────────────────────────────────────────────────────┘
```

**Data Requirements**:
```python
{
    'change': {...},
    'base_object': {
        'nodes': [
            {'node_id': 'n1', 'node_type': 'Start', 'node_name': 'Start'}
        ],
        'flows': [
            {'from_node_id': 'n1', 'to_node_id': 'n2', 'label': ''}
        ],
        'variables': [
            {'name': 'var1', 'type': 'Text', 'is_parameter': True}
        ]
    },
    'vendor_object': {...},
    'process_model_comparison': {
        'nodes_added': [...],
        'nodes_removed': [...],
        'nodes_modified': [...],
        'flows_added': [...],
        'flows_removed': [...],
        'flows_modified': [...],
        'variables_changed': [...],
        'mermaid_diagram': '...'  # Mermaid syntax
    }
}
```

---

### 4.5 Record Type Comparison (`record_type_comparison.html`)

**Purpose**: Compare record type fields, relationships, views, and actions

**Sections**:

#### Fields Comparison
```
┌─────────────────────────────────────────────────────────┐
│ Fields                                                  │
├─────────────────────────────────────────────────────────┤
│ Added Fields (2)                                        │
│ • newField1 (Text) - Required                          │
│ • newField2 (Number)                                    │
├─────────────────────────────────────────────────────────┤
│ Modified Fields (1)                                     │
│ • existingField                                         │
│   Before: Text, Optional                                │
│   After: Text, Required, Primary Key                    │
└─────────────────────────────────────────────────────────┘
```

#### Relationships Comparison
```
┌─────────────────────────────────────────────────────────┐
│ Relationships                                           │
├─────────────────────────────────────────────────────────┤
│ Added Relationships (1)                                 │
│ • relatedOrders (One-to-Many) → Order Record Type      │
└─────────────────────────────────────────────────────────┘
```

#### Views & Actions
```
┌─────────────────────────────────────────────────────────┐
│ Views                                                   │
├─────────────────────────────────────────────────────────┤
│ Modified Views (1)                                      │
│ • Summary View - Configuration changed                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Actions                                                 │
├─────────────────────────────────────────────────────────┤
│ Added Actions (1)                                       │
│ • Export to Excel                                       │
└─────────────────────────────────────────────────────────┘
```

---

### 4.6 CDT Comparison (`cdt_comparison.html`)

**Purpose**: Compare CDT fields and namespace

**Sections**:

#### Namespace
```
┌─────────────────────────────────────────────────────────┐
│ Namespace                                               │
├─────────────────────────────────────────────────────────┤
│ Before: urn:com:appian:types:OLD                        │
│ After: urn:com:appian:types:NEW                         │
└─────────────────────────────────────────────────────────┘
```

#### Fields Comparison
```
┌─────────────────────────────────────────────────────────┐
│ Fields                                                  │
├─────────────────────────────────────────────────────────┤
│ Added Fields (2)                                        │
│ • newField (Text)                                       │
│ • anotherField (Number, List)                           │
├─────────────────────────────────────────────────────────┤
│ Modified Fields (1)                                     │
│ • existingField                                         │
│   Before: Text                                          │
│   After: Text, Required                                 │
└─────────────────────────────────────────────────────────┘
```

---

### 4.7 Integration Comparison (`integration_comparison.html`)

**Purpose**: Compare integration SAIL code, connection, auth, and endpoint

**Sections**:
- SAIL Code Comparison (same as interface)
- Connection Changes
- Authentication Changes
- Endpoint Changes

---

### 4.8 Web API Comparison (`web_api_comparison.html`)

**Purpose**: Compare web API SAIL code, endpoint, and methods

**Sections**:
- SAIL Code Comparison
- Endpoint Changes
- HTTP Methods (GET, POST, PUT, DELETE)

---

### 4.9 Site Comparison (`site_comparison.html`)

**Purpose**: Compare site pages and hierarchy

**Sections**:

#### Page Hierarchy
```
┌─────────────────────────────────────────────────────────┐
│ Page Hierarchy                                          │
├─────────────────────────────────────────────────────────┤
│ [Tree View]                                             │
│ ▼ Home                                                  │
│   ├─ Dashboard                                          │
│   ├─ Reports (Added)                                    │
│   └─ Settings                                           │
│       ├─ User Settings                                  │
│       └─ System Settings (Modified)                     │
└─────────────────────────────────────────────────────────┘
```

---

### 4.10 Group Comparison (`group_comparison.html`)

**Purpose**: Compare group members and parent

**Sections**:
- Members Added/Removed
- Parent Group Changed

---

### 4.11 Constant Comparison (`constant_comparison.html`)

**Purpose**: Compare constant value, type, and scope

**Sections**:

#### Value Comparison
```
┌─────────────────────────────────────────────────────────┐
│ Value                                                   │
├─────────────────────────────────────────────────────────┤
│ Before: "OLD_VALUE"                                     │
│ After: "NEW_VALUE"                                      │
└─────────────────────────────────────────────────────────┘
```

#### Type & Scope
```
┌─────────────────────────────────────────────────────────┐
│ Type                                                    │
├─────────────────────────────────────────────────────────┤
│ Before: Text                                            │
│ After: Text                                             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Scope                                                   │
├─────────────────────────────────────────────────────────┤
│ Before: Application                                     │
│ After: System                                           │
└─────────────────────────────────────────────────────────┘
```

---

### 4.12 Connected System Comparison (`connected_system_comparison.html`)

**Purpose**: Compare connected system properties and type

**Sections**:
- System Type Changed
- Properties Added/Removed/Modified

---

## 5. Component Library

### 5.1 Classification Badges

```html
<!-- NO_CONFLICT -->
<span class="badge classification-no-conflict">
    <i class="fas fa-check-circle"></i> No Conflict
</span>

<!-- CONFLICT -->
<span class="badge classification-conflict">
    <i class="fas fa-exclamation-triangle"></i> Conflict
</span>

<!-- NEW -->
<span class="badge classification-new">
    <i class="fas fa-plus-circle"></i> New
</span>

<!-- DELETED -->
<span class="badge classification-deleted">
    <i class="fas fa-trash-alt"></i> Deleted
</span>
```

**CSS**:
```css
.classification-no-conflict {
    background-color: #10b981;
    color: white;
}

.classification-conflict {
    background-color: #ef4444;
    color: white;
}

.classification-new {
    background-color: #3b82f6;
    color: white;
}

.classification-deleted {
    background-color: #6b7280;
    color: white;
}
```

---

### 5.2 Object Type Icons

```html
<!-- Interface -->
<i class="fas fa-window-maximize"></i>

<!-- Expression Rule -->
<i class="fas fa-function"></i>

<!-- Process Model -->
<i class="fas fa-project-diagram"></i>

<!-- Record Type -->
<i class="fas fa-database"></i>

<!-- CDT -->
<i class="fas fa-cube"></i>

<!-- Integration -->
<i class="fas fa-plug"></i>

<!-- Web API -->
<i class="fas fa-globe"></i>

<!-- Site -->
<i class="fas fa-sitemap"></i>

<!-- Group -->
<i class="fas fa-users"></i>

<!-- Constant -->
<i class="fas fa-hashtag"></i>

<!-- Connected System -->
<i class="fas fa-server"></i>
```

---

### 5.3 Progress Bar

```html
<div class="progress-card">
    <div class="progress-header">
        <div class="progress-info">
            <span class="progress-label">Progress</span>
            <span class="progress-count">{{ change_index + 1 }} of {{ total_changes }}</span>
        </div>
        <div class="progress-percentage">
            {{ ((change_index + 1) / total_changes * 100)|int }}%
        </div>
    </div>
    <div class="progress-bar-container">
        <div class="progress-bar-fill" 
             style="width: {{ ((change_index + 1) / total_changes * 100) }}%">
        </div>
    </div>
</div>
```

---

### 5.4 SAIL Code Diff

```html
<div class="sail-diff-container">
    <div class="diff-side">
        <div class="diff-side-header before">
            <i class="fas fa-minus-circle"></i> Before
        </div>
        <div class="diff-code-content">
            <pre><code class="language-sail">{{ sail_code_before }}</code></pre>
        </div>
    </div>
    <div class="diff-side">
        <div class="diff-side-header after">
            <i class="fas fa-plus-circle"></i> After
        </div>
        <div class="diff-code-content">
            <pre><code class="language-sail">{{ sail_code_after }}</code></pre>
        </div>
    </div>
</div>
```

---

*Continued in next section...*
