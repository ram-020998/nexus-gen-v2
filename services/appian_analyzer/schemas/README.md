# Appian XML Schema Documentation

This directory contains XML schema documentation for each Appian object type that can be exported.

## Files Overview

- **constant.md** - Constants (configuration values)
- **rule.md** - Expression rules (business logic)
- **interface.md** - User interfaces (SAIL UI)
- **process-model.md** - Process models (workflows)
- **record-type.md** - Record types (data entities)
- **document.md** - Documents (binary files)
- **datatype.md** - Data types (custom data structures)
- **decision.md** - Decisions (business rules)
- **integration.md** - Integrations (external API connections)
- **folder.md** - Folders (organizational structure)
- **query-rule.md** - Query rules (database queries)
- **report.md** - Reports (data visualization)
- **application.md** - Applications (object groupings)
- **connected-system.md** - Connected systems (external system connections)

## Common XML Patterns

### Standard Structure
All objects follow this pattern:
```xml
<objectType xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>version-tracking-uuid</versionUuid>
  <ixObject>
    <!-- Object-specific content -->
  </ixObject>
  <roleMap>
    <!-- Security permissions -->
  </roleMap>
</objectType>
```

### Key Elements
- **versionUuid**: Version tracking for import/export
- **ixObject**: Main object content and metadata
- **roleMap**: Security permissions (users/groups and roles)
- **parent**: Reference to containing folder (if applicable)

### Reference Patterns
Objects reference each other using UUIDs:
```xml
<reference>
  <uuid>referenced-object-uuid</uuid>
  <type>RULE|CONSTANT|RECORD_TYPE</type>
</reference>
```

## Usage for Blueprint Generation

1. **Parse by root element** to identify object type
2. **Extract key metadata** from ixObject section
3. **Map relationships** using reference UUIDs
4. **Build hierarchy** using parent-child relationships
5. **Analyze dependencies** through nested references
