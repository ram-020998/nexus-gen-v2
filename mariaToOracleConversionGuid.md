# MariaDB to Oracle SQL Conversion Guide - AI Agent Instructions

## CRITICAL: AI Agent Guidelines

### ⚠️ STRICT RULES - NEVER VIOLATE THESE:

1. **NEVER CREATE AUTO_INCREMENT TRIGGERS** - The actual Oracle implementation does NOT use triggers for AUTO_INCREMENT replacement
2. **ALWAYS create named constraints** - Never use unnamed PRIMARY KEY constraints
3. **ALWAYS create indexes separately** - After table creation
4. **ALWAYS use VARCHAR2** - Never use VARCHAR in Oracle
5. **ALWAYS preserve sequence start values** - Extract from AUTO_INCREMENT=value
6. **Add comments to table and column names if comment is available**

### 🎯 CONVERSION WORKFLOW:

#### Step 1: Analyze MariaDB Table
```sql
-- Input example:
CREATE TABLE IF NOT EXISTS `table_name` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`)
) AUTO_INCREMENT=1000;
```

#### Step 2: Extract Information
- Table name: `table_name`
- AUTO_INCREMENT column: `id`
- Start value: `1000`
- Indexes: `idx_name` on `name`
- Data types: `int(11)` → `NUMBER(10)`, `varchar(255)` → `VARCHAR2(255)`

#### Step 3: Generate Oracle Code (EXACT PATTERN)
```sql
-- 1. Create table with named constraint
CREATE TABLE table_name (
  id NUMBER(10) NOT NULL,
  name VARCHAR2(255) DEFAULT NULL,
  CONSTRAINT table_name_PK PRIMARY KEY (id)
);

-- 2. Create indexes
CREATE INDEX idx_name ON table_name (name);

-- 3. Create sequence (NO TRIGGER)
CREATE SEQUENCE table_name_sq START WITH 1000 INCREMENT BY 1;
```

## MANDATORY Data Type Conversions

| MariaDB | Oracle | NEVER USE |
|---------|--------|-----------|
| `INT(n)` | `NUMBER(10)` | `INTEGER` |
| `TINYINT(1)` | `NUMBER(1)` | `BOOLEAN` |
| `VARCHAR(n)` | `VARCHAR2(n)` | `VARCHAR` |
| `DATETIME` | `TIMESTAMP` | `DATE` |
| `LONGTEXT` | `CLOB` | `LONG` |
| `DOUBLE` | `NUMBER` | `FLOAT` |

## FORBIDDEN Patterns - DO NOT USE

### ❌ NEVER Create AUTO_INCREMENT Triggers
```sql
-- WRONG - DO NOT DO THIS:
CREATE OR REPLACE TRIGGER table_name_tr
  BEFORE INSERT ON table_name FOR EACH ROW 
  BEGIN 
    IF :NEW.id IS NULL THEN 
      SELECT table_name_sq.NEXTVAL INTO :NEW.id FROM DUAL; 
    END IF; 
  END;
```

### ❌ NEVER Use Existence Checks for Tables
```sql
-- WRONG - DO NOT DO THIS:
DECLARE
  tableCount NUMBER;
BEGIN
  SELECT COUNT(*) INTO tableCount FROM USER_TABLES WHERE TABLE_NAME = 'TABLE_NAME';
  IF (tableCount <= 0) THEN
    EXECUTE IMMEDIATE 'CREATE TABLE...';
  END IF;
END;
```

### ❌ NEVER Use Unnamed Constraints
```sql
-- WRONG:
PRIMARY KEY (id)

-- CORRECT:
CONSTRAINT table_name_PK PRIMARY KEY (id)
```

## REQUIRED Patterns - ALWAYS USE

### ✅ Table Creation Pattern
```sql
CREATE TABLE {table_name} (
  {column_definitions},
  CONSTRAINT {table_name}_PK PRIMARY KEY ({pk_column})
);
```

### ✅ Index Creation Pattern
```sql
CREATE INDEX {index_name} ON {table_name} ({column_list});
```

### ✅ Sequence Creation Pattern
```sql
CREATE SEQUENCE {table_name}_sq START WITH {start_value} INCREMENT BY 1;
```

## Oracle 30-Character Table Name Limit

**CRITICAL RULE**: Oracle table names cannot exceed 30 characters. When MariaDB table names are longer, they MUST be abbreviated.

### Abbreviation Strategy:
1. **Check actual Oracle file first** - Use existing abbreviation if table already exists
2. **If new table**, apply these abbreviation rules:

| Full Word | Abbreviation | Example |
|-----------|--------------|---------|
| `ADDRESS` | `ADDR` | `AS_RM_ACTIVITY_ADDRESS_CODE_ADDRESS` → `AS_RM_ACTVTY_ADDR_CD_ADDRSS` |
| `REQUIREMENT` | `RQRMNT` or `RQIREMENT` | `AS_RM_REQUIREMENT_AAC_ADDRESS` → `AS_RM_RQIREMENT_AAC_ADDRESS` |
| `ACTIVITY` | `ACTVTY` | `AS_RM_ACTIVITY_ADDRESS_CODE` → `AS_RM_ACTVTY_ADDR_CD` |
| `TEMPLATE` | `TMPLT` | `AS_RM_TMG_TEMPLATE_TASK` → `AS_RM_TMG_TMPLT_TSK` |
| `PRECEDENT` | `PRCDNT` | `AS_RM_TMG_TEMPLATE_TASK_PRECEDENT` → `AS_RM_TMG_TMPLT_TSK_PRCDNT` |
| `QUESTION` | `QSTN` | `AS_RM_QNM_QUESTION_CATEGORY` → `AS_RM_QNM_QSTN_CATEGORY` |
| `RESPONSE` | `RSPNS` | `AS_RM_QNM_RESPONSE_REQUIREMENT` → `AS_RM_QNM_RSPNS_RQRMNT` |
| `DOCUMENT` | `DCMNT` | `AS_RM_REQUIREMENT_DOCUMENT` → `AS_RM_RQRMNT_DCMNT` |
| `INFORMATION` | `INFRMTN` | `AS_RM_FUNDING_INFORMATION` → `AS_RM_FNDNG_INFRMTN` |
| `MANAGEMENT` | `MGMT` | `AS_RM_TASK_MANAGEMENT` → `AS_RM_TSK_MGMT` |

### Name Length Validation:
```sql
-- ALWAYS verify table name length before creation:
-- Length check: AS_RM_REQUIREMENT_AAC_ADDRESS = 29 chars ✓
-- Length check: AS_RM_A_R_REQUIREMENT_AAC_ADDRESS_FIELD = 38 chars ❌
-- Must abbreviate: AS_RM_A_R_RQRMNT_AAC_ADDR_FLD = 30 chars ✓
```

## Special Cases - Handle Carefully

### Reserved Words - MUST Quote These Columns
```sql
-- When column name is reserved word, quote it:
"TIMESTAMP" TIMESTAMP  -- Note the quotes
"COMMENT" VARCHAR2(4000)  -- COMMENT is reserved
"DATE" DATE  -- DATE is reserved
"ORDER" NUMBER(10)  -- ORDER is reserved
```

### Common Reserved Words in Oracle:
- `COMMENT` → `"COMMENT"`
- `TIMESTAMP` → `"TIMESTAMP"`
- `DATE` → `"DATE"`
- `ORDER` → `"ORDER"`
- `SIZE` → `"SIZE"`
- `LEVEL` → `"LEVEL"`

### Framework Tables Only
Only these tables get AUTO_INCREMENT triggers:
- `AS_GAM_SCRIPT_EXEC_HIST`
- `AS_RM_SCRIPT_EXEC_HIST`

```sql
-- Framework trigger pattern:
EXECUTE IMMEDIATE 'CREATE OR REPLACE TRIGGER AS_GAM_SCRIPT_EXEC_HIST_tr 
  BEFORE INSERT ON AS_GAM_SCRIPT_EXEC_HIST FOR EACH ROW 
  BEGIN 
    IF :NEW.scriptexecuteid IS NULL THEN 
      SELECT AS_GAM_SCRIPT_EXEC_HIST_sq.NEXTVAL INTO :NEW.scriptexecuteid FROM DUAL; 
    END IF; 
  END';
```

## Validation Checklist for AI Agent

Before outputting Oracle code, verify:

- [ ] No AUTO_INCREMENT triggers for regular tables
- [ ] All DDL uses EXECUTE IMMEDIATE
- [ ] All constraints are named with `_PK`, `_FK` suffixes
- [ ] All indexes created separately
- [ ] VARCHAR converted to VARCHAR2
- [ ] INT(n) converted to NUMBER(10)
- [ ] DATETIME converted to TIMESTAMP
- [ ] Sequence start values preserved
- [ ] **Table names ≤ 30 characters (Oracle limit)**
- [ ] **Check actual Oracle file for existing abbreviations**
- [ ] **Reserved words quoted (COMMENT, TIMESTAMP, DATE, ORDER)**
- [ ] **Preserve original column names (including typos)**

## Error Prevention

### Common Mistakes to Avoid:
1. **Creating triggers for every AUTO_INCREMENT** - Only framework tables need them
2. **Using VARCHAR instead of VARCHAR2** - Oracle prefers VARCHAR2
3. **Missing index creation** - Always create indexes separately
4. **Unnamed constraints** - Always name constraints explicitly
5. **Wrong data types** - Follow the conversion table exactly

### Quality Assurance:
- Every MariaDB table → 3 Oracle statements (table, index, sequence)
- Every AUTO_INCREMENT → 1 sequence (no trigger unless framework table)
- Every PRIMARY KEY → named constraint
- Every index → separate EXECUTE IMMEDIATE

## Example Complete Conversion

### Input (MariaDB):
```sql
CREATE TABLE IF NOT EXISTS `AS_RM_ACTIVITY_ADDRESS_CODE` (
  `AAC_ID` int(11) NOT NULL AUTO_INCREMENT,
  `AAC_REF_ID` int(11) DEFAULT NULL,
  `AAC` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`AAC_ID`),
  KEY `idx_aac_ref` (`AAC_REF_ID`)
) COMMENT = 'Contains reference values for Socio Economic Classification of Vendor Groups' AUTO_INCREMENT=1503;
```

### Output (Oracle):
```sql
CREATE TABLE AS_RM_ACTIVITY_ADDRESS_CODE (
  AAC_ID NUMBER(10) NOT NULL,
  AAC_REF_ID NUMBER(10) DEFAULT NULL,
  AAC VARCHAR2(255) DEFAULT NULL,
  CONSTRAINT AS_RM_ACTIVITY_ADDRESS_CODE_PK PRIMARY KEY (AAC_ID)
);

COMMENT ON TABLE AS_RM_ACTIVITY_ADDRESS_CODE IS 'Contains reference values for Socio Economic Classification of Vendor Groups';

CREATE INDEX idx_aac_ref ON AS_RM_ACTIVITY_ADDRESS_CODE (AAC_REF_ID);

CREATE SEQUENCE AS_RM_ACTIVITY_ADDRESS_CODE_sq START WITH 1503 INCREMENT BY 1;
```

## Final Instructions for AI Agent

1. **Process each MariaDB table individually**
2. **Generate exactly 3 Oracle statements per table** (table, indexes, sequence)
3. **Always validate against the checklist**
4. **When in doubt, follow the actual Oracle file patterns shown in this guide**

This guide is based on analysis of production Oracle scripts and must be followed exactly to ensure compatibility with the existing Oracle implementation.
