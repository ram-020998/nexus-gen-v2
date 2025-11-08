# Appian Rule XML Schema

## XML Structure
```xml
<rule xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>rule-uuid</uuid>
    <name>ruleName</name>
    <description>Rule description</description>
    <definition>SAIL/expression code</definition>
    <ruleInputs>
      <ruleInput>
        <name>inputName</name>
        <type>Text</type>
        <multiple>false</multiple>
        <required>true</required>
      </ruleInput>
    </ruleInputs>
    <returnType>Text</returnType>
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
</rule>
```

## Key Tags
- **name**: Rule identifier used in expressions (e.g., `rule!myRule`)
- **definition**: Contains the actual SAIL/expression code
- **ruleInputs**: Input parameters with names and types
- **description**: Human-readable description of the rule's purpose
- **parent**: Reference to containing folder UUID

## Usage
Rules contain reusable SAIL expressions and business logic. They can be called from interfaces, process models, and other rules.

## Blueprint Context
- **Purpose**: Encapsulates business logic and calculations
- **Dependencies**: May reference constants, other rules, record types
- **Used By**: Interfaces, process models, other rules
- **Security**: Controlled via roleMap for viewing/editing permissions
