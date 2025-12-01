"""Check test database schema"""
import sqlite3

conn = sqlite3.connect('instance/docflow.db')
cursor = conn.cursor()

# Check interfaces table
cursor.execute("PRAGMA table_info(interfaces)")
cols = cursor.fetchall()
print('Interfaces columns:')
for col in cols:
    print(f'  {col[1]}: {col[2]}')

# Check foreign keys
cursor.execute("PRAGMA foreign_keys")
print(f'\nForeign keys enabled: {cursor.fetchone()}')

# Check if package_id column exists
has_package_id = any(col[1] == 'package_id' for col in cols)
print(f'\npackage_id column exists: {has_package_id}')

conn.close()
