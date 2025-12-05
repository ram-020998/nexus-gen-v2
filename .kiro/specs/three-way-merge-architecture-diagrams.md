# Three-Way Merge Architecture Diagrams

**Visual representations of the architecture**

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│  (Upload packages, view comparisons, make merge decisions)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONTROLLER LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  MergeAssistantController                                 │  │
│  │  - POST /merge/create                                     │  │
│  │  - GET /merge/<ref_id>/summary                            │  │
│  │  - GET /merge/<ref_id>/changes                            │  │
│  │  - GET /merge/<ref_id>/object/<obj_id>                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ThreeWayMergeOrchestrator (Main Coordinator)            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  1. PackageExtractionService                       │  │  │
│  │  │     - Extract ZIP files                            │  │  │
│  │  │     - Parse XML objects                            │  │  │
│  │  │     - Store in database                            │  │  │
│  │  │                                                     │  │  │
│  │  │  2. DeltaComparisonService                         │  │  │
│  │  │     - Compare A→C                                  │  │  │
│  │  │     - Identify NEW, MODIFIED, DEPRECATED           │  │  │
│  │  │                                                     │  │  │
│  │  │  3. CustomerComparisonService                      │  │  │
│  │  │     - Compare delta vs B                           │  │  │
│  │  │     - Identify customer modifications              │  │  │
│  │  │                                                     │  │  │
│  │  │  4. ClassificationService                          │  │  │
│  │  │     - Apply 7 classification rules                 │  │  │
│  │  │     - Create Change records                        │  │  │
│  │  │                                                     │  │  │
│  │  │  5. MergeGuidanceService                           │  │  │
│  │  │     - Generate recommendations                     │  │  │
│  │  │     - Identify conflicts                           │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   REPOSITORY LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  - ObjectLookupRepository                                 │  │
│  │  - PackageObjectMappingRepository                         │  │
│  │  - DeltaComparisonRepository                              │  │
│  │  - ChangeRepository                                       │  │
│  │  - InterfaceRepository                                    │  │
│  │  - ProcessModelRepository                                 │  │
│  │  - ... (other object repositories)                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Core Tables:                                             │  │
│  │  - object_lookup (global registry)                        │  │
│  │  - package_object_mappings                                │  │
│  │  - delta_comparison_results                               │  │
│  │  - changes (working set)                                  │  │
│  │                                                            │  │
│  │  Object Tables:                                            │  │
│  │  - interfaces, expression_rules, process_models, etc.     │  │
│  │                                                            │  │
│  │  Comparison Tables:                                        │  │
│  │  - interface_comparisons, process_model_comparisons, etc. │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Package A  │  │  Package B  │  │  Package C  │
│   (Base)    │  │ (Customer)  │  │ (New Vendor)│
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┴────────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │  PackageExtractionService    │
         │  - Extract ZIP               │
         │  - Parse XML                 │
         │  - find_or_create objects    │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │     object_lookup            │
         │  (Global Object Registry)    │
         │  - NO duplicates             │
         │  - NO package_id             │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │  package_object_mappings     │
         │  - Track membership          │
         │  - Many-to-many              │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │  DeltaComparisonService      │
         │  - Compare A→C               │
         │  - Identify changes          │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │  delta_comparison_results    │
         │  - NEW                       │
         │  - MODIFIED                  │
         │  - DEPRECATED                │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │  CustomerComparisonService   │
         │  - Compare delta vs B        │
         │  - Check modifications       │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │  ClassificationService       │
         │  - Apply 7 rules             │
         │  - Create Change records     │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │        changes               │
         │  (Working Set)               │
         │  - NO_CONFLICT               │
         │  - CONFLICT                  │
         │  - NEW                       │
         │  - DELETED                   │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │  MergeGuidanceService        │
         │  - Generate recommendations  │
         │  - Identify conflicts        │
         └──────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │      User Review             │
         │  - View comparisons          │
         │  - Make decisions            │
         └──────────────────────────────┘
```

---

## Database Entity Relationship Diagram

```
┌─────────────────────┐
│  merge_sessions     │
│  ─────────────────  │
│  id (PK)            │
│  reference_id       │
│  status             │
│  total_changes      │
└──────────┬──────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────┐
│  packages           │
│  ─────────────────  │
│  id (PK)            │
│  session_id (FK)    │
│  package_type       │
│  package_name       │
└──────────┬──────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────────────────┐
│  package_object_mappings        │
│  ─────────────────────────────  │
│  id (PK)                        │
│  package_id (FK) ────────┐      │
│  object_id (FK)          │      │
└──────────────────────────┼──────┘
                           │
                           │ N:1
                           │
                           ▼
           ┌─────────────────────────┐
           │  object_lookup          │
           │  ─────────────────────  │
           │  id (PK)                │
           │  uuid (UNIQUE)          │
           │  name                   │
           │  object_type            │
           │  NO package_id!         │
           └──────────┬──────────────┘
                      │
                      │ 1:N
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ▼             ▼             ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐
│ interfaces   │ │ process_ │ │ record_  │
│              │ │ models   │ │ types    │
│ object_id(FK)│ │ object_  │ │ object_  │
│              │ │ id (FK)  │ │ id (FK)  │
└──────────────┘ └──────────┘ └──────────┘
     ... (other object-specific tables)


┌─────────────────────┐
│  merge_sessions     │
└──────────┬──────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────────────────┐
│  delta_comparison_results       │
│  ─────────────────────────────  │
│  id (PK)                        │
│  session_id (FK)                │
│  object_id (FK) ────────────────┼──► object_lookup
│  change_category                │
│  version_changed                │
│  content_changed                │
└─────────────────────────────────┘


┌─────────────────────┐
│  merge_sessions     │
└──────────┬──────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────────────────┐
│  changes                        │
│  ─────────────────────────────  │
│  id (PK)                        │
│  session_id (FK)                │
│  object_id (FK) ────────────────┼──► object_lookup
│  classification                 │
│  vendor_change_type             │
│  customer_change_type           │
│  display_order                  │
└──────────┬──────────────────────┘
           │
           │ 1:1
           │
           ▼
┌─────────────────────────────────┐
│  merge_guidance                 │
│  ─────────────────────────────  │
│  id (PK)                        │
│  change_id (FK)                 │
│  recommendation                 │
│  reason                         │
└─────────────────────────────────┘
```

---

## Classification Rule Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Delta Comparison Result                                     │
│  (A→C comparison)                                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  Change Category?      │
        └────────┬───────────────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
     ▼           ▼           ▼
  ┌─────┐   ┌─────────┐  ┌────────────┐
  │ NEW │   │MODIFIED │  │DEPRECATED  │
  └──┬──┘   └────┬────┘  └─────┬──────┘
     │           │              │
     │           │              │
     │           ▼              │
     │    ┌──────────────┐     │
     │    │ Exists in B? │     │
     │    └──────┬───────┘     │
     │           │              │
     │      ┌────┴────┐         │
     │      │         │         │
     │      ▼         ▼         │
     │    ┌───┐    ┌────┐      │
     │    │YES│    │ NO │      │
     │    └─┬─┘    └──┬─┘      │
     │      │         │         │
     │      ▼         │         │
     │  ┌────────────┐│         │
     │  │Modified in ││         │
     │  │    B?      ││         │
     │  └──┬─────┬───┘│         │
     │     │     │    │         │
     │     ▼     ▼    │         │
     │   ┌───┐ ┌───┐ │         │
     │   │YES│ │NO │ │         │
     │   └─┬─┘ └─┬─┘ │         │
     │     │     │   │         │
     ▼     ▼     ▼   ▼         ▼
┌─────┐ ┌────────┐ ┌──────────┐ ┌────────────┐
│ NEW │ │CONFLICT│ │NO_CONFLICT│ │  DELETED   │
│     │ │        │ │           │ │            │
│Rule │ │Rule 10b│ │Rule 10a   │ │Rule 10c    │
│ 10d │ │Rule 10f│ │Rule 10e   │ │            │
└─────┘ └────────┘ └──────────┘ └────────────┘
                                 Rule 10g
```

---

## Package Extraction Flow

```
┌─────────────┐
│  ZIP File   │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│ Extract to temp  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Find XML files   │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ For each XML file:                   │
│                                      │
│  1. Detect object type               │
│  2. Get appropriate parser           │
│  3. Parse XML                        │
│  4. Extract data                     │
│     ├─ uuid                          │
│     ├─ name                          │
│     ├─ version_uuid                  │
│     ├─ SAIL code (if applicable)     │
│     └─ object-specific fields        │
│                                      │
│  5. find_or_create in object_lookup  │
│     ├─ Check if UUID exists          │
│     ├─ If exists: return existing    │
│     └─ If not: create new            │
│                                      │
│  6. Create package_object_mapping    │
│     └─ Link package to object        │
│                                      │
│  7. Store object-specific data       │
│     └─ In appropriate table          │
│        (interfaces, process_models,  │
│         record_types, etc.)          │
└──────────────────────────────────────┘
       │
       ▼
┌──────────────────┐
│ Update package   │
│ statistics       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Clean up temp    │
│ directory        │
└──────────────────┘
```

---

## Comparison Strategy Pattern

```
┌─────────────────────────────────────┐
│  ComparisonStrategy (Interface)     │
│  ─────────────────────────────────  │
│  + compare(obj_a, obj_b): bool      │
└──────────────┬──────────────────────┘
               │
               │ implements
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌──────────────┐  ┌──────────────────┐
│  Version     │  │  Content         │
│  Comparison  │  │  Comparison      │
│  Strategy    │  │  Strategy        │
│              │  │                  │
│  Compare     │  │  Compare         │
│  version     │  │  SAIL code,      │
│  UUIDs       │  │  fields,         │
│              │  │  properties      │
└──────────────┘  └──────────────────┘
```

---

## Parser Factory Pattern

```
┌─────────────────────────────────────┐
│  XMLParserFactory                   │
│  ─────────────────────────────────  │
│  + get_parser(type): BaseParser     │
└──────────────┬──────────────────────┘
               │
               │ creates
               │
       ┌───────┴────────────────────────────┐
       │                                    │
       ▼                                    ▼
┌──────────────┐                    ┌──────────────┐
│  BaseParser  │                    │  Unknown     │
│  (Abstract)  │                    │  Object      │
│              │                    │  Parser      │
│  + parse()   │                    │              │
└──────┬───────┘                    └──────────────┘
       │
       │ extends
       │
       ├─────────────────────────────────────┐
       │                                     │
       ▼                                     ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Interface   │  │  Process     │  │  Record      │
│  Parser      │  │  Model       │  │  Type        │
│              │  │  Parser      │  │  Parser      │
└──────────────┘  └──────────────┘  └──────────────┘
       ... (other parsers)
```

---

## Repository Pattern

```
┌─────────────────────────────────────┐
│  BaseRepository (Abstract)          │
│  ─────────────────────────────────  │
│  + find_by_id(id)                   │
│  + find_all()                       │
│  + create(entity)                   │
│  + update(entity)                   │
│  + delete(id)                       │
└──────────────┬──────────────────────┘
               │
               │ extends
               │
       ┌───────┴────────────────────────────┐
       │                                    │
       ▼                                    ▼
┌──────────────────────┐      ┌──────────────────────┐
│  ObjectLookup        │      │  PackageObject       │
│  Repository          │      │  Mapping             │
│                      │      │  Repository          │
│  + find_by_uuid()    │      │                      │
│  + find_or_create()  │      │  + get_objects_in_   │
│  + bulk_find_or_     │      │    package()         │
│    create()          │      │  + get_packages_for_ │
└──────────────────────┘      │    object()          │
                              └──────────────────────┘
       ... (other repositories)
```

---

## Service Dependency Graph

```
ThreeWayMergeOrchestrator
├── PackageExtractionService
│   ├── ZipExtractorService
│   ├── XMLParserFactory
│   │   └── All Parsers
│   ├── SAILCodeCleanerService
│   ├── ObjectLookupRepository
│   ├── PackageObjectMappingRepository
│   └── Object Repositories
│
├── DeltaComparisonService
│   ├── ObjectLookupRepository
│   ├── PackageObjectMappingRepository
│   ├── DeltaComparisonRepository
│   ├── ObjectVersionRepository
│   ├── VersionComparisonStrategy
│   └── ContentComparisonStrategy
│
├── CustomerComparisonService
│   ├── ObjectLookupRepository
│   ├── PackageObjectMappingRepository
│   ├── ObjectVersionRepository
│   ├── VersionComparisonStrategy
│   └── ContentComparisonStrategy
│
├── ClassificationService
│   ├── ChangeRepository
│   └── ClassificationRuleEngine
│
├── MergeGuidanceService
│   ├── MergeGuidanceRepository
│   ├── ConflictAnalyzer
│   └── RecommendationEngine
│
└── DependencyAnalysisService
    └── DependencyGraphBuilder
```

---

## Object Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│  1. Object discovered in XML file                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Parser extracts data                                     │
│     - uuid, name, version_uuid                               │
│     - SAIL code (if applicable)                              │
│     - Object-specific fields                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  3. find_or_create in object_lookup                          │
│     - Check if UUID exists                                   │
│     - If exists: return existing object                      │
│     - If not: create new object                              │
│     Result: ObjectLookup with id                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Create package_object_mapping                            │
│     - Link package_id to object_id                           │
│     - Tracks which packages contain this object              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Store object-specific data                               │
│     - In appropriate table (interfaces, process_models, etc.)│
│     - References object_id from object_lookup                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  6. Object available for comparison                          │
│     - Can be retrieved by UUID                               │
│     - Can be retrieved by package                            │
│     - Can be compared across packages                        │
└─────────────────────────────────────────────────────────────┘
```

---

*End of Architecture Diagrams*
