# Merge UI Components

This directory contains reusable UI components for the three-way merge interface. All components follow a consistent design system and are built to work with the NexusGen theme.

## Components

### 1. Classification Badge (`classification_badge.html`)

Displays a colored badge indicating the classification of a change.

**Usage:**
```jinja
{% include 'merge/components/classification_badge.html' with classification='NO_CONFLICT' %}
{% include 'merge/components/classification_badge.html' with classification='CONFLICT', size='lg' %}
```

**Parameters:**
- `classification` (required): NO_CONFLICT, CONFLICT, NEW, or DELETED
- `size` (optional): 'sm', 'md' (default), or 'lg'

**Classifications:**
- **NO_CONFLICT**: Green badge - vendor changes that don't conflict with customer changes
- **CONFLICT**: Red badge - vendor changes that conflict with customer modifications
- **NEW**: Blue badge - new objects added by vendor
- **DELETED**: Gray badge - objects removed by customer

---

### 2. Object Type Icon (`object_type_icon.html`)

Displays an icon representing the Appian object type with optional label.

**Usage:**
```jinja
{% include 'merge/components/object_type_icon.html' with object_type='Interface' %}
{% include 'merge/components/object_type_icon.html' with object_type='Process Model', size='lg', show_label=true %}
```

**Parameters:**
- `object_type` (required): Interface, Expression Rule, Process Model, Record Type, CDT, Integration, Web API, Site, Group, Constant, or Connected System
- `size` (optional): 'sm', 'md' (default), or 'lg'
- `show_label` (optional): true/false (default: false) - displays object type name next to icon

**Supported Object Types:**
- **Interface**: Window icon (purple)
- **Expression Rule**: Function icon (cyan)
- **Process Model**: Diagram icon (pink)
- **Record Type**: Database icon (green)
- **CDT**: Cube icon (orange)
- **Integration**: Plug icon (indigo)
- **Web API**: Globe icon (teal)
- **Site**: Sitemap icon (purple)
- **Group**: Users icon (rose)
- **Constant**: Hashtag icon (lime)
- **Connected System**: Server icon (sky blue)

---

### 3. Progress Bar (`progress_bar.html`)

Displays a progress bar with current/total values and percentage.

**Usage:**
```jinja
{% include 'merge/components/progress_bar.html' with current=5, total=20 %}
{% include 'merge/components/progress_bar.html' with current=15, total=20, variant='success', label='Processing...' %}
```

**Parameters:**
- `current` (required): Current progress value
- `total` (required): Total value
- `label` (optional): Custom label text (default: "Change X of Y")
- `show_percentage` (optional): true/false (default: true)
- `variant` (optional): 'default', 'success', 'warning', 'danger' (default: 'default')

**Variants:**
- **default**: Purple to teal gradient
- **success**: Green gradient
- **warning**: Orange gradient
- **danger**: Red gradient

---

### 4. SAIL Code Diff (`sail_code_diff.html`)

Displays SAIL code comparison with tabbed views for base, customer, and vendor versions.

**Usage:**
```jinja
{% include 'merge/components/sail_code_diff.html' with base_code=base_sail, vendor_code=vendor_sail %}
{% include 'merge/components/sail_code_diff.html' with base_code=base_sail, vendor_code=vendor_sail, customer_code=customer_sail, title='Interface Code' %}
```

**Parameters:**
- `base_code` (required): SAIL code from base version (Package A)
- `vendor_code` (required): SAIL code from vendor version (Package C)
- `customer_code` (optional): SAIL code from customer version (Package B)
- `title` (optional): Custom title (default: "SAIL Code Comparison")
- `show_tabs` (optional): true/false (default: true) - enables tabbed view

**Features:**
- Tabbed interface for Base (A), Customer (B), Vendor (C), and Side-by-Side views
- Copy to clipboard functionality
- Syntax highlighting for SAIL code
- Responsive side-by-side diff view
- Scrollable code blocks with max height

---

### 5. Navigation Buttons (`navigation_buttons.html`)

Provides navigation controls for moving through changes in the working set.

**Usage:**
```jinja
{% include 'merge/components/navigation_buttons.html' with session=session, change=change, prev_change_id=prev_id, next_change_id=next_id %}
```

**Parameters:**
- `session` (required): MergeSession object
- `change` (required): Change object
- `prev_change_id` (optional): ID of previous change
- `next_change_id` (optional): ID of next change
- `show_back` (optional): true/false (default: true) - shows "Back to Summary" button
- `show_mark_reviewed` (optional): true/false (default: true) - shows "Mark as Reviewed" button

**Features:**
- Previous/Next navigation with keyboard shortcuts (← →)
- Mark as Reviewed button with keyboard shortcut (R)
- Back to Summary button
- Complete Review button on last change
- Keyboard shortcut hints
- Disabled state for unavailable actions
- Auto-navigation after marking as reviewed

**Keyboard Shortcuts:**
- `←` (Left Arrow): Navigate to previous change
- `→` (Right Arrow): Navigate to next change
- `R`: Mark current change as reviewed and move to next

---

### 6. Notes Section (`notes_section.html`)

Provides a textarea for adding merge notes with save functionality and status indicators.

**Usage:**
```jinja
{% include 'merge/components/notes_section.html' with session=session, change=change %}
{% include 'merge/components/notes_section.html' with session=session, change=change, auto_save=true, rows=6 %}
```

**Parameters:**
- `session` (required): MergeSession object
- `change` (required): Change object
- `title` (optional): Custom title (default: "Merge Notes")
- `placeholder` (optional): Custom placeholder text
- `rows` (optional): Number of textarea rows (default: 4)
- `show_save_button` (optional): true/false (default: true)
- `auto_save` (optional): true/false (default: false) - auto-saves on blur

**Features:**
- Real-time save status indicator (Saved/Unsaved/Saving)
- Character count display
- Last saved timestamp
- Save and Clear buttons
- Auto-save option (on blur or every 30 seconds)
- Unsaved changes warning before page navigation
- Responsive design

**Status Indicators:**
- **Saved**: Green indicator - notes are saved
- **Unsaved**: Orange indicator - notes have been modified
- **Saving**: Purple indicator with pulse animation - save in progress

---

## Design System

All components follow the NexusGen design system:

### Colors
- **Primary (Purple)**: `#8b5cf6` - Main brand color
- **Teal**: `#06b6d4` - Secondary accent
- **Green**: `#10b981` - Success states
- **Orange**: `#f59e0b` - Warning states
- **Red**: `#ef4444` - Error/conflict states
- **Pink**: `#ec4899` - Accent color

### Typography
- **Font Family**: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif
- **Code Font**: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace

### Spacing
- Uses consistent spacing scale: 0.25rem, 0.5rem, 0.75rem, 1rem, 1.5rem, 2rem

### Border Radius
- Small: 6px
- Medium: 8px
- Large: 12px

### Transitions
- Standard: `all 0.2s ease`
- Hover effects: `transform: translateY(-2px)`

---

## Theme Support

All components support both dark and light themes through CSS custom properties:

```css
:root {
    --bg-primary: #0f1419;
    --bg-secondary: #1a1f2e;
    --bg-card: #1a1f2e;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --border-color: #374151;
    --purple: #8b5cf6;
    --teal: #06b6d4;
    --green: #10b981;
}

[data-theme="light"] {
    --bg-primary: #f8fafc;
    --bg-secondary: #ffffff;
    --bg-card: #ffffff;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --border-color: #e2e8f0;
}
```

---

## Responsive Design

All components are responsive and adapt to mobile screens:

- **Desktop**: Full features with all labels and hints
- **Tablet**: Adjusted layouts with maintained functionality
- **Mobile**: Stacked layouts, hidden non-essential elements

Breakpoints:
- Mobile: `max-width: 480px`
- Tablet: `max-width: 768px`

---

## Integration Example

Here's a complete example of using multiple components together:

```jinja
{% extends "base.html" %}

{% block content %}
<div class="merge-detail-page">
    {# Progress Bar #}
    {% include 'merge/components/progress_bar.html' with 
        current=change.display_order, 
        total=session.total_changes 
    %}
    
    {# Object Header with Icon and Badge #}
    <div class="object-header">
        {% include 'merge/components/object_type_icon.html' with 
            object_type=object.object_type, 
            size='lg' 
        %}
        
        <h2>{{ object.name }}</h2>
        
        {% include 'merge/components/classification_badge.html' with 
            classification=change.classification, 
            size='lg' 
        %}
    </div>
    
    {# SAIL Code Diff #}
    {% include 'merge/components/sail_code_diff.html' with 
        base_code=base_version.sail_code,
        customer_code=customer_version.sail_code,
        vendor_code=vendor_version.sail_code
    %}
    
    {# Notes Section #}
    {% include 'merge/components/notes_section.html' with 
        session=session, 
        change=change,
        auto_save=true
    %}
    
    {# Navigation #}
    {% include 'merge/components/navigation_buttons.html' with 
        session=session, 
        change=change,
        prev_change_id=prev_id,
        next_change_id=next_id
    %}
</div>
{% endblock %}
```

---

## API Endpoints Used

Components make AJAX calls to these endpoints:

### Save Notes
```
POST /merge/<reference_id>/changes/<change_id>/notes
Content-Type: application/json

{
    "notes": "User's notes text"
}

Response:
{
    "success": true,
    "message": "Notes saved successfully"
}
```

### Mark as Reviewed
```
POST /merge/<reference_id>/changes/<change_id>/review
Content-Type: application/json

{
    "reviewed": true
}

Response:
{
    "success": true,
    "message": "Change marked as reviewed"
}
```

---

## Browser Support

Components are tested and supported on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## Accessibility

All components follow accessibility best practices:
- Semantic HTML elements
- ARIA labels and roles
- Keyboard navigation support
- Focus indicators
- Color contrast ratios meet WCAG AA standards
- Screen reader friendly

---

## Performance

Components are optimized for performance:
- Minimal JavaScript
- CSS animations use GPU-accelerated properties
- Lazy loading for code blocks
- Debounced auto-save
- Efficient DOM updates

---

## Future Enhancements

Planned improvements:
- Advanced syntax highlighting for SAIL code
- Inline diff highlighting (line-by-line)
- Collapsible sections for large code blocks
- Export notes to PDF/Markdown
- Bulk review actions
- Custom keyboard shortcut configuration
