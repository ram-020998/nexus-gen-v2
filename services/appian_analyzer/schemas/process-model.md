# Appian Process Model XML Schema

## XML Structure
```xml
<processModel xmlns="http://www.appian.com/ae/types/2009">
  <versionUuid>uuid-string</versionUuid>
  <ixObject>
    <uuid>pm-uuid</uuid>
    <name>Process Model Name</name>
    <description>Description</description>
    <processVariables>
      <processVariable>
        <name>pv!variableName</name>
        <type>Text</type>
        <parameter>true</parameter>
        <multiple>false</multiple>
      </processVariable>
    </processVariables>
    <processFlow>
      <nodes>
        <node>
          <id>0</id>
          <name>Start Node</name>
          <type>startNode</type>
          <position>
            <x>100</x>
            <y>100</y>
          </position>
        </node>
        <node>
          <id>1</id>
          <name>User Input Task</name>
          <type>userInputTask</type>
          <assignmentRule>rule!assignmentRule</assignmentRule>
          <form>rule!formInterface</form>
          <taskDisplayName>Task Name</taskDisplayName>
          <instructions>Task instructions</instructions>
          <priority>NORMAL</priority>
          <escalations>
            <escalation>
              <condition>pv!escalateAfter</condition>
              <action>rule!escalationAction</action>
            </escalation>
          </escalations>
          <position>
            <x>200</x>
            <y>100</y>
          </position>
        </node>
        <node>
          <id>2</id>
          <name>Script Task</name>
          <type>scriptTask</type>
          <expression>rule!businessLogic</expression>
          <saveInto>pv!result</saveInto>
          <position>
            <x>300</x>
            <y>100</y>
          </position>
        </node>
        <node>
          <id>3</id>
          <name>XOR Gateway</name>
          <type>xorGateway</type>
          <position>
            <x>400</x>
            <y>100</y>
          </position>
        </node>
        <node>
          <id>4</id>
          <name>Call Process</name>
          <type>callProcess</type>
          <processModel>rule!childProcessModel</processModel>
          <processParameters>
            <parameter>
              <name>childPv1</name>
              <value>pv!parentValue</value>
            </parameter>
          </processParameters>
          <position>
            <x>500</x>
            <y>100</y>
          </position>
        </node>
        <node>
          <id>5</id>
          <name>End Node</name>
          <type>endNode</type>
          <position>
            <x>600</x>
            <y>100</y>
          </position>
        </node>
      </nodes>
      <flows>
        <flow>
          <id>f1</id>
          <from>0</from>
          <to>1</to>
        </flow>
        <flow>
          <id>f2</id>
          <from>1</from>
          <to>2</to>
        </flow>
        <flow>
          <id>f3</id>
          <from>2</from>
          <to>3</to>
        </flow>
        <flow>
          <id>f4</id>
          <from>3</from>
          <to>4</to>
          <condition>pv!approved = true</condition>
          <label>Approved</label>
        </flow>
        <flow>
          <id>f5</id>
          <from>3</from>
          <to>5</to>
          <condition>pv!approved = false</condition>
          <label>Rejected</label>
        </flow>
      </flows>
    </processFlow>
    <parent>parent-folder-id</parent>
  </ixObject>
  <roleMap>
    <roleMapEntry>
      <actor type="user|group">actor-name</actor>
      <role>VIEWER|EDITOR|ADMIN|INITIATOR</role>
    </roleMapEntry>
  </roleMap>
</processModel>
```

## Key Node Types and Tags

### Start Node
```xml
<node>
  <type>startNode</type>
  <name>Start Node</name>
  <id>unique-node-id</id>
  <position><x>100</x><y>100</y></position>
</node>
```

### User Input Task
```xml
<node>
  <type>userInputTask</type>
  <assignmentRule>rule!assignmentRule</assignmentRule>
  <form>rule!formInterface</form>
  <taskDisplayName>Display Name</taskDisplayName>
  <instructions>Task instructions</instructions>
  <priority>NORMAL|HIGH|LOW</priority>
  <escalations>
    <escalation>
      <condition>expression</condition>
      <action>rule!escalationAction</action>
    </escalation>
  </escalations>
</node>
```

### Script Task
```xml
<node>
  <type>scriptTask</type>
  <expression>rule!businessLogic</expression>
  <saveInto>pv!variableName</saveInto>
</node>
```

### XOR Gateway (Decision Point)
```xml
<node>
  <type>xorGateway</type>
  <!-- Conditions defined on outgoing flows -->
</node>
```

### AND Gateway (Parallel Split/Join)
```xml
<node>
  <type>andGateway</type>
  <!-- Splits or joins parallel paths -->
</node>
```

### Call Process
```xml
<node>
  <type>callProcess</type>
  <processModel>rule!childProcessModel</processModel>
  <processParameters>
    <parameter>
      <name>childPv1</name>
      <value>pv!parentValue</value>
    </parameter>
  </processParameters>
  <synchronous>true</synchronous>
</node>
```

### Send Message
```xml
<node>
  <type>sendMessage</type>
  <messageRule>rule!messageRule</messageRule>
  <recipients>rule!getRecipients</recipients>
</node>
```

### Receive Message
```xml
<node>
  <type>receiveMessage</type>
  <messageRule>rule!messageRule</messageRule>
  <timeout>pv!timeoutDuration</timeout>
</node>
```

### Timer Event
```xml
<node>
  <type>timerEvent</type>
  <duration>pv!waitDuration</duration>
  <dateTime>pv!specificDateTime</dateTime>
</node>
```

### End Node
```xml
<node>
  <type>endNode</type>
  <name>End Node</name>
  <id>unique-node-id</id>
  <position><x>600</x><y>100</y></position>
</node>
```

## Flow Connections
```xml
<flow>
  <id>flow-id</id>
  <from>source-node-id</from>
  <to>target-node-id</to>
  <condition>pv!condition = true</condition>
  <label>Flow Label</label>
</flow>
```

## Common Node Properties
- **id**: Unique identifier within the process
- **name**: Display name of the node
- **type**: Node type (determines behavior)
- **position**: X,Y coordinates for visual layout
- **condition**: Flow conditions for gateways
- **assignmentRule**: Who gets assigned tasks
- **form**: Interface used for user tasks

## Usage
Process models define automated workflows with various node types for different behaviors: user tasks, automated scripts, decision points, parallel processing, and external integrations.

## Blueprint Context
- **Purpose**: Defines business process workflows and automation
- **Dependencies**: References interfaces (forms), rules, constants, record types, other process models
- **Used By**: Can be started by users, other processes, or integrations
- **Security**: Controlled via roleMap including initiator permissions
- **Flow Logic**: Nodes connected by flows with conditional routing
