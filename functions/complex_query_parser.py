#!/usr/bin/env python3
"""
Complex Query Parser for Alfred
Uses Ollama to break down complex queries into multiple intents
"""

import requests
import json
from typing import Dict, List, Any, Optional

class ComplexQueryParser:
    """Parse complex queries that require multiple API calls or reasoning"""

    def __init__(self, ollama_host: str = "localhost:11434", model: str = "llama3.2"):
        """
        Initialize complex query parser

        Args:
            ollama_host: Ollama API host:port
            model: Ollama model to use for query parsing
        """
        self.ollama_url = f"http://{ollama_host}/api/generate"
        self.model = model

    def is_complex_query(self, intent: str, query: str, confidence: float) -> bool:
        """
        Determine if a query requires complex processing

        Args:
            intent: Detected intent
            query: User's query
            confidence: Confidence score from simple parser

        Returns:
            True if complex processing needed
        """
        # Low confidence general_chat might benefit from analysis
        if intent == "general_chat" and confidence < 0.7:
            # Check for multi-part questions
            if any(keyword in query.lower() for keyword in [
                'and', 'also', 'then', 'after that', 'plus',
                'e', 'anche', 'poi', 'dopo', 'inoltre'
            ]):
                return True

            # Check for complex decision questions
            if any(keyword in query.lower() for keyword in [
                'should i', 'can i', 'what should', 'when should',
                'devo', 'posso', 'cosa dovrei', 'quando dovrei'
            ]):
                return True

        return False

    def parse_complex_query(self, query: str, language: str = "en") -> Optional[Dict[str, Any]]:
        """
        Parse a complex query into sub-intents using Ollama

        Args:
            query: User's complex query
            language: Language code (en or it)

        Returns:
            Dict with parsed sub-intents or None if parsing fails
        """
        prompt = self._build_parsing_prompt(query, language)

        try:
            print(f"[DEBUG] Analyzing complex query with Ollama...")

            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 300,
                        "temperature": 0.3  # Lower temperature for more consistent parsing
                    }
                },
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )

            if response.status_code == 200:
                data = response.json()
                generated_text = data.get("response", "").strip()

                # Try to parse JSON response
                try:
                    # Extract JSON from response (might have explanatory text around it)
                    if '{' in generated_text and '}' in generated_text:
                        json_start = generated_text.find('{')
                        json_end = generated_text.rfind('}') + 1
                        json_str = generated_text[json_start:json_end]
                        parsed = json.loads(json_str)
                        print(f"[DEBUG] Parsed {len(parsed.get('intents', []))} sub-intents")
                        return parsed
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] Failed to parse Ollama JSON: {e}")
                    print(f"[DEBUG] Raw response: {generated_text[:200]}")

            return None

        except Exception as e:
            print(f"[DEBUG] Complex query parsing failed: {e}")
            return None

    def _build_parsing_prompt(self, query: str, language: str) -> str:
        """Build the prompt for Ollama to parse the query"""

        if language == "it":
            return f"""Analizza questa richiesta italiana e rispondi SOLO con JSON valido.

Richiesta utente: "{query}"

Intenzioni disponibili:
- weather: meteo
- time: ora corrente
- date: data corrente
- calendar_today: eventi del calendario
- news: notizie
- general_chat: conversazione generica

IMPORTANTE: Rispondi SOLO con JSON, nient'altro. Usa esattamente questo formato:
{{"type": "complex", "intents": ["intent1", "intent2"], "reason": "breve spiegazione"}}

Regole:
- Se la richiesta contiene "e" tra due domande → type="complex", lista entrambi gli intent
- Se la richiesta è una domanda complessa (es. "cosa indossare") → type="complex", lista intent necessari
- Se la richiesta è semplice → type="simple", un solo intent

Esempi validi:
{{"type": "complex", "intents": ["weather", "calendar_today"], "reason": "serve meteo e calendario per consigliare abbigliamento"}}
{{"type": "complex", "intents": ["weather", "news"], "reason": "due domande separate con la congiunzione e"}}
{{"type": "complex", "intents": ["weather", "time"], "reason": "chiede meteo e ora corrente"}}
{{"type": "simple", "intents": ["general_chat"], "reason": "saluto o domanda generica"}}

Ora analizza: "{query}"
JSON:"""
        else:
            return f"""Analyze this English request and respond ONLY with valid JSON.

User request: "{query}"

Available intents:
- weather: weather information
- time: current time
- date: current date
- calendar_today: calendar events
- news: latest news
- general_chat: general conversation

IMPORTANT: Respond ONLY with JSON, nothing else. Use exactly this format:
{{"type": "complex", "intents": ["intent1", "intent2"], "reason": "brief explanation"}}

Rules:
- If request contains "and" between two questions → type="complex", list both intents
- If request is a complex question (e.g. "what to wear") → type="complex", list required intents
- If request is simple → type="simple", single intent

Valid examples:
{{"type": "complex", "intents": ["weather", "calendar_today"], "reason": "needs weather and calendar to suggest clothing"}}
{{"type": "complex", "intents": ["weather", "news"], "reason": "two separate questions joined by and"}}
{{"type": "complex", "intents": ["weather", "time"], "reason": "asks for weather and current time"}}
{{"type": "simple", "intents": ["general_chat"], "reason": "greeting or generic question"}}

Now analyze: "{query}"
JSON:"""

    def parse_concatenated_query(self, query: str, language: str = "en") -> Optional[List[str]]:
        """
        Parse a query with multiple intents concatenated (e.g. "weather and news")

        Args:
            query: User's query
            language: Language code

        Returns:
            List of intent strings or None
        """
        # Check for obvious concatenation keywords
        concat_keywords_en = ['and', 'also', 'plus', 'then', 'after that']
        concat_keywords_it = ['e', 'anche', 'poi', 'inoltre', 'dopo']

        keywords = concat_keywords_it if language == "it" else concat_keywords_en

        if not any(keyword in query.lower() for keyword in keywords):
            return None

        # Use Ollama to parse
        result = self.parse_complex_query(query, language)

        if result and result.get('type') == 'complex':
            return result.get('intents', [])

        return None


# Singleton instance
_parser_instance = None

def get_complex_parser(ollama_host: str = "localhost:11434", model: str = "llama3.2") -> ComplexQueryParser:
    """Get or create the complex query parser singleton"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = ComplexQueryParser(ollama_host, model)
    return _parser_instance


if __name__ == '__main__':
    # Test the complex query parser
    parser = ComplexQueryParser()

    test_queries = [
        ("What should I wear today?", "en"),
        ("What's the weather and what's the news?", "en"),
        ("Che tempo fa e quali sono le notizie?", "it"),
        ("Hello", "en"),
        ("Can I go for a run?", "en"),
        ("Posso andare a correre?", "it"),
    ]

    print("=" * 70)
    print("TESTING COMPLEX QUERY PARSER")
    print("=" * 70)

    for query, lang in test_queries:
        print(f"\nQuery: {query} ({lang})")
        result = parser.parse_complex_query(query, lang)

        if result:
            print(f"Type: {result.get('type')}")
            print(f"Intents: {result.get('intents')}")
            print(f"Reason: {result.get('reason')}")
        else:
            print("Failed to parse")

        print("-" * 70)
