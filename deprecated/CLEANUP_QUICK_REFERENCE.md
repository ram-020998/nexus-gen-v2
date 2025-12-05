# Database Cleanup - Quick Reference

## 🚀 Quick Commands

### Preview Before Deleting (ALWAYS DO THIS FIRST)
```bash
python clean_all_data_complete.py --dry-run
```

### Delete All Merge Data
```bash
python clean_all_data_complete.py
# Requires typing "yes" to confirm
```

### Delete Specific Session
```bash
python clean_all_data_complete.py --session MRG_001
```

### Check Database Health
```bash
python verify_cleanup.py > /tmp/verify.txt 2>&1; cat /tmp/verify.txt
```

### Fix Corrupted Data (NULL foreign keys)
```bash
python cleanup_corrupted_data.py
```

### Fix Orphaned Data (missing parents)
```bash
python cleanup_orphaned_data.py
```

---

## 📊 Script Comparison

| Script | Tables Covered | Features | Use Case |
|--------|---------------|----------|----------|
| `clean_all_data.py` | 39 | Basic cleanup | Simple full cleanup |
| `clean_all_data_complete.py` | 39 | Dry-run, session-specific, safety | Production use |
| `cleanup_corrupted_data.py` | 39 | NULL FK detection | Fix corrupted data |
| `cleanup_orphaned_data.py` | 39 | Orphan detection | Fix orphaned records |
| `verify_cleanup.py` | 39 | Health checks | Verify database state |

---

## 🎯 Common Scenarios

### Scenario 1: Clean Start for Testing
```bash
# 1. Preview
python clean_all_data_complete.py --dry-run

# 2. Clean everything
python clean_all_data_complete.py

# 3. Verify
python verify_cleanup.py > /tmp/verify.txt 2>&1; cat /tmp/verify.txt
```

### Scenario 2: Remove Failed Session
```bash
# 1. Preview what would be deleted
python clean_all_data_complete.py --session MRG_006 --dry-run

# 2. Delete the session
python clean_all_data_complete.py --session MRG_006

# 3. Verify
python verify_cleanup.py > /tmp/verify.txt 2>&1; cat /tmp/verify.txt
```

### Scenario 3: Database Maintenance
```bash
# 1. Check for corrupted data
python cleanup_corrupted_data.py

# 2. Check for orphaned data
python cleanup_orphaned_data.py

# 3. Verify health
python verify_cleanup.py > /tmp/verify.txt 2>&1; cat /tmp/verify.txt
```

### Scenario 4: Before Property Tests
```bash
# Clean database for fresh test run
python clean_all_data_complete.py
# Type "yes" when prompted

# Run tests
python -m pytest tests/test_three_way_merge.py -v > /tmp/test.txt 2>&1; cat /tmp/test.txt
```

---

## ⚠️ Important Notes

1. **Always use dry-run first** - Preview what will be deleted
2. **Use redirect pattern for pytest** - Required due to TTY issues
3. **CASCADE DELETE works** - Database constraints are properly configured
4. **No orphaned data currently** - Database is healthy (124,153 rows)
5. **Session-specific cleanup** - Safer for development/testing

---

## 📋 What Gets Deleted

### Full Cleanup (clean_all_data_complete.py)
Deletes from 39 tables in this order:
1. Comparison detail tables (6 tables)
2. Object detail tables (12 tables)
3. Object-specific tables (18 tables)
4. Core comparison tables (3 tables)
5. Package-related tables (3 tables)
6. Session table (1 table)
7. Global object registry (1 table)

### Session-Specific Cleanup
Only deletes data related to specified session:
- Session record
- Packages for that session
- All objects in those packages
- All comparisons for that session
- All changes for that session

---

## 🔍 Verification Checks

`verify_cleanup.py` checks for:
- Row counts in all 39 tables
- Packages without sessions
- Delta results without sessions
- Customer results without sessions
- Changes without sessions
- Object versions without packages
- Package mappings without packages/objects
- Duplicate UUIDs in object_lookup

---

## 💡 Pro Tips

1. **Use dry-run liberally** - It's free and safe
2. **Check verification after cleanup** - Confirms success
3. **Session-specific for dev** - Keeps other test data
4. **Full cleanup for CI/CD** - Clean slate for automated tests
5. **Run maintenance scripts weekly** - Catch issues early

---

## 🐛 Troubleshooting

### "Address already in use" when starting app
```bash
lsof -ti :5002 | xargs kill -9
```

### "TY=not a tty" error with pytest
```bash
# Use redirect pattern
python -m pytest > /tmp/test.txt 2>&1; cat /tmp/test.txt
```

### Cleanup seems incomplete
```bash
# Run verification
python verify_cleanup.py > /tmp/verify.txt 2>&1; cat /tmp/verify.txt

# If orphaned data found
python cleanup_orphaned_data.py

# If corrupted data found
python cleanup_corrupted_data.py
```

### Want to see what's in database
```bash
python verify_cleanup.py > /tmp/verify.txt 2>&1; cat /tmp/verify.txt
```

---

## 📈 Current Database Stats

As of last check:
- **Total Rows:** 124,153
- **Sessions:** 9
- **Objects:** 2,371
- **Packages:** 27
- **Changes:** 177
- **Status:** ✅ Healthy (no orphaned/corrupted data)
