# Phase 6: Visual Test Guide

**Quick guide for testing the UI components**

---

## Prerequisites

1. Flask app running on port 5002
2. Valid merge session created
3. Browser with developer tools

---

## Test 1: Change Detail Page - AI Summary

### Steps:

1. **Navigate to change detail:**
   ```
   http://localhost:5002/merge/MRG_001/changes/1
   ```

2. **Check AI Summary Card:**
   - Should appear between comparison section and notes
   - Card header shows robot icon and "AI Analysis" title

3. **Verify Loading State (if pending/processing):**
   - ✅ Animated spinner visible
   - ✅ Text says "Queued for analysis..." or "Analyzing changes..."
   - ✅ Gradient background with dashed border
   - ✅ Status updates every 3 seconds

4. **Verify Completed State:**
   - ✅ Summary text displays with formatting
   - ✅ Strong text appears in purple
   - ✅ Line breaks render correctly
   - ✅ Timestamp shows "Generated X minutes ago"

5. **Verify Failed State:**
   - ✅ Red warning icon visible
   - ✅ Error message displays
   - ✅ "Retry" button appears
   - ✅ Red-tinted background

6. **Test Retry Button:**
   - Click "Retry" button
   - ✅ Button shows "Regenerating..." with spinner
   - ✅ Loading state appears
   - ✅ Polling starts automatically

---

## Test 2: Session Summary Page - Progress Indicator

### Steps:

1. **Navigate to session summary:**
   ```
   http://localhost:5002/merge/MRG_001/summary
   ```

2. **Check Progress Card:**
   - Should appear after statistics section
   - Card shows robot icon and "AI Summary Generation" title

3. **Verify Progress Display:**
   - ✅ Progress bar shows percentage
   - ✅ Badge shows "X/Y" (completed/total)
   - ✅ Processing count with spinner icon
   - ✅ Failed count with warning icon

4. **Verify Real-Time Updates:**
   - Open browser DevTools → Network tab
   - ✅ See requests to `/summary-progress` every 3 seconds
   - ✅ Progress bar advances smoothly
   - ✅ Counts update automatically

5. **Verify Shimmer Animation:**
   - ✅ Progress bar has animated shimmer effect
   - ✅ Smooth gradient from purple to pink

6. **Test Retry Failed Button:**
   - If failed count > 0, button should be visible
   - Click "Retry Failed" button
   - ✅ Button shows "Retrying..." with spinner
   - ✅ Progress resets to 0%
   - ✅ Polling continues

7. **Verify Auto-Hide:**
   - Wait for all summaries to complete
   - ✅ Notification appears: "AI analysis completed!"
   - ✅ Card fades out after 5 seconds
   - ✅ Card disappears completely

---

## Test 3: Polling Behavior

### Steps:

1. **Open Browser DevTools:**
   - Press F12
   - Go to Network tab
   - Filter by "Fetch/XHR"

2. **Navigate to change detail page**

3. **Verify Polling Requests:**
   - ✅ See requests to `/changes?classification=all` every 3 seconds
   - ✅ Requests stop when status is 'completed' or 'failed'

4. **Navigate to summary page**

5. **Verify Progress Polling:**
   - ✅ See requests to `/summary-progress` every 3 seconds
   - ✅ Requests stop when processing=0 and pending=0

6. **Test Page Navigation:**
   - Navigate away from page
   - ✅ Polling stops (no more requests)
   - Navigate back
   - ✅ Polling resumes automatically

---

## Test 4: Responsive Design

### Steps:

1. **Open Browser DevTools:**
   - Press F12
   - Click device toolbar icon (Ctrl+Shift+M)

2. **Test Mobile View (375px):**
   - ✅ AI Summary card stacks vertically
   - ✅ Progress card adapts to width
   - ✅ Text remains readable
   - ✅ Buttons are full width

3. **Test Tablet View (768px):**
   - ✅ Layout adjusts appropriately
   - ✅ Progress details wrap if needed

4. **Test Desktop View (1920px):**
   - ✅ All elements display correctly
   - ✅ No horizontal scrolling

---

## Test 5: Error Handling

### Steps:

1. **Simulate Network Error:**
   - Open DevTools → Network tab
   - Enable "Offline" mode

2. **Verify Error Handling:**
   - ✅ Polling continues to attempt
   - ✅ No JavaScript errors in console
   - ✅ UI remains functional

3. **Re-enable Network:**
   - Disable "Offline" mode
   - ✅ Polling resumes automatically
   - ✅ Data updates correctly

---

## Test 6: Text Formatting

### Steps:

1. **Check Summary Text Formatting:**
   - Look for text with `**bold**` in database
   - ✅ Renders as `<strong>bold</strong>`
   - ✅ Strong text appears in purple

2. **Check Line Breaks:**
   - Look for text with `\n` in database
   - ✅ Renders as `<br>` tags
   - ✅ Text breaks correctly

3. **Check Timestamp Formatting:**
   - ✅ "just now" for <1 minute
   - ✅ "5 minutes ago" for <1 hour
   - ✅ "2 hours ago" for <24 hours
   - ✅ Full date for >24 hours

---

## Test 7: Animations

### Steps:

1. **Check Loading Spinner:**
   - ✅ Spins smoothly (no jitter)
   - ✅ Purple color
   - ✅ Appropriate size

2. **Check Progress Bar Animation:**
   - ✅ Width transitions smoothly (0.5s)
   - ✅ Shimmer effect animates (2s loop)
   - ✅ No performance issues

3. **Check Fade Out Animation:**
   - Wait for completion
   - ✅ Card fades out smoothly (0.5s)
   - ✅ No layout shift

---

## Test 8: Accessibility

### Steps:

1. **Test Keyboard Navigation:**
   - Use Tab key to navigate
   - ✅ Can reach retry buttons
   - ✅ Focus indicators visible
   - ✅ Enter key activates buttons

2. **Test Screen Reader:**
   - Enable screen reader (NVDA/JAWS)
   - ✅ Card headers announced
   - ✅ Status changes announced
   - ✅ Button labels clear

3. **Test Color Contrast:**
   - Use browser contrast checker
   - ✅ Text meets WCAG AA standards
   - ✅ Icons are distinguishable

---

## Expected Console Output

### Normal Operation:

```
No errors
```

### During Polling:

```
(No console output - polling happens silently)
```

### On Completion:

```
(No console output - success is silent)
```

### On Error:

```
Failed to check AI summary status: [error details]
Failed to poll AI progress: [error details]
```

---

## Visual Checklist

### Change Detail Page:

- [ ] AI Summary card appears in correct location
- [ ] Loading state displays correctly
- [ ] Completed state shows formatted text
- [ ] Failed state shows error message
- [ ] Retry button works
- [ ] Polling updates automatically
- [ ] Animations are smooth
- [ ] Responsive on mobile

### Summary Page:

- [ ] Progress card appears after statistics
- [ ] Progress bar animates smoothly
- [ ] Counts update in real-time
- [ ] Shimmer effect visible
- [ ] Retry Failed button appears when needed
- [ ] Auto-hide works after completion
- [ ] Notification displays
- [ ] Responsive on mobile

---

## Common Issues & Solutions

### Issue: Progress card doesn't appear

**Solution:** Check if session has any changes with AI summaries

### Issue: Polling doesn't start

**Solution:** Check browser console for JavaScript errors

### Issue: Progress bar doesn't animate

**Solution:** Check CSS is loaded correctly

### Issue: Retry button doesn't work

**Solution:** Check API endpoint is accessible

### Issue: Auto-hide doesn't work

**Solution:** Check JavaScript timeout logic

---

## Performance Benchmarks

### Expected Performance:

- **Page Load:** <2 seconds
- **Polling Request:** <100ms
- **UI Update:** <50ms
- **Animation FPS:** 60fps
- **Memory Usage:** <50MB increase

### How to Measure:

1. Open DevTools → Performance tab
2. Click Record
3. Interact with page
4. Stop recording
5. Check metrics

---

## Browser-Specific Notes

### Chrome:
- All features work perfectly
- DevTools provide best debugging

### Firefox:
- All features work
- May need to enable fetch in about:config

### Safari:
- All features work
- May need to enable developer menu

### Edge:
- All features work
- Same as Chrome (Chromium-based)

---

## Quick Test Script

```bash
# 1. Start app
python app.py

# 2. Open browser
open http://localhost:5002/merge/MRG_001/summary

# 3. Open DevTools
# Press F12

# 4. Watch Network tab
# Filter by "Fetch/XHR"

# 5. Verify polling
# Should see requests every 3 seconds

# 6. Navigate to change detail
open http://localhost:5002/merge/MRG_001/changes/1

# 7. Verify AI summary displays
# Check for AI Summary card

# 8. Test retry button
# Click if failed state

# 9. Verify completion
# Wait for all summaries to complete
```

---

**Testing Complete!** ✅

If all tests pass, Phase 6 UI implementation is working correctly.
