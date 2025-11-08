# Appian Data Type XML Schema

## XML Structure
```xml
<datatype xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>dt-uuid</uuid>
    <name>DataTypeName</name>
    <description>Data type description</description>
    <namespace>http://www.appian.com/ae/types/2009</namespace>
    <elements>
      <element>
        <name>fieldName</name>
        <type>Text</type>
        <multiple>false</multiple>
      </element>
    </elements>
    <parent>parent-folder-id</parent>
  </ixObject>
  <resourceName>DataTypeName.xsd</resourceName>
  <roleMap>
    <roleMapEntry>
      <actor type="user|group">actor-name</actor>
      <role>VIEWER|EDITOR|ADMIN</role>
    </roleMapEntry>
  </roleMap>
</datatype>
```

## Key Tags
- **name**: Data type identifier used in expressions (e.g., `type!DataTypeName`)
- **namespace**: XML namespace for the data type
- **elements**: Field definitions with names and types
- **resourceName**: Points to the XSD schema file in the export package
- **description**: Human-readable description of the data structure

## Usage
Data types define custom data structures (CDTs) used throughout Appian applications.

## Blueprint Context
- **Purpose**: Defines custom data structures and schemas
- **Dependencies**: May reference other data types as field types
- **Used By**: Rules, interfaces, process models for structured data
- **Security**: Controlled via roleMap for schema access permissions
- **Schema File**: XSD definition stored separately in export package
