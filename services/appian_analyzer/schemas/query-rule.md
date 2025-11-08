# Appian Query Rule XML Schema

## XML Structure
```xml
<queryRule xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>query-uuid</uuid>
    <name>queryRuleName</name>
    <description>Query rule description</description>
    <definition>Query expression code</definition>
    <dataSource>
      <database>
        <dataSourceName>datasource_name</dataSourceName>
      </database>
    </dataSource>
    <ruleInputs>
      <ruleInput>
        <name>inputName</name>
        <type>Text</type>
        <multiple>false</multiple>
      </ruleInput>
    </ruleInputs>
    <parent>parent-folder-id</parent>
  </ixObject>
  <roleMap>
    <roleMapEntry>
      <actor type="user|group">actor-name</actor>
      <role>VIEWER|EDITOR|ADMIN</role>
    </roleMapEntry>
  </roleMap>
</queryRule>
```

## Key Tags
- **name**: Query rule identifier used in expressions (e.g., `rule!myQuery`)
- **definition**: Contains the query expression code
- **dataSource**: Database connection information
- **ruleInputs**: Input parameters for the query
- **description**: Human-readable description of the query's purpose

## Usage
Query rules contain database queries and data retrieval logic. They are used to fetch data from databases.

## Blueprint Context
- **Purpose**: Encapsulates database queries and data access logic
- **Dependencies**: Requires database connections, may reference constants
- **Used By**: Rules, interfaces, process models for data retrieval
- **Security**: Controlled via roleMap for viewing/editing permissions
