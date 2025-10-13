#!/usr/bin/env python3
"""
General Functions for Alfred - Jokes, Calculator, etc.
"""

import requests
import re
from typing import Optional

def tell_joke(language: str = "en") -> dict:
    """
    Tell a joke using free joke API or fallback to hardcoded jokes

    Args:
        language: Language code ("en" or "it")

    Returns:
        dict with joke
    """
    try:
        if language == "en":
            # Try Official Joke API (no auth required)
            response = requests.get(
                "https://official-joke-api.appspot.com/random_joke",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                joke = f"{data['setup']} ... {data['punchline']}"
                return {
                    "success": True,
                    "joke": joke,
                    "setup": data['setup'],
                    "punchline": data['punchline']
                }

        # Fallback to hardcoded jokes
        return _fallback_joke(language)

    except Exception as e:
        return _fallback_joke(language)


def _fallback_joke(language: str = "en") -> dict:
    """Fallback hardcoded jokes when API fails"""
    import random

    jokes_en = [
        {"setup": "Why did the butler bring a ladder to work?", "punchline": "To reach new heights of service, sir."},
        {"setup": "What did Alfred say when Batman asked for a snack?", "punchline": "I'm afraid the bat-cave is out of bat-snacks, sir."},
        {"setup": "Why don't scientists trust atoms?", "punchline": "Because they make up everything, sir."},
        {"setup": "What's the best thing about Switzerland?", "punchline": "I don't know, but the flag is a big plus."},
        {"setup": "Why did the Pi refuse to be rational?", "punchline": "Because it goes on forever, much like your to-do list, sir."}
    ]

    jokes_it = [
        {"setup": "Perche il maggiordomo porta una scala al lavoro?", "punchline": "Per raggiungere nuovi livelli di servizio, signore."},
        {"setup": "Cosa disse il computer al programmatore?", "punchline": "Mi hai usato solo per i tuoi bug, signore."},
        {"setup": "Perche gli scienziati non si fidano degli atomi?", "punchline": "Perche inventano tutto, signore."},
        {"setup": "Qual e la cosa migliore della Svizzera?", "punchline": "Non lo so, ma la bandiera e un grande vantaggio."}
    ]

    jokes = jokes_it if language == "it" else jokes_en
    joke = random.choice(jokes)

    return {
        "success": True,
        "joke": f"{joke['setup']} ... {joke['punchline']}",
        "setup": joke['setup'],
        "punchline": joke['punchline'],
        "source": "fallback"
    }


def calculate(expression: str) -> dict:
    """
    Calculate mathematical expression safely

    Args:
        expression: Mathematical expression (e.g., "2+2", "25% of 80", "5 più 5")

    Returns:
        dict with calculation result
    """
    try:
        # Clean the expression
        expression = expression.strip()
        original_expression = expression

        # Handle percentage calculations: "25% of 80" or "25 % di 80" -> 0.25 * 80
        percentage_pattern_en = r'(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)'
        percentage_pattern_it = r'(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)'  # From regex groups for Italian

        # Try English percentage format first
        match = re.search(percentage_pattern_en, expression, re.IGNORECASE)
        if match:
            percentage = float(match.group(1))
            value = float(match.group(2))
            result = (percentage / 100) * value
            return {
                "success": True,
                "expression": original_expression,
                "result": result,
                "formatted": f"{percentage}% of {value} = {result}"
            }

        # Try Italian format: "10 100" (from "il 10% di 100")
        if ' ' in expression and expression.count(' ') == 1:
            parts = expression.split()
            if len(parts) == 2 and parts[0].replace('.', '').isdigit() and parts[1].replace('.', '').isdigit():
                # This is likely a percentage from Italian pattern
                percentage = float(parts[0])
                value = float(parts[1])
                result = (percentage / 100) * value
                return {
                    "success": True,
                    "expression": original_expression,
                    "result": result,
                    "formatted": f"{percentage}% of {value} = {result}"
                }

        # Convert Italian word operators to symbols
        expression = expression.lower()
        expression = re.sub(r'\bpiù\b', '+', expression)
        expression = re.sub(r'\bmeno\b', '-', expression)
        expression = re.sub(r'\bper\b', '*', expression)
        expression = re.sub(r'\bdiviso\b', '/', expression)

        # Convert alternative symbols
        expression = expression.replace('x', '*')
        expression = expression.replace('×', '*')
        expression = expression.replace('÷', '/')

        # Clean expression - only allow numbers and basic operators
        cleaned = re.sub(r'[^0-9+\-*/().%\s]', '', expression)

        # Handle standalone percentages: "25%" -> 0.25
        cleaned = re.sub(r'(\d+)%', r'(\1/100)', cleaned)

        # Evaluate safely
        # Using eval is generally unsafe, but we've sanitized the input
        result = eval(cleaned, {"__builtins__": {}}, {})

        return {
            "success": True,
            "expression": original_expression,
            "result": result,
            "formatted": f"{original_expression} = {result}"
        }

    except ZeroDivisionError:
        return {
            "success": False,
            "error": "Cannot divide by zero",
            "expression": original_expression
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Invalid expression: {str(e)}",
            "expression": original_expression
        }


def translate_text(text: str, target_language: str, source_language: Optional[str] = None) -> dict:
    """
    Translate text using free translation API

    Args:
        text: Text to translate
        target_language: Target language code
        source_language: Source language code (auto-detect if None)

    Returns:
        dict with translation
    """
    try:
        # Using LibreTranslate (self-hosted, free API)
        # Note: You may need to deploy your own instance or use a public one
        # For now, return a placeholder
        return {
            "success": False,
            "error": "Translation API not configured yet",
            "text": text,
            "target_language": target_language
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == '__main__':
    # Test functions
    print("General Functions Test\n" + "="*50)

    print("\n1. Joke (English):")
    joke_en = tell_joke("en")
    if joke_en["success"]:
        print(f"   Setup: {joke_en['setup']}")
        print(f"   Punchline: {joke_en['punchline']}")

    print("\n2. Joke (Italian):")
    joke_it = tell_joke("it")
    if joke_it["success"]:
        print(f"   Setup: {joke_it['setup']}")
        print(f"   Punchline: {joke_it['punchline']}")

    print("\n3. Calculator - Basic:")
    calc1 = calculate("2 + 2")
    if calc1["success"]:
        print(f"   {calc1['formatted']}")

    print("\n4. Calculator - Percentage:")
    calc2 = calculate("25% of 80")
    if calc2["success"]:
        print(f"   {calc2['formatted']}")

    print("\n5. Calculator - Complex:")
    calc3 = calculate("(10 + 5) * 2")
    if calc3["success"]:
        print(f"   {calc3['formatted']}")
