#!/usr/bin/env python3
"""Find DGS Create Parent process model"""

from app import create_app
from models import db
import json

def main():
    app = create_app()
    with app.app_context():
        result = db.session.execute(
            db.text("SELECT reference_id, new_vendor_blueprint FROM merge_sessions ORDER BY created_at DESC LIMIT 1")
        ).fetchone()
        
        if not result:
            print('No merge sessions found')
            return
        
        reference_id, blueprint_json = result
        print(f'Merge Session: {reference_id}')
        print('=' * 80)
        print()
        
        blueprint = json.loads(blueprint_json)
        obj_lookup = blueprint.get('object_lookup', {})
        
        # Search for DGS Create Parent
        found_objects = []
        for obj_uuid, obj_data in obj_lookup.items():
            name = obj_data.get('name', '')
            obj_type = obj_data.get('object_type', 'Unknown')
            
            if 'Create Parent' in name or 'Create_Parent' in name:
                found_objects.append((name, obj_type, obj_uuid, obj_data))
        
        if found_objects:
            print(f'Found {len(found_objects)} matching object(s):\n')
            for name, obj_type, uuid, data in found_objects:
                print(f'Name: {name}')
                print(f'Type: {obj_type}')
                print(f'UUID: {uuid}')
                print('\nFull Blueprint Data:')
                print(json.dumps(data, indent=2))
                print('\n' + '=' * 80 + '\n')
        else:
            print('No objects found with "Create Parent" in name')
            print('\nSearching for objects with "DGS" and "Create"...\n')
            
            for obj_uuid, obj_data in obj_lookup.items():
                name = obj_data.get('name', '')
                obj_type = obj_data.get('object_type', 'Unknown')
                
                if 'DGS' in name and 'Create' in name:
                    print(f'  - {name} ({obj_type})')
                    print(f'    UUID: {obj_uuid}')

if __name__ == '__main__':
    main()
