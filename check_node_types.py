#!/usr/bin/env python3
"""Check node types in change 5"""

from app import create_app
from models import db
import json

def main():
    app = create_app()
    with app.app_context():
        result = db.session.execute(
            db.text("SELECT ordered_changes FROM merge_sessions WHERE id = 1")
        ).fetchone()
        
        if not result or not result[0]:
            print('No data')
            return
        
        ordered_changes = json.loads(result[0])
        change_5 = ordered_changes[5]
        
        pm_data = change_5.get('process_model_data', {})
        node_comp = pm_data.get('node_comparison', {})
        
        print('Node Types:')
        all_nodes = []
        all_nodes.extend(node_comp.get('added', []))
        all_nodes.extend(node_comp.get('removed', []))
        all_nodes.extend([m.get('node', {}) for m in node_comp.get('modified', [])])
        all_nodes.extend(node_comp.get('unchanged', []))
        
        for node in all_nodes:
            print(f'  {node.get("name")}:')
            print(f'    type: {node.get("type")}')
            print(f'    uuid: {node.get("uuid")}')
            print()

if __name__ == '__main__':
    main()
