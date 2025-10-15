# Known Issues & Future Fixes

This document tracks known bugs and issues that need to be fixed in future updates.

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

## 📋 Future Enhancements

### Language Detection
- Improve Italian keyword detection for mixed phrases
- Handle code-switching between Italian and English

### Time Parsing
- Support more natural time expressions ("mezzogiorno" for "12", "sera" for evening times)
- Handle relative times ("fra un'ora", "in 30 minuti")

### Transport
- Add walking/cycling modes
- Support multiple destinations
- Calculate cost estimates for transit

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
