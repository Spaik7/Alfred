#!/usr/bin/env python3
"""
Error Handling Framework for Alfred
Provides graceful error recovery with user-friendly messages and personality
"""

import time
import requests
from typing import Optional, Callable, Any
from functools import wraps
from enum import Enum

class ErrorType(Enum):
    """Types of errors Alfred can encounter"""
    API_TIMEOUT = "api_timeout"
    API_ERROR = "api_error"
    API_RATE_LIMIT = "api_rate_limit"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "auth_error"
    INVALID_INPUT = "invalid_input"
    FUNCTION_ERROR = "function_error"
    UNKNOWN_ERROR = "unknown_error"


class AlfredError(Exception):
    """Base exception for Alfred errors"""
    def __init__(self, error_type: ErrorType, message: str, details: Optional[str] = None):
        self.error_type = error_type
        self.message = message
        self.details = details
        super().__init__(self.message)


class ErrorHandler:
    """Centralized error handling with personality and recovery strategies"""

    # British butler error messages with dry humor
    ERROR_MESSAGES = {
        ErrorType.API_TIMEOUT: {
            "en": [
                "I'm afraid the {service} is taking rather longer than expected, sir.",
                "It appears {service} is not responding in a timely manner, sir.",
                "The {service} seems to be having a leisurely moment, sir. Shall we try again?",
            ],
            "it": [
                "Mi dispiace, signore, {service} sta impiegando più tempo del previsto.",
                "Sembra che {service} non risponda in tempo utile, signore.",
            ]
        },
        ErrorType.API_ERROR: {
            "en": [
                "I regret to inform you that {service} has encountered a difficulty, sir.",
                "I'm afraid {service} is not cooperating at the moment, sir.",
                "It seems {service} is experiencing technical difficulties, sir.",
            ],
            "it": [
                "Mi rammarico di informarla che {service} ha riscontrato un problema, signore.",
                "Temo che {service} non stia cooperando al momento, signore.",
            ]
        },
        ErrorType.API_RATE_LIMIT: {
            "en": [
                "I'm afraid we've been rather enthusiastic with {service}, sir. We must wait a moment.",
                "It appears we've exceeded our allowance with {service}, sir.",
                "{service} has politely asked us to slow down, sir.",
            ],
            "it": [
                "Temo che siamo stati troppo entusiasti con {service}, signore.",
                "Sembra che abbiamo superato il limite con {service}, signore.",
            ]
        },
        ErrorType.NETWORK_ERROR: {
            "en": [
                "I'm unable to reach {service} at the moment, sir. Perhaps a connectivity issue?",
                "The network appears to be uncooperative, sir.",
                "I seem to have lost my connection to {service}, sir.",
            ],
            "it": [
                "Non riesco a raggiungere {service} al momento, signore.",
                "La rete sembra non cooperare, signore.",
            ]
        },
        ErrorType.AUTHENTICATION_ERROR: {
            "en": [
                "I'm afraid my credentials for {service} are not being accepted, sir.",
                "It appears {service} does not recognize me, sir. Most irregular.",
                "I lack the proper authorization for {service}, sir.",
            ],
            "it": [
                "Temo che le mie credenziali per {service} non siano accettate, signore.",
                "Sembra che {service} non mi riconosca, signore.",
            ]
        },
        ErrorType.INVALID_INPUT: {
            "en": [
                "I'm afraid I didn't quite understand that, sir. Could you rephrase?",
                "That request is somewhat unclear to me, sir.",
                "I'm not entirely certain what you mean, sir. Might you clarify?",
            ],
            "it": [
                "Temo di non aver capito bene, signore. Può riformulare?",
                "Quella richiesta non è del tutto chiara, signore.",
            ]
        },
        ErrorType.FUNCTION_ERROR: {
            "en": [
                "I encountered an unexpected difficulty while {action}, sir.",
                "Something rather unusual occurred while {action}, sir.",
                "I'm afraid that didn't go as planned while {action}, sir.",
            ],
            "it": [
                "Ho riscontrato una difficoltà inaspettata durante {action}, signore.",
                "È successo qualcosa di insolito durante {action}, signore.",
            ]
        },
        ErrorType.UNKNOWN_ERROR: {
            "en": [
                "I'm afraid something unexpected has occurred, sir.",
                "An unforeseen complication has arisen, sir.",
                "This is most irregular, sir. An unknown error has occurred.",
            ],
            "it": [
                "Temo che sia successo qualcosa di inaspettato, signore.",
                "È sorta una complicazione imprevista, signore.",
            ]
        }
    }

    def __init__(self, logger=None):
        """
        Initialize error handler

        Args:
            logger: Alfred logger instance (optional)
        """
        self.logger = logger
        self.error_count = {}  # Track errors for rate limiting
        self.last_error_time = {}

    def get_user_message(
        self,
        error_type: ErrorType,
        language: str = "en",
        **kwargs
    ) -> str:
        """
        Get user-friendly error message with personality

        Args:
            error_type: Type of error
            language: Language code (en or it)
            **kwargs: Values to format into message (service, action, etc.)

        Returns:
            User-friendly error message
        """
        messages = self.ERROR_MESSAGES.get(error_type, self.ERROR_MESSAGES[ErrorType.UNKNOWN_ERROR])
        lang_messages = messages.get(language, messages["en"])

        # Pick first message (could rotate for variety)
        message_template = lang_messages[0]

        # Format with provided values
        try:
            return message_template.format(**kwargs)
        except KeyError:
            return message_template

    def handle_api_error(
        self,
        service: str,
        error: Exception,
        language: str = "en"
    ) -> tuple[ErrorType, str]:
        """
        Handle API-related errors

        Args:
            service: Name of the API service
            error: Exception that occurred
            language: Language for response

        Returns:
            Tuple of (error_type, user_message)
        """
        if self.logger:
            self.logger.log_api_error(service, str(error))

        # Determine error type
        if isinstance(error, requests.exceptions.Timeout):
            error_type = ErrorType.API_TIMEOUT
        elif isinstance(error, requests.exceptions.ConnectionError):
            error_type = ErrorType.NETWORK_ERROR
        elif isinstance(error, requests.exceptions.HTTPError):
            if error.response.status_code == 429:
                error_type = ErrorType.API_RATE_LIMIT
            elif error.response.status_code in [401, 403]:
                error_type = ErrorType.AUTHENTICATION_ERROR
            else:
                error_type = ErrorType.API_ERROR
        else:
            error_type = ErrorType.API_ERROR

        message = self.get_user_message(error_type, language, service=service)
        return error_type, message

    def handle_function_error(
        self,
        function_name: str,
        error: Exception,
        language: str = "en"
    ) -> tuple[ErrorType, str]:
        """
        Handle function execution errors

        Args:
            function_name: Name of function that failed
            error: Exception that occurred
            language: Language for response

        Returns:
            Tuple of (error_type, user_message)
        """
        if self.logger:
            self.logger.log_exception(error, f"in {function_name}")

        error_type = ErrorType.FUNCTION_ERROR
        message = self.get_user_message(
            error_type,
            language,
            action=function_name.replace("_", " ")
        )
        return error_type, message

    def should_retry(self, error_type: ErrorType, service: str, max_retries: int = 3) -> bool:
        """
        Determine if operation should be retried

        Args:
            error_type: Type of error
            service: Service name
            max_retries: Maximum retry attempts

        Returns:
            True if should retry
        """
        # Track error count
        key = f"{service}:{error_type.value}"
        self.error_count[key] = self.error_count.get(key, 0) + 1

        # Reset count after 60 seconds
        current_time = time.time()
        last_time = self.last_error_time.get(key, 0)
        if current_time - last_time > 60:
            self.error_count[key] = 1

        self.last_error_time[key] = current_time

        # Don't retry authentication errors or invalid input
        if error_type in [ErrorType.AUTHENTICATION_ERROR, ErrorType.INVALID_INPUT]:
            return False

        # Retry timeouts and network errors
        if error_type in [ErrorType.API_TIMEOUT, ErrorType.NETWORK_ERROR]:
            return self.error_count[key] <= max_retries

        # Retry API errors once
        if error_type == ErrorType.API_ERROR:
            return self.error_count[key] <= 1

        return False


def with_error_handling(service_name: str = "service", language: str = "en"):
    """
    Decorator for automatic error handling with retry logic

    Args:
        service_name: Name of service for error messages
        language: Language for error messages

    Usage:
        @with_error_handling(service_name="Weather API")
        def get_weather(location):
            # ... API call ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            handler = ErrorHandler()
            max_retries = 2
            retry_count = 0

            while retry_count <= max_retries:
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    error_type, message = handler.handle_api_error(service_name, e, language)

                    if not handler.should_retry(error_type, service_name, max_retries):
                        return {
                            "success": False,
                            "error": message,
                            "error_type": error_type.value
                        }

                    retry_count += 1
                    if retry_count <= max_retries:
                        time.sleep(1 * retry_count)  # Exponential backoff
                        continue
                    else:
                        return {
                            "success": False,
                            "error": message,
                            "error_type": error_type.value
                        }
                except Exception as e:
                    error_type, message = handler.handle_function_error(func.__name__, e, language)
                    return {
                        "success": False,
                        "error": message,
                        "error_type": error_type.value
                    }

            return {
                "success": False,
                "error": handler.get_user_message(ErrorType.UNKNOWN_ERROR, language),
                "error_type": ErrorType.UNKNOWN_ERROR.value
            }

        return wrapper
    return decorator


if __name__ == '__main__':
    # Test error handler
    print("\n" + "=" * 60)
    print("Testing Alfred Error Handler")
    print("=" * 60)

    handler = ErrorHandler()

    # Test different error messages
    print("\n1. API Timeout (English):")
    msg = handler.get_user_message(ErrorType.API_TIMEOUT, "en", service="Weather API")
    print(f"   {msg}")

    print("\n2. API Timeout (Italian):")
    msg = handler.get_user_message(ErrorType.API_TIMEOUT, "it", service="Weather API")
    print(f"   {msg}")

    print("\n3. Network Error:")
    msg = handler.get_user_message(ErrorType.NETWORK_ERROR, "en", service="News API")
    print(f"   {msg}")

    print("\n4. Rate Limit:")
    msg = handler.get_user_message(ErrorType.API_RATE_LIMIT, "en", service="Finance API")
    print(f"   {msg}")

    print("\n5. Function Error:")
    msg = handler.get_user_message(ErrorType.FUNCTION_ERROR, "en", action="calculating the result")
    print(f"   {msg}")

    # Test retry logic
    print("\n6. Testing retry logic:")
    print(f"   Should retry timeout? {handler.should_retry(ErrorType.API_TIMEOUT, 'test', 3)}")
    print(f"   Should retry auth? {handler.should_retry(ErrorType.AUTHENTICATION_ERROR, 'test', 3)}")

    print("\n✅ Error handling working correctly!")
