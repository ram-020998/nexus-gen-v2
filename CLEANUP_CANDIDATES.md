# Repository Cleanup Candidates

Generated: December 5, 2025  
**Status: ✅ COMPLETED - All files moved to `deprecated/` folder**

This document lists all files that were identified as temporary, adhoc testing scripts, or task completion documentation and have been moved to the `deprecated/` folder.

---

## Category 1: Adhoc Testing Python Scripts (38 files)

These are Python files created for one-off testing, debugging, or verification purposes:

### Analysis & Debugging Scripts
- `analyze_actual_differences.py`
- `debug_change_213.py`
- `diagnose_missing_delta_objects.py`

### Check/Verification Scripts
- `check_change_111.py`
- `check_change_1408.py`
- `check_conflict_classification.py`
- `check_conflict_objects.py`
- `check_object_specific_tables.py`
- `verify_ai_summary_schema.py`
- `verify_cleanup.py`
- `verify_flow_fix.py`
- `final_verification_mrg_006.py`

### Cleanup Scripts
- `clean_all_data.py`
- `clean_all_data_complete.py`
- `cleanup_corrupted_data.py`
- `cleanup_orphaned_data.py`

### Delete/Force Operations
- `delete_old_merge_sessions.py`
- `delete_session_mrg_001.py`
- `force_delete_session.py`

### Fix Scripts
- `fix_delta_comparison_service.py`
- `fix_template_quotes.py`

### Regenerate/Rerun Scripts
- `regenerate_report.py`
- `rerun_mrg_006_workflow.py`

### Utility Scripts
- `list_sessions.py`

### Test Scripts (Root Level - Should be in tests/ folder)
- `test_ai_summary_integration.py`
- `test_api_endpoints.py`
- `test_b_vs_c_comparison.py`
- `test_cleanup_functionality.py`
- `test_comparison_mode_api.py`
- `test_complete_workflow.py`
- `test_conflict_detection_fix.py`
- `test_customer_only_fix.py`
- `test_delete_mrg_002.py`
- `test_delta_comparison_fix.py`
- `test_flow_storage.py`
- `test_no_conflict_display_logic.py`
- `test_report_generation.py`
- `test_sail_diff.py`
- `test_sail_formatter.py`
- `test_sail_formatter_integration.py`
- `test_sail_formatter_simple.py`

---

## Category 2: Task Completion Markdown Files (34 files)

These are documentation files created to track completion of specific tasks or features:

### Implementation Documentation
- `AI_MERGE_SUMMARY_IMPLEMENTATION_PLAN.md`
- `AI_SUMMARY_IMPLEMENTATION_STATUS.md`
- `AI_SUMMARY_LOGGING_ENHANCEMENT.md`
- `COMPLETE_WORKFLOW_IMPLEMENTATION.md`
- `SAIL_DIFF_IMPLEMENTATION.md`
- `SAIL_FORMATTER_IMPLEMENTATION.md`
- `THREE_WAY_MERGE_FIX_IMPLEMENTATION.md`

### Summary/Completion Reports
- `CLEANUP_COMPLETE.md`
- `CLEANUP_FIX_SUMMARY.md`
- `CLEANUP_FUNCTIONALITY_REPORT.md`
- `COMPARISON_UI_FIX_SUMMARY.md`
- `COMPLETE_WORKFLOW_FINAL_SUMMARY.md`
- `DELTA_COMPARISON_FIX_SUMMARY.md`
- `IMPLEMENTATION_COMPLETE.md`
- `IMPLEMENTATION_SUMMARY.md`
- `MERGE_SESSION_FIX_SUMMARY.md`
- `NO_CONFLICT_UI_UPDATE_SUMMARY.md`
- `PHASE_5_API_ENDPOINTS_SUMMARY.md`
- `PHASE_6_UI_COMPLETION_SUMMARY.md`
- `REPORT_ENHANCEMENT_SUMMARY.md`

### Fix Documentation
- `COMPARISON_LABEL_FIX_FINAL.md`
- `CONFLICT_DETECTION_FIX.md`
- `THREE_WAY_MERGE_DESIGN_FIX.md`

### Update Documentation
- `ACTUAL_SAIL_CHANGE_EXPLANATION.md`
- `APPIAN_COLOR_PALETTE_UPDATE.md`
- `NO_CONFLICT_DISPLAY_LOGIC_UPDATE.md`
- `REFERENCE_ID_UPDATE.md`
- `SETTINGS_FEATURE_UPDATE.md`

### Analysis Documentation
- `THREE_WAY_MERGE_CORRECT_ANALYSIS.md`

### Quick Reference/Guides
- `CLEANUP_QUICK_REFERENCE.md`
- `PHASE_5_COMPLETION_CHECKLIST.md`
- `PHASE_6_VISUAL_TEST_GUIDE.md`
- `PROCESS_MODEL_VARIABLES_TAB_SUMMARY.md`
- `VERIFICATION_CHECKLIST.md`

---

## Category 3: Shell Scripts for Testing (3 files)

These are bash scripts created for adhoc testing purposes:

- `test_endpoints_quick.sh` - Quick API endpoint testing
- `update_all_comparison_templates.sh` - Template update script
- `verify_fix.sh` - Verification script

---

## Summary Statistics

- **Total Python Scripts:** 38 files
- **Total Markdown Files:** 34 files
- **Total Shell Scripts:** 3 files
- **Grand Total:** 75 files

---

## Recommendations

### High Priority for Removal
1. All `check_*.py` scripts (specific to debugging past issues)
2. All `debug_*.py` scripts (one-off debugging)
3. All `delete_*.py` scripts (manual cleanup operations)
4. All `fix_*.py` scripts (patches that should be in main code)
5. Session-specific scripts (`*_mrg_001.py`, `*_mrg_006.py`, etc.)
6. All `*_SUMMARY.md` and `*_COMPLETE.md` files (historical documentation)

### Medium Priority for Removal
1. Test scripts in root (should move to `tests/` folder if still needed)
2. Shell scripts (`.sh` files) - evaluate if still needed
3. Implementation/fix documentation (`.md` files) - archive if needed

### Keep (Potentially Useful)
1. `cleanup_corrupted_data.py` - May be useful for maintenance
2. `cleanup_orphaned_data.py` - May be useful for maintenance
3. `list_sessions.py` - Utility script that might be useful
4. `README.md` - Main project documentation

---

## Suggested Action Plan

1. **Review** each file to ensure no critical functionality
2. **Archive** important documentation to a `docs/archive/` folder
3. **Move** legitimate test files to `tests/` folder
4. **Delete** adhoc scripts and temporary files
5. **Update** `.gitignore` to prevent future accumulation

---

## Notes

- This analysis was performed on the root directory only
- Some files may have dependencies or be referenced elsewhere
- Always verify before deletion
- Consider creating a backup before bulk deletion


---

## ✅ Cleanup Completed

**Date:** December 5, 2025  
**Action Taken:** All 75+ files moved to `deprecated/` folder  
**Files Moved:** 79 files total (includes some additional files that were already in deprecated)

### Current Status
- ✅ All adhoc Python scripts moved
- ✅ All task completion markdown files moved
- ✅ All testing shell scripts moved
- ✅ Root directory cleaned up
- ✅ Only essential files remain (README.md, CLEANUP_CANDIDATES.md, core application files)

### Deprecated Folder Location
All files are now located in: `./deprecated/`

### Next Steps (Optional)
1. Review deprecated folder contents if needed
2. Add `deprecated/` to `.gitignore` if desired
3. Archive or delete the deprecated folder after verification period
4. Update any documentation that references moved files
