# Appian Report XML Schema

## XML Structure
```xml
<report xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>report-uuid</uuid>
    <name>Report Name</name>
    <description>Report description</description>
    <reportType>PROCESS|TASK|CUSTOM</reportType>
    <dataSource>
      <database>
        <dataSourceName>datasource_name</dataSourceName>
      </database>
    </dataSource>
    <columns>
      <column>
        <name>columnName</name>
        <displayName>Display Name</displayName>
        <type>Text</type>
        <sortable>true</sortable>
      </column>
    </columns>
    <filters>
      <filter>
        <name>filterName</name>
        <type>Text</type>
        <operator>EQUALS</operator>
      </filter>
    </filters>
    <parent>parent-folder-id</parent>
  </ixObject>
  <roleMap>
    <roleMapEntry>
      <actor type="user|group">actor-name</actor>
      <role>VIEWER|EDITOR|ADMIN</role>
    </roleMapEntry>
  </roleMap>
</report>
```

## Key Tags
- **name**: Report identifier
- **reportType**: Type of report (PROCESS, TASK, CUSTOM)
- **dataSource**: Database connection information
- **columns**: Report column definitions with display properties
- **filters**: Available filters for the report
- **description**: Human-readable description of the report's purpose

## Usage
Reports provide data visualization and analytics capabilities, often used for process monitoring and business intelligence.

## Blueprint Context
- **Purpose**: Provides data visualization and reporting capabilities
- **Dependencies**: Requires database connections, may reference process models
- **Used By**: Interfaces, dashboards for data display
- **Security**: Controlled via roleMap for viewing/editing permissions
