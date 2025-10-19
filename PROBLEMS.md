# Known Issues & Future Fixes

This document tracks known bugs, issues, and future enhancements for Alfred.

---

## 🐛 Active Bugs

### 1. Intent Pattern Conflict - Transport with Arrival Time
**Status:** Open
**Priority:** Medium
**Date Reported:** 2025-10-15

**Issue:**
When saying "Arrivare a Vercelli con i mezzi pubblici alle 12", the intent parser incorrectly matches `transport_car` instead of `transport_public`.

**Details:**
```
Input: "Arrivare a Vercelli con i mezzi pubblici alle 12"
Expected: transport_public with destination="vercelli", arrival_time="12"
Actual: transport_car with destination="vercelli con i mezzi pubblici", arrival_time="12"
```

**Root Cause:**
The car transport pattern `arrivare a (.+?) (?:alle|per le) (\d{1,2}(?::\d{2})?)` is too greedy and matches before the public transport patterns can be evaluated. The `.+?` captures "vercelli con i mezzi pubblici" as the destination.

**Proposed Fix:**
- Reorder patterns so public transport patterns are checked before car patterns
- OR make car pattern more specific to exclude "con i mezzi" phrases
- OR add negative lookahead: `arrivare a (.+?)(?! con i mezzi) (?:alle|per le)`

**Workaround:**
Use alternative phrasings:
- "Mezzi pubblici per Vercelli per arrivare alle 12" ✅
- "Quando devo partire per Vercelli per arrivare alle 12" ✅

**Files Affected:**
- `/Volumes/jarvis/functions/intents.py` (lines 460-494)

---

### 2. Concatenated Queries - Only Executes First Intent
**Status:** Open (By Design for Phase 1)
**Priority:** Medium
**Date Reported:** 2025-10-15

**Issue:**
Concatenated queries are detected and split correctly, but only the FIRST sub-query is executed.

**Details:**
```
Input: "Che tempo fa e che ore sono?"
Expected: Weather AND time responses
Actual: Only weather response

Detection Works:
✅ Detects concatenation
✅ Splits into ["Che tempo fa", "che ore sono?"]
✅ Correctly identifies weather as primary intent
❌ Does NOT execute time (second query ignored)
```

**Root Cause:**
`alfred.py` lines 375-383 - designed to execute only first intent for Phase 1 simplicity.

**Proposed Fix:**
Execute ALL sub-queries and combine results:
```python
if len(sub_queries) > 1:
    responses = []
    for sq in sub_queries:
        sub_result = parse_intent(sq)
        sub_response = execute_intent(sub_result)
        responses.append(sub_response)

    # Combine
    combined = ". E poi, ".join(responses) if lang=='it' else ". And then, ".join(responses)
    speak(combined)
```

**Files Affected:**
- `/Volumes/jarvis/alfred.py` (lines 375-383)

---

### 3. Ollama Timeouts
**Status:** Open (Intermittent)
**Priority:** Medium
**Date Reported:** 2025-10-15

**Issue:**
Ollama API sometimes times out after 45 seconds, causing fallback responses.

**Details:**
```
Test 1: "What should I wear?" → ✅ Worked (225 chars in ~3s)
Test 2: "Dimmi le news e il meteo" → ❌ Timed out after 45s
Test 3: "Che tempo fa?" → ✅ Worked (192 chars in ~2s)

Pattern: Random timeouts, possibly due to model not preloaded
```

**Proposed Fix:**
1. Preload model at startup (already exists in code!)
2. Increase timeout to 90s
3. Add retry logic

**Files Affected:**
- `/Volumes/jarvis/functions/response_generator.py` (line 66)

---

### 4. Concatenation Keywords Too Strict
**Status:** Open
**Priority:** Low
**Date Reported:** 2025-10-15

**Issue:**
Some concatenation patterns not detected because patterns require spaces on both sides.

**Details:**
```
Input: "Dimmi le news e il meteo"
Issue: "le" ends with 'e', so " e " pattern doesn't match
Pattern: r'\s+e\s+' requires spaces on BOTH sides

Input: "Meteo & News"
Issue: "&" not in keyword list
```

**Proposed Fix:**
Make patterns more flexible:
```python
r'\be\b',        # Word boundary (catches "news e meteo")
r'\s*&\s*',      # Allow "&" with optional spaces
```

**Files Affected:**
- `/Volumes/jarvis/functions/simple_concatenation_parser.py` (lines 21-32)

---

### 5. Language Mixing in AI Responses
**Status:** Open (Feature, not bug!)
**Priority:** Low
**Date Reported:** 2025-10-15

**Issue:**
Alfred sometimes mixes English and Italian in responses.

**Details:**
```
Input (Italian): "Che tempo fa?"
Response: "Very well, sir. Il tempo è di circa 18 gradi..."
          ^^^^^^^^^^ English    ^^^^^^^^^^^^^^ Italian

This is the "British butler speaking Italian" personality quirk!
```

**Decision:**
Keep as-is - it's charming! British butler should say "sir" even in Italian.

**Alternative Fix (if needed):**
Post-process Italian responses to replace "sir" → "signore"

---

## 📋 Future Enhancements

### Phase 1 Polish
- ✅ Execute all sub-queries in concatenated queries (Medium priority)
- ✅ Preload Ollama model at startup (Easy win)
- ✅ Add more flexible concatenation patterns (Nice to have)

### Language Detection
- Improve Italian keyword detection for mixed phrases
- Handle code-switching between Italian and English

### Time Parsing
- Support natural time expressions ("mezzogiorno" for "12", "sera" for evening)
- Handle relative times ("fra un'ora", "in 30 minuti")

### Transport
- Add walking/cycling modes
- Support multiple destinations
- Calculate cost estimates for transit

### General
- Cache frequent Ollama responses
- Batch multiple API calls
- Voice recognition for multiple users
- Mobile app for remote control

---

### 6. Calendar Recurring Events Not Detected
**Status:** Open
**Priority:** Medium
**Date Reported:** 2025-10-19

**Issue:**
Calendar events with yearly or weekly recurrence are not being detected on their occurrence dates. Only non-recurring events in the target date range are found.

**Details:**
```
Oct 17, 2025 (Friday):
Expected: 2 events (Daniele Rizzo birthday + Weekly Call)
Actual: 0 events found

Oct 19, 2025 (Sunday/today):
Expected: 1 event (pranzo)
Actual: 1 event ✅ (works for non-recurring events)

Calendar has 854 total events, including:
- Birthday: starts Oct 17, 2005, recurs yearly (FREQ=YEARLY)
- Weekly Call (Mon): starts Nov 25, 2024, recurs weekly (FREQ=WEEKLY)
- Weekly Call (Fri): starts Jul 25, 2025, recurs weekly (FREQ=WEEKLY)
```

**Root Cause:**
AppleScript query `whose start date >= targetDate and start date < endDate` checks the ORIGINAL start date of the event, not the occurrence date. Recurring events have start dates from years ago (birthday from 2005), so they don't match the date range filter.

**Current Workaround Attempts:**
1. ❌ Iterate through ALL events (854) - times out after 30s
2. ❌ Filter to events within 400-day window + manually check recurrence - still times out
3. ❌ Separate pass for old yearly events - doesn't find them

**Proposed Fix:**
Use Python with EventKit framework instead of AppleScript:
```python
from EventKit import EKEventStore
predicate = store.predicateForEventsWithStartDate_endDate_calendars_(start_ns, end_ns, calendars)
events = store.eventsMatchingPredicate_(predicate)
```
EventKit's `predicateForEventsWithStartDate_endDate_calendars_` properly handles recurring events and returns occurrences in the date range.

**Challenge:**
SSH expect script mangles Python f-strings and complex quotes when sending commands to Mac. Need to write Python script to temp file first, then execute it.

**Alternative Fix:**
Use JavaScript for Automation (JXA) which has better date handling than AppleScript.

**Files Affected:**
- `/Volumes/jarvis/functions/ssh_helper.py` (lines 414-528) - `get_calendar_events_for_date()`
- Related functions: `get_calendar_events_today()`, `get_calendar_events_yesterday()`, `get_calendar_events_tomorrow()`, `get_calendar_events_specific()`

**Impact:**
- Calendar yesterday/tomorrow checks don't work for recurring events
- Birthday reminders not working
- Weekly recurring meetings not detected

---

## ✅ Fixed Issues

### Variable Name Collision - `duration`
**Fixed:** 2025-10-15
**Issue:** Global `duration` variable (1.5s for recording) was overwritten by transit duration string ("22 mins")
**Solution:** Renamed to `travel_duration` in transport handlers

### Transport Functions - None Origin
**Fixed:** 2025-10-15
**Issue:** `get_traffic_status(None, destination)` failed because None is not valid
**Solution:** Added DEFAULT_LOCATION fallback when origin is None

### Recipe Search - Punctuation in Parameters
**Fixed:** 2025-10-15
**Issue:** "Recipe for pasta." captured "pasta." with period
**Solution:** Added `.rstrip('.,!?;:')` to parameter extraction

---

## 📝 Notes

- When adding new intent patterns, always consider pattern order (specific before generic)
- Test with both languages (English and Italian)
- Check for variable name collisions with global scope variables
