#!/usr/bin/env python3
import sys
from app import create_app
from models import db, Change

app = create_app()
with app.app_context():
    change = db.session.query(Change).filter_by(id=1408).first()
    if change:
        print(f"Change ID: {change.id}")
        print(f"Object: {change.object.name}")
        print(f"Object Type: {change.object.object_type}")
        print(f"Classification: {change.classification}")
    else:
        print("Change not found")
