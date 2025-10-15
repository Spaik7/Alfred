#!/usr/bin/env python3
"""
Weather Functions for Alfred - Using Open-Meteo API (no API key needed)
"""

import requests
import sys
from pathlib import Path
from typing import Optional, Dict

# Import default location from config
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import DEFAULT_LOCATION
except ImportError:
    DEFAULT_LOCATION = "Santhia"

# Import fuzzy city matcher
try:
    from functions.fuzzy_city_matcher import fuzzy_match_city
except ImportError:
    # Fallback if fuzzy matcher not available
    def fuzzy_match_city(city): return city

def get_coordinates(location: str) -> Optional[Dict]:
    """
    Get latitude and longitude for a location using geocoding

    Args:
        location: City name (e.g., "Turin", "New York")

    Returns:
        dict with coordinates or None
    """
    try:
        # Use Open-Meteo geocoding API
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": location, "count": 1, "language": "en", "format": "json"},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                result = data["results"][0]
                return {
                    "latitude": result["latitude"],
                    "longitude": result["longitude"],
                    "name": result["name"],
                    "country": result.get("country", ""),
                    "timezone": result.get("timezone", "UTC")
                }
        return None
    except Exception:
        return None


def get_weather(language, location: str = None) -> dict:
    """
    Get current weather for a location

    Args:
        location: City name (default: from config, Santhia VC)

    Returns:
        dict with weather information
    """
    if location is None:
        location = DEFAULT_LOCATION

    # Try fuzzy matching for Italian cities if geocoding fails
    original_location = location

    try:
        # Get coordinates for the location
        coords = get_coordinates(location)
        if not coords:
            # Try fuzzy matching
            fuzzy_match = fuzzy_match_city(location, threshold=0.6)
            if fuzzy_match:
                coords = get_coordinates(fuzzy_match)
                if coords:
                    # Successfully matched!
                    pass
                else:
                    return {
                        "success": False,
                        "error": f"Location '{original_location}' not found (tried: {fuzzy_match})"
                    }
            else:
                return {
                    "success": False,
                    "error": f"Location '{original_location}' not found"
                }

        # Get weather data from Open-Meteo
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
                "timezone": coords["timezone"]
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            current = data["current"]

            # Weather code descriptions
            weather_descriptions_en = {
                0: "Clear sky",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Overcast",
                45: "Foggy",
                48: "Depositing rime fog",
                51: "Light drizzle",
                53: "Moderate drizzle",
                55: "Dense drizzle",
                61: "Slight rain",
                63: "Moderate rain",
                65: "Heavy rain",
                71: "Slight snow",
                73: "Moderate snow",
                75: "Heavy snow",
                77: "Snow grains",
                80: "Slight rain showers",
                81: "Moderate rain showers",
                82: "Violent rain showers",
                85: "Slight snow showers",
                86: "Heavy snow showers",
                95: "Thunderstorm",
                96: "Thunderstorm with slight hail",
                99: "Thunderstorm with heavy hail"
            }
            
            weather_descriptions_it = {
                0: "Cielo sereno",
                1: "Cielo parzialmente sereno",
                2: "Cielo parzialmente nuvoloso",
                3: "Cielo nuvoloso",
                45: "Nebbia",
                48: "Nebbia di brina depositata",
                51: "Pioggerella leggera",
                53: "Pioggerella moderata",
                55: "Pioggerella fitta",
                61: "Pioggia leggera",
                63: "Pioggia moderata",
                65: "Pioggia intensa",
                71: "Nevicata leggera",
                73: "Nevicata moderata",
                75: "Nevicata intensa",
                77: "Granelli di neve",
                80: "Piogge leggere",
                81: "Piogge moderate",
                82: "Piogge violente",
                85: "Neve leggera",
                86: "Neve intensa",
                95: "Temporale",
                96: "Temporale con leggera grandine",
                99: "Temporale con forte grandine"
            }

            weather_code = current.get("weather_code", 0)
            weather_desc = weather_descriptions_en.get(weather_code, "Unknown") if language == "en" else weather_descriptions_it.get(weather_code, "Unknown")

            return {
                "success": True,
                "location": coords["name"],
                "country": coords["country"],
                "temperature_c": current["temperature_2m"],
                "temperature_f": round((current["temperature_2m"] * 9/5) + 32, 1),
                "feels_like_c": current["apparent_temperature"],
                "feels_like_f": round((current["apparent_temperature"] * 9/5) + 32, 1),
                "humidity": current["relative_humidity_2m"],
                "precipitation": current["precipitation"],
                "wind_speed_kmh": current["wind_speed_10m"],
                "wind_speed_mph": round(current["wind_speed_10m"] * 0.621371, 1),
                "weather_code": weather_code,
                "description": weather_desc,
                "timezone": coords["timezone"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to fetch weather data"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_forecast(location: str = None, days: int = 3) -> dict:
    """
    Get weather forecast for the next few days

    Args:
        location: City name (default: from config, Santhia VC)
        days: Number of days to forecast (1-7)

    Returns:
        dict with forecast information
    """
    if location is None:
        location = DEFAULT_LOCATION

    try:
        # Clamp days to 1-7
        days = max(1, min(7, days))

        # Get coordinates for the location
        coords = get_coordinates(location)
        if not coords:
            return {
                "success": False,
                "error": f"Location '{location}' not found"
            }

        # Get forecast data from Open-Meteo
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": coords["latitude"],
                "longitude": coords["longitude"],
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                "timezone": coords["timezone"],
                "forecast_days": days
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            daily = data["daily"]

            forecast_days = []
            for i in range(len(daily["time"])):
                weather_code = daily["weather_code"][i]
                weather_descriptions = {
                    0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                    45: "Fog", 51: "Drizzle", 61: "Rain", 71: "Snow", 95: "Thunderstorm"
                }
                weather_desc = weather_descriptions.get(weather_code, "Unknown")

                forecast_days.append({
                    "date": daily["time"][i],
                    "temp_max_c": daily["temperature_2m_max"][i],
                    "temp_min_c": daily["temperature_2m_min"][i],
                    "temp_max_f": round((daily["temperature_2m_max"][i] * 9/5) + 32, 1),
                    "temp_min_f": round((daily["temperature_2m_min"][i] * 9/5) + 32, 1),
                    "precipitation_mm": daily["precipitation_sum"][i],
                    "wind_speed_kmh": daily["wind_speed_10m_max"][i],
                    "weather_code": weather_code,
                    "description": weather_desc
                })

            return {
                "success": True,
                "location": coords["name"],
                "country": coords["country"],
                "forecast": forecast_days,
                "timezone": coords["timezone"]
            }
        else:
            return {
                "success": False,
                "error": "Failed to fetch forecast data"
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == '__main__':
    # Test functions
    print("Weather Functions Test\n" + "="*50)

    print("\n1. Current Weather (Turin, English):")
    weather = get_weather("en", "Turin")
    if weather["success"]:
        print(f"   Location: {weather['location']}, {weather['country']}")
        print(f"   Temperature: {weather['temperature_c']}C / {weather['temperature_f']}F")
        print(f"   Feels like: {weather['feels_like_c']}C / {weather['feels_like_f']}F")
        print(f"   Conditions: {weather['description']}")
        print(f"   Humidity: {weather['humidity']}%")
        print(f"   Wind: {weather['wind_speed_kmh']} km/h")

    print("\n2. Current Weather (Turin, Italian):")
    weather_it = get_weather("it", "Turin")
    if weather_it["success"]:
        print(f"   Posizione: {weather_it['location']}, {weather_it['country']}")
        print(f"   Temperatura: {weather_it['temperature_c']}C")
        print(f"   Condizioni: {weather_it['description']}")

    print("\n3. 3-Day Forecast (Turin):")
    forecast = get_forecast("Turin", days=3)
    if forecast["success"]:
        print(f"   Location: {forecast['location']}, {forecast['country']}")
        for day in forecast["forecast"]:
            print(f"   {day['date']}: {day['temp_min_c']}-{day['temp_max_c']}C, {day['description']}")

    print("\n4. Current Weather (London, English):")
    weather_london = get_weather("en", "London")
    if weather_london["success"]:
        print(f"   Location: {weather_london['location']}, {weather_london['country']}")
        print(f"   Temperature: {weather_london['temperature_c']}C")
        print(f"   Conditions: {weather_london['description']}")
