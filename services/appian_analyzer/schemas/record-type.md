# Appian Record Type XML Schema

## XML Structure
```xml
<recordType xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>rt-uuid</uuid>
    <name>Record Type Name</name>
    <description>Description</description>
    <dataSource>
      <database>
        <tableName>table_name</tableName>
        <schema>schema_name</schema>
        <dataSourceName>datasource_name</dataSourceName>
      </database>
    </dataSource>
    <recordFields>
      <recordField>
        <name>fieldName</name>
        <type>Text</type>
        <required>true</required>
        <primaryKey>false</primaryKey>
        <unique>false</unique>
        <columnName>db_column_name</columnName>
      </recordField>
    </recordFields>
    <relationships>
      <relationship>
        <name>relatedRecords</name>
        <relatedRecordType>uuid-of-related-rt</relatedRecordType>
        <type>oneToMany|manyToOne|oneToOne</type>
        <foreignKey>foreign_key_field</foreignKey>
      </relationship>
    </relationships>
    <recordActions>
      <recordAction>
        <name>actionName</name>
        <type>CREATE|UPDATE|DELETE</type>
        <interface>rule!actionInterface</interface>
      </recordAction>
    </recordActions>
    <recordViews>
      <recordView>
        <name>viewName</name>
        <type>LIST|SUMMARY|FORM</type>
        <interface>rule!viewInterface</interface>
      </recordView>
    </recordViews>
    <parent>parent-folder-id</parent>
  </ixObject>
  <roleMap>
    <roleMapEntry>
      <actor type="user|group">actor-name</actor>
      <role>VIEWER|EDITOR|ADMIN</role>
    </roleMapEntry>
  </roleMap>
</recordType>
```

## Key Tags
- **name**: Record type identifier used in expressions (e.g., `recordType!Customer`)
- **dataSource**: Database connection and table information
- **recordFields**: Field definitions with types and constraints
- **relationships**: Connections to other record types
- **description**: Human-readable description of the data entity

## Usage
Record types define data entities and their structure. They provide the foundation for data operations and user interfaces.

## Blueprint Context
- **Purpose**: Defines data model and database structure
- **Dependencies**: May reference other record types through relationships
- **Used By**: Interfaces, rules, process models for data operations
- **Security**: Controlled via roleMap for data access permissions
