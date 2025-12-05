"""
Fix escaped quotes in templates
"""

import os

templates = [
    "templates/merge/comparisons/constant.html",
    "templates/merge/comparisons/process_model.html",
    "templates/merge/comparisons/record_type.html",
    "templates/merge/comparisons/other_objects.html",
]

def fix_template(filepath):
    """Fix escaped quotes in a template."""
    if not os.path.exists(filepath):
        print(f"✗ File not found: {filepath}")
        return False
    
    print(f"Fixing {filepath}...")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Replace escaped quotes with regular quotes
    content = content.replace("\\'", "'")
    
    # Only write if changes were made
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✓ Fixed {filepath}")
        return True
    else:
        print(f"- No changes needed for {filepath}")
        return False

def main():
    """Fix all templates."""
    print("Fixing escaped quotes in templates...\n")
    
    fixed_count = 0
    for template in templates:
        if fix_template(template):
            fixed_count += 1
    
    print(f"\n{'='*60}")
    print(f"Fixed {fixed_count} of {len(templates)} templates")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
