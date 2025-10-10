#!/usr/bin/env python3
"""
Intent Parser for Alfred
Fast rule-based parser with language detection and parameter extraction
Falls back to LLM only for ambiguous cases
"""

import re
import json
from typing import Dict, Any, Optional, List
from enum import Enum

class Language(Enum):
    ENGLISH = "en"
    ITALIAN = "it"

class IntentType(Enum):
    # Basic queries
    WEATHER = "weather"
    TIME = "time"
    DATE = "date"
    
    # Email
    EMAIL_CHECK = "email_check"
    EMAIL_READ = "email_read"
    EMAIL_SEND = "email_send"
    EMAIL_SEARCH = "email_search"
    
    # Calendar
    CALENDAR_TODAY = "calendar_today"
    CALENDAR_WEEK = "calendar_week"
    CALENDAR_NEXT = "calendar_next"
    CALENDAR_CREATE = "calendar_create"
    
    # System
    SYSTEM_STATUS = "system_status"
    SYSTEM_SHUTDOWN = "system_shutdown"
    
    # Mac control
    MAC_OPEN_APP = "mac_open_app"
    MAC_CLOSE_APP = "mac_close_app"
    MAC_VOLUME = "mac_volume"
    MAC_SLEEP = "mac_sleep"
    MAC_LOCK = "mac_lock"
    
    # Messaging
    TELEGRAM_SEND = "telegram_send"
    TELEGRAM_CHECK = "telegram_check"
    TELEGRAM_READ = "telegram_read"
    WHATSAPP_SEND = "whatsapp_send"
    WHATSAPP_CHECK = "whatsapp_check"
    WHATSAPP_READ = "whatsapp_read"
    
    # General
    JOKE = "joke"
    TRANSLATE = "translate"
    CALCULATE = "calculate"
    GENERAL_CHAT = "general_chat"
    
    # Unknown
    UNKNOWN = "unknown"

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
    
    def __init__(self, default_location: str = "Turin"):
        self.default_location = default_location
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
                # Italian - More specific (doesn't match "che tempo" or "che giorno")
                (r"(?:cosa|che cosa) (?:ho |c'è )?(?:in )?(?:calendario|programma)(?: oggi)?", Language.ITALIAN, IntentType.CALENDAR_TODAY),
                (r"(?:ho )?appuntamenti oggi", Language.ITALIAN, IntentType.CALENDAR_TODAY),
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
                (r"leggi (?:i )?(?:ultimi )?messaggi telegram(?: di (.+))?", Language.ITALIAN, IntentType.TELEGRAM_READ),
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
                # Italian
                (r"calcola (.+)", Language.ITALIAN, IntentType.CALCULATE),
                (r"quanto (?:fa|è) (\d+[\d\s\+\-\*\/\%\.]+)", Language.ITALIAN, IntentType.CALCULATE),
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
        
        return params
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse intent from text"""
        text_clean = text.strip().lower()
        
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
                        'language': language.value,
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
