import sounddevice as sd
import numpy as np
import os
import sys
import argparse
from pathlib import Path
from scipy.io.wavfile import write
import gc

from functions.intents import parse_intent
from functions.tts_engine import TTSEngine, Language
from functions import volume_control, time_date, system, general, weather, news, finance, food, transport
from functions.function import (
    generate_response,
    load_model_with_progress,
    record_audio,
    extract_features,
    record_until_silence,
    transcribe
)
from config import RESPONSE_MODE, AI_MODEL, FINANCE_WATCHLIST

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
        audio = record_audio(duration, fs, device_index)
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
            command = transcribe(audio_file, args.whisper, args.whisper_model, args.docker_ip)
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

                # News intents
                elif intent == 'news':
                    # Get multi-country headlines (Italy + US by default)
                    news_data = news.get_multi_country_headlines(count_per_country=3)
                    if news_data["success"] and news_data["articles"]:
                        # Speak summary
                        total = len(news_data["articles"])
                        if speak_lang == 'italian':
                            speak(f"Ecco le ultime {total} notizie, signore:", language="italian")
                        else:
                            speak(f"Here are the latest {total} headlines, sir:", language="english")

                        # Read first 5 headlines
                        for i, article in enumerate(news_data["articles"][:5], 1):
                            country = article.get('country', '')
                            title = article['title']
                            if country:
                                speak(f"{country}: {title}", language=speak_lang)
                            else:
                                speak(f"{i}. {title}", language=speak_lang)
                    else:
                        speak("I'm afraid I cannot fetch the news at the moment, sir.", language=speak_lang)

                # Finance intents
                elif intent == 'finance' or intent == 'finance_watchlist':
                    # Get full watchlist summary
                    watchlist_data = finance.get_watchlist_summary(FINANCE_WATCHLIST)
                    if watchlist_data["success"]:
                        # Speak stocks
                        if watchlist_data["stocks"]:
                            if speak_lang == 'italian':
                                speak("Azioni:", language="italian")
                            else:
                                speak("Stocks:", language="english")

                            for stock in watchlist_data["stocks"]:
                                change_dir = "up" if stock["change"] > 0 else "down"
                                speak(f"{stock['name']}: ${stock['price']}, {change_dir} {abs(stock['change_percent'])}%", language=speak_lang)

                        # Speak crypto
                        if watchlist_data["crypto"]:
                            if speak_lang == 'italian':
                                speak("Criptovalute:", language="italian")
                            else:
                                speak("Crypto:", language="english")

                            for crypto in watchlist_data["crypto"]:
                                change_dir = "up" if crypto["change_24h"] > 0 else "down"
                                speak(f"{crypto['name']}: ${crypto['price_usd']}, {change_dir} {abs(crypto['change_24h'])}%", language=speak_lang)

                        # Speak forex
                        if watchlist_data["forex"]:
                            if speak_lang == 'italian':
                                speak("Cambi:", language="italian")
                            else:
                                speak("Forex:", language="english")

                            for pair in watchlist_data["forex"]:
                                speak(f"{pair['from']}/{pair['to']}: {pair['rate']}", language=speak_lang)
                    else:
                        speak("I'm afraid I cannot fetch financial data at the moment, sir.", language=speak_lang)

                # Recipe intents
                elif intent == 'recipe_search':
                    query = params.get('query', '')
                    if query:
                        recipe_data = food.search_recipes(query, count=3)
                        if recipe_data["success"] and recipe_data["recipes"]:
                            total = len(recipe_data["recipes"])
                            if speak_lang == 'italian':
                                speak(f"Ho trovato {total} ricette per {query}, signore:", language="italian")
                            else:
                                speak(f"I found {total} recipes for {query}, sir:", language="english")

                            for recipe in recipe_data["recipes"]:
                                speak(f"{recipe['name']} from {recipe['area']}", language=speak_lang)
                        else:
                            speak(f"I'm afraid I couldn't find recipes for {query}, sir.", language=speak_lang)
                    else:
                        speak("I need a recipe name or ingredient, sir.", language=speak_lang)

                elif intent == 'recipe_random':
                    recipe_data = food.get_random_recipe()
                    if recipe_data["success"]:
                        recipe = recipe_data['recipe']
                        if speak_lang == 'italian':
                            speak(f"Suggerisco {recipe['name']}, un piatto {recipe['area']}, signore.", language="italian")
                        else:
                            speak(f"I suggest {recipe['name']}, a {recipe['area']} dish, sir.", language="english")

                        # Optionally speak category
                        if recipe.get('category'):
                            speak(f"Category: {recipe['category']}", language=speak_lang)
                    else:
                        speak("I'm afraid I cannot get a recipe suggestion at the moment, sir.", language=speak_lang)

                # Transport intents
                elif intent == 'transport_car':
                    destination = params.get('destination', '')
                    arrival_time = params.get('arrival_time', None)

                    if destination:
                        traffic_data = transport.get_traffic_status(None, destination, arrival_time)
                        if traffic_data["success"]:
                            travel_duration = traffic_data['duration_text']
                            traffic = traffic_data['delay_minutes']
                            departure_time = traffic_data.get('departure_time')

                            # If arrival time was specified, tell when to leave
                            if arrival_time and departure_time:
                                if speak_lang == 'italian':
                                    speak(f"Per arrivare a {destination} alle {arrival_time}, devi partire alle {departure_time}, signore.", language="italian")
                                else:
                                    speak(f"To arrive at {destination} by {arrival_time}, you need to leave at {departure_time}, sir.", language="english")
                            else:
                                if speak_lang == 'italian':
                                    speak(f"Per arrivare a {destination} ci vogliono {travel_duration}, signore.", language="italian")
                                else:
                                    speak(f"It will take {travel_duration} to get to {destination}, sir.", language="english")

                            # Mention traffic if significant
                            if traffic > 5:
                                if speak_lang == 'italian':
                                    speak(f"C'è traffico, {traffic} minuti di ritardo.", language="italian")
                                else:
                                    speak(f"There's traffic, {traffic} minutes delay.", language="english")
                        else:
                            speak(f"I'm afraid I cannot get directions to {destination}, sir.", language=speak_lang)
                    else:
                        speak("I need a destination, sir.", language=speak_lang)

                elif intent == 'transport_public':
                    destination = params.get('destination', '')
                    arrival_time = params.get('arrival_time', None)

                    if destination:
                        transit_data = transport.get_public_transit(None, destination, arrival_time)
                        if transit_data["success"]:
                            travel_duration = transit_data['duration']
                            transit_steps = transit_data['transit_steps']
                            departure_time = transit_data.get('departure_time')

                            # If arrival time was specified, tell when to leave
                            if arrival_time and departure_time:
                                if speak_lang == 'italian':
                                    speak(f"Per arrivare a {destination} alle {arrival_time}, devi partire alle {departure_time}, signore.", language="italian")
                                else:
                                    speak(f"To arrive at {destination} by {arrival_time}, you need to leave at {departure_time}, sir.", language="english")
                            else:
                                if speak_lang == 'italian':
                                    speak(f"Per arrivare a {destination} con i mezzi pubblici ci vogliono {travel_duration}, signore.", language="italian")
                                else:
                                    speak(f"To get to {destination} by public transport takes {travel_duration}, sir.", language="english")

                            # Count transfers
                            if len(transit_steps) > 1:
                                transfers = len(transit_steps) - 1
                                if speak_lang == 'italian':
                                    speak(f"Devi fare {transfers} cambi.", language="italian")
                                else:
                                    speak(f"You need to make {transfers} transfers.", language="english")

                            # Speak first transit line
                            if transit_steps:
                                first_step = transit_steps[0]
                                line = first_step.get('line', 'Unknown')
                                if speak_lang == 'italian':
                                    speak(f"Prendi la linea {line}.", language="italian")
                                else:
                                    speak(f"Take line {line}.", language="english")
                        else:
                            speak(f"I'm afraid I cannot get public transport directions to {destination}, sir.", language=speak_lang)
                    else:
                        speak("I need a destination, sir.", language=speak_lang)

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
