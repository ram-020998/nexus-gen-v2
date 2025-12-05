# Three-Way Merge Database Schema

**Part of:** Three-Way Merge Clean Architecture Specification  
**Version:** 1.0  
**Date:** 2025-11-30

---

## Database Schema Design

### Core Principles

1. **No Duplication**: Each object stored once in object_lookup
2. **Package-Agnostic**: object_lookup has NO package_id
3. **Explicit Mapping**: package_object_mappings tracks membership
4. **Delta Storage**: delta_comparison_results stores A→C comparison
5. **Referential Integrity**: All foreign keys enforced with CASCADE

---

## Core Tables

### 1. object_lookup (Global Object Registry)

**Purpose**: Single source of truth for all unique objects across all packages

```sql
CREATE TABLE object_lookup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(500) NOT NULL,
    object_type VARCHAR(50) NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_uuid (uuid),
    INDEX idx_name (name),
    INDEX idx_type (object_type)
);
```

**Key Design Decisions:**
- ❌ NO `package_id` column - package-agnostic!
- ✅ UUID is globally unique
- ✅ Minimal metadata (only identification)
- ✅ Indexed for fast lookups

**Example Data:**
```
id | uuid                                  | name              | object_type
1  | _a-0001ed6e-54f1-8000-9df6-011c48... | AS_GSS_Interface  | Interface
2  | de199b3f-b072-4438-9508-3b6594827eaf | PM_Approval       | Process Model
```

---

### 2. package_object_mappings

**Purpose**: Track which objects belong to which packages

```sql
CREATE TABLE package_object_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    package_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    
    UNIQUE (package_id, object_id),
    INDEX idx_pom_package (package_id),
    INDEX idx_pom_object (object_id),
    INDEX idx_pom_package_object (package_id, object_id)
);
```

**Key Design Decisions:**
- ✅ Composite unique constraint prevents duplicates
- ✅ Enables query: "which objects in package A?"
- ✅ Enables query: "which packages contain object X?"

**Example Data:**
```
id | package_id | object_id | created_at
1  | 1 (Pkg A)  | 1         | 2025-11-30 10:00:00
2  | 2 (Pkg B)  | 1         | 2025-11-30 10:00:00
3  | 3 (Pkg C)  | 1         | 2025-11-30 10:00:00
```
*Object 1 exists in all three packages*

---

### 3. delta_comparison_results

**Purpose**: Store A→C comparison results (vendor delta)

```sql
CREATE TABLE delta_comparison_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,
    change_category VARCHAR(20) NOT NULL,  -- NEW, MODIFIED, DEPRECATED
    change_type VARCHAR(20) NOT NULL,      -- ADDED, MODIFIED, REMOVED
    version_changed BOOLEAN DEFAULT 0,
    content_changed BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    
    UNIQUE (session_id, object_id),
    INDEX idx_delta_session (session_id),
    INDEX idx_delta_category (session_id, change_category),
    INDEX idx_delta_object (object_id),
    
    CHECK (change_category IN ('NEW', 'MODIFIED', 'DEPRECATED')),
    CHECK (change_type IN ('ADDED', 'MODIFIED', 'REMOVED'))
);
```

**Key Design Decisions:**
- ✅ Stores ONLY A→C comparison (vendor delta)
- ✅ Persistent storage (not in-memory)
- ✅ Indexed for fast filtering by category
- ✅ Unique constraint per session+object

**Example Data:**
```
id | session_id | object_id | change_category | change_type | version_changed | content_changed
1  | 1          | 1         | MODIFIED        | MODIFIED    | 1               | 1
2  | 1          | 2         | NEW             | ADDED       | 0               | 0
3  | 1          | 3         | DEPRECATED      | REMOVED     | 0               | 0
```

---

### 4. changes (Working Set)

**Purpose**: Store classified changes for user review

```sql
CREATE TABLE changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    object_id INTEGER NOT NULL,  -- NEW: references object_lookup
    
    -- Classification
    classification VARCHAR(50) NOT NULL,  -- NO_CONFLICT, CONFLICT, NEW, DELETED
    change_type VARCHAR(20),              -- ADDED, MODIFIED, REMOVED
    vendor_change_type VARCHAR(20),       -- A→C change type
    customer_change_type VARCHAR(20),     -- A→B change type
    
    -- Ordering
    display_order INTEGER NOT NULL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES merge_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    
    INDEX idx_change_session_classification (session_id, classification),
    INDEX idx_change_session_object (session_id, object_id),
    INDEX idx_change_session_order (session_id, display_order),
    INDEX idx_change_object (object_id),
    
    CHECK (classification IN ('NO_CONFLICT', 'CONFLICT', 'NEW', 'DELETED'))
);
```

**Key Design Decisions:**
- ✅ References object_lookup (not duplicate data)
- ❌ NO object_uuid, object_name, object_type columns (redundant)
- ✅ Only 4 classifications (removed CUSTOMER_ONLY, REMOVED_BUT_CUSTOMIZED)
- ✅ Tracks both vendor and customer change types

**REMOVED Columns:**
```sql
-- ❌ DEPRECATED (kept temporarily for migration):
base_object_id_old INTEGER,
customer_object_id_old INTEGER,
vendor_object_id_old INTEGER,
object_uuid_old VARCHAR(255),
object_name_old VARCHAR(500),
object_type_old VARCHAR(50)
```

---

### 5. object_versions

**Purpose**: Store package-specific versions of objects

```sql
CREATE TABLE object_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id INTEGER NOT NULL,
    package_id INTEGER NOT NULL,
    version_uuid VARCHAR(255),
    sail_code TEXT,
    fields TEXT,        -- JSON string
    properties TEXT,    -- JSON string
    raw_xml TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    
    UNIQUE (object_id, package_id),
    INDEX idx_objver_object (object_id),
    INDEX idx_objver_package (package_id),
    INDEX idx_objver_object_package (object_id, package_id)
);
```

**Key Design Decisions:**
- ✅ Stores package-specific versions
- ✅ Enables comparison: "get Interface X from package A vs package C"
- ✅ Keeps object-specific tables clean (one row per object)

**Example Data:**
```
id | object_id | package_id | version_uuid                          | sail_code
1  | 1         | 1 (Pkg A)  | v1-uuid-abc...                       | a!localVariables(...)
2  | 1         | 2 (Pkg B)  | v1-uuid-abc...                       | a!localVariables(...)
3  | 1         | 3 (Pkg C)  | v2-uuid-xyz...                       | a!localVariables(...)
```
*Object 1 has same version in A and B, but different version in C*

---

## Object-Specific Tables

### Design Pattern for Object Tables

**All object-specific tables follow this pattern:**

```sql
CREATE TABLE <object_type>s (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- NEW: Reference to global object lookup
    object_id INTEGER,
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    INDEX idx_<type>_object (object_id),
    
    -- DEPRECATED: Old package_id (kept temporarily for migration)
    package_id INTEGER,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    
    -- Object identification (redundant with object_lookup, but kept for queries)
    uuid VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    version_uuid VARCHAR(255),
    
    -- Object-specific fields
    <type_specific_fields>,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (package_id, uuid)  -- Temporary during migration
);
```

**Migration Strategy:**
1. Add `object_id` column (nullable)
2. Populate `object_id` from `object_lookup`
3. Make `object_id` NOT NULL
4. Remove `package_id` column
5. Remove `uuid`, `name` columns (redundant)

---

### 6. interfaces

```sql
CREATE TABLE interfaces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id INTEGER,
    package_id INTEGER,  -- DEPRECATED
    uuid VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    version_uuid VARCHAR(255),
    sail_code TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    
    UNIQUE (package_id, uuid),
    INDEX idx_interface_object (object_id)
);

CREATE TABLE interface_parameters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interface_id INTEGER NOT NULL,
    parameter_name VARCHAR(255) NOT NULL,
    parameter_type VARCHAR(100),
    is_required BOOLEAN DEFAULT 0,
    default_value TEXT,
    display_order INTEGER,
    
    FOREIGN KEY (interface_id) REFERENCES interfaces(id) ON DELETE CASCADE
);

CREATE TABLE interface_security (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interface_id INTEGER NOT NULL,
    role_name VARCHAR(255),
    permission_type VARCHAR(50),
    
    FOREIGN KEY (interface_id) REFERENCES interfaces(id) ON DELETE CASCADE,
    UNIQUE (interface_id, role_name, permission_type)
);
```

---

### 7. expression_rules

```sql
CREATE TABLE expression_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id INTEGER,
    package_id INTEGER,  -- DEPRECATED
    uuid VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    version_uuid VARCHAR(255),
    sail_code TEXT,
    output_type VARCHAR(100),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    
    UNIQUE (package_id, uuid),
    INDEX idx_rule_object (object_id)
);

CREATE TABLE expression_rule_inputs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER NOT NULL,
    input_name VARCHAR(255) NOT NULL,
    input_type VARCHAR(100),
    is_required BOOLEAN DEFAULT 0,
    default_value TEXT,
    display_order INTEGER,
    
    FOREIGN KEY (rule_id) REFERENCES expression_rules(id) ON DELETE CASCADE
);
```

---

### 8. process_models

```sql
CREATE TABLE process_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id INTEGER,
    package_id INTEGER,  -- DEPRECATED
    uuid VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    version_uuid VARCHAR(255),
    description TEXT,
    total_nodes INTEGER DEFAULT 0,
    total_flows INTEGER DEFAULT 0,
    complexity_score FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    
    UNIQUE (package_id, uuid),
    INDEX idx_pm_object (object_id)
);

CREATE TABLE process_model_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_model_id INTEGER NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    node_type VARCHAR(100) NOT NULL,
    node_name VARCHAR(500),
    properties TEXT,  -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (process_model_id) REFERENCES process_models(id) ON DELETE CASCADE,
    UNIQUE (process_model_id, node_id),
    INDEX idx_node_type (process_model_id, node_type)
);

CREATE TABLE process_model_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_model_id INTEGER NOT NULL,
    from_node_id INTEGER NOT NULL,
    to_node_id INTEGER NOT NULL,
    flow_label VARCHAR(500),
    flow_condition TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (process_model_id) REFERENCES process_models(id) ON DELETE CASCADE,
    FOREIGN KEY (from_node_id) REFERENCES process_model_nodes(id),
    FOREIGN KEY (to_node_id) REFERENCES process_model_nodes(id),
    
    INDEX idx_flow_from (process_model_id, from_node_id),
    INDEX idx_flow_to (process_model_id, to_node_id)
);

CREATE TABLE process_model_variables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    process_model_id INTEGER NOT NULL,
    variable_name VARCHAR(255) NOT NULL,
    variable_type VARCHAR(100),
    is_parameter BOOLEAN DEFAULT 0,
    default_value TEXT,
    
    FOREIGN KEY (process_model_id) REFERENCES process_models(id) ON DELETE CASCADE
);
```

---

### 9. record_types

```sql
CREATE TABLE record_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id INTEGER,
    package_id INTEGER,  -- DEPRECATED
    uuid VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    version_uuid VARCHAR(255),
    description TEXT,
    source_type VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    
    UNIQUE (package_id, uuid),
    INDEX idx_recordtype_object (object_id)
);

CREATE TABLE record_type_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type_id INTEGER NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    field_type VARCHAR(100),
    is_primary_key BOOLEAN DEFAULT 0,
    is_required BOOLEAN DEFAULT 0,
    display_order INTEGER,
    
    FOREIGN KEY (record_type_id) REFERENCES record_types(id) ON DELETE CASCADE
);

CREATE TABLE record_type_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type_id INTEGER NOT NULL,
    relationship_name VARCHAR(255),
    related_record_uuid VARCHAR(255),
    relationship_type VARCHAR(50),
    
    FOREIGN KEY (record_type_id) REFERENCES record_types(id) ON DELETE CASCADE
);

CREATE TABLE record_type_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type_id INTEGER NOT NULL,
    view_name VARCHAR(255),
    view_type VARCHAR(50),
    configuration TEXT,
    
    FOREIGN KEY (record_type_id) REFERENCES record_types(id) ON DELETE CASCADE
);

CREATE TABLE record_type_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type_id INTEGER NOT NULL,
    action_name VARCHAR(255),
    action_type VARCHAR(50),
    configuration TEXT,
    
    FOREIGN KEY (record_type_id) REFERENCES record_types(id) ON DELETE CASCADE
);
```

---

### 10. cdts (Custom Data Types)

```sql
CREATE TABLE cdts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id INTEGER,
    package_id INTEGER,  -- DEPRECATED
    uuid VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    version_uuid VARCHAR(255),
    namespace VARCHAR(255),
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (object_id) REFERENCES object_lookup(id) ON DELETE CASCADE,
    FOREIGN KEY (package_id) REFERENCES packages(id) ON DELETE CASCADE,
    
    UNIQUE (package_id, uuid),
    INDEX idx_cdt_object (object_id)
);

CREATE TABLE cdt_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cdt_id INTEGER NOT NULL,
    field_name VARCHAR(255) NOT NULL,
    field_type VARCHAR(100),
    is_list BOOLEAN DEFAULT 0,
    is_required BOOLEAN DEFAULT 0,
    display_order INTEGER,
    
    FOREIGN KEY (cdt_id) REFERENCES cdts(id) ON DELETE CASCADE
);
```

---

## Comparison Result Tables

### Pattern for Comparison Tables

```sql
CREATE TABLE <object_type>_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_id INTEGER NOT NULL UNIQUE,
    
    -- Object-specific comparison fields
    <type_specific_comparison_fields>,
    
    FOREIGN KEY (change_id) REFERENCES changes(id) ON DELETE CASCADE
);
```

### 11. interface_comparisons

```sql
CREATE TABLE interface_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_id INTEGER NOT NULL UNIQUE,
    sail_code_diff TEXT,
    parameters_added TEXT,      -- JSON
    parameters_removed TEXT,    -- JSON
    parameters_modified TEXT,   -- JSON
    security_changes TEXT,      -- JSON
    
    FOREIGN KEY (change_id) REFERENCES changes(id) ON DELETE CASCADE
);
```

### 12. process_model_comparisons

```sql
CREATE TABLE process_model_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    change_id INTEGER NOT NULL UNIQUE,
    nodes_added TEXT,           -- JSON
    nodes_removed TEXT,         -- JSON
    nodes_modified TEXT,        -- JSON
    flows_added TEXT,           -- JSON
    flows_removed TEXT,         -- JSON
    flows_modified TEXT,        -- JSON
    variables_changed TEXT,     -- JSON
    mermaid_diagram TEXT,
    
    FOREIGN KEY (change_id) REFERENCES changes(id) ON DELETE CASCADE
);
```

---

## Validation Queries

### Check for Duplicates
```sql
-- Should return 0 rows
SELECT uuid, COUNT(*) as count 
FROM object_lookup 
GROUP BY uuid 
HAVING count > 1;
```

### Verify Working Set is Delta-Driven
```sql
-- Should be equal
SELECT COUNT(*) FROM delta_comparison_results WHERE session_id = ?;
SELECT COUNT(*) FROM changes WHERE session_id = ?;
```

### Verify Package Mappings
```sql
-- Get objects in package A
SELECT ol.uuid, ol.name, ol.object_type
FROM object_lookup ol
JOIN package_object_mappings pom ON ol.id = pom.object_id
WHERE pom.package_id = ?;
```

### Get Object Across All Packages
```sql
-- Get all versions of object X
SELECT p.package_type, ov.version_uuid, ov.sail_code
FROM object_versions ov
JOIN packages p ON ov.package_id = p.id
WHERE ov.object_id = ?;
```

---

## Migration Strategy

### Phase 1: Add New Columns
```sql
ALTER TABLE interfaces ADD COLUMN object_id INTEGER;
ALTER TABLE expression_rules ADD COLUMN object_id INTEGER;
-- ... for all object tables
```

### Phase 2: Populate object_id
```python
# For each object in interfaces table:
# 1. Find or create in object_lookup
# 2. Update object_id
```

### Phase 3: Make object_id NOT NULL
```sql
ALTER TABLE interfaces MODIFY COLUMN object_id INTEGER NOT NULL;
```

### Phase 4: Remove Deprecated Columns
```sql
ALTER TABLE interfaces DROP COLUMN package_id;
ALTER TABLE interfaces DROP COLUMN uuid;
ALTER TABLE interfaces DROP COLUMN name;
```

---

*End of Database Schema Document*
