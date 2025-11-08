# Appian Folder XML Schema

## XML Structure
```xml
<folder xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>folder-uuid</uuid>
    <name>Folder Name</name>
    <description>Folder description</description>
    <parent>parent-folder-id</parent>
  </ixObject>
  <roleMap>
    <roleMapEntry>
      <actor type="user|group">actor-name</actor>
      <role>VIEWER|EDITOR|ADMIN</role>
    </roleMapEntry>
  </roleMap>
</folder>
```

## Key Tags
- **name**: Folder name as displayed in Appian
- **description**: Human-readable description of the folder's purpose
- **parent**: Reference to parent folder UUID (null for root folders)

## Usage
Folders organize other Appian objects in a hierarchical structure for better management and security.

## Blueprint Context
- **Purpose**: Organizes and groups related objects
- **Dependencies**: None (organizational structure)
- **Contains**: Other folders, rules, constants, interfaces, process models, etc.
- **Security**: Controlled via roleMap, inherited by contained objects
