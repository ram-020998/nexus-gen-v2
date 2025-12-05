# NO_CONFLICT Display Logic Update

**Date:** December 4, 2025  
**Feature:** Dynamic comparison display for NO_CONFLICT changes

---

## Overview

Updated the NO_CONFLICT comparison display logic to show the appropriate comparison based on whether vendor or customer made changes.

## Requirements

For NO_CONFLICT objects:

1. **If vendor change is None AND customer change is Modified/Added**  
   → Display: **Customer vs Base**  
   → Labels: "Vendor Base" (left) vs "Customer" (right)

2. **If vendor change is Modified/Added**  
   → Display: **Vendor Base vs Vendor Latest** (existing behavior)  
   → Labels: "Vendor Base" (left) vs "Vendor Latest" (right)

## Changes Made

### 1. Backend Service Updates

**File:** `services/comparison_retrieval_service.py`

#### Added Helper Method

```python
def _determine_comparison_strategy(
    self,
    change: Change,
    base_package_id: int,
    customer_package_id: int,
    new_vendor_package_id: int
) -> Dict[str, Any]:
    """
    Determine which packages to compare based on classification and change types.
    
    Returns:
        Dict with keys:
        - old_package_id: Package ID for left side
        - new_package_id: Package ID for right side
        - old_label: Label for left side
        - new_label: Label for right side
        - comparison_type: 'customer_only', 'vendor_changes', or 'conflict'
    """
    if change.classification == 'NO_CONFLICT':
        # NO_CONFLICT logic:
        # 1. If vendor change is None AND customer change is Modified/Added → Show Customer vs Base
        # 2. If vendor change is Modified/Added → Show Vendor Base vs Vendor Latest
        if not change.vendor_change_type and change.customer_change_type in ['MODIFIED', 'ADDED']:
            # Customer-only changes: compare base vs customer
            return {
                'old_package_id': base_package_id,
                'new_package_id': customer_package_id,
                'old_label': 'Vendor Base',
                'new_label': 'Customer',
                'comparison_type': 'customer_only'
            }
        else:
            # Vendor changes: compare base vs vendor latest
            return {
                'old_package_id': base_package_id,
                'new_package_id': new_vendor_package_id,
                'old_label': 'Vendor Base',
                'new_label': 'Vendor Latest',
                'comparison_type': 'vendor_changes'
            }
    else:
        # CONFLICT: compare vendor vs customer
        return {
            'old_package_id': new_vendor_package_id,
            'new_package_id': customer_package_id,
            'old_label': 'Vendor Latest',
            'new_label': 'Customer',
            'comparison_type': 'conflict'
        }
```

#### Updated Comparison Methods

All comparison methods now use the `_determine_comparison_strategy()` helper:

- `_get_interface_comparison()`
- `_get_expression_rule_comparison()`
- `_get_process_model_comparison()`
- `_get_cdt_comparison()`
- `_get_record_type_comparison()`
- `_get_constant_comparison()`
- `_get_group_comparison()`
- `_get_connected_system_comparison()`
- `_get_integration_comparison()`
- `_get_web_api_comparison()`
- `_get_site_comparison()`
- `_get_basic_comparison()`

#### Added to Comparison Response

Each comparison now includes:
```python
{
    'comparison_type': 'customer_only' | 'vendor_changes' | 'conflict',
    'old_label': 'Vendor Base' | 'Vendor Latest',
    'new_label': 'Customer' | 'Vendor Latest',
    # ... existing fields
}
```

### 2. Frontend Template Updates

**Updated Templates:**

1. `templates/merge/comparisons/interface.html`
2. `templates/merge/comparisons/expression_rule.html`
3. `templates/merge/comparisons/cdt.html`
4. `templates/merge/comparisons/constant.html`
5. `templates/merge/comparisons/process_model.html`
6. `templates/merge/comparisons/record_type.html`
7. `templates/merge/comparisons/other_objects.html`

#### Changes Applied

**Before:**
```html
<span class="badge bg-secondary">Vendor Base</span>
<span class="badge bg-info">Vendor Latest</span>
```

**After:**
```html
<span class="badge bg-secondary">{{ comparison.old_label or 'Vendor Base' }}</span>
<span class="badge bg-info">{{ comparison.new_label or 'Vendor Latest' }}</span>
```

**SAIL Diff Labels - Before:**
```jinja
{% if detail.change.classification == 'CONFLICT' %}
    {{ render_sail_diff(comparison.diff_hunks, old_label='Customer', new_label='Vendor Latest', stats=comparison.diff_stats) }}
{% else %}
    {{ render_sail_diff(comparison.diff_hunks, old_label='Vendor Base', new_label='Vendor Latest', stats=comparison.diff_stats) }}
{% endif %}
```

**SAIL Diff Labels - After:**
```jinja
{{ render_sail_diff(comparison.diff_hunks, old_label=comparison.old_label, new_label=comparison.new_label, stats=comparison.diff_stats) }}
```

## Testing

### Test Script

Created `test_no_conflict_display_logic.py` to verify the logic:

```bash
python test_no_conflict_display_logic.py
```

The script:
1. Finds a ready merge session
2. Gets NO_CONFLICT changes
3. Verifies the comparison strategy matches expected behavior
4. Checks that labels are correct

### Expected Test Results

For each NO_CONFLICT change:

**Scenario 1: Customer-only changes**
- Vendor Change Type: `None`
- Customer Change Type: `MODIFIED` or `ADDED`
- Expected Comparison: `customer_only`
- Expected Labels: "Vendor Base" vs "Customer"

**Scenario 2: Vendor changes**
- Vendor Change Type: `MODIFIED` or `ADDED`
- Expected Comparison: `vendor_changes`
- Expected Labels: "Vendor Base" vs "Vendor Latest"

## Database Schema

No database changes required. The logic uses existing fields:
- `changes.vendor_change_type`
- `changes.customer_change_type`
- `changes.classification`

## Backward Compatibility

✅ **Fully backward compatible**

- Templates use fallback values: `{{ comparison.old_label or 'Vendor Base' }}`
- If `old_label` or `new_label` are missing, defaults to original behavior
- Existing sessions will continue to work

## Files Modified

### Backend
- `services/comparison_retrieval_service.py` (12 methods updated)

### Frontend
- `templates/merge/comparisons/interface.html`
- `templates/merge/comparisons/expression_rule.html`
- `templates/merge/comparisons/cdt.html`
- `templates/merge/comparisons/constant.html`
- `templates/merge/comparisons/process_model.html`
- `templates/merge/comparisons/record_type.html`
- `templates/merge/comparisons/other_objects.html`

### Test Files
- `test_no_conflict_display_logic.py` (new)
- `update_comparison_templates.py` (utility script)

## How to Verify

1. **Start the application:**
   ```bash
   python app.py
   ```

2. **Create or open a merge session with NO_CONFLICT changes**

3. **Navigate to the workflow and review changes:**
   - Look for NO_CONFLICT changes where customer made modifications
   - Verify the comparison shows "Vendor Base" vs "Customer"
   - Look for NO_CONFLICT changes where vendor made modifications
   - Verify the comparison shows "Vendor Base" vs "Vendor Latest"

4. **Run the test script:**
   ```bash
   python test_no_conflict_display_logic.py
   ```

## Benefits

1. **Clearer Context:** Users can see customer-only changes compared against the base
2. **Better Decision Making:** Understanding what the customer changed helps with merge decisions
3. **Consistent Logic:** All object types follow the same comparison strategy
4. **Flexible Display:** Dynamic labels adapt to the change scenario

## Implementation Notes

- The `vendor` and `customer` keys in comparison data now represent "new" and "old" respectively
- This is semantic: for customer-only changes, `vendor` key contains customer data
- Labels (`old_label`, `new_label`) provide the correct display context
- All 12 comparison methods follow the same pattern for consistency

---

## Issue Resolution

### Problem Found
The Python script `update_comparison_templates.py` used escaped quotes `\'` which were rendered literally in HTML as `\'` instead of `'`.

### Solution Applied
Created `fix_template_quotes.py` to replace all `\'` with `'` in the templates.

**Fixed Templates:**
- `templates/merge/comparisons/constant.html`
- `templates/merge/comparisons/process_model.html`
- `templates/merge/comparisons/record_type.html`
- `templates/merge/comparisons/other_objects.html`

### Verification
Tested with Change 213 in MRG_010:
- Backend returns correct labels: "Vendor Base" and "Customer"
- Templates now have correct syntax: `{{ comparison.old_label or 'Vendor Base' }}`
- Ready for browser refresh to see changes

---

**Status:** ✅ Complete and Verified  
**Tested:** Change 213 in MRG_010 (backend verified)  
**Ready for:** User testing (refresh browser)
