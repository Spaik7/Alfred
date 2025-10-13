import sounddevice as sd
import numpy as np
import librosa
import onnxruntime as ort
import subprocess
import time
from tqdm import tqdm
from scipy.io.wavfile import write
import gc
import requests
import os
import sys
import argparse
from pathlib import Path
from functions.intents import parse_intent
from functions.tts_engine import TTSEngine, Language
from functions import volume_control, time_date, system, general, weather
from functions.response_generator import generate_response as generate_ai_response
from functions.response_templates import generate_template_response
from config import RESPONSE_MODE, AI_MODEL

# =============================
#     COMMAND LINE ARGUMENTS
# =============================
parser = argparse.ArgumentParser(
    description='Alfred Wake Word Assistant',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Use local Whisper (default base model)
  python alfred.py -w local

  # Use local Whisper with larger model
  python alfred.py -w local -wm medium

  # Use Docker Whisper with custom IP
  python alfred.py -w docker -d 192.168.1.10:9999

  # Set custom wake threshold (more sensitive)
  python alfred.py -t 0.8

  # Adjust silence detection (quieter environment)
  python alfred.py -s 0.005

  # Increase silence duration (for speech with long pauses)
  python alfred.py -st 3.0

  # Combined options
  python alfred.py -w local -wm small -t 0.9 -s 0.02 -st 2.5
    """
)

parser.add_argument(
    '-w', '--whisper',
    choices=['local', 'docker'],
    default='docker',
    help='Use local Whisper or Docker Whisper (default: docker)'
)
parser.add_argument(
    '-d', '--docker-ip',
    default='192.168.1.5:9999',
    help='Docker Whisper API IP:PORT (default: 192.168.1.5:9999)'
)
parser.add_argument(
    '-wm', '--whisper-model',
    choices=['tiny', 'base', 'small', 'medium', 'large'],
    default='base',
    help='Whisper model for local mode (default: base). Larger models are more accurate but slower.'
)
parser.add_argument(
    '-t', '--threshold',
    type=float,
    default=0.98,
    help='Wake word detection threshold 0-1 (default: 0.98, lower = more sensitive)'
)
parser.add_argument(
    '-s', '--silence-threshold',
    type=float,
    default=0.01,
    help='Silence detection threshold for voice activity detection. This is the RMS energy level below which audio is considered silence. Range: 0.001-0.1. Lower values (e.g., 0.005) detect silence more aggressively, stopping recording sooner. Higher values (e.g., 0.05) require louder silence, useful in noisy environments. (default: 0.01)'
)
parser.add_argument(
    '-st', '--silence-duration',
    type=float,
    default=2.0,
    help='How many seconds of continuous silence before stopping recording. Increase this if your speech has long pauses. Range: 0.5-5.0 seconds. (default: 2.0)'
)

parser.add_argument(
    '--debug',
    action='store_true',
    help='Debug mode: type commands instead of using wake word detection'
)

parser.add_argument(
    '--no-tts',
    action='store_true',
    help='Disable TTS output (print only)'
)

parser.add_argument(
    '-v', '--volume',
    type=int,
    default=20,
    help='Startup volume level 0-100 (default: 20)'
)

args = parser.parse_args()

# =============================
#     TTS ENGINE SETUP
# =============================
tts_engine = None
if not args.no_tts:
    try:
        print("Initializing TTS engine...")
        tts_engine = TTSEngine()
        print("✅ TTS engine ready (US English + Italian voices)!")
    except Exception as e:
        print(f"⚠️  TTS initialization failed: {e}")
        print("   Continuing without voice output...")
        tts_engine = None

# =============================
#        SPEECH OUTPUT
# =============================
def speak(text: str, language: str = "english"):
    """
    Speak text using Piper TTS with automatic voice selection

    Args:
        text: Text to speak
        language: Language of the text ("english" or "italian")
    """
    print(f"🗣️  Alfred ({language}): {text}")

    if tts_engine:
        try:
            # Map string language to Language enum
            lang = Language.ITALIAN if language.lower() == "italian" else Language.ENGLISH
            wav_path = tts_engine.speak(text, language=lang)
            # Clean up temporary file after playing
            if os.path.exists(wav_path):
                os.unlink(wav_path)
        except Exception as e:
            print(f"⚠️  TTS error: {e}")
    else:
        print("   [TTS disabled]")

# =============================
#    RESPONSE GENERATION
# =============================
def generate_response(intent: str, result: str, language: str = "en", parameters: dict = None):
    """
    Unified response generation - switches between template and AI modes

    Args:
        intent: Intent type (e.g., "weather", "time", "volume_up")
        result: Result value to include in response
        language: Language code ("en" or "it")
        parameters: Additional parameters for response generation

    Returns:
        Generated response string
    """
    if RESPONSE_MODE == "template":
        return generate_template_response(intent, result, language, parameters)
    else:  # AI mode
        return generate_ai_response(intent, result, language, parameters)

# =============================
#      MODEL LOADING
# =============================
def load_model_with_progress(path):
    print(f"Loading ONNX model '{path}' ...")
    with tqdm(total=100) as pbar:
        for _ in range(10):
            time.sleep(0.05)
            pbar.update(10)

    # Load ONNX model with ONNX Runtime
    session = ort.InferenceSession(path, providers=['CPUExecutionProvider'])

    print("✅ Model loaded successfully!")
    return session

# =============================
#      MODEL CHECK
# =============================
MODEL_PATH = Path("models/alfred.onnx")

if not MODEL_PATH.exists():
    print("=" * 60)
    print("❌ ONNX Model not found!")
    print("=" * 60)
    print(f"\nThe wake word model was not found at: {MODEL_PATH}")
    print("\nPlease train and export the model by running:")
    print("  python tools/3_train.py --epochs 100 --export-onnx")
    print("\nThis will:")
    print("  1. Train the model on your wake word samples")
    print("  2. Save PyTorch model to models/alfred_pytorch.pt")
    print("  3. Export optimized ONNX model to models/alfred.onnx")
    print("\nNote: The ONNX model is used for faster, lightweight inference!")
    print("=" * 60)
    sys.exit(1)

# =============================
#     AUDIO DEVICE SETUP
# =============================
print("\nSelect your audio input device:")
devices = [d for d in sd.query_devices() if d['max_input_channels'] > 0]
for i, dev in enumerate(devices):
    print(f"{i}: {dev['name']}")

device_index = int(input("\nEnter device number to use: "))
chosen_device = devices[device_index]
print(f"🎤 Using input device #{device_index}")

# Load wake word model
wakeword_model = load_model_with_progress(str(MODEL_PATH))

# =============================
#       CONFIGURATION
# =============================
duration = 1.5        # seconds for wake word listening
fs = 48000            # hardware sample rate (what device supports)
target_sr = 16000     # model sample rate (what training used)
wake_word_name = "Alfred"
wake_threshold = args.threshold  # from command line args
audio_file = "last_command.wav"

# =============================
#     AUDIO HELPERS
# =============================
def record_audio(duration=1.5, rate=48000):
    """Record audio at device's native sample rate"""
    recording = sd.rec(int(duration * rate),
                       samplerate=rate,
                       channels=1,
                       device=device_index,
                       dtype='float32')
    sd.wait()
    return recording.flatten()

def extract_features(audio, sr=48000, target_sr=16000):
    """Extract MFCC features matching training pipeline"""
    # Resample to 16kHz (matching training data)
    if sr != target_sr:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)

    # Extract 13 MFCCs (matching training)
    mfcc = librosa.feature.mfcc(y=audio, sr=target_sr, n_mfcc=13)
    mfcc = mfcc.T  # (time, features)

    # Pad or truncate to 29 frames (matching training)
    if len(mfcc) < 29:
        mfcc = np.pad(mfcc, ((0, 29 - len(mfcc)), (0, 0)), mode='constant')
    else:
        mfcc = mfcc[:29]

    # Normalize (matching training)
    mfcc = (mfcc - np.mean(mfcc)) / (np.std(mfcc) + 1e-8)

    # Return as numpy array with batch dimension for ONNX
    return np.expand_dims(mfcc, axis=0).astype(np.float32)  # (1, 29, 13)

def record_until_silence(rate=48000, silence_threshold=0.01, silence_duration=1.5, max_duration=10, device=None):
    """Record audio until user stops talking"""
    chunk_duration = 0.5  # seconds per chunk
    chunk_samples = int(chunk_duration * rate)

    print("🎤 Listening... (speak now)")

    audio_chunks = []
    silent_chunks = 0
    silence_chunks_needed = int(silence_duration / chunk_duration)
    max_chunks = int(max_duration / chunk_duration)

    for _ in range(max_chunks):
        # Record chunk
        chunk = sd.rec(chunk_samples, samplerate=rate, channels=1, device=device, dtype='float32')
        sd.wait()
        chunk = chunk.flatten()
        audio_chunks.append(chunk)

        # Calculate energy (RMS)
        energy = np.sqrt(np.mean(chunk**2))

        # Check if silent
        if energy < silence_threshold:
            silent_chunks += 1
            if silent_chunks >= silence_chunks_needed:
                print("🔇 Silence detected, stopping...")
                break
        else:
            silent_chunks = 0  # Reset counter if speech detected

    # Concatenate all chunks
    full_audio = np.concatenate(audio_chunks)
    return full_audio

# =============================
#    WHISPER TRANSCRIPTION
# =============================
def transcribe_with_whisper_local(file_path, model='base'):
    """Transcribe using local Whisper CLI"""
    try:
        result = subprocess.run(
            ['whisper', file_path, '--model', model, '--output_format', 'txt'],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            # Whisper saves output as filename.txt
            txt_file = file_path.replace('.wav', '.txt')
            if os.path.exists(txt_file):
                with open(txt_file, 'r') as f:
                    transcription = f.read().strip()
                os.remove(txt_file)  # Clean up
                return transcription
        else:
            print("⚠ Whisper local error:", result.stderr)
            return ""
    except FileNotFoundError:
        print("❌ Whisper not found. Install with: pip install openai-whisper")
        return ""
    except Exception as e:
        print("❌ Error calling local Whisper:", e)
        return ""

def transcribe_with_whisper_docker(file_path, api_url):
    """Transcribe using Docker Whisper API"""
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(api_url, files=files, timeout=60)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            return data.get("transcription", "")
        else:
            print("⚠ Whisper Docker returned error:", data)
            return ""
    except Exception as e:
        print("❌ Error calling Whisper Docker API:", e)
        return ""

def transcribe(file_path):
    """Main transcription function that routes to local or docker"""
    if args.whisper == 'local':
        return transcribe_with_whisper_local(file_path, model=args.whisper_model)
    else:
        api_url = f"http://{args.docker_ip}/audio"
        return transcribe_with_whisper_docker(file_path, api_url)

# =============================
#   VOLUME INITIALIZATION
# =============================
# Set startup volume
startup_volume = max(0, min(100, args.volume))  # Clamp to 0-100
volume_control.set_volume(startup_volume)
print(f"🔊 Volume set to {startup_volume}%")

# =============================
#   RESPONSE MODEL SETUP
# =============================
print(f"\n📝 Response mode: {RESPONSE_MODE}")
if RESPONSE_MODE == "ai":
    print(f"   AI Model: {AI_MODEL}")
    print("   Preloading response model...")
    from functions.response_generator import get_generator
    response_gen = get_generator()
    response_gen.preload_model()
else:
    print("   Using instant template responses")

# =============================
#        MAIN LOOP
# =============================
print("\n" + "=" * 60)
print(f"🤖 {wake_word_name} is ready!")
print("=" * 60)
print(f"Configuration:")
print(f"  Wake threshold: {wake_threshold}")
print(f"  Whisper mode: {args.whisper}")
if args.whisper == 'docker':
    print(f"  Docker API: http://{args.docker_ip}/audio")
else:
    print(f"  Whisper model: {args.whisper_model}")
print(f"  Silence threshold: {args.silence_threshold} (audio energy level)")
print(f"  Silence duration: {args.silence_duration}s (continuous silence to stop)")
print(f"  TTS: {'Enabled (US English + Italian)' if tts_engine else 'Disabled'}")
print(f"  Startup volume: {startup_volume}%")
print(f"\nSay 'Hey {wake_word_name}' to wake me up.")

# Welcome message in Italian
speak(f"Ciao! Sono {wake_word_name}, pronto ad aiutarti.", language="italian")

print("=" * 60 + "\n")

while True:
    try:
        # Record audio for wake word detection (48kHz, then resampled to 16kHz)
        audio = record_audio(duration, fs)
        features = extract_features(audio, sr=fs, target_sr=target_sr)
        del audio
        gc.collect()

        # Predict with ONNX model
        input_name = wakeword_model.get_inputs()[0].name
        output_name = wakeword_model.get_outputs()[0].name
        prediction = wakeword_model.run([output_name], {input_name: features})
        wake_prob = float(prediction[0][0][0])  # ONNX returns [[[ value ]]]

        del features
        del prediction
        gc.collect()

        print(f"Wake word probability: {wake_prob:.3f}")

        if wake_prob > wake_threshold:
            print("🚀 Wake word detected! Listening for command...")
            speak("Yes sir, I'm listening.", language="english")

            # Record command until silence (48kHz for Whisper)
            command_audio = record_until_silence(
                rate=fs,
                silence_threshold=args.silence_threshold,
                silence_duration=args.silence_duration,
                device=device_index
            )
            write(audio_file, fs, (command_audio * 32767).astype(np.int16))
            del command_audio
            gc.collect()

            print("🎧 Transcribing command...")
            command = transcribe(audio_file)
            print(f"🗣 You said: {command}")

            # Parse intent
            if command:
                intent_result = parse_intent(command)
                print(f"\n📋 Intent parsed:")
                print(f"   Intent: {intent_result['intent']}")
                print(f"   Language: {intent_result['language']}")
                print(f"   Confidence: {intent_result['confidence']}")
                if intent_result['parameters']:
                    print(f"   Parameters: {intent_result['parameters']}")
                print(f"   Requires PIN: {intent_result['requires_pin']}")
                print()

                # Get detected language from intent
                detected_lang = intent_result['language']
                lang_map = {'en': 'english', 'it': 'italian'}
                speak_lang = lang_map.get(detected_lang, 'english')

                # Execute the intent
                intent = intent_result['intent']
                params = intent_result['parameters']

                # Volume control intents
                if intent == 'volume_set':
                    level = params.get('level', 50)
                    volume_control.set_volume(level)
                    response = generate_response(intent, str(level), language=detected_lang, parameters=params)
                    speak(response, language=speak_lang)

                elif intent == 'volume_up':
                    amount = params.get('amount', 10)
                    new_vol = volume_control.increase_volume(amount)
                    response = generate_response(intent, str(new_vol), language=detected_lang, parameters=params)
                    speak(response, language=speak_lang)

                elif intent == 'volume_down':
                    amount = params.get('amount', 10)
                    new_vol = volume_control.decrease_volume(amount)
                    response = generate_response(intent, str(new_vol), language=detected_lang, parameters=params)
                    speak(response, language=speak_lang)

                # Time & Date intents
                elif intent == 'time':
                    time_data = time_date.get_time()
                    if time_data["success"]:
                        response = generate_response(intent, time_data["time"], language=detected_lang, parameters=time_data)
                        speak(response, language=speak_lang)
                    else:
                        speak("I'm afraid I cannot tell the time at the moment, sir.", language=speak_lang)

                elif intent == 'date':
                    date_data = time_date.get_date()
                    if date_data["success"]:
                        result = f"{date_data['weekday']}, {date_data['date_formatted']}"
                        response = generate_response(intent, result, language=detected_lang, parameters=date_data)
                        speak(response, language=speak_lang)
                    else:
                        speak("I'm afraid I cannot tell the date at the moment, sir.", language=speak_lang)

                # Weather intents
                elif intent == 'weather':
                    location = params.get('location', None)  # None will use default from config
                    weather_data = weather.get_weather(detected_lang, location)  # Pass language code (en/it)
                    if weather_data["success"]:
                        # Let template system handle formatting - just provide basic result
                        result = f"{weather_data['temperature_c']}C, {weather_data['description']}"
                        response = generate_response(intent, result, language=detected_lang, parameters=weather_data)
                        speak(response, language=speak_lang)
                    else:
                        loc_name = location if location else "your location"
                        speak(f"I'm afraid I cannot fetch the weather for {loc_name}, sir.", language=speak_lang)

                # System status intents
                elif intent == 'system_status':
                    status_data = system.get_system_status()
                    if status_data["success"]:
                        cpu = status_data['cpu']
                        memory = status_data['memory']
                        temp = status_data['temperature']
                        # Let template system handle formatting - just provide basic result
                        result = f"CPU {cpu['usage_percent']}%, Memory {memory['usage_percent']}%"
                        if temp['success']:
                            result += f", Temp {temp['celsius']}C"
                        response = generate_response(intent, result, language=detected_lang, parameters=status_data)
                        speak(response, language=speak_lang)
                    else:
                        speak("I'm afraid I cannot check the system status, sir.", language=speak_lang)

                # General intents
                elif intent == 'joke':
                    joke_data = general.tell_joke(language=detected_lang)
                    if joke_data["success"]:
                        speak(joke_data['joke'], language=speak_lang)
                    else:
                        speak("I'm afraid my joke collection is unavailable at the moment, sir.", language=speak_lang)

                elif intent == 'calculate':
                    expression = params.get('expression', '')
                    if expression:
                        calc_data = general.calculate(expression)
                        if calc_data["success"]:
                            response = generate_response(intent, str(calc_data['result']), language=detected_lang, parameters=calc_data)
                            speak(response, language=speak_lang)
                        else:
                            speak(f"I'm afraid I cannot calculate that, sir. {calc_data['error']}", language=speak_lang)
                    else:
                        speak("I need an expression to calculate, sir.", language=speak_lang)

                # Generic acknowledgment for other intents
                elif intent != 'general_chat':
                    if speak_lang == 'italian':
                        speak(f"Capito signore, richiesta {intent} ricevuta.", language="italian")
                    else:
                        speak(f"Understood sir, {intent} request received.", language="english")

            if os.path.exists(audio_file):
                os.remove(audio_file)

            print("Listening again...\n")

    except KeyboardInterrupt:
        print("\n🛑 Exiting gracefully.")
        speak("Goodbye sir, until next time.", language="english")
        break
