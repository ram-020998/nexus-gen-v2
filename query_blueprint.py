#!/usr/bin/env python3
"""Query process model blueprint from database"""

from app import create_app
from models import db, ComparisonRequest
import json
import sys

def main():
    app = create_app()
    with app.app_context():
        # Get the latest comparison request
        latest_request = ComparisonRequest.query.order_by(ComparisonRequest.created_at.desc()).first()
        
        if not latest_request:
            print('No comparison requests found in database')
            return
        
        print(f'Latest Request: {latest_request.reference_id}')
        print(f'Old App: {latest_request.old_app_name}')
        print(f'New App: {latest_request.new_app_name}')
        print(f'Status: {latest_request.status}')
        print(f'Created: {latest_request.created_at}')
        print('=' * 80)
        print()
        
        # Parse the new app blueprint
        new_blueprint = json.loads(latest_request.new_app_blueprint)
        
        # Search for DGS Create Parent process model
        found = False
        for obj_uuid, obj_data in new_blueprint.get('object_lookup', {}).items():
            if obj_data.get('type') == 'Process Model' and 'DGS Create Parent' in obj_data.get('name', ''):
                found = True
                print(f'Found Process Model: {obj_data.get("name")}')
                print(f'UUID: {obj_uuid}')
                print(f'Type: {obj_data.get("type")}')
                print()
                print('Full Blueprint Data:')
                print(json.dumps(obj_data, indent=2))
                break
        
        if not found:
            print('Process Model "DGS Create Parent" not found in new blueprint')
            print()
            print('Searching in all Process Models...')
            process_models = []
            for obj_uuid, obj_data in new_blueprint.get('object_lookup', {}).items():
                if obj_data.get('type') == 'Process Model':
                    process_models.append((obj_data.get('name', 'Unknown'), obj_uuid))
            
            process_models.sort()
            print(f'\nFound {len(process_models)} Process Models:')
            for name, uuid in process_models:
                if 'DGS' in name or 'Parent' in name or 'Create' in name:
                    print(f'  *** {name} ({uuid})')
                else:
                    print(f'  - {name}')

if __name__ == '__main__':
    main()
