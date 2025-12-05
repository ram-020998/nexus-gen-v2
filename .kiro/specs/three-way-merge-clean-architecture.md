# Three-Way Merge Clean Architecture Specification

**Version:** 1.0  
**Date:** 2025-11-30  
**Status:** Draft for Implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Business Requirements](#business-requirements)
3. [Current State Analysis](#current-state-analysis)
4. [Target Architecture](#target-architecture)
5. [Database Schema](#database-schema)
6. [Service Layer Design](#service-layer-design)
7. [Data Flow](#data-flow)
8. [Implementation Plan](#implementation-plan)
9. [Testing Strategy](#testing-strategy)

---

## 1. Executive Summary

### Purpose
This document defines the complete architecture for rebuilding the three-way merge functionality from scratch, addressing critical data duplication issues and implementing proper OOP design patterns.

### Key Problems Identified
1. **Data Duplication**: Same objects stored multiple times across tables
2. **Inconsistent References**: Objects referenced from wrong tables/packages
3. **Blueprint Dependency**: Over-reliance on deprecated blueprint generation
4. **Poor Separation of Concerns**: Mixed responsibilities across services
5. **Incomplete Extraction**: Missing data from XML objects
6. **No Delta-Driven Workflow**: Working set includes non-delta objects

### Solution Approach
- **Global Object Registry**: Single source of truth for all objects (object_lookup)
- **Package-Object Mapping**: Separate table tracking object-package relationships
- **Delta-Driven Workflow**: Only process objects that changed in vendor package (A→C)
- **Object-Specific Tables**: Dedicated tables for each Appian object type
- **Comparison Result Storage**: Persistent storage of all comparison results
- **Clean OOP Design**: Repository pattern, service layer, dependency injection

---

## 2. Business Requirements

### 2.1 Core Workflow

**User uploads three packages:**
- **Package A**: Vendor Base Version (original)
- **Package B**: Customer Customized Version (with customer changes)
- **Package C**: Vendor New Version (latest from vendor)

**System must:**
1. Extract all objects from all three packages
2. Store objects without duplication (one entry per unique UUID)
3. Track which objects belong to which packages
4. Compare A→C to identify vendor delta (NEW, MODIFIED, DEPRECATED)
5. Compare delta objects against B to classify conflicts
6. Present working set to user for review
7. Generate merge guidance for each change
8. Support object-specific comparison views

### 2.2 Classification Rules

The system must implement **7 classification rules**:

| Rule | Condition | Classification |
|------|-----------|----------------|
| 10a | Modified in delta AND not modified in customer | NO_CONFLICT |
| 10b | Modified in delta AND modified in customer | CONFLICT |
| 10c | Modified in delta AND removed in customer | DELETED |
| 10d | New object in delta | NEW |
| 10e | Deprecated in delta AND not modified in customer | NO_CONFLICT |
| 10f | Deprecated in delta AND modified in customer | CONFLICT |
| 10g | Deprecated in delta AND removed in customer | NO_CONFLICT |

**Classifications:**
- `NO_CONFLICT`: Can be auto-merged
- `CONFLICT`: Requires manual review
- `NEW`: New vendor object to add
- `DELETED`: Object removed by customer

**Removed Classifications:**
- ~~`CUSTOMER_ONLY`~~ - Not part of working set
- ~~`REMOVED_BUT_CUSTOMIZED`~~ - Covered by DELETED

### 2.3 Object Types to Support

Must extract and compare these Appian object types:

1. **Interface** - SAIL code, parameters, security
2. **Expression Rule** - SAIL code, inputs, output type
3. **Integration** - SAIL code, connection details, auth
4. **Web API** - SAIL code, endpoints, methods
5. **Record Type** - Fields, relationships, views, actions
6. **CDT (Custom Data Type)** - Fields, namespace
7. **Process Model** - Nodes, flows, variables, complexity
8. **Site** - Pages, hierarchy
9. **Group** - Members, parent group, properties
10. **Constant** - Value, data type, scope
11. **Connected System** - Properties, system type
12. **Unknown Objects** - Graceful handling of unsupported types

### 2.4 Comparison Requirements

**For SAIL Code Objects** (Interface, Expression Rule, Integration, Web API):
- Side-by-side diff view
- Syntax highlighting
- Line-by-line comparison

**For Process Models**:
- Node differences (added/removed/modified)
- Flow differences
- Mermaid diagram visualization
- Complexity metrics

**For Data Objects** (Record Type, CDT):
- Field differences (added/removed/modified)
- Relationship changes
- Type changes

**For Constants**:
- Value differences
- Type changes
- Scope changes

### 2.5 Data Integrity Requirements

**CRITICAL CONSTRAINTS:**

1. **No Duplicate Objects**: Each UUID appears exactly once in `object_lookup`
2. **Delta-Driven Working Set**: `changes` table contains ONLY delta objects
3. **Package-Agnostic Lookup**: `object_lookup` has NO `package_id` column
4. **Referential Integrity**: All foreign keys properly enforced
5. **Atomic Operations**: Package extraction is transactional
6. **Idempotent Comparisons**: Re-running comparison produces same results

---

## 3. Current State Analysis

### 3.1 Problems in Current Implementation

**Problem 1: Data Duplication**
```
Current: Interface X stored 3 times (once per package)
- interfaces table: 3 rows with same UUID
- object_lookup: 3 rows with same UUID
Result: Inconsistent data, wasted storage, comparison errors
```

**Problem 2: Wrong References**
```
Current: Change references object_uuid directly
- No link to object_lookup
- Duplicate object_uuid, object_name, object_type in changes table
- Cannot track object across packages
```

**Problem 3: Blueprint Dependency**
```
Current: Relies on BlueprintGenerationService (deprecated)
- In-memory dictionaries
- No persistent storage
- Cannot resume interrupted sessions
```

**Problem 4: Customer-Only in Working Set**
```
Current: Working set includes customer-only changes
- Violates delta-driven principle
- Confuses users
- Not relevant to merge decision
```

**Problem 5: Incomplete Extraction**
```
Current: Parsers miss critical data
- Process model nodes incomplete
- Record type relationships missing
- Connected system properties not extracted
```

### 3.2 Files to Remove/Deprecate

**Services:**
- `services/merge_assistant/blueprint_generation_service.py` ❌
- Old `three_way_merge_service.py` (current version) ❌

**Models:**
- `AppianObject` model ❌ (already removed)
- Old `ObjectLookup` with `package_id` ❌

**Logic:**
- `CUSTOMER_ONLY` classification ❌
- `REMOVED_BUT_CUSTOMIZED` classification ❌
- Customer-only statistics ❌

---

## 4. Target Architecture

### 4.1 Architecture Principles

**Clean Architecture Layers:**
```
┌─────────────────────────────────────┐
│         Controllers                  │  ← HTTP endpoints
├─────────────────────────────────────┤
│         Services                     │  ← Business logic
├─────────────────────────────────────┤
│         Repositories                 │  ← Data access
├─────────────────────────────────────┤
│         Models (SQLAlchemy)          │  ← Database schema
└─────────────────────────────────────┘
```

**Design Patterns:**
- **Repository Pattern**: All database access through repositories
- **Service Layer**: Business logic in services
- **Factory Pattern**: Object creation (parsers, comparators)
- **Strategy Pattern**: Pluggable comparison algorithms
- **Dependency Injection**: Services receive dependencies via constructor

**SOLID Principles:**
- **S**ingle Responsibility: Each class has one reason to change
- **O**pen/Closed: Open for extension, closed for modification
- **L**iskov Substitution: Subtypes must be substitutable
- **I**nterface Segregation: Many specific interfaces > one general
- **D**ependency Inversion: Depend on abstractions, not concretions

### 4.2 High-Level Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    MergeAssistantController                   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                  ThreeWayMergeOrchestrator                    │
│  - Coordinates entire workflow                                │
│  - Manages session lifecycle                                  │
│  - Handles errors and rollback                                │
└────┬────────┬────────┬────────┬────────┬──────────┬──────────┘
     │        │        │        │        │          │
     ▼        ▼        ▼        ▼        ▼          ▼
┌─────────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌────────┐ ┌──────────┐
│Package  │ │Delta │ │Cust  │ │Class │ │Merge   │ │Report    │
│Extract  │ │Comp  │ │Comp  │ │ify   │ │Guidance│ │Generator │
│Service  │ │Svc   │ │Svc   │ │Svc   │ │Service │ │Service   │
└────┬────┘ └───┬──┘ └───┬──┘ └───┬──┘ └────┬───┘ └─────┬────┘
     │          │        │        │         │           │
     ▼          ▼        ▼        ▼         ▼           ▼
┌──────────────────────────────────────────────────────────────┐
│                      Repositories                             │
│  - ObjectLookupRepository                                     │
│  - PackageObjectMappingRepository                             │
│  - DeltaComparisonRepository                                  │
│  - ChangeRepository                                           │
│  - Object-specific repositories (Interface, ProcessModel...)  │
└──────────────────────────────────────────────────────────────┘
```

### 4.3 Service Responsibilities

**ThreeWayMergeOrchestrator**
- Entry point for merge workflow
- Creates merge session
- Coordinates all sub-services
- Handles transactions and rollback
- Updates session status

**PackageExtractionService**
- Extracts ZIP files
- Parses XML objects using parsers
- Stores in object_lookup (find_or_create)
- Creates package_object_mappings
- Stores object-specific data

**DeltaComparisonService**
- Compares Package A → Package C
- Identifies NEW, MODIFIED, DEPRECATED
- Stores results in delta_comparison_results
- Uses version + content comparison

**CustomerComparisonService**
- Compares delta objects against Package B
- Identifies customer modifications
- Prepares data for classification

**ClassificationService**
- Applies 7 classification rules
- Creates Change records
- Links to object_lookup
- Sets display_order

**MergeGuidanceService**
- Generates recommendations
- Identifies conflicts
- Creates MergeGuidance records
- Analyzes dependencies

**ReportGeneratorService**
- Exports comparison results
- Generates Excel reports
- Creates summary statistics

---

*Continued in next section...*
