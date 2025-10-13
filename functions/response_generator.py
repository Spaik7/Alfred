#!/usr/bin/env python3
"""
Response Generator for Alfred - Generates personality-rich responses using Ollama
"""

import requests
import json
from typing import Dict, Any, Optional

class ResponseGenerator:
    """Generate natural responses using alfred-response Ollama model"""

    def __init__(self, model: str = "alfred-response", ollama_host: str = "localhost:11434"):
        """
        Initialize response generator

        Args:
            model: Ollama model name
            ollama_host: Ollama API host:port
        """
        self.model = model
        self.ollama_url = f"http://{ollama_host}/api/generate"

    def generate_response(self, intent: str, result: Any, language: str = "en", parameters: Optional[Dict] = None) -> str:
        """
        Generate a natural response based on intent and result

        Args:
            intent: The intent type (e.g., "volume_up", "weather")
            result: The result of the action (e.g., "50" for volume, "success" for email)
            language: Language code ("en" or "it")
            parameters: Optional parameters from the intent

        Returns:
            Natural language response from Alfred
        """
        # Build the input for the model
        input_data = {
            "intent": intent,
            "result": result,
            "language": language
        }

        if parameters:
            input_data["parameters"] = parameters

        # Create the prompt
        prompt = json.dumps(input_data)

        try:
            # Call Ollama using HTTP API (much faster than subprocess)
            print(f"[DEBUG] Calling Ollama API for {self.model}...")
            print(f"[DEBUG] Prompt: {prompt[:100]}...")  # Show first 100 chars

            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 200,  # Limit response length
                        "temperature": 0.9
                    }
                },
                timeout=45  # Increased timeout
            )

            if response.status_code == 200:
                data = response.json()
                generated_text = data.get("response", "").strip()
                print(f"[DEBUG] Ollama responded: {len(generated_text)} chars")

                # Clean up any JSON artifacts if present
                if generated_text.startswith('"') and generated_text.endswith('"'):
                    generated_text = generated_text[1:-1]

                return generated_text if generated_text else self._fallback_response(intent, result, language)
            else:
                print(f"WARNING: Ollama HTTP error: {response.status_code}")
                print(f"[DEBUG] Response: {response.text[:200]}")
                return self._fallback_response(intent, result, language)

        except requests.exceptions.Timeout:
            print("WARNING: Ollama API timed out after 45s")
            return self._fallback_response(intent, result, language)
        except requests.exceptions.ConnectionError as e:
            print(f"WARNING: Could not connect to Ollama: {e}")
            return self._fallback_response(intent, result, language)
        except Exception as e:
            print(f"WARNING: Response generation failed: {e}")
            return self._fallback_response(intent, result, language)

    def preload_model(self) -> bool:
        """
        Preload the model into memory for faster responses

        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"Preloading {self.model} model...")
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": "test",
                    "stream": False
                },
                timeout=60
            )
            if response.status_code == 200:
                print(f"✅ {self.model} model loaded and ready!")
                return True
            return False
        except Exception as e:
            print(f"⚠️  Failed to preload model: {e}")
            return False

    def _fallback_response(self, intent: str, result: Any, language: str) -> str:
        """Fallback responses if model fails"""
        if language == "it":
            return f"Fatto, signore. {intent} completato."
        else:
            return f"Very well, sir. {intent} completed."


# Singleton instance
_generator = None

def get_generator() -> ResponseGenerator:
    """Get singleton response generator instance"""
    global _generator
    if _generator is None:
        _generator = ResponseGenerator()
    return _generator


def generate_response(intent: str, result: Any, language: str = "en", parameters: Optional[Dict] = None) -> str:
    """
    Generate a natural response (convenience function)

    Args:
        intent: The intent type
        result: The result of the action
        language: Language code ("en" or "it")
        parameters: Optional parameters

    Returns:
        Natural language response
    """
    return get_generator().generate_response(intent, result, language, parameters)


if __name__ == '__main__':
    # Test response generation
    generator = ResponseGenerator()

    print("Testing Response Generator\n" + "="*50)

    # Test volume control
    print("\n1. Volume up (English):")
    response = generator.generate_response("volume_up", "55", language="en", parameters={"amount": 10})
    print(f"   {response}")

    print("\n2. Volume up (Italian):")
    response = generator.generate_response("volume_up", "55", language="it", parameters={"amount": 5})
    print(f"   {response}")

    print("\n3. Volume set (English):")
    response = generator.generate_response("volume_set", "75", language="en", parameters={"level": 75})
    print(f"   {response}")

    print("\n4. Volume down (Italian):")
    response = generator.generate_response("volume_down", "30", language="it", parameters={"amount": 20})
    print(f"   {response}")
