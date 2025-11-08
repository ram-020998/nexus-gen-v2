# Appian Interface XML Schema

## XML Structure
```xml
<interface xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>interface-uuid</uuid>
    <name>interfaceName</name>
    <description>Interface description</description>
    <definition>SAIL UI code</definition>
    <ruleInputs>
      <ruleInput>
        <name>ri!inputName</name>
        <type>Any Type</type>
        <multiple>false</multiple>
        <required>false</required>
      </ruleInput>
    </ruleInputs>
    <localVariables>
      <localVariable>
        <name>local!variableName</name>
        <type>Text</type>
        <refreshAlways>false</refreshAlways>
      </localVariable>
    </localVariables>
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
</interface>
```

## Key Tags
- **name**: Interface identifier used in expressions (e.g., `rule!myInterface`)
- **definition**: Contains the SAIL UI code defining the interface layout
- **ruleInputs**: Input parameters passed to the interface
- **description**: Human-readable description of the interface's purpose
- **parent**: Reference to containing folder UUID

## Usage
Interfaces define user interface layouts using SAIL. They are used in process models, sites, and other interfaces.

## Blueprint Context
- **Purpose**: Defines user interface and user experience
- **Dependencies**: May reference rules, constants, record types, process models
- **Used By**: Process models (as forms), sites (as pages), other interfaces
- **Security**: Controlled via roleMap for viewing/editing permissions
