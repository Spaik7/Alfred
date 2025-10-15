#!/usr/bin/env python3
"""
Logging system for Alfred
Simplified data-flow logging with daily rotation (7-day retention)
"""

import logging
import os
import glob
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta
from typing import Optional
import json

class AlfredLogger:
    """Simplified logging focusing on data flow: Input → Parser → Work → Output"""

    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        """
        Initialize Alfred's logging system with daily rotation

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

        # Daily rotating file handler
        # Rotates at midnight, keeps 7 days
        log_file = self.log_dir / "alfred.log"
        file_handler = TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=7  # Keep 7 days
        )
        file_handler.setLevel(logging.INFO)
        file_handler.suffix = "%Y-%m-%d"  # Date suffix for rotated files

        # Console handler (minimal output)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        # Clean up old logs on startup
        self._cleanup_old_logs()

        self.logger.info("=" * 80)
        self.logger.info("Alfred logging system initialized")
        self.logger.info(f"Log directory: {self.log_dir.absolute()}")
        self.logger.info(f"Daily rotation enabled - keeping 7 days")
        self.logger.info("=" * 80)

    def _cleanup_old_logs(self):
        """Remove log files older than 7 days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=7)

            # Find all rotated log files (alfred.log.YYYY-MM-DD)
            pattern = str(self.log_dir / "alfred.log.*")
            old_logs = []

            for log_file in glob.glob(pattern):
                # Extract date from filename
                try:
                    # Format: alfred.log.2025-10-15
                    date_str = log_file.split('.')[-1]
                    log_date = datetime.strptime(date_str, "%Y-%m-%d")

                    if log_date < cutoff_date:
                        old_logs.append(log_file)
                        os.remove(log_file)
                except (ValueError, OSError):
                    continue

            if old_logs:
                self.logger.info(f"Cleaned up {len(old_logs)} old log files (>7 days)")

        except Exception as e:
            self.logger.warning(f"Could not clean up old logs: {e}")

    # =============================
    #   DATA FLOW LOGGING
    # =============================

    def log_conversation_turn(self,
                             user_input: str,
                             parser_output: dict,
                             work_output: dict,
                             ai_response: str,
                             final_output: str):
        """
        Log a complete conversation turn (Input → Parser → Work → AI → Output)

        Args:
            user_input: What the user said
            parser_output: Intent parser output (intent, language, params)
            work_output: Result from API/function (weather data, calculation result, etc.)
            ai_response: Raw AI response (before any post-processing)
            final_output: Final output spoken to user
        """
        separator = "─" * 80

        self.logger.info(separator)
        self.logger.info("📥 USER INPUT:")
        self.logger.info(f"   \"{user_input}\"")

        self.logger.info("")
        self.logger.info("🔍 PARSER OUTPUT:")
        self.logger.info(f"   Intent: {parser_output.get('intent', 'unknown')}")
        self.logger.info(f"   Language: {parser_output.get('language', 'unknown')}")
        self.logger.info(f"   Confidence: {parser_output.get('confidence', 0):.2f}")
        if parser_output.get('parameters'):
            params_str = json.dumps(parser_output['parameters'], indent=6)
            self.logger.info(f"   Parameters: {params_str}")

        self.logger.info("")
        self.logger.info("⚙️  WORK OUTPUT (API/Function Result):")
        if work_output.get('success'):
            # Log relevant data only (not the entire dict)
            if 'error' in work_output:
                self.logger.info(f"   ❌ Error: {work_output['error']}")
            else:
                # Format work output nicely
                work_str = self._format_work_output(parser_output.get('intent'), work_output)
                self.logger.info(f"   {work_str}")
        else:
            self.logger.info(f"   ❌ Failed: {work_output.get('error', 'Unknown error')}")

        self.logger.info("")
        self.logger.info("🤖 AI RESPONSE:")
        self.logger.info(f"   \"{ai_response}\"")

        self.logger.info("")
        self.logger.info("📤 FINAL OUTPUT (Spoken to User):")
        self.logger.info(f"   \"{final_output}\"")

        self.logger.info(separator)
        self.logger.info("")  # Blank line for readability

    def _format_work_output(self, intent: str, work_output: dict) -> str:
        """Format work output based on intent type"""
        if intent == 'weather':
            return f"Temp: {work_output.get('temperature_c')}°C, {work_output.get('description')}, Location: {work_output.get('location')}"
        elif intent == 'time':
            return f"Time: {work_output.get('time')}"
        elif intent == 'date':
            return f"Date: {work_output.get('date_formatted')}"
        elif intent == 'calculate':
            return f"Result: {work_output.get('result')}"
        elif intent == 'volume_set' or intent == 'volume_up' or intent == 'volume_down':
            return f"Volume: {work_output}"
        elif intent == 'system_status':
            cpu = work_output.get('cpu', {}).get('usage_percent', 'N/A')
            mem = work_output.get('memory', {}).get('usage_percent', 'N/A')
            temp = work_output.get('temperature', {}).get('celsius', 'N/A')
            return f"CPU: {cpu}%, Memory: {mem}%, Temp: {temp}°C"
        elif intent == 'transport_car' or intent == 'transport_public':
            return f"Duration: {work_output.get('duration_text', work_output.get('duration'))}, Destination: {work_output.get('destination')}"
        elif intent == 'news':
            count = len(work_output.get('articles', []))
            return f"Articles: {count}"
        elif intent == 'finance' or intent == 'finance_watchlist':
            stocks = len(work_output.get('stocks', []))
            crypto = len(work_output.get('crypto', []))
            return f"Stocks: {stocks}, Crypto: {crypto}"
        elif intent == 'recipe_search':
            count = len(work_output.get('recipes', []))
            return f"Recipes found: {count}"
        else:
            # Generic format
            return json.dumps(work_output, indent=6)

    # =============================
    #   SIMPLE EVENT LOGGING
    # =============================

    def log_startup(self, config: dict):
        """Log system startup"""
        self.logger.info("🚀 Alfred starting up...")
        for key, value in config.items():
            self.logger.info(f"   {key}: {value}")

    def log_shutdown(self, reason: str = "User interrupt"):
        """Log system shutdown"""
        self.logger.info(f"🛑 Alfred shutting down: {reason}")
        self.logger.info("=" * 80)

    def log_error(self, error_type: str, message: str, details: Optional[str] = None):
        """Log errors"""
        self.logger.error(f"❌ {error_type}: {message}")
        if details:
            self.logger.error(f"   Details: {details}")

    def log_exception(self, exception: Exception, context: str = ""):
        """Log exceptions with traceback"""
        self.logger.exception(f"💥 Exception {context}: {str(exception)}")

    # Generic logging methods
    def info(self, message: str):
        """Info level log"""
        self.logger.info(message)

    def warning(self, message: str):
        """Warning level log"""
        self.logger.warning(message)

    def error(self, message: str):
        """Error level log"""
        self.logger.error(message)

    def debug(self, message: str):
        """Debug level log"""
        self.logger.debug(message)

    def log_context_update(self, context_key: str, value: str):
        """Log context updates (for debugging context management)"""
        self.logger.debug(f"🔄 Context update: {context_key} = {value}")


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
    logger = get_logger(log_level="INFO")

    print("\n" + "=" * 60)
    print("Testing Alfred Logging System")
    print("=" * 60)

    # Test conversation turn logging
    logger.log_conversation_turn(
        user_input="What's the weather in Milan?",
        parser_output={
            'intent': 'weather',
            'language': 'en',
            'confidence': 0.95,
            'parameters': {'location': 'Milan'}
        },
        work_output={
            'success': True,
            'temperature_c': 15,
            'temperature_f': 59,
            'description': 'partly cloudy',
            'humidity': 65,
            'wind_speed': 12,
            'location': 'Milan'
        },
        ai_response="The weather in Milan is 15 degrees Celsius and partly cloudy, sir.",
        final_output="The weather in Milan is 15 degrees Celsius and partly cloudy, sir."
    )

    # Test error logging
    logger.log_error("API_TIMEOUT", "Weather API took too long", "Timeout after 10s")

    # Test exception logging
    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger.log_exception(e, "during testing")

    logger.log_shutdown("Testing complete")

    print("\n✅ Logs written to ./logs/")
    print("   - alfred.log (today's log)")
    print("   - alfred.log.YYYY-MM-DD (rotated daily, keeps 7 days)")
    print("\nView logs:")
    print("   cat logs/alfred.log")
    print("   tail -f logs/alfred.log  # Follow in real-time")
