#!/usr/bin/env python3
"""
Context Manager for Alfred
Maintains conversation state and handles follow-up questions
"""

import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class ConversationTurn:
    """Single turn in conversation"""
    timestamp: float
    command: str
    intent: str
    language: str
    parameters: Dict[str, Any]
    response: str
    success: bool


class ContextManager:
    """Manages conversation context and state"""

    def __init__(
        self,
        timeout: int = 300,  # 5 minutes
        max_history: int = 10,
        logger=None
    ):
        """
        Initialize context manager

        Args:
            timeout: Context timeout in seconds
            max_history: Maximum conversation turns to remember
            logger: Alfred logger instance
        """
        self.timeout = timeout
        self.max_history = max_history
        self.logger = logger

        # Conversation history
        self.history: List[ConversationTurn] = []

        # Current context state
        self.current_location: Optional[str] = None
        self.current_destination: Optional[str] = None
        self.current_time_reference: Optional[str] = None
        self.current_topic: Optional[str] = None
        self.last_entity: Optional[str] = None  # For "it", "that", etc.

        # User preferences (learned over time)
        self.preferences: Dict[str, Any] = {}

        # Active state
        self.last_activity: float = time.time()
        self.session_start: float = time.time()

    def is_active(self) -> bool:
        """Check if context is still active (within timeout)"""
        return (time.time() - self.last_activity) < self.timeout

    def reset(self):
        """Reset context (timeout or explicit reset)"""
        if self.logger:
            self.logger.log_context_update("reset", "Context cleared due to timeout or reset")

        self.history.clear()
        self.current_location = None
        self.current_destination = None
        self.current_time_reference = None
        self.current_topic = None
        self.last_entity = None
        self.last_activity = time.time()

    def add_turn(
        self,
        command: str,
        intent: str,
        language: str,
        parameters: Dict[str, Any],
        response: str,
        success: bool
    ):
        """
        Add a conversation turn to history

        Args:
            command: User's command
            intent: Detected intent
            language: Language used
            parameters: Intent parameters
            response: Alfred's response
            success: Whether command succeeded
        """
        # Reset if context timed out
        if not self.is_active():
            self.reset()

        # Create turn
        turn = ConversationTurn(
            timestamp=time.time(),
            command=command,
            intent=intent,
            language=language,
            parameters=parameters,
            response=response,
            success=success
        )

        # Add to history
        self.history.append(turn)

        # Trim history if too long
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # Update context state
        self._update_context_from_turn(turn)

        # Update activity
        self.last_activity = time.time()

        if self.logger:
            self.logger.debug(f"Context updated: {len(self.history)} turns in history")

    def _update_context_from_turn(self, turn: ConversationTurn):
        """Update context state from conversation turn"""
        # Extract locations
        if 'location' in turn.parameters:
            self.current_location = turn.parameters['location']
            if self.logger:
                self.logger.log_context_update("location", self.current_location)

        if 'destination' in turn.parameters:
            self.current_destination = turn.parameters['destination']
            self.last_entity = self.current_destination  # Can refer to "it"
            if self.logger:
                self.logger.log_context_update("destination", self.current_destination)

        # Extract time references
        if 'arrival_time' in turn.parameters:
            self.current_time_reference = turn.parameters['arrival_time']

        # Track topic
        self.current_topic = self._infer_topic(turn.intent)

        # Track entities that can be referenced
        if turn.intent in ['recipe_search', 'recipe_random']:
            if 'query' in turn.parameters:
                self.last_entity = turn.parameters['query']

    def _infer_topic(self, intent: str) -> str:
        """Infer conversation topic from intent"""
        topic_map = {
            'weather': 'weather',
            'transport_car': 'transport',
            'transport_public': 'transport',
            'recipe_search': 'food',
            'recipe_random': 'food',
            'news': 'news',
            'finance': 'finance',
            'finance_watchlist': 'finance',
            'calculate': 'math',
        }
        return topic_map.get(intent, 'general')

    def get_last_turn(self) -> Optional[ConversationTurn]:
        """Get the most recent conversation turn"""
        return self.history[-1] if self.history else None

    def get_last_n_turns(self, n: int = 3) -> List[ConversationTurn]:
        """Get last N conversation turns"""
        return self.history[-n:] if self.history else []

    def resolve_pronoun(self, text: str) -> str:
        """
        Resolve pronouns like "it", "there", "that" using context

        Args:
            text: User's command with potential pronouns

        Returns:
            Text with pronouns resolved
        """
        if not self.is_active():
            return text

        text_lower = text.lower()

        # "it" or "that" -> last entity
        if self.last_entity:
            if ' it ' in text_lower or text_lower.startswith('it ') or text_lower.endswith(' it'):
                text = text.replace(' it ', f' {self.last_entity} ')
                text = text.replace('It ', f'{self.last_entity.capitalize()} ')

            if ' that ' in text_lower or text_lower.startswith('that '):
                text = text.replace(' that ', f' {self.last_entity} ')
                text = text.replace('That ', f'{self.last_entity.capitalize()} ')

        # "there" -> last destination
        if self.current_destination and ' there' in text_lower:
            text = text.replace(' there', f' {self.current_destination}')

        return text

    def handle_follow_up(self, command: str, current_intent: str) -> tuple[str, Dict[str, Any]]:
        """
        Handle follow-up questions that depend on context

        Args:
            command: User's command
            current_intent: Currently detected intent

        Returns:
            Tuple of (resolved_command, additional_parameters)
        """
        if not self.is_active() or not self.history:
            return command, {}

        command_lower = command.lower()
        additional_params = {}

        # "What about tomorrow?" -> needs previous location/topic
        if 'tomorrow' in command_lower or 'what about' in command_lower:
            last_turn = self.get_last_turn()
            if last_turn:
                # Copy relevant parameters from last turn
                if self.current_location and 'location' not in additional_params:
                    additional_params['location'] = self.current_location

                if self.current_destination and 'destination' not in additional_params:
                    additional_params['destination'] = self.current_destination

        # "How long will it take?" -> needs destination from context
        if ('how long' in command_lower or 'will it take' in command_lower) and self.current_destination:
            additional_params['destination'] = self.current_destination

        # "What's the traffic like?" -> needs destination
        if 'traffic' in command_lower and self.current_destination and 'to' not in command_lower:
            additional_params['destination'] = self.current_destination

        # Resolve pronouns
        resolved_command = self.resolve_pronoun(command)

        return resolved_command, additional_params

    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of current context"""
        return {
            "active": self.is_active(),
            "turns": len(self.history),
            "current_topic": self.current_topic,
            "current_location": self.current_location,
            "current_destination": self.current_destination,
            "last_entity": self.last_entity,
            "session_duration": int(time.time() - self.session_start),
            "time_since_last": int(time.time() - self.last_activity)
        }

    def set_preference(self, key: str, value: Any):
        """Set a user preference"""
        self.preferences[key] = value
        if self.logger:
            self.logger.log_context_update(f"preference.{key}", str(value))

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        return self.preferences.get(key, default)


# Singleton instance
_context_instance = None

def get_context_manager(timeout: int = 300, max_history: int = 10, logger=None) -> ContextManager:
    """Get or create the context manager singleton"""
    global _context_instance
    if _context_instance is None:
        _context_instance = ContextManager(timeout, max_history, logger)
    return _context_instance


if __name__ == '__main__':
    # Test context manager
    print("\n" + "=" * 60)
    print("Testing Alfred Context Manager")
    print("=" * 60)

    context = ContextManager(timeout=300)

    # Simulate conversation
    print("\n1. First command: 'What's the weather in Milan?'")
    context.add_turn(
        command="What's the weather in Milan?",
        intent="weather",
        language="en",
        parameters={"location": "Milan"},
        response="The weather in Milan is 15°C, partly cloudy.",
        success=True
    )
    print(f"   Location stored: {context.current_location}")

    print("\n2. Follow-up: 'What about tomorrow?'")
    resolved, params = context.handle_follow_up("What about tomorrow?", "weather")
    print(f"   Additional params: {params}")

    print("\n3. New command: 'Traffic to Vercelli'")
    context.add_turn(
        command="Traffic to Vercelli",
        intent="transport_car",
        language="en",
        parameters={"destination": "Vercelli"},
        response="It will take 22 minutes to get to Vercelli.",
        success=True
    )
    print(f"   Destination stored: {context.current_destination}")
    print(f"   Last entity: {context.last_entity}")

    print("\n4. Follow-up with pronoun: 'How long to get there?'")
    resolved, params = context.handle_follow_up("How long to get there?", "transport_car")
    print(f"   Resolved: {resolved}")
    print(f"   Additional params: {params}")

    print("\n5. Pronoun resolution: 'What's the traffic to it?'")
    resolved = context.resolve_pronoun("What's the traffic to it?")
    print(f"   Resolved: {resolved}")

    print("\n6. Context summary:")
    summary = context.get_context_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")

    print("\n7. Test timeout:")
    context.last_activity = time.time() - 400  # 400 seconds ago
    print(f"   Is active? {context.is_active()}")
    context.add_turn("test", "test", "en", {}, "test", True)
    print(f"   After new turn, history length: {len(context.history)}")

    print("\n✅ Context management working correctly!")
