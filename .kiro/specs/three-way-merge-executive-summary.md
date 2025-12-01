# Three-Way Merge Rebuild - Executive Summary

**Version:** 1.0  
**Date:** 2025-11-30  
**Status:** Ready for Implementation

---

## Overview

This document provides a complete architecture specification for rebuilding the three-way merge functionality from scratch. The current implementation has fundamental flaws that require a clean slate approach.

---

## Problem Statement

### Current Issues

1. **Data Duplication**: Same objects stored multiple times across tables
2. **Inconsistent References**: Objects referenced from wrong tables/packages
3. **Blueprint Dependency**: Over-reliance on deprecated blueprint generation
4. **Poor Separation of Concerns**: Mixed responsibilities across services
5. **Incomplete Extraction**: Missing data from XML objects
6. **No Delta-Driven Workflow**: Working set includes non-delta objects

### Impact

- Incorrect comparison results
- Wasted storage
- Performance degradation
- Difficult to maintain
- Cannot resume interrupted sessions

---

## Solution Architecture

### Core Principles

1. **Global Object Registry**: Single source of truth (object_lookup table)
2. **Package-Object Mapping**: Separate table tracking membership
3. **Delta-Driven Workflow**: Only process vendor delta objects (A→C)
4. **Object-Specific Tables**: Dedicated tables for each Appian object type
5. **Comparison Result Storage**: Persistent storage of all comparisons
6. **Clean OOP Design**: Repository pattern, service layer, DI

### Key Design Decisions

**Database:**
- `object_lookup` table with NO `package_id` (package-agnostic)
- `package_object_mappings` table for membership tracking
- `delta_comparison_results` table for A→C comparison storage
- `object_versions` table for package-specific versions
- Object-specific tables reference `object_lookup.id`

**Services:**
- `ThreeWayMergeOrchestrator` - Main coordinator
- `PackageExtractionService` - Extract and parse packages
- `DeltaComparisonService` - Compare A→C
- `CustomerComparisonService` - Compare delta vs B
- `ClassificationService` - Apply 7 classification rules
- `MergeGuidanceService` - Generate recommendations

**Parsers:**
- One parser per object type
- Extract ALL data from XML
- Clean SAIL code
- Store in object-specific tables

---

## Classification Rules

The system implements **7 classification rules**:

| Rule | Condition | Classification |
|------|-----------|----------------|
| 10a | Modified in delta AND not modified in customer | NO_CONFLICT |
| 10b | Modified in delta AND modified in customer | CONFLICT |
| 10c | Modified in delta AND removed in customer | DELETED |
| 10d | New object in delta | NEW |
| 10e | Deprecated in delta AND not modified in customer | NO_CONFLICT |
| 10f | Deprecated in delta AND modified in customer | CONFLICT |
| 10g | Deprecated in delta AND removed in customer | NO_CONFLICT |

**Removed Classifications:**
- ~~CUSTOMER_ONLY~~ - Not part of working set
- ~~REMOVED_BUT_CUSTOMIZED~~ - Covered by DELETED

---

## Data Flow

```
1. User uploads 3 packages (A, B, C)
   ↓
2. PackageExtractionService extracts all packages
   - Parse XML files
   - Store in object_lookup (find_or_create)
   - Create package_object_mappings
   - Store object-specific data
   ↓
3. DeltaComparisonService compares A→C
   - Identify NEW, MODIFIED, DEPRECATED
   - Store in delta_comparison_results
   ↓
4. CustomerComparisonService compares delta vs B
   - Check if objects exist in B
   - Check if modified in B
   ↓
5. ClassificationService applies 7 rules
   - Create Change records
   - Link to object_lookup
   - Set display_order
   ↓
6. MergeGuidanceService generates recommendations
   - Analyze conflicts
   - Create MergeGuidance records
   ↓
7. User reviews working set
   - View object-specific comparisons
   - Make merge decisions
```

---

## Implementation Plan

### Timeline: 19 Days

**Phase 1: Database Schema (Days 1-2)**
- Create migration script
- Test migration
- Validate schema

**Phase 2: Domain Models (Day 3)**
- Create enums
- Create domain entities
- Create comparison strategies

**Phase 3: Repository Layer (Days 4-5)**
- Implement base repository
- Implement object repositories
- Write repository tests

**Phase 4: Parser Layer (Days 6-7)**
- Implement base parser
- Implement object-specific parsers
- Test with real XML files

**Phase 5: Service Layer (Days 8-10)**
- Implement all services
- Write service tests
- Integration testing

**Phase 6: Integration Testing (Days 11-12)**
- End-to-end tests with real packages
- Property-based tests
- Validate invariants

**Phase 7: Controller and UI (Days 13-14)**
- Update controllers
- Update templates
- Remove customer-only sections

**Phase 8: Performance (Days 15-16)**
- Optimize queries
- Add caching
- Load testing

**Phase 9: Documentation (Day 17)**
- Update README
- API documentation
- Development log

**Phase 10: Deployment (Days 18-19)**
- Run all tests
- Deploy to staging
- Deploy to production
- Remove deprecated code

---

## Success Criteria

✅ **Zero Data Duplication**: Each UUID appears exactly once in object_lookup  
✅ **100% Rule Coverage**: All 7 classification rules implemented  
✅ **Delta-Driven**: Working set contains only delta objects  
✅ **Performance**: All queries < 200ms  
✅ **Test Coverage**: >80% for all new code  
✅ **Zero Deprecated Code**: All deprecated services removed  

---

## Validation Queries

### Check for Duplicates
```sql
SELECT uuid, COUNT(*) as count 
FROM object_lookup 
GROUP BY uuid 
HAVING count > 1;
-- Should return 0 rows
```

### Verify Working Set is Delta-Driven
```sql
SELECT COUNT(*) FROM delta_comparison_results WHERE session_id = ?;
SELECT COUNT(*) FROM changes WHERE session_id = ?;
-- Should be equal
```

### Verify Package Mappings
```sql
SELECT ol.uuid, ol.name, ol.object_type
FROM object_lookup ol
JOIN package_object_mappings pom ON ol.id = pom.object_id
WHERE pom.package_id = ?;
```

---

## Test Packages

**Location**: `applicationArtifacts/Three Way Testing Files/V2/`

1. **Test Application - Base Version.zip** (Package A)
2. **Test Application Customer Version.zip** (Package B)
3. **Test Application Vendor New Version.zip** (Package C)

**Contents**: ~27 objects each
- 2 Groups
- 3 CDTs
- 1 Data Store
- 14 Content objects (Constants, Expression Rules, Interfaces)
- 1 Process Model Folder
- 2 Process Models
- 1 Record Type

**Known Test UUIDs**:
```python
PROCESS_MODEL_UUID_1 = "de199b3f-b072-4438-9508-3b6594827eaf"
PROCESS_MODEL_UUID_2 = "2c8de7e9-23b9-40d6-afc2-233a963832be"
RECORD_TYPE_UUID = "57318b79-0bfd-45c4-a07e-ceae8277e0fb"
```

---

## Documentation Structure

1. **three-way-merge-clean-architecture.md** - Overview and business requirements
2. **three-way-merge-database-schema.md** - Complete database schema
3. **three-way-merge-service-design.md** - Service layer design
4. **three-way-merge-implementation-plan.md** - Implementation plan and testing
5. **three-way-merge-executive-summary.md** - This document

---

## Next Steps

1. **Review** this architecture with team
2. **Approve** the approach
3. **Start** Phase 1: Database Schema
4. **Follow** implementation plan strictly
5. **Test** at each phase
6. **Deploy** when all criteria met

---

## Critical Reminders

1. **NO package_id in object_lookup** - It's global!
2. **NO duplicate objects** - Use `find_or_create()`
3. **NO customer-only in working set** - Only delta objects
4. **NO old classifications** - Only 4 types: NO_CONFLICT, CONFLICT, NEW, DELETED
5. **ALL tests use real packages** - No mocks for integration tests
6. **ALL 7 rules implemented** - No shortcuts

---

## Contact

For questions or clarifications, refer to:
- Architecture documents in `.kiro/specs/`
- Development log in `.kiro/DEVELOPMENT_LOG.md`
- Test fixtures in `tests/fixtures/test_fixtures.py`

---

**Status**: Ready for implementation  
**Approval**: Pending  
**Start Date**: TBD

---

*End of Executive Summary*
