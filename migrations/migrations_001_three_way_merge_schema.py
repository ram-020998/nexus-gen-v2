"""
Three-Way Merge Database Schema Migration
Version: 1.0
Date: 2025-11-30

This migration creates the complete schema for the three-way merge functionality
following clean architecture principles with no data duplication.

Key Design Principles:
1. No Duplication: Each object stored once in object_lookup
2. Package-Agnostic: object_lookup has NO package_id
3. Explicit Mapping: package_object_mappings tracks membership
4. Delta Storage: delta_comparison_results stores A→C comparison
5. Referential Integrity: All foreign keys enforced with CASCADE
"""

from models import db


def upgrade():
    """Apply migration - create all three-way merge tables"""
    
    # Core Tables
    create_merge_sessions_table()
    create_packages_table()
    create_object_lookup_table()
    create_package_object_mappings_table()
    create_delta_comparison_results_table()
    create_changes_table()
    create_object_versions_table()
    
    # Object-Specific Tables
    create_interfaces_tables()
    create_expression_rules_tables()
    create_process_models_tables()
    create_record_types_tables()
    create_cdts_tables()
    create_integrations_table()
    create_web_apis_table()
    create_sites_table()
    create_groups_table()
    create_constants_table()
    create_connected_systems_table()
    create_unknown_objects_table()
    
    # Comparison Result Tables
    create_interface_comparisons_table()
    create_process_model_comparisons_table()
    create_record_type_comparisons_table()
    
    print("✅ Three-way merge schema created successfully")


def downgrade():
    """Rollback migration - drop all three-way merge tables"""
    
    # Drop in reverse order to respect foreign key constraints
    tables = [
        'interface_comparisons',
        'process_model_comparisons',
        'record_type_comparisons',
        'unknown_objects',
        'connected_systems',
        'constants',
        'groups',
        'sites',
        'web_apis',
        'integrations',
        'cdt_fields',
        'cdts',
        'record_type_actions',
        'record_type_views',
        'record_type_relationships',
        'record_type_fields',
        'record_types',
        'process_model_variables',
        'process_model_flows',
        'process_model_nodes',
        'process_models',
        'expression_rule_inputs',
        'expression_rules',
        'interface_security',
        'interface_parameters',
        'interfaces',
        'object_versions',
        'changes',
        'delta_comparison_results',
        'package_object_mappings',
        'object_lookup',
        'packages',
        'merge_sessions'
    ]
    
    for table in tables:
        db.session.execute(f"DROP TABLE IF EXISTS {table}")
    
    db.session.commit()
    print("✅ Three-way merge schema rolled back successfully")


# Core Tables

def create_merge_sessions_table():
    """Create merge_sessions table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS merge_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_id VARCHAR(50) NOT NULL UNIQUE,
            status VARCHAR(20) NOT NULL DEFAULT 'processing',
            total_changes INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            CHECK (status IN ('processing', 'ready', 'in_progress', 'completed', 'error'))
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_session_reference ON merge_sessions(reference_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_session_status ON merge_sessions(status)")


def create_packages_table():
    """Create packages table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            package_type VARCHAR(20) NOT NULL,
            filename VARCHAR(500) NOT NULL,
            total_objects INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
            
            CHECK (package_type IN ('base', 'customized', 'new_vendor'))
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_package_session ON packages(session_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_package_type ON packages(session_id, package_type)")


def create_object_lookup_table():
    """Create object_lookup table - Global Object Registry"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS object_lookup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid VARCHAR(255) NOT NULL UNIQUE,
            name VARCHAR(500) NOT NULL,
            object_type VARCHAR(50) NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.session.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_object_uuid ON object_lookup(uuid)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_object_name ON object_lookup(name)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_object_type ON object_lookup(object_type)")


def create_package_object_mappings_table():
    """Create package_object_mappings table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS package_object_mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_id INTEGER NOT NULL,
            object_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
            
            UNIQUE (package_id, object_id)
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_pom_package ON package_object_mappings(package_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_pom_object ON package_object_mappings(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_pom_package_object ON package_object_mappings(package_id, object_id)")


def create_delta_comparison_results_table():
    """Create delta_comparison_results table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS delta_comparison_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            object_id INTEGER NOT NULL,
            change_category VARCHAR(20) NOT NULL,
            change_type VARCHAR(20) NOT NULL,
            version_changed BOOLEAN DEFAULT 0,
            content_changed BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
            
            UNIQUE (session_id, object_id),
            
            CHECK (change_category IN ('NEW', 'MODIFIED', 'DEPRECATED')),
            CHECK (change_type IN ('ADDED', 'MODIFIED', 'REMOVED'))
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_delta_session ON delta_comparison_results(session_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_delta_category ON delta_comparison_results(session_id, change_category)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_delta_object ON delta_comparison_results(object_id)")


def create_changes_table():
    """Create changes table - Working Set"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            object_id INTEGER NOT NULL,
            classification VARCHAR(50) NOT NULL,
            change_type VARCHAR(20),
            vendor_change_type VARCHAR(20),
            customer_change_type VARCHAR(20),
            display_order INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
            
            CHECK (classification IN ('NO_CONFLICT', 'CONFLICT', 'NEW', 'DELETED'))
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_change_session_classification ON changes(session_id, classification)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_change_session_object ON changes(session_id, object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_change_session_order ON changes(session_id, display_order)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_change_object ON changes(object_id)")


def create_object_versions_table():
    """Create object_versions table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS object_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER NOT NULL,
            package_id INTEGER NOT NULL,
            version_uuid VARCHAR(255),
            sail_code TEXT,
            fields TEXT,
            properties TEXT,
            raw_xml TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
            FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
            
            UNIQUE (object_id, package_id)
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_objver_object ON object_versions(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_objver_package ON object_versions(package_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_objver_object_package ON object_versions(object_id, package_id)")


# Object-Specific Tables

def create_interfaces_tables():
    """Create interfaces and related tables"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS interfaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER,
            uuid VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            version_uuid VARCHAR(255),
            sail_code TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_interface_object ON interfaces(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_interface_uuid ON interfaces(uuid)")
    
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS interface_parameters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interface_id INTEGER NOT NULL,
            parameter_name VARCHAR(255) NOT NULL,
            parameter_type VARCHAR(100),
            is_required BOOLEAN DEFAULT 0,
            default_value TEXT,
            display_order INTEGER,
            
            FOREIGN KEY (interface_id) REFERENCES interfaces(id) ON DELETE CASCADE
        )
    """)
    
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS interface_security (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interface_id INTEGER NOT NULL,
            role_name VARCHAR(255),
            permission_type VARCHAR(50),
            
            FOREIGN KEY (interface_id) REFERENCES interfaces(id) ON DELETE CASCADE,
            UNIQUE (interface_id, role_name, permission_type)
        )
    """)


def create_expression_rules_tables():
    """Create expression_rules and related tables"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS expression_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER,
            uuid VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            version_uuid VARCHAR(255),
            sail_code TEXT,
            output_type VARCHAR(100),
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_rule_object ON expression_rules(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_rule_uuid ON expression_rules(uuid)")
    
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS expression_rule_inputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER NOT NULL,
            input_name VARCHAR(255) NOT NULL,
            input_type VARCHAR(100),
            is_required BOOLEAN DEFAULT 0,
            default_value TEXT,
            display_order INTEGER,
            
            FOREIGN KEY (rule_id) REFERENCES expression_rules(id) ON DELETE CASCADE
        )
    """)


def create_process_models_tables():
    """Create process_models and related tables"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS process_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER,
            uuid VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            version_uuid VARCHAR(255),
            description TEXT,
            total_nodes INTEGER DEFAULT 0,
            total_flows INTEGER DEFAULT 0,
            complexity_score FLOAT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_pm_object ON process_models(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_pm_uuid ON process_models(uuid)")
    
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS process_model_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            process_model_id INTEGER NOT NULL,
            node_id VARCHAR(255) NOT NULL,
            node_type VARCHAR(100) NOT NULL,
            node_name VARCHAR(500),
            properties TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (process_model_id) REFERENCES process_models(id) ON DELETE CASCADE,
            UNIQUE (process_model_id, node_id)
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_node_type ON process_model_nodes(process_model_id, node_type)")
    
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS process_model_flows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            process_model_id INTEGER NOT NULL,
            from_node_id INTEGER NOT NULL,
            to_node_id INTEGER NOT NULL,
            flow_label VARCHAR(500),
            flow_condition TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (process_model_id) REFERENCES process_models(id) ON DELETE CASCADE,
            FOREIGN KEY (from_node_id) REFERENCES process_model_nodes(id),
            FOREIGN KEY (to_node_id) REFERENCES process_model_nodes(id)
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_flow_from ON process_model_flows(process_model_id, from_node_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_flow_to ON process_model_flows(process_model_id, to_node_id)")
    
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS process_model_variables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            process_model_id INTEGER NOT NULL,
            variable_name VARCHAR(255) NOT NULL,
            variable_type VARCHAR(100),
            is_parameter BOOLEAN DEFAULT 0,
            default_value TEXT,
            
            FOREIGN KEY (process_model_id) REFERENCES process_models(id) ON DELETE CASCADE
        )
    """)


def create_record_types_tables():
    """Create record_types and related tables"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS record_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER,
            uuid VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            version_uuid VARCHAR(255),
            description TEXT,
            source_type VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_recordtype_object ON record_types(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_recordtype_uuid ON record_types(uuid)")
    
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS record_type_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_type_id INTEGER NOT NULL,
            field_name VARCHAR(255) NOT NULL,
            field_type VARCHAR(100),
            is_primary_key BOOLEAN DEFAULT 0,
            is_required BOOLEAN DEFAULT 0,
            display_order INTEGER,
            
            FOREIGN KEY (record_type_id) REFERENCES record_types(id) ON DELETE CASCADE
        )
    """)
    
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS record_type_relationships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_type_id INTEGER NOT NULL,
            relationship_name VARCHAR(255),
            related_record_uuid VARCHAR(255),
            relationship_type VARCHAR(50),
            
            FOREIGN KEY (record_type_id) REFERENCES record_types(id) ON DELETE CASCADE
        )
    """)
    
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS record_type_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_type_id INTEGER NOT NULL,
            view_name VARCHAR(255),
            view_type VARCHAR(50),
            configuration TEXT,
            
            FOREIGN KEY (record_type_id) REFERENCES record_types(id) ON DELETE CASCADE
        )
    """)
    
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS record_type_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_type_id INTEGER NOT NULL,
            action_name VARCHAR(255),
            action_type VARCHAR(50),
            configuration TEXT,
            
            FOREIGN KEY (record_type_id) REFERENCES record_types(id) ON DELETE CASCADE
        )
    """)


def create_cdts_tables():
    """Create cdts and related tables"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS cdts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER,
            uuid VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            version_uuid VARCHAR(255),
            namespace VARCHAR(255),
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_cdt_object ON cdts(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_cdt_uuid ON cdts(uuid)")
    
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS cdt_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cdt_id INTEGER NOT NULL,
            field_name VARCHAR(255) NOT NULL,
            field_type VARCHAR(100),
            is_list BOOLEAN DEFAULT 0,
            is_required BOOLEAN DEFAULT 0,
            display_order INTEGER,
            
            FOREIGN KEY (cdt_id) REFERENCES cdts(id) ON DELETE CASCADE
        )
    """)


def create_integrations_table():
    """Create integrations table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS integrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER,
            uuid VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            version_uuid VARCHAR(255),
            sail_code TEXT,
            connection_info TEXT,
            authentication_info TEXT,
            endpoint VARCHAR(500),
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_integration_object ON integrations(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_integration_uuid ON integrations(uuid)")


def create_web_apis_table():
    """Create web_apis table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS web_apis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER,
            uuid VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            version_uuid VARCHAR(255),
            sail_code TEXT,
            endpoint VARCHAR(500),
            http_methods TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_webapi_object ON web_apis(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_webapi_uuid ON web_apis(uuid)")


def create_sites_table():
    """Create sites table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER,
            uuid VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            version_uuid VARCHAR(255),
            page_hierarchy TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_site_object ON sites(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_site_uuid ON sites(uuid)")


def create_groups_table():
    """Create groups table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER,
            uuid VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            version_uuid VARCHAR(255),
            members TEXT,
            parent_group_uuid VARCHAR(255),
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_group_object ON groups(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_group_uuid ON groups(uuid)")


def create_constants_table():
    """Create constants table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS constants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER,
            uuid VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            version_uuid VARCHAR(255),
            constant_value TEXT,
            constant_type VARCHAR(100),
            scope VARCHAR(50),
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_constant_object ON constants(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_constant_uuid ON constants(uuid)")


def create_connected_systems_table():
    """Create connected_systems table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS connected_systems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER,
            uuid VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            version_uuid VARCHAR(255),
            system_type VARCHAR(100),
            properties TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_connsys_object ON connected_systems(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_connsys_uuid ON connected_systems(uuid)")


def create_unknown_objects_table():
    """Create unknown_objects table for unrecognized object types"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS unknown_objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER,
            uuid VARCHAR(255) NOT NULL,
            name VARCHAR(500) NOT NULL,
            version_uuid VARCHAR(255),
            raw_xml TEXT,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE
        )
    """)
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_unknown_object ON unknown_objects(object_id)")
    db.session.execute("CREATE INDEX IF NOT EXISTS idx_unknown_uuid ON unknown_objects(uuid)")


# Comparison Result Tables

def create_interface_comparisons_table():
    """Create interface_comparisons table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS interface_comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            change_id INTEGER NOT NULL UNIQUE,
            sail_code_diff TEXT,
            parameters_added TEXT,
            parameters_removed TEXT,
            parameters_modified TEXT,
            security_changes TEXT,
            
            FOREIGN KEY (change_id) REFERENCES changes(id) ON DELETE CASCADE
        )
    """)


def create_process_model_comparisons_table():
    """Create process_model_comparisons table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS process_model_comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            change_id INTEGER NOT NULL UNIQUE,
            nodes_added TEXT,
            nodes_removed TEXT,
            nodes_modified TEXT,
            flows_added TEXT,
            flows_removed TEXT,
            flows_modified TEXT,
            variables_changed TEXT,
            mermaid_diagram TEXT,
            
            FOREIGN KEY (change_id) REFERENCES changes(id) ON DELETE CASCADE
        )
    """)


def create_record_type_comparisons_table():
    """Create record_type_comparisons table"""
    db.session.execute("""
        CREATE TABLE IF NOT EXISTS record_type_comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            change_id INTEGER NOT NULL UNIQUE,
            fields_changed TEXT,
            relationships_changed TEXT,
            views_changed TEXT,
            actions_changed TEXT,
            
            FOREIGN KEY (change_id) REFERENCES changes(id) ON DELETE CASCADE
        )
    """)


if __name__ == '__main__':
    """Run migration directly"""
    from app import create_app
    
    app = create_app()
    with app.app_context():
        print("Running three-way merge schema migration...")
        upgrade()
        print("Migration completed successfully!")
