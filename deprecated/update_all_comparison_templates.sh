#!/bin/bash

# Script to update all comparison templates with dynamic labels

echo "Updating comparison templates with dynamic labels..."

# List of templates to update
templates=(
    "templates/merge/comparisons/cdt.html"
    "templates/merge/comparisons/constant.html"
    "templates/merge/comparisons/process_model.html"
    "templates/merge/comparisons/record_type.html"
    "templates/merge/comparisons/other_objects.html"
)

for template in "${templates[@]}"; do
    if [ -f "$template" ]; then
        echo "Updating $template..."
        
        # Replace hardcoded labels with dynamic ones
        sed -i '' 's/<span class="badge bg-secondary">Vendor Base<\/span>/<span class="badge bg-secondary">{{ comparison.old_label or '\''Vendor Base'\'' }}<\/span>/g' "$template"
        sed -i '' 's/<span class="badge bg-info">Vendor Latest<\/span>/<span class="badge bg-info">{{ comparison.new_label or '\''Vendor Latest'\'' }}<\/span>/g' "$template"
        sed -i '' 's/<span>Vendor Base<\/span>/<span>{{ comparison.old_label or '\''Vendor Base'\'' }}<\/span>/g' "$template"
        sed -i '' 's/<span>Vendor Latest<\/span>/<span>{{ comparison.new_label or '\''Vendor Latest'\'' }}<\/span>/g' "$template"
        sed -i '' 's/<span>Customer<\/span>/<span>{{ comparison.new_label or '\''Customer'\'' }}<\/span>/g' "$template"
        sed -i '' 's/old_label='\''Vendor Base'\''/old_label=comparison.old_label/g' "$template"
        sed -i '' 's/new_label='\''Vendor Latest'\''/new_label=comparison.new_label/g' "$template"
        sed -i '' 's/old_label='\''Customer'\''/old_label=comparison.old_label/g' "$template"
        sed -i '' 's/<!-- NO_CONFLICT: Vendor Base (left) vs Vendor Latest (right) -->/<!-- NO_CONFLICT: Dynamic based on change types -->/g' "$template"
        
        echo "✓ Updated $template"
    else
        echo "✗ File not found: $template"
    fi
done

echo ""
echo "All templates updated!"
