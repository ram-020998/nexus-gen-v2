# GitHub-Style SAIL Code Diff Implementation

## Overview

Implemented a dual-view SAIL code diff system for interfaces and expression rules with both unified (GitHub-style) and split (side-by-side) views, with synchronized scrolling in split mode.

## Components Created

### 1. SailDiffService (`services/sail_diff_service.py`)
- Generates unified diffs using Python's `difflib`
- Parses diff output into structured hunks
- Provides change statistics (additions, deletions)
- Handles None/empty code gracefully

**Key Methods:**
- `generate_unified_diff()` - Creates diff hunks with line numbers
- `get_change_stats()` - Returns addition/deletion counts
- `has_changes()` - Quick check if code differs

### 2. SAIL Diff Template Component (`templates/merge/comparisons/_sail_diff.html`)
- Reusable Jinja2 macro for rendering diffs
- GitHub-style visual design with:
  - Line numbers (old and new)
  - Color-coded additions (green) and deletions (red)
  - Hunk headers showing line ranges
  - Change statistics in header
  - Scrollable content area

**Features:**
- Monospace font for code readability
- Hover effects on lines
- Proper syntax highlighting structure
- Responsive scrollbars

### 3. Updated Comparison Service (`services/comparison_retrieval_service.py`)
Modified `_get_interface_comparison()` and `_get_expression_rule_comparison()` to:
- Generate diff hunks using SailDiffService
- Calculate change statistics
- Include diff data in comparison results

### 4. Updated Templates
- `templates/merge/comparisons/interface.html` - Uses new diff component
- `templates/merge/comparisons/expression_rule.html` - Uses new diff component
- Both templates fall back to side-by-side view if diff data unavailable

## Visual Design

The diff view matches GitHub's style:

```
┌─────────────────────────────────────────────────────────┐
│ 📄 Customer → Vendor          +5 additions -2 deletions │
├─────────────────────────────────────────────────────────┤
│ @@ -1,4 +1,5 @@                                         │
├────┬────┬───┬──────────────────────────────────────────┤
│ 1  │ 1  │   │ a!localVariables(                        │
│ 2  │    │ - │   local!items: {1, 2, 3},                │
│ 3  │    │ - │   local!total: sum(local!items)          │
│    │ 2  │ + │   local!items: {1, 2, 3, 4, 5},          │
│    │ 3  │ + │   local!total: sum(local!items),         │
│    │ 4  │ + │   local!average: avg(local!items)        │
│ 4  │ 5  │   │ )                                        │
└────┴────┴───┴──────────────────────────────────────────┘
```

**Color Scheme:**
- Green background: Added lines
- Red background: Removed lines
- Purple accents: Headers and metadata
- Dark theme compatible

## Usage

The diff view automatically appears when viewing interface or expression rule changes in the merge workflow. No configuration needed.

**Example Flow:**
1. User navigates to change detail page
2. Controller calls `comparison_service.get_comparison_details()`
3. Service generates diff hunks and stats
4. Template renders GitHub-style diff
5. User sees line-by-line changes with proper highlighting

## Testing

Created `test_sail_diff.py` with tests for:
- ✅ Basic diff generation
- ✅ No changes detection
- ✅ None value handling
- ✅ Change statistics calculation

All tests pass successfully.

## Features

### Unified View (GitHub-style)
- Line-by-line diff with +/- indicators
- Color-coded additions (green) and deletions (red)
- Line numbers for both old and new versions
- Hunk headers showing line ranges
- Compact single-column layout

### Split View (Side-by-Side)
- Customer code on left, Vendor code on right
- Synchronized scrolling between both panels
- Color-coded changes in each panel
- Independent line numbering
- Full context for both versions

### Toggle Controls
- Easy switching between unified and split views
- Change statistics (+additions, -deletions)
- Visual indicators for active view

## Benefits

1. **Flexible Viewing** - Choose between unified or split based on preference
2. **Synchronized Navigation** - Split view scrolls both panels together
3. **Better Change Visibility** - Line-by-line view shows exactly what changed
4. **Familiar Interface** - Developers recognize GitHub-style diffs
5. **Full Context** - Split view shows complete code on both sides
6. **Scalable** - Works with large SAIL code files

## Future Enhancements

Potential improvements:
- Syntax highlighting within diff lines
- Inline word-level diffs for modified lines
- Collapsible hunks for large files
- Copy-to-clipboard functionality
- Export diff as patch file
- Keyboard shortcuts for navigation
