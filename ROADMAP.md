# 🤖 Alfred - Batman's Butler AI Assistant
## Complete Development Roadmap

---

## 📋 Project Overview

**Vision:** A voice-activated AI assistant running on Raspberry Pi 5, with full access to Mac applications, email, calendar, messaging, and future smart home integration.

**Personality:** British butler (like Batman's Alfred) - formal, helpful, dry humor, bilingual (Italian/English)

**Architecture:**
- **Pi 5**: Wake word detection, Ollama reasoning, function orchestration, TTS
- **Mac (SSH)**: Apple Mail, Calendar, Telegram, WhatsApp, app control
- **Mac (Docker)**: Whisper transcription service

---

## 🎯 Phase 1: Foundation (Week 1-2)
**Goal:** Core infrastructure + basic information queries

### 1.1 Project Structure Setup
```
alfred/
├── alfred.py                 # Main orchestrator
├── config.py                # Configuration & API keys
├── requirements.txt         # Python dependencies
├── ssh_helper.py           # SSH connection utilities
├── intents.py              # Ollama intent parser
├── response_generator.py   # Natural language responses
├── tts_engine.py           # Text-to-speech
├── security.py             # PIN verification system
├── functions/
│   ├── __init__.py
│   ├── weather.py         # Weather API integration
│   ├── time_date.py       # Time/date queries
│   ├── system.py          # Pi monitoring
│   ├── calculations.py    # Math, conversions
│   └── general.py         # Jokes, translations, etc.
├── models/
│   └── alfred.onnx        # Wake word model
├── logs/
│   └── alfred.log         # System logs
└── tests/
    └── test_functions.py  # Unit tests
```

### 1.2 Core Components
- [x] Wake word detection (already done)
- [x] Ollama integration for complex query parsing (✅ Complete - see PHASE_1_COMPLETE.md)
- [x] Simple query intent parsing
- [x] Response generator (templates + LLM) (✅ Enhanced with full personality - see PHASE_1.2_COMPLETE.md)
- [x] TTS engine setup (Piper)
- [x] Logging system (✅ Complete with rotation, emojis, performance tracking)
- [x] Error handling framework (✅ Complete with British butler personality)
- [x] Configuration management (✅ Complete with validation and env vars)
- [x] Query concatenation (✅ Complete - handles multiple intents in one sentence)

### 1.3 Basic Functions
- [x] Weather queries (OpenWeatherMap API)
- [x] Time and date
- [x] System monitoring (CPU, RAM, temp)
- [x] Simple calculations
- [x] Jokes
- [x] General chat (✅ Complete - Ollama fallback for conversational responses)

### 1.4 Personality System
- [x] Response templates with Alfred's personality (✅ Complete - 14 intent types with British butler style)
- [x] Italian/English language detection
- [x] Formal British phrases (✅ All responses use "sir", "I'm afraid", "Rather", etc.)
- [x] Dry humor responses (✅ Contextual comments: "Not far at all", "A bit of a decline")
- [x] Context-aware tone adjustment (✅ Weather, traffic, finance comments based on data)

**Deliverable:** Alfred can answer basic questions with personality ✅ **COMPLETE!**

**See PHASE_1_COMPLETE.md for full details**

---

## 🎯 Phase 2: Mac Integration via SSH (Week 3-4)
**Goal:** Remote control of Mac applications

### 2.1 SSH Infrastructure
- [ ] SSH key authentication setup
- [ ] AppleScript execution wrapper
- [ ] Connection pooling for performance
- [ ] Error handling for connection failures
- [ ] Retry logic

### 2.2 Apple Mail Integration
```python
functions/email.py:
- [ ] Check unread count
- [ ] Get recent emails (with sender, subject, date)
- [ ] Get emails from specific sender
- [ ] Search emails by keyword
- [ ] Read email content
- [ ] Send email (with PIN verification)
- [ ] Reply to email (with PIN)
- [ ] Mark as read/unread
- [ ] Delete email (with PIN)
```

### 2.3 Apple Calendar Integration
```python
functions/calendar.py:
- [ ] Get today's events
- [ ] Get week's schedule
- [ ] Get next event
- [ ] Check availability at time
- [ ] Find free time slots
- [ ] Create event (with PIN)
- [ ] Modify event (with PIN)
- [ ] Delete event (with PIN)
- [ ] Get event details
```

### 2.4 Mac Application Control
```python
functions/mac_control.py:
- [ ] Open application by name
- [ ] Close application
- [ ] Check if app is running
- [ ] Take screenshot
- [ ] Lock screen
- [ ] Sleep/wake Mac
- [ ] Shutdown (with PIN)
- [ ] Volume control
- [ ] Brightness control
```

### 2.5 PIN Security System
```python
security.py:
- [ ] PIN storage (hashed)
- [ ] PIN verification
- [ ] Sensitive action detection
- [ ] PIN prompt via TTS
- [ ] Failed attempt tracking
- [ ] Lockout after 3 failures
- [ ] PIN reset mechanism
```

**Deliverable:** Alfred can read/send emails, manage calendar, control Mac

---

## 🎯 Phase 3: Messaging Integration (Week 5-6)
**Goal:** Telegram and WhatsApp messaging

### 3.1 Telegram Bot
```python
functions/telegram.py:
- [ ] Bot setup and authentication
- [ ] Send message to contact
- [ ] Send message to group
- [ ] Get recent messages
- [ ] Read messages from person
- [ ] Forward message
- [ ] Send photo/file
- [ ] Create poll
- [ ] Get chat list
```

**Setup:**
- [ ] Create Telegram bot with BotFather
- [ ] Get bot token
- [ ] Get your chat_id
- [ ] Test bot communication

### 3.2 WhatsApp Integration
```python
functions/whatsapp.py:
- [ ] Choose integration method (pywhatkit or Twilio)
- [ ] Send message to contact
- [ ] Get recent messages (if possible)
- [ ] Send to multiple contacts
- [ ] Schedule message
```

**Setup:**
- [ ] If Twilio: create account, get credentials
- [ ] If pywhatkit: setup WhatsApp Web on Mac
- [ ] Test sending messages

### 3.3 Contact Management
```python
functions/contacts.py:
- [ ] Load contacts from Mac Address Book
- [ ] Search contact by name
- [ ] Get contact info (email, phone, telegram)
- [ ] Fuzzy matching for names
- [ ] Nickname support
```

**Deliverable:** Alfred can send/receive messages via Telegram and WhatsApp

---

## 🎯 Phase 4: Media & Development Tools (Week 7-8)
**Goal:** Apple Music control and developer workflows

### 4.1 Spotify Integration
```python
functions/spotify.py:
#- [ ] Spotify API authentication need to check apple music
- [ ] Play song/artist/album
- [ ] Pause/resume
- [ ] Next/previous track
- [ ] Volume control
- [ ] Get current playing
- [ ] Add to playlist
- [ ] Search tracks
- [ ] Play user's playlists
```

### 4.2 Developer Workflows
```python
functions/development.py:
- [ ] Open project in VS Code/PyCharm
- [ ] Run tests
- [ ] Start dev server
- [ ] Stop dev server
- [ ] Git operations (pull, status, commit)
- [ ] Docker operations (ps, restart)
- [ ] Check service status
- [ ] View logs
- [ ] Deploy to staging (with PIN)
```

### 4.3 GitHub Integration (Optional)
```python
functions/github.py:
- [ ] Check repo status
- [ ] List pull requests
- [ ] Get latest commits
- [ ] Check CI/CD status
- [ ] Create issue
```

**Deliverable:** Alfred controls music and helps with development

---

## 🎯 Phase 5: Context-Aware Intelligence (Week 9-10)
**Goal:** Complex queries combining multiple data sources

### 5.1 Advanced Query Handler
```python
functions/advanced_queries.py:
- [ ] "What should I wear today?"
      → Weather + Calendar (formal meeting?) + Clothing suggestions
      
- [ ] "Should I leave now?"
      → Calendar (next meeting) + Traffic + Travel time
      
- [ ] "Can I go for a run?"
      → Weather + Air quality + Calendar + Last run time
      
- [ ] "Summary of my day"
      → Calendar + Emails + Tasks + Weather
      
- [ ] "Good morning routine"
      → Weather forecast + Calendar + Top emails + News
      
- [ ] "What's urgent?"
      → Emails (flagged/important) + Calendar (soon) + Tasks (due)
```

### 5.2 Concatenation Query
```python
- [ ] "What should i wear today and what's on the calendar today"
      → Weather + Calendar + Tasks
```

### 5.3 Context Management
```python
context_manager.py:
- [x] Maintain conversation context (✅ Phase 1.2 - Last 10 turns, 5-min timeout)
- [x] Remember previous queries (✅ ConversationTurn dataclass with full history)
- [x] Handle follow-up questions (✅ "What about tomorrow?", "How long to there?")
- [x] Track user preferences (✅ Preferences dictionary in context)
- [ ] Learn from interactions (Future - ML/pattern recognition)
```

### 5.4 Proactive Suggestions
```python
proactive.py:
- [ ] Morning briefing at wake time 
- [ ] Meeting reminders (15 min before)
- [ ] Weather alerts (rain coming)
- [ ] Task reminders
- [ ] Birthday reminders
- [ ] Travel time alerts
```

**Deliverable:** Alfred provides intelligent, context-aware assistance

---

## 🎯 Phase 6: Productivity & Automation (Week 11-12)
**Goal:** Notes, tasks, and workflow automation

### 6.1 Notes & Tasks
```python
functions/productivity.py:
- [ ] Integration choice (Apple Notes, Notion, Todoist)
- [ ] Create note
- [ ] Add to shopping list
- [ ] Create task
- [ ] Mark task complete
- [ ] Get task list
- [ ] Search notes
- [ ] Set reminder
```

### 6.2 Workflow Automation
```python
functions/workflows.py:
- [ ] "Start work mode"
      → Mac: open work apps, Pi: focus mode, lights: work
      
- [ ] "End work"
      → Save all, git commit, close apps, summary
      
- [ ] "Movie time"
      → Dim lights, TV on, phone silent
      
- [ ] "I'm leaving"
      → Lights off, lock Mac, arm security
      
- [ ] "Bedtime routine"
      → Mac sleep, lights off, set alarm
```

### 6.3 Voice Journal
```python
functions/journal.py:
- [ ] Record journal entry
- [ ] Read past entries
- [ ] Search journal
- [ ] Daily reflection prompt
- [ ] Mood tracking
```

**Deliverable:** Alfred manages tasks and automates routines

---

## 🎯 Phase 7: Smart Home Integration (Future - Week 13+)
**Goal:** Control lights, climate, and devices

### 7.1 Home Assistant Setup
- [ ] Install Home Assistant on Pi or separate device
- [ ] Configure devices
- [ ] API integration

### 7.2 Lighting Control
```python
functions/smart_home/lights.py:
- [ ] Turn on/off lights by room
- [ ] Dim to percentage
- [ ] Set color/temperature
- [ ] Scenes (movie, focus, party)
- [ ] Schedule automation
```

### 7.3 Climate Control
```python
functions/smart_home/climate.py:
- [ ] Set temperature
- [ ] Turn on/off AC/heater
- [ ] Get current temperature
- [ ] Humidity control
```

### 7.4 Security & Sensors
```python
functions/smart_home/security.py:
- [ ] Arm/disarm system
- [ ] Check door/window status
- [ ] Lock/unlock doors
- [ ] Motion detection status
- [ ] Camera feeds
```

**Deliverable:** Alfred controls your smart home

---

## 🎯 Phase 8: Advanced Features (Ongoing)
**Goal:** Continuous improvement and new capabilities

### 8.1 Learning & Adaptation
- [ ] Track command usage patterns
- [ ] Personalized responses
- [ ] Predictive suggestions
- [ ] Habit recognition

### 8.2 Multi-User Support
- [ ] Voice recognition for family members
- [ ] User-specific contexts
- [ ] Separate PINs per user
- [ ] Privacy controls

### 8.3 Data Analytics
- [ ] Email response time tracking
- [ ] Calendar utilization
- [ ] Productivity insights
- [ ] Health habit tracking

### 8.4 External Integrations
- [ ] Banking/finance APIs
- [ ] Fitness tracking
- [ ] Food delivery
- [ ] Transportation (Uber, public transit)

---

## 🛠️ Technical Requirements

### Hardware
- ✅ Raspberry Pi 5 8GB
- ✅ Microphone
- ✅ USB speakers (recommended: Logitech Z150 or Creative Pebble)
- ✅ Mac with SSH enabled
- ✅ Network connection

### Software - Pi
```bash
# System packages
sudo apt-get update
sudo apt-get install -y espeak-ng portaudio19-dev python3-pip

# Python packages
pip install numpy scipy librosa onnxruntime sounddevice
pip install paramiko python-telegram-bot pywhatkit requests
pip install openai-whisper  # if running locally
```

### Software - Mac
```bash
# Enable SSH
System Settings → Sharing → Remote Login (ON)

# Install Whisper Docker (if not done)
docker run -d -p 9999:9000 --name whisper onerahmet/openai-whisper-asr-webservice

# Generate SSH key on Pi
ssh-keygen -t rsa
ssh-copy-id your_user@mac_ip
```

### API Keys & Services
- [ ] OpenWeatherMap API (free tier)
- [ ] Telegram Bot Token (free)
- [ ] Spotify API credentials (free)
- [ ] Twilio (optional, for WhatsApp)
- [ ] Home Assistant (when ready)

---

## 📊 Success Criteria

### Phase 1 Complete When: ✅ **ALL CRITERIA MET!**
- ✅ Alfred responds to wake word
- ✅ Answers weather, time, system queries
- ✅ Speaks with British butler personality
- ✅ Switches between Italian and English
- ✅ Handles complex multi-part queries (NEW!)
- ✅ Concatenates multiple intents (NEW!)
- ✅ Provides general conversational responses (NEW!)

### Phase 2 Complete When:
- ✅ Can read and send emails
- ✅ Manages calendar events
- ✅ Opens Mac applications remotely
- ✅ PIN protection works

### Phase 3 Complete When:
- ✅ Sends Telegram messages
- ✅ Sends WhatsApp messages
- ✅ Finds contacts by name

### Phase 4 Complete When:
- ✅ Controls Spotify playback
- ✅ Runs development commands
- ✅ Checks code repositories

### Phase 5 Complete When:
- ✅ Handles complex context-aware queries
- ✅ Provides morning briefings
- ✅ Gives proactive suggestions

### Phase 6 Complete When:
- ✅ Manages tasks and notes
- ✅ Executes workflow automations
- ✅ Keeps voice journal

### Phase 7 Complete When:
- ✅ Controls smart home devices
- ✅ Manages security system
- ✅ Automates home routines

---

## 🐛 Testing Strategy

### Unit Tests
- Test each function independently
- Mock external APIs
- Verify error handling

### Integration Tests
- Test SSH connectivity
- Test API integrations
- Test Whisper transcription
- Test Ollama reasoning

### End-to-End Tests
- Full conversation flows
- Complex query scenarios
- Error recovery
- PIN verification

### Manual Testing Checklist
```
[ ] Wake word detection accuracy
[ ] Transcription accuracy (Italian & English)
[ ] Intent understanding
[ ] Function execution
[ ] Response generation
[ ] TTS quality
[ ] PIN security
[ ] SSH reliability
[ ] API rate limits
[ ] Error messages clarity
```

---

## 📝 Documentation

### Code Documentation
- Docstrings for all functions
- Type hints
- Inline comments for complex logic
- README for each module

### User Documentation
- Setup guide
- Command reference
- Configuration guide
- Troubleshooting FAQ
- Privacy policy

---

## 🔐 Security Checklist

- [ ] SSH keys (no passwords)
- [ ] API tokens in encrypted config
- [ ] PIN hashing (bcrypt)
- [ ] Sensitive action logging
- [ ] Rate limiting on PIN attempts
- [ ] Secure credential storage
- [ ] HTTPS for all API calls
- [ ] Regular security audits

---

## 🚀 Deployment

### Development Environment
- Code on Mac, test on Pi
- Git repository for version control
- Separate config for dev/prod

### Production Setup
- Systemd service for auto-start
- Log rotation
- Automatic restart on failure
- Health check monitoring

---

## 📈 Future Enhancements

### Short Term (3-6 months)
- Voice recognition for family members
- Mobile app for remote control
- Web dashboard for monitoring
- Plugin system for extensions

### Long Term (6-12 months)
- Computer vision integration
- Emotion detection in voice
- Predictive behavior modeling
- Multi-room audio support
- Alfred teaching mode (learn from corrections)

---

## 🎓 Learning Resources

- Ollama documentation: https://ollama.ai/docs
- Apple AppleScript guide: https://developer.apple.com/applescript
- Telegram Bot API: https://core.telegram.org/bots/api
- Home Assistant: https://www.home-assistant.io/docs
- Whisper: https://github.com/openai/whisper

---

**Version:** 1.0  
**Last Updated:** 2025-10-08  
**Status:** Ready to begin Phase 1 🚀