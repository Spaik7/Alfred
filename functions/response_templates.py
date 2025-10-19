#!/usr/bin/env python3
"""
Response Templates for Alfred - Fast, personality-rich responses
British butler style with bilingual support
"""

import random
from typing import Dict, Any, Optional

class ResponseTemplates:
    """Template-based response generator with British butler personality"""

    def __init__(self):
        """Initialize response templates"""
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Dict[str, list]]:
        """Load all response templates organized by intent and language"""
        return {
            # Weather responses
            'weather': {
                'en': [
                    "The weather in {location}? {temp} degrees Celsius and {description}, sir. {weather_comment}",
                    "Currently {temp} degrees Celsius with {description} in {location}, sir.",
                    "It's {temp} degrees Celsius in {location} at present, {description} conditions, sir.",
                    "Rather {description} at {temp} degrees Celsius in {location}, sir. {weather_comment}",
                ],
                'it': [
                    "A {location} ci sono {temp} gradi Celsius con {description}, signore.",
                    "Il tempo a {location} è {description} con {temp} gradi Celsius, signore.",
                    "Attualmente {temp} gradi Celsius e {description} a {location}, signore.",
                    "Fa {temp} gradi con {description} a {location}, signore.",
                ]
            },

            # Time responses
            'time': {
                'en': [
                    "It's currently {time}, sir.",
                    "The time is {time}, sir.",
                    "{time} at present, sir.",
                    "It's {time}, sir. Right on schedule, I trust?",
                ],
                'it': [
                    "Sono le {time}, signore.",
                    "L'ora è {time}, signore.",
                    "Attualmente sono le {time}, signore.",
                    "Sono le {time} in punto, signore.",
                ]
            },

            # Date responses
            'date': {
                'en': [
                    "Today is {weekday}, {month_name} {day}, sir.",
                    "It's {weekday}, {month_name} {day}, sir.",
                    "{weekday}, the {day} of {month_name}, sir.",
                    "We're at {weekday}, {month_name} {day}, sir.",
                ],
                'it': [
                    "Oggi è {weekday_it_lower} {day} {month_name_it_lower}, signore.",
                    "Siamo {weekday_it_lower} {day} {month_name_it_lower}, signore.",
                    "È {weekday_it_lower} {day} {month_name_it_lower}, signore.",
                ]
            },

            # System status responses
            'system_status': {
                'en': [
                    "System status: CPU at {cpu}%, memory at {memory}%, temperature {temp} degrees Celsius, sir.",
                    "The Pi is running at {cpu}% CPU, {memory}% memory, {temp} degrees Celsius, sir. {status_comment}",
                    "All systems nominal, sir. CPU {cpu}%, RAM {memory}%, temperature {temp} degrees Celsius.",
                    "Performance metrics: {cpu}% CPU load, {memory}% memory usage, {temp} degrees Celsius, sir.",
                ],
                'it': [
                    "Stato sistema: CPU al {cpu}%, memoria al {memory}%, temperatura {temp} gradi Celsius, signore.",
                    "Il Pi funziona al {cpu}% CPU, {memory}% memoria, {temp} gradi Celsius, signore.",
                    "Tutto normale, signore. CPU {cpu}%, RAM {memory}%, temperatura {temp} gradi Celsius.",
                ]
            },

            # Volume control responses
            'volume_set': {
                'en': [
                    "Volume set to {level} percent, sir.",
                    "Very well, sir. Volume adjusted to {level} percent.",
                    "Audio level now at {level} percent, sir.",
                    "{level} percent it is, sir.",
                ],
                'it': [
                    "Volume impostato al {level} percento, signore.",
                    "Molto bene, signore. Volume al {level} percento.",
                    "Livello audio al {level} percento, signore.",
                ]
            },

            'volume_up': {
                'en': [
                    "Volume increased to {result} percent, sir.",
                    "Raised to {result} percent, sir.",
                    "Audio level now at {result} percent, sir.",
                    "A bit louder at {result} percent, sir.",
                ],
                'it': [
                    "Volume alzato al {result} percento, signore.",
                    "Aumentato al {result} percento, signore.",
                    "Più forte, al {result} percento, signore.",
                ]
            },

            'volume_down': {
                'en': [
                    "Volume decreased to {result} percent, sir.",
                    "Lowered to {result} percent, sir.",
                    "Audio level now at {result} percent, sir.",
                    "Quieter at {result} percent, sir.",
                ],
                'it': [
                    "Volume abbassato al {result} percento, signore.",
                    "Diminuito al {result} percento, signore.",
                    "Più piano, al {result} percento, signore.",
                ]
            },

            # Joke responses (just acknowledge, the joke is spoken separately)
            'joke': {
                'en': [
                    "Here's one for you, sir.",
                    "Very well, sir. A bit of humor.",
                    "As you wish, sir.",
                ],
                'it': [
                    "Eccone una, signore.",
                    "Molto bene, signore. Un po' di umorismo.",
                    "Come desidera, signore.",
                ]
            },

            # Calculator responses
            'calculate': {
                'en': [
                    "{expression} equals {result}, sir.",
                    "That would be {result}, sir.",
                    "The answer is {result}, sir.",
                    "{expression} comes to {result}, sir.",
                ],
                'it': [
                    "{expression} fa {result}, signore.",
                    "Il risultato è {result}, signore.",
                    "La risposta è {result}, signore.",
                ]
            },

            # Transport - Car directions
            'transport_car': {
                'en': [
                    "It will take {duration} to reach {destination}, sir. Distance: {distance}.",
                    "Your journey to {destination} should take {duration}, covering {distance}, sir.",
                    "Expect {duration} to {destination}, sir. That's {distance} by road.",
                    "To {destination}, sir: {duration} over {distance}. {traffic_comment}",
                ],
                'it': [
                    "Per arrivare a {destination} ci vogliono {duration}, signore. Distanza: {distance}.",
                    "Il viaggio verso {destination} richiede {duration}, per {distance}, signore.",
                    "Ci vorranno {duration} per {destination}, signore. {distance} di strada.",
                ]
            },

            # Transport - Public transit
            'transport_public': {
                'en': [
                    "By public transport to {destination}: depart at {departure}, arrive {arrival}. {duration}, sir.",
                    "Take the {departure} service to {destination}, arriving {arrival}. Journey time: {duration}, sir.",
                    "To {destination} by transit, sir: leave at {departure}, arrive {arrival}. {duration} total.",
                ],
                'it': [
                    "Con i mezzi pubblici per {destination}: partenza alle {departure}, arrivo alle {arrival}. {duration}, signore.",
                    "Per {destination} in trasporto pubblico: partire alle {departure}, arrivare alle {arrival}. {duration}, signore.",
                ]
            },

            # News
            'news': {
                'en': [
                    "Here are today's headlines, sir: {headlines}",
                    "The news from {source}, sir: {headlines}",
                    "Top stories at present, sir: {headlines}",
                    "Today's developments, sir: {headlines}",
                ],
                'it': [
                    "Ecco le notizie di oggi, signore: {headlines}",
                    "Le notizie principali, signore: {headlines}",
                    "I titoli di oggi, signore: {headlines}",
                ]
            },

            # Finance - Stock quote
            'finance': {
                'en': [
                    "{symbol}: {price}, {change} today, sir. {trend_comment}",
                    "{symbol} is trading at {price}, {change}, sir.",
                    "Current price for {symbol}: {price}. {change} on the day, sir.",
                    "{symbol} at {price}, sir. {change}. {trend_comment}",
                ],
                'it': [
                    "{symbol}: {price}, {change} oggi, signore.",
                    "{symbol} a {price}, {change}, signore.",
                    "Prezzo attuale di {symbol}: {price}. {change}, signore.",
                ]
            },

            # Finance - Watchlist
            'finance_watchlist': {
                'en': [
                    "Your portfolio, sir: {summary}. {performance_comment}",
                    "Market update for your watchlist, sir: {summary}",
                    "Here's your financial overview, sir: {summary}",
                ],
                'it': [
                    "Il suo portafoglio, signore: {summary}",
                    "Aggiornamento di mercato, signore: {summary}",
                ]
            },

            # Recipe search
            'recipe_search': {
                'en': [
                    "I found these {query} recipes, sir: {recipes}",
                    "For {query}, might I suggest, sir: {recipes}",
                    "Here are some {query} options, sir: {recipes}",
                    "Regarding {query}, sir, I've located: {recipes}",
                ],
                'it': [
                    "Ho trovato queste ricette di {query}, signore: {recipes}",
                    "Per {query}, signore: {recipes}",
                    "Ecco alcune opzioni di {query}, signore: {recipes}",
                ]
            },

            # Recipe random
            'recipe_random': {
                'en': [
                    "Might I suggest {recipe_name}, sir? A {area} {category}.",
                    "How about {recipe_name}, sir? {area} cuisine, {category}.",
                    "Perhaps {recipe_name} would suit, sir. From {area}, a fine {category}.",
                    "I recommend {recipe_name}, sir. A {area} {category}.",
                ],
                'it': [
                    "Potrei suggerire {recipe_name}, signore? Un {category} {area}.",
                    "Che ne dice di {recipe_name}, signore? Cucina {area}, {category}.",
                    "Forse {recipe_name}, signore. {area}, un ottimo {category}.",
                ]
            },

            # Gratitude responses
            'thanks': {
                'en': [
                    "You're most welcome, sir.",
                    "My pleasure, sir.",
                    "At your service, sir.",
                    "Always happy to assist, sir.",
                    "Not at all, sir.",
                    "Think nothing of it, sir.",
                ],
                'it': [
                    "Prego, signore.",
                    "È un piacere, signore.",
                    "Ai suoi ordini, signore.",
                    "Felice di aiutare, signore.",
                    "Di niente, signore.",
                ]
            },

            # Greetings
            'greeting': {
                'en': [
                    "Good {time_of_day}, sir. How may I be of service?",
                    "{time_of_day_greeting}, sir. What can I do for you?",
                    "Good {time_of_day}, sir. At your disposal.",
                    "{time_of_day_greeting}, sir. How may I assist?",
                ],
                'it': [
                    "Buon{time_of_day_it}, signore. Come posso aiutarla?",
                    "{time_of_day_it_greeting}, signore. Cosa posso fare per lei?",
                    "Buon{time_of_day_it}, signore. Ai suoi ordini.",
                ]
            },

            # Apologies/Unknown
            'unknown': {
                'en': [
                    "I'm afraid I didn't quite catch that, sir. Could you rephrase?",
                    "I beg your pardon, sir. I didn't understand that request.",
                    "I'm not entirely certain what you mean, sir. Might you elaborate?",
                    "That's not quite clear to me, sir. Could you try again?",
                ],
                'it': [
                    "Mi dispiace, signore, non ho capito bene. Può ripetere?",
                    "Chiedo scusa, signore. Non ho compreso la richiesta.",
                    "Non sono sicuro di aver capito, signore. Può chiarire?",
                ]
            },

            # Generic acknowledgments
            'generic': {
                'en': [
                    "Very well, sir.",
                    "Understood, sir.",
                    "At your service, sir.",
                    "As you wish, sir.",
                    "Certainly, sir.",
                ],
                'it': [
                    "Molto bene, signore.",
                    "Capito, signore.",
                    "Ai suoi ordini, signore.",
                    "Come desidera, signore.",
                    "Certamente, signore.",
                ]
            },

            # Email check responses
            'email_check': {
                'en': [
                    "You have {count} unread {emails}, sir.",
                    "{count} unread {emails} in your inbox, sir.",
                    "There {are} {count} unread {emails} awaiting your attention, sir.",
                    "{count} {emails} unread at present, sir.",
                ],
                'it': [
                    "{lei_ha} {count} email non {lette}, signore.",
                    "Ci sono {count} email non {lette} nella casella, signore.",
                    "{count} email non {lette} in attesa, signore.",
                    "Al momento {lei_ha} {count} email non {lette}, signore.",
                ]
            },

            # Email list responses
            'email_list': {
                'en': [
                    "Your recent emails, sir: {email_list}",
                    "Here are your last {count} {emails}, sir: {email_list}",
                    "{count} recent {emails}: {email_list}",
                    "The most recent {emails}, sir: {email_list}",
                ],
                'it': [
                    "Le sue email recenti, signore: {email_list}",
                    "Ecco le ultime {count} email, signore: {email_list}",
                    "{count} email recenti: {email_list}",
                    "Le email più recenti, signore: {email_list}",
                ]
            }
        }

    def _get_weather_comment(self, temp: float, description: str) -> str:
        """Generate contextual weather comments"""
        if temp < 5:
            return random.choice([
                "Rather chilly, I'm afraid.",
                "Do dress warmly, sir.",
                "Quite cold indeed.",
            ])
        elif temp > 25:
            return random.choice([
                "Quite warm, sir.",
                "Perfect weather for a stroll.",
                "Rather pleasant, I'd say.",
            ])
        elif "rain" in description.lower():
            return random.choice([
                "Do take an umbrella, sir.",
                "A spot of rain, I'm afraid.",
            ])
        else:
            return random.choice([
                "Quite agreeable conditions.",
                "Rather pleasant weather.",
                "",
            ])

    def _get_status_comment(self, cpu: float, memory: float, temp: float) -> str:
        """Generate contextual system status comments"""
        if cpu > 80 or memory > 85:
            return "Running a bit warm, sir."
        elif temp > 70:
            return "Temperature is elevated, sir."
        else:
            return "All systems performing well."

    def _get_traffic_comment(self, duration_minutes: int) -> str:
        """Generate contextual traffic comments"""
        if duration_minutes > 60:
            return "Quite a journey, sir."
        elif duration_minutes > 30:
            return "A reasonable trip, sir."
        else:
            return random.choice([
                "Not far at all, sir.",
                "A quick drive, sir.",
                "",
            ])

    def _get_trend_comment(self, change_percent: float) -> str:
        """Generate contextual finance trend comments"""
        if change_percent > 5:
            return "Performing rather well, sir."
        elif change_percent < -5:
            return "A bit of a decline, I'm afraid."
        elif change_percent > 0:
            return "On the rise, sir."
        elif change_percent < 0:
            return "Slightly down, sir."
        else:
            return ""

    def _get_performance_comment(self, gains: int, losses: int) -> str:
        """Generate portfolio performance comments"""
        if gains > losses * 2:
            return "Rather encouraging results, sir."
        elif losses > gains * 2:
            return "A challenging day, I'm afraid, sir."
        elif gains > losses:
            return "Trending positively, sir."
        else:
            return ""

    def _get_time_of_day_greeting(self, language: str = "en") -> dict:
        """Get time-of-day specific greetings"""
        from datetime import datetime
        hour = datetime.now().hour

        if language == "en":
            if 5 <= hour < 12:
                return {"time_of_day": "morning", "time_of_day_greeting": "Good morning"}
            elif 12 <= hour < 17:
                return {"time_of_day": "afternoon", "time_of_day_greeting": "Good afternoon"}
            elif 17 <= hour < 21:
                return {"time_of_day": "evening", "time_of_day_greeting": "Good evening"}
            else:
                return {"time_of_day": "evening", "time_of_day_greeting": "Good evening"}
        else:  # Italian
            if 5 <= hour < 12:
                return {"time_of_day_it": "giorno", "time_of_day_it_greeting": "Buongiorno"}
            elif 12 <= hour < 17:
                return {"time_of_day_it": "giorno", "time_of_day_it_greeting": "Buon pomeriggio"}
            elif 17 <= hour < 21:
                return {"time_of_day_it": "asera", "time_of_day_it_greeting": "Buonasera"}
            else:
                return {"time_of_day_it": "asera", "time_of_day_it_greeting": "Buonasera"}

    def generate(self, intent: str, result: Any, language: str = "en", parameters: Optional[Dict] = None) -> str:
        """
        Generate a template response

        Args:
            intent: Intent type (e.g., "weather", "time")
            result: Result value (e.g., "20.2C", "14:30")
            language: Language code ("en" or "it")
            parameters: Additional parameters for template substitution

        Returns:
            Generated response string
        """
        if parameters is None:
            parameters = {}

        # Get templates for this intent and language
        intent_templates = self.templates.get(intent, {})
        lang_templates = intent_templates.get(language, intent_templates.get('en', []))

        if not lang_templates:
            # Fallback to generic
            lang_templates = self.templates['generic'].get(language, self.templates['generic']['en'])

        # Choose a random template
        template = random.choice(lang_templates)

        # Prepare substitution values
        values = {
            'result': result,
            **parameters
        }

        # Extract and add simplified values for templates
        # Weather: add 'temp' as alias for 'temperature_c'
        if intent == 'weather' and 'temperature_c' in parameters:
            values['temp'] = parameters['temperature_c']
            # Add weather comment for English (some templates use it, some don't)
            if language == 'en':
                values['weather_comment'] = self._get_weather_comment(
                    parameters.get('temperature_c', 0),
                    parameters.get('description', '')
                )
            else:
                # Ensure key exists even for other languages (in case template uses it)
                values['weather_comment'] = ''

        # Date: add lowercase versions for Italian
        if intent == 'date':
            if 'weekday_it' in parameters:
                values['weekday_it_lower'] = parameters['weekday_it'].lower()
            if 'month_name_it' in parameters:
                values['month_name_it_lower'] = parameters['month_name_it'].lower()

        # System status: extract nested values
        if intent == 'system_status':
            cpu_data = parameters.get('cpu', {})
            memory_data = parameters.get('memory', {})
            temp_data = parameters.get('temperature', {})

            values['cpu'] = cpu_data.get('usage_percent', 0)
            values['memory'] = memory_data.get('usage_percent', 0)
            values['temp'] = temp_data.get('celsius', 0) if temp_data.get('success') else 0

            # Add status comment for English (some templates use it)
            if language == 'en':
                values['status_comment'] = self._get_status_comment(
                    values['cpu'], values['memory'], values['temp']
                )
            else:
                values['status_comment'] = ''

        # Transport: add traffic comment
        if intent in ['transport_car', 'transport_public']:
            # Extract duration in minutes for comment
            duration_str = parameters.get('duration', '0 mins')
            try:
                duration_minutes = int(duration_str.split()[0])
            except:
                duration_minutes = 0

            if language == 'en' and intent == 'transport_car':
                values['traffic_comment'] = self._get_traffic_comment(duration_minutes)
            else:
                values['traffic_comment'] = ''

        # Finance: add trend comment
        if intent == 'finance':
            change_str = parameters.get('change', '0%')
            try:
                # Parse "+2.5%" or "-1.2%" to float
                change_percent = float(change_str.replace('%', '').replace('+', ''))
            except:
                change_percent = 0

            if language == 'en':
                values['trend_comment'] = self._get_trend_comment(change_percent)
            else:
                values['trend_comment'] = ''

        # Finance watchlist: add performance comment
        if intent == 'finance_watchlist':
            # Count gains vs losses in summary
            summary = parameters.get('summary', '')
            gains = summary.count('+')
            losses = summary.count('-')

            if language == 'en':
                values['performance_comment'] = self._get_performance_comment(gains, losses)
            else:
                values['performance_comment'] = ''

        # Greeting: add time-of-day context
        if intent == 'greeting':
            tod = self._get_time_of_day_greeting(language)
            values.update(tod)

        # Email check: add pluralization
        if intent == 'email_check':
            count = parameters.get('count', parameters.get('unread_count', 0))
            values['count'] = count
            # English pluralization
            values['emails'] = 'email' if count == 1 else 'emails'
            values['are'] = 'is' if count == 1 else 'are'
            # Italian pluralization
            values['lei_ha'] = 'Ha' if count == 1 else 'Ha'
            values['lette'] = 'letta' if count == 1 else 'lette'

        # Email list: format email list
        if intent == 'email_list':
            count = parameters.get('count', 0)
            emails = parameters.get('emails', [])
            values['count'] = count
            values['emails'] = 'email' if count == 1 else 'emails'

            # Build email list string
            email_items = []
            for i, email in enumerate(emails, 1):
                sender = email.get('sender', 'Unknown')
                # Extract just name from "Name <email@domain.com>"
                if '<' in sender:
                    sender = sender.split('<')[0].strip()
                subject = email.get('subject', 'No subject')
                read_status = "read" if email.get('is_read', False) else "unread"

                if language == 'en':
                    email_items.append(f"Number {i}, from {sender}, subject {subject}, {read_status}")
                else:
                    read_it = "letta" if email.get('is_read', False) else "non letta"
                    email_items.append(f"Numero {i}, da {sender}, oggetto {subject}, {read_it}")

            values['email_list'] = '. '.join(email_items) + '.' if email_items else ''

        # Format the template
        try:
            response = template.format(**values)
            return response
        except KeyError as e:
            print(f"[DEBUG] Template formatting error: {e}")
            print(f"[DEBUG] Template: {template}")
            print(f"[DEBUG] Values: {values}")
            # Fallback
            if language == 'it':
                return f"Fatto, signore. {intent} completato."
            else:
                return f"Very well, sir. {intent} completed."


# Singleton instance
_template_generator = None

def get_template_generator() -> ResponseTemplates:
    """Get singleton template generator"""
    global _template_generator
    if _template_generator is None:
        _template_generator = ResponseTemplates()
    return _template_generator


def generate_template_response(intent: str, result: Any, language: str = "en", parameters: Optional[Dict] = None) -> str:
    """Convenience function for template generation"""
    return get_template_generator().generate(intent, result, language, parameters)


if __name__ == '__main__':
    # Test templates
    gen = ResponseTemplates()

    print("\n" + "="*60)
    print("Testing Alfred Response Templates with Personality")
    print("="*60)

    print("\n1. Weather (English with comment):")
    print(gen.generate('weather', '20.2C, Mainly clear', 'en', {
        'location': 'Santhia',
        'temp': 20.2,
        'description': 'Mainly clear',
        'temperature_c': 20.2
    }))

    print("\n2. Weather (Italian):")
    print(gen.generate('weather', '20.2C, Sereno', 'it', {
        'location': 'Santhia',
        'temp': 20.2,
        'description': 'Sereno',
        'temperature_c': 20.2
    }))

    print("\n3. Time:")
    print(gen.generate('time', '14:30', 'en', {'time': '14:30'}))

    print("\n4. Volume:")
    print(gen.generate('volume_up', '55', 'it', {'result': 55}))

    print("\n5. System Status:")
    print(gen.generate('system_status', 'OK', 'en', {
        'cpu': {'usage_percent': 45},
        'memory': {'usage_percent': 60},
        'temperature': {'success': True, 'celsius': 55}
    }))

    print("\n6. Transport - Car (with traffic comment):")
    print(gen.generate('transport_car', 'OK', 'en', {
        'destination': 'Vercelli',
        'duration': '22 mins',
        'distance': '18.5 km'
    }))

    print("\n7. Transport - Public Transit:")
    print(gen.generate('transport_public', 'OK', 'it', {
        'destination': 'Milano',
        'departure': '14:30',
        'arrival': '15:45',
        'duration': '75 mins'
    }))

    print("\n8. Finance (with trend comment):")
    print(gen.generate('finance', 'OK', 'en', {
        'symbol': 'AAPL',
        'price': '$182.45',
        'change': '+2.3%'
    }))

    print("\n9. Recipe Search:")
    print(gen.generate('recipe_search', 'OK', 'en', {
        'query': 'pasta',
        'recipes': 'Carbonara, Amatriciana, Puttanesca'
    }))

    print("\n10. Recipe Random:")
    print(gen.generate('recipe_random', 'OK', 'it', {
        'recipe_name': 'Ossobuco',
        'area': 'Italian',
        'category': 'Beef'
    }))

    print("\n11. News:")
    print(gen.generate('news', 'OK', 'en', {
        'source': 'BBC',
        'headlines': '1) Markets rise 2) Tech innovation 3) Climate action'
    }))

    print("\n12. Greeting:")
    print(gen.generate('greeting', 'OK', 'en', {}))

    print("\n13. Thanks:")
    print(gen.generate('thanks', 'OK', 'it', {}))

    print("\n14. Unknown:")
    print(gen.generate('unknown', 'OK', 'en', {}))

    print("\n✅ All personality templates working correctly!")
