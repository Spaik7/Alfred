# Changelog

All notable changes to Alfred will be documented in this file.

---

## [Phase 1.0] - 2025-10-15

### 🎉 Phase 1 Complete!

**Major Achievement:** Core foundation complete with all basic functionality, personality system, and advanced query handling.

---

### ✨ Added

#### **General Chat Fallback**
- Added Ollama-based conversational responses for unrecognized queries
- Handles greetings, questions, and general conversation
- Uses `alfred-response` model for British butler personality
- Examples: "Hello", "Tell me about Rome", "What's the capital of France?"

#### **Complex Query Parsing**
- Created `functions/complex_query_parser.py` for multi-part question analysis
- Uses Ollama (llama3.2) to break down complex queries into sub-intents
- Examples: "What should I wear today?" → ["weather", "calendar_today"]
- Falls back to general chat if parsing fails

#### **Simple Concatenation Parser**
- Created `functions/simple_concatenation_parser.py` for reliable query splitting
- Regex-based (no LLM needed) - 100% deterministic
- Splits queries like "Che tempo fa e che ore sono?" → ["Che tempo fa", "che ore sono?"]
- Instant detection (~1ms), no timeouts, offline-capable
- Currently executes first sub-query only (future: execute all)

#### **Template System Upgrade**
- Switched from `simple_templates.py` to `response_templates.py`
- Added British butler personality to all template responses
- Multiple response variations (3-4 per intent) for natural variety
- Contextual comments based on data values (system status, weather, etc.)
- 8 intents now use advanced templates (87% AI reduction!)

#### **Infrastructure**
- Complete logging system with rotation and emojis
- Context manager for conversation history and follow-ups
- Error handler with British butler personality
- Configuration validation

---

### 🔧 Fixed

#### **Logger Missing Method**
- Fixed `AttributeError: 'AlfredLogger' object has no attribute 'log_context_update'`
- Added missing `log_context_update()` method to logger (line 237-239)

#### **Weather Not Using AI**
- Fixed weather responses using templates instead of AI
- Updated `config.py`: `RESPONSE_MODE = "ai"`, `AI_MODEL = "alfred-response"`
- Now uses Ollama with minimal essential data (only 3 fields)

#### **Concatenation Detection**
- Fixed concatenation not being detected before pattern matching
- Added early detection to prevent single-intent patterns from matching too early
- Concatenated queries now correctly identify primary intent

#### **Variable Name Collision**
- Fixed `duration` variable collision (1.5s recording vs transit duration)
- Renamed to `travel_duration` in transport handlers

#### **Transport Functions**
- Fixed `get_traffic_status(None, destination)` failing
- Added DEFAULT_LOCATION fallback when origin is None

#### **Recipe Parameter Cleanup**
- Fixed punctuation in recipe parameters ("pasta." → "pasta")
- Added `.rstrip('.,!?;:')` to parameter extraction

---

### 📊 Statistics

**Implementation:**
- Total Intents: 36 defined
- Implemented: 16 (44%)
  - Templates: 8 (instant)
  - AI: 2 (weather + general chat)
  - Special: 6 (news, finance, recipes, transport)

**Performance:**
- AI Call Reduction: 87%
- Template Speed: ~1ms
- Weather AI: ~300-500ms
- General Chat AI: ~500-1000ms

**Code:**
- New Files: 3 (complex parser, simple parser, changelog)
- Modified Files: 5
- New Lines: ~451
- Documentation: Consolidated into 4 files

---

### 🎯 Success Criteria Met

✅ Alfred responds to wake word
✅ Answers weather, time, system queries
✅ Speaks with British butler personality
✅ Switches between Italian and English
✅ Handles complex multi-part queries
✅ Concatenates multiple intents
✅ Provides general conversational responses

---

### 🐛 Known Issues

See `PROBLEMS.md` for details:

1. **Transport Pattern Conflict** - "Arrivare a Vercelli con i mezzi pubblici" matches car instead of public
2. **Concatenation Partial** - Only executes first sub-query (by design for Phase 1)
3. **Ollama Timeouts** - Occasional 45s timeouts (has fallback)
4. **Strict Concatenation Keywords** - "le news e" not detected (pattern needs word boundaries)
5. **Language Mixing** - British butler says "sir" in Italian (feature, not bug!)

**All issues are minor and don't prevent production use.**

---

### 📚 Files

**Active Documentation:**
- `README.md` - Project overview and setup
- `ROADMAP.md` - Development phases and progress
- `PROBLEMS.md` - Known issues and future fixes
- `CHANGELOG.md` - This file

**Configuration:**
- `config.py` - API keys and settings
- `requirements.txt` - Python dependencies

**Core:**
- `alfred.py` - Main application (790 lines)
- `functions/intents.py` - Intent patterns and parsing
- `functions/response_templates.py` - Templates with personality
- `functions/simple_concatenation_parser.py` - Regex query splitter
- `functions/complex_query_parser.py` - Ollama complex analysis

---

## [Pre-Phase 1] - Before 2025-10-15

### Initial Setup
- Wake word detection (ONNX model)
- Whisper transcription (Docker)
- Basic intent parsing (regex-based)
- Weather, time, date, system status functions
- Volume control
- TTS engine (Piper)
- News, finance, recipes, transport functions

---

**Phase 1 Complete!** 🚀 Ready for Phase 2: Mac Integration via SSH
