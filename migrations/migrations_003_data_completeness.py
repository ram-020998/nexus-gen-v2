"""
Three-Way Merge Data Completeness Migration
Version: 3.0
Date: 2025-12-01

This migration addresses critical data completeness defects by:
1. Adding data_stores and data_store_entities tables
2. Adding missing comparison tables (expression_rule_comparisons, cdt_comparisons, constant_comparisons)
3. Modifying changes table to add vendor_object_id and customer_object_id columns
4. Migrating existing data (object_id → vendor_object_id)
5. Adding foreign key constraints with CASCADE behavior

Requirements: 5.1, 5.2, 5.3, 5.5
"""

from models import db
from sqlalchemy import text


def upgrade():
    """Apply migration - add data completeness enhancements"""
    
    print("Creating data_stores and data_store_entities tables...")
    create_data_stores_tables()
    
    print("Creating missing comparison tables...")
    create_expression_rule_comparisons_table()
    create_cdt_comparisons_table()
    create_constant_comparisons_table()
    
    print("Adding vendor_object_id and customer_object_id to changes table...")
    add_changes_dual_object_tracking()
    
    print("Migrating existing data...")
    migrate_existing_changes_data()
    
    print("Creating performance indexes...")
    create_performance_indexes()
    
    db.session.commit()
    print("✅ Data completeness migration completed successfully")


def downgrade():
    """Rollback migration - remove data completeness enhancements"""
    
    print("Removing performance indexes...")
    remove_performance_indexes()
    
    print("Removing comparison tables...")
    db.session.execute(text("DROP TABLE IF EXISTS constant_comparisons"))
    db.session.execute(text("DROP TABLE IF EXISTS cdt_comparisons"))
    db.session.execute(text("DROP TABLE IF EXISTS expression_rule_comparisons"))
    
    print("Removing data_stores tables...")
    db.session.execute(text("DROP TABLE IF EXISTS data_store_entities"))
    db.session.execute(text("DROP TABLE IF EXISTS data_stores"))
    
    print("⚠ SQLite doesn't support DROP COLUMN - manual rollback required for changes table")
    print("  To rollback changes table modifications, recreate the table without vendor_object_id and customer_object_id")
    
    db.session.commit()
    print("✅ Data completeness migration rolled back successfully")


# Data Store Tables

def create_data_stores_tables():
    """Create data_stores and data_store_entities tables"""
    
    # Create data_stores table
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS data_stores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER NOT NULL,
            uuid VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            version_uuid VARCHAR(255),
            description TEXT,
            connection_reference TEXT,
            configuration TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
        )
    """))
    
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_datastore_object ON data_stores(object_id)"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_datastore_uuid ON data_stores(uuid)"))
    
    # Create data_store_entities table
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS data_store_entities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_store_id INTEGER NOT NULL,
            cdt_uuid VARCHAR(255) NOT NULL,
            table_name VARCHAR(255) NOT NULL,
            column_mappings TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (data_store_id) REFERENCES data_stores(id) ON DELETE CASCADE
        )
    """))
    
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_dse_datastore ON data_store_entities(data_store_id)"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_dse_cdt ON data_store_entities(cdt_uuid)"))
    
    print("  ✓ Created data_stores and data_store_entities tables")


# Comparison Tables

def create_expression_rule_comparisons_table():
    """Create expression_rule_comparisons table"""
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS expression_rule_comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            object_id INTEGER NOT NULL,
            input_changes TEXT,
            return_type_change TEXT,
            logic_diff TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
            
            UNIQUE(session_id, object_id)
        )
    """))
    
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_ercomp_session ON expression_rule_comparisons(session_id)"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_ercomp_object ON expression_rule_comparisons(object_id)"))
    
    print("  ✓ Created expression_rule_comparisons table")


def create_cdt_comparisons_table():
    """Create cdt_comparisons table"""
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS cdt_comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            object_id INTEGER NOT NULL,
            field_changes TEXT,
            namespace_change TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
            
            UNIQUE(session_id, object_id)
        )
    """))
    
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_cdtcomp_session ON cdt_comparisons(session_id)"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_cdtcomp_object ON cdt_comparisons(object_id)"))
    
    print("  ✓ Created cdt_comparisons table")


def create_constant_comparisons_table():
    """Create constant_comparisons table"""
    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS constant_comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            object_id INTEGER NOT NULL,
            base_value TEXT,
            customer_value TEXT,
            new_vendor_value TEXT,
            type_change TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
            
            UNIQUE(session_id, object_id)
        )
    """))
    
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_constcomp_session ON constant_comparisons(session_id)"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_constcomp_object ON constant_comparisons(object_id)"))
    
    print("  ✓ Created constant_comparisons table")


# Changes Table Modifications

def add_changes_dual_object_tracking():
    """Add vendor_object_id and customer_object_id columns to changes table"""
    
    # Add vendor_object_id column
    db.session.execute(text("""
        ALTER TABLE changes 
        ADD COLUMN vendor_object_id INTEGER
    """))
    
    # Add customer_object_id column
    db.session.execute(text("""
        ALTER TABLE changes 
        ADD COLUMN customer_object_id INTEGER
    """))
    
    print("  ✓ Added vendor_object_id and customer_object_id columns to changes table")


def migrate_existing_changes_data():
    """Migrate existing data: UPDATE changes SET vendor_object_id = object_id"""
    
    # Migrate existing object_id values to vendor_object_id
    db.session.execute(text("""
        UPDATE changes 
        SET vendor_object_id = object_id
        WHERE vendor_object_id IS NULL
    """))
    
    # Count migrated records
    result = db.session.execute(text("SELECT COUNT(*) FROM changes WHERE vendor_object_id IS NOT NULL"))
    count = result.scalar()
    
    print(f"  ✓ Migrated {count} existing change records (object_id → vendor_object_id)")


def create_performance_indexes():
    """Create indexes for efficient dual object ID queries"""
    
    # Index on vendor_object_id for efficient vendor object lookups
    db.session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_change_vendor_object 
        ON changes(vendor_object_id)
    """))
    
    # Index on customer_object_id for efficient customer object lookups
    db.session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_change_customer_object 
        ON changes(customer_object_id)
    """))
    
    # Composite index for dual object queries
    db.session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_change_vendor_customer 
        ON changes(vendor_object_id, customer_object_id)
    """))
    
    print("  ✓ Created performance indexes for dual object tracking")


def remove_performance_indexes():
    """Remove performance indexes"""
    db.session.execute(text("DROP INDEX IF EXISTS idx_change_vendor_object"))
    db.session.execute(text("DROP INDEX IF EXISTS idx_change_customer_object"))
    db.session.execute(text("DROP INDEX IF EXISTS idx_change_vendor_customer"))
    db.session.execute(text("DROP INDEX IF EXISTS idx_constcomp_session"))
    db.session.execute(text("DROP INDEX IF EXISTS idx_constcomp_object"))
    db.session.execute(text("DROP INDEX IF EXISTS idx_cdtcomp_session"))
    db.session.execute(text("DROP INDEX IF EXISTS idx_cdtcomp_object"))
    db.session.execute(text("DROP INDEX IF EXISTS idx_ercomp_session"))
    db.session.execute(text("DROP INDEX IF EXISTS idx_ercomp_object"))
    db.session.execute(text("DROP INDEX IF EXISTS idx_dse_datastore"))
    db.session.execute(text("DROP INDEX IF EXISTS idx_dse_cdt"))
    db.session.execute(text("DROP INDEX IF EXISTS idx_datastore_object"))
    db.session.execute(text("DROP INDEX IF EXISTS idx_datastore_uuid"))
    print("  ✓ Removed performance indexes")


if __name__ == '__main__':
    """Run migration directly"""
    from app import create_app
    
    app = create_app()
    with app.app_context():
        print("Running data completeness migration...")
        upgrade()
        print("Migration completed successfully!")
