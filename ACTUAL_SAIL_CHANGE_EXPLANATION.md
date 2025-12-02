# Actual SAIL Change Column - Explanation

## What is Stored in the "Actual SAIL Change" Column?

The "Actual SAIL Change" column in the generated Excel report contains **meaningful descriptions of what actually changed** between package versions, not just raw SAIL code.

## Content Based on Change Type

### 1. NEW Objects (Classification: NEW)
**What's shown:**
- Message: "NEW: Added in vendor version"
- Preview of the SAIL code (first 500 characters) if available
- Or just the message if no SAIL code exists

**Example:**
```
NEW: Added in vendor version

a!localVariables(
  local!data: {
    a!map(id: 1, name: "Item 1"),
    a!map(id: 2, name: "Item 2")
  },
  a!gridField(
    ...
  )
)
```

### 2. DELETED Objects (Classification: DELETED)
**What's shown:**
- Message: "DELETED: Removed in vendor version"
- Original SAIL code from base version (first 500 characters)
- Shows what was removed

**Example:**
```
DELETED: Removed in vendor version

Original code:
a!localVariables(
  local!oldData: {},
  a!textField(
    label: "Old Field",
    value: local!oldData
  )
)
```

### 3. MODIFIED Objects with SAIL Code (Classification: NO_CONFLICT or CONFLICT)
**What's shown:**
- Message: "MODIFIED: SAIL code changed"
- **GitHub-style unified diff** showing:
  - Lines removed (prefixed with `-`)
  - Lines added (prefixed with `+`)
  - Context lines (prefixed with space)
  - Hunk headers showing line numbers

**Example:**
```
MODIFIED: SAIL code changed

@@ -5,3 +5,4 @@
   local!data: {},
-  a!textField(
-    label: "Old Label",
+  a!textField(
+    label: "New Label",
+    required: true,
     value: local!data
   )
```

**Diff Format Explanation:**
- `@@ -5,3 +5,4 @@` = Hunk header (old line 5, 3 lines → new line 5, 4 lines)
- Lines starting with `-` = Removed from base version
- Lines starting with `+` = Added in new vendor version
- Lines with just spaces = Unchanged context lines

### 4. MODIFIED Objects without SAIL Code (e.g., CDTs, Constants)
**What's shown:**
- Message: "MODIFIED: Fields/properties changed"
- Comparison of field structures
- Shows base version fields vs vendor version fields

**Example:**
```
MODIFIED: Fields/properties changed
Base: {'name': 'string', 'age': 'integer', 'email': 'string'}
Vendor: {'name': 'string', 'age': 'integer', 'email': 'string', 'phone': 'string'}
```

### 5. DEPRECATED Objects
**What's shown:**
- Message: "DEPRECATED: Object marked as deprecated in vendor version"

### 6. Other Changes
**What's shown:**
- Summary of change types
- Format: "Change Type: Vendor=MODIFIED, Customer=REMOVED"

## Technical Implementation

### How It Works

1. **Retrieves All Three Versions:**
   - Base version (Package A)
   - Customer version (Package B)
   - New vendor version (Package C)

2. **Analyzes Change Type:**
   - Checks classification (NEW, DELETED, CONFLICT, NO_CONFLICT)
   - Checks vendor change type (MODIFIED, NEW, DEPRECATED, REMOVED)
   - Checks customer change type

3. **Generates Appropriate Content:**
   - For SAIL objects: Uses `SailDiffService` to generate unified diffs
   - For non-SAIL objects: Compares fields/properties
   - For NEW/DELETED: Shows relevant code preview

4. **Formats for Excel:**
   - Truncates to 1000 characters for readability
   - Uses monospace font (Courier New) for code
   - Wraps text for better display

### Code Location

The logic is implemented in:
- **File:** `services/report_generation_service.py`
- **Method:** `_generate_actual_change_description()`
- **Helper:** `_format_diff_hunks()` for diff formatting
- **Dependency:** `services/sail_diff_service.py` for diff generation

## Benefits of This Approach

### ✅ Shows What Actually Changed
Instead of dumping full SAIL code, you see:
- Specific lines that were added
- Specific lines that were removed
- Context around the changes

### ✅ Easier to Review
- Analysts can quickly understand the impact
- No need to manually compare full code blocks
- Highlights only the differences

### ✅ Works for All Object Types
- SAIL objects: Shows code diffs
- CDTs: Shows field changes
- Constants: Shows value changes
- Process Models: Shows structural changes

### ✅ Handles Edge Cases
- Objects with no SAIL code
- Objects that only exist in one version
- Objects with only metadata changes

## Example Scenarios

### Scenario 1: Interface with SAIL Changes
```
Object: Customer Search Interface
Classification: CONFLICT
Vendor Change: MODIFIED
Customer Change: MODIFIED

Actual SAIL Change:
MODIFIED: SAIL code changed

@@ -12,5 +12,7 @@
   a!textField(
     label: "Customer Name",
-    value: local!searchText
+    value: local!searchText,
+    placeholder: "Enter customer name",
+    required: true
   )
```

### Scenario 2: New Interface
```
Object: New Dashboard Interface
Classification: NEW
Vendor Change: NEW
Customer Change: N/A

Actual SAIL Change:
NEW: Added in vendor version

a!dashboardLayout(
  header: a!dashboardHeader(
    title: "Customer Dashboard"
  ),
  columns: {
    a!dashboardColumn(
      contents: {
        a!cardLayout(...)
      }
    )
  }
)
```

### Scenario 3: Deleted Group
```
Object: All Users
Classification: DELETED
Vendor Change: REMOVED
Customer Change: REMOVED

Actual SAIL Change:
DELETED: Object removed in vendor version
(No SAIL code - Group object)
```

### Scenario 4: CDT Field Changes
```
Object: Customer CDT
Classification: NO_CONFLICT
Vendor Change: MODIFIED
Customer Change: N/A

Actual SAIL Change:
MODIFIED: Fields/properties changed
Base: {'id': 'integer', 'name': 'string', 'email': 'string'}
Vendor: {'id': 'integer', 'name': 'string', 'email': 'string', 'phone': 'string', 'address': 'string'}
```

## Limitations

1. **Truncation:** Content is truncated to 1000 characters for Excel readability
2. **Diff Context:** Shows only 2 context lines around changes (configurable)
3. **Hunk Limit:** Shows first 3 hunks only (for very large changes)
4. **Line Limit:** Shows first 20 lines per hunk

## Future Enhancements

Potential improvements:
- [ ] Add full diff in separate sheet for large changes
- [ ] Include customer version in diff (3-way diff)
- [ ] Add syntax highlighting in Excel (colored cells)
- [ ] Generate side-by-side comparison view
- [ ] Include line numbers in diff output
- [ ] Add statistics (lines added/removed)
- [ ] Link to detailed comparison in UI

## Summary

The "Actual SAIL Change" column provides **actionable, meaningful information** about what changed, making it easy for merge analysts to:
- Understand the scope of changes
- Identify potential conflicts
- Make informed merge decisions
- Review changes efficiently

Instead of showing raw SAIL code, it shows **the delta** - what was added, removed, or modified - which is exactly what analysts need to see.
