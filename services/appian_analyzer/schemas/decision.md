# Appian Decision XML Schema

## XML Structure
```xml
<decision xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>decision-uuid</uuid>
    <name>decisionName</name>
    <description>Decision description</description>
    <decisionTable>
      <inputs>
        <input>
          <name>inputName</name>
          <type>Text</type>
        </input>
      </inputs>
      <outputs>
        <output>
          <name>outputName</name>
          <type>Text</type>
        </output>
      </outputs>
      <rules>
        <rule>
          <conditions>
            <condition>input1 = "value"</condition>
          </conditions>
          <results>
            <result>"output value"</result>
          </results>
        </rule>
      </rules>
    </decisionTable>
    <parent>parent-folder-id</parent>
  </ixObject>
  <roleMap>
    <roleMapEntry>
      <actor type="user|group">actor-name</actor>
      <role>VIEWER|EDITOR|ADMIN</role>
    </roleMapEntry>
  </roleMap>
</decision>
```

## Key Tags
- **name**: Decision identifier used in expressions (e.g., `rule!decisionName`)
- **decisionTable**: Contains the decision logic structure
- **inputs**: Input parameters for the decision
- **outputs**: Output values from the decision
- **rules**: Decision rules with conditions and results

## Usage
Decisions define business rules using decision tables for complex conditional logic.

## Blueprint Context
- **Purpose**: Encapsulates complex business decision logic
- **Dependencies**: May reference constants, other rules, data types
- **Used By**: Rules, interfaces, process models for decision-making
- **Security**: Controlled via roleMap for viewing/editing permissions
