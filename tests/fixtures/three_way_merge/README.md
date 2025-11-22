# Three-Way Merge Assistant Test Fixtures

This directory contains test fixtures for the three-way merge assistant feature. These are synthetic Appian application packages designed for testing various merge scenarios.

## Fixture Categories

### 1. Small Packages (5-10 objects)
Minimal packages for quick testing and basic functionality verification.

- **small_base_v1.0.zip** - Base vendor version (A)
  - 1 application, 2 interfaces, 2 rules, 1 datatype
  
- **small_customized_v1.0.zip** - Customer customized version (B)
  - Modified: HomePage interface, FormatName rule
  - Added: CustomerOnlyRule
  
- **small_new_vendor_v2.0.zip** - New vendor release (C)
  - Modified: HomePage interface (different changes), GetUserName rule, User datatype
  - Added: VendorNewFeature rule

**Expected Results:**
- CONFLICT: HomePage (both modified), FormatName (customer modified)
- NO_CONFLICT: GetUserName (vendor only), User datatype (vendor only), VendorNewFeature (vendor only)
- CUSTOMER_ONLY: CustomerOnlyRule

### 2. Medium Packages (20-30 objects)
Moderate-sized packages for testing performance and scalability.

- **medium_base_v1.0.zip** - 10 interfaces, 10 rules, 5 datatypes
- **medium_customized_v1.0.zip** - Modified Interface0, added CustomerRule
- **medium_new_vendor_v2.0.zip** - Modified Interface1, added VendorRule

**Expected Results:**
- CONFLICT: Interface0 (customer modified)
- NO_CONFLICT: Interface1 (vendor modified), VendorRule (vendor added)
- CUSTOMER_ONLY: CustomerRule

### 3. Large Packages (50+ objects)
Large packages for stress testing and performance validation.

- **large_base_v1.0.zip** - 30 interfaces, 20 rules, 10 datatypes
- **large_customized_v1.0.zip** - Modified first 5 interfaces
- **large_new_vendor_v2.0.zip** - Modified interfaces 5-9

**Expected Results:**
- CONFLICT: Interfaces 0-4 (customer modified)
- NO_CONFLICT: Interfaces 5-9 (vendor modified)

### 4. Circular Dependency Packages
Packages with circular dependencies to test dependency resolution.

- **circular_base_v1.0.zip**
- **circular_customized_v1.0.zip**
- **circular_new_vendor_v2.0.zip**

**Dependency Chain:**
- RuleA → RuleB → RuleC → RuleA (circular!)

**Purpose:** Test that the system can detect and handle circular dependencies without crashing.

### 5. Malformed Packages
Invalid packages for error handling testing.

- **malformed_no_application.zip** - Missing application.xml file
- **malformed_invalid_xml.zip** - Contains invalid XML syntax
- **malformed_empty.zip** - Empty ZIP file
- **malformed_wrong_structure.zip** - Wrong folder structure

**Purpose:** Verify proper error handling and user-friendly error messages.

### 6. Known Differences Packages
Packages with specific, documented differences for precise testing.

- **known_diff_base_v1.0.zip**
  - SharedInterface, ToBeRemoved interface, SharedRule
  
- **known_diff_customized_v1.0.zip**
  - Modified: SharedInterface, ToBeRemoved, SharedRule
  - Added: CustomerOnlyRule
  
- **known_diff_new_vendor_v2.0.zip**
  - Modified: SharedInterface (different changes)
  - Removed: ToBeRemoved
  - Unchanged: SharedRule
  - Added: VendorOnlyRule

**Expected Results:**
- CONFLICT: SharedInterface (both modified), SharedRule (customer modified)
- REMOVED_BUT_CUSTOMIZED: ToBeRemoved (vendor removed, customer modified)
- CUSTOMER_ONLY: CustomerOnlyRule
- NO_CONFLICT: VendorOnlyRule (vendor added)

## Usage

### Regenerating Fixtures

To regenerate all fixtures:

```bash
python3 tests/fixtures/three_way_merge/generate_fixtures.py
```

### Using in Tests

```python
import os
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "three_way_merge"

# Load small packages
base_path = FIXTURES_DIR / "small_base_v1.0.zip"
customized_path = FIXTURES_DIR / "small_customized_v1.0.zip"
new_vendor_path = FIXTURES_DIR / "small_new_vendor_v2.0.zip"

# Use in tests
service.create_session(base_path, customized_path, new_vendor_path)
```

## Fixture Structure

Each Appian package ZIP contains:
- `application/` - Application definition XML
- `content/` - Interfaces and expression rules
- `datatype/` - Data type definitions

### XML Structure

All objects follow standard Appian XML format:
- Version UUID for tracking
- Object metadata (name, uuid, description)
- Parent UUID for hierarchy
- Visibility settings
- Object-specific content (SAIL code, expressions, fields)

## Testing Scenarios

### Basic Functionality
Use **small packages** to test:
- Blueprint generation
- Three-way comparison
- Change classification
- Basic merge guidance

### Performance
Use **medium** and **large packages** to test:
- Processing time
- Memory usage
- UI responsiveness with many changes

### Edge Cases
Use **circular dependency** and **malformed packages** to test:
- Error handling
- Dependency resolution
- User-friendly error messages

### Correctness
Use **known differences packages** to test:
- Accurate change detection
- Correct classification
- Proper conflict identification

## Maintenance

When updating fixtures:
1. Modify `generate_fixtures.py`
2. Run the generator script
3. Update this README with any changes
4. Update tests that depend on specific fixture characteristics

## Notes

- All UUIDs follow Appian's format: `_[type]-[hex]-[hex]-[hex]-[hex]-[name][number]`
- SAIL code is kept minimal for readability
- Fixtures are deterministic - same input always produces same output
- File sizes are kept small for fast test execution
