#!/usr/bin/env python3
"""
Database Migration Script for Step 9 Fields
"""
import sqlite3
from pathlib import Path

def migrate_database():
    """Add Step 9 tracking fields to existing database"""
    db_path = Path("instance/docflow.db")
    
    if not db_path.exists():
        print("Database not found. Run the app first to create it.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List of new columns to add
    new_columns = [
        ("reference_id", "VARCHAR(20)"),
        ("agent_name", "VARCHAR(50)"),
        ("model_name", "VARCHAR(100)"),
        ("parameters", "TEXT"),
        ("total_time", "INTEGER"),
        ("step_durations", "TEXT"),
        ("raw_agent_output", "TEXT"),
        ("rag_similarity_avg", "REAL"),
        ("json_valid", "BOOLEAN DEFAULT 1"),
        ("error_log", "TEXT")
    ]
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(requests)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    
    # Add missing columns
    for column_name, column_type in new_columns:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE requests ADD COLUMN {column_name} {column_type}")
                print(f"✅ Added column: {column_name}")
            except sqlite3.Error as e:
                print(f"❌ Error adding {column_name}: {e}")
    
    conn.commit()
    conn.close()
    print("🎉 Database migration completed!")

if __name__ == "__main__":
    migrate_database()
