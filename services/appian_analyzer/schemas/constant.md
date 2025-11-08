# Appian Constant XML Schema

## XML Structure
```xml
<constant xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>constant-uuid</uuid>
    <name>CONSTANT_NAME</name>
    <description>Description text</description>
    <value type="Text|Number|Boolean|Date|Time|DateTime">Constant Value</value>
    <multiple>false</multiple>
    <visibility>PUBLIC|PRIVATE</visibility>
    <parent>parent-folder-id</parent>
    <createdBy>username</createdBy>
    <createdOn>2023-01-01T00:00:00Z</createdOn>
    <lastModifiedBy>username</lastModifiedBy>
    <lastModifiedOn>2023-01-01T00:00:00Z</lastModifiedOn>
  </ixObject>
  <roleMap>
    <roleMapEntry>
      <actor type="user|group">actor-name</actor>
      <role>VIEWER|EDITOR|ADMIN</role>
    </roleMapEntry>
  </roleMap>
</constant>
```

## Key Tags
- **name**: Constant identifier used in expressions (e.g., `cons!MY_CONSTANT`)
- **value**: The actual constant value with type attribute
- **description**: Human-readable description of the constant's purpose
- **parent**: Reference to containing folder UUID
- **type attribute**: Data type (Text, Number, Boolean, Date, Time, DateTime)

## Usage
Constants provide reusable values across applications. They are referenced in SAIL expressions using `cons!CONSTANT_NAME` syntax.

## Blueprint Context
- **Purpose**: Stores application configuration values
- **Dependencies**: None (leaf objects)
- **Used By**: Rules, interfaces, process models that reference the constant
- **Security**: Controlled via roleMap for viewing/editing permissions
