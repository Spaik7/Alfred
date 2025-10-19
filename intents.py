#!/usr/bin/env python3
"""
Intent Parser for Alfred
Fast rule-based parser with language detection and parameter extraction
Falls back to LLM only for ambiguous cases
"""

import re
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

# Import default location from config
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))  # Go up to project root
    from config import DEFAULT_LOCATION
except ImportError:
    DEFAULT_LOCATION = "Santhia"

class Language(Enum):
    ENGLISH = "en"
    ITALIAN = "it"

class IntentType(Enum):
    # Basic queries
    WEATHER = "weather"                      # AI (minimal essential data only)
    TIME = "time"                            # TEMPLATE (simple_templates.py)
    DATE = "date"                            # TEMPLATE (simple_templates.py)

    # Email
    EMAIL_CHECK = "email_check"              # AI (uses SSH to Mac, Ollama for response)
    EMAIL_LIST = "email_list"                # AI (list recent emails)
    EMAIL_READ = "email_read"                # NOT IMPLEMENTED
    EMAIL_SEND = "email_send"                # NOT IMPLEMENTED
    EMAIL_SEARCH = "email_search"            # NOT IMPLEMENTED

    # Calendar
    CALENDAR_TODAY = "calendar_today"        # AI (uses SSH to Mac, Ollama for response)
    CALENDAR_YESTERDAY = "calendar_yesterday" # AI (uses SSH to Mac, Ollama for response)
    CALENDAR_TOMORROW = "calendar_tomorrow"  # AI (uses SSH to Mac, Ollama for response)
    CALENDAR_SPECIFIC = "calendar_specific"  # AI (check specific calendar by name)
    CALENDAR_WEEK = "calendar_week"          # NOT IMPLEMENTED
    CALENDAR_NEXT = "calendar_next"          # NOT IMPLEMENTED
    CALENDAR_CREATE = "calendar_create"      # NOT IMPLEMENTED

    # System
    SYSTEM_STATUS = "system_status"          # AI (combines multiple metrics)
    SYSTEM_SHUTDOWN = "system_shutdown"      # NOT IMPLEMENTED
    VOLUME_UP = "volume_up"                  # TEMPLATE (simple_templates.py)
    VOLUME_DOWN = "volume_down"              # TEMPLATE (simple_templates.py)
    VOLUME_SET = "volume_set"                # TEMPLATE (simple_templates.py)

    # Mac control
    MAC_OPEN_APP = "mac_open_app"            # NOT IMPLEMENTED
    MAC_CLOSE_APP = "mac_close_app"          # NOT IMPLEMENTED
    MAC_VOLUME = "mac_volume"                # NOT IMPLEMENTED
    MAC_SLEEP = "mac_sleep"                  # NOT IMPLEMENTED
    MAC_LOCK = "mac_lock"                    # NOT IMPLEMENTED

    # Messaging
    TELEGRAM_SEND = "telegram_send"          # NOT IMPLEMENTED
    TELEGRAM_CHECK = "telegram_check"        # NOT IMPLEMENTED
    TELEGRAM_READ = "telegram_read"          # NOT IMPLEMENTED
    WHATSAPP_SEND = "whatsapp_send"          # NOT IMPLEMENTED
    WHATSAPP_CHECK = "whatsapp_check"        # NOT IMPLEMENTED
    WHATSAPP_READ = "whatsapp_read"          # NOT IMPLEMENTED

    # General
    JOKE = "joke"                            # TEMPLATE (simple_templates.py - returns joke as-is)
    TRANSLATE = "translate"                  # NOT IMPLEMENTED
    CALCULATE = "calculate"                  # TEMPLATE (simple_templates.py)
    GENERAL_CHAT = "general_chat"            # NOT IMPLEMENTED (fallback intent)

    # Information & Services
    NEWS = "news"                            # SPECIAL HANDLING (multiple headlines)
    FINANCE = "finance"                      # SPECIAL HANDLING (multiple stocks)
    FINANCE_WATCHLIST = "finance_watchlist"  # SPECIAL HANDLING (multiple stocks)
    RECIPE_SEARCH = "recipe_search"          # SPECIAL HANDLING (multiple recipes)
    RECIPE_RANDOM = "recipe_random"          # SPECIAL HANDLING (single recipe)
    TRANSPORT_CAR = "transport_car"          # SPECIAL HANDLING (directions)
    TRANSPORT_PUBLIC = "transport_public"    # SPECIAL HANDLING (transit steps)

    # Unknown
    UNKNOWN = "unknown"                      # NOT IMPLEMENTED

class IntentParser:
    """Rule-based intent parser with language detection"""
    
    # Italian keywords for language detection
    ITALIAN_KEYWORDS = {
        'che', 'tempo', 'fa', 'ora', 'è', 'sono', 'oggi', 'domani',
        'email', 'posta', 'manda', 'invia', 'apri', 'chiudi', 'dimmi',
        'quanto', 'come', 'dove', 'quando', 'perché', 'calendario',
        'appuntamento', 'sveglia', 'promemoria', 'battuta', 'scherzo',
        'cerca', 'trova', 'settimana', 'spegni', 'blocca', 'volume',
        'traduci', 'calcola', 'leggi', 'messaggi', 'mostrami', 'digli',
        'dille', 'dimmi', 'controlla', 'ultimi', 'nuovi'
    }
    
    # English keywords
    ENGLISH_KEYWORDS = {
        'what', 'weather', 'time', 'is', 'are', 'today', 'tomorrow',
        'email', 'mail', 'send', 'open', 'close', 'tell', 'me',
        'how', 'where', 'when', 'why', 'calendar', 'appointment',
        'alarm', 'reminder', 'joke', 'funny', 'search', 'find',
        'week', 'shutdown', 'lock', 'volume', 'translate', 'calculate'
    }
    
    def __init__(self, default_location: str = None):
        self.default_location = default_location if default_location else DEFAULT_LOCATION
        self.patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[str, List[tuple]]:
        """Compile regex patterns for each intent - ORDER MATTERS!"""
        return {
            # IMPORTANT: Specific patterns must come BEFORE general ones
            # Weather and Date must come BEFORE Calendar to avoid "oggi" conflicts
            
            # Time - specific phrases
            'time': [
                # English
                (r"what time is it", Language.ENGLISH, IntentType.TIME),
                (r"what'?s? the time", Language.ENGLISH, IntentType.TIME),
                (r"tell me the time", Language.ENGLISH, IntentType.TIME),
                # Italian  
                (r"che or[ae] (?:è|sono)", Language.ITALIAN, IntentType.TIME),
                (r"(?:mi )?di[ci]? (?:che ore sono|l'ora) (?:che ora è)", Language.ITALIAN, IntentType.TIME),
            ],
            
            # Date - must match BEFORE calendar_today
            'date': [
                # English
                (r"what'?s? (?:the )?date", Language.ENGLISH, IntentType.DATE),
                (r"what day is it", Language.ENGLISH, IntentType.DATE),
                # Italian - "che giorno è" must match before calendar
                (r"che giorno (?:è|e)(?: oggi)?", Language.ITALIAN, IntentType.DATE),
                (r"(?:mi )?di[ci]? la data", Language.ITALIAN, IntentType.DATE),
            ],
            
            # Weather - must match BEFORE calendar to avoid "oggi" matching calendar_today
            'weather': [
                # English
                (r"what'?s? (?:the )?weather(?: like)?(?: today)?(?: in (.+))?", Language.ENGLISH, IntentType.WEATHER),
                (r"how'?s? (?:the )?weather(?: today)?(?: in (.+))?", Language.ENGLISH, IntentType.WEATHER),
                (r"is it (?:going to )?rain(?: today)?(?: in (.+))?", Language.ENGLISH, IntentType.WEATHER),
                (r"weather (?:forecast )?(in |for )?(.+)?", Language.ENGLISH, IntentType.WEATHER),
                # Italian - "che tempo fa" is THE weather question
                (r"che tempo fa(?: oggi)?(?: a (.+))?", Language.ITALIAN, IntentType.WEATHER),
                (r"com'?è il tempo(?: oggi)?(?: a (.+))?", Language.ITALIAN, IntentType.WEATHER),
                (r"piove(?: oggi)?(?: a (.+))?", Language.ITALIAN, IntentType.WEATHER),
                (r"(?:il )?meteo(?: oggi)?(?: (?:a|di) (.+))?", Language.ITALIAN, IntentType.WEATHER),
            ],
            
            # Email - Specific actions first
            'email_send': [
                # English - More flexible verb forms
                (r"send (?:an )?email to (.+?) (?:saying|says?|and says?|that|to say) (.+)", Language.ENGLISH, IntentType.EMAIL_SEND),
                (r"email (.+?) (?:and say|saying|says|that) (.+)", Language.ENGLISH, IntentType.EMAIL_SEND),
                (r"(?:write|compose) (?:an )?email to (.+)", Language.ENGLISH, IntentType.EMAIL_SEND),
                # Italian - More flexible with pronouns (digli, dille, dimmi, etc.)
                (r"manda (?:un'?)?email a (.+?) (?:e )?(?:dic[iae](?:ndo)?|che dice|di(?:gli|lle|mmi|ci|vi)) (.+)", Language.ITALIAN, IntentType.EMAIL_SEND),
                (r"invia (?:un'?)?email a (.+?) (?:e )?(?:dic[iae](?:ndo)?|di(?:gli|lle|mmi|ci|vi)|con )?(?:il testo )?(.+)", Language.ITALIAN, IntentType.EMAIL_SEND),
            ],
            'email_search': [
                # English
                (r"search (?:my )?emails? (?:for |about )(.+)", Language.ENGLISH, IntentType.EMAIL_SEARCH),
                (r"find emails? (?:about |with |containing )(.+)", Language.ENGLISH, IntentType.EMAIL_SEARCH),
                # Italian
                (r"cerca (?:nelle )?email (.+)", Language.ITALIAN, IntentType.EMAIL_SEARCH),
                (r"trova email (?:su |con |riguardo )(.+)", Language.ITALIAN, IntentType.EMAIL_SEARCH),
            ],
            'email_read': [
                # English
                (r"read (?:my )?(?:latest |last |recent )?emails?(?: from (.+))?", Language.ENGLISH, IntentType.EMAIL_READ),
                (r"show me emails? from (.+)", Language.ENGLISH, IntentType.EMAIL_READ),
                # Italian
                (r"leggi (?:le )?(?:ultime )?email(?: di (.+))?", Language.ITALIAN, IntentType.EMAIL_READ),
                (r"mostrami (?:le )?email di (.+)", Language.ITALIAN, IntentType.EMAIL_READ),
            ],
            'email_check': [
                # English
                (r"check (?:my )?(?:emails?|mail|inbox)", Language.ENGLISH, IntentType.EMAIL_CHECK),
                (r"(?:do i have |any )(?:new )?(?:unread )?emails?", Language.ENGLISH, IntentType.EMAIL_CHECK),
                # Italian
                (r"controlla (?:la )?(?:posta|email)", Language.ITALIAN, IntentType.EMAIL_CHECK),
                (r"(?:ho )?(?:nuove )?email", Language.ITALIAN, IntentType.EMAIL_CHECK),
            ],
            'email_list': [
                # English
                (r"(?:show|list|get)(?: me)?(?: my)? (?:recent |last |latest )?emails?", Language.ENGLISH, IntentType.EMAIL_LIST),
                (r"what are (?:my )?(?:recent |last |latest )?emails?", Language.ENGLISH, IntentType.EMAIL_LIST),
                (r"read (?:my )?(?:recent |last )?emails?", Language.ENGLISH, IntentType.EMAIL_LIST),
                # Italian
                (r"(?:mostrami|dammi|elenca)(?: le)? (?:ultime |recenti )?email", Language.ITALIAN, IntentType.EMAIL_LIST),
                (r"quali sono le (?:ultime |recenti )?email", Language.ITALIAN, IntentType.EMAIL_LIST),
                (r"leggi (?:le )?(?:ultime |recenti )?email", Language.ITALIAN, IntentType.EMAIL_LIST),
            ],

            # Calendar - NOW comes after weather/date
            'calendar_week': [
                # English
                (r"what'?s? (?:on )?(?:my )?(?:calendar|schedule) (?:this |for (?:the )?)?week", Language.ENGLISH, IntentType.CALENDAR_WEEK),
                (r"(?:show me )?(?:my )?(?:events|appointments) (?:for )?(?:this |the )?week", Language.ENGLISH, IntentType.CALENDAR_WEEK),
                # Italian
                (r"(?:cosa ho in )?calendario (?:questa |della )?settimana", Language.ITALIAN, IntentType.CALENDAR_WEEK),
                (r"(?:mostrami )?(?:gli )?appuntamenti (?:di |della )?(?:questa )?settimana", Language.ITALIAN, IntentType.CALENDAR_WEEK),
            ],
            'calendar_create': [
                # English
                (r"create (?:an? )?(?:event|appointment|meeting) (.+)", Language.ENGLISH, IntentType.CALENDAR_CREATE),
                (r"add (?:to calendar|event) (.+)", Language.ENGLISH, IntentType.CALENDAR_CREATE),
                (r"schedule (?:an? )?(?:event|appointment|meeting) (.+)", Language.ENGLISH, IntentType.CALENDAR_CREATE),
                # Italian
                (r"crea (?:un )?(?:evento|appuntamento) (.+)", Language.ITALIAN, IntentType.CALENDAR_CREATE),
                (r"aggiungi (?:al calendario|evento) (.+)", Language.ITALIAN, IntentType.CALENDAR_CREATE),
            ],
            'calendar_next': [
                # English
                (r"what'?s? (?:my )?next (?:event|appointment|meeting)", Language.ENGLISH, IntentType.CALENDAR_NEXT),
                (r"when is (?:my )?next (?:event|appointment|meeting)", Language.ENGLISH, IntentType.CALENDAR_NEXT),
                # Italian
                (r"(?:qual è il|quando è) (?:mio )?prossimo (?:evento|appuntamento)", Language.ITALIAN, IntentType.CALENDAR_NEXT),
            ],
            'calendar_today': [
                # English - More specific now (doesn't catch everything)
                (r"what'?s? (?:on )?(?:my )?(?:calendar|schedule) today", Language.ENGLISH, IntentType.CALENDAR_TODAY),
                (r"(?:do i have )?(?:any )?(?:events|appointments|meetings) today", Language.ENGLISH, IntentType.CALENDAR_TODAY),
                (r"what'?s? (?:on )?(?:my )?(?:calendar|schedule)(?:\?)?$", Language.ENGLISH, IntentType.CALENDAR_TODAY),
                (r"check (?:my |the )?(?:calendar|schedule)(?:\?)?$", Language.ENGLISH, IntentType.CALENDAR_TODAY),
                # Italian - More specific (doesn't match "che tempo" or "che giorno")
                (r"(?:cosa|che cosa) (?:ho |c'è )?(?:in )?(?:calendario|programma)(?: oggi)?", Language.ITALIAN, IntentType.CALENDAR_TODAY),
                (r"(?:ho )?appuntamenti oggi", Language.ITALIAN, IntentType.CALENDAR_TODAY),
                (r"controlla (?:il )?calendario(?:\?)?$", Language.ITALIAN, IntentType.CALENDAR_TODAY),
            ],
            'calendar_yesterday': [
                # English
                (r"what'?s? (?:was )?(?:on )?(?:my )?(?:calendar|schedule) yesterday", Language.ENGLISH, IntentType.CALENDAR_YESTERDAY),
                (r"(?:did i have )?(?:any )?(?:events|appointments|meetings) yesterday", Language.ENGLISH, IntentType.CALENDAR_YESTERDAY),
                (r"what (?:was|were) (?:my )?(?:events|appointments) yesterday", Language.ENGLISH, IntentType.CALENDAR_YESTERDAY),
                (r"check (?:my |the )?(?:calendar|schedule) yesterday", Language.ENGLISH, IntentType.CALENDAR_YESTERDAY),
                # Italian
                (r"(?:cosa|che cosa) (?:ho avuto|c'era) (?:in )?(?:calendario|programma) ieri", Language.ITALIAN, IntentType.CALENDAR_YESTERDAY),
                (r"(?:avevo )?appuntamenti ieri", Language.ITALIAN, IntentType.CALENDAR_YESTERDAY),
                (r"controlla (?:il )?calendario ieri", Language.ITALIAN, IntentType.CALENDAR_YESTERDAY),
            ],
            'calendar_tomorrow': [
                # English
                (r"what'?s? (?:on )?(?:my )?(?:calendar|schedule) tomorrow", Language.ENGLISH, IntentType.CALENDAR_TOMORROW),
                (r"(?:do i have )?(?:any )?(?:events|appointments|meetings) tomorrow", Language.ENGLISH, IntentType.CALENDAR_TOMORROW),
                (r"what'?s? tomorrow'?s? (?:schedule|calendar|events?)", Language.ENGLISH, IntentType.CALENDAR_TOMORROW),
                (r"check (?:my |the )?(?:calendar|schedule) tomorrow", Language.ENGLISH, IntentType.CALENDAR_TOMORROW),
                # Italian
                (r"(?:cosa|che cosa) (?:ho |c'è )?(?:in )?(?:calendario|programma) domani", Language.ITALIAN, IntentType.CALENDAR_TOMORROW),
                (r"(?:ho )?appuntamenti domani", Language.ITALIAN, IntentType.CALENDAR_TOMORROW),
                (r"controlla (?:il )?calendario domani", Language.ITALIAN, IntentType.CALENDAR_TOMORROW),
            ],
            'calendar_specific': [
                # English - Must have specific calendar name (not "my", "the", "a")
                # Pattern: "check [specific name] calendar" - excludes articles/pronouns
                (r"check (?:my |the )?([A-Z]\w+) calendar", Language.ENGLISH, IntentType.CALENDAR_SPECIFIC),
                (r"(?:what'?s?|what is) (?:on|in) (?:my |the )?([A-Z]\w+) calendar", Language.ENGLISH, IntentType.CALENDAR_SPECIFIC),
                (r"(?:do i have )?(?:any )?(?:events|appointments) (?:on|in) (?:my |the )?([A-Z]\w+) calendar", Language.ENGLISH, IntentType.CALENDAR_SPECIFIC),
                (r"show (?:me )?(?:my |the )?([A-Z]\w+) calendar", Language.ENGLISH, IntentType.CALENDAR_SPECIFIC),
                # Italian - Must have specific calendar name after "calendario"
                (r"controlla (?:il )?calendario ([A-Z]\w+)", Language.ITALIAN, IntentType.CALENDAR_SPECIFIC),
                (r"(?:cosa|che cosa) (?:ho |c'è )?(?:nel|in) calendario ([A-Z]\w+)", Language.ITALIAN, IntentType.CALENDAR_SPECIFIC),
                (r"(?:ho )?appuntamenti (?:nel|in|sul) calendario ([A-Z]\w+)", Language.ITALIAN, IntentType.CALENDAR_SPECIFIC),
                (r"mostra(?:mi)? (?:il )?calendario ([A-Z]\w+)", Language.ITALIAN, IntentType.CALENDAR_SPECIFIC),
            ],

            # System
            'system_shutdown': [
                # English
                (r"shutdown (?:the )?(?:mac|computer|system)", Language.ENGLISH, IntentType.SYSTEM_SHUTDOWN),
                (r"turn off (?:the )?(?:mac|computer)", Language.ENGLISH, IntentType.SYSTEM_SHUTDOWN),
                (r"power off (?:the )?mac", Language.ENGLISH, IntentType.SYSTEM_SHUTDOWN),
                # Italian
                (r"spegni (?:il )?(?:mac|computer)", Language.ITALIAN, IntentType.SYSTEM_SHUTDOWN),
                (r"arresta (?:il )?sistema", Language.ITALIAN, IntentType.SYSTEM_SHUTDOWN),
            ],
            'system_status': [
                # English
                (r"how'?s? (?:the )?(?:pi|raspberry|system)(?: doing)?", Language.ENGLISH, IntentType.SYSTEM_STATUS),
                (r"(?:system|pi) status", Language.ENGLISH, IntentType.SYSTEM_STATUS),
                (r"check (?:the )?(?:system|pi)", Language.ENGLISH, IntentType.SYSTEM_STATUS),
                # Italian
                (r"come sta (?:il )?(?:pi|sistema)", Language.ITALIAN, IntentType.SYSTEM_STATUS),
                (r"stato (?:del )?sistema", Language.ITALIAN, IntentType.SYSTEM_STATUS),
            ],

            # Local volume control (Pi speakers)
            'volume_set': [
                # English
                (r"set (?:the )?volume (?:to |at )?(\d+)", Language.ENGLISH, IntentType.VOLUME_SET),
                (r"volume (?:to |at )?(\d+)", Language.ENGLISH, IntentType.VOLUME_SET),
                # Italian
                (r"(?:imposta|metti) (?:il )?volume a (\d+)", Language.ITALIAN, IntentType.VOLUME_SET),
                (r"volume a (\d+)", Language.ITALIAN, IntentType.VOLUME_SET),
            ],
            'volume_up': [
                # English
                (r"volume up(?: (\d+))?", Language.ENGLISH, IntentType.VOLUME_UP),
                (r"(?:turn|crank) (?:the )?volume up(?: (\d+))?", Language.ENGLISH, IntentType.VOLUME_UP),
                (r"(?:make it )?louder(?: (\d+))?", Language.ENGLISH, IntentType.VOLUME_UP),
                (r"increase (?:the )?volume(?: by )?(\d+)?", Language.ENGLISH, IntentType.VOLUME_UP),
                # Italian
                (r"alza (?:il )?volume(?: di )?(\d+)?", Language.ITALIAN, IntentType.VOLUME_UP),
                (r"aumenta (?:il )?volume(?: di )?(\d+)?", Language.ITALIAN, IntentType.VOLUME_UP),
                (r"più forte(?: di )?(\d+)?", Language.ITALIAN, IntentType.VOLUME_UP),
            ],
            'volume_down': [
                # English
                (r"volume down(?: (\d+))?", Language.ENGLISH, IntentType.VOLUME_DOWN),
                (r"(?:turn|lower) (?:the )?volume down(?: (\d+))?", Language.ENGLISH, IntentType.VOLUME_DOWN),
                (r"(?:make it )?quieter(?: (\d+))?", Language.ENGLISH, IntentType.VOLUME_DOWN),
                (r"decrease (?:the )?volume(?: by )?(\d+)?", Language.ENGLISH, IntentType.VOLUME_DOWN),
                # Italian
                (r"abbassa (?:il )?volume(?: di )?(\d+)?", Language.ITALIAN, IntentType.VOLUME_DOWN),
                (r"diminuisci (?:il )?volume(?: di )?(\d+)?", Language.ITALIAN, IntentType.VOLUME_DOWN),
                (r"più piano(?: di )?(\d+)?", Language.ITALIAN, IntentType.VOLUME_DOWN),
            ],

            # Mac control - More specific patterns
            'mac_close_app': [
                # English - Must come before mac_open_app, capture multiple words
                (r"close (.+?)$", Language.ENGLISH, IntentType.MAC_CLOSE_APP),
                (r"quit (.+?)$", Language.ENGLISH, IntentType.MAC_CLOSE_APP),
                (r"exit (.+?)$", Language.ENGLISH, IntentType.MAC_CLOSE_APP),
                # Italian
                (r"chiudi (.+?)$", Language.ITALIAN, IntentType.MAC_CLOSE_APP),
                (r"esci da (.+?)$", Language.ITALIAN, IntentType.MAC_CLOSE_APP),
            ],
            'mac_open_app': [
                # English - Capture multiple words
                (r"open (.+?)(?:\s+on.*)?$", Language.ENGLISH, IntentType.MAC_OPEN_APP),
                (r"launch (.+?)$", Language.ENGLISH, IntentType.MAC_OPEN_APP),
                (r"start (.+?)$", Language.ENGLISH, IntentType.MAC_OPEN_APP),
                # Italian - Capture multiple words
                (r"apri (.+?)(?:\s+sul.*)?$", Language.ITALIAN, IntentType.MAC_OPEN_APP),
                (r"avvia (.+?)$", Language.ITALIAN, IntentType.MAC_OPEN_APP),
            ],
            'mac_volume': [
                # English
                (r"set volume to (\d+)", Language.ENGLISH, IntentType.MAC_VOLUME),
                (r"(?:turn )?volume (?:to |at )?(\d+)", Language.ENGLISH, IntentType.MAC_VOLUME),
                (r"(?:make it |set )?(?:louder|quieter|mute)", Language.ENGLISH, IntentType.MAC_VOLUME),
                # Italian
                (r"(?:imposta |metti )?volume a (\d+)", Language.ITALIAN, IntentType.MAC_VOLUME),
                (r"(?:alza|abbassa|silenzia) (?:il )?volume", Language.ITALIAN, IntentType.MAC_VOLUME),
            ],
            'mac_sleep': [
                # English
                (r"(?:put )?(?:the )?mac to sleep", Language.ENGLISH, IntentType.MAC_SLEEP),
                (r"sleep (?:the )?(?:mac|computer)", Language.ENGLISH, IntentType.MAC_SLEEP),
                # Italian
                (r"metti (?:il )?mac in (?:sleep|stop|pausa)", Language.ITALIAN, IntentType.MAC_SLEEP),
                (r"sospendi (?:il )?(?:mac|computer)", Language.ITALIAN, IntentType.MAC_SLEEP),
            ],
            'mac_lock': [
                # English
                (r"lock (?:the )?(?:screen|mac|computer)", Language.ENGLISH, IntentType.MAC_LOCK),
                (r"lock it", Language.ENGLISH, IntentType.MAC_LOCK),
                # Italian
                (r"blocca (?:lo )?schermo", Language.ITALIAN, IntentType.MAC_LOCK),
                (r"blocca (?:il )?mac", Language.ITALIAN, IntentType.MAC_LOCK),
            ],
            
            # Messaging
            'telegram_send': [
                # English
                (r"send (?:a )?telegram (?:message )?to (.+?) saying (.+)", Language.ENGLISH, IntentType.TELEGRAM_SEND),
                (r"telegram (.+?) (?:saying|that) (.+)", Language.ENGLISH, IntentType.TELEGRAM_SEND),
                (r"message (.+?) on telegram (.+)", Language.ENGLISH, IntentType.TELEGRAM_SEND),
                # Italian - with pronouns
                (r"manda (?:un )?telegram a (.+?) (?:e )?(?:dicendo|che dice|di(?:gli|lle|mmi|ci|vi)) (.+)", Language.ITALIAN, IntentType.TELEGRAM_SEND),
                (r"invia messaggio telegram a (.+?) (?:e )?(?:dicendo|di(?:gli|lle|mmi|ci|vi))? (.+)", Language.ITALIAN, IntentType.TELEGRAM_SEND),
            ],
            'telegram_check': [
                # English
                (r"check (?:my )?(?:telegram|telegram messages?)", Language.ENGLISH, IntentType.TELEGRAM_CHECK),
                (r"(?:do i have |any )(?:new )?telegram messages?", Language.ENGLISH, IntentType.TELEGRAM_CHECK),
                # Italian
                (r"(?:ho |controlla )(?:nuovi )?messaggi (?:su )?telegram", Language.ITALIAN, IntentType.TELEGRAM_CHECK),
                (r"(?:ci sono )?messaggi (?:su )?telegram", Language.ITALIAN, IntentType.TELEGRAM_CHECK),
            ],
            'telegram_read': [
                # English
                (r"read (?:my )?(?:latest |last |recent )?telegram (?:messages?)?(?: from (.+))?", Language.ENGLISH, IntentType.TELEGRAM_READ),
                (r"show me telegram messages? from (.+)", Language.ENGLISH, IntentType.TELEGRAM_READ),
                # Italian
                (r"leggi (?:i miei|gli )?(?:ultimi )?messaggi telegram(?: di (.+))?", Language.ITALIAN, IntentType.TELEGRAM_READ),
                (r"mostrami (?:i )?messaggi telegram di (.+)", Language.ITALIAN, IntentType.TELEGRAM_READ),
            ],
            'whatsapp_send': [
                # English
                (r"send (?:a )?whatsapp (?:message )?to (.+?) saying (.+)", Language.ENGLISH, IntentType.WHATSAPP_SEND),
                (r"whatsapp (.+?) (?:saying|that) (.+)", Language.ENGLISH, IntentType.WHATSAPP_SEND),
                (r"message (.+?) on whatsapp (.+)", Language.ENGLISH, IntentType.WHATSAPP_SEND),
                # Italian - with pronouns
                (r"manda (?:un )?whatsapp a (.+?) (?:e )?(?:dicendo|che dice|di(?:gli|lle|mmi|ci|vi)) (.+)", Language.ITALIAN, IntentType.WHATSAPP_SEND),
                (r"invia messaggio whatsapp a (.+?) (?:e )?(?:dicendo|di(?:gli|lle|mmi|ci|vi))? (.+)", Language.ITALIAN, IntentType.WHATSAPP_SEND),
            ],
            'whatsapp_check': [
                # English
                (r"check (?:my )?(?:whatsapp|whatsapp messages?)", Language.ENGLISH, IntentType.WHATSAPP_CHECK),
                (r"(?:do i have |any )(?:new )?whatsapp messages?", Language.ENGLISH, IntentType.WHATSAPP_CHECK),
                # Italian
                (r"(?:ho |controlla )(?:nuovi )?messaggi (?:su )?whatsapp", Language.ITALIAN, IntentType.WHATSAPP_CHECK),
                (r"(?:ci sono )?messaggi (?:su )?whatsapp", Language.ITALIAN, IntentType.WHATSAPP_CHECK),
            ],
            'whatsapp_read': [
                # English
                (r"read (?:my )?(?:latest |last |recent )?whatsapp (?:messages?)?(?: from (.+))?", Language.ENGLISH, IntentType.WHATSAPP_READ),
                (r"show me whatsapp messages? from (.+)", Language.ENGLISH, IntentType.WHATSAPP_READ),
                # Italian
                (r"leggi (?:i )?(?:ultimi )?messaggi whatsapp(?: di (.+))?", Language.ITALIAN, IntentType.WHATSAPP_READ),
                (r"mostrami (?:i )?messaggi whatsapp di (.+)", Language.ITALIAN, IntentType.WHATSAPP_READ),
            ],
            
            # General functions
            'translate': [
                # English
                (r"translate (.+?) (?:to|into) (\w+)", Language.ENGLISH, IntentType.TRANSLATE),
                (r"how do you say (.+?) in (\w+)", Language.ENGLISH, IntentType.TRANSLATE),
                # Italian
                (r"traduci (.+?) in (\w+)", Language.ITALIAN, IntentType.TRANSLATE),
                (r"come si dice (.+?) in (\w+)", Language.ITALIAN, IntentType.TRANSLATE),
            ],
            'calculate': [
                # English - More specific patterns only
                (r"calculate (.+)", Language.ENGLISH, IntentType.CALCULATE),
                (r"compute (.+)", Language.ENGLISH, IntentType.CALCULATE),
                (r"what(?:'s| is) (\d+[\d\s\+\-\*\/\%\.]+)", Language.ENGLISH, IntentType.CALCULATE),
                (r"what(?:'s| is) (\d+)% of (.+)", Language.ENGLISH, IntentType.CALCULATE),
                # Italian word-based questions
                (r"calcola (.+)", Language.ITALIAN, IntentType.CALCULATE),
                (r"quanto (?:fa|è) (.+)", Language.ITALIAN, IntentType.CALCULATE),
                # Italian percentage patterns - must match before standalone to avoid "50%" being stripped
                (r"(?:il|la) (\d+(?:\.\d+)?)%\s*(?:di|del) (.+)", Language.ITALIAN, IntentType.CALCULATE),
                # Standalone expressions with Italian word operators - CAPTURE EVERYTHING
                (r"^(\d+(?:\.\d+)?\s*(?:più|meno|per|diviso)\s*\d+(?:\.\d+)?)", Language.ITALIAN, IntentType.CALCULATE),
                # English word numbers with all operators including "over" for division
                (r"^([a-z]+\s+(?:plus|minus|times|over|divided by)\s+[a-z]+)", Language.ENGLISH, IntentType.CALCULATE),
                # English numbers with "divided by" (multi-word operator)
                (r"^(\d+(?:\.\d+)?\s+divided\s+by\s+\d+(?:\.\d+)?)", Language.ENGLISH, IntentType.CALCULATE),
                # Standalone math expressions with symbols
                (r"^(\d+[\d\s\+\-\*\/x×÷\%\.]+\d+)", Language.ENGLISH, IntentType.CALCULATE),
            ],
            'joke': [
                # English
                (r"tell me a joke", Language.ENGLISH, IntentType.JOKE),
                (r"make me laugh", Language.ENGLISH, IntentType.JOKE),
                (r"(?:say )?something funny", Language.ENGLISH, IntentType.JOKE),
                # Italian
                (r"dimmi una battuta", Language.ITALIAN, IntentType.JOKE),
                (r"raccontami (?:una barzelletta|uno scherzo)", Language.ITALIAN, IntentType.JOKE),
                (r"fammi ridere", Language.ITALIAN, IntentType.JOKE),
            ],

            # News
            'news': [
                # English
                (r"what'?s? (?:the )?(?:latest )?news", Language.ENGLISH, IntentType.NEWS),
                (r"(?:give me |tell me )?(?:the )?(?:news|headlines)", Language.ENGLISH, IntentType.NEWS),
                (r"any news", Language.ENGLISH, IntentType.NEWS),
                # Italian
                (r"(?:quali sono |dammi )?(?:le )?(?:ultime )?notizie", Language.ITALIAN, IntentType.NEWS),
                (r"che notizie ci sono", Language.ITALIAN, IntentType.NEWS),
                (r"novità", Language.ITALIAN, IntentType.NEWS),
            ],

            # Finance
            'finance': [
                # English - Watchlist
                (r"(?:my )?(?:finance |financial )?watchlist", Language.ENGLISH, IntentType.FINANCE_WATCHLIST),
                (r"(?:check |show )?(?:my )?(?:stocks|investments|portfolio)", Language.ENGLISH, IntentType.FINANCE_WATCHLIST),
                (r"how(?:'s| are) (?:my )?(?:stocks|investments)", Language.ENGLISH, IntentType.FINANCE_WATCHLIST),
                (r"market (?:update|summary)", Language.ENGLISH, IntentType.FINANCE_WATCHLIST),
                # Italian - Watchlist
                (r"(?:i miei )?investimenti", Language.ITALIAN, IntentType.FINANCE_WATCHLIST),
                (r"(?:le mie )?azioni", Language.ITALIAN, IntentType.FINANCE_WATCHLIST),
                (r"come vanno (?:le azioni|gli investimenti)", Language.ITALIAN, IntentType.FINANCE_WATCHLIST),
                (r"mercati", Language.ITALIAN, IntentType.FINANCE_WATCHLIST),
            ],

            # Recipes/Food
            'recipe_search': [
                # English
                (r"(?:find |search |show me )?(?:a )?recipe(?:s)? (?:for |with )?(.+)", Language.ENGLISH, IntentType.RECIPE_SEARCH),
                (r"how (?:do i |to )?(?:make|cook) (.+)", Language.ENGLISH, IntentType.RECIPE_SEARCH),
                (r"(?:i want to |i'll )(?:make|cook) (.+)", Language.ENGLISH, IntentType.RECIPE_SEARCH),
                # Italian
                (r"(?:cerca |trova |mostrami )?(?:una )?ricetta (?:per |di |con )?(.+)", Language.ITALIAN, IntentType.RECIPE_SEARCH),
                (r"come (?:si )?(?:fa|cucina|prepara) (.+)", Language.ITALIAN, IntentType.RECIPE_SEARCH),
                (r"voglio (?:fare|cucinare|preparare) (.+)", Language.ITALIAN, IntentType.RECIPE_SEARCH),
            ],
            'recipe_random': [
                # English
                (r"(?:give me |suggest |show me )?(?:a )?random recipe", Language.ENGLISH, IntentType.RECIPE_RANDOM),
                (r"(?:what|something) (?:should i |can i |to )(?:cook|make|eat)", Language.ENGLISH, IntentType.RECIPE_RANDOM),
                (r"recipe idea", Language.ENGLISH, IntentType.RECIPE_RANDOM),
                # Italian
                (r"ricetta (?:a )?caso", Language.ITALIAN, IntentType.RECIPE_RANDOM),
                (r"(?:cosa |che cosa )?(?:posso |dovrei )?(?:cucinare|preparare|mangiare)", Language.ITALIAN, IntentType.RECIPE_RANDOM),
                (r"suggerimento ricetta", Language.ITALIAN, IntentType.RECIPE_RANDOM),
            ],

            # Transport
            'transport_car': [
                # English - with arrival time
                (r"(?:get to|arrive at) (.+?) (?:by|at) (\d{1,2}(?::\d{2})?(?: ?(?:am|pm))?)(?: by car)?", Language.ENGLISH, IntentType.TRANSPORT_CAR),
                (r"traffic to (.+?) (?:to arrive )?(?:by|at) (\d{1,2}(?::\d{2})?(?: ?(?:am|pm))?)", Language.ENGLISH, IntentType.TRANSPORT_CAR),
                # English - without arrival time
                (r"how long (?:to get )?to (.+?) (?:by car)?", Language.ENGLISH, IntentType.TRANSPORT_CAR),
                (r"(?:driving )?(?:time|traffic) to (.+)", Language.ENGLISH, IntentType.TRANSPORT_CAR),
                (r"how's (?:the )?traffic to (.+)", Language.ENGLISH, IntentType.TRANSPORT_CAR),
                (r"route to (.+)", Language.ENGLISH, IntentType.TRANSPORT_CAR),
                # Italian - with arrival time
                (r"arrivare a (.+?) (?:alle|per le) (\d{1,2}(?::\d{2})?)(?: in macchina)?", Language.ITALIAN, IntentType.TRANSPORT_CAR),
                (r"traffico (?:per |verso )?(.+?) per arrivare alle (\d{1,2}(?::\d{2})?)", Language.ITALIAN, IntentType.TRANSPORT_CAR),
                # Italian - without arrival time
                (r"quanto (?:ci vuole|tempo) per (?:andare a |arrivare a )?(.+?)(?: in macchina)?", Language.ITALIAN, IntentType.TRANSPORT_CAR),
                (r"traffico (?:per |verso )?(.+)", Language.ITALIAN, IntentType.TRANSPORT_CAR),
                (r"strada per (.+)", Language.ITALIAN, IntentType.TRANSPORT_CAR),
            ],
            'transport_public': [
                # English - with arrival time
                (r"(?:get to|arrive at) (.+?) (?:by|at) (\d{1,2}(?::\d{2})?(?: ?(?:am|pm))?) (?:by )?(?:bus|train|public (?:transit|transport))", Language.ENGLISH, IntentType.TRANSPORT_PUBLIC),
                (r"when (?:should i |do i need to |to )leave (?:for |to get to )?(.+?) (?:by|at) (\d{1,2}(?::\d{2})?(?: ?(?:am|pm))?)", Language.ENGLISH, IntentType.TRANSPORT_PUBLIC),
                (r"(?:public )?(?:transit|transport|bus|train) to (.+?) (?:by|at) (\d{1,2}(?::\d{2})?(?: ?(?:am|pm))?)", Language.ENGLISH, IntentType.TRANSPORT_PUBLIC),
                # English - without arrival time
                (r"(?:public )?(?:transit|transport|bus|train) to (.+)", Language.ENGLISH, IntentType.TRANSPORT_PUBLIC),
                (r"how (?:do i |can i |to )get to (.+?)(?: by (?:bus|train|public transport))?", Language.ENGLISH, IntentType.TRANSPORT_PUBLIC),
                (r"when (?:should i |do i need to )leave (?:for |to get to )?(.+?)(?:\?)?$", Language.ENGLISH, IntentType.TRANSPORT_PUBLIC),
                # Italian - with arrival time (MUST come before "quando devo partire per" pattern)
                (r"quando devo partire per (?:andare a )?(.+?) per arrivare alle (\d{1,2}(?::\d{2})?)", Language.ITALIAN, IntentType.TRANSPORT_PUBLIC),
                (r"mezzi (?:pubblici )?(?:per |verso )?(.+?) per arrivare alle (\d{1,2}(?::\d{2})?)", Language.ITALIAN, IntentType.TRANSPORT_PUBLIC),
                (r"come arrivo a (.+?) alle (\d{1,2}(?::\d{2})?)(?: (?:con i mezzi|in bus|in treno))?", Language.ITALIAN, IntentType.TRANSPORT_PUBLIC),
                # Italian - without arrival time (MUST come after "per arrivare alle" patterns)
                (r"mezzi (?:pubblici )?(?:per |verso )?(.+?)(?:\?)?$", Language.ITALIAN, IntentType.TRANSPORT_PUBLIC),
                (r"come arrivo a (.+?)(?: (?:con i mezzi|in bus|in treno))?(?:\?)?$", Language.ITALIAN, IntentType.TRANSPORT_PUBLIC),
                (r"quando devo partire per (.+?)(?:\?)?$", Language.ITALIAN, IntentType.TRANSPORT_PUBLIC),
            ],
        }


    def detect_language(self, text: str) -> Language:
        """Detect language from text using keyword matching"""
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        italian_score = len(words & self.ITALIAN_KEYWORDS)
        english_score = len(words & self.ENGLISH_KEYWORDS)
        
        # Check for definitive Italian markers
        if any(word in text_lower for word in ['è', 'sono', 'perché', 'più', 'già']):
            return Language.ITALIAN
        
        # Otherwise use score
        if italian_score > english_score:
            return Language.ITALIAN
        return Language.ENGLISH
    
    def extract_parameters(self, text: str, intent_type: IntentType, match_groups: tuple) -> Dict[str, Any]:
        """Extract parameters based on intent type and regex groups"""
        params = {}
        
        # Filter out None values from regex groups
        groups = [g.strip() if g else None for g in match_groups if g]
        
        if intent_type == IntentType.WEATHER:
            params['location'] = groups[0] if groups else self.default_location
        
        elif intent_type == IntentType.EMAIL_SEND:
            if len(groups) >= 2:
                params['recipient'] = groups[0]
                params['message'] = groups[1]
            elif len(groups) == 1:
                params['recipient'] = groups[0]
        
        elif intent_type == IntentType.EMAIL_READ:
            if groups:
                params['sender'] = groups[0]
        
        elif intent_type == IntentType.EMAIL_SEARCH:
            if groups:
                params['keyword'] = groups[0]
        
        elif intent_type == IntentType.CALENDAR_CREATE:
            if groups:
                params['event_description'] = groups[0]

        elif intent_type == IntentType.CALENDAR_SPECIFIC:
            if groups:
                # Extract calendar name and clean it
                calendar_name = groups[0].strip().rstrip('.,!?;:')
                # Capitalize first letter for matching
                params['calendar_name'] = calendar_name.capitalize()

        elif intent_type == IntentType.MAC_OPEN_APP:
            if groups:
                # Strip punctuation from app name
                params['app_name'] = groups[0].rstrip('.,!?;:')
        
        elif intent_type == IntentType.MAC_CLOSE_APP:
            if groups:
                # Strip punctuation from app name
                params['app_name'] = groups[0].rstrip('.,!?;:')
        
        elif intent_type in [IntentType.TELEGRAM_READ, IntentType.WHATSAPP_READ]:
            if groups:
                params['sender'] = groups[0]
        
        elif intent_type in [IntentType.TELEGRAM_CHECK, IntentType.WHATSAPP_CHECK]:
            # No parameters needed
            pass

        elif intent_type == IntentType.VOLUME_SET:
            if groups:
                try:
                    params['level'] = int(groups[0])
                except (ValueError, IndexError):
                    pass

        elif intent_type == IntentType.VOLUME_UP:
            # Optional amount parameter (default 10)
            if groups and groups[0]:
                try:
                    params['amount'] = int(groups[0])
                except (ValueError, IndexError):
                    params['amount'] = 10  # Default
            else:
                params['amount'] = 10  # Default

        elif intent_type == IntentType.VOLUME_DOWN:
            # Optional amount parameter (default 10)
            if groups and groups[0]:
                try:
                    params['amount'] = int(groups[0])
                except (ValueError, IndexError):
                    params['amount'] = 10  # Default
            else:
                params['amount'] = 10  # Default

        elif intent_type == IntentType.MAC_VOLUME:
            if groups:
                # Try to extract number
                try:
                    params['level'] = int(groups[0])
                except (ValueError, IndexError):
                    # Check for keywords
                    if 'louder' in text or 'alza' in text:
                        params['action'] = 'increase'
                    elif 'quieter' in text or 'abbassa' in text:
                        params['action'] = 'decrease'
                    elif 'mute' in text or 'silenzia' in text:
                        params['action'] = 'mute'
        
        elif intent_type in [IntentType.TELEGRAM_SEND, IntentType.WHATSAPP_SEND]:
            if len(groups) >= 2:
                params['recipient'] = groups[0]
                params['message'] = groups[1]
        
        elif intent_type == IntentType.TRANSLATE:
            if len(groups) >= 2:
                params['text'] = groups[0]
                params['target_language'] = groups[1]
        
        elif intent_type == IntentType.CALCULATE:
            if groups:
                # Join all groups for expressions like "25% of 80"
                params['expression'] = ' '.join(str(g) for g in groups if g)

        elif intent_type == IntentType.RECIPE_SEARCH:
            if groups:
                # Strip punctuation from query
                params['query'] = groups[0].rstrip('.,!?;:')

        elif intent_type in [IntentType.TRANSPORT_CAR, IntentType.TRANSPORT_PUBLIC]:
            if groups:
                # Strip punctuation from destination
                params['destination'] = groups[0].rstrip('.,!?;:')
                # Check if arrival time is provided (second group)
                if len(groups) >= 2 and groups[1]:
                    params['arrival_time'] = groups[1].strip()

        return params
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse intent from text"""
        # Clean the text more aggressively - remove all trailing punctuation
        text_clean = text.strip().lower()
        # Remove common punctuation that whisper adds
        text_clean = text_clean.rstrip('.,!?;:')

        # Detect language first
        language = self.detect_language(text_clean)
        
        # Try to match patterns
        for category, patterns in self.patterns.items():
            for pattern, lang, intent_type in patterns:
                match = re.search(pattern, text_clean, re.IGNORECASE)
                if match:
                    params = self.extract_parameters(text_clean, intent_type, match.groups())

                    return {
                        'intent': intent_type.value,
                        'language': lang.value,  # Use language from matched pattern
                        'parameters': params,
                        'confidence': 0.9,  # High confidence for pattern match
                        'original_text': text,
                        'requires_pin': self._requires_pin(intent_type)
                    }
        
        # No pattern matched - return general chat
        return {
            'intent': IntentType.GENERAL_CHAT.value,
            'language': language.value,
            'parameters': {'query': text},
            'confidence': 0.5,  # Low confidence, might need LLM
            'original_text': text,
            'requires_pin': False
        }
    
    def _requires_pin(self, intent_type: IntentType) -> bool:
        """Check if intent requires PIN authentication"""
        sensitive_intents = {
            IntentType.EMAIL_SEND,
            IntentType.SYSTEM_SHUTDOWN,
            IntentType.TELEGRAM_SEND,
            IntentType.WHATSAPP_SEND,
            IntentType.CALENDAR_CREATE,
        }
        return intent_type in sensitive_intents


# Convenience function
parser = IntentParser()

def parse_intent(text: str) -> Dict[str, Any]:
    """Parse intent from text (convenience function)"""
    return parser.parse(text)


if __name__ == '__main__':
    # Test cases
    test_commands = [
        # Weather & Time
        "What's the weather like?",
        "Che tempo fa a Torino?",
        "What time is it?",
        "Che ora è?",
        
        # Email - Testing the problematic cases
        "Check my emails",
        "Send an email to Marco saying I'll be late",
        "Search emails for project alpha",
        "Controlla la posta",
        
        # Calendar - Testing week vs today
        "What's on my calendar today?",
        "What's my schedule this week?",
        "Create an event tomorrow at 3pm meeting with Bob",
        "Cosa ho in calendario oggi?",
        
        # System & Mac
        "How's the Pi doing?",
        "Shutdown the Mac",
        "Open Spotify",
        "Close Chrome",
        "Set volume to 50",
        "Lock the screen",
        "Put Mac to sleep",
        
        # Messaging
        "Send a telegram to Alice saying hello",
        "WhatsApp Bob that I'm on my way",
        
        # General
        "Tell me a joke",
        "Translate hello to Italian",
        "Calculate 25% of 80",
        "Dimmi una battuta",
        
        # Ambiguous - Should be general_chat
        "What should I wear today?",
        "Can I go for a run?",
    ]
    
    print("Testing Intent Parser\n" + "="*50)
    for cmd in test_commands:
        result = parse_intent(cmd)
        print(f"\nCommand: {cmd}")
        print(f"Intent: {result['intent']}")
        print(f"Language: {result['language']}")
        print(f"Confidence: {result['confidence']}")
        if result['parameters']:
            print(f"Parameters: {json.dumps(result['parameters'], indent=2)}")
        print(f"Requires PIN: {result['requires_pin']}")
