#!/usr/bin/env python3
"""
TTS Engine using Piper for Alfred voice assistant
Provides high-quality neural text-to-speech with multi-language support
"""

import subprocess
import os
import tempfile
from pathlib import Path
from enum import Enum
from typing import Dict

class Language(Enum):
    """Supported languages"""
    ENGLISH = "english"
    ITALIAN = "italian"

class Voice(Enum):
    """Available voice models"""
    US_MALE = "en_US-ryan-medium"
    ITALIAN_MALE = "it_IT-riccardo-x_low"

class TTSEngine:
    """Piper TTS engine wrapper for Alfred with multi-language support"""

    def __init__(self):
        """
        Initialize the TTS engine with multiple voice models
        """
        self.piper_path = Path.home() / "piper" / "piper" / "piper"
        self.voices_dir = Path.home() / "piper" / "voices"

        # Voice mapping: Language -> Voice model
        self.voice_map: Dict[Language, Voice] = {
            Language.ENGLISH: Voice.US_MALE,
            Language.ITALIAN: Voice.ITALIAN_MALE
        }

        # Verify Piper installation
        if not self.piper_path.exists():
            raise FileNotFoundError(
                f"Piper binary not found at {self.piper_path}. "
                "Please install Piper first."
            )

        # Verify all voice models exist
        missing_voices = []
        for voice in self.voice_map.values():
            model_path = self.voices_dir / f"{voice.value}.onnx"
            if not model_path.exists():
                missing_voices.append(f"{voice.value}.onnx")

        if missing_voices:
            raise FileNotFoundError(
                f"Voice models not found: {', '.join(missing_voices)}. "
                f"Please download the missing voice models to {self.voices_dir}"
            )

    def _get_model_path(self, language: Language) -> Path:
        """
        Get the model path for a specific language

        Args:
            language: Language to get the voice for

        Returns:
            Path to the voice model
        """
        voice = self.voice_map.get(language, Voice.US_MALE)
        return self.voices_dir / f"{voice.value}.onnx"

    def speak(self, text: str, language: Language = Language.ENGLISH, play: bool = True) -> str:
        """
        Convert text to speech and optionally play it

        Args:
            text: Text to convert to speech
            language: Language to use for speech (default: English)
            play: If True, play the audio immediately (default: True)

        Returns:
            Path to the generated WAV file

        Raises:
            RuntimeError: If TTS generation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Get the appropriate model for the language
        model_path = self._get_model_path(language)

        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            output_path = tmp_file.name

        try:
            # Generate speech using Piper
            process = subprocess.Popen(
                [
                    str(self.piper_path),
                    '--model', str(model_path),
                    '--output_file', output_path
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Send text to Piper
            stdout, stderr = process.communicate(input=text, timeout=30)

            if process.returncode != 0:
                raise RuntimeError(
                    f"Piper TTS failed with return code {process.returncode}: {stderr}"
                )

            # Play the audio if requested
            if play:
                self._play_audio(output_path)

            return output_path

        except subprocess.TimeoutExpired:
            process.kill()
            raise RuntimeError("TTS generation timed out after 30 seconds")
        except Exception as e:
            # Clean up temporary file on error
            if os.path.exists(output_path):
                os.unlink(output_path)
            raise RuntimeError(f"TTS generation failed: {e}")

    def _play_audio(self, wav_path: str):
        """
        Play audio file using aplay

        Args:
            wav_path: Path to WAV file to play
        """
        try:
            subprocess.run(
                ['aplay', '-q', wav_path],
                check=True,
                timeout=60,
                capture_output=True
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Audio playback timed out")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Audio playback failed: {e}")
        except FileNotFoundError:
            raise RuntimeError(
                "aplay not found. Please install alsa-utils: sudo apt install alsa-utils"
            )

    def save_speech(self, text: str, output_file: str, language: Language = Language.ENGLISH) -> str:
        """
        Generate speech and save to a specific file without playing

        Args:
            text: Text to convert to speech
            output_file: Path where to save the WAV file
            language: Language to use for speech (default: English)

        Returns:
            Path to the generated WAV file
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Get the appropriate model for the language
        model_path = self._get_model_path(language)

        try:
            # Generate speech using Piper
            process = subprocess.Popen(
                [
                    str(self.piper_path),
                    '--model', str(model_path),
                    '--output_file', output_file
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Send text to Piper
            stdout, stderr = process.communicate(input=text, timeout=30)

            if process.returncode != 0:
                raise RuntimeError(
                    f"Piper TTS failed with return code {process.returncode}: {stderr}"
                )

            return output_file

        except subprocess.TimeoutExpired:
            process.kill()
            raise RuntimeError("TTS generation timed out after 30 seconds")
        except Exception as e:
            raise RuntimeError(f"TTS generation failed: {e}")


# Simple test/example usage
if __name__ == "__main__":
    import sys

    # Create TTS engine with multi-language support
    tts = TTSEngine()

    # Test phrases in both languages
    test_phrases = [
        ("Good afternoon sir, Alfred at your service.", Language.ENGLISH),
        ("Buongiorno signore, sono Alfred al suo servizio.", Language.ITALIAN),
        ("The weather forecast for today is partly cloudy.", Language.ENGLISH),
        ("Il tempo oggi è parzialmente nuvoloso.", Language.ITALIAN),
    ]

    if len(sys.argv) > 1:
        # Use command-line argument if provided
        text = ' '.join(sys.argv[1:])
        lang = Language.ITALIAN if any(c in text for c in 'àèéìòù') else Language.ENGLISH
        print(f"Speaking ({lang.value}): {text}")
        wav_path = tts.speak(text, language=lang)
        print(f"Generated: {wav_path}")
        os.unlink(wav_path)
    else:
        # Run through test phrases
        for phrase, lang in test_phrases:
            print(f"\nSpeaking ({lang.value}): {phrase}")
            try:
                wav_path = tts.speak(phrase, language=lang)
                print(f"✓ Generated: {wav_path}")
                # Clean up temp file after playing
                os.unlink(wav_path)
            except Exception as e:
                print(f"✗ Error: {e}")
