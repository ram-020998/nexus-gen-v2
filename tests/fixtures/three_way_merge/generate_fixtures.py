#!/usr/bin/env python3
"""
Generate test fixtures for three-way merge assistant testing.

Creates various Appian package ZIP files with different characteristics:
- Small, medium, large packages
- Packages with known differences
- Packages with circular dependencies
- Malformed packages for error testing
"""

import zipfile
import os
from pathlib import Path

# Base directory for fixtures
FIXTURES_DIR = Path(__file__).parent


def create_application_xml(app_name, app_uuid, description="Test application"):
    """Create a minimal application.xml file"""
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<applicationHaul xmlns:a="http://www.appian.com/ae/types/2009">
    <versionUuid>{app_uuid}_v1</versionUuid>
    <application>
        <name>{app_name}</name>
        <uuid>{app_uuid}</uuid>
        <description>{description}</description>
        <parentUuid>SYSTEM_APPLICATIONS_ROOT</parentUuid>
        <visibility>
            <advertise>false</advertise>
            <hierarchy>true</hierarchy>
            <indexable>true</indexable>
            <quota>false</quota>
            <searchable>true</searchable>
            <system>false</system>
            <unlogged>false</unlogged>
        </visibility>
        <urlIdentifier>test</urlIdentifier>
        <published>true</published>
        <public>false</public>
    </application>
</applicationHaul>"""


def create_interface_xml(name, uuid, sail_code, parent_uuid=None):
    """Create an interface XML file"""
    parent_ref = f"<parentUuid>{parent_uuid}</parentUuid>" if parent_uuid else "<parentUuid>SYSTEM_KNOWLEDGE_CENTER</parentUuid>"
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<contentHaul xmlns:a="http://www.appian.com/ae/types/2009">
    <versionUuid>{uuid}_v1</versionUuid>
    <interfaceDefinition>
        <name>{name}</name>
        <uuid>{uuid}</uuid>
        <description>Test interface</description>
        {parent_ref}
        <visibility>
            <advertise>true</advertise>
            <hierarchy>true</hierarchy>
            <indexable>true</indexable>
            <quota>false</quota>
            <searchable>true</searchable>
            <system>false</system>
            <unlogged>false</unlogged>
        </visibility>
        <definition>{sail_code}</definition>
    </interfaceDefinition>
</contentHaul>"""


def create_rule_xml(name, uuid, expression, dependencies=None):
    """Create an expression rule XML file"""
    deps = ""
    if dependencies:
        deps = "<precedents>"
        for dep_uuid in dependencies:
            deps += f'<uuid a:isNull="false">{dep_uuid}</uuid>'
        deps += "</precedents>"
    
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<contentHaul xmlns:a="http://www.appian.com/ae/types/2009">
    <versionUuid>{uuid}_v1</versionUuid>
    <expressionRule>
        <name>{name}</name>
        <uuid>{uuid}</uuid>
        <description>Test rule</description>
        <parentUuid>SYSTEM_KNOWLEDGE_CENTER</parentUuid>
        <visibility>
            <advertise>true</advertise>
            <hierarchy>true</hierarchy>
            <indexable>true</indexable>
            <quota>false</quota>
            <searchable>true</searchable>
            <system>false</system>
            <unlogged>false</unlogged>
        </visibility>
        <definition>{expression}</definition>
        {deps}
    </expressionRule>
</contentHaul>"""


def create_datatype_xml(name, uuid, fields=None):
    """Create a data type XML file"""
    field_defs = ""
    if fields:
        for field_name, field_type in fields:
            field_defs += f"""
            <field>
                <name>{field_name}</name>
                <type>{field_type}</type>
            </field>"""
    
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<datatypeHaul xmlns:a="http://www.appian.com/ae/types/2009">
    <versionUuid>{uuid}_v1</versionUuid>
    <datatype>
        <name>{name}</name>
        <uuid>{uuid}</uuid>
        <description>Test data type</description>
        <parentUuid>SYSTEM_DATATYPE_ROOT</parentUuid>
        <visibility>
            <advertise>true</advertise>
            <hierarchy>true</hierarchy>
            <indexable>true</indexable>
            <quota>false</quota>
            <searchable>true</searchable>
            <system>false</system>
            <unlogged>false</unlogged>
        </visibility>
        <fields>{field_defs}
        </fields>
    </datatype>
</datatypeHaul>"""


def create_package(zip_path, objects):
    """
    Create a test Appian package ZIP file.
    
    Args:
        zip_path: Path to the output ZIP file
        objects: List of tuples (folder, filename, content)
    """
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for folder, filename, content in objects:
            zf.writestr(f"{folder}/{filename}", content)


# ============================================================================
# SMALL PACKAGES (5-10 objects each)
# ============================================================================

def generate_small_base_package():
    """Generate small base package (A) - original vendor version"""
    app_uuid = "_a-0000-1111-2222-3333-base00000001"
    
    objects = [
        ("application", f"{app_uuid}.xml", 
         create_application_xml("Small Test App", app_uuid, "Base version 1.0")),
        
        ("content", "_i-0000-1111-2222-3333-interface01.xml",
         create_interface_xml("HomePage", "_i-0000-1111-2222-3333-interface01", 
                            "a!textField(label: \"Welcome\", value: \"Hello\")")),
        
        ("content", "_r-0000-1111-2222-3333-rule000001.xml",
         create_rule_xml("GetUserName", "_r-0000-1111-2222-3333-rule000001",
                        "loggedInUser()")),
        
        ("content", "_r-0000-1111-2222-3333-rule000002.xml",
         create_rule_xml("FormatName", "_r-0000-1111-2222-3333-rule000002",
                        "upper(ri!name)")),
        
        ("datatype", "_t-0000-1111-2222-3333-type000001.xml",
         create_datatype_xml("User", "_t-0000-1111-2222-3333-type000001",
                           [("firstName", "Text"), ("lastName", "Text")])),
    ]
    
    create_package(FIXTURES_DIR / "small_base_v1.0.zip", objects)
    print("✓ Created small_base_v1.0.zip")


def generate_small_customized_package():
    """Generate small customized package (B) - customer modifications"""
    app_uuid = "_a-0000-1111-2222-3333-base00000001"
    
    objects = [
        ("application", f"{app_uuid}.xml",
         create_application_xml("Small Test App", app_uuid, "Customized version 1.0")),
        
        # Modified interface - customer added a field
        ("content", "_i-0000-1111-2222-3333-interface01.xml",
         create_interface_xml("HomePage", "_i-0000-1111-2222-3333-interface01",
                            "a!textField(label: \"Welcome\", value: \"Hello\"), a!textField(label: \"Custom\", value: \"Customer Field\")")),
        
        # Same rule
        ("content", "_r-0000-1111-2222-3333-rule000001.xml",
         create_rule_xml("GetUserName", "_r-0000-1111-2222-3333-rule000001",
                        "loggedInUser()")),
        
        # Modified rule - customer changed logic
        ("content", "_r-0000-1111-2222-3333-rule000002.xml",
         create_rule_xml("FormatName", "_r-0000-1111-2222-3333-rule000002",
                        "proper(ri!name)")),  # Changed from upper to proper
        
        # Same datatype
        ("datatype", "_t-0000-1111-2222-3333-type000001.xml",
         create_datatype_xml("User", "_t-0000-1111-2222-3333-type000001",
                           [("firstName", "Text"), ("lastName", "Text")])),
        
        # Customer-only addition
        ("content", "_r-0000-1111-2222-3333-rule000003.xml",
         create_rule_xml("CustomerOnlyRule", "_r-0000-1111-2222-3333-rule000003",
                        "\"Customer specific logic\"")),
    ]
    
    create_package(FIXTURES_DIR / "small_customized_v1.0.zip", objects)
    print("✓ Created small_customized_v1.0.zip")


def generate_small_new_vendor_package():
    """Generate small new vendor package (C) - new vendor release"""
    app_uuid = "_a-0000-1111-2222-3333-base00000001"
    
    objects = [
        ("application", f"{app_uuid}.xml",
         create_application_xml("Small Test App", app_uuid, "Vendor version 2.0")),
        
        # Modified interface - vendor added different field
        ("content", "_i-0000-1111-2222-3333-interface01.xml",
         create_interface_xml("HomePage", "_i-0000-1111-2222-3333-interface01",
                            "a!textField(label: \"Welcome\", value: \"Hello\"), a!textField(label: \"Version\", value: \"2.0\")")),
        
        # Modified rule - vendor changed implementation
        ("content", "_r-0000-1111-2222-3333-rule000001.xml",
         create_rule_xml("GetUserName", "_r-0000-1111-2222-3333-rule000001",
                        "user(loggedInUser(), \"username\")")),  # More specific
        
        # Same rule
        ("content", "_r-0000-1111-2222-3333-rule000002.xml",
         create_rule_xml("FormatName", "_r-0000-1111-2222-3333-rule000002",
                        "upper(ri!name)")),
        
        # Modified datatype - vendor added field
        ("datatype", "_t-0000-1111-2222-3333-type000001.xml",
         create_datatype_xml("User", "_t-0000-1111-2222-3333-type000001",
                           [("firstName", "Text"), ("lastName", "Text"), ("email", "Text")])),
        
        # Vendor-only addition
        ("content", "_r-0000-1111-2222-3333-rule000004.xml",
         create_rule_xml("VendorNewFeature", "_r-0000-1111-2222-3333-rule000004",
                        "\"New vendor feature\"")),
    ]
    
    create_package(FIXTURES_DIR / "small_new_vendor_v2.0.zip", objects)
    print("✓ Created small_new_vendor_v2.0.zip")


# ============================================================================
# MEDIUM PACKAGES (20-30 objects each)
# ============================================================================

def generate_medium_packages():
    """Generate medium-sized packages with more objects"""
    app_uuid = "_a-0000-2222-3333-4444-medium000001"
    
    # Base package
    base_objects = [
        ("application", f"{app_uuid}.xml",
         create_application_xml("Medium Test App", app_uuid, "Base version 1.0")),
    ]
    
    # Add 10 interfaces
    for i in range(10):
        uuid = f"_i-0000-2222-3333-4444-interface{i:02d}"
        base_objects.append(
            ("content", f"{uuid}.xml",
             create_interface_xml(f"Interface{i}", uuid, f"a!textField(label: \"Field{i}\", value: \"Value{i}\")"))
        )
    
    # Add 10 rules
    for i in range(10):
        uuid = f"_r-0000-2222-3333-4444-rule0000{i:02d}"
        base_objects.append(
            ("content", f"{uuid}.xml",
             create_rule_xml(f"Rule{i}", uuid, f"\"Rule {i} logic\""))
        )
    
    # Add 5 datatypes
    for i in range(5):
        uuid = f"_t-0000-2222-3333-4444-type0000{i:02d}"
        base_objects.append(
            ("datatype", f"{uuid}.xml",
             create_datatype_xml(f"Type{i}", uuid, [(f"field{j}", "Text") for j in range(3)]))
        )
    
    create_package(FIXTURES_DIR / "medium_base_v1.0.zip", base_objects)
    print("✓ Created medium_base_v1.0.zip")

    # Customized package - modify some objects
    customized_objects = base_objects.copy()
    # Modify interface 0
    customized_objects[1] = (
        "content", "_i-0000-2222-3333-4444-interface00.xml",
        create_interface_xml("Interface0", "_i-0000-2222-3333-4444-interface00",
                           "a!textField(label: \"Field0\", value: \"CustomValue0\")")
    )
    # Add customer-only object
    customized_objects.append(
        ("content", "_r-0000-2222-3333-4444-rule000099.xml",
         create_rule_xml("CustomerRule", "_r-0000-2222-3333-4444-rule000099", "\"Customer logic\""))
    )
    
    create_package(FIXTURES_DIR / "medium_customized_v1.0.zip", customized_objects)
    print("✓ Created medium_customized_v1.0.zip")
    
    # New vendor package - modify different objects
    new_vendor_objects = base_objects.copy()
    # Modify interface 1
    new_vendor_objects[2] = (
        "content", "_i-0000-2222-3333-4444-interface01.xml",
        create_interface_xml("Interface1", "_i-0000-2222-3333-4444-interface01",
                           "a!textField(label: \"Field1\", value: \"VendorValue1\")")
    )
    # Add vendor-only object
    new_vendor_objects.append(
        ("content", "_r-0000-2222-3333-4444-rule000098.xml",
         create_rule_xml("VendorRule", "_r-0000-2222-3333-4444-rule000098", "\"Vendor logic\""))
    )
    
    create_package(FIXTURES_DIR / "medium_new_vendor_v2.0.zip", new_vendor_objects)
    print("✓ Created medium_new_vendor_v2.0.zip")


# ============================================================================
# LARGE PACKAGES (50+ objects each)
# ============================================================================

def generate_large_packages():
    """Generate large packages with many objects"""
    app_uuid = "_a-0000-3333-4444-5555-large0000001"
    
    base_objects = [
        ("application", f"{app_uuid}.xml",
         create_application_xml("Large Test App", app_uuid, "Base version 1.0")),
    ]
    
    # Add 30 interfaces
    for i in range(30):
        uuid = f"_i-0000-3333-4444-5555-interface{i:02d}"
        base_objects.append(
            ("content", f"{uuid}.xml",
             create_interface_xml(f"Interface{i}", uuid, f"a!textField(label: \"Field{i}\", value: \"Value{i}\")"))
        )
    
    # Add 20 rules
    for i in range(20):
        uuid = f"_r-0000-3333-4444-5555-rule0000{i:02d}"
        base_objects.append(
            ("content", f"{uuid}.xml",
             create_rule_xml(f"Rule{i}", uuid, f"\"Rule {i} logic\""))
        )
    
    # Add 10 datatypes
    for i in range(10):
        uuid = f"_t-0000-3333-4444-5555-type0000{i:02d}"
        base_objects.append(
            ("datatype", f"{uuid}.xml",
             create_datatype_xml(f"Type{i}", uuid, [(f"field{j}", "Text") for j in range(5)]))
        )
    
    create_package(FIXTURES_DIR / "large_base_v1.0.zip", base_objects)
    print("✓ Created large_base_v1.0.zip")

    # Customized - modify 10 objects
    customized_objects = base_objects.copy()
    for i in range(5):
        idx = i + 1
        customized_objects[idx] = (
            "content", f"_i-0000-3333-4444-5555-interface{i:02d}.xml",
            create_interface_xml(f"Interface{i}", f"_i-0000-3333-4444-5555-interface{i:02d}",
                               f"a!textField(label: \"Field{i}\", value: \"CustomValue{i}\")")
        )
    
    create_package(FIXTURES_DIR / "large_customized_v1.0.zip", customized_objects)
    print("✓ Created large_customized_v1.0.zip")
    
    # New vendor - modify different 10 objects
    new_vendor_objects = base_objects.copy()
    for i in range(5, 10):
        idx = i + 1
        new_vendor_objects[idx] = (
            "content", f"_i-0000-3333-4444-5555-interface{i:02d}.xml",
            create_interface_xml(f"Interface{i}", f"_i-0000-3333-4444-5555-interface{i:02d}",
                               f"a!textField(label: \"Field{i}\", value: \"VendorValue{i}\")")
        )
    
    create_package(FIXTURES_DIR / "large_new_vendor_v2.0.zip", new_vendor_objects)
    print("✓ Created large_new_vendor_v2.0.zip")


# ============================================================================
# CIRCULAR DEPENDENCY PACKAGES
# ============================================================================

def generate_circular_dependency_packages():
    """Generate packages with circular dependencies"""
    app_uuid = "_a-0000-4444-5555-6666-circular00001"
    
    # Rule A depends on Rule B
    # Rule B depends on Rule C
    # Rule C depends on Rule A (circular!)
    
    objects = [
        ("application", f"{app_uuid}.xml",
         create_application_xml("Circular Dep App", app_uuid, "Base version with circular deps")),
        
        ("content", "_r-0000-4444-5555-6666-ruleA00001.xml",
         create_rule_xml("RuleA", "_r-0000-4444-5555-6666-ruleA00001",
                        "rule!RuleB()",
                        dependencies=["_r-0000-4444-5555-6666-ruleB00001"])),
        
        ("content", "_r-0000-4444-5555-6666-ruleB00001.xml",
         create_rule_xml("RuleB", "_r-0000-4444-5555-6666-ruleB00001",
                        "rule!RuleC()",
                        dependencies=["_r-0000-4444-5555-6666-ruleC00001"])),
        
        ("content", "_r-0000-4444-5555-6666-ruleC00001.xml",
         create_rule_xml("RuleC", "_r-0000-4444-5555-6666-ruleC00001",
                        "rule!RuleA()",
                        dependencies=["_r-0000-4444-5555-6666-ruleA00001"])),
    ]
    
    create_package(FIXTURES_DIR / "circular_base_v1.0.zip", objects)
    print("✓ Created circular_base_v1.0.zip")
    
    # Customized version - same circular deps
    create_package(FIXTURES_DIR / "circular_customized_v1.0.zip", objects)
    print("✓ Created circular_customized_v1.0.zip")
    
    # New vendor - same circular deps
    create_package(FIXTURES_DIR / "circular_new_vendor_v2.0.zip", objects)
    print("✓ Created circular_new_vendor_v2.0.zip")


# ============================================================================
# MALFORMED PACKAGES FOR ERROR TESTING
# ============================================================================

def generate_malformed_packages():
    """Generate malformed packages for error testing"""
    
    # 1. Missing application.xml
    objects = [
        ("content", "_i-0000-5555-6666-7777-interface01.xml",
         create_interface_xml("Interface1", "_i-0000-5555-6666-7777-interface01", "a!textField()"))
    ]
    create_package(FIXTURES_DIR / "malformed_no_application.zip", objects)
    print("✓ Created malformed_no_application.zip")
    
    # 2. Invalid XML
    objects = [
        ("application", "_a-0000-5555-6666-7777-malformed01.xml",
         "<?xml version=\"1.0\"?><invalid><unclosed>")
    ]
    create_package(FIXTURES_DIR / "malformed_invalid_xml.zip", objects)
    print("✓ Created malformed_invalid_xml.zip")
    
    # 3. Empty package
    create_package(FIXTURES_DIR / "malformed_empty.zip", [])
    print("✓ Created malformed_empty.zip")
    
    # 4. Corrupted structure (wrong folder names)
    app_uuid = "_a-0000-5555-6666-7777-malformed02"
    objects = [
        ("wrong_folder", f"{app_uuid}.xml",
         create_application_xml("Malformed App", app_uuid, "Wrong folder structure"))
    ]
    create_package(FIXTURES_DIR / "malformed_wrong_structure.zip", objects)
    print("✓ Created malformed_wrong_structure.zip")


# ============================================================================
# KNOWN DIFFERENCES PACKAGES
# ============================================================================

def generate_known_differences_packages():
    """Generate packages with specific known differences for testing"""
    app_uuid = "_a-0000-6666-7777-8888-known000001"
    
    # Base: 3 interfaces, 2 rules
    base_objects = [
        ("application", f"{app_uuid}.xml",
         create_application_xml("Known Diff App", app_uuid, "Base version")),
        
        ("content", "_i-0000-6666-7777-8888-interface01.xml",
         create_interface_xml("SharedInterface", "_i-0000-6666-7777-8888-interface01",
                            "a!textField(label: \"Shared\", value: \"Base\")")),
        
        ("content", "_i-0000-6666-7777-8888-interface02.xml",
         create_interface_xml("ToBeRemoved", "_i-0000-6666-7777-8888-interface02",
                            "a!textField(label: \"Remove\", value: \"Me\")")),
        
        ("content", "_r-0000-6666-7777-8888-rule000001.xml",
         create_rule_xml("SharedRule", "_r-0000-6666-7777-8888-rule000001", "\"base\"")),
    ]
    
    create_package(FIXTURES_DIR / "known_diff_base_v1.0.zip", base_objects)
    print("✓ Created known_diff_base_v1.0.zip")

    # Customized: Modified SharedInterface, kept ToBeRemoved, modified SharedRule, added CustomerOnly
    customized_objects = [
        ("application", f"{app_uuid}.xml",
         create_application_xml("Known Diff App", app_uuid, "Customized version")),
        
        ("content", "_i-0000-6666-7777-8888-interface01.xml",
         create_interface_xml("SharedInterface", "_i-0000-6666-7777-8888-interface01",
                            "a!textField(label: \"Shared\", value: \"Customer Modified\")")),
        
        ("content", "_i-0000-6666-7777-8888-interface02.xml",
         create_interface_xml("ToBeRemoved", "_i-0000-6666-7777-8888-interface02",
                            "a!textField(label: \"Remove\", value: \"Customer kept and modified\")")),
        
        ("content", "_r-0000-6666-7777-8888-rule000001.xml",
         create_rule_xml("SharedRule", "_r-0000-6666-7777-8888-rule000001", "\"customer\"")),
        
        ("content", "_r-0000-6666-7777-8888-rule000002.xml",
         create_rule_xml("CustomerOnlyRule", "_r-0000-6666-7777-8888-rule000002", "\"customer only\"")),
    ]
    
    create_package(FIXTURES_DIR / "known_diff_customized_v1.0.zip", customized_objects)
    print("✓ Created known_diff_customized_v1.0.zip")
    
    # New Vendor: Modified SharedInterface differently, removed ToBeRemoved, kept SharedRule, added VendorOnly
    new_vendor_objects = [
        ("application", f"{app_uuid}.xml",
         create_application_xml("Known Diff App", app_uuid, "New vendor version")),
        
        ("content", "_i-0000-6666-7777-8888-interface01.xml",
         create_interface_xml("SharedInterface", "_i-0000-6666-7777-8888-interface01",
                            "a!textField(label: \"Shared\", value: \"Vendor Modified\")")),
        
        # ToBeRemoved is removed (not included)
        
        ("content", "_r-0000-6666-7777-8888-rule000001.xml",
         create_rule_xml("SharedRule", "_r-0000-6666-7777-8888-rule000001", "\"base\"")),  # Unchanged
        
        ("content", "_r-0000-6666-7777-8888-rule000003.xml",
         create_rule_xml("VendorOnlyRule", "_r-0000-6666-7777-8888-rule000003", "\"vendor only\"")),
    ]
    
    create_package(FIXTURES_DIR / "known_diff_new_vendor_v2.0.zip", new_vendor_objects)
    print("✓ Created known_diff_new_vendor_v2.0.zip")
    
    print("\nExpected differences:")
    print("  - SharedInterface: CONFLICT (both modified)")
    print("  - ToBeRemoved: REMOVED_BUT_CUSTOMIZED (vendor removed, customer modified)")
    print("  - SharedRule: CONFLICT (customer modified, vendor kept same)")
    print("  - CustomerOnlyRule: CUSTOMER_ONLY")
    print("  - VendorOnlyRule: NO_CONFLICT (vendor added)")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("Generating test fixtures for three-way merge assistant...\n")
    
    print("Small packages:")
    generate_small_base_package()
    generate_small_customized_package()
    generate_small_new_vendor_package()
    
    print("\nMedium packages:")
    generate_medium_packages()
    
    print("\nLarge packages:")
    generate_large_packages()
    
    print("\nCircular dependency packages:")
    generate_circular_dependency_packages()
    
    print("\nMalformed packages:")
    generate_malformed_packages()
    
    print("\nKnown differences packages:")
    generate_known_differences_packages()
    
    print("\n✅ All test fixtures generated successfully!")
    print(f"Location: {FIXTURES_DIR}")
