# Appian Integration XML Schema

## XML Structure
```xml
<outboundIntegration xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>integration-uuid</uuid>
    <name>integrationName</name>
    <description>Integration description</description>
    <endpointUrl>https://api.example.com/endpoint</endpointUrl>
    <httpMethod>GET|POST|PUT|DELETE</httpMethod>
    <requestHeaders>
      <header>
        <name>Content-Type</name>
        <value>application/json</value>
      </header>
    </requestHeaders>
    <requestBody>JSON or XML request body</requestBody>
    <ruleInputs>
      <ruleInput>
        <name>inputName</name>
        <type>Text</type>
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
</outboundIntegration>
```

## Key Tags
- **name**: Integration identifier used in expressions (e.g., `rule!integrationName`)
- **endpointUrl**: Target API endpoint URL
- **httpMethod**: HTTP method (GET, POST, PUT, DELETE)
- **requestHeaders**: HTTP headers for the request
- **requestBody**: Request payload template
- **ruleInputs**: Input parameters for the integration

## Usage
Integrations define connections to external systems and APIs for data exchange.

## Blueprint Context
- **Purpose**: Connects Appian to external systems and services
- **Dependencies**: May reference constants for configuration, rules for data transformation
- **Used By**: Rules, process models, interfaces for external data operations
- **Security**: Controlled via roleMap and may include authentication configuration
