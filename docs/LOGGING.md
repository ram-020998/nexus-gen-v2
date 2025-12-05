# NexusGen Logging System

## Overview

NexusGen uses a centralized logging system that provides comprehensive logging for all application components, with special focus on the three-way merge assistant workflow.

## Log Files

All log files are stored in the `logs/` directory:

- **nexusgen.log** - Main application log (all components)
- **merge_assistant.log** - Detailed merge assistant workflow logs
- **settings_service.log** - Settings service logs

Each log file uses rotation to prevent disk space issues:
- Maximum file size: 10MB
- Backup count: 5 files
- Total maximum storage per log: ~50MB

## Log Format

### Detailed Format (File Logs)
```
2024-01-15 10:30:45,123 - merge_assistant - INFO - [orchestrator.py:125] - create_merge_session() - Starting three-way merge workflow
```

Components:
- Timestamp with milliseconds
- Logger name (module)
- Log level (DEBUG, INFO, WARNING, ERROR)
- Source file and line number
- Function name
- Log message

### Simple Format (Console)
```
2024-01-15 10:30:45,123 - INFO - Starting three-way merge workflow
```

## Usage

### Basic Logging

```python
from core.logger import LoggerConfig

# Get a logger for your module
logger = LoggerConfig.get_logger(__name__)

# Log messages
logger.debug("Detailed debug information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

### Merge Assistant Logging

```python
from core.logger import get_merge_logger

# Get merge-specific logger
logger = get_merge_logger()

logger.info("Starting merge session")
```

### Structured Logging Helpers

#### Function Entry/Exit
```python
from core.logger import LoggerConfig

logger = LoggerConfig.get_logger(__name__)

# Log function entry with parameters
LoggerConfig.log_function_entry(
    logger,
    'process_package',
    package_id=123,
    package_type='base'
)

# ... function logic ...

# Log function exit with result
LoggerConfig.log_function_exit(
    logger,
    'process_package',
    result='Processed 42 objects'
)
```

#### Workflow Steps
```python
# Log workflow step with progress
LoggerConfig.log_step(
    logger,
    step_number=3,
    total_steps=8,
    description='Extracting Package B'
)
```

#### Visual Separators
```python
# Log separator line
LoggerConfig.log_separator(logger)  # Uses "="
LoggerConfig.log_separator(logger, char="-")  # Uses "-"
```

#### Error Logging with Context
```python
try:
    process_package(package_id=123)
except Exception as e:
    LoggerConfig.log_error_with_context(
        logger,
        e,
        'Processing package',
        package_id=123,
        package_type='base'
    )
```

#### Performance Logging
```python
import time

start_time = time.time()
# ... operation ...
duration = time.time() - start_time

LoggerConfig.log_performance(
    logger,
    'Package Extraction',
    duration_seconds=duration,
    objects_processed=150,
    files_parsed=75
)
```

## Three-Way Merge Workflow Logging

The merge assistant provides extensive logging at each step:

### Step 1: Session Creation
```
================================================================================
THREE-WAY MERGE WORKFLOW STARTING
================================================================================
→ Entering create_merge_session(base_zip_path=..., customized_zip_path=..., new_vendor_zip_path=...)
Step 1/8: Creating merge session record
✓ Session created: MS_A1B2C3 (id=1) in 0.05s
```

### Step 2-4: Package Extraction
```
Step 2/8: Extracting Package A (Base Version)
✓ Package A extracted: 150 objects in 12.34s
Object type breakdown for base package:
  - Interface: 45
  - Process Model: 30
  - Record Type: 25
  ...
```

### Step 5: Delta Comparison
```
Step 5/8: Performing delta comparison (A→C)
✓ Delta comparison complete: 42 changes detected in 3.21s
```

### Step 6: Customer Comparison
```
Step 6/8: Performing customer comparison (delta vs B)
✓ Customer comparison complete: 42 objects analyzed in 2.15s
```

### Step 7: Classification
```
Step 7/8: Classifying changes (applying 7 classification rules)
✓ Classification complete: 42 changes classified in 1.05s
Classification breakdown:
  - CONFLICT: 15
  - NEW: 10
  - NO_CONFLICT: 12
  - DELETED: 5
```

### Step 8: Guidance Generation
```
Step 8/8: Generating merge guidance
✓ Guidance generation complete: 42 guidance records in 0.85s
```

### Workflow Completion
```
================================================================================
THREE-WAY MERGE WORKFLOW COMPLETED SUCCESSFULLY
================================================================================
Session Reference ID: MS_A1B2C3
Session Status: ready
Total Changes: 42
Performance: Three-Way Merge Workflow completed in 25.67s | Metrics: session_id=1, reference_id=MS_A1B2C3, total_changes=42, package_a_objects=150, package_b_objects=155, package_c_objects=160
================================================================================
← Exiting create_merge_session: Session MS_A1B2C3 with 42 changes
```

### Error Handling
```
--------------------------------------------------------------------------------
THREE-WAY MERGE WORKFLOW FAILED
--------------------------------------------------------------------------------
Error during Three-way merge workflow: Failed to extract package | Context: session_id=1, reference_id=MS_A1B2C3, base_zip_path=..., workflow_duration=5.23s
[Full stack trace]
--------------------------------------------------------------------------------
```

## Log Levels

- **DEBUG**: Detailed diagnostic information (function entry/exit, variable values)
- **INFO**: General informational messages (workflow steps, completion)
- **WARNING**: Warning messages (non-critical issues, skipped files)
- **ERROR**: Error messages (failures, exceptions)

## Configuration

Logging is initialized in `app.py` during application startup:

```python
from core.logger import LoggerConfig

# Initialize logging
LoggerConfig.setup()
```

## Viewing Logs

### Real-time Monitoring
```bash
# Watch main application log
tail -f logs/nexusgen.log

# Watch merge assistant log
tail -f logs/merge_assistant.log

# Watch with grep filter
tail -f logs/merge_assistant.log | grep "ERROR"
```

### Search Logs
```bash
# Search for specific session
grep "MS_A1B2C3" logs/merge_assistant.log

# Search for errors
grep "ERROR" logs/nexusgen.log

# Search for performance metrics
grep "Performance:" logs/merge_assistant.log
```

## Best Practices

1. **Use appropriate log levels**
   - DEBUG for detailed diagnostics
   - INFO for workflow progress
   - WARNING for recoverable issues
   - ERROR for failures

2. **Include context in log messages**
   - Session IDs, reference IDs
   - Object counts, file names
   - Duration metrics

3. **Use structured logging helpers**
   - `log_function_entry/exit` for function boundaries
   - `log_step` for workflow progress
   - `log_error_with_context` for errors
   - `log_performance` for timing metrics

4. **Log at key decision points**
   - Before/after major operations
   - When applying business rules
   - When handling errors

5. **Don't log sensitive data**
   - No passwords or API keys
   - No PII (personally identifiable information)
   - Sanitize file paths if needed

## Troubleshooting

### Log files not created
- Check that `logs/` directory exists
- Verify write permissions
- Check disk space

### Log files too large
- Logs automatically rotate at 10MB
- 5 backup files are kept
- Old backups are automatically deleted

### Missing log entries
- Check log level configuration
- Verify logger is properly initialized
- Check for exceptions during logging

## Future Enhancements

Potential improvements to the logging system:

- JSON structured logging for machine parsing
- Log aggregation to external services (e.g., CloudWatch, Splunk)
- Real-time log streaming via WebSocket
- Log analysis dashboard
- Configurable log levels per module
- Log sampling for high-volume operations
