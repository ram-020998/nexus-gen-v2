#!/usr/bin/env python3
"""
Vacuum the database to reclaim disk space after deletions
"""
import sqlite3
import os
from pathlib import Path

db_path = Path('instance/docflow.db')

if not db_path.exists():
    print(f"Error: Database not found at {db_path}")
    exit(1)

# Get size before
size_before = db_path.stat().st_size / (1024 * 1024)  # MB
print(f"Database size before VACUUM: {size_before:.2f} MB")

# Connect and vacuum
print("Running VACUUM... (this may take a moment)")
conn = sqlite3.connect(str(db_path))
conn.execute("VACUUM")
conn.close()

# Get size after
size_after = db_path.stat().st_size / (1024 * 1024)  # MB
print(f"Database size after VACUUM: {size_after:.2f} MB")
print(f"Space reclaimed: {size_before - size_after:.2f} MB")
