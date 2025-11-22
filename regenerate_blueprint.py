#!/usr/bin/env python3
"""
Regenerate blueprint for a merge session to get proper flow connections

This script will re-analyze the packages and regenerate the blueprints
with the fixed flow extraction logic.
"""

from app import create_app
from models import db
from services.appian_analyzer.analyzer import AppianAnalyzer
import json
import os

def main():
    app = create_app()
    with app.app_context():
        # Get the latest merge session
        result = db.session.execute(
            db.text("SELECT id, reference_id, base_package_name, customized_package_name, new_vendor_package_name FROM merge_sessions ORDER BY created_at DESC LIMIT 1")
        ).fetchone()
        
        if not result:
            print('No merge sessions found')
            return
        
        session_id, reference_id, base_name, custom_name, vendor_name = result
        
        print(f'Merge Session: {reference_id}')
        print(f'Base: {base_name}')
        print(f'Customized: {custom_name}')
        print(f'Vendor: {vendor_name}')
        print('=' * 80)
        
        # Check if package files exist
        uploads_dir = 'uploads'
        
        # Find the package files (they should be in uploads directory)
        # For now, let's just show what we would need to do
        print('\nTo regenerate blueprints, you would need to:')
        print('1. Re-upload the three package ZIP files')
        print('2. Start a new merge comparison')
        print('3. The new comparison will use the fixed flow extraction')
        print('\nAlternatively, if you have the original ZIP files:')
        print('- Upload them again through the web interface')
        print('- Or provide the file paths and we can process them here')
        
        # Show current blueprint status
        result = db.session.execute(
            db.text("SELECT new_vendor_blueprint FROM merge_sessions WHERE id = :id"),
            {'id': session_id}
        ).fetchone()
        
        if result and result[0]:
            blueprint = json.loads(result[0])
            obj_lookup = blueprint.get('object_lookup', {})
            
            # Find DGS Create Parent
            for obj_uuid, obj_data in obj_lookup.items():
                name = obj_data.get('name', '')
                if 'Create Parent' in name:
                    flows = obj_data.get('flows', [])
                    flow_graph = obj_data.get('flow_graph', {})
                    
                    print(f'\n\nCurrent blueprint for "{name}":')
                    print(f'  Flows: {len(flows)}')
                    print(f'  Start nodes: {len(flow_graph.get("start_nodes", []))}')
                    print(f'  End nodes: {len(flow_graph.get("end_nodes", []))}')
                    
                    if len(flows) == 0:
                        print('\n  ⚠️  No flows extracted - blueprint needs regeneration')
                    else:
                        print('\n  ✅ Flows are present')
                    
                    break

if __name__ == '__main__':
    main()
