# Three-Way Merge Architecture Specification

**Complete documentation for rebuilding the three-way merge functionality**

---

## 📚 Documentation Index

### 1. Executive Summary
**File**: `three-way-merge-executive-summary.md`

**Purpose**: High-level overview for stakeholders and decision makers

**Contents**:
- Problem statement
- Solution approach
- Key design decisions
- Success criteria
- Timeline overview

**Read this first** to understand the big picture.

---

### 2. Database Schema
**File**: `three-way-merge-database-schema.md`

**Purpose**: Complete database design specification

**Contents**:
- Core tables (object_lookup, package_object_mappings, delta_comparison_results, changes)
- Object-specific tables (interfaces, process_models, record_types, etc.)
- Comparison result tables
- Validation queries
- Migration strategy

**Read this** when implementing database changes.

---

### 3. Service Layer Design
**File**: `three-way-merge-service-design.md`

**Purpose**: Service architecture and business logic

**Contents**:
- Service hierarchy
- Service responsibilities
- Interface definitions
- Workflow implementations
- Parser design
- Comparison strategies

**Read this** when implementing services.

---

### 4. Implementation Plan
**File**: `three-way-merge-implementation-plan.md`

**Purpose**: Step-by-step implementation guide

**Contents**:
- 10 implementation phases
- Detailed tasks for each phase
- Testing strategy
- Code examples
- Success criteria

**Read this** when starting implementation.

---

### 5. Architecture Diagrams
**File**: `three-way-merge-architecture-diagrams.md`

**Purpose**: Visual representations of the architecture

**Contents**:
- System architecture diagram
- Data flow diagram
- Entity relationship diagram
- Classification rule flow
- Package extraction flow
- Design pattern diagrams

**Read this** to visualize the architecture.

---

### 6. Quick Reference Guide
**File**: `three-way-merge-quick-reference.md`

**Purpose**: Developer cheat sheet

**Contents**:
- Core concepts
- Database tables cheat sheet
- Classification rules quick reference
- Common queries
- Repository patterns
- Parser patterns
- Testing patterns
- Common pitfalls
- Debugging tips

**Keep this handy** while implementing.

---

### 7. Clean Architecture (Original)
**File**: `three-way-merge-clean-architecture.md`

**Purpose**: Original comprehensive specification

**Contents**:
- Executive summary
- Business requirements
- Current state analysis
- Target architecture
- All sections in one document

**Read this** for complete context.

---

### 8. UI & Template Specification
**Files**: 
- `three-way-merge-ui-templates.md` (Part 1: Overview & Pages)
- `three-way-merge-ui-templates-part2.md` (Part 2: Comparison Templates)
- `three-way-merge-ui-templates-part3.md` (Part 3: Styling & JavaScript)

**Purpose**: Complete UI/template documentation

**Contents**:
- Template structure and hierarchy
- Page specifications (upload, sessions, summary, change detail)
- Comparison templates for all object types
- Component library (badges, icons, progress bars, diff viewers)
- Styling guidelines (colors, typography, cards, buttons)
- JavaScript interactions (file upload, navigation, review actions)
- Data binding specifications

**Read this** when implementing UI/templates.

---

## 🎯 Quick Start Guide

### For Project Managers
1. Read: **Executive Summary**
2. Review: **Implementation Plan** (timeline and phases)
3. Monitor: Success criteria and milestones

### For Architects
1. Read: **Executive Summary**
2. Study: **Database Schema**
3. Review: **Service Layer Design**
4. Examine: **Architecture Diagrams**

### For Developers
1. Read: **Executive Summary** (overview)
2. Study: **Quick Reference Guide** (keep handy)
3. Follow: **Implementation Plan** (step-by-step)
4. Reference: **Database Schema** and **Service Layer Design** as needed
5. Use: **Architecture Diagrams** for visualization
6. Implement: **UI & Template Specification** for frontend work

### For Testers
1. Read: **Executive Summary** (understand goals)
2. Study: **Implementation Plan** (testing strategy section)
3. Reference: **Quick Reference Guide** (validation queries)

---

## 🔑 Key Concepts

### The Three Packages
- **Package A**: Vendor Base Version (original)
- **Package B**: Customer Customized Version (with customer changes)
- **Package C**: Vendor New Version (latest from vendor)

### The Delta
**Delta = A→C comparison**

Identifies what changed in the vendor package:
- NEW: Objects added in C
- MODIFIED: Objects changed in C
- DEPRECATED: Objects removed in C

### The Working Set
**Working Set = Delta objects classified against B**

Only contains objects from the delta, classified as:
- NO_CONFLICT: Can be auto-merged
- CONFLICT: Requires manual review
- NEW: New vendor object to add
- DELETED: Object removed by customer

### Core Principles
1. **No Duplication**: Each object stored once in object_lookup
2. **Package-Agnostic**: object_lookup has NO package_id
3. **Delta-Driven**: Working set contains only delta objects
4. **Explicit Mapping**: package_object_mappings tracks membership
5. **Persistent Storage**: All comparisons stored in database

---

## 📊 Architecture Overview

```
User uploads 3 packages (A, B, C)
   ↓
Extract packages → object_lookup (no duplicates)
   ↓
Delta comparison (A→C) → delta_comparison_results
   ↓
Customer comparison (delta vs B)
   ↓
Classification (7 rules) → changes (working set)
   ↓
Merge guidance → recommendations
   ↓
User reviews and makes decisions
```

---

## 🗄️ Database Tables

### Core Tables
- `object_lookup` - Global object registry (NO package_id!)
- `package_object_mappings` - Track object-package membership
- `delta_comparison_results` - Store A→C comparison
- `changes` - Working set for user review

### Object Tables
- `interfaces`, `expression_rules`, `process_models`, `record_types`, `cdts`, etc.
- Each references `object_lookup.id`

### Comparison Tables
- `interface_comparisons`, `process_model_comparisons`, etc.
- Store detailed comparison results

---

## 🎨 Design Patterns

- **Repository Pattern**: All database access through repositories
- **Service Layer**: Business logic in services
- **Factory Pattern**: Object creation (parsers, comparators)
- **Strategy Pattern**: Pluggable comparison algorithms
- **Dependency Injection**: Services receive dependencies via constructor

---

## ✅ Success Criteria

1. **Zero Data Duplication**: Each UUID appears exactly once in object_lookup
2. **100% Rule Coverage**: All 7 classification rules implemented
3. **Delta-Driven**: Working set contains only delta objects
4. **Performance**: All queries < 200ms
5. **Test Coverage**: >80% for all new code
6. **Zero Deprecated Code**: All deprecated services removed

---

## 📅 Implementation Timeline

**Total: 19 Days**

- **Phase 1**: Database Schema (Days 1-2)
- **Phase 2**: Domain Models (Day 3)
- **Phase 3**: Repository Layer (Days 4-5)
- **Phase 4**: Parser Layer (Days 6-7)
- **Phase 5**: Service Layer (Days 8-10)
- **Phase 6**: Integration Testing (Days 11-12)
- **Phase 7**: Controller and UI (Days 13-14)
- **Phase 8**: Performance (Days 15-16)
- **Phase 9**: Documentation (Day 17)
- **Phase 10**: Deployment (Days 18-19)

---

## 🧪 Test Packages

**Location**: `applicationArtifacts/Three Way Testing Files/V2/`

1. Test Application - Base Version.zip (Package A)
2. Test Application Customer Version.zip (Package B)
3. Test Application Vendor New Version.zip (Package C)

**Contents**: ~27 objects each including process models, record types, interfaces, etc.

---

## 🚨 Critical Reminders

1. **NO package_id in object_lookup** - It's global!
2. **NO duplicate objects** - Use `find_or_create()`
3. **NO customer-only in working set** - Only delta objects
4. **NO old classifications** - Only 4 types: NO_CONFLICT, CONFLICT, NEW, DELETED
5. **ALL tests use real packages** - No mocks for integration tests
6. **ALL 7 rules implemented** - No shortcuts

---

## 📝 Document Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| Executive Summary | ✅ Complete | 2025-11-30 |
| Database Schema | ✅ Complete | 2025-11-30 |
| Service Design | ✅ Complete | 2025-11-30 |
| Implementation Plan | ✅ Complete | 2025-11-30 |
| Architecture Diagrams | ✅ Complete | 2025-11-30 |
| Quick Reference | ✅ Complete | 2025-11-30 |
| Clean Architecture | ✅ Complete | 2025-11-30 |
| UI & Template Spec | ✅ Complete | 2025-11-30 |

---

## 🔗 Related Documents

- **Development Log**: `.kiro/DEVELOPMENT_LOG.md`
- **Application Context**: `.kiro/steering/nexusgen-application-context.md`
- **Test Fixtures**: `tests/fixtures/test_fixtures.py`
- **Models**: `models.py`

---

## 📞 Support

For questions or clarifications:
1. Review the appropriate specification document
2. Check the Quick Reference Guide
3. Consult the Development Log
4. Refer to existing code examples

---

## 🎯 Next Steps

1. **Review** all specification documents
2. **Approve** the architecture
3. **Set up** development environment
4. **Start** Phase 1: Database Schema
5. **Follow** implementation plan strictly
6. **Test** at each phase
7. **Deploy** when all criteria met

---

**Status**: Ready for Implementation  
**Version**: 1.0  
**Date**: 2025-11-30

---

*This specification provides everything needed to rebuild the three-way merge functionality from scratch with proper architecture, no data duplication, and clean OOP design.*
