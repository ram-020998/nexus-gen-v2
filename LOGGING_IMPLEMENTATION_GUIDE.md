# Logging Implementation Guide for Appian Analyzer

## Overview

A comprehensive logging system has been created for the Appian Analyzer feature. This guide shows how to integrate it into the existing codebase.

## Logger Features

### 1. Structured Logging
- **DEBUG** - Detailed diagnostic information
- **INFO** - General informational messages
- **WARNING** - Warning messages for potential issues
- **ERROR** - Error messages with optional stack traces
- **CRITICAL** - Critical failures

### 2. File Rotation
- Log files automatically rotate at 10MB
- Keeps 5 backup files
- Location: `logs/appian_analyzer.log`

### 3. Request Tracking
- Each comparison request gets a unique logger
- All log messages automatically tagged with request ID
- Easy to trace a specific request through the logs

### 4. Dual Output
- **File:** Detailed logs with full context (DEBUG level)
- **Console:** Important messages only (INFO level and above)

## Implementation Examples

### Example 1: Comparison Service

**Before (using print):**
```python
def process_comparison(self, old_zip_path: str, new_zip_path: str):
    print(f"🔍 Analyzing {old_app_name}...")
    old_result = old_analyzer.analyze()
    
    print(f"🔍 Analyzing {new_app_name}...")
    new_result = new_analyzer.analyze()
    
    print("✨ Using enhanced dual-layer comparison system")
    comparison = enhanced_service.compare_applications(...)
    
    print(f"📊 Found {total_changes} changes")
```

**After (using logger):**
```python
from services.appian_analyzer.logger import create_request_logger

def process_comparison(self, old_zip_path: str, new_zip_path: str):
    # Create request and logger
    request = self.request_manager.create_request(old_app_name, new_app_name)
    logger = create_request_logger(request.reference_id)
    
    try:
        logger.info(f"Starting comparison: {old_app_name} vs {new_app_name}")
        logger.log_stage("Upload", {
            "old_file": old_zip_path,
            "new_file": new_zip_path,
            "old_size": Path(old_zip_path).stat().st_size,
            "new_size": Path(new_zip_path).stat().st_size
        })
        
        # Analyze old version
        logger.log_stage("Analyzing old version", {"app": old_app_name})
        old_analyzer = AppianAnalyzer(old_zip_path)
        old_result = old_analyzer.analyze()
        logger.info(f"Old version analyzed: {old_result['blueprint']['metadata']['total_objects']} objects")
        
        # Analyze new version
        logger.log_stage("Analyzing new version", {"app": new_app_name})
        new_analyzer = AppianAnalyzer(new_zip_path)
        new_result = new_analyzer.analyze()
        logger.info(f"New version analyzed: {new_result['blueprint']['metadata']['total_objects']} objects")
        
        # Perform comparison
        logger.log_stage("Comparison", {"method": "enhanced"})
        enhanced_service = EnhancedComparisonService()
        comparison = enhanced_service.compare_applications(
            old_result, new_result, old_app_name, new_app_name
        )
        
        total_changes = comparison.get('comparison_summary', {}).get('total_changes', 0)
        logger.log_metrics({
            "total_changes": total_changes,
            "impact_level": comparison.get('comparison_summary', {}).get('impact_level', 'UNKNOWN')
        })
        
        # Save results
        processing_time = int(time.time() - start_time)
        self.request_manager.save_results(...)
        
        logger.log_completion(
            status='success',
            total_changes=total_changes,
            processing_time=f"{processing_time}s"
        )
        
        return request
        
    except Exception as e:
        logger.error(f"Comparison failed: {str(e)}", exc_info=True)
        self.request_manager.update_status(request.id, 'error', str(e))
        raise
```

### Example 2: Analyzer Controller

**Before:**
```python
@analyzer_bp.route('/analyzer/compare', methods=['POST'])
def compare_versions():
    print("DEBUG: Compare request received")
    print(f"DEBUG: Old file: {old_file.filename}")
    print(f"DEBUG: New file: {new_file.filename}")
```

**After:**
```python
from services.appian_analyzer.logger import get_logger

logger = get_logger()

@analyzer_bp.route('/analyzer/compare', methods=['POST'])
def compare_versions():
    """Compare two application versions"""
    logger.info("Comparison request received")
    
    if 'old_file' not in request.files or 'new_file' not in request.files:
        logger.warning("Missing files in request")
        flash('Please select both files for comparison', 'error')
        return redirect(url_for('analyzer.analyzer_home'))
    
    old_file = request.files['old_file']
    new_file = request.files['new_file']
    
    logger.info(f"Files received: {old_file.filename} vs {new_file.filename}")
    
    if not (old_file.filename and new_file.filename and 
            allowed_file(old_file.filename) and allowed_file(new_file.filename)):
        logger.warning("File validation failed")
        flash('Please select valid ZIP files', 'error')
        return redirect(url_for('analyzer.analyzer_home'))
    
    try:
        # Save files
        old_path = Path('uploads') / secure_filename(old_file.filename)
        new_path = Path('uploads') / secure_filename(new_file.filename)
        
        old_path.parent.mkdir(exist_ok=True)
        old_file.save(old_path)
        new_file.save(new_path)
        
        logger.debug(f"Files saved: {old_path} ({old_path.stat().st_size} bytes), "
                    f"{new_path} ({new_path.stat().st_size} bytes)")
        
        # Process comparison
        comparison_request = comparison_service.process_comparison(str(old_path), str(new_path))
        logger.info(f"Comparison completed: {comparison_request.reference_id}")
        
        # Clean up
        old_path.unlink(missing_ok=True)
        new_path.unlink(missing_ok=True)
        logger.debug("Temporary files cleaned up")
        
        flash(f'Comparison completed successfully! Request ID: {comparison_request.reference_id}', 'success')
        
    except Exception as e:
        logger.error(f"Comparison failed: {str(e)}", exc_info=True)
        flash(f'Comparison failed: {str(e)}', 'error')
        
        # Clean up on error
        if 'old_path' in locals():
            old_path.unlink(missing_ok=True)
        if 'new_path' in locals():
            new_path.unlink(missing_ok=True)
    
    return redirect(url_for('analyzer.analyzer_home'))
```

### Example 3: Enhanced Comparison Service

**Add logging to track comparison stages:**

```python
from services.appian_analyzer.logger import get_logger

class EnhancedComparisonService:
    def __init__(self):
        self.comparator = EnhancedVersionComparator()
        self.report_generator = ComparisonReportGenerator()
        self.compatibility_layer = WebCompatibilityLayer()
        self.logger = get_logger()
    
    def compare_applications(self, result1, result2, version1_name, version2_name):
        self.logger.info(f"Enhanced comparison: {version1_name} vs {version2_name}")
        
        # Get object lookups
        lookup1 = result1.get("object_lookup", {})
        lookup2 = result2.get("object_lookup", {})
        
        self.logger.debug(f"Object counts: {len(lookup1)} vs {len(lookup2)}")
        
        if not lookup1 or not lookup2:
            self.logger.error("Object lookup data not available")
            raise ValueError("Object lookup data not available")
        
        # Convert lookups
        self.logger.debug("Converting lookups to objects")
        objects1 = self._convert_lookup_to_objects(lookup1)
        objects2 = self._convert_lookup_to_objects(lookup2)
        
        # Perform comparison
        self.logger.debug("Performing dual-layer comparison")
        comparison_results = self.comparator.compare_by_uuid(objects1, objects2)
        
        # Generate report
        self.logger.debug("Generating comparison report")
        enhanced_report = self.report_generator.generate_report(
            comparison_results, version1_name, version2_name
        )
        
        # Convert to compatible format
        self.logger.debug("Converting to web-compatible format")
        compatible_result = self.compatibility_layer.to_compatible_format(enhanced_report)
        
        # Log summary
        summary = compatible_result.get('comparison_summary', {})
        self.logger.info(f"Comparison complete: {summary.get('total_changes', 0)} changes, "
                        f"impact: {summary.get('impact_level', 'UNKNOWN')}")
        
        return compatible_result
```

## Log Output Examples

### Console Output (INFO level)
```
18:30:15 | INFO     | [CMP_012] Starting comparison: SourceSelectionv2.4.0 vs SourceSelectionv2.6.0
18:30:15 | INFO     | [CMP_012] Stage: Upload | old_file=uploads/SourceSelectionv2.4.0.zip, new_file=uploads/SourceSelectionv2.6.0.zip
18:30:16 | INFO     | [CMP_012] Stage: Analyzing old version | app=SourceSelectionv2.4.0
18:30:17 | INFO     | [CMP_012] Old version analyzed: 1156 objects
18:30:17 | INFO     | [CMP_012] Stage: Analyzing new version | app=SourceSelectionv2.6.0
18:30:18 | INFO     | [CMP_012] New version analyzed: 1157 objects
18:30:18 | INFO     | [CMP_012] Stage: Comparison | method=enhanced
18:30:19 | INFO     | [CMP_012] Metrics: total_changes=261, impact_level=VERY_HIGH
18:30:19 | INFO     | [CMP_012] Completed: status=success, total_changes=261, processing_time=4.2s
```

### File Output (DEBUG level)
```
2025-11-21 18:30:15 | DEBUG    | appian_analyzer | process_comparison:285 | [CMP_012] Files saved: uploads/SourceSelectionv2.4.0.zip (2.3 MB), uploads/SourceSelectionv2.6.0.zip (2.4 MB)
2025-11-21 18:30:16 | DEBUG    | appian_analyzer | analyze:145 | [CMP_012] Parsing XML files from ZIP
2025-11-21 18:30:16 | DEBUG    | appian_analyzer | analyze:167 | [CMP_012] Parsed 1156 objects
2025-11-21 18:30:17 | DEBUG    | appian_analyzer | compare_applications:45 | [CMP_012] Converting lookups to objects
2025-11-21 18:30:17 | DEBUG    | appian_analyzer | _convert_lookup_to_objects:98 | [CMP_012] Created SimpleObject for AS_GSS_HCL_vendorsTab (Interface)
2025-11-21 18:30:18 | DEBUG    | appian_analyzer | compare_by_uuid:312 | [CMP_012] Comparing 2313 objects
2025-11-21 18:30:18 | DEBUG    | appian_analyzer | compare_objects:78 | [CMP_012] Object AS_GSS_HCL_vendorsTab: status=CHANGED
2025-11-21 18:30:19 | INFO     | appian_analyzer | compare_applications:67 | [CMP_012] Comparison complete: 261 changes, impact: VERY_HIGH
2025-11-21 18:30:19 | DEBUG    | appian_analyzer | process_comparison:325 | [CMP_012] Temporary files cleaned up
```

## Benefits

### 1. Better Debugging
- Trace exact flow of each request
- See timing information for each stage
- Identify bottlenecks and errors quickly

### 2. Production Monitoring
- Track request success/failure rates
- Monitor processing times
- Identify patterns in errors

### 3. Audit Trail
- Complete history of all comparisons
- Who uploaded what and when
- What changes were detected

### 4. Performance Analysis
- See which stages take longest
- Identify optimization opportunities
- Track improvements over time

### 5. Error Diagnosis
- Full stack traces in log files
- Context about what was being processed
- Easy to reproduce issues

## Log File Management

### Location
```
logs/
├── appian_analyzer.log         # Current log
├── appian_analyzer.log.1       # Previous rotation
├── appian_analyzer.log.2       # Older rotation
├── appian_analyzer.log.3
├── appian_analyzer.log.4
└── appian_analyzer.log.5       # Oldest (will be deleted on next rotation)
```

### Rotation Policy
- **Size trigger:** 10MB per file
- **Backup count:** 5 files
- **Total storage:** ~50MB maximum

### Viewing Logs
```bash
# View latest logs
tail -f logs/appian_analyzer.log

# View last 100 lines
tail -100 logs/appian_analyzer.log

# Search for specific request
grep "CMP_012" logs/appian_analyzer.log

# Search for errors
grep "ERROR" logs/appian_analyzer.log

# View all logs including rotated
cat logs/appian_analyzer.log* | grep "CMP_012"
```

## Integration Steps

### Step 1: Update comparison_service.py

Replace all `print()` statements with logger calls:

```python
from services.appian_analyzer.logger import create_request_logger

class ComparisonService:
    def process_comparison(self, old_zip_path: str, new_zip_path: str):
        start_time = time.time()
        
        # Extract app names
        old_app_name = Path(old_zip_path).stem
        new_app_name = Path(new_zip_path).stem
        
        # Create request
        request = self.request_manager.create_request(old_app_name, new_app_name)
        
        # Create request-specific logger
        logger = create_request_logger(request.reference_id)
        
        try:
            logger.info(f"Starting comparison: {old_app_name} vs {new_app_name}")
            logger.log_stage("Upload", {
                "old_file": old_zip_path,
                "new_file": new_zip_path
            })
            
            # Analyze old version
            logger.log_stage("Analyzing old version")
            old_analyzer = AppianAnalyzer(old_zip_path)
            old_result = old_analyzer.analyze()
            logger.info(f"Old version: {old_result['blueprint']['metadata']['total_objects']} objects")
            
            # Analyze new version
            logger.log_stage("Analyzing new version")
            new_analyzer = AppianAnalyzer(new_zip_path)
            new_result = new_analyzer.analyze()
            logger.info(f"New version: {new_result['blueprint']['metadata']['total_objects']} objects")
            
            # Perform comparison
            if ENHANCED_COMPARISON_AVAILABLE:
                logger.log_stage("Comparison", {"method": "enhanced"})
                try:
                    enhanced_service = EnhancedComparisonService()
                    comparison = enhanced_service.compare_applications(
                        old_result, new_result, old_app_name, new_app_name
                    )
                except Exception as enhanced_error:
                    logger.warning(f"Enhanced comparison failed: {str(enhanced_error)}")
                    logger.info("Falling back to basic comparison")
                    engine = ComparisonEngine(old_app_name, new_app_name)
                    comparison = engine.compare_results(old_result, new_result)
            else:
                logger.log_stage("Comparison", {"method": "basic"})
                comparator = AppianVersionComparator(old_zip_path, new_zip_path)
                comparison = comparator.compare_versions()
            
            total_changes = comparison.get('comparison_summary', {}).get('total_changes', 0)
            logger.log_metrics({
                "total_changes": total_changes,
                "impact_level": comparison.get('comparison_summary', {}).get('impact_level', 'UNKNOWN')
            })
            
            # Save results
            processing_time = int(time.time() - start_time)
            self.request_manager.save_results(
                request.id, old_result["blueprint"], new_result["blueprint"], 
                comparison, processing_time
            )
            
            logger.log_completion(
                status='success',
                total_changes=total_changes,
                processing_time=f"{processing_time}s"
            )
            
            return request
            
        except Exception as e:
            logger.error(f"Comparison failed: {str(e)}", exc_info=True)
            self.request_manager.update_status(request.id, 'error', str(e))
            raise
```

### Step 2: Update analyzer_controller.py

```python
from services.appian_analyzer.logger import get_logger

logger = get_logger()

@analyzer_bp.route('/analyzer/compare', methods=['POST'])
def compare_versions():
    """Compare two application versions"""
    logger.info("Comparison request received via web interface")
    
    if 'old_file' not in request.files or 'new_file' not in request.files:
        logger.warning("Missing files in upload request")
        flash('Please select both files for comparison', 'error')
        return redirect(url_for('analyzer.analyzer_home'))
    
    old_file = request.files['old_file']
    new_file = request.files['new_file']
    
    logger.info(f"Files: {old_file.filename} vs {new_file.filename}")
    
    if not (old_file.filename and new_file.filename and 
            allowed_file(old_file.filename) and allowed_file(new_file.filename)):
        logger.warning(f"File validation failed: {old_file.filename}, {new_file.filename}")
        flash('Please select valid ZIP files', 'error')
        return redirect(url_for('analyzer.analyzer_home'))
    
    try:
        # Save files
        old_path = Path('uploads') / secure_filename(old_file.filename)
        new_path = Path('uploads') / secure_filename(new_file.filename)
        
        old_path.parent.mkdir(exist_ok=True)
        old_file.save(old_path)
        new_file.save(new_path)
        
        logger.debug(f"Files saved to {old_path} and {new_path}")
        
        # Process comparison (this will create its own request logger)
        comparison_request = comparison_service.process_comparison(str(old_path), str(new_path))
        
        # Clean up
        old_path.unlink(missing_ok=True)
        new_path.unlink(missing_ok=True)
        
        flash(f'Comparison completed successfully! Request ID: {comparison_request.reference_id}', 'success')
        
    except Exception as e:
        logger.error(f"Comparison request failed: {str(e)}", exc_info=True)
        flash(f'Comparison failed: {str(e)}', 'error')
        
        # Clean up on error
        if 'old_path' in locals():
            old_path.unlink(missing_ok=True)
        if 'new_path' in locals():
            new_path.unlink(missing_ok=True)
    
    return redirect(url_for('analyzer.analyzer_home'))
```

### Step 3: Update Enhanced Version Comparator

Add logging for comparison decisions:

```python
from services.appian_analyzer.logger import get_logger

class EnhancedVersionComparator:
    def __init__(self):
        self.diff_hash_generator = DiffHashGenerator()
        self.version_history_extractor = VersionHistoryExtractor()
        self.logger = get_logger()
    
    def compare_objects(self, obj1, obj2):
        # Log comparison for important objects
        if obj1 and obj2:
            self.logger.debug(f"Comparing {obj2.name} ({obj2.object_type})")
        
        # ... comparison logic ...
        
        # Log status determination
        if status == ImportChangeStatus.NOT_CHANGED_NEW_VUUID:
            self.logger.debug(f"{obj2.name}: Version changed but content identical")
        elif status == ImportChangeStatus.CONFLICT_DETECTED:
            self.logger.warning(f"{obj2.name}: Version conflict detected")
        
        return ComparisonResult(...)
```

## Log Message Guidelines

### What to Log

**INFO Level:**
- Request start/completion
- Major processing stages
- Summary metrics (objects processed, changes found)
- Success/failure status

**DEBUG Level:**
- Detailed processing steps
- Object-level operations
- Data transformations
- File operations

**WARNING Level:**
- Fallback to basic comparison
- Missing optional data
- Potential issues that don't stop processing

**ERROR Level:**
- Exceptions and failures
- Data validation errors
- Processing errors

### What NOT to Log

- ❌ Sensitive data (passwords, tokens)
- ❌ Full SAIL code content (too large)
- ❌ Complete XML content (too large)
- ❌ Excessive detail in loops (log summaries instead)

### Log Message Format

**Good:**
```python
logger.info(f"Comparison complete: 261 changes, impact: VERY_HIGH")
logger.debug(f"Created SimpleObject for {name} ({obj_type})")
logger.error(f"Failed to parse XML: {filename}", exc_info=True)
```

**Bad:**
```python
logger.info("Done")  # Too vague
logger.debug(f"SAIL code: {full_sail_code}")  # Too much data
logger.error("Error")  # No context
```

## Testing the Logger

### Quick Test

```python
# In Python console or test script
from services.appian_analyzer.logger import create_request_logger

# Create test logger
logger = create_request_logger("TEST_001")

# Test different levels
logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning")
logger.error("This is an error")

# Test stage logging
logger.log_stage("Testing", {"test_param": "value"})

# Test metrics
logger.log_metrics({"objects": 100, "changes": 50})

# Test completion
logger.log_completion(status='success', total_changes=50)
```

### Check Output

```bash
# View the log file
cat logs/appian_analyzer.log

# Should see entries like:
# 2025-11-21 18:30:15 | DEBUG    | appian_analyzer | <module>:5 | [TEST_001] This is a debug message
# 2025-11-21 18:30:15 | INFO     | appian_analyzer | <module>:6 | [TEST_001] This is an info message
```

## Migration Strategy

### Phase 1: Appian Analyzer Only (Current)
1. Implement logger in comparison_service.py
2. Update analyzer_controller.py
3. Add logging to enhanced_comparison_service.py
4. Test with real comparisons

### Phase 2: Other Features (Later)
1. Create separate loggers for other features:
   - `breakdown_logger` for document breakdown
   - `convert_logger` for SQL conversion
   - `chat_logger` for chat functionality
2. Use same logging infrastructure
3. Separate log files per feature

### Phase 3: Centralized Logging (Future)
1. Add log aggregation
2. Add log viewer in web UI
3. Add log search functionality
4. Add log analytics dashboard

## Recommendations

### Immediate Implementation
1. ✅ **Start with comparison_service.py** - Most critical for debugging
2. ✅ **Add to analyzer_controller.py** - Track web requests
3. ✅ **Add to enhanced_comparison_service.py** - Track comparison logic

### Short-term
1. Add logging to all appian_analyzer components
2. Test with real comparisons
3. Review log output for usefulness
4. Adjust log levels as needed

### Long-term
1. Add log viewer to web UI
2. Implement log search
3. Add performance monitoring
4. Extend to other features

## Next Steps

Would you like me to:
1. **Implement the logger** in comparison_service.py and analyzer_controller.py?
2. **Create a test script** to verify the logger works?
3. **Add logging to all appian_analyzer components**?

Let me know and I'll proceed with the implementation!
