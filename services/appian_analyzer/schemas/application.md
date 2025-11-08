# Appian Application XML Schema

## XML Structure
```xml
<application xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>app-uuid</uuid>
    <name>Application Name</name>
    <description>Application description</description>
    <version>1.0.0</version>
    <applicationObjects>
      <applicationObject>
        <uuid>object-uuid</uuid>
        <type>RULE|INTERFACE|PROCESS_MODEL|RECORD_TYPE</type>
        <name>objectName</name>
      </applicationObject>
    </applicationObjects>
    <precedence>
      <precedenceEntry>
        <uuid>object-uuid</uuid>
        <precedence>1</precedence>
      </precedenceEntry>
    </precedence>
    <parent>parent-folder-id</parent>
  </ixObject>
  <roleMap>
    <roleMapEntry>
      <actor type="user|group">actor-name</actor>
      <role>VIEWER|EDITOR|ADMIN</role>
    </roleMapEntry>
  </roleMap>
</application>
```

## Key Tags
- **name**: Application identifier
- **version**: Application version number
- **applicationObjects**: List of objects included in the application
- **precedence**: Object precedence for deployment ordering
- **description**: Human-readable description of the application

## Usage
Applications group related objects together for deployment and management purposes.

## Blueprint Context
- **Purpose**: Groups and manages related objects as a deployable unit
- **Dependencies**: Contains references to multiple object types
- **Used By**: Deployment processes, application management
- **Security**: Controlled via roleMap for application management permissions
