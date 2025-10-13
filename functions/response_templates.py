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

    print("Testing Response Templates\n" + "="*50)

    print("\n1. Weather (English):")
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
        'description': 'Sereno'
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
