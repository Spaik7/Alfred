#!/usr/bin/env python3
"""
Simple Concatenation Parser for Alfred
Splits concatenated queries into sub-queries using regex (no LLM needed)
More reliable than trying to get Ollama to return JSON
"""

import re
from typing import List, Tuple, Optional

class SimpleConcatenationParser:
    """Split concatenated queries into individual sub-queries using regex"""

    def __init__(self):
        """Initialize the parser with split patterns"""
        # Patterns that indicate concatenation
        # Use lookbehind and lookahead to preserve the questions
        self.split_patterns = {
            'it': [
                r'\s+e\s+',           # " e " (and)
                r'\s+anche\s+',       # " anche " (also)
                r'\s+poi\s+',         # " poi " (then)
                r'\s+inoltre\s+',     # " inoltre " (furthermore)
            ],
            'en': [
                r'\s+and\s+',         # " and "
                r'\s+also\s+',        # " also "
                r'\s+then\s+',        # " then "
                r'\s+plus\s+',        # " plus "
            ]
        }

    def has_concatenation(self, query: str, language: str = 'en') -> bool:
        """
        Check if query contains concatenation keywords

        Args:
            query: User's query
            language: Language code (en or it)

        Returns:
            True if concatenation detected
        """
        patterns = self.split_patterns.get(language, self.split_patterns['en'])
        query_lower = query.lower()

        for pattern in patterns:
            if re.search(pattern, query_lower):
                return True
        return False

    def split_query(self, query: str, language: str = 'en') -> List[str]:
        """
        Split a concatenated query into sub-queries

        Args:
            query: User's concatenated query
            language: Language code (en or it)

        Returns:
            List of sub-queries

        Examples:
            "What's the weather and what's the news?" → ["What's the weather", "what's the news?"]
            "Che tempo fa e che ore sono?" → ["Che tempo fa", "che ore sono?"]
        """
        if not self.has_concatenation(query, language):
            return [query]

        patterns = self.split_patterns.get(language, self.split_patterns['en'])

        # Try each pattern to split
        for pattern in patterns:
            parts = re.split(pattern, query, flags=re.IGNORECASE)
            if len(parts) > 1:
                # Clean up parts
                cleaned_parts = [part.strip() for part in parts if part.strip()]
                return cleaned_parts

        # Fallback: return original query
        return [query]

    def parse_concatenated_queries(self, query: str, language: str = 'en') -> Optional[List[Tuple[str, str]]]:
        """
        Parse concatenated query and return list of (sub_query, intent) tuples

        Args:
            query: User's query
            language: Language code

        Returns:
            List of (sub_query, intent_guess) tuples or None if not concatenated

        Example:
            Input: "Che tempo fa e che ore sono?"
            Output: [
                ("Che tempo fa", "weather_likely"),
                ("che ore sono?", "time_likely")
            ]
        """
        if not self.has_concatenation(query, language):
            return None

        sub_queries = self.split_query(query, language)

        # Return sub-queries with intent hints
        results = []
        for sq in sub_queries:
            intent_hint = self._guess_intent(sq, language)
            results.append((sq, intent_hint))

        return results

    def _guess_intent(self, query: str, language: str) -> str:
        """
        Quick guess at what intent a sub-query might be
        This is just a hint, not authoritative

        Args:
            query: Sub-query
            language: Language code

        Returns:
            Intent hint string
        """
        q = query.lower()

        # Weather keywords
        if language == 'it':
            if any(kw in q for kw in ['tempo', 'meteo', 'piove']):
                return 'weather'
            if any(kw in q for kw in ['ora', 'ore sono']):
                return 'time'
            if any(kw in q for kw in ['giorno', 'data']):
                return 'date'
            if any(kw in q for kw in ['notizie', 'novità']):
                return 'news'
        else:
            if any(kw in q for kw in ['weather', 'rain', 'temperature']):
                return 'weather'
            if any(kw in q for kw in ['time', 'clock']):
                return 'time'
            if any(kw in q for kw in ['date', 'day is it']):
                return 'date'
            if any(kw in q for kw in ['news', 'headlines']):
                return 'news'

        return 'unknown'


# Singleton instance
_simple_parser_instance = None

def get_simple_concatenation_parser() -> SimpleConcatenationParser:
    """Get or create the simple concatenation parser singleton"""
    global _simple_parser_instance
    if _simple_parser_instance is None:
        _simple_parser_instance = SimpleConcatenationParser()
    return _simple_parser_instance


if __name__ == '__main__':
    # Test the simple concatenation parser
    parser = SimpleConcatenationParser()

    test_queries = [
        ("Che tempo fa e che ore sono?", "it"),
        ("What's the weather and what's the news?", "en"),
        ("What's the time and the date?", "en"),
        ("Che tempo fa?", "it"),  # No concatenation
        ("Hello", "en"),  # No concatenation
    ]

    print("=" * 70)
    print("TESTING SIMPLE CONCATENATION PARSER")
    print("=" * 70)

    for query, lang in test_queries:
        print(f"\nQuery: {query} ({lang})")
        print(f"Has concatenation: {parser.has_concatenation(query, lang)}")

        if parser.has_concatenation(query, lang):
            parts = parser.split_query(query, lang)
            print(f"Split into {len(parts)} parts:")
            for i, part in enumerate(parts, 1):
                print(f"  {i}. {part}")

            parsed = parser.parse_concatenated_queries(query, lang)
            if parsed:
                print(f"With intent hints:")
                for sub_q, hint in parsed:
                    print(f"  - \"{sub_q}\" → likely {hint}")

        print("-" * 70)
