# Appian Connected System XML Schema

## XML Structure
```xml
<connectedSystem xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>cs-uuid</uuid>
    <name>Connected System Name</name>
    <description>Connected system description</description>
    <pluginKey>com.appian.connectedsystems.http</pluginKey>
    <templateKey>HttpConnectedSystemTemplate</templateKey>
    <configuration>
      <property>
        <key>baseUrl</key>
        <value>https://api.example.com</value>
        <encrypted>false</encrypted>
      </property>
      <property>
        <key>authentication</key>
        <value>
          <type>BASIC|OAUTH|API_KEY</type>
          <username>username</username>
          <password>encrypted-password</password>
        </value>
        <encrypted>true</encrypted>
      </property>
    </configuration>
    <parent>parent-folder-id</parent>
  </ixObject>
  <roleMap>
    <roleMapEntry>
      <actor type="user|group">actor-name</actor>
      <role>VIEWER|EDITOR|ADMIN</role>
    </roleMapEntry>
  </roleMap>
</connectedSystem>
```

## Key Tags
- **name**: Connected system identifier
- **pluginKey**: Plugin that provides the connected system functionality
- **templateKey**: Template used for the connected system
- **configuration**: Connection settings and authentication details
- **encrypted**: Indicates if property values are encrypted

## Usage
Connected systems define connections to external systems and services for integrations.

## Blueprint Context
- **Purpose**: Defines external system connections and authentication
- **Dependencies**: May reference constants for configuration values
- **Used By**: Integrations for external API calls
- **Security**: Contains encrypted authentication credentials
