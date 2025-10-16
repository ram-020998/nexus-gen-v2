# NexusGen Troubleshooting Guide

## Spec Breakdown Issues - Fixed (Oct 16, 2025)

### Problems Identified:
1. **Missing DATA_SOURCE Configuration**: `DataSourceFactory` couldn't access `Config.DATA_SOURCE`
2. **JSON Parsing Errors**: Q agent returning malformed JSON causing decode failures
3. **Service Initialization**: RequestService failing to initialize due to config issues

### Solutions Applied:

#### 1. Fixed DataSourceFactory
```python
# services/data_source_factory.py
data_source = getattr(Config, 'DATA_SOURCE', 'BEDROCK')  # Added fallback
```

#### 2. Enhanced Q Agent Error Handling
```python
# services/q_agent_service.py - process_breakdown()
try:
    with open(output_path, 'r') as f:
        content = f.read().strip()
        if content:
            return json.loads(content)
        else:
            return self._generate_fallback_breakdown()
except json.JSONDecodeError as e:
    print(f"JSON decode error: {e}")
    return self._generate_fallback_breakdown()
```

### Current Configuration Status:
- ✅ Q CLI Agent: v1.18.1 working
- ✅ Breakdown Agent: Configured with fs_read/fs_write tools
- ✅ Bedrock KB: ID `WAQ6NJLGKN` active
- ✅ Data Sources: Factory pattern functional
- ✅ JSON Generation: Proper breakdown structure

### Test Results:
Successfully generated breakdown for User Management System spec:
- Epic: "User Management System"
- 8 User Stories with GIVEN/WHEN/THEN format
- Proper JSON structure saved to outputs/

### Key Files Modified:
- `services/data_source_factory.py`
- `services/q_agent_service.py`

### Monitoring Points:
1. AWS credentials for Bedrock API
2. Q agent JSON output validation
3. File upload size/type limits
4. Performance with large documents
