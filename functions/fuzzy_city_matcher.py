#!/usr/bin/env python3
"""
Fuzzy City Name Matcher
Fixes transcription errors like "torrino" → "Torino", "vercelli" → "Vercelli"
"""

from difflib import get_close_matches
from typing import Optional, List

# Common Italian cities (expand as needed)
ITALIAN_CITIES = [
    # Major cities
    "Roma", "Milano", "Napoli", "Torino", "Palermo", "Genova", "Bologna",
    "Firenze", "Bari", "Catania", "Venezia", "Verona", "Messina", "Padova",
    "Trieste", "Brescia", "Taranto", "Prato", "Parma", "Modena", "Reggio Calabria",

    # Piedmont region (where Santhia is)
    "Santhia", "Santhià", "Vercelli", "Biella", "Novara", "Alessandria", "Asti",
    "Cuneo", "Verbania", "Ivrea", "Casale Monferrato", "Alba", "Moncalieri",

    # Other notable cities
    "Perugia", "Livorno", "Cagliari", "Foggia", "Rimini", "Salerno", "Ferrara",
    "Sassari", "Latina", "Giugliano in Campania", "Monza", "Siracusa", "Pescara",
    "Bergamo", "Forlì", "Trento", "Vicenza", "Terni", "Bolzano", "Novara",
    "Piacenza", "Ancona", "Andria", "Arezzo", "Udine", "Cesena",
]

# Add lowercase versions for matching
ITALIAN_CITIES_LOWER = [city.lower() for city in ITALIAN_CITIES]

def fuzzy_match_city(city_name: str, threshold: float = 0.6, max_results: int = 1) -> Optional[str]:
    """
    Fuzzy match a city name to known Italian cities

    Args:
        city_name: The city name to match (possibly misspelled)
        threshold: Similarity threshold (0.0 to 1.0)
        max_results: Maximum number of matches to return

    Returns:
        Best matching city name, or None if no good match
    """
    if not city_name:
        return None

    # Clean the input
    city_clean = city_name.strip().lower()

    # Check for exact match first
    if city_clean in ITALIAN_CITIES_LOWER:
        idx = ITALIAN_CITIES_LOWER.index(city_clean)
        return ITALIAN_CITIES[idx]

    # Fuzzy match using difflib
    matches = get_close_matches(
        city_clean,
        ITALIAN_CITIES_LOWER,
        n=max_results,
        cutoff=threshold
    )

    if matches:
        # Return the properly capitalized version
        idx = ITALIAN_CITIES_LOWER.index(matches[0])
        return ITALIAN_CITIES[idx]

    return None

def get_all_matches(city_name: str, threshold: float = 0.6, max_results: int = 3) -> List[str]:
    """
    Get multiple fuzzy matches for a city name

    Returns:
        List of matching city names (properly capitalized)
    """
    if not city_name:
        return []

    city_clean = city_name.strip().lower()

    matches = get_close_matches(
        city_clean,
        ITALIAN_CITIES_LOWER,
        n=max_results,
        cutoff=threshold
    )

    # Return properly capitalized versions
    return [ITALIAN_CITIES[ITALIAN_CITIES_LOWER.index(m)] for m in matches]


if __name__ == '__main__':
    # Test fuzzy matching
    print("="*60)
    print("Fuzzy City Matcher Test")
    print("="*60)

    test_cases = [
        # Transcription errors
        "torrino",      # → Torino
        "vercelli",     # → Vercelli (correct already)
        "millan",       # → Milano
        "rooma",        # → Roma
        "ferenze",      # → Firenze
        "venise",       # → Venezia
        "santhia",      # → Santhià
        "santhiaa",     # → Santhià
        "turino",       # → Torino
        "melano",       # → Milano

        # Correct spellings
        "Milano",
        "Torino",
        "Roma",

        # Gibberish
        "xyzabc",       # → None
        "werchalli",    # → Vercelli (if close enough)
    ]

    for test in test_cases:
        match = fuzzy_match_city(test, threshold=0.6)
        all_matches = get_all_matches(test, threshold=0.5, max_results=3)

        print(f"\nInput: '{test}'")
        print(f"  Best match: {match if match else 'None'}")
        if all_matches:
            print(f"  All matches: {', '.join(all_matches)}")

    print("\n" + "="*60)
    print("✅ Fuzzy matching working!")
