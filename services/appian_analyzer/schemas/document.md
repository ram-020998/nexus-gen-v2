# Appian Document XML Schema

## XML Structure
```xml
<document xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>doc-uuid</uuid>
    <name>Document Name</name>
    <description>Document description</description>
    <extension>pdf|docx|xlsx|txt</extension>
    <size>12345</size>
    <parent>parent-folder-id</parent>
  </ixObject>
  <resourceName>file</resourceName>
  <roleMap>
    <roleMapEntry>
      <actor type="user|group">actor-name</actor>
      <role>VIEWER|EDITOR|ADMIN</role>
    </roleMapEntry>
  </roleMap>
</document>
```

## Key Tags
- **name**: Document name as displayed in Appian
- **extension**: File type (pdf, docx, xlsx, txt, etc.)
- **size**: File size in bytes
- **resourceName**: Points to the actual binary file in the export package
- **parent**: Reference to containing folder UUID

## Usage
Documents store binary files that can be used in interfaces, process models, and integrations.

## Blueprint Context
- **Purpose**: Stores binary files and attachments
- **Dependencies**: None (leaf objects)
- **Used By**: Interfaces (for display), process models (as attachments), integrations
- **Security**: Controlled via roleMap for file access permissions
- **Binary Data**: Actual file content stored separately in export package
