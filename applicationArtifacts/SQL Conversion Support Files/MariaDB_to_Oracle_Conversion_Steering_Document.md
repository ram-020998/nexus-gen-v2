# MariaDB to Oracle SQL Conversion Steering Document

## Table of Contents
1. [Overview](#overview)
2. [Data Type Conversions](#data-type-conversions)
3. [Table Creation Patterns](#table-creation-patterns)
4. [Insert Statement Patterns](#insert-statement-patterns)
5. [Index and Constraint Patterns](#index-and-constraint-patterns)
6. [Sequence Patterns](#sequence-patterns)
7. [Trigger Patterns](#trigger-patterns)
8. [Function and Procedure Patterns](#function-and-procedure-patterns)
9. [View Patterns](#view-patterns)
10. [Update and Delete Patterns](#update-and-delete-patterns)
11. [Special Oracle Considerations](#special-oracle-considerations)
12. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)

## Overview

This document provides comprehensive guidance for converting MariaDB SQL scripts to Oracle SQL scripts. It covers all major database objects and SQL constructs with detailed examples and conversion patterns.

## Data Type Conversions

### MariaDB to Oracle Data Type Mapping Table

| MariaDB Type | Oracle Equivalent | Notes |
|--------------|------------------|-------|
| `TINYINT` | `NUMBER(3)` | Range: -128 to 127 |
| `TINYINT(1)` | `NUMBER(1)` | Used for boolean values |
| `SMALLINT` | `NUMBER(5)` | Range: -32,768 to 32,767 |
| `MEDIUMINT` | `NUMBER(7)` | Range: -8,388,608 to 8,388,607 |
| `INT` / `INTEGER` | `NUMBER(10)` | Range: -2,147,483,648 to 2,147,483,647 |
| `BIGINT` | `NUMBER(19)` | Range: -9,223,372,036,854,775,808 to 9,223,372,036,854,775,807 |
| `DECIMAL(p,s)` | `NUMBER(p,s)` | Same precision and scale |
| `NUMERIC(p,s)` | `NUMBER(p,s)` | Same precision and scale |
| `FLOAT` | `FLOAT` | Single precision |
| `DOUBLE` | `FLOAT` | Double precision |
| `REAL` | `FLOAT` | Real number |
| `BIT(n)` | `RAW(n)` | Bit string |
| `BOOLEAN` | `NUMBER(1)` | 0 = false, 1 = true |
| `VARCHAR(n)` | `VARCHAR2(n)` | Variable length string |
| `CHAR(n)` | `CHAR(n)` | Fixed length string |
| `TEXT` | `CLOB` | Large text |
| `TINYTEXT` | `VARCHAR2(255)` | Small text |
| `MEDIUMTEXT` | `CLOB` | Medium text |
| `LONGTEXT` | `CLOB` | Large text |
| `BINARY(n)` | `RAW(n)` | Fixed binary |
| `VARBINARY(n)` | `RAW(n)` | Variable binary |
| `BLOB` | `BLOB` | Binary large object |
| `TINYBLOB` | `RAW(255)` | Small binary |
| `MEDIUMBLOB` | `BLOB` | Medium binary |
| `LONGBLOB` | `BLOB` | Large binary |
| `DATE` | `DATE` | Date only |
| `TIME` | `TIMESTAMP` | Time only (use TIMESTAMP) |
| `DATETIME` | `TIMESTAMP` | Date and time |
| `TIMESTAMP` | `TIMESTAMP` | Timestamp |
| `YEAR` | `NUMBER(4)` | Year as number |
| `ENUM('a','b')` | `VARCHAR2(n) + CHECK` | Use CHECK constraint |
| `SET('a','b')` | `VARCHAR2(n)` | Comma-separated values |
| `JSON` | `CLOB + CHECK` | JSON validation with CHECK |

### Numeric Data Types

#### INTEGER Types
**MariaDB Pattern:**
```sql
`ID` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY
`SORT_ORDER` int(10) DEFAULT NULL
`IS_ACTIVE` tinyint(1) DEFAULT NULL
```

**Oracle Conversion:**
```sql
ID NUMBER(10) NOT NULL
SORT_ORDER NUMBER(10) DEFAULT NULL
IS_ACTIVE NUMBER(1) DEFAULT NULL
```

**Conversion Rules:**
- `int(11)` → `NUMBER(10)`
- `tinyint(1)` → `NUMBER(1)` (for boolean-like fields)
- `AUTO_INCREMENT` → Remove (handle with sequences)
- Remove size specifications in parentheses for Oracle NUMBER type

#### FLOAT/DOUBLE Types
**MariaDB Pattern:**
```sql
`UNIT_PRICE` DOUBLE DEFAULT NULL
`EXTENDED_PRICE` FLOAT DEFAULT NULL
```

**Oracle Conversion:**
```sql
UNIT_PRICE FLOAT DEFAULT NULL
EXTENDED_PRICE FLOAT DEFAULT NULL
```

### String Data Types

#### VARCHAR Types
**MariaDB Pattern:**
```sql
`COUNTRY_NAME` varchar(50) NOT NULL
`DESCRIPTION` varchar(4000) DEFAULT NULL
```

**Oracle Conversion:**
```sql
COUNTRY_NAME VARCHAR2(50) NOT NULL
DESCRIPTION VARCHAR2(4000) DEFAULT NULL
```

**Conversion Rules:**
- `varchar(n)` → `VARCHAR2(n)`
- Maximum length in Oracle VARCHAR2 is 4000 bytes (32767 in 12c+)

#### TEXT Types
**MariaDB Pattern:**
```sql
`LONG_DESCRIPTION` TEXT
`COMMENTS` LONGTEXT
```

**Oracle Conversion:**
```sql
LONG_DESCRIPTION CLOB
COMMENTS CLOB
```

### Date and Time Types

#### DATETIME Types
**MariaDB Pattern:**
```sql
`CREATED_DATE_TIME` datetime DEFAULT NULL
`MODIFIED_DATETIME` datetime DEFAULT CURRENT_TIMESTAMP
```

**Oracle Conversion:**
```sql
CREATED_DATE_TIME TIMESTAMP DEFAULT NULL
MODIFIED_DATETIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### DATE Types
**MariaDB Pattern:**
```sql
`AWARD_DATE` DATE DEFAULT NULL
```

**Oracle Conversion:**
```sql
AWARD_DATE DATE DEFAULT NULL
```

### Boolean Types
**MariaDB Pattern:**
```sql
`IS_ACTIVE` tinyint(1) DEFAULT NULL
`IS_DELETED` boolean DEFAULT false
```

**Oracle Conversion:**
```sql
IS_ACTIVE NUMBER(1) DEFAULT NULL
IS_DELETED NUMBER(1) DEFAULT 0
```

**Conversion Rules:**
- `tinyint(1)` → `NUMBER(1)`
- `boolean` → `NUMBER(1)`
- `true` → `1`
- `false` → `0`

## Column Keywords and Attributes Conversion

### NULL/NOT NULL Constraints
**MariaDB Pattern:**
```sql
`COUNTRY_NAME` varchar(50) NOT NULL
`DESCRIPTION` varchar(255) DEFAULT NULL
`ID` int(11) NOT NULL
```

**Oracle Conversion:**
```sql
COUNTRY_NAME VARCHAR2(50) NOT NULL
DESCRIPTION VARCHAR2(255) DEFAULT NULL
ID NUMBER(10) NOT NULL
```

**Conversion Rules:**
- `NOT NULL` → `NOT NULL` (same)
- `DEFAULT NULL` → `DEFAULT NULL` (same)
- `NULL` → `NULL` (same, but usually omitted)

### DEFAULT Values
**MariaDB Pattern:**
```sql
`CREATED_DATETIME` datetime DEFAULT CURRENT_TIMESTAMP
`IS_ACTIVE` tinyint(1) DEFAULT 1
`STATUS` varchar(50) DEFAULT 'ACTIVE'
`SORT_ORDER` int(11) DEFAULT 0
```

**Oracle Conversion:**
```sql
CREATED_DATETIME TIMESTAMP DEFAULT CURRENT_TIMESTAMP
IS_ACTIVE NUMBER(1) DEFAULT 1
STATUS VARCHAR2(50) DEFAULT 'ACTIVE'
SORT_ORDER NUMBER(10) DEFAULT 0
```

**Conversion Rules:**
- `DEFAULT CURRENT_TIMESTAMP` → `DEFAULT CURRENT_TIMESTAMP`
- `DEFAULT NOW()` → `DEFAULT CURRENT_TIMESTAMP`
- `DEFAULT 'string'` → `DEFAULT 'string'` (same)
- `DEFAULT number` → `DEFAULT number` (same)

### AUTO_INCREMENT Attribute
**MariaDB Pattern:**
```sql
`ID` int(11) NOT NULL AUTO_INCREMENT
`SEQUENCE_ID` bigint(20) NOT NULL AUTO_INCREMENT
```

**Oracle Conversion:**
```sql
ID NUMBER(10) NOT NULL
SEQUENCE_ID NUMBER(19) NOT NULL

-- Separate sequence creation required
CREATE SEQUENCE table_name_SQ START WITH 1 INCREMENT BY 1;
```

**Conversion Rules:**
- Remove `AUTO_INCREMENT` keyword completely
- Create separate sequence with naming convention: `{TABLE_NAME}_SQ`
- Use sequence in INSERT statements: `sequence_name.NEXTVAL`

### PRIMARY KEY Constraints
**MariaDB Pattern:**
```sql
-- Inline primary key
`ID` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY

-- Table-level primary key
PRIMARY KEY (`ID`)

-- Composite primary key
PRIMARY KEY (`ID`, `TYPE`)
```

**Oracle Conversion:**
```sql
-- Inline primary key (not recommended)
ID NUMBER(10) NOT NULL PRIMARY KEY

-- Table-level primary key (recommended)
CONSTRAINT table_name_PK PRIMARY KEY (ID)

-- Composite primary key
CONSTRAINT table_name_PK PRIMARY KEY (ID, TYPE)
```

**Conversion Rules:**
- Move PRIMARY KEY to table level with explicit constraint name
- Use naming convention: `{TABLE_NAME}_PK`
- Remove `AUTO_INCREMENT` and handle with sequences

### UNIQUE Constraints
**MariaDB Pattern:**
```sql
`EMAIL` varchar(255) UNIQUE
`CODE` varchar(10) UNIQUE KEY
UNIQUE KEY `unique_code` (`CODE`)
```

**Oracle Conversion:**
```sql
EMAIL VARCHAR2(255)
CODE VARCHAR2(10)

-- Add as table constraints
CONSTRAINT table_name_email_UK UNIQUE (EMAIL)
CONSTRAINT table_name_code_UK UNIQUE (CODE)
```

**Conversion Rules:**
- Remove inline `UNIQUE` keyword
- Create explicit UNIQUE constraints at table level
- Use naming convention: `{TABLE_NAME}_{COLUMN}_UK`

### CHECK Constraints
**MariaDB Pattern:**
```sql
`STATUS` varchar(20) CHECK (`STATUS` IN ('ACTIVE', 'INACTIVE'))
`PERCENTAGE` decimal(5,2) CHECK (`PERCENTAGE` >= 0 AND `PERCENTAGE` <= 100)
```

**Oracle Conversion:**
```sql
STATUS VARCHAR2(20)
PERCENTAGE NUMBER(5,2)

-- Add as table constraints
CONSTRAINT table_name_status_CK CHECK (STATUS IN ('ACTIVE', 'INACTIVE'))
CONSTRAINT table_name_percentage_CK CHECK (PERCENTAGE >= 0 AND PERCENTAGE <= 100)
```

**Conversion Rules:**
- Move CHECK constraints to table level
- Use naming convention: `{TABLE_NAME}_{COLUMN}_CK`
- Remove backticks from constraint expressions

### COMMENT Attribute
**MariaDB Pattern:**
```sql
`ID` int(11) NOT NULL COMMENT 'Primary key identifier'
`STATUS` varchar(20) COMMENT 'Record status: ACTIVE or INACTIVE'
```

**Oracle Conversion:**
```sql
ID NUMBER(10) NOT NULL
STATUS VARCHAR2(20)

-- Add comments separately
COMMENT ON COLUMN table_name.ID IS 'Primary key identifier';
COMMENT ON COLUMN table_name.STATUS IS 'Record status: ACTIVE or INACTIVE';
```

**Conversion Rules:**
- Remove inline `COMMENT` attribute
- Add `COMMENT ON COLUMN` statements after table creation
- Use single quotes for comment text

### Table-Level Comments
**MariaDB Pattern:**
```sql
CREATE TABLE `AS_RM_REQUIREMENT` (
  `ID` int(11) NOT NULL AUTO_INCREMENT,
  `TITLE` varchar(255) NOT NULL,
  `DESCRIPTION` text
) COMMENT='Table for storing requirement information';
```

**Oracle Conversion:**
```sql
CREATE TABLE AS_RM_REQUIREMENT (
    ID NUMBER(10) NOT NULL,
    TITLE VARCHAR2(255) NOT NULL,
    DESCRIPTION CLOB
);

-- Add table comment separately
COMMENT ON TABLE AS_RM_REQUIREMENT IS 'Table for storing requirement information';
```

**Conversion Rules:**
- Remove `COMMENT='text'` from CREATE TABLE statement
- Add `COMMENT ON TABLE` statement after table creation
- Use single quotes for comment text

### Complex Comments Example
**MariaDB Pattern:**
```sql
CREATE TABLE `USER_PROFILE` (
  `USER_ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'Unique identifier for user',
  `USERNAME` varchar(50) NOT NULL COMMENT 'Login username - must be unique',
  `EMAIL` varchar(255) NOT NULL COMMENT 'User email address for notifications',
  `STATUS` enum('ACTIVE','INACTIVE','SUSPENDED') COMMENT 'Current user status',
  `CREATED_DATE` datetime DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation timestamp',
  PRIMARY KEY (`USER_ID`)
) COMMENT='User profile information and account details';
```

**Oracle Conversion:**
```sql
CREATE TABLE USER_PROFILE (
    USER_ID NUMBER(10) NOT NULL,
    USERNAME VARCHAR2(50) NOT NULL,
    EMAIL VARCHAR2(255) NOT NULL,
    STATUS VARCHAR2(20),
    CREATED_DATE TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT USER_PROFILE_PK PRIMARY KEY (USER_ID),
    CONSTRAINT USER_PROFILE_status_CK CHECK (STATUS IN ('ACTIVE','INACTIVE','SUSPENDED'))
);

CREATE SEQUENCE USER_PROFILE_SQ START WITH 1 INCREMENT BY 1;

-- Add all comments after table creation
COMMENT ON TABLE USER_PROFILE IS 'User profile information and account details';
COMMENT ON COLUMN USER_PROFILE.USER_ID IS 'Unique identifier for user';
COMMENT ON COLUMN USER_PROFILE.USERNAME IS 'Login username - must be unique';
COMMENT ON COLUMN USER_PROFILE.EMAIL IS 'User email address for notifications';
COMMENT ON COLUMN USER_PROFILE.STATUS IS 'Current user status';
COMMENT ON COLUMN USER_PROFILE.CREATED_DATE IS 'Record creation timestamp';
```

### Comments with Special Characters
**MariaDB Pattern:**
```sql
`DESCRIPTION` text COMMENT 'User\'s detailed description with "quotes" and symbols'
```

**Oracle Conversion:**
```sql
DESCRIPTION CLOB

-- Handle quotes in comments
COMMENT ON COLUMN table_name.DESCRIPTION IS 'User''s detailed description with "quotes" and symbols';
```

**Conversion Rules:**
- Escape single quotes by doubling them (`'` → `''`)
- Double quotes can remain as-is within single-quoted strings
- Handle special characters properly in comment text

### COLLATE Attribute
**MariaDB Pattern:**
```sql
`NAME` varchar(255) COLLATE utf8_unicode_ci
`DESCRIPTION` text COLLATE utf8mb4_general_ci
```

**Oracle Conversion:**
```sql
NAME VARCHAR2(255)
DESCRIPTION CLOB
```

**Conversion Rules:**
- Remove `COLLATE` attribute (Oracle handles collation at database/session level)
- Set appropriate NLS parameters at database level if needed

### ZEROFILL and UNSIGNED Attributes
**MariaDB Pattern:**
```sql
`ID` int(11) UNSIGNED NOT NULL
`AMOUNT` decimal(10,2) UNSIGNED ZEROFILL
`COUNTER` int(11) UNSIGNED ZEROFILL
```

**Oracle Conversion:**
```sql
ID NUMBER(10) NOT NULL
AMOUNT NUMBER(10,2)
COUNTER NUMBER(10)

-- Add check constraints for unsigned behavior if needed
CONSTRAINT table_name_id_CK CHECK (ID >= 0)
CONSTRAINT table_name_amount_CK CHECK (AMOUNT >= 0)
```

**Conversion Rules:**
- Remove `UNSIGNED` and `ZEROFILL` attributes
- Add CHECK constraints for non-negative values if business logic requires
- Handle zero-padding in application layer or with TO_CHAR formatting

### BINARY Attribute
**MariaDB Pattern:**
```sql
`CODE` varchar(50) BINARY
`HASH` char(32) BINARY
```

**Oracle Conversion:**
```sql
CODE VARCHAR2(50)
HASH CHAR(32)
```

**Conversion Rules:**
- Remove `BINARY` attribute
- Oracle VARCHAR2/CHAR are case-sensitive by default in comparisons when using binary collation
- Use appropriate NLS settings if case-insensitive comparison needed

### Generated Columns (Virtual/Stored)
**MariaDB Pattern:**
```sql
`FULL_NAME` varchar(255) GENERATED ALWAYS AS (CONCAT(`FIRST_NAME`, ' ', `LAST_NAME`)) VIRTUAL
`TOTAL_AMOUNT` decimal(10,2) AS (`UNIT_PRICE` * `QUANTITY`) STORED
```

**Oracle Conversion:**
```sql
FULL_NAME VARCHAR2(255) GENERATED ALWAYS AS (FIRST_NAME || ' ' || LAST_NAME) VIRTUAL
TOTAL_AMOUNT NUMBER(10,2) GENERATED ALWAYS AS (UNIT_PRICE * QUANTITY) STORED
```

**Conversion Rules:**
- `GENERATED ALWAYS AS` syntax is similar
- Replace `CONCAT()` with `||` operator
- `VIRTUAL` and `STORED` keywords remain the same
- Remove backticks from expressions

## Table Creation Patterns

### Basic Table Creation

#### MariaDB Pattern:
```sql
CREATE TABLE IF NOT EXISTS `AS_GAM_AWARD_REQUIREMENT_MAPPING` (
`ID` int(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
`AWARD_ID` int(11) DEFAULT NULL,
`REQUIREMENT_ID` int(11) DEFAULT NULL,
`CREATED_BY` varchar(255) DEFAULT NULL,
`CREATED_DATE_TIME` datetime DEFAULT NULL,
`MODIFIED_BY` varchar(255) DEFAULT NULL,
`MODIFIED_DATE_TIME` datetime DEFAULT NULL,
`IS_ACTIVE` tinyint(1) DEFAULT NULL
);
```

#### Oracle Conversion:
```sql
CREATE TABLE AS_GAM_AWRD_RQRMENT_MAPPING (
    ID NUMBER(10),
    AWARD_ID NUMBER(10),
    REQUIREMENT_ID NUMBER(10),
    CREATED_BY VARCHAR2(255),
    CREATED_DATE_TIME TIMESTAMP,
    MODIFIED_BY VARCHAR2(255),
    MODIFIED_DATE_TIME TIMESTAMP,
    IS_ACTIVE NUMBER(1),
    PRIMARY KEY(ID)
);

CREATE SEQUENCE AS_GAM_AWRD_RQRMENT_MAPPING_SQ START WITH 1 INCREMENT BY 1;
```

**Conversion Rules:**
1. Remove `IF NOT EXISTS` (Oracle doesn't support this)
2. Remove backticks around table and column names
3. Convert data types according to mapping rules
4. Move PRIMARY KEY constraint to separate line or use CONSTRAINT syntax
5. Create separate sequence for AUTO_INCREMENT columns
6. Shorten table names if they exceed Oracle's 30-character limit (pre-12.2)

### Table with Constraints

#### MariaDB Pattern:
```sql
CREATE TABLE IF NOT EXISTS `AS_GAM_R_COUNTRY` (
  `COUNTRY_ID` int(11) NOT NULL AUTO_INCREMENT,
  `COUNTRY_NAME` varchar(50) NOT NULL,
  `COUNTRY_CODE` varchar(5) NOT NULL,
  `IS_ACTIVE` tinyint(1) NOT NULL,
  PRIMARY KEY (`COUNTRY_ID`)
) AUTO_INCREMENT=245;
```

#### Oracle Conversion:
```sql
CREATE TABLE AS_GAM_R_COUNTRY (
    COUNTRY_ID NUMBER(10),
    COUNTRY_NAME VARCHAR2(50) NOT NULL,
    COUNTRY_CODE VARCHAR2(5) NOT NULL,
    IS_ACTIVE NUMBER(1) NOT NULL,
    CONSTRAINT AS_GAM_R_COUNTRY_PK PRIMARY KEY (COUNTRY_ID)
);

CREATE SEQUENCE AS_GAM_R_COUNTRY_sq START WITH 245 INCREMENT BY 1;
```

**Conversion Rules:**
1. Use explicit CONSTRAINT names for primary keys
2. Convert AUTO_INCREMENT start value to sequence START WITH clause
3. Remove AUTO_INCREMENT table option

## Insert Statement Patterns

### Simple Insert Statements

#### MariaDB Pattern:
```sql
INSERT IGNORE INTO `AS_GAM_R_COUNTRY` (`COUNTRY_ID`, `COUNTRY_NAME`, `COUNTRY_CODE`, `IS_ACTIVE`) VALUES
(1, 'Afghanistan', 'AF', true),
(2, 'Albania', 'AL', true),
(3, 'Algeria', 'DZ', true);
```

#### Oracle Conversion:
```sql
INSERT ALL
 INTO AS_GAM_R_COUNTRY (COUNTRY_ID, COUNTRY_NAME, COUNTRY_CODE, IS_ACTIVE) VALUES (1, 'Afghanistan', 'AF', 1)
 INTO AS_GAM_R_COUNTRY (COUNTRY_ID, COUNTRY_NAME, COUNTRY_CODE, IS_ACTIVE) VALUES (2, 'Albania', 'AL', 1)
 INTO AS_GAM_R_COUNTRY (COUNTRY_ID, COUNTRY_NAME, COUNTRY_CODE, IS_ACTIVE) VALUES (3, 'Algeria', 'DZ', 1)
SELECT * FROM dual;
```

**Conversion Rules:**
1. Replace `INSERT IGNORE INTO` with `INSERT ALL`
2. Convert multi-row VALUES to multiple INTO clauses
3. Add `SELECT * FROM dual;` at the end
4. Remove backticks from table and column names
5. Convert `true`/`false` to `1`/`0`

### Insert with Functions

#### MariaDB Pattern:
```sql
INSERT INTO `AS_RM_R_DATA` (`REF_DATA_ID`, `REF_LABEL`, `REF_TYPE`, `CREATED_DATETIME`) VALUES 
(118, 'New', 'Requirement Type', NOW());
```

#### Oracle Conversion:
```sql
INSERT INTO AS_RM_R_DATA (REF_DATA_ID, REF_LABEL, REF_TYPE, CREATED_DATETIME) VALUES 
(118, 'New', 'Requirement Type', CURRENT_TIMESTAMP);
```

**Conversion Rules:**
1. `NOW()` → `CURRENT_TIMESTAMP`
2. `CURRENT_TIMESTAMP()` → `CURRENT_TIMESTAMP`

### Insert with SELECT

#### MariaDB Pattern:
```sql
INSERT INTO AS_RM_R_DATA (REF_DATA_ID, REF_LABEL, REF_TYPE, IS_ACTIVE, CREATED_BY, CREATED_DATETIME) 
SELECT REF_DATA_ID, REF_LABEL, 'appian.administrator', CURRENT_TIMESTAMP(), 'appian.administrator', CURRENT_TIMESTAMP(), IS_ACTIVE 
FROM AS_RM_R_DATA 
WHERE REF_TYPE = 'Document Type';
```

#### Oracle Conversion:
```sql
INSERT INTO AS_RM_R_DATA (REF_DATA_ID, REF_LABEL, REF_TYPE, IS_ACTIVE, CREATED_BY, CREATED_DATETIME) 
SELECT REF_DATA_ID, REF_LABEL, 'appian.administrator', CURRENT_TIMESTAMP, 'appian.administrator', CURRENT_TIMESTAMP, IS_ACTIVE 
FROM AS_RM_R_DATA 
WHERE REF_TYPE = 'Document Type';
```

## Index and Constraint Patterns

### Index Creation

#### MariaDB Pattern:
```sql
ALTER TABLE `AS_GAM_A_R_AWARD_REQUIREMENT_MAPPING_FIELD` ADD KEY `asgmrwrdrqrmnt_smplfldchngs` (`MAPPING_AUDIT_ID`);
```

#### Oracle Conversion:
```sql
CREATE INDEX asrmrrqrmntcdd_smplfldchngs ON AS_RM_A_R_REQ_AC_ADDRSS_FLD (REQ_AAC_ADDRESS_AUDIT_ID);
```

**Conversion Rules:**
1. Convert `ALTER TABLE ... ADD KEY` to `CREATE INDEX`
2. Remove backticks
3. Ensure index names don't exceed 30 characters (pre-12.2)

### Foreign Key Constraints

#### MariaDB Pattern:
```sql
ALTER TABLE `AS_RM_REQUIREMENT` ADD CONSTRAINT `asrmrequirement_keydates` 
FOREIGN KEY (`KEY_DATES`) REFERENCES `AS_RM_REQUIREMENT_KEYDATES` (`KEY_DATES_ID`) ON DELETE CASCADE;
```

#### Oracle Conversion:
```sql
ALTER TABLE AS_RM_REQUIREMENT ADD CONSTRAINT asrmrequirement_keydates 
FOREIGN KEY (KEY_DATES) REFERENCES AS_RM_REQUIREMENT_KEYDATES (KEY_DATES_ID) ON DELETE CASCADE;
```

**Conversion Rules:**
1. Remove backticks from all identifiers
2. Syntax remains largely the same
3. Ensure constraint names don't exceed 30 characters (pre-12.2)

### Primary Key Constraints

#### MariaDB Pattern:
```sql
CREATE TABLE `AS_RM_REQUIREMENT` (
  `REQUIREMENT_ID` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`REQUIREMENT_ID`)
);
```

#### Oracle Conversion:
```sql
CREATE TABLE AS_RM_REQUIREMENT (
    REQUIREMENT_ID NUMBER(10),
    CONSTRAINT AS_RM_REQUIREMENT_PK PRIMARY KEY (REQUIREMENT_ID)
);
```

## Sequence Patterns

### Sequence Creation for AUTO_INCREMENT

#### MariaDB Pattern:
```sql
CREATE TABLE `AS_RM_REQUIREMENT` (
  `REQUIREMENT_ID` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`REQUIREMENT_ID`)
) AUTO_INCREMENT=1000;
```

#### Oracle Conversion:
```sql
CREATE TABLE AS_RM_REQUIREMENT (
    REQUIREMENT_ID NUMBER(10),
    CONSTRAINT AS_RM_REQUIREMENT_PK PRIMARY KEY (REQUIREMENT_ID)
);

CREATE SEQUENCE AS_RM_REQUIREMENT_SQ START WITH 1000 INCREMENT BY 1;
```

**Conversion Rules:**
1. Create sequence with same name as table + "_SQ" suffix
2. Use AUTO_INCREMENT start value for START WITH clause
3. Default INCREMENT BY 1

### Using Sequences in INSERT

#### MariaDB Pattern:
```sql
INSERT INTO `AS_RM_REQUIREMENT` (`TITLE`, `DESCRIPTION`) VALUES ('Test', 'Description');
```

#### Oracle Conversion:
```sql
INSERT INTO AS_RM_REQUIREMENT (REQUIREMENT_ID, TITLE, DESCRIPTION) 
VALUES (AS_RM_REQUIREMENT_SQ.NEXTVAL, 'Test', 'Description');
```

## Update Statement Patterns

### UPDATE with JOIN Conversion

#### MariaDB Pattern:
```sql
UPDATE AS_GCM_QNM_T_QSTON_CATEGORY S
JOIN(
     SELECT R.QUESTIONNAIRE_TEMPLATE_ID,
  R.QUESTION_CATEGORY_TEMPLATE_ID,
        ROW_NUMBER() OVER(
        PARTITION BY R.QUESTIONNAIRE_TEMPLATE_ID
    ORDER BY
        R.QUESTION_CATEGORY_TEMPLATE_ID
    ) AS display_order
FROM AS_GCM_QNM_T_QSTON_CATEGORY R) AS RankedRows
    ON
        S.QUESTION_CATEGORY_TEMPLATE_ID = RankedRows.QUESTION_CATEGORY_TEMPLATE_ID
    SET
        S.DISPLAY_ORDER = RankedRows.display_order WHERE S.DISPLAY_ORDER IS NULL;
```

#### Oracle Conversion:
```sql
MERGE INTO AS_GCM_QNM_T_QSTON_CATEGORY S
USING (
     SELECT R.QUESTIONNAIRE_TEMPLATE_ID,
  R.QUESTION_CATEGORY_TEMPLATE_ID,
        ROW_NUMBER() OVER(
        PARTITION BY R.QUESTIONNAIRE_TEMPLATE_ID
    ORDER BY
        R.QUESTION_CATEGORY_TEMPLATE_ID
    ) AS display_order
FROM AS_GCM_QNM_T_QSTON_CATEGORY R) RankedRows
ON (S.QUESTION_CATEGORY_TEMPLATE_ID = RankedRows.QUESTION_CATEGORY_TEMPLATE_ID)
WHEN MATCHED THEN
    UPDATE SET S.DISPLAY_ORDER = RankedRows.display_order WHERE S.DISPLAY_ORDER IS NULL;
```

**Conversion Rules:**
1. Replace `UPDATE table JOIN` with `MERGE INTO table USING`
2. Convert JOIN condition to ON clause with parentheses
3. Replace SET clause with `WHEN MATCHED THEN UPDATE SET`
4. WHERE condition moves inside the UPDATE SET clause
5. Remove table alias from subquery (AS RankedRows → RankedRows)

## Trigger Patterns

### BEFORE INSERT Triggers

#### MariaDB Pattern:
```sql
DROP TRIGGER IF EXISTS `AS_RM_Set_Serial_Number_And_Req_Number`;

DELIMITER $$
CREATE TRIGGER `AS_RM_Set_Serial_Number_And_Req_Number` BEFORE INSERT ON `AS_RM_REQUIREMENT` FOR EACH ROW BEGIN
  DECLARE aacCode VARCHAR(255);
  DECLARE previousSerialNumber VARCHAR(255);
  
  IF NEW.REQUIREMENT_AAC IS NOT NULL THEN
    SELECT AAC INTO aacCode FROM AS_RM_ACTIVITY_ADDRESS_CODE WHERE AAC_ID = NEW.REQUIREMENT_AAC;
    SET NEW.REQ_NUMBER = CONCAT(aacCode, '-', LPAD(NEW.REQUIREMENT_ID, 6, '0'));
  END IF;
END$$
DELIMITER ;
```

#### Oracle Conversion:
```sql
CREATE OR REPLACE TRIGGER AS_RM_ST_SRL_NMBR_AND_RQ_NMBER 
BEFORE INSERT ON AS_RM_REQUIREMENT FOR EACH ROW
DECLARE
  aacCode VARCHAR2(255);
  previousSerialNumber VARCHAR2(255);
BEGIN
  IF :NEW.REQUIREMENT_AAC IS NOT NULL THEN
    SELECT AAC INTO aacCode FROM AS_RM_ACTIVITY_ADDRESS_CODE WHERE AAC_ID = :NEW.REQUIREMENT_AAC;
    :NEW.REQ_NUMBER := aacCode || '-' || LPAD(:NEW.REQUIREMENT_ID, 6, '0');
  END IF;
END;
/
```

**Conversion Rules:**
1. Remove `DROP TRIGGER IF EXISTS` (use `CREATE OR REPLACE`)
2. Remove DELIMITER statements
3. Use `:NEW` and `:OLD` instead of `NEW` and `OLD`
4. Use `VARCHAR2` instead of `VARCHAR`
5. Use `||` for concatenation instead of `CONCAT()`
6. Use `:=` for assignment instead of `SET`
7. End with `/` instead of `$$`

### AFTER INSERT Triggers

#### MariaDB Pattern:
```sql
CREATE TRIGGER AS_RM_POP_KYDTS_PRNT_TBL_INSRT AFTER INSERT ON AS_RM_REQUIREMENT_KEYDATES
 FOR EACH ROW BEGIN
	UPDATE AS_RM_REQUIREMENT R
  	SET R.KEY_DATES= NEW.KEY_DATES_ID WHERE
  	R.REQUIREMENT_ID=NEW.REQUIREMENT_ID;
END$$
```

#### Oracle Conversion:
```sql
CREATE OR REPLACE TRIGGER AS_RM_POP_KYDTS_PRNT_TBL_INSRT 
AFTER INSERT ON AS_RM_REQUIREMENT_KEYDATES
FOR EACH ROW
BEGIN
  UPDATE AS_RM_REQUIREMENT R
  SET R.KEY_DATES= :NEW.KEY_DATES_ID WHERE
  R.REQUIREMENT_ID=:NEW.REQUIREMENT_ID;
END;
/
```

## Function and Procedure Patterns

### Stored Procedures

#### MariaDB Pattern:
```sql
DELIMITER $$
CREATE PROCEDURE GetRequirementDetails(IN req_id INT)
BEGIN
    SELECT * FROM AS_RM_REQUIREMENT WHERE REQUIREMENT_ID = req_id;
END$$
DELIMITER ;
```

#### Oracle Conversion:
```sql
CREATE OR REPLACE PROCEDURE GetRequirementDetails(req_id IN NUMBER)
IS
BEGIN
    SELECT * FROM AS_RM_REQUIREMENT WHERE REQUIREMENT_ID = req_id;
END;
/
```

**Conversion Rules:**
1. Remove DELIMITER statements
2. Use `IS` instead of `BEGIN` after parameter declaration
3. Use `IN`, `OUT`, `IN OUT` parameter modes explicitly
4. Use `NUMBER` instead of `INT`
5. End with `/`

### Functions

#### MariaDB Pattern:
```sql
DELIMITER $$
CREATE FUNCTION CalculateTotal(amount DECIMAL(10,2), tax_rate DECIMAL(5,4))
RETURNS DECIMAL(10,2)
READS SQL DATA
DETERMINISTIC
BEGIN
    RETURN amount * (1 + tax_rate);
END$$
DELIMITER ;
```

#### Oracle Conversion:
```sql
CREATE OR REPLACE FUNCTION CalculateTotal(amount NUMBER, tax_rate NUMBER)
RETURN NUMBER
IS
BEGIN
    RETURN amount * (1 + tax_rate);
END;
/
```

**Conversion Rules:**
1. Use `RETURN` instead of `RETURNS`
2. Remove `READS SQL DATA` and `DETERMINISTIC` (use different syntax in Oracle)
3. Use `NUMBER` instead of `DECIMAL`

## View Patterns

### Simple Views

#### MariaDB Pattern:
```sql
CREATE VIEW `requirement_summary` AS
SELECT 
    `REQUIREMENT_ID`,
    `TITLE`,
    `STATUS`,
    `CREATED_DATE_TIME`
FROM `AS_RM_REQUIREMENT`
WHERE `IS_ACTIVE` = true;
```

#### Oracle Conversion:
```sql
CREATE VIEW requirement_summary AS
SELECT 
    REQUIREMENT_ID,
    TITLE,
    STATUS,
    CREATED_DATE_TIME
FROM AS_RM_REQUIREMENT
WHERE IS_ACTIVE = 1;
```

**Conversion Rules:**
1. Remove backticks
2. Convert `true`/`false` to `1`/`0`

## Update and Delete Patterns

### UPDATE Statements

#### MariaDB Pattern:
```sql
UPDATE `AS_GAM_R_COUNTRY` SET `SAM_GOV_CODE` = 'USA' WHERE `COUNTRY_NAME` = "United States";
```

#### Oracle Conversion:
```sql
UPDATE AS_GAM_R_COUNTRY SET SAM_GOV_CODE = 'USA' WHERE COUNTRY_NAME = 'United States';
```

**Conversion Rules:**
1. Remove backticks
2. Use single quotes for string literals consistently

### DELETE Statements

#### MariaDB Pattern:
```sql
DELETE FROM `AS_RM_REQUIREMENT` WHERE `IS_ACTIVE` = false;
```

#### Oracle Conversion:
```sql
DELETE FROM AS_RM_REQUIREMENT WHERE IS_ACTIVE = 0;
```

## Special Oracle Considerations

### MERGE Statements

Oracle provides MERGE for upsert operations:

#### Oracle Pattern:
```sql
MERGE INTO AS_RM_R_DOCUMENT_TYPE docType 
USING AS_RM_R_DATA rData ON (docType.DOCUMENT_TYPE_ID+60 = rData.REF_DATA_ID)
WHEN MATCHED THEN 
    UPDATE SET docType.LABEL = rData.REF_LABEL, docType.IS_ACTIVE = rData.IS_ACTIVE 
    WHERE rData.REF_TYPE = 'Document Type';
```

### DUAL Table

Oracle requires FROM clause in SELECT statements:

#### Oracle Pattern:
```sql
SELECT 1 FROM DUAL;
SELECT CURRENT_TIMESTAMP FROM DUAL;
```

### String Concatenation

#### MariaDB Pattern:
```sql
SELECT CONCAT(first_name, ' ', last_name) AS full_name FROM users;
```

#### Oracle Conversion:
```sql
SELECT first_name || ' ' || last_name AS full_name FROM users;
```

### LIMIT vs ROWNUM

#### MariaDB Pattern:
```sql
SELECT * FROM AS_RM_REQUIREMENT ORDER BY CREATED_DATE_TIME DESC LIMIT 10;
```

#### Oracle Conversion (Pre-12c):
```sql
SELECT * FROM (
    SELECT * FROM AS_RM_REQUIREMENT ORDER BY CREATED_DATE_TIME DESC
) WHERE ROWNUM <= 10;
```

#### Oracle Conversion (12c+):
```sql
SELECT * FROM AS_RM_REQUIREMENT ORDER BY CREATED_DATE_TIME DESC FETCH FIRST 10 ROWS ONLY;
```

## Common Pitfalls and Solutions

### 1. Identifier Length Limits

**Issue:** Oracle has 30-character limit for identifiers (pre-12.2)

**Solution:** Truncate long names systematically:
```sql
-- MariaDB
AS_GAM_A_R_AWARD_REQUIREMENT_MAPPING_FIELD

-- Oracle
AS_GAM_A_R_AWRD_REQ_MAP_FLD
```

### 2. Reserved Words

**Issue:** Oracle has different reserved words than MariaDB

**Solution:** Use quotes or rename:
```sql
-- If "COMMENT" is reserved
"COMMENT" VARCHAR2(255)
-- Or rename
COMMENT_TEXT VARCHAR2(255)
```

### 3. Case Sensitivity

**Issue:** Oracle converts unquoted identifiers to uppercase

**Solution:** Be consistent with casing or use quotes:
```sql
-- These are the same in Oracle
CREATE TABLE test_table (id NUMBER);
CREATE TABLE TEST_TABLE (ID NUMBER);

-- These are different
CREATE TABLE "test_table" (id NUMBER);
CREATE TABLE "TEST_TABLE" (ID NUMBER);
```

### 4. Date Formats

**Issue:** Different default date formats

**Solution:** Use explicit format masks:
```sql
-- MariaDB
'2023-01-01 10:30:00'

-- Oracle
TO_TIMESTAMP('2023-01-01 10:30:00', 'YYYY-MM-DD HH24:MI:SS')
```

### 5. Boolean Values

**Issue:** Oracle doesn't have native boolean type

**Solution:** Use NUMBER(1) with check constraints:
```sql
CREATE TABLE test_table (
    id NUMBER(10),
    is_active NUMBER(1),
    CONSTRAINT chk_is_active CHECK (is_active IN (0,1))
);
```

### 6. AUTO_INCREMENT Handling

**Issue:** Oracle doesn't have AUTO_INCREMENT

**Solution:** Use sequences and triggers or default values:
```sql
-- Method 1: Trigger
CREATE SEQUENCE test_seq START WITH 1 INCREMENT BY 1;

CREATE OR REPLACE TRIGGER test_trigger
BEFORE INSERT ON test_table
FOR EACH ROW
BEGIN
    :NEW.id := test_seq.NEXTVAL;
END;
/

-- Method 2: Default value (12c+)
CREATE TABLE test_table (
    id NUMBER DEFAULT test_seq.NEXTVAL,
    name VARCHAR2(100)
);
```

### 7. String Escaping

**Issue:** Different escaping rules for quotes

**Solution:** Use consistent escaping:
```sql
-- MariaDB
'It''s a test'
"It's a test"

-- Oracle
'It''s a test'
```

### 8. Transaction Control

**Issue:** Different autocommit behavior

**Solution:** Explicit transaction control:
```sql
-- Oracle
BEGIN
    INSERT INTO table1 VALUES (...);
    UPDATE table2 SET ...;
    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;
END;
/
```

## Conversion Checklist

### Pre-Conversion Analysis
- [ ] Identify all database objects (tables, views, procedures, functions, triggers)
- [ ] List all custom data types and functions used
- [ ] Identify long identifier names that need truncation
- [ ] Check for MariaDB-specific features that need alternatives

### Table Conversion
- [ ] Remove backticks from all identifiers
- [ ] Convert data types according to mapping rules
- [ ] Handle AUTO_INCREMENT columns with sequences
- [ ] Convert IF NOT EXISTS logic
- [ ] Shorten table/column names if necessary
- [ ] Add explicit constraint names

### Data Conversion
- [ ] Convert boolean values (true/false to 1/0)
- [ ] Update date/time functions (NOW() to CURRENT_TIMESTAMP)
- [ ] Handle string concatenation (CONCAT() to ||)
- [ ] Convert LIMIT clauses to ROWNUM or FETCH

### Index and Constraint Conversion
- [ ] Convert ADD KEY to CREATE INDEX
- [ ] Ensure constraint names are within length limits
- [ ] Verify foreign key references are correct

### Procedure/Function Conversion
- [ ] Remove DELIMITER statements
- [ ] Convert parameter syntax
- [ ] Update variable declarations
- [ ] Convert control structures
- [ ] Handle exception handling differences

### Testing and Validation
- [ ] Verify all objects compile successfully
- [ ] Test data insertion and retrieval
- [ ] Validate constraint enforcement
- [ ] Test trigger functionality
- [ ] Performance testing with Oracle optimizer

This steering document provides comprehensive guidance for converting MariaDB scripts to Oracle. Each pattern should be applied consistently throughout the conversion process to ensure accuracy and maintainability of the resulting Oracle scripts.
