"""
Script to update all comparison templates with dynamic labels.
"""

import re
import os

# Templates to update
templates = [
    "templates/merge/comparisons/constant.html",
    "templates/merge/comparisons/process_model.html",
    "templates/merge/comparisons/record_type.html",
    "templates/merge/comparisons/other_objects.html",
]

# Replacement patterns
replacements = [
    # Badge labels in headers
    (r'<span class="badge bg-secondary">Vendor Base</span>', 
     r'<span class="badge bg-secondary">{{ comparison.old_label or \'Vendor Base\' }}</span>'),
    
    (r'<span class="badge bg-info">Vendor Latest</span>', 
     r'<span class="badge bg-info">{{ comparison.new_label or \'Vendor Latest\' }}</span>'),
    
    (r'<span class="badge bg-success">Customer</span>', 
     r'<span class="badge bg-success">{{ comparison.new_label or \'Customer\' }}</span>'),
    
    # Text labels in code headers
    (r'<span>Vendor Base</span>', 
     r'<span>{{ comparison.old_label or \'Vendor Base\' }}</span>'),
    
    (r'<span>Vendor Latest</span>', 
     r'<span>{{ comparison.new_label or \'Vendor Latest\' }}</span>'),
    
    (r'<span>Customer</span>', 
     r'<span>{{ comparison.new_label or \'Customer\' }}</span>'),
    
    # Badge text in code sections
    (r'<span class="code-diff-badge vendor">Base Version</span>', 
     r'<span class="code-diff-badge vendor">{{ comparison.old_label or \'Base Version\' }}</span>'),
    
    (r'<span class="code-diff-badge vendor">New Version</span>', 
     r'<span class="code-diff-badge vendor">{{ comparison.new_label or \'New Version\' }}</span>'),
    
    (r'<span class="code-diff-badge customer">Current</span>', 
     r'<span class="code-diff-badge customer">{{ comparison.new_label or \'Current\' }}</span>'),
    
    # Diff labels in render_sail_diff calls
    (r"old_label='Vendor Base'", 
     r"old_label=comparison.old_label"),
    
    (r"new_label='Vendor Latest'", 
     r"new_label=comparison.new_label"),
    
    (r"old_label='Customer'", 
     r"old_label=comparison.old_label"),
    
    # Comments
    (r'<!-- NO_CONFLICT: Vendor Base \(left\) vs Vendor Latest \(right\) -->', 
     r'<!-- NO_CONFLICT: Dynamic based on change types -->'),
]

def update_template(filepath):
    """Update a single template file."""
    if not os.path.exists(filepath):
        print(f"✗ File not found: {filepath}")
        return False
    
    print(f"Updating {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Apply all replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Only write if changes were made
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✓ Updated {filepath}")
        return True
    else:
        print(f"- No changes needed for {filepath}")
        return False

def main():
    """Update all templates."""
    print("Updating comparison templates with dynamic labels...\n")
    
    updated_count = 0
    for template in templates:
        if update_template(template):
            updated_count += 1
    
    print(f"\n{'='*60}")
    print(f"Updated {updated_count} of {len(templates)} templates")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
