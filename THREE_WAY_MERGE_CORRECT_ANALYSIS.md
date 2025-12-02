# Three-Way Merge - Correct Design Analysis

**Date:** December 2, 2025  
**Issue:** Customer-only changes are not being analyzed  
**Impact:** Critical - Customer modifications are lost in merge analysis  
**Status:** Requires service layer refactoring

---

## Executive Summary

The current three-way merge implementation has a **critical flaw**: it only analyzes objects that the vendor changed (Set D), completely missing objects that only the customer changed (Set E). This results in **data loss** where customer-only modifications are never included in the working set.

**The core issue:** The customer comparison service only checks objects that are in the vendor delta, instead of performing a full comparison to identify all customer changes.

**Package Labels (CORRECT in current code):**
- Package A = Base vendor version
- Package B = Customer version  
- Package C = Latest vendor version

**Required Comparisons:**
- D = A → C (vendor changes)
- E = A → B (customer changes)

**Classification Logic:**
- Object in D ∩ E → CONFLICT
- Object in D \ E → NO_CONFLICT (vendor-only)
- Object in E \ D → NO_CONFLICT (customer-only)
- Object in A but not in C, and exists in B/E → DELETED

---

## Table of Contents

1. [Package Definitions (Current Code)](#1-package-definitions-current-code)
2. [The Correct Design](#2-the-correct-design)
3. [Current Implementation Analysis](#3-current-implementation-analysis)
4. [The Problem Explained](#4-the-problem-explained)
5. [Detailed Code Analysis](#5-detailed-code-analysis)
6. [The Fix Implementation](#6-the-fix-implementation)
7. [Testing Strategy](#7-testing-strategy)
8. [Migration Plan](#8-migration-plan)

---

## 1. Package Definitions (Current Code)

### 1.1 Package Labels in Code

The current code uses these labels, which are **CORRECT**:

```python
Package A = Base vendor version (base_zip_path)
Package B = Customer version (customized_zip_path)
Package C = Latest vendor version (new_vendor_zip_path)
```

**Database package_type values:**
- `'base'` → Package A (Base vendor version)
- `'customized'` → Package B (Customer version)
- `'new_vendor'` → Package C (Latest vendor version)

### 1.2 Visual Representation

```
         Package A
      (Base Vendor)
            |
            |
      ┌─────┴─────┐
      |           |
      v           v
 Package C    Package B
(New Vendor) (Customer)
      |           |
      |           |
      v           v
   Set D       Set E
(A→C Δ)     (A→B Δ)
```

### 1.3 Comparison Sets

**Set D (Vendor Changes):**
- Compare Package A → Package C
- Identifies what the vendor changed from base to new version
- Includes: NEW, MODIFIED, DEPRECATED objects

**Set E (Customer Changes):**
- Compare Package A → Package B
- Identifies what the customer changed from base to their version
- Includes: NEW, MODIFIED, DEPRECATED objects

---

## 2. The Correct Design

### 2.1 Comparison Logic

**Step 1: Vendor Comparison (A → C)**
```python
# Compare base package (A) with new vendor package (C)
vendor_changes = compare_packages(package_a, package_c)

# This produces Set D containing:
# - NEW: Objects in C but not in A (vendor added)
# - MODIFIED: Objects in both A and C with differences (vendor modified)
# - DEPRECATED: Objects in A but not in C (vendor removed)
```

**Step 2: Customer Comparison (A → B)**
```python
# Compare base package (A) with customer package (B)
customer_changes = compare_packages(package_a, package_b)

# This produces Set E containing:
# - NEW: Objects in B but not in A (customer added)
# - MODIFIED: Objects in both A and B with differences (customer modified)
# - DEPRECATED: Objects in A but not in B (customer removed)
```

**Step 3: Set-Based Classification**
```python
# Build sets of object IDs
D = {obj.object_id for obj in vendor_changes}
E = {obj.object_id for obj in customer_changes}

# Classify each object
for object_id in (D | E):  # Union of both sets
    if object_id in D and object_id in E:
        # Both parties modified the same object
        classification = CONFLICT
    
    elif object_id in D and object_id not in E:
        # Only vendor changed this object
        classification = NO_CONFLICT (vendor-only)
    
    elif object_id not in D and object_id in E:
        # Only customer changed this object
        classification = NO_CONFLICT (customer-only)
```

### 2.2 Classification Rules

| Condition | Classification | Meaning | Action |
|-----------|---------------|---------|--------|
| Object in D ∩ E | CONFLICT | Both parties modified | Manual review required |
| Object in D \ E | NO_CONFLICT | Vendor-only change | Auto-merge vendor version |
| Object in E \ D | NO_CONFLICT | Customer-only change | Keep customer version |
| Object in A, not in C, exists in E | DELETED | Vendor deleted, customer modified | Special conflict |

### 2.3 Example Scenarios

#### Scenario 1: Conflict (Object in D ∩ E)

**Object:** `AS_GSS_CRD_mainEvaluationFactorDetailsForSummary`

```
Package A (Base):     version 1.0, content X
Package B (Customer): version 1.5, content Y (customer modified)
Package C (Vendor):   version 2.0, content Z (vendor modified)

Analysis:
- A→C comparison: MODIFIED (1.0 → 2.0) → Object in Set D ✓
- A→B comparison: MODIFIED (1.0 → 1.5) → Object in Set E ✓
- Classification: Object in D ∩ E → CONFLICT ✓

Explanation: Both vendor and customer independently modified the same object.
Manual review needed to merge both changes.
```

#### Scenario 2: Vendor-Only Change (Object in D \ E)

**Object:** `VendorNewInterface`

```
Package A (Base):     Does not exist
Package B (Customer): Does not exist
Package C (Vendor):   Exists (vendor added it)

Analysis:
- A→C comparison: NEW → Object in Set D ✓
- A→B comparison: Not found → Object NOT in Set E ✓
- Classification: Object in D \ E → NO_CONFLICT (vendor-only) ✓

Explanation: Only vendor added this object. Customer didn't touch it.
Auto-merge: Include vendor's new object.
```

#### Scenario 3: Customer-Only Change (Object in E \ D) ⚠️ CRITICAL

**Object:** `CustomerCustomInterface`

```
Package A (Base):     Does not exist
Package B (Customer): Exists (customer added it)
Package C (Vendor):   Does not exist

Analysis:
- A→C comparison: Not found → Object NOT in Set D ✓
- A→B comparison: NEW → Object in Set E ✓
- Classification: Object in E \ D → NO_CONFLICT (customer-only) ✓

Explanation: Only customer added this object. Vendor didn't touch it.
Auto-merge: Keep customer's object.

⚠️ CURRENT BUG: This object is NEVER ANALYZED because customer comparison
only checks objects in Set D (vendor delta). Since this object is not in D,
it's completely missed!
```

#### Scenario 4: Vendor Deleted, Customer Modified (DELETED)

**Object:** `DeprecatedInterface`

```
Package A (Base):     Exists, version 1.0
Package B (Customer): Exists, version 1.5 (customer modified)
Package C (Vendor):   Does not exist (vendor removed)

Analysis:
- A→C comparison: DEPRECATED → Object in Set D ✓
- A→B comparison: MODIFIED → Object in Set E ✓
- Classification: Object in D ∩ E, vendor=DEPRECATED, customer=MODIFIED → DELETED ✓

Explanation: Vendor removed the object, but customer modified it.
This is a special conflict requiring manual review.
```


---

## 3. Current Implementation Analysis

### 3.1 Current Workflow

**File:** `services/three_way_merge_orchestrator.py`

```python
# Step 2: Extract Package A (Base)
package_a = extract_package(base_zip_path, package_type='base')

# Step 3: Extract Package B (Customer)
package_b = extract_package(customized_zip_path, package_type='customized')

# Step 4: Extract Package C (New Vendor)
package_c = extract_package(new_vendor_zip_path, package_type='new_vendor')

# Step 5: Perform delta comparison (A→C) ✓ CORRECT
delta_changes = delta_comparison_service.compare(
    session_id=session.id,
    base_package_id=package_a.id,      # A
    new_vendor_package_id=package_c.id # C
)
# Returns Set D (vendor changes) ✓

# Step 6: Perform customer comparison ❌ WRONG
customer_modifications = customer_comparison_service.compare(
    base_package_id=package_a.id,      # A
    customer_package_id=package_b.id,  # B
    delta_changes=delta_changes        # ❌ Only checks objects in delta!
)
# Should return Set E (all customer changes)
# Actually returns: customer modification status for objects in Set D only

# Step 7: Classify changes ❌ WRONG
classified_changes = classification_service.classify(
    session_id=session.id,
    delta_changes=delta_changes,              # Set D
    customer_modifications=customer_modifications  # NOT Set E!
)
# Only classifies objects in Set D
# Completely misses objects in E \ D (customer-only changes)
```

### 3.2 What's Wrong

#### Problem 1: Customer Comparison is Delta-Dependent

**File:** `services/customer_comparison_service.py`

```python
def compare(
    self,
    base_package_id: int,
    customer_package_id: int,
    delta_changes: List[DeltaChange]  # ❌ Takes delta as input!
) -> Dict[int, CustomerModification]:
    
    # Get customer objects
    customer_objects = get_objects_in_package(customer_package_id)
    customer_map = {obj.id: obj for obj in customer_objects}
    
    customer_modifications = {}
    
    # ❌ ONLY iterates through delta objects!
    for delta_change in delta_changes:
        object_id = delta_change.object_id
        
        # Check if this delta object exists in customer package
        if object_id in customer_map:
            # Compare A→B for this object
            version_changed, content_changed = compare_versions(...)
            customer_modifications[object_id] = CustomerModification(
                exists_in_customer=True,
                customer_modified=(version_changed or content_changed)
            )
        else:
            customer_modifications[object_id] = CustomerModification(
                exists_in_customer=False,
                customer_modified=False
            )
    
    return customer_modifications
```

**The Problem:**
- Only checks objects that are in `delta_changes` (Set D)
- Never looks at objects that are ONLY in customer package
- Customer-only changes (E \ D) are completely ignored

**What it should do:**
```python
def compare(
    self,
    session_id: int,
    base_package_id: int,
    customer_package_id: int
    # ❌ Remove delta_changes parameter!
) -> List[CustomerChange]:
    
    # Get objects in both packages
    base_objects = get_objects_in_package(base_package_id)
    customer_objects = get_objects_in_package(customer_package_id)
    
    # Create lookup maps
    base_map = {obj.uuid: obj for obj in base_objects}
    customer_map = {obj.uuid: obj for obj in customer_objects}
    
    customer_changes = []
    
    # Find NEW objects (in B, not in A)
    for uuid, obj in customer_map.items():
        if uuid not in base_map:
            customer_changes.append(CustomerChange(
                object_id=obj.id,
                change_category=ChangeCategory.NEW,
                ...
            ))
    
    # Find DEPRECATED objects (in A, not in B)
    for uuid, obj in base_map.items():
        if uuid not in customer_map:
            customer_changes.append(CustomerChange(
                object_id=obj.id,
                change_category=ChangeCategory.DEPRECATED,
                ...
            ))
    
    # Find MODIFIED objects (in both A and B with differences)
    common_uuids = set(base_map.keys()) & set(customer_map.keys())
    for uuid in common_uuids:
        version_changed, content_changed = compare_versions(...)
        if content_changed:
            customer_changes.append(CustomerChange(
                object_id=base_map[uuid].id,
                change_category=ChangeCategory.MODIFIED,
                ...
            ))
    
    return customer_changes  # Complete Set E
```

#### Problem 2: Classification is Delta-Centric

**File:** `services/classification_service.py`

```python
def classify(
    self,
    session_id: int,
    delta_changes: List[DeltaChange],  # Set D
    customer_modifications: Dict[int, CustomerModification]  # NOT Set E!
) -> List[ClassifiedChange]:
    
    classified_changes = []
    
    # ❌ Only iterates through delta objects!
    for delta_change in delta_changes:
        object_id = delta_change.object_id
        
        # Get customer modification status for this object
        customer_mod = customer_modifications.get(object_id)
        
        # Apply classification rules
        classification = self.rule_engine.classify(
            delta_change,
            customer_mod
        )
        
        classified_changes.append(ClassifiedChange(...))
    
    return classified_changes
```

**The Problem:**
- Only classifies objects in `delta_changes` (Set D)
- Never sees objects that are only in customer changes (E \ D)
- Customer-only changes are never added to working set

**What it should do:**
```python
def classify(
    self,
    session_id: int,
    vendor_changes: List[VendorChange],    # Set D
    customer_changes: List[CustomerChange]  # Set E
) -> List[ClassifiedChange]:
    
    # Build sets of object IDs
    vendor_set = {change.object_id for change in vendor_changes}
    customer_set = {change.object_id for change in customer_changes}
    
    # Get all objects (union)
    all_objects = vendor_set | customer_set
    
    # Build lookup maps
    vendor_map = {change.object_id: change for change in vendor_changes}
    customer_map = {change.object_id: change for change in customer_changes}
    
    classified_changes = []
    
    # Classify each object in the union
    for object_id in all_objects:
        in_vendor = object_id in vendor_set
        in_customer = object_id in customer_set
        
        if in_vendor and in_customer:
            # Both parties modified → CONFLICT
            classification = Classification.CONFLICT
        elif in_vendor:
            # Vendor only → NO_CONFLICT
            classification = Classification.NO_CONFLICT
        elif in_customer:
            # Customer only → NO_CONFLICT
            classification = Classification.NO_CONFLICT
        
        classified_changes.append(ClassifiedChange(...))
    
    return classified_changes
```


### 3.3 Impact of Current Bug

#### Missing Data Example

Let's say we have these objects:

| Object | In A (Base) | In B (Customer) | In C (Vendor) | Should Be In Working Set? |
|--------|-------------|-----------------|---------------|---------------------------|
| `Obj1` | ✓ v1.0 | ✓ v1.5 (modified) | ✓ v2.0 (modified) | ✓ YES (CONFLICT) |
| `Obj2` | ✓ v1.0 | ✓ v1.0 (unchanged) | ✓ v2.0 (modified) | ✓ YES (NO_CONFLICT, vendor-only) |
| `Obj3` | ✓ v1.0 | ✓ v1.5 (modified) | ✓ v1.0 (unchanged) | ✓ YES (NO_CONFLICT, customer-only) |
| `Obj4` | ✗ | ✓ (customer added) | ✗ | ✓ YES (NO_CONFLICT, customer-only) |
| `Obj5` | ✗ | ✗ | ✓ (vendor added) | ✓ YES (NO_CONFLICT, vendor-only) |

**Current System Results:**

| Object | In Set D (A→C)? | Analyzed? | Classification | Correct? |
|--------|-----------------|-----------|----------------|----------|
| `Obj1` | ✓ MODIFIED | ✓ YES | CONFLICT | ✓ Correct |
| `Obj2` | ✓ MODIFIED | ✓ YES | NO_CONFLICT | ✓ Correct |
| `Obj3` | ✗ (not in D) | ❌ **NO** | **MISSING** | ❌ **WRONG!** |
| `Obj4` | ✗ (not in D) | ❌ **NO** | **MISSING** | ❌ **WRONG!** |
| `Obj5` | ✓ NEW | ✓ YES | NO_CONFLICT | ✓ Correct |

**Result:**
- Objects 3 and 4 are **completely missing** from the working set
- Customer-only changes are **lost**
- User has no visibility into what the customer changed

#### Real-World Impact

**Scenario:** Customer added 50 custom interfaces for their specific business logic.

**Current System:**
- These 50 interfaces are **never analyzed**
- They don't appear in the working set
- User doesn't know they exist
- During merge, these interfaces might be **accidentally lost**

**Correct System:**
- All 50 interfaces are identified in Set E
- Classified as NO_CONFLICT (customer-only)
- Appear in working set with clear indication: "Customer added, vendor didn't touch"
- User can review and ensure they're preserved in the merge

---

## 4. The Problem Explained

### 4.1 Root Cause

The fundamental issue is that the current implementation treats vendor changes as **primary** and customer changes as **secondary**.

**Current (Wrong) Approach:**
```
1. Find all vendor changes (Set D) ✓
2. For each vendor change, check if customer also changed it ✓
3. Classify based on vendor change + customer status ✓
4. Done ❌ (missed customer-only changes!)
```

**Correct Approach:**
```
1. Find all vendor changes (Set D) ✓
2. Find all customer changes (Set E) ✓
3. For each object in D ∪ E, classify based on set membership ✓
4. Done ✓ (includes all changes from both parties)
```

### 4.2 Why This Happened

The original design likely assumed:
- "We only care about vendor changes (the delta)"
- "Customer changes are only relevant if they conflict with vendor changes"
- "If customer changed something the vendor didn't touch, it's not part of the merge"

**This assumption is WRONG because:**
- Customer-only changes ARE part of the merge
- They need to be preserved in the final merged version
- User needs visibility into ALL changes, not just conflicts

### 4.3 Asymmetry Problem

**Current System:**

| Comparison | Scope | Result |
|------------|-------|--------|
| Vendor (A→C) | **FULL** comparison | Complete Set D |
| Customer (A→B) | **PARTIAL** (only delta objects) | Incomplete Set E |

This asymmetry is the core problem!

**Correct System:**

| Comparison | Scope | Result |
|------------|-------|--------|
| Vendor (A→C) | **FULL** comparison | Complete Set D |
| Customer (A→B) | **FULL** comparison | Complete Set E |

Both comparisons should be **symmetric** and **complete**.

### 4.4 Conceptual Misunderstanding

The current code seems to think:

> "Three-way merge means: take the vendor delta, and check if customer conflicts with it"

**This is wrong!** Three-way merge actually means:

> "Three-way merge means: compare both parties' changes against the common base, then find conflicts where both parties changed the same thing"

The difference is subtle but critical:
- **Wrong:** Delta-centric (vendor changes are primary)
- **Right:** Set-based (both parties' changes are equal)


---

## 5. Detailed Code Analysis

### 5.1 Delta Comparison Service (CORRECT)

**File:** `services/delta_comparison_service.py`

**Current Implementation:**
```python
def compare(
    self,
    session_id: int,
    base_package_id: int,
    new_vendor_package_id: int
) -> List[DeltaChange]:
    """
    Compare Package A (Base) to Package C (New Vendor).
    Returns Set D (vendor changes).
    """
    # Get objects in both packages
    base_objects = get_objects_in_package(base_package_id)      # A
    new_vendor_objects = get_objects_in_package(new_vendor_package_id)  # C
    
    # Create lookup maps
    base_map = {obj.uuid: obj for obj in base_objects}
    new_vendor_map = {obj.uuid: obj for obj in new_vendor_objects}
    
    delta_results = []
    
    # Find NEW objects (in C, not in A)
    new_objects = [
        obj for uuid, obj in new_vendor_map.items()
        if uuid not in base_map
    ]
    for obj in new_objects:
        delta_results.append({
            'change_category': ChangeCategory.NEW.value,
            'change_type': ChangeType.ADDED.value,
            ...
        })
    
    # Find DEPRECATED objects (in A, not in C)
    deprecated_objects = [
        obj for uuid, obj in base_map.items()
        if uuid not in new_vendor_map
    ]
    for obj in deprecated_objects:
        delta_results.append({
            'change_category': ChangeCategory.DEPRECATED.value,
            'change_type': ChangeType.REMOVED.value,
            ...
        })
    
    # Find MODIFIED objects (in both A and C with differences)
    common_uuids = set(base_map.keys()) & set(new_vendor_map.keys())
    for uuid in common_uuids:
        version_changed, content_changed = self._compare_versions(...)
        if content_changed:
            delta_results.append({
                'change_category': ChangeCategory.MODIFIED.value,
                'change_type': ChangeType.MODIFIED.value,
                ...
            })
    
    # Store in delta_comparison_results table
    self.delta_comparison_repo.bulk_create_results(delta_results)
    
    return domain_entities  # Set D
```

**Analysis:**
- ✅ **CORRECT:** Performs full comparison A→C
- ✅ **CORRECT:** Identifies NEW, DEPRECATED, MODIFIED
- ✅ **CORRECT:** Returns complete Set D
- ✅ **CORRECT:** Stores results in database

**No changes needed for this service!**

### 5.2 Customer Comparison Service (WRONG)

**File:** `services/customer_comparison_service.py`

**Current Implementation:**
```python
def compare(
    self,
    base_package_id: int,
    customer_package_id: int,
    delta_changes: List[DeltaChange]  # ❌ Problem starts here!
) -> Dict[int, CustomerModification]:
    """
    Compare delta objects against Package B (Customer).
    
    ❌ WRONG: Only checks objects in delta_changes!
    ✓ SHOULD: Perform full A→B comparison like delta service does.
    """
    # Get customer objects
    customer_objects = get_objects_in_package(customer_package_id)
    customer_map = {obj.id: obj for obj in customer_objects}
    
    customer_modifications = {}
    
    # ❌ CRITICAL BUG: Only iterates through delta objects!
    for delta_change in delta_changes:
        object_id = delta_change.object_id
        
        # Check if this delta object exists in customer package
        exists_in_customer = object_id in customer_map
        
        if not exists_in_customer:
            customer_modifications[object_id] = CustomerModification(
                object_id=object_id,
                exists_in_customer=False,
                customer_modified=False,
                ...
            )
        else:
            # Compare A→B for this specific object
            version_changed, content_changed = self._compare_versions(
                obj_lookup,
                base_package_id,
                customer_package_id
            )
            
            customer_modified = version_changed or content_changed
            
            customer_modifications[object_id] = CustomerModification(
                object_id=object_id,
                exists_in_customer=True,
                customer_modified=customer_modified,
                ...
            )
    
    # ❌ Returns only modification status for delta objects
    # ❌ Never looks at objects that are ONLY in customer package
    return customer_modifications
```

**Problems:**

1. **Takes `delta_changes` as parameter** - This immediately limits scope to vendor changes
2. **Only iterates delta objects** - Never discovers customer-only changes
3. **Returns Dict, not List** - Asymmetric with delta comparison
4. **Returns CustomerModification, not CustomerChange** - Different entity type
5. **No database persistence** - Doesn't store results like delta comparison does

**What it should do:**

```python
def compare(
    self,
    session_id: int,  # ✓ Add session_id
    base_package_id: int,
    customer_package_id: int
    # ✓ Remove delta_changes parameter!
) -> List[CustomerChange]:  # ✓ Return List, not Dict
    """
    Compare Package A (Base) to Package B (Customer).
    Returns Set E (customer changes).
    
    This is SYMMETRIC with delta_comparison_service.
    """
    # Get objects in both packages
    base_objects = get_objects_in_package(base_package_id)      # A
    customer_objects = get_objects_in_package(customer_package_id)  # B
    
    # Create lookup maps
    base_map = {obj.uuid: obj for obj in base_objects}
    customer_map = {obj.uuid: obj for obj in customer_objects}
    
    customer_results = []
    
    # Find NEW objects (in B, not in A)
    new_objects = [
        obj for uuid, obj in customer_map.items()
        if uuid not in base_map
    ]
    for obj in new_objects:
        customer_results.append({
            'session_id': session_id,
            'object_id': obj.id,
            'change_category': ChangeCategory.NEW.value,
            'change_type': ChangeType.ADDED.value,
            ...
        })
    
    # Find DEPRECATED objects (in A, not in B)
    deprecated_objects = [
        obj for uuid, obj in base_map.items()
        if uuid not in customer_map
    ]
    for obj in deprecated_objects:
        customer_results.append({
            'session_id': session_id,
            'object_id': obj.id,
            'change_category': ChangeCategory.DEPRECATED.value,
            'change_type': ChangeType.REMOVED.value,
            ...
        })
    
    # Find MODIFIED objects (in both A and B with differences)
    common_uuids = set(base_map.keys()) & set(customer_map.keys())
    for uuid in common_uuids:
        version_changed, content_changed = self._compare_versions(...)
        if content_changed:
            customer_results.append({
                'session_id': session_id,
                'object_id': base_map[uuid].id,
                'change_category': ChangeCategory.MODIFIED.value,
                'change_type': ChangeType.MODIFIED.value,
                ...
            })
    
    # ✓ Store in customer_comparison_results table (NEW TABLE!)
    self._bulk_create_results(customer_results)
    
    # ✓ Return domain entities (Set E)
    return [CustomerChange(**result) for result in customer_results]
```

**Key Changes:**
1. ✅ Remove `delta_changes` parameter
2. ✅ Perform full A→B comparison
3. ✅ Return `List[CustomerChange]` instead of `Dict[int, CustomerModification]`
4. ✅ Store results in new `customer_comparison_results` table
5. ✅ Make it symmetric with `delta_comparison_service`


### 5.3 Classification Service (WRONG)

**File:** `services/classification_service.py`

**Current Implementation:**
```python
class ClassificationRuleEngine:
    def classify(
        self,
        delta_change: DeltaChange,
        customer_modification: CustomerModification
    ) -> Classification:
        """
        Apply classification rules.
        
        ❌ WRONG: Only classifies objects in delta_changes
        ❌ WRONG: Uses complex rule system (10a-10g)
        ✓ SHOULD: Use simple set-based logic
        """
        delta_category = delta_change.change_category
        exists_in_customer = customer_modification.exists_in_customer
        customer_modified = customer_modification.customer_modified
        
        # Rule 10d: NEW in delta → NEW
        if delta_category == ChangeCategory.NEW:
            return Classification.NEW
        
        # Rules for MODIFIED in delta
        elif delta_category == ChangeCategory.MODIFIED:
            if not exists_in_customer:
                return Classification.DELETED  # Rule 10c
            elif customer_modified:
                return Classification.CONFLICT  # Rule 10b
            else:
                return Classification.NO_CONFLICT  # Rule 10a
        
        # Rules for DEPRECATED in delta
        elif delta_category == ChangeCategory.DEPRECATED:
            if not exists_in_customer:
                return Classification.NO_CONFLICT  # Rule 10g
            elif customer_modified:
                return Classification.CONFLICT  # Rule 10f
            else:
                return Classification.NO_CONFLICT  # Rule 10e


class ClassificationService(BaseService):
    def classify(
        self,
        session_id: int,
        delta_changes: List[DeltaChange],  # ❌ Only delta objects
        customer_modifications: Dict[int, CustomerModification]  # ❌ Not full Set E
    ) -> List[ClassifiedChange]:
        """
        Classify changes using 7 classification rules.
        
        ❌ WRONG: Only classifies objects in delta_changes
        ❌ WRONG: Never sees customer-only changes
        """
        classified_changes = []
        
        # ❌ CRITICAL BUG: Only iterates through delta objects!
        for delta_change in delta_changes:
            object_id = delta_change.object_id
            
            # Get customer modification status
            customer_mod = customer_modifications.get(object_id)
            
            # Apply classification rule
            classification = self.rule_engine.classify(
                delta_change,
                customer_mod
            )
            
            classified_changes.append(ClassifiedChange(...))
        
        # ❌ Returns only classifications for delta objects
        # ❌ Customer-only changes are never classified
        return classified_changes
```

**Problems:**

1. **Only iterates delta objects** - Never sees customer-only changes
2. **Complex rule system** - 7 rules (10a-10g) are hard to understand
3. **Delta-centric logic** - Treats vendor changes as primary
4. **Missing classifications** - No handling for customer-only NEW, MODIFIED, DEPRECATED

**What it should do:**

```python
class SetBasedClassifier:
    """
    Set-based classifier using simple logic:
    - D ∩ E → CONFLICT
    - D \ E → NO_CONFLICT (vendor-only)
    - E \ D → NO_CONFLICT (customer-only)
    """
    
    def classify(
        self,
        vendor_changes: List[VendorChange],    # Set D
        customer_changes: List[CustomerChange]  # Set E
    ) -> List[MergeAnalysis]:
        """
        Classify changes using set-based logic.
        """
        # Build sets of object IDs
        vendor_set = {change.object_id for change in vendor_changes}
        customer_set = {change.object_id for change in customer_changes}
        
        # Build lookup maps
        vendor_map = {change.object_id: change for change in vendor_changes}
        customer_map = {change.object_id: change for change in customer_changes}
        
        # Get all objects (union of both sets)
        all_objects = vendor_set | customer_set
        
        analyses = []
        
        # ✓ Classify EVERY object in the union
        for object_id in all_objects:
            in_vendor = object_id in vendor_set
            in_customer = object_id in customer_set
            
            vendor_change = vendor_map.get(object_id)
            customer_change = customer_map.get(object_id)
            
            # Determine classification
            if in_vendor and in_customer:
                # Both parties modified the same object
                # Check for special case: vendor deleted, customer modified
                if (vendor_change.change_category == ChangeCategory.DEPRECATED and
                    customer_change.change_category == ChangeCategory.MODIFIED):
                    classification = Classification.DELETED
                else:
                    classification = Classification.CONFLICT
            
            elif in_vendor:
                # Only vendor changed this object
                classification = Classification.NO_CONFLICT
            
            elif in_customer:
                # Only customer changed this object
                classification = Classification.NO_CONFLICT
            
            analyses.append(MergeAnalysis(
                object_id=object_id,
                in_vendor_changes=in_vendor,
                in_customer_changes=in_customer,
                vendor_change=vendor_change,
                customer_change=customer_change,
                classification=classification
            ))
        
        return analyses


class ClassificationService(BaseService):
    def classify(
        self,
        session_id: int,
        vendor_changes: List[VendorChange],    # ✓ Set D (complete)
        customer_changes: List[CustomerChange]  # ✓ Set E (complete)
    ) -> List[ClassifiedChange]:
        """
        Classify changes using set-based logic.
        
        ✓ CORRECT: Analyzes all objects in D ∪ E
        ✓ CORRECT: Includes customer-only changes
        """
        # Apply set-based classification
        analyses = self.classifier.classify(vendor_changes, customer_changes)
        
        # Convert to ClassifiedChange entities
        classified_changes = []
        
        for analysis in analyses:
            vendor_change_type = (
                analysis.vendor_change.change_type
                if analysis.vendor_change
                else None
            )
            
            customer_change_type = (
                analysis.customer_change.change_type
                if analysis.customer_change
                else None
            )
            
            classified_change = ClassifiedChange(
                object_id=analysis.object_id,
                classification=analysis.classification,
                vendor_change_type=vendor_change_type,
                customer_change_type=customer_change_type,
                display_order=0
            )
            
            classified_changes.append(classified_change)
        
        # Sort by priority and assign display order
        classified_changes = self._sort_by_priority(classified_changes)
        
        for i, change in enumerate(classified_changes, start=1):
            change.display_order = i
        
        # Create Change records in database
        self._create_change_records(session_id, classified_changes)
        
        return classified_changes
```

**Key Changes:**
1. ✅ Accept both `vendor_changes` and `customer_changes` as complete lists
2. ✅ Use set-based logic (D ∩ E, D \ E, E \ D)
3. ✅ Classify ALL objects in the union
4. ✅ Include customer-only changes
5. ✅ Simpler logic (no complex rules)

### 5.4 Orchestrator (NEEDS UPDATE)

**File:** `services/three_way_merge_orchestrator.py`

**Current Implementation:**
```python
# Step 5: Perform delta comparison (A→C) ✓ CORRECT
delta_changes = self.delta_comparison_service.compare(
    session_id=session.id,
    base_package_id=package_a.id,      # A
    new_vendor_package_id=package_c.id # C
)

# Step 6: Perform customer comparison ❌ WRONG
customer_modifications = self.customer_comparison_service.compare(
    base_package_id=package_a.id,      # A
    customer_package_id=package_b.id,  # B
    delta_changes=delta_changes        # ❌ Passes delta!
)

# Step 7: Classify changes ❌ WRONG
classified_changes = self.classification_service.classify(
    session_id=session.id,
    delta_changes=delta_changes,              # Set D
    customer_modifications=customer_modifications  # Not Set E!
)
```

**What it should do:**

```python
# Step 5: Perform vendor comparison (A→C) ✓ CORRECT
vendor_changes = self.delta_comparison_service.compare(
    session_id=session.id,
    base_package_id=package_a.id,      # A
    new_vendor_package_id=package_c.id # C
)
# Returns complete Set D

# Step 6: Perform customer comparison (A→B) ✓ FIXED
customer_changes = self.customer_comparison_service.compare(
    session_id=session.id,             # ✓ Add session_id
    base_package_id=package_a.id,      # A
    customer_package_id=package_b.id   # B
    # ✓ Remove delta_changes parameter!
)
# Returns complete Set E

# Step 7: Classify changes (D ∪ E) ✓ FIXED
classified_changes = self.classification_service.classify(
    session_id=session.id,
    vendor_changes=vendor_changes,     # ✓ Complete Set D
    customer_changes=customer_changes  # ✓ Complete Set E
)
# Classifies all objects in D ∪ E
```

**Key Changes:**
1. ✅ Rename `delta_changes` to `vendor_changes` for clarity
2. ✅ Add `session_id` to customer comparison
3. ✅ Remove `delta_changes` parameter from customer comparison
4. ✅ Pass both complete sets to classification service


---

## 6. The Fix Implementation

### 6.1 Overview of Changes

The fix requires changes to 3 main components:

1. **Database Schema** - Add `customer_comparison_results` table
2. **Customer Comparison Service** - Make it symmetric with delta comparison
3. **Classification Service** - Use set-based logic instead of rules
4. **Orchestrator** - Update to pass correct parameters

**Estimated Effort:** 8-10 hours

### 6.2 Phase 1: Database Schema

#### Step 1.1: Add customer_comparison_results Table

**File:** `models.py`

Add new model after `DeltaComparisonResult`:

```python
class CustomerComparisonResult(db.Model):
    """
    Stores customer comparison results (Set E: A→B comparison).
    
    This table stores ALL changes made by the customer from the base version.
    It's symmetric with delta_comparison_results (vendor changes).
    """
    __tablename__ = 'customer_comparison_results'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey('merge_sessions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    object_id = db.Column(
        db.Integer,
        db.ForeignKey('object_lookup.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    change_category = db.Column(db.String(20), nullable=False)  # NEW, MODIFIED, DEPRECATED
    change_type = db.Column(db.String(20), nullable=False)  # ADDED, MODIFIED, REMOVED
    version_changed = db.Column(db.Boolean, default=False)
    content_changed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint: one result per object per session
    __table_args__ = (
        db.UniqueConstraint('session_id', 'object_id', name='uq_customer_comparison_session_object'),
    )
    
    # Relationships
    session = db.relationship('MergeSession', backref='customer_comparison_results')
    object = db.relationship('ObjectLookup', backref='customer_comparisons')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'object_id': self.object_id,
            'change_category': self.change_category,
            'change_type': self.change_type,
            'version_changed': self.version_changed,
            'content_changed': self.content_changed,
            'created_at': self.created_at.isoformat()
        }
```

#### Step 1.2: Create Migration Script

**File:** `migrations/add_customer_comparison_results.py`

```python
"""
Migration: Add customer_comparison_results table

This migration creates the customer_comparison_results table to store
complete customer changes (Set E).
"""

from app import create_app
from models import db

def upgrade():
    """Apply migration."""
    app = create_app()
    with app.app_context():
        # Create customer_comparison_results table
        db.session.execute("""
            CREATE TABLE IF NOT EXISTS customer_comparison_results (
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
                UNIQUE (session_id, object_id)
            )
        """)
        
        # Create indexes
        db.session.execute("""
            CREATE INDEX IF NOT EXISTS ix_customer_comparison_session_id 
            ON customer_comparison_results(session_id)
        """)
        
        db.session.execute("""
            CREATE INDEX IF NOT EXISTS ix_customer_comparison_object_id 
            ON customer_comparison_results(object_id)
        """)
        
        db.session.commit()
        print("✓ Migration completed successfully")

def downgrade():
    """Rollback migration."""
    app = create_app()
    with app.app_context():
        db.session.execute("DROP TABLE IF EXISTS customer_comparison_results")
        db.session.commit()
        print("✓ Migration rolled back successfully")

if __name__ == '__main__':
    upgrade()
```

#### Step 1.3: Add Repository

**File:** `repositories/customer_comparison_repository.py` (NEW FILE)

```python
"""
Customer Comparison Repository

Handles database operations for customer comparison results.
"""

from typing import List, Dict, Any
from core.base_repository import BaseRepository
from models import db, CustomerComparisonResult


class CustomerComparisonRepository(BaseRepository):
    """Repository for customer comparison results."""
    
    def __init__(self):
        """Initialize repository."""
        super().__init__()
    
    def bulk_create_results(self, results: List[Dict[str, Any]]) -> None:
        """
        Bulk create customer comparison results.
        
        Args:
            results: List of result dictionaries
        """
        for result in results:
            record = CustomerComparisonResult(**result)
            db.session.add(record)
        
        db.session.flush()
    
    def get_by_session(self, session_id: int) -> List[CustomerComparisonResult]:
        """
        Get all customer comparison results for a session.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            List of CustomerComparisonResult entities
        """
        return db.session.query(CustomerComparisonResult).filter_by(
            session_id=session_id
        ).all()
    
    def get_statistics(self, session_id: int) -> Dict[str, Any]:
        """
        Get statistics for customer comparison results.
        
        Args:
            session_id: Merge session ID
            
        Returns:
            Dict with statistics
        """
        from sqlalchemy import func
        
        # Total count
        total = db.session.query(CustomerComparisonResult).filter_by(
            session_id=session_id
        ).count()
        
        # Count by category
        results = db.session.query(
            CustomerComparisonResult.change_category,
            func.count(CustomerComparisonResult.id).label('count')
        ).filter_by(
            session_id=session_id
        ).group_by(
            CustomerComparisonResult.change_category
        ).all()
        
        by_category = {category: count for category, count in results}
        
        return {
            'total': total,
            'by_category': by_category
        }
```

### 6.3 Phase 2: Update Domain Entities

**File:** `domain/entities.py`

Update entities to reflect correct design:

```python
from dataclasses import dataclass
from typing import Optional
from domain.enums import ChangeCategory, ChangeType, Classification


@dataclass
class VendorChange:
    """
    Represents a change in the vendor package (Set D: A→C).
    
    This represents what the vendor changed from the base version
    to the new vendor version.
    """
    object_id: int
    change_category: ChangeCategory  # NEW, MODIFIED, DEPRECATED
    change_type: ChangeType  # ADDED, MODIFIED, REMOVED
    version_changed: bool
    content_changed: bool


@dataclass
class CustomerChange:
    """
    Represents a change in the customer package (Set E: A→B).
    
    This represents what the customer changed from the base version
    to their customized version.
    """
    object_id: int
    change_category: ChangeCategory  # NEW, MODIFIED, DEPRECATED
    change_type: ChangeType  # ADDED, MODIFIED, REMOVED
    version_changed: bool
    content_changed: bool


@dataclass
class MergeAnalysis:
    """
    Represents the merge analysis result for an object.
    
    This combines vendor and customer changes to determine
    if there's a conflict.
    """
    object_id: int
    in_vendor_changes: bool  # Object in Set D
    in_customer_changes: bool  # Object in Set E
    vendor_change: Optional[VendorChange]
    customer_change: Optional[CustomerChange]
    classification: Classification
    
    @property
    def is_conflict(self) -> bool:
        """Check if this is a conflict (object in both D and E)."""
        return self.in_vendor_changes and self.in_customer_changes
    
    @property
    def is_vendor_only(self) -> bool:
        """Check if this is a vendor-only change (in D, not in E)."""
        return self.in_vendor_changes and not self.in_customer_changes
    
    @property
    def is_customer_only(self) -> bool:
        """Check if this is a customer-only change (in E, not in D)."""
        return not self.in_vendor_changes and self.in_customer_changes


# Legacy aliases for backward compatibility
DeltaChange = VendorChange  # For existing code that uses DeltaChange
```


### 6.4 Phase 3: Refactor Customer Comparison Service

**File:** `services/customer_comparison_service.py`

Complete rewrite to make it symmetric with delta comparison:

```python
"""
Customer Comparison Service

Handles comparison between Package A (Base) and Package B (Customer)
to identify customer changes (Set E).
"""

import logging
from typing import List, Dict, Any, Tuple, Optional

from core.base_service import BaseService
from models import db, ObjectLookup, ObjectVersion
from repositories.object_lookup_repository import ObjectLookupRepository
from repositories.package_object_mapping_repository import PackageObjectMappingRepository
from repositories.customer_comparison_repository import CustomerComparisonRepository
from domain.entities import CustomerChange
from domain.enums import ChangeCategory, ChangeType
from domain.comparison_strategies import (
    SimpleVersionComparisonStrategy,
    SAILCodeComparisonStrategy
)


class CustomerComparisonService(BaseService):
    """
    Service for comparing Package A (Base) to Package B (Customer).
    
    This service identifies customer changes (Set E) by comparing two packages:
    - NEW objects: In B but not in A (customer added)
    - DEPRECATED objects: In A but not in B (customer removed)
    - MODIFIED objects: In both A and B with differences (customer modified)
    
    This is SYMMETRIC with DeltaComparisonService (vendor changes).
    
    Results are stored in customer_comparison_results table.
    """
    
    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.object_lookup_repo = self._get_repository(ObjectLookupRepository)
        self.package_object_mapping_repo = self._get_repository(
            PackageObjectMappingRepository
        )
        self.customer_comparison_repo = self._get_repository(
            CustomerComparisonRepository
        )
        
        # Initialize comparison strategies
        self.version_strategy = SimpleVersionComparisonStrategy()
        self.content_strategy = SAILCodeComparisonStrategy(
            critical_fields=['sail_code', 'fields', 'properties']
        )
    
    def compare(
        self,
        session_id: int,
        base_package_id: int,
        customer_package_id: int
    ) -> List[CustomerChange]:
        """
        Compare Package A (Base) to Package B (Customer) to identify customer changes.
        
        This performs a FULL comparison, symmetric with delta comparison.
        
        Steps:
        1. Get objects in package A
        2. Get objects in package B
        3. Identify NEW objects (in B, not in A)
        4. Identify DEPRECATED objects (in A, not in B)
        5. Identify MODIFIED objects (in both A and B with differences)
        6. Store results in customer_comparison_results
        
        Args:
            session_id: Merge session ID
            base_package_id: Package A (Base) ID
            customer_package_id: Package B (Customer) ID
            
        Returns:
            List of CustomerChange domain entities (Set E)
        """
        self.logger.info(
            f"Starting customer comparison for session {session_id}: "
            f"Package A (id={base_package_id}) → Package B (id={customer_package_id})"
        )
        
        # Get objects in both packages
        base_objects = self.package_object_mapping_repo.get_objects_in_package(
            base_package_id
        )
        customer_objects = self.package_object_mapping_repo.get_objects_in_package(
            customer_package_id
        )
        
        self.logger.info(
            f"Package A has {len(base_objects)} objects, "
            f"Package B has {len(customer_objects)} objects"
        )
        
        # Create lookup maps by UUID
        base_map = {obj.uuid: obj for obj in base_objects}
        customer_map = {obj.uuid: obj for obj in customer_objects}
        
        customer_results = []
        
        # Find NEW objects (in B, not in A)
        new_objects = [
            obj for uuid, obj in customer_map.items()
            if uuid not in base_map
        ]
        
        for obj in new_objects:
            customer_results.append({
                'session_id': session_id,
                'object_id': obj.id,
                'change_category': ChangeCategory.NEW.value,
                'change_type': ChangeType.ADDED.value,
                'version_changed': False,
                'content_changed': False
            })
        
        self.logger.info(f"Found {len(new_objects)} NEW objects (customer added)")
        
        # Find DEPRECATED objects (in A, not in B)
        deprecated_objects = [
            obj for uuid, obj in base_map.items()
            if uuid not in customer_map
        ]
        
        for obj in deprecated_objects:
            customer_results.append({
                'session_id': session_id,
                'object_id': obj.id,
                'change_category': ChangeCategory.DEPRECATED.value,
                'change_type': ChangeType.REMOVED.value,
                'version_changed': False,
                'content_changed': False
            })
        
        self.logger.info(
            f"Found {len(deprecated_objects)} DEPRECATED objects (customer removed)"
        )
        
        # Find MODIFIED objects (in both A and B)
        common_uuids = set(base_map.keys()) & set(customer_map.keys())
        modified_count = 0
        
        for uuid in common_uuids:
            base_obj = base_map[uuid]
            
            # Compare versions
            version_changed, content_changed = self._compare_versions(
                base_obj,
                base_package_id,
                customer_package_id
            )
            
            # Only store if content actually changed
            if content_changed:
                customer_results.append({
                    'session_id': session_id,
                    'object_id': base_obj.id,
                    'change_category': ChangeCategory.MODIFIED.value,
                    'change_type': ChangeType.MODIFIED.value,
                    'version_changed': version_changed,
                    'content_changed': content_changed
                })
                modified_count += 1
        
        self.logger.info(
            f"Found {modified_count} MODIFIED objects (customer modified)"
        )
        
        # Store results in customer_comparison_results
        if customer_results:
            self.customer_comparison_repo.bulk_create_results(customer_results)
            self.logger.info(
                f"Stored {len(customer_results)} customer comparison results"
            )
        
        # Convert to domain entities
        domain_entities = [
            CustomerChange(
                object_id=result['object_id'],
                change_category=ChangeCategory(result['change_category']),
                change_type=ChangeType(result['change_type']),
                version_changed=result['version_changed'],
                content_changed=result['content_changed']
            )
            for result in customer_results
        ]
        
        self.logger.info(
            f"Customer comparison complete: {len(new_objects)} NEW, "
            f"{modified_count} MODIFIED, {len(deprecated_objects)} DEPRECATED"
        )
        
        return domain_entities
    
    def _compare_versions(
        self,
        obj_lookup: ObjectLookup,
        base_package_id: int,
        customer_package_id: int
    ) -> Tuple[bool, bool]:
        """Compare versions between base and customer packages."""
        base_version = self._get_object_version(obj_lookup.id, base_package_id)
        customer_version = self._get_object_version(obj_lookup.id, customer_package_id)
        
        if not base_version or not customer_version:
            return False, False
        
        version_changed = self.version_strategy.compare(
            base_version.version_uuid,
            customer_version.version_uuid
        )
        
        base_content = self._extract_content(base_version)
        customer_content = self._extract_content(customer_version)
        
        content_changed = self.content_strategy.compare(
            base_content,
            customer_content
        )
        
        return version_changed, content_changed
    
    def _get_object_version(
        self,
        object_id: int,
        package_id: int
    ) -> Optional[ObjectVersion]:
        """Get object version for a specific package."""
        return db.session.query(ObjectVersion).filter_by(
            object_id=object_id,
            package_id=package_id
        ).first()
    
    def _extract_content(self, version: ObjectVersion) -> Dict[str, Any]:
        """Extract content from ObjectVersion for comparison."""
        import json
        
        content = {}
        
        if version.sail_code:
            content['sail_code'] = version.sail_code
        
        if version.fields:
            try:
                content['fields'] = json.loads(version.fields)
            except json.JSONDecodeError:
                content['fields'] = version.fields
        
        if version.properties:
            try:
                content['properties'] = json.loads(version.properties)
            except json.JSONDecodeError:
                content['properties'] = version.properties
        
        return content
```

**Key Changes:**
1. ✅ Removed `delta_changes` parameter
2. ✅ Added `session_id` parameter
3. ✅ Performs full A→B comparison (symmetric with delta)
4. ✅ Returns `List[CustomerChange]` instead of `Dict`
5. ✅ Stores results in `customer_comparison_results` table
6. ✅ Finds NEW, DEPRECATED, MODIFIED objects independently


### 6.5 Phase 4: Rewrite Classification Service

**File:** `services/classification_service.py`

Complete rewrite with set-based logic:

```python
"""
Classification Service

Applies set-based classification logic to determine merge conflicts.

Key Concept:
- Set D: Vendor changes (Base → New Vendor, A→C)
- Set E: Customer changes (Base → Customer, A→B)
- Conflict: Object in D ∩ E (both parties modified)
- No Conflict: Object in D \ E (vendor only) or E \ D (customer only)
"""

import logging
from typing import List, Dict, Any

from core.base_service import BaseService
from repositories.change_repository import ChangeRepository
from domain.entities import VendorChange, CustomerChange, MergeAnalysis, ClassifiedChange
from domain.enums import Classification, ChangeType, ChangeCategory


class SetBasedClassifier:
    """
    Set-based classifier for three-way merge.
    
    Uses set theory to determine conflicts:
    - D ∩ E → CONFLICT (both modified)
    - D \ E → NO_CONFLICT (vendor only)
    - E \ D → NO_CONFLICT (customer only)
    """
    
    def __init__(self):
        """Initialize classifier."""
        self.logger = logging.getLogger(__name__)
    
    def classify(
        self,
        vendor_changes: List[VendorChange],
        customer_changes: List[CustomerChange]
    ) -> List[MergeAnalysis]:
        """
        Classify changes using set-based logic.
        
        Args:
            vendor_changes: List of vendor changes (Set D)
            customer_changes: List of customer changes (Set E)
            
        Returns:
            List of MergeAnalysis entities with classifications
        """
        # Build sets of object IDs
        vendor_set = {change.object_id for change in vendor_changes}
        customer_set = {change.object_id for change in customer_changes}
        
        # Build lookup maps
        vendor_map = {change.object_id: change for change in vendor_changes}
        customer_map = {change.object_id: change for change in customer_changes}
        
        # Get all objects (union of both sets)
        all_objects = vendor_set | customer_set
        
        self.logger.info(
            f"Classifying {len(all_objects)} objects: "
            f"Vendor={len(vendor_set)}, Customer={len(customer_set)}, "
            f"Intersection={len(vendor_set & customer_set)}"
        )
        
        analyses = []
        
        for object_id in all_objects:
            in_vendor = object_id in vendor_set
            in_customer = object_id in customer_set
            
            vendor_change = vendor_map.get(object_id)
            customer_change = customer_map.get(object_id)
            
            # Determine classification
            classification = self._determine_classification(
                in_vendor,
                in_customer,
                vendor_change,
                customer_change
            )
            
            analysis = MergeAnalysis(
                object_id=object_id,
                in_vendor_changes=in_vendor,
                in_customer_changes=in_customer,
                vendor_change=vendor_change,
                customer_change=customer_change,
                classification=classification
            )
            
            analyses.append(analysis)
        
        # Log statistics
        stats = self._get_classification_stats(analyses)
        self.logger.info(
            f"Classification complete: "
            f"CONFLICT={stats['CONFLICT']}, "
            f"NO_CONFLICT={stats['NO_CONFLICT']}, "
            f"DELETED={stats['DELETED']}"
        )
        
        return analyses
    
    def _determine_classification(
        self,
        in_vendor: bool,
        in_customer: bool,
        vendor_change: VendorChange,
        customer_change: CustomerChange
    ) -> Classification:
        """
        Determine classification based on set membership.
        
        Logic:
        1. If in both D and E → Check for special cases, else CONFLICT
        2. If in D only or E only → NO_CONFLICT
        
        Special case: Vendor deleted (DEPRECATED) + Customer modified → DELETED
        """
        if in_vendor and in_customer:
            # Both parties modified the same object
            # Check for special case: vendor deleted, customer modified
            if (vendor_change.change_category == ChangeCategory.DEPRECATED and
                customer_change.change_category == ChangeCategory.MODIFIED):
                self.logger.debug(
                    f"Object {vendor_change.object_id}: DELETED "
                    f"(vendor removed, customer modified)"
                )
                return Classification.DELETED
            else:
                self.logger.debug(
                    f"Object {vendor_change.object_id}: CONFLICT "
                    f"(both parties modified)"
                )
                return Classification.CONFLICT
        
        elif in_vendor:
            # Only vendor changed this object
            self.logger.debug(
                f"Object {vendor_change.object_id}: NO_CONFLICT (vendor only)"
            )
            return Classification.NO_CONFLICT
        
        elif in_customer:
            # Only customer changed this object
            self.logger.debug(
                f"Object {customer_change.object_id}: NO_CONFLICT (customer only)"
            )
            return Classification.NO_CONFLICT
        
        else:
            # This shouldn't happen
            raise ValueError("Object not in vendor or customer changes")
    
    def _get_classification_stats(
        self,
        analyses: List[MergeAnalysis]
    ) -> Dict[str, int]:
        """Get statistics for classifications."""
        stats = {
            'CONFLICT': 0,
            'NO_CONFLICT': 0,
            'DELETED': 0
        }
        
        for analysis in analyses:
            classification_str = analysis.classification.value
            stats[classification_str] = stats.get(classification_str, 0) + 1
        
        return stats


class ClassificationService(BaseService):
    """
    Service for classifying changes using set-based logic.
    
    This service:
    1. Takes vendor changes (Set D) and customer changes (Set E)
    2. Applies set-based classification logic
    3. Creates Change records in the working set
    4. Sets display_order for consistent presentation
    """
    
    def __init__(self, container=None):
        """Initialize service with dependencies."""
        super().__init__(container)
        self.logger = logging.getLogger(__name__)
    
    def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        self.change_repo = self._get_repository(ChangeRepository)
        self.classifier = SetBasedClassifier()
    
    def classify(
        self,
        session_id: int,
        vendor_changes: List[VendorChange],
        customer_changes: List[CustomerChange]
    ) -> List[ClassifiedChange]:
        """
        Classify changes using set-based logic.
        
        Args:
            session_id: Merge session ID
            vendor_changes: List of VendorChange entities (Set D)
            customer_changes: List of CustomerChange entities (Set E)
            
        Returns:
            List of ClassifiedChange entities
        """
        self.logger.info(
            f"Starting classification for session {session_id}: "
            f"Vendor changes={len(vendor_changes)}, "
            f"Customer changes={len(customer_changes)}"
        )
        
        # Apply set-based classification
        analyses = self.classifier.classify(vendor_changes, customer_changes)
        
        # Convert to ClassifiedChange entities
        classified_changes = []
        
        for analysis in analyses:
            vendor_change_type = (
                analysis.vendor_change.change_type
                if analysis.vendor_change
                else None
            )
            
            customer_change_type = (
                analysis.customer_change.change_type
                if analysis.customer_change
                else None
            )
            
            classified_change = ClassifiedChange(
                object_id=analysis.object_id,
                classification=analysis.classification,
                vendor_change_type=vendor_change_type,
                customer_change_type=customer_change_type,
                display_order=0
            )
            
            classified_changes.append(classified_change)
        
        # Sort by classification priority for display order
        classified_changes = self._sort_by_priority(classified_changes)
        
        # Assign display order
        for i, change in enumerate(classified_changes, start=1):
            change.display_order = i
        
        # Create Change records in database
        self._create_change_records(session_id, classified_changes)
        
        # Log statistics
        stats = self._get_classification_stats(classified_changes)
        self.logger.info(
            f"Classification complete for session {session_id}: "
            f"CONFLICT={stats['CONFLICT']}, "
            f"NO_CONFLICT={stats['NO_CONFLICT']}, "
            f"DELETED={stats['DELETED']}"
        )
        
        return classified_changes
    
    def _sort_by_priority(
        self,
        classified_changes: List[ClassifiedChange]
    ) -> List[ClassifiedChange]:
        """
        Sort classified changes by priority.
        
        Priority order:
        1. CONFLICT (highest priority - requires manual review)
        2. DELETED (vendor deleted, customer modified)
        3. NO_CONFLICT (lowest priority - can be auto-merged)
        """
        priority_map = {
            Classification.CONFLICT: 1,
            Classification.DELETED: 2,
            Classification.NO_CONFLICT: 3
        }
        
        return sorted(
            classified_changes,
            key=lambda c: priority_map[c.classification]
        )
    
    def _create_change_records(
        self,
        session_id: int,
        classified_changes: List[ClassifiedChange]
    ) -> None:
        """Create Change records in database."""
        changes_data = []
        
        for classified_change in classified_changes:
            change_data = {
                'session_id': session_id,
                'object_id': classified_change.object_id,
                'classification': classified_change.classification.value,
                'display_order': classified_change.display_order,
                'vendor_change_type': (
                    classified_change.vendor_change_type.value
                    if classified_change.vendor_change_type
                    else None
                ),
                'customer_change_type': (
                    classified_change.customer_change_type.value
                    if classified_change.customer_change_type
                    else None
                )
            }
            changes_data.append(change_data)
        
        # Bulk create
        self.change_repo.bulk_create_changes(changes_data)
        
        self.logger.info(
            f"Created {len(changes_data)} change records for session {session_id}"
        )
    
    def _get_classification_stats(
        self,
        classified_changes: List[ClassifiedChange]
    ) -> Dict[str, int]:
        """Get statistics for classified changes."""
        stats = {
            'CONFLICT': 0,
            'NO_CONFLICT': 0,
            'DELETED': 0
        }
        
        for change in classified_changes:
            classification_str = change.classification.value
            stats[classification_str] = stats.get(classification_str, 0) + 1
        
        return stats
```

**Key Changes:**
1. ✅ Accept both `vendor_changes` and `customer_changes` as complete lists
2. ✅ Use set-based logic (D ∩ E, D \ E, E \ D)
3. ✅ Classify ALL objects in the union (D ∪ E)
4. ✅ Include customer-only changes
5. ✅ Simpler logic (no complex 7-rule system)
6. ✅ Handle special case: vendor deleted + customer modified → DELETED


### 6.6 Phase 5: Update Orchestrator

**File:** `services/three_way_merge_orchestrator.py`

Update the workflow to use correct parameters:

```python
def create_merge_session(
    self,
    base_zip_path: str,
    customized_zip_path: str,  # Customer package
    new_vendor_zip_path: str   # New vendor package
) -> MergeSession:
    """
    Create and process a new merge session.
    
    Package Assignment:
    - Package A = Base vendor version (base_zip_path)
    - Package B = Customer version (customized_zip_path)
    - Package C = Latest vendor version (new_vendor_zip_path)
    
    Workflow:
    1. Create session record
    2. Extract Package A (Base)
    3. Extract Package B (Customer)
    4. Extract Package C (New Vendor)
    5. Perform vendor comparison (A→C, Set D)
    6. Perform customer comparison (A→B, Set E)
    7. Classify changes (D ∩ E, D \ E, E \ D)
    8. Generate merge guidance
    9. Update session status to 'READY'
    """
    try:
        # ... session creation ...
        
        # Step 2: Extract Package A (Base)
        package_a = self.package_extraction_service.extract_package(
            session_id=session.id,
            zip_path=base_zip_path,
            package_type='base'
        )
        
        # Step 3: Extract Package B (Customer)
        package_b = self.package_extraction_service.extract_package(
            session_id=session.id,
            zip_path=customized_zip_path,
            package_type='customized'
        )
        
        # Step 4: Extract Package C (New Vendor)
        package_c = self.package_extraction_service.extract_package(
            session_id=session.id,
            zip_path=new_vendor_zip_path,
            package_type='new_vendor'
        )
        
        # Step 5: Perform vendor comparison (A→C, Set D)
        LoggerConfig.log_step(
            self.logger, 5, 9,
            "Performing vendor comparison (A→C, Set D)"
        )
        
        vendor_changes = self.delta_comparison_service.compare(
            session_id=session.id,
            base_package_id=package_a.id,      # A
            new_vendor_package_id=package_c.id # C
        )
        
        self.logger.info(
            f"✓ Vendor comparison complete: {len(vendor_changes)} changes detected"
        )
        
        # Step 6: Perform customer comparison (A→B, Set E)
        LoggerConfig.log_step(
            self.logger, 6, 9,
            "Performing customer comparison (A→B, Set E)"
        )
        
        customer_changes = self.customer_comparison_service.compare(
            session_id=session.id,             # ✓ Added session_id
            base_package_id=package_a.id,      # A
            customer_package_id=package_b.id   # B
            # ✓ Removed delta_changes parameter!
        )
        
        self.logger.info(
            f"✓ Customer comparison complete: {len(customer_changes)} changes detected"
        )
        
        # Step 7: Classify changes (D ∪ E)
        LoggerConfig.log_step(
            self.logger, 7, 9,
            "Classifying changes (set-based: D ∩ E, D \\ E, E \\ D)"
        )
        
        classified_changes = self.classification_service.classify(
            session_id=session.id,
            vendor_changes=vendor_changes,     # ✓ Complete Set D
            customer_changes=customer_changes  # ✓ Complete Set E
        )
        
        self.logger.info(
            f"✓ Classification complete: {len(classified_changes)} changes classified"
        )
        
        # Log classification breakdown
        classification_counts = {}
        for change in classified_changes:
            classification_counts[change.classification] = \
                classification_counts.get(change.classification, 0) + 1
        
        self.logger.info("Classification breakdown:")
        for classification, count in sorted(
            classification_counts.items(),
            key=lambda x: x[0].name
        ):
            self.logger.info(f"  - {classification.value}: {count}")
        
        # ... rest of workflow ...
        
        return session
```

**Key Changes:**
1. ✅ Renamed `delta_changes` to `vendor_changes` for clarity
2. ✅ Added `session_id` to customer comparison call
3. ✅ Removed `delta_changes` parameter from customer comparison
4. ✅ Pass both complete sets to classification service
5. ✅ Updated log messages to reflect correct logic

### 6.7 Phase 6: Register New Repository

**File:** `app.py`

Add the new repository to dependency injection:

```python
def _register_repositories(container):
    """Register all repository classes with the dependency container."""
    from repositories.request_repository import RequestRepository
    from repositories.chat_session_repository import ChatSessionRepository
    from repositories.change_repository import ChangeRepository
    from repositories.object_lookup_repository import ObjectLookupRepository
    from repositories.package_object_mapping_repository import (
        PackageObjectMappingRepository
    )
    from repositories.delta_comparison_repository import (
        DeltaComparisonRepository
    )
    from repositories.customer_comparison_repository import (
        CustomerComparisonRepository  # ✓ NEW
    )
    
    # Register each repository
    container.register_repository(RequestRepository)
    container.register_repository(ChatSessionRepository)
    container.register_repository(ChangeRepository)
    container.register_repository(ObjectLookupRepository)
    container.register_repository(PackageObjectMappingRepository)
    container.register_repository(DeltaComparisonRepository)
    container.register_repository(CustomerComparisonRepository)  # ✓ NEW
```

---

## 7. Testing Strategy

### 7.1 Property-Based Tests

Update existing property tests to verify correct behavior:

#### Test 1: Set-Based Working Set
```python
def test_property_working_set_is_union():
    """
    Property: Working set equals D ∪ E
    
    The working set should contain exactly the union of vendor
    and customer changes.
    """
    # Get vendor changes (Set D)
    vendor_results = db.session.query(DeltaComparisonResult).filter_by(
        session_id=session_id
    ).all()
    vendor_objects = {r.object_id for r in vendor_results}
    
    # Get customer changes (Set E)
    customer_results = db.session.query(CustomerComparisonResult).filter_by(
        session_id=session_id
    ).all()
    customer_objects = {r.object_id for r in customer_results}
    
    # Get working set
    changes = db.session.query(Change).filter_by(
        session_id=session_id
    ).all()
    working_set_objects = {c.object_id for c in changes}
    
    # Verify: working set = D ∪ E
    union = vendor_objects | customer_objects
    assert working_set_objects == union, \
        f"Working set should equal D ∪ E. Expected {len(union)}, got {len(working_set_objects)}"
```

#### Test 2: Conflicts are Intersection
```python
def test_property_conflicts_are_intersection():
    """
    Property: CONFLICT objects are exactly D ∩ E
    
    An object is classified as CONFLICT (or DELETED) if and only if
    it appears in both vendor and customer changes.
    """
    vendor_objects = {r.object_id for r in vendor_results}
    customer_objects = {r.object_id for r in customer_results}
    intersection = vendor_objects & customer_objects
    
    # Get conflicts and deleted
    conflicts = {c.object_id for c in changes if c.classification == 'CONFLICT'}
    deleted = {c.object_id for c in changes if c.classification == 'DELETED'}
    
    # Conflicts + Deleted should equal intersection
    assert (conflicts | deleted) == intersection, \
        f"CONFLICT + DELETED should equal D ∩ E"
```

#### Test 3: Vendor-Only Changes
```python
def test_property_vendor_only_changes():
    """
    Property: Vendor-only NO_CONFLICT objects are exactly D \ E
    """
    vendor_objects = {r.object_id for r in vendor_results}
    customer_objects = {r.object_id for r in customer_results}
    vendor_only = vendor_objects - customer_objects
    
    vendor_only_changes = {
        c.object_id for c in changes
        if c.classification == 'NO_CONFLICT'
        and c.vendor_change_type is not None
        and c.customer_change_type is None
    }
    
    assert vendor_only_changes == vendor_only, \
        f"Vendor-only NO_CONFLICT should equal D \\ E"
```

#### Test 4: Customer-Only Changes (CRITICAL)
```python
def test_property_customer_only_changes():
    """
    Property: Customer-only NO_CONFLICT objects are exactly E \ D
    
    This is the CRITICAL test that verifies customer-only changes
    are not lost.
    """
    vendor_objects = {r.object_id for r in vendor_results}
    customer_objects = {r.object_id for r in customer_results}
    customer_only = customer_objects - vendor_objects
    
    customer_only_changes = {
        c.object_id for c in changes
        if c.classification == 'NO_CONFLICT'
        and c.customer_change_type is not None
        and c.vendor_change_type is None
    }
    
    assert customer_only_changes == customer_only, \
        f"Customer-only NO_CONFLICT should equal E \\ D"
    
    # Verify customer-only changes are not empty
    assert len(customer_only) > 0, \
        "Test data should have customer-only changes"
```

### 7.2 Integration Tests

```python
def test_complete_workflow_with_customer_only_changes():
    """
    Integration test: Verify customer-only changes are included.
    
    This test uses real packages and verifies that customer-only
    changes appear in the working set.
    """
    # Create merge session
    orchestrator = ThreeWayMergeOrchestrator()
    session = orchestrator.create_merge_session(
        base_zip_path='applicationArtifacts/Three Way Testing Files/V3/Test Application - Base Version.zip',
        customized_zip_path='applicationArtifacts/Three Way Testing Files/V3/Test Application Customer Version.zip',
        new_vendor_zip_path='applicationArtifacts/Three Way Testing Files/V3/Test Application Vendor New Version.zip'
    )
    
    # Get customer comparison results
    customer_results = db.session.query(CustomerComparisonResult).filter_by(
        session_id=session.id
    ).all()
    
    # Verify customer comparison was performed
    assert len(customer_results) > 0, "Customer comparison should produce results"
    
    # Get vendor comparison results
    vendor_results = db.session.query(DeltaComparisonResult).filter_by(
        session_id=session.id
    ).all()
    
    # Find customer-only objects
    vendor_objects = {r.object_id for r in vendor_results}
    customer_objects = {r.object_id for r in customer_results}
    customer_only = customer_objects - vendor_objects
    
    # Verify customer-only objects are in working set
    changes = db.session.query(Change).filter_by(
        session_id=session.id
    ).all()
    working_set_objects = {c.object_id for c in changes}
    
    for obj_id in customer_only:
        assert obj_id in working_set_objects, \
            f"Customer-only object {obj_id} should be in working set"
    
    # Verify they're classified as NO_CONFLICT
    customer_only_changes = [
        c for c in changes
        if c.object_id in customer_only
    ]
    
    for change in customer_only_changes:
        assert change.classification == 'NO_CONFLICT', \
            f"Customer-only change should be NO_CONFLICT"
        assert change.customer_change_type is not None, \
            f"Customer-only change should have customer_change_type"
        assert change.vendor_change_type is None, \
            f"Customer-only change should not have vendor_change_type"
```

### 7.3 Test Execution

**MANDATORY: Use redirect-and-cat pattern:**

```bash
# Run all tests
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run property tests
python -m pytest tests/test_three_way_merge.py -k "property" -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Run specific test
python -m pytest tests/test_three_way_merge.py::test_property_customer_only_changes -v > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

---

## 8. Migration Plan

### 8.1 Pre-Migration Checklist

- [ ] Backup production database
- [ ] Test migration script on copy of database
- [ ] Run all tests for other features (breakdown, verify, create, etc.)
- [ ] Verify other features still work
- [ ] Document current merge sessions (will be deleted)

### 8.2 Migration Steps

#### Step 1: Database Migration (5 minutes)

```bash
# Run migration script
python migrations/add_customer_comparison_results.py

# Verify migration
python -c "
from app import create_app
from models import db, CustomerComparisonResult
app = create_app()
with app.app_context():
    # Check table exists
    result = db.session.execute(
        'SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"customer_comparison_results\"'
    )
    assert result.fetchone() is not None
    print('✓ customer_comparison_results table exists')
"
```

#### Step 2: Delete Old Merge Sessions (2 minutes)

```python
# Old sessions used incorrect logic, must be deleted
from app import create_app
from models import db, MergeSession

app = create_app()
with app.app_context():
    sessions = MergeSession.query.all()
    print(f"Deleting {len(sessions)} old merge sessions...")
    
    for session in sessions:
        print(f"  Deleting {session.reference_id}")
        db.session.delete(session)
    
    db.session.commit()
    print("✓ All old sessions deleted")
```

#### Step 3: Code Deployment (5 minutes)

```bash
# Pull latest code
git pull origin main

# Install any new dependencies
pip install -r requirements.txt

# Restart application
# (Stop existing instance first)
lsof -ti :5002 | xargs kill -9

# Start new instance
python app.py
```

#### Step 4: Verification (15 minutes)

```bash
# Run all tests
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt

# Test with real packages
python -c "
from app import create_app
from core.dependency_container import DependencyContainer
from services.three_way_merge_orchestrator import ThreeWayMergeOrchestrator

app = create_app()
with app.app_context():
    container = DependencyContainer.get_instance()
    orchestrator = container.get_service(ThreeWayMergeOrchestrator)
    
    session = orchestrator.create_merge_session(
        base_zip_path='applicationArtifacts/Three Way Testing Files/V3/Test Application - Base Version.zip',
        customized_zip_path='applicationArtifacts/Three Way Testing Files/V3/Test Application Customer Version.zip',
        new_vendor_zip_path='applicationArtifacts/Three Way Testing Files/V3/Test Application Vendor New Version.zip'
    )
    
    print(f'✓ Session created: {session.reference_id}')
    print(f'✓ Total changes: {session.total_changes}')
    print(f'✓ Status: {session.status}')
"
```

#### Step 5: Verify Customer-Only Changes (CRITICAL)

```python
from app import create_app
from models import db, DeltaComparisonResult, CustomerComparisonResult, Change

app = create_app()
with app.app_context():
    # Get latest session
    from models import MergeSession
    session = MergeSession.query.order_by(MergeSession.id.desc()).first()
    
    # Get vendor changes (Set D)
    vendor_results = db.session.query(DeltaComparisonResult).filter_by(
        session_id=session.id
    ).all()
    vendor_objects = {r.object_id for r in vendor_results}
    
    # Get customer changes (Set E)
    customer_results = db.session.query(CustomerComparisonResult).filter_by(
        session_id=session.id
    ).all()
    customer_objects = {r.object_id for r in customer_results}
    
    # Find customer-only objects
    customer_only = customer_objects - vendor_objects
    
    print(f"✓ Vendor changes (Set D): {len(vendor_objects)}")
    print(f"✓ Customer changes (Set E): {len(customer_objects)}")
    print(f"✓ Customer-only changes (E \\ D): {len(customer_only)}")
    
    # Verify they're in working set
    changes = db.session.query(Change).filter_by(
        session_id=session.id
    ).all()
    working_set_objects = {c.object_id for c in changes}
    
    customer_only_in_working_set = customer_only & working_set_objects
    
    print(f"✓ Customer-only in working set: {len(customer_only_in_working_set)}")
    
    if len(customer_only) > 0:
        assert len(customer_only_in_working_set) == len(customer_only), \
            "All customer-only changes should be in working set!"
        print("✓ SUCCESS: All customer-only changes are in working set!")
    else:
        print("⚠ WARNING: No customer-only changes in test data")
```

### 8.3 Rollback Plan

If issues are discovered:

```bash
# Step 1: Stop application
lsof -ti :5002 | xargs kill -9

# Step 2: Rollback database
python -c "
from migrations.add_customer_comparison_results import downgrade
downgrade()
"

# Step 3: Revert code
git revert <commit-hash>

# Step 4: Restart application
python app.py

# Step 5: Verify rollback
python -c "
from app import create_app
from models import db
app = create_app()
with app.app_context():
    result = db.session.execute(
        'SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"customer_comparison_results\"'
    )
    assert result.fetchone() is None
    print('✓ customer_comparison_results table removed')
"
```

### 8.4 Post-Migration Verification

**Verify other features still work:**

```bash
# Test document intelligence features
curl -X POST http://localhost:5002/breakdown/upload \
  -F "file=@test_document.pdf" \
  -F "action_type=breakdown"

# Should return success response
```

**Verify merge feature works correctly:**

```bash
# Create merge session via API
curl -X POST http://localhost:5002/merge/create \
  -F "base_package=@base.zip" \
  -F "customized_package=@customer.zip" \
  -F "new_vendor_package=@vendor.zip"

# Should return session with reference_id and total_changes
```

---

## 9. Summary

### 9.1 What Was Wrong

1. **Customer comparison only checked delta objects** - Missed customer-only changes
2. **Classification only analyzed delta objects** - Customer-only changes never classified
3. **Asymmetric comparison logic** - Vendor changes fully analyzed, customer changes partially analyzed
4. **Delta-centric approach** - Treated vendor changes as primary, customer changes as secondary

### 9.2 What Was Fixed

1. **Customer comparison now performs full A→B comparison** - Finds all customer changes
2. **Classification uses set-based logic** - Analyzes all objects in D ∪ E
3. **Symmetric comparison logic** - Both vendor and customer changes fully analyzed
4. **Set-based approach** - Both parties' changes are equal (D ∩ E, D \ E, E \ D)

### 9.3 Impact

**Before Fix:**
- Customer-only changes: **MISSING**
- Working set: Only vendor changes + conflicts
- Data loss: Customer modifications not visible

**After Fix:**
- Customer-only changes: **INCLUDED**
- Working set: All changes from both parties (D ∪ E)
- Complete visibility: All modifications tracked

### 9.4 Effort Estimate

| Phase | Task | Effort |
|-------|------|--------|
| 1 | Database schema | 1 hour |
| 2 | Domain entities | 0.5 hours |
| 3 | Customer comparison service | 2 hours |
| 4 | Classification service | 2 hours |
| 5 | Orchestrator updates | 1 hour |
| 6 | Testing | 2 hours |
| 7 | Migration & deployment | 1 hour |
| **Total** | | **9.5 hours** |

### 9.5 Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Other features affected | Very Low | High | They're completely isolated |
| Migration fails | Low | High | Test on copy, have rollback plan |
| Customer-only changes still missing | Low | Critical | Property tests verify this |
| Performance degradation | Low | Medium | Customer comparison is same as delta |

### 9.6 Success Criteria

- [ ] All property tests pass
- [ ] Customer-only changes appear in working set
- [ ] Set-based classification works correctly (D ∩ E, D \ E, E \ D)
- [ ] No data loss
- [ ] Other features (breakdown, verify, create, etc.) still work
- [ ] Performance is acceptable

---

**End of Document**

**Document Version:** 1.0  
**Last Updated:** December 2, 2025  
**Author:** Kiro AI Assistant  
**Status:** Ready for Implementation
