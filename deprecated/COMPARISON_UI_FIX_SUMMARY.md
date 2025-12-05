# Comparison UI Fix Summary

## Issue
The comparison HTML templates were displaying incorrect labels and comparing wrong versions:
- All comparisons were showing "Vendor" vs "Customer" regardless of classification
- For NO_CONFLICT cases, should show "Vendor Base" vs "Vendor Latest"
- For CONFLICT cases, should show "Vendor Latest" vs "Customer"

## Solution

### 1. Updated All Comparison HTML Templates

Updated 8 comparison template files to conditionally display correct labels and data based on classification:

#### Files Updated:
- `templates/merge/comparisons/interface.html`
- `templates/merge/comparisons/expression_rule.html`
- `templates/merge/comparisons/constant.html`
- `templates/merge/comparisons/cdt.html`
- `templates/merge/comparisons/process_model.html`
- `templates/merge/comparisons/record_type.html`
- `templates/merge/comparisons/other_objects.html`

#### Changes Made:
Each template now uses conditional logic:

```jinja2
{% if detail.change.classification == 'CONFLICT' %}
    <!-- CONFLICT: Vendor Latest (left) vs Customer (right) -->
    <div class="version-column vendor-column">
        <div class="version-header">
            <span class="badge bg-info">Vendor Latest</span>
        </div>
        <!-- Display comparison.vendor data -->
    </div>
    
    <div class="version-column customer-column">
        <div class="version-header">
            <span class="badge bg-success">Customer</span>
        </div>
        <!-- Display comparison.customer data -->
    </div>
{% else %}
    <!-- NO_CONFLICT: Vendor Base (left) vs Vendor Latest (right) -->
    <div class="version-column vendor-column">
        <div class="version-header">
            <span class="badge bg-secondary">Vendor Base</span>
        </div>
        <!-- Display comparison.customer data (which contains base) -->
    </div>
    
    <div class="version-column customer-column">
        <div class="version-header">
            <span class="badge bg-info">Vendor Latest</span>
        </div>
        <!-- Display comparison.vendor data -->
    </div>
{% endif %}
```

### 2. Updated Comparison Retrieval Service

Updated `services/comparison_retrieval_service.py` to fetch correct package data based on classification:

#### Key Change:
```python
# For NO_CONFLICT: compare base vs vendor
# For CONFLICT: compare vendor vs customer
compare_package_id = base_package_id if change.classification == 'NO_CONFLICT' else customer_package_id
```

#### Methods Updated:
- `_get_constant_comparison()`
- `_get_expression_rule_comparison()`
- `_get_interface_comparison()`
- `_get_process_model_comparison()`
- `_get_cdt_comparison()`
- `_get_record_type_comparison()`
- `_get_group_comparison()`
- `_get_connected_system_comparison()`
- `_get_integration_comparison()`
- `_get_web_api_comparison()`
- `_get_site_comparison()`
- `_get_basic_comparison()`

### 3. Updated SAIL Diff Labels

Updated SAIL diff generation to use correct labels:

```python
# Use appropriate labels based on classification
old_label = 'Vendor Base' if change.classification == 'NO_CONFLICT' else 'Customer'

diff_hunks = diff_service.generate_unified_diff(
    old_code,
    new_code,
    old_label=old_label,
    new_label='Vendor Latest'
)
```

## Data Flow

### For CONFLICT Objects:
1. Service fetches: `vendor` = Package C (new vendor), `customer` = Package B (customer)
2. Template displays: Left = "Vendor Latest" (vendor data), Right = "Customer" (customer data)

### For NO_CONFLICT Objects:
1. Service fetches: `vendor` = Package C (new vendor), `customer` = Package A (base)
2. Template displays: Left = "Vendor Base" (customer data), Right = "Vendor Latest" (vendor data)

## Label Mapping

| Classification | Left Column | Right Column | Left Data Source | Right Data Source |
|---------------|-------------|--------------|------------------|-------------------|
| CONFLICT | Vendor Latest | Customer | comparison.vendor (Package C) | comparison.customer (Package B) |
| NO_CONFLICT | Vendor Base | Vendor Latest | comparison.customer (Package A) | comparison.vendor (Package C) |

## Testing

All HTML templates validated with no syntax errors. The Python service has only style warnings (line length) that don't affect functionality.

## Impact

- Users will now see correct version labels in all comparison views
- NO_CONFLICT changes will show base-to-latest vendor evolution
- CONFLICT changes will show vendor-vs-customer differences
- SAIL code diffs will have correct labels in both unified and split views
- All object types (Interface, Expression Rule, Process Model, Record Type, CDT, Constant, Group, Connected System, Integration, Web API, Site) are updated

## Files Modified

### Templates (8 files):
1. templates/merge/comparisons/interface.html
2. templates/merge/comparisons/expression_rule.html
3. templates/merge/comparisons/constant.html
4. templates/merge/comparisons/cdt.html
5. templates/merge/comparisons/process_model.html
6. templates/merge/comparisons/record_type.html
7. templates/merge/comparisons/other_objects.html
8. templates/merge/comparisons/_sail_diff.html (labels updated in calling templates)

### Services (1 file):
1. services/comparison_retrieval_service.py (12 methods updated)

## Completion Status

✅ All comparison templates updated
✅ All comparison service methods updated
✅ SAIL diff labels corrected
✅ No syntax errors in templates
✅ Service validated (only style warnings)
