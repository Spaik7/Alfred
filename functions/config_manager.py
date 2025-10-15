#!/usr/bin/env python3
"""
Configuration Management for Alfred
Centralized config with validation, environment variables, and easy updates
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict

@dataclass
class AlfredConfig:
    """Alfred's configuration with defaults and validation"""

    # Location & Language
    default_location: str = "Santhia, Italy"
    default_timezone: str = "Europe/Rome"
    default_language: str = "en"  # en or it
    temp_unit: str = "celsius"  # celsius or fahrenheit

    # API Keys (can be overridden by environment variables)
    news_api_key: str = ""
    google_maps_api_key: str = ""
    spoonacular_api_key: str = ""
    openweather_api_key: str = ""

    # News Settings
    news_countries: list = field(default_factory=lambda: ["eu", "us"])
    news_category: Optional[str] = None  # business, entertainment, health, science, sports, technology

    # System Settings
    ollama_host: str = "localhost:11434"
    whisper_docker_host: str = "192.168.1.5:9999"

    # Response Generation
    response_mode: str = "template"  # template or ai
    ai_model: str = "tinyllama"  # Model for AI mode

    # Wake Word Detection
    wake_word: str = "Alfred"
    wake_threshold: float = 0.98
    silence_threshold: float = 0.01
    silence_duration: float = 2.0

    # Audio Settings
    sample_rate: int = 48000
    target_sample_rate: int = 16000
    wake_duration: float = 1.5

    # Volume
    startup_volume: int = 20

    # Logging
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_dir: str = "logs"
    enable_performance_logging: bool = True

    # TTS Settings
    enable_tts: bool = True
    tts_voice_english: str = "en_US-ryan-high"
    tts_voice_italian: str = "it_IT-riccardo-x_low"

    # Whisper Settings
    whisper_mode: str = "docker"  # local or docker
    whisper_model: str = "base"  # tiny, base, small, medium, large

    # Personality Settings
    personality_enabled: bool = True
    personality_formality: str = "high"  # low, medium, high
    personality_humor: bool = True

    # Context Settings
    enable_context: bool = True
    context_timeout: int = 300  # seconds (5 minutes)
    max_context_history: int = 10

    # Security
    enable_pin: bool = True
    pin_hash: str = ""  # bcrypt hash
    pin_max_attempts: int = 3
    pin_lockout_duration: int = 300  # seconds (5 minutes)

    # Finance Watchlist
    watchlist_stocks: list = field(default_factory=lambda: [
        {"symbol": "AAPL", "name": "Apple"},
        {"symbol": "GOOGL", "name": "Google"},
        {"symbol": "NVDA", "name": "NVIDIA"},
    ])
    watchlist_crypto: list = field(default_factory=lambda: [
        {"id": "bitcoin", "name": "Bitcoin", "symbol": "BTC"},
        {"id": "ethereum", "name": "Ethereum", "symbol": "ETH"},
    ])
    watchlist_forex: list = field(default_factory=lambda: [
        {"from": "EUR", "to": "USD", "name": "Euro to US Dollar"},
    ])

    def __post_init__(self):
        """Validate configuration after initialization"""
        self.validate()

    def validate(self):
        """Validate configuration values"""
        # Validate temperature unit
        if self.temp_unit not in ["celsius", "fahrenheit"]:
            raise ValueError(f"Invalid temp_unit: {self.temp_unit}")

        # Validate response mode
        if self.response_mode not in ["template", "ai"]:
            raise ValueError(f"Invalid response_mode: {self.response_mode}")

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"Invalid log_level: {self.log_level}")

        # Validate thresholds
        if not 0 <= self.wake_threshold <= 1:
            raise ValueError(f"wake_threshold must be 0-1: {self.wake_threshold}")

        if not 0 <= self.startup_volume <= 100:
            raise ValueError(f"startup_volume must be 0-100: {self.startup_volume}")

        # Validate whisper mode
        if self.whisper_mode not in ["local", "docker"]:
            raise ValueError(f"Invalid whisper_mode: {self.whisper_mode}")

    def load_from_env(self):
        """Load sensitive values from environment variables"""
        # API Keys
        self.news_api_key = os.getenv("NEWS_API_KEY", self.news_api_key)
        self.google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY", self.google_maps_api_key)
        self.spoonacular_api_key = os.getenv("SPOONACULAR_API_KEY", self.spoonacular_api_key)
        self.openweather_api_key = os.getenv("OPENWEATHER_API_KEY", self.openweather_api_key)

        # Other settings
        if os.getenv("ALFRED_LOG_LEVEL"):
            self.log_level = os.getenv("ALFRED_LOG_LEVEL")

        if os.getenv("ALFRED_WAKE_THRESHOLD"):
            self.wake_threshold = float(os.getenv("ALFRED_WAKE_THRESHOLD"))

        if os.getenv("ALFRED_WHISPER_MODE"):
            self.whisper_mode = os.getenv("ALFRED_WHISPER_MODE")

        self.validate()

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return asdict(self)

    def save_to_file(self, filepath: str):
        """Save configuration to JSON file"""
        config_dict = self.to_dict()
        # Don't save sensitive keys
        config_dict['news_api_key'] = "***"
        config_dict['google_maps_api_key'] = "***"
        config_dict['spoonacular_api_key'] = "***"
        config_dict['openweather_api_key'] = "***"
        config_dict['pin_hash'] = "***"

        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'AlfredConfig':
        """Load configuration from JSON file"""
        if not os.path.exists(filepath):
            return cls()  # Return default config

        with open(filepath, 'r') as f:
            data = json.load(f)

        # Filter out None values and unknown fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields and v is not None}

        return cls(**filtered_data)

    def get_finance_watchlist(self) -> Dict[str, list]:
        """Get finance watchlist in the format expected by finance functions"""
        return {
            "stocks": self.watchlist_stocks,
            "crypto": self.watchlist_crypto,
            "forex": self.watchlist_forex
        }


# Singleton instance
_config_instance = None

def get_config(config_file: str = "config.json") -> AlfredConfig:
    """Get or create the Alfred configuration singleton"""
    global _config_instance
    if _config_instance is None:
        # Try to load from file, fall back to defaults
        if os.path.exists(config_file):
            _config_instance = AlfredConfig.load_from_file(config_file)
        else:
            _config_instance = AlfredConfig()

        # Override with environment variables
        _config_instance.load_from_env()

    return _config_instance


if __name__ == '__main__':
    # Test configuration management
    print("\n" + "=" * 60)
    print("Testing Alfred Configuration Management")
    print("=" * 60)

    # Create config with defaults
    config = AlfredConfig()
    print("\n1. Default Configuration:")
    print(f"   Default location: {config.default_location}")
    print(f"   Wake threshold: {config.wake_threshold}")
    print(f"   Response mode: {config.response_mode}")
    print(f"   Log level: {config.log_level}")

    # Save to file
    config.save_to_file("test_config.json")
    print("\n2. Saved to test_config.json")

    # Load from file
    loaded_config = AlfredConfig.load_from_file("test_config.json")
    print("\n3. Loaded from file:")
    print(f"   Default location: {loaded_config.default_location}")

    # Test environment variable override
    os.environ["ALFRED_LOG_LEVEL"] = "DEBUG"
    os.environ["ALFRED_WAKE_THRESHOLD"] = "0.95"
    config_with_env = AlfredConfig()
    config_with_env.load_from_env()
    print("\n4. With environment variables:")
    print(f"   Log level: {config_with_env.log_level}")
    print(f"   Wake threshold: {config_with_env.wake_threshold}")

    # Test validation
    print("\n5. Testing validation...")
    try:
        bad_config = AlfredConfig(temp_unit="kelvin")
        bad_config.validate()
    except ValueError as e:
        print(f"   ✅ Caught invalid config: {e}")

    # Clean up
    os.remove("test_config.json")
    print("\n✅ Configuration management working correctly!")
