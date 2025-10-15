#!/usr/bin/env python3
"""
Configuration file for Alfred - API Keys and Settings
KEEP THIS FILE SECURE - DO NOT COMMIT TO GIT
"""

import os

# API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")

# Default Settings
DEFAULT_LOCATION = "Tokyo"
DEFAULT_TIMEZONE = "Japan/Tokyo"
DEFAULT_LANGUAGE = "en"

# Temperature Units
TEMP_UNIT = "celsius"  # celsius or fahrenheit

# News Settings
NEWS_DEFAULT_COUNTRIES = ["eu", "us"]  # Italy and US
NEWS_DEFAULT_CATEGORY = None  # None, business, entertainment, health, science, sports, technology

# System Settings
OLLAMA_HOST = "localhost:11434"
WHISPER_DOCKER_HOST = "192.168.1.5:9999"

# Response Generation
# Mode: "template" (fast, instant) or "ai" (slow, more dynamic)
RESPONSE_MODE = "template"  # Use "ai" to try tinyllama later
AI_MODEL = "tinyllama"  # Model to use when RESPONSE_MODE="ai" (tinyllama or alfred-response)

# Finance Watchlist
FINANCE_WATCHLIST = {
    # Stocks (Yahoo Finance ticker symbols)
    "stocks": [
        {"symbol": "AAPL", "name": "Apple"},
        {"symbol": "GOOGL", "name": "Google"},
        {"symbol": "NVDA", "name": "NVIDIA"},
        {"symbol": "PEP", "name": "Pepsi"},
        {"symbol": "STLAM", "name": "Stellantis"},
    ],

    # Crypto (CoinGecko IDs)
    "crypto": [
        {"id": "bitcoin", "name": "Bitcoin", "symbol": "BTC"},
        {"id": "ethereum", "name": "Ethereum", "symbol": "ETH"}
    ],

    # Forex (base currency pairs)
    "forex": [
        {"from": "EUR", "to": "USD", "name": "Euro to US Dollar"},
        {"from": "GBP", "to": "USD", "name": "British Pound to US Dollar"},
        {"from": "USD", "to": "JPY", "name": "US Dollar to Japanese Yen"},
    ]
}
