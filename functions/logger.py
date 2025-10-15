#!/usr/bin/env python3
"""
Logging system for Alfred
Provides structured logging with rotation and different log levels
"""

import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional

class AlfredLogger:
    """Centralized logging for Alfred with rotation and formatting"""

    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        """
        Initialize Alfred's logging system

        Args:
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create logger
        self.logger = logging.getLogger("Alfred")
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        # File handler with rotation (10MB max, keep 5 backups)
        log_file = self.log_dir / "alfred.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)

        # Console handler (for terminal output)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter with timestamp and module
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Create separate error log
        error_file = self.log_dir / "errors.log"
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=10*1024*1024,
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)

        # Performance log
        self.perf_logger = logging.getLogger("Alfred.Performance")
        self.perf_logger.setLevel(logging.INFO)
        perf_file = self.log_dir / "performance.log"
        perf_handler = RotatingFileHandler(
            perf_file,
            maxBytes=5*1024*1024,
            backupCount=3
        )
        perf_handler.setFormatter(formatter)
        self.perf_logger.addHandler(perf_handler)

        self.logger.info("=" * 80)
        self.logger.info("Alfred logging system initialized")
        self.logger.info(f"Log directory: {self.log_dir.absolute()}")
        self.logger.info("=" * 80)

    # Command logging
    def log_wake_word(self, confidence: float):
        """Log wake word detection"""
        self.logger.info(f"🎤 Wake word detected (confidence: {confidence:.3f})")

    def log_command(self, transcription: str):
        """Log transcribed command"""
        self.logger.info(f"📝 Command: '{transcription}'")

    def log_intent(self, intent: str, language: str, confidence: float, parameters: dict):
        """Log parsed intent"""
        params_str = ", ".join(f"{k}={v}" for k, v in parameters.items()) if parameters else "none"
        self.logger.info(f"🎯 Intent: {intent} | Language: {language} | Confidence: {confidence:.2f} | Params: {params_str}")

    def log_response(self, response: str, language: str):
        """Log Alfred's response"""
        self.logger.info(f"💬 Response ({language}): {response[:100]}...")

    def log_tts(self, text: str, voice: str):
        """Log TTS generation"""
        self.logger.debug(f"🔊 TTS: {text[:50]}... (voice: {voice})")

    # API logging
    def log_api_call(self, api_name: str, endpoint: str, status: str):
        """Log API calls"""
        self.logger.info(f"🌐 API: {api_name} | {endpoint} | {status}")

    def log_api_error(self, api_name: str, error: str):
        """Log API errors"""
        self.logger.error(f"❌ API Error: {api_name} | {error}")

    # Performance logging
    def log_performance(self, operation: str, duration_ms: float):
        """Log performance metrics"""
        self.perf_logger.info(f"⚡ {operation}: {duration_ms:.0f}ms")

    # Function execution
    def log_function_start(self, function_name: str):
        """Log function execution start"""
        self.logger.debug(f"▶️  Executing: {function_name}")

    def log_function_end(self, function_name: str, success: bool):
        """Log function execution end"""
        status = "✅" if success else "❌"
        self.logger.debug(f"{status} Completed: {function_name}")

    # Error handling
    def log_error(self, error_type: str, message: str, details: Optional[str] = None):
        """Log errors"""
        self.logger.error(f"❌ {error_type}: {message}")
        if details:
            self.logger.error(f"   Details: {details}")

    def log_exception(self, exception: Exception, context: str = ""):
        """Log exceptions with traceback"""
        self.logger.exception(f"💥 Exception {context}: {str(exception)}")

    # System events
    def log_startup(self, config: dict):
        """Log system startup"""
        self.logger.info("🚀 Alfred starting up...")
        for key, value in config.items():
            self.logger.info(f"   {key}: {value}")

    def log_shutdown(self, reason: str = "User interrupt"):
        """Log system shutdown"""
        self.logger.info(f"🛑 Alfred shutting down: {reason}")
        self.logger.info("=" * 80)

    # Context and state
    def log_context_update(self, context_key: str, value: str):
        """Log context changes"""
        self.logger.debug(f"📋 Context updated: {context_key} = {value}")

    # Security
    def log_pin_attempt(self, success: bool, attempts: int):
        """Log PIN verification attempts"""
        status = "✅ Success" if success else f"❌ Failed (attempt {attempts})"
        self.logger.warning(f"🔐 PIN verification: {status}")

    def log_sensitive_action(self, action: str, authorized: bool):
        """Log sensitive actions"""
        status = "✅ Authorized" if authorized else "❌ Denied"
        self.logger.warning(f"⚠️  Sensitive action: {action} | {status}")

    # Generic logging methods
    def debug(self, message: str):
        """Debug level log"""
        self.logger.debug(message)

    def info(self, message: str):
        """Info level log"""
        self.logger.info(message)

    def warning(self, message: str):
        """Warning level log"""
        self.logger.warning(message)

    def error(self, message: str):
        """Error level log"""
        self.logger.error(message)

    def critical(self, message: str):
        """Critical level log"""
        self.logger.critical(message)


# Singleton instance
_logger_instance = None

def get_logger(log_dir: str = "logs", log_level: str = "INFO") -> AlfredLogger:
    """Get or create the Alfred logger singleton"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = AlfredLogger(log_dir, log_level)
    return _logger_instance


if __name__ == '__main__':
    # Test the logging system
    logger = get_logger(log_level="DEBUG")

    print("\n" + "=" * 60)
    print("Testing Alfred Logging System")
    print("=" * 60)

    # Test different log types
    logger.log_wake_word(0.985)
    logger.log_command("What's the weather?")
    logger.log_intent("weather", "en", 0.9, {"location": "Santhia"})
    logger.log_response("The weather in Santhia is 15°C, partly cloudy, sir.", "english")

    logger.log_api_call("OpenWeatherMap", "/weather", "200 OK")
    logger.log_performance("Weather query", 234.5)

    logger.log_function_start("get_weather")
    logger.log_function_end("get_weather", True)

    logger.log_error("API_TIMEOUT", "Weather API took too long", "Timeout after 10s")

    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.log_exception(e, "during testing")

    logger.log_pin_attempt(False, 1)
    logger.log_sensitive_action("send_email", False)

    logger.log_shutdown("Testing complete")

    print("\n✅ Logs written to ./logs/")
    print("   - alfred.log (main log)")
    print("   - errors.log (errors only)")
    print("   - performance.log (performance metrics)")
