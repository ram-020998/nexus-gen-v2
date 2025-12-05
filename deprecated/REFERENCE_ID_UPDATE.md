# Reference ID Format Update

## Summary

Updated merge session reference IDs from random format to sequential format.

## Changes Made

### Old Format
- Pattern: `MS_XXXXXX` (e.g., `MS_A1B2C3`, `MS_7B98CF`)
- Generation: Random 6-character hex string from UUID
- Example: `MS_A1B2C3`

### New Format
- Pattern: `MRG_XXX` (e.g., `MRG_001`, `MRG_002`)
- Generation: Sequential 3-digit number with zero-padding
- Example: `MRG_001`, `MRG_002`, `MRG_003`

## Files Updated

### Core Implementation
1. **services/three_way_merge_orchestrator.py**
   - Updated `_generate_reference_id()` method
   - Now queries database for last session and increments sequence
   - Handles migration from old format gracefully

### Documentation
2. **controllers/merge_assistant_controller.py**
   - Updated all docstrings and examples
   - Changed from `MS_A1B2C3` to `MRG_001`

3. **services/change_navigation_service.py**
   - Updated docstrings and examples

4. **services/change_action_service.py**
   - Updated docstrings and examples

### Tests
5. **tests/test_change_action_service.py**
   - `MS_TEST01` → `MRG_001`

6. **tests/test_change_navigation_service.py**
   - `MS_TEST01` → `MRG_001`

7. **tests/test_merge_assistant_controller.py**
   - `MS_TEST01` → `MRG_001`

8. **tests/test_merge_assistant_controller_integration.py**
   - `MS_TEST02` → `MRG_002`

9. **tests/test_report_generation_service.py**
   - `MS_REPORT01` → `MRG_003`

10. **tests/test_session_statistics_service.py**
    - `MS_STATS01` → `MRG_004`
    - `MS_SIMPLE` → `MRG_005`
    - `MS_COMPLEX` → `MRG_006`
    - `MS_EMPTY` → `MRG_007`
    - `MS_EMPTY2` → `MRG_008`
    - `MS_PM` → `MRG_009`
    - `MS_PM2` → `MRG_010`

11. **tests/test_three_way_merge_orchestrator.py**
    - Updated assertion from `startswith('MS_')` to `startswith('MRG_')`

12. **tests/test_integration_end_to_end.py**
    - Updated assertion from `startswith('MS_')` to `startswith('MRG_')`

## Implementation Details

### Reference ID Generation Logic

```python
def _generate_reference_id(self) -> str:
    """
    Generate unique reference ID for merge session.
    
    Format: MRG_XXX where XXX is a sequential 3-digit number (001, 002, etc.).
    """
    # Get the last session to determine next sequence number
    last_session = MergeSession.query.order_by(MergeSession.id.desc()).first()
    
    if last_session and last_session.reference_id.startswith('MRG_'):
        # Extract sequence number from last reference_id
        try:
            last_seq = int(last_session.reference_id.split('_')[1])
            next_seq = last_seq + 1
        except (IndexError, ValueError):
            # If parsing fails, start from 1
            next_seq = 1
    else:
        # First session or migrating from old format
        next_seq = 1
    
    return f"MRG_{next_seq:03d}"
```

### Migration Strategy

The implementation handles migration gracefully:
- If no sessions exist, starts at `MRG_001`
- If last session uses old `MS_` format, starts at `MRG_001`
- If last session uses new `MRG_` format, increments from that number
- Handles parsing errors by defaulting to sequence 1

## Benefits

1. **Human-Readable**: Sequential numbers are easier to reference and remember
2. **Sortable**: Natural ordering by creation time
3. **Predictable**: Users can anticipate the next session ID
4. **Professional**: Follows common industry patterns (e.g., invoice numbers, ticket IDs)
5. **Compact**: Shorter format (7 characters vs 9 characters)

## Testing

All test files have been updated to use the new format. Run tests with:

```bash
python -m pytest > /tmp/test_output.txt 2>&1; cat /tmp/test_output.txt
```

## Backward Compatibility

- Old sessions with `MS_` format will continue to work
- New sessions will use `MRG_` format
- No database migration required
- System automatically detects and handles both formats
