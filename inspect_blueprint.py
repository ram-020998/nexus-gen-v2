#!/usr/bin/env python3
"""Inspect blueprint structure"""

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
        
        if not blueprint_json:
            print('No blueprint data')
            return
        
        blueprint = json.loads(blueprint_json)
        
        print(f'\nBlueprint top-level keys: {list(blueprint.keys())}')
        
        if 'object_lookup' in blueprint:
            obj_lookup = blueprint['object_lookup']
            print(f'\nTotal objects in object_lookup: {len(obj_lookup)}')
            
            # Count by type
            type_counts = {}
            for obj_uuid, obj_data in obj_lookup.items():
                obj_type = obj_data.get('type', 'Unknown')
                type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
            
            print('\nObject counts by type:')
            for obj_type, count in sorted(type_counts.items()):
                print(f'  {obj_type}: {count}')
            
            # Show first few objects
            print('\nFirst 5 objects:')
            for i, (uuid, data) in enumerate(list(obj_lookup.items())[:5]):
                print(f'\n  {i+1}. {data.get("name", "Unknown")} ({data.get("type", "Unknown")})')
                print(f'     UUID: {uuid}')
                print(f'     Keys: {list(data.keys())}')
        
        # Check other blueprint sections
        for key in blueprint.keys():
            if key != 'object_lookup':
                value = blueprint[key]
                if isinstance(value, dict):
                    print(f'\n{key}: dict with {len(value)} items')
                elif isinstance(value, list):
                    print(f'\n{key}: list with {len(value)} items')
                else:
                    print(f'\n{key}: {type(value).__name__}')

if __name__ == '__main__':
    main()
