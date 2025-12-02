# AI Summary Logging Enhancement

**Date:** December 2, 2025  
**File Modified:** `services/merge_summary_service.py`

## Overview

Added extensive logging throughout the AI merge summary generation service to provide detailed visibility into the summary generation process. This will help diagnose issues with AI summary generation and track performance.

## Logging Enhancements

### 1. Background Worker (`_generate_summaries_background`)

**Added:**
- Start/end banners with session ID and thread name
- Step-by-step progress (1/4, 2/4, 3/4, 4/4)
- Timing for each phase (preparation, batching, processing)
- Sample of first 3 changes being processed
- Batch-by-batch progress with detailed timing
- Success/failure counts per batch
- Final summary with:
  - Total duration
  - Successful vs failed batches
  - Total summaries generated
  - Average time per summary

**Example Output:**
```
================================================================================
AI SUMMARY GENERATION STARTED - Session 1
Thread: MergeSummary-1
Start Time: 2025-12-02T22:00:00.000000
================================================================================
Step 1/4: Fetching and preparing change data...
✓ Prepared 50 changes in 0.45s
Sample changes (first 3):
  1. Change 1: Student Interface (Interface) - Classification: CONFLICT
  2. Change 2: Process Model A (Process Model) - Classification: NO_CONFLICT
  3. Change 3: Record Type B (Record Type) - Classification: NEW
Step 2/4: Creating batches...
✓ Created 4 batches (size=15)
Step 3/4: Processing batches...
------------------------------------------------------------
Batch 1/4: Processing 15 changes
  Change IDs: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
  Marking batch as 'processing'...
  ✓ Status updated
  Calling Q Agent for summary generation...
  ✓ Q Agent returned 15 summaries in 12.34s
  Updating changes with summaries...
  ✓ Batch 1 completed in 12.89s (agent: 12.34s, update: 0.45s)
...
================================================================================
AI SUMMARY GENERATION COMPLETED - Session 1
Total Duration: 52.34s
Successful Batches: 4/4
Failed Batches: 0/4
Total Summaries Generated: 50
Average Time per Summary: 1.05s
================================================================================
```

### 2. Change Data Preparation (`_prepare_changes_data`)

**Added:**
- Count of changes found in database
- Package discovery logging
- Package details (type, filename, object count)
- Warnings for missing packages
- Progress updates every 10 changes
- Error logging for missing objects
- Success/failure summary

**Example Output:**
```
Fetching changes for session 1...
Found 50 changes in database
Fetching packages for session 1...
Found 3 packages
  Package: base - Test_Application_-_Base_Version.zip (38 objects)
  Package: customized - Test_Application_Customer_Version.zip (38 objects)
  Package: new_vendor - Test_Application_Vendor_New_Version.zip (38 objects)
Preparing data for 50 changes...
  Processing change 10/50...
  Processing change 20/50...
  Processing change 30/50...
  Processing change 40/50...
  Processing change 50/50...
Successfully prepared 50 changes (0 failed)
```

### 3. Version Fetching (`_fetch_object_versions`)

**Added:**
- Debug logging for missing packages
- SAIL code truncation logging with before/after lengths
- Version details (version_uuid, SAIL code length)
- Warnings when versions not found

**Example Output:**
```
Fetched version for object 123 in customized: version_uuid=abc-123, sail_code_length=2500
Truncated SAIL code for object 456 in new_vendor: 8000 -> 5000 chars
No version found for object 789 in customized
```

### 4. Batch Status Updates (`_update_batch_status`)

**Added:**
- Count of changes being updated
- Result count after update
- Status being set

**Example Output:**
```
Updating 15 changes to status 'processing'
Updated 15 changes to status 'processing'
```

### 5. Summary Updates (`_update_change_summaries`)

**Added:**
- Total count of summaries to update
- Per-change success/failure logging
- Summary text length
- Success/failure counts

**Example Output:**
```
Updating 15 changes with summaries...
Formatted summary for change 1: 450 chars
✓ Updated summary for change 1
Formatted summary for change 2: 380 chars
✓ Updated summary for change 2
...
Summary updates: 15 succeeded, 0 failed
```

### 6. Batch Failure Marking (`_mark_batch_failed`)

**Added:**
- Warning with count and error message
- Result count after marking

**Example Output:**
```
Marking 15 changes as failed: Connection timeout
Marked 15 changes as failed
```

### 7. Summary Regeneration (`regenerate_summary`)

**Added:**
- Change details (name, type, classification)
- Data preparation progress
- Q Agent timing
- Success/failure indicators

**Example Output:**
```
Regenerating summary for change 123...
Change 123: Student Interface (Interface) - Classification: CONFLICT
Preparing change data for session 1...
Change data prepared successfully
Marking change 123 as 'processing'...
Calling Q Agent for change 123...
Q Agent completed in 8.45s, returned 1 summaries
Updating change 123 with summary...
✓ Successfully regenerated summary for change 123
```

## Log Levels Used

- **INFO:** Major milestones, batch progress, completion summaries
- **DEBUG:** Detailed step-by-step operations, data details
- **WARNING:** Missing data, skipped items, non-critical issues
- **ERROR:** Failures, exceptions with stack traces

## Benefits

1. **Troubleshooting:** Quickly identify where summary generation fails
2. **Performance Monitoring:** Track timing for each phase and batch
3. **Progress Tracking:** See real-time progress through batches
4. **Data Validation:** Verify all required data is present
5. **Audit Trail:** Complete record of what was processed

## Testing

To see the enhanced logging in action:

```bash
# Watch the merge assistant log
tail -f logs/merge_assistant.log

# Or filter for summary-related logs
tail -f logs/merge_assistant.log | grep -i "summary\|batch"
```

## Next Steps

1. Create a new merge session via UI
2. Monitor logs during AI summary generation
3. Verify all logging appears as expected
4. Use logs to diagnose any issues that arise
