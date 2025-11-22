#!/usr/bin/env python3
"""Query process model blueprint from merge session"""

from app import create_app
from models import db
import json
import sys

def main():
    app = create_app()
    with app.app_context():
        # Query merge_sessions table
        result = db.session.execute(
            db.text("SELECT reference_id, base_package_name, customized_package_name, new_vendor_package_name, status, new_vendor_blueprint FROM merge_sessions ORDER BY created_at DESC LIMIT 1")
        ).fetchone()
        
        if not result:
            print('No merge sessions found in database')
            return
        
        reference_id, base_name, custom_name, vendor_name, status, blueprint_json = result
        
        print(f'Latest Merge Session: {reference_id}')
        print(f'Base Package: {base_name}')
        print(f'Customized Package: {custom_name}')
        print(f'New Vendor Package: {vendor_name}')
        print(f'Status: {status}')
        print('=' * 80)
        print()
        
        if not blueprint_json:
            print('No blueprint data found in new_vendor_blueprint')
            return
        
        # Parse the blueprint
        blueprint = json.loads(blueprint_json)
        
        # Search for DGS Create Parent process model
        found = False
        search_terms = ['DGS Create Parent', 'DGS_Create_Parent', 'Create Parent']
        
        for obj_uuid, obj_data in blueprint.get('object_lookup', {}).items():
            obj_name = obj_data.get('name', '')
            if obj_data.get('type') == 'Process Model':
                for term in search_terms:
                    if term.lower() in obj_name.lower():
                        found = True
                        print(f'Found Process Model: {obj_name}')
                        print(f'UUID: {obj_uuid}')
                        print(f'Type: {obj_data.get("type")}')
                        print()
                        print('Full Blueprint Data:')
                        print(json.dumps(obj_data, indent=2))
                        print()
                        print('=' * 80)
                        break
            if found:
                break
        
        if not found:
            print('Process Model with "DGS Create Parent" not found')
            print()
            print('Searching for similar Process Models...')
            process_models = []
            for obj_uuid, obj_data in blueprint.get('object_lookup', {}).items():
                if obj_data.get('type') == 'Process Model':
                    name = obj_data.get('name', 'Unknown')
                    process_models.append((name, obj_uuid))
            
            process_models.sort()
            print(f'\nFound {len(process_models)} Process Models total')
            print('\nProcess Models containing "DGS", "Create", or "Parent":')
            for name, uuid in process_models:
                if any(term in name for term in ['DGS', 'Create', 'Parent', 'create', 'parent']):
                    print(f'  *** {name}')
                    print(f'      UUID: {uuid}')

if __name__ == '__main__':
    main()
