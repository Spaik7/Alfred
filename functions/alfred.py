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
from functions.ssh_helper import check_mail, get_recent_emails, get_calendar_events_today, get_calendar_events_yesterday, get_calendar_events_tomorrow, get_calendar_events_specific
from functions.function import (
    generate_response,
    load_model_with_progress,
    record_audio,
    extract_features,
    record_until_silence,
    transcribe
)
from config import RESPONSE_MODE, AI_MODEL, FINANCE_WATCHLIST, OLLAMA_HOST

# Phase 1.2: Infrastructure components
from functions.logger import get_logger
from functions.context_manager import get_context_manager
from functions.error_handler import ErrorHandler
from functions.response_templates import generate_template_response
from functions.complex_query_parser import get_complex_parser
from functions.simple_concatenation_parser import get_simple_concatenation_parser

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
    default=0.998,
    help='Wake word detection threshold 0-1 (default: 0.998, lower = more sensitive)'
)
parser.add_argument(
    '-s', '--silence-threshold',
    type=float,
    default=3,
    help='Silence detection threshold for voice activity detection. This is the RMS energy level below which audio is considered silence. Range: 0.001-0.1. Lower values (e.g., 0.005) detect silence more aggressively, stopping recording sooner. Higher values (e.g., 0.05) require louder silence, useful in noisy environments. (default: 3)'
)
parser.add_argument(
    '-st', '--silence-duration',
    type=float,
    default=5.0,
    help='How many seconds of continuous silence before stopping recording. Increase this if your speech has long pauses. Range: 0.5-5.0 seconds. (default: 5.0)'
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
#  PHASE 1.2 INFRASTRUCTURE
# =============================
print("Initializing Alfred infrastructure...")

# Initialize logger
logger = get_logger(log_dir="logs", log_level="INFO")
logger.info("Alfred infrastructure initialization started")

# Initialize context manager
context = get_context_manager(timeout=300, max_history=10, logger=logger)
logger.info("Context manager initialized (5 minute timeout, 10 turn history)")

# Initialize error handler
error_handler = ErrorHandler(logger=logger)
logger.info("Error handler initialized")

# Initialize complex query parser
complex_parser = get_complex_parser(ollama_host=OLLAMA_HOST, model="llama3.2")
logger.info("Complex query parser initialized")

# Initialize simple concatenation parser (regex-based, no LLM needed)
simple_concat_parser = get_simple_concatenation_parser()
logger.info("Simple concatenation parser initialized")

print("✅ Infrastructure ready (logging, context, error handling, complex queries)!")

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
            logger.log_error("TTS_ERROR", str(e))
    else:
        print("   [TTS disabled]")

    return text  # Return for context tracking and logging


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

# Log startup configuration
config_dict = {
    "wake_threshold": wake_threshold,
    "whisper_mode": args.whisper,
    "whisper_model": args.whisper_model if args.whisper == 'local' else f"docker@{args.docker_ip}",
    "silence_threshold": args.silence_threshold,
    "silence_duration": args.silence_duration,
    "tts_enabled": tts_engine is not None,
    "startup_volume": startup_volume,
    "response_mode": RESPONSE_MODE,
}
logger.log_startup(config_dict)

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
                # Use context manager to resolve pronouns and follow-ups
                resolved_command, additional_params = context.handle_follow_up(command, "")

                # Check for concatenated queries using simple regex parser
                # This is more reliable than trying to get Ollama to parse
                detected_lang_temp = 'it' if any(word in resolved_command.lower() for word in ['che', 'sono', 'è']) else 'en'
                has_concatenation = simple_concat_parser.has_concatenation(resolved_command, detected_lang_temp)

                intent_result = parse_intent(resolved_command)

                # Merge additional params from context
                intent_result['parameters'].update(additional_params)

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

                # Check if this is a complex/concatenated query that needs Ollama analysis
                intent = intent_result['intent']
                params = intent_result['parameters']
                confidence = intent_result['confidence']

                # Handle concatenated queries using simple regex splitting
                if has_concatenation:
                    print("🔗 Concatenated query detected (multiple intents in one sentence)")
                    sub_queries = simple_concat_parser.split_query(resolved_command, detected_lang)
                    print(f"   📝 Split into {len(sub_queries)} parts:")
                    for i, sq in enumerate(sub_queries, 1):
                        print(f"      {i}. \"{sq}\"")

                    # Parse each sub-query separately and execute
                    # For now, just execute the first one (future: execute all and combine)
                    if len(sub_queries) > 1:
                        print(f"   ⚡ Processing first query: \"{sub_queries[0]}\"")
                        # Re-parse the first sub-query
                        first_result = parse_intent(sub_queries[0])
                        intent = first_result['intent']
                        params = first_result['parameters']
                        print(f"   → Detected intent: {intent}")

                # Check for complex queries (not concatenated, but complex like "what should I wear")
                elif complex_parser.is_complex_query(intent, resolved_command, confidence):
                    print("🤔 Complex query detected - analyzing with Ollama...")
                    complex_result = complex_parser.parse_complex_query(resolved_command, detected_lang)

                    if complex_result and complex_result.get('type') == 'complex':
                        sub_intents = complex_result.get('intents', [])
                        print(f"   ✅ Identified {len(sub_intents)} sub-intents: {sub_intents}")
                        print(f"   Reason: {complex_result.get('reason')}")

                        if sub_intents:
                            intent = sub_intents[0]
                            print(f"   ⚡ Executing primary intent: {intent}")
                    else:
                        print("   ℹ️  Ollama couldn't break it down - treating as general chat")

                # Execute the intent

                # Track data for logging - collect everything for log_conversation_turn()
                user_input = command
                parser_output = {
                    'intent': intent_result['intent'],
                    'language': intent_result['language'],
                    'confidence': intent_result['confidence'],
                    'parameters': intent_result['parameters']
                }
                work_output = {}  # Will be populated by API/function calls
                ai_response = ""  # Raw AI response (if used)
                final_output = ""  # What gets spoken to user

                # Track response for context
                response_text = ""
                success = False

                # Volume control intents (use advanced templates)
                if intent == 'volume_set':
                    level = params.get('level', 50)
                    volume_control.set_volume(level)
                    work_output = {'level': level, 'success': True}
                    ai_response = "Template response (with personality)"
                    final_output = speak(generate_template_response(intent, str(level), detected_lang, {'level': level}), language=speak_lang)
                    response_text = final_output
                    success = True

                elif intent == 'volume_up':
                    amount = params.get('amount', 10)
                    new_vol = volume_control.increase_volume(amount)
                    work_output = {'new_volume': new_vol, 'amount': amount, 'success': True}
                    ai_response = "Template response (with personality)"
                    final_output = speak(generate_template_response(intent, str(new_vol), detected_lang, {'result': new_vol}), language=speak_lang)
                    response_text = final_output
                    success = True

                elif intent == 'volume_down':
                    amount = params.get('amount', 10)
                    new_vol = volume_control.decrease_volume(amount)
                    work_output = {'new_volume': new_vol, 'amount': amount, 'success': True}
                    ai_response = "Template response (with personality)"
                    final_output = speak(generate_template_response(intent, str(new_vol), detected_lang, {'result': new_vol}), language=speak_lang)
                    response_text = final_output
                    success = True

                # Time & Date intents (use advanced templates)
                elif intent == 'time':
                    time_data = time_date.get_time()
                    work_output = time_data
                    if time_data["success"]:
                        ai_response = "Template response (with personality)"
                        final_output = speak(generate_template_response(intent, time_data["time"], detected_lang, {'time': time_data["time"]}), language=speak_lang)
                        response_text = final_output
                        success = True
                    else:
                        final_output = speak("I'm afraid I cannot tell the time at the moment, sir.", language=speak_lang)
                        response_text = final_output
                        success = False

                elif intent == 'date':
                    date_data = time_date.get_date()
                    work_output = date_data
                    if date_data["success"]:
                        result = f"{date_data['weekday']}, {date_data['date_formatted']}"
                        ai_response = "Template response (with personality)"
                        final_output = speak(generate_template_response(intent, result, detected_lang, date_data), language=speak_lang)
                        response_text = final_output
                        success = True
                    else:
                        final_output = speak("I'm afraid I cannot tell the date at the moment, sir.", language=speak_lang)
                        response_text = final_output
                        success = False

                # Weather intents (use AI with minimal data)
                elif intent == 'weather':
                    location = params.get('location', None)  # None will use default from config
                    weather_data = weather.get_weather(detected_lang, location)  # Pass language code (en/it)
                    work_output = weather_data
                    if weather_data["success"]:
                        # Pass only essential information to AI
                        essential_params = {
                            'temperature_c': weather_data['temperature_c'],
                            'description': weather_data['description'],
                            'location': weather_data['location']
                        }
                        result = f"{weather_data['temperature_c']}C, {weather_data['description']}"
                        ai_response = generate_response(intent, result, language=detected_lang, parameters=essential_params)
                        final_output = speak(ai_response, language=speak_lang)
                        response_text = final_output
                        success = True
                    else:
                        loc_name = location if location else "your location"
                        final_output = speak(f"I'm afraid I cannot fetch the weather for {loc_name}, sir.", language=speak_lang)
                        response_text = final_output
                        success = False

                # System status intents (use advanced templates with contextual comments)
                elif intent == 'system_status':
                    status_data = system.get_system_status()
                    work_output = status_data
                    if status_data["success"]:
                        cpu = status_data['cpu']
                        memory = status_data['memory']
                        temp = status_data['temperature']
                        result = "OK"
                        ai_response = "Template response (with personality + contextual comments)"
                        final_output = speak(generate_template_response(intent, result, detected_lang, status_data), language=speak_lang)
                        response_text = final_output
                        success = True
                    else:
                        final_output = speak("I'm afraid I cannot check the system status, sir.", language=speak_lang)
                        response_text = final_output
                        success = False

                # General intents (use advanced templates)
                elif intent == 'joke':
                    joke_data = general.tell_joke(language=detected_lang)
                    work_output = joke_data
                    if joke_data["success"]:
                        # Joke: template says the joke directly
                        ai_response = "Template response (with personality)"
                        final_output = speak(joke_data['joke'], language=speak_lang)
                        response_text = final_output
                        success = True
                    else:
                        final_output = speak("I'm afraid my joke collection is unavailable at the moment, sir.", language=speak_lang)
                        response_text = final_output
                        success = False

                elif intent == 'calculate':
                    expression = params.get('expression', '')
                    if expression:
                        calc_data = general.calculate(expression)
                        work_output = calc_data
                        if calc_data["success"]:
                            ai_response = "Template response (with personality)"
                            final_output = speak(generate_template_response(intent, str(calc_data['result']), detected_lang, {'expression': expression, 'result': calc_data['result']}), language=speak_lang)
                            response_text = final_output
                            success = True
                        else:
                            final_output = speak(f"I'm afraid I cannot calculate that, sir. {calc_data['error']}", language=speak_lang)
                            response_text = final_output
                            success = False
                    else:
                        work_output = {'error': 'No expression provided', 'success': False}
                        final_output = speak("I need an expression to calculate, sir.", language=speak_lang)
                        response_text = final_output
                        success = False

                # News intents
                elif intent == 'news':
                    # Get multi-country headlines (Italy + US by default)
                    news_data = news.get_multi_country_headlines(count_per_country=3)
                    work_output = news_data
                    if news_data["success"] and news_data["articles"]:
                        # Speak summary
                        total = len(news_data["articles"])
                        outputs = []
                        if speak_lang == 'italian':
                            outputs.append(speak(f"Ecco le ultime {total} notizie, signore:", language="italian"))
                        else:
                            outputs.append(speak(f"Here are the latest {total} headlines, sir:", language="english"))

                        # Read first 5 headlines
                        for i, article in enumerate(news_data["articles"][:5], 1):
                            country = article.get('country', '')
                            title = article['title']
                            if country:
                                outputs.append(speak(f"{country}: {title}", language=speak_lang))
                            else:
                                outputs.append(speak(f"{i}. {title}", language=speak_lang))

                        final_output = " | ".join(outputs)
                        ai_response = "News headlines"  # No AI generation for news
                        response_text = final_output
                        success = True
                    else:
                        final_output = speak("I'm afraid I cannot fetch the news at the moment, sir.", language=speak_lang)
                        response_text = final_output
                        success = False

                # Finance intents
                elif intent == 'finance' or intent == 'finance_watchlist':
                    # Get full watchlist summary
                    watchlist_data = finance.get_watchlist_summary(FINANCE_WATCHLIST)
                    work_output = watchlist_data
                    if watchlist_data["success"]:
                        outputs = []
                        # Speak stocks
                        if watchlist_data["stocks"]:
                            if speak_lang == 'italian':
                                outputs.append(speak("Azioni:", language="italian"))
                            else:
                                outputs.append(speak("Stocks:", language="english"))

                            for stock in watchlist_data["stocks"]:
                                change_dir = "up" if stock["change"] > 0 else "down"
                                outputs.append(speak(f"{stock['name']}: ${stock['price']}, {change_dir} {abs(stock['change_percent'])}%", language=speak_lang))

                        # Speak crypto
                        if watchlist_data["crypto"]:
                            if speak_lang == 'italian':
                                outputs.append(speak("Criptovalute:", language="italian"))
                            else:
                                outputs.append(speak("Crypto:", language="english"))

                            for crypto in watchlist_data["crypto"]:
                                change_dir = "up" if crypto["change_24h"] > 0 else "down"
                                outputs.append(speak(f"{crypto['name']}: ${crypto['price_usd']}, {change_dir} {abs(crypto['change_24h'])}%", language=speak_lang))

                        # Speak forex
                        if watchlist_data["forex"]:
                            if speak_lang == 'italian':
                                outputs.append(speak("Cambi:", language="italian"))
                            else:
                                outputs.append(speak("Forex:", language="english"))

                            for pair in watchlist_data["forex"]:
                                outputs.append(speak(f"{pair['from']}/{pair['to']}: {pair['rate']}", language=speak_lang))

                        final_output = " | ".join(outputs)
                        ai_response = "Financial watchlist"  # No AI generation for finance
                        response_text = final_output
                        success = True
                    else:
                        final_output = speak("I'm afraid I cannot fetch financial data at the moment, sir.", language=speak_lang)
                        response_text = final_output
                        success = False

                # Recipe intents
                elif intent == 'recipe_search':
                    query = params.get('query', '')
                    if query:
                        recipe_data = food.search_recipes(query, count=3)
                        work_output = recipe_data
                        if recipe_data["success"] and recipe_data["recipes"]:
                            total = len(recipe_data["recipes"])
                            outputs = []
                            if speak_lang == 'italian':
                                outputs.append(speak(f"Ho trovato {total} ricette per {query}, signore:", language="italian"))
                            else:
                                outputs.append(speak(f"I found {total} recipes for {query}, sir:", language="english"))

                            for recipe in recipe_data["recipes"]:
                                outputs.append(speak(f"{recipe['name']} from {recipe['area']}", language=speak_lang))

                            final_output = " | ".join(outputs)
                            ai_response = f"Recipe search: {query}"
                            response_text = final_output
                            success = True
                        else:
                            final_output = speak(f"I'm afraid I couldn't find recipes for {query}, sir.", language=speak_lang)
                            response_text = final_output
                            success = False
                    else:
                        work_output = {'error': 'No query provided', 'success': False}
                        final_output = speak("I need a recipe name or ingredient, sir.", language=speak_lang)
                        response_text = final_output
                        success = False

                elif intent == 'recipe_random':
                    recipe_data = food.get_random_recipe()
                    work_output = recipe_data
                    if recipe_data["success"]:
                        recipe = recipe_data['recipe']
                        outputs = []
                        if speak_lang == 'italian':
                            outputs.append(speak(f"Suggerisco {recipe['name']}, un piatto {recipe['area']}, signore.", language="italian"))
                        else:
                            outputs.append(speak(f"I suggest {recipe['name']}, a {recipe['area']} dish, sir.", language="english"))

                        # Optionally speak category
                        if recipe.get('category'):
                            outputs.append(speak(f"Category: {recipe['category']}", language=speak_lang))

                        final_output = " | ".join(outputs)
                        ai_response = "Random recipe suggestion"
                        response_text = final_output
                        success = True
                    else:
                        final_output = speak("I'm afraid I cannot get a recipe suggestion at the moment, sir.", language=speak_lang)
                        response_text = final_output
                        success = False

                # Transport intents
                elif intent == 'transport_car':
                    destination = params.get('destination', '')
                    arrival_time = params.get('arrival_time', None)

                    if destination:
                        traffic_data = transport.get_traffic_status(None, destination, arrival_time)
                        work_output = traffic_data
                        if traffic_data["success"]:
                            travel_duration = traffic_data['duration_text']
                            traffic = traffic_data['delay_minutes']
                            departure_time = traffic_data.get('departure_time')
                            outputs = []

                            # If arrival time was specified, tell when to leave
                            if arrival_time and departure_time:
                                if speak_lang == 'italian':
                                    outputs.append(speak(f"Per arrivare a {destination} alle {arrival_time}, devi partire alle {departure_time}, signore.", language="italian"))
                                else:
                                    outputs.append(speak(f"To arrive at {destination} by {arrival_time}, you need to leave at {departure_time}, sir.", language="english"))
                            else:
                                if speak_lang == 'italian':
                                    outputs.append(speak(f"Per arrivare a {destination} ci vogliono {travel_duration}, signore.", language="italian"))
                                else:
                                    outputs.append(speak(f"It will take {travel_duration} to get to {destination}, sir.", language="english"))

                            # Mention traffic if significant
                            if traffic > 5:
                                if speak_lang == 'italian':
                                    outputs.append(speak(f"C'è traffico, {traffic} minuti di ritardo.", language="italian"))
                                else:
                                    outputs.append(speak(f"There's traffic, {traffic} minutes delay.", language="english"))

                            final_output = " | ".join(outputs)
                            ai_response = "Traffic directions"
                            response_text = final_output
                            success = True
                        else:
                            final_output = speak(f"I'm afraid I cannot get directions to {destination}, sir.", language=speak_lang)
                            response_text = final_output
                            success = False
                    else:
                        work_output = {'error': 'No destination provided', 'success': False}
                        final_output = speak("I need a destination, sir.", language=speak_lang)
                        response_text = final_output
                        success = False

                elif intent == 'transport_public':
                    destination = params.get('destination', '')
                    arrival_time = params.get('arrival_time', None)

                    if destination:
                        transit_data = transport.get_public_transit(None, destination, arrival_time)
                        work_output = transit_data
                        if transit_data["success"]:
                            travel_duration = transit_data['duration']
                            transit_steps = transit_data['transit_steps']
                            departure_time = transit_data.get('departure_time')
                            outputs = []

                            # If arrival time was specified, tell when to leave
                            if arrival_time and departure_time:
                                if speak_lang == 'italian':
                                    outputs.append(speak(f"Per arrivare a {destination} alle {arrival_time}, devi partire alle {departure_time}, signore.", language="italian"))
                                else:
                                    outputs.append(speak(f"To arrive at {destination} by {arrival_time}, you need to leave at {departure_time}, sir.", language="english"))
                            else:
                                if speak_lang == 'italian':
                                    outputs.append(speak(f"Per arrivare a {destination} con i mezzi pubblici ci vogliono {travel_duration}, signore.", language="italian"))
                                else:
                                    outputs.append(speak(f"To get to {destination} by public transport takes {travel_duration}, sir.", language="english"))

                            # Count transfers
                            if len(transit_steps) > 1:
                                transfers = len(transit_steps) - 1
                                if speak_lang == 'italian':
                                    outputs.append(speak(f"Devi fare {transfers} cambi.", language="italian"))
                                else:
                                    outputs.append(speak(f"You need to make {transfers} transfers.", language="english"))

                            # Speak first transit line
                            if transit_steps:
                                first_step = transit_steps[0]
                                line = first_step.get('line', 'Unknown')
                                if speak_lang == 'italian':
                                    outputs.append(speak(f"Prendi la linea {line}.", language="italian"))
                                else:
                                    outputs.append(speak(f"Take line {line}.", language="english"))

                            final_output = " | ".join(outputs)
                            ai_response = "Public transport directions"
                            response_text = final_output
                            success = True
                        else:
                            final_output = speak(f"I'm afraid I cannot get public transport directions to {destination}, sir.", language=speak_lang)
                            response_text = final_output
                            success = False
                    else:
                        work_output = {'error': 'No destination provided', 'success': False}
                        final_output = speak("I need a destination, sir.", language=speak_lang)
                        response_text = final_output
                        success = False

                # Mac Integration - Email & Calendar (Phase 2)
                elif intent == 'email_check':
                    # Check unread mail count via SSH to Mac
                    mail_result = check_mail()
                    work_output = mail_result

                    if mail_result.get('success'):
                        unread_count = mail_result.get('unread_count', 0)
                        # Use template for fast response
                        ai_response = "Template response (with personality)"
                        final_output = speak(generate_template_response(
                            'email_check',
                            str(unread_count),
                            detected_lang,
                            {'unread_count': unread_count}
                        ), language=speak_lang)
                        response_text = final_output
                        success = True
                    else:
                        error_msg = mail_result.get('error', 'Unknown error')
                        logger.error(f"Mail check failed: {error_msg}")
                        if speak_lang == 'italian':
                            final_output = speak("Mi dispiace signore, non riesco ad accedere alla posta.", language="italian")
                        else:
                            final_output = speak("Apologies sir, I cannot access the mail at the moment.", language="english")
                        response_text = final_output
                        success = False

                elif intent == 'email_list':
                    # Get recent emails via SSH to Mac
                    emails_result = get_recent_emails(count=5)
                    work_output = emails_result

                    if emails_result.get('success'):
                        emails = emails_result.get('emails', [])
                        count = emails_result.get('count', 0)

                        if count == 0:
                            if speak_lang == 'italian':
                                final_output = speak("Non ci sono email nella casella di posta, signore.", language="italian")
                            else:
                                final_output = speak("There are no emails in the inbox, sir.", language="english")
                            response_text = final_output
                            success = True
                        else:
                            # Use template for fast, natural response
                            ai_response = "Template response (with personality)"
                            final_output = speak(generate_template_response(
                                'email_list',
                                str(count),
                                detected_lang,
                                {'count': count, 'emails': emails}
                            ), language=speak_lang)
                            response_text = final_output
                            success = True
                    else:
                        error_msg = emails_result.get('error', 'Unknown error')
                        logger.error(f"Email list failed: {error_msg}")
                        if speak_lang == 'italian':
                            final_output = speak("Mi dispiace signore, non riesco ad accedere alla posta.", language="italian")
                        else:
                            final_output = speak("Apologies sir, I cannot access the mail at the moment.", language="english")
                        response_text = final_output
                        success = False

                elif intent == 'calendar_today':
                    # Get today's calendar events via SSH to Mac
                    calendar_result = get_calendar_events_today()
                    work_output = calendar_result

                    if calendar_result.get('success'):
                        event_count = calendar_result.get('count', 0)
                        date_label = calendar_result.get('date', 'today')
                        # Use AI to generate natural response
                        ai_response = generate_response(
                            'calendar_today',
                            f"User has {event_count} events {date_label}",
                            language=detected_lang,
                            parameters={'count': event_count, 'date': date_label}
                        )
                        final_output = speak(ai_response, language=speak_lang)
                        response_text = final_output
                        success = True
                    else:
                        error_msg = calendar_result.get('error', 'Unknown error')
                        logger.error(f"Calendar check failed: {error_msg}")
                        if speak_lang == 'italian':
                            final_output = speak("Mi dispiace signore, non riesco ad accedere al calendario.", language="italian")
                        else:
                            final_output = speak("Apologies sir, I cannot access the calendar at the moment.", language="english")
                        response_text = final_output
                        success = False

                elif intent == 'calendar_yesterday':
                    # Get yesterday's calendar events via SSH to Mac
                    calendar_result = get_calendar_events_yesterday()
                    work_output = calendar_result

                    if calendar_result.get('success'):
                        event_count = calendar_result.get('count', 0)
                        date_label = calendar_result.get('date', 'yesterday')
                        # Use AI to generate natural response
                        ai_response = generate_response(
                            'calendar_yesterday',
                            f"User had {event_count} events {date_label}",
                            language=detected_lang,
                            parameters={'count': event_count, 'date': date_label}
                        )
                        final_output = speak(ai_response, language=speak_lang)
                        response_text = final_output
                        success = True
                    else:
                        error_msg = calendar_result.get('error', 'Unknown error')
                        logger.error(f"Calendar check failed: {error_msg}")
                        if speak_lang == 'italian':
                            final_output = speak("Mi dispiace signore, non riesco ad accedere al calendario.", language="italian")
                        else:
                            final_output = speak("Apologies sir, I cannot access the calendar at the moment.", language="english")
                        response_text = final_output
                        success = False

                elif intent == 'calendar_tomorrow':
                    # Get tomorrow's calendar events via SSH to Mac
                    calendar_result = get_calendar_events_tomorrow()
                    work_output = calendar_result

                    if calendar_result.get('success'):
                        event_count = calendar_result.get('count', 0)
                        date_label = calendar_result.get('date', 'tomorrow')
                        # Use AI to generate natural response
                        ai_response = generate_response(
                            'calendar_tomorrow',
                            f"User has {event_count} events {date_label}",
                            language=detected_lang,
                            parameters={'count': event_count, 'date': date_label}
                        )
                        final_output = speak(ai_response, language=speak_lang)
                        response_text = final_output
                        success = True
                    else:
                        error_msg = calendar_result.get('error', 'Unknown error')
                        logger.error(f"Calendar check failed: {error_msg}")
                        if speak_lang == 'italian':
                            final_output = speak("Mi dispiace signore, non riesco ad accedere al calendario.", language="italian")
                        else:
                            final_output = speak("Apologies sir, I cannot access the calendar at the moment.", language="english")
                        response_text = final_output
                        success = False

                elif intent == 'calendar_specific':
                    # Get events from a specific calendar by name
                    calendar_name = params.get('calendar_name', '').strip()

                    if calendar_name:
                        calendar_result = get_calendar_events_specific(calendar_name, date_offset=0)
                        work_output = calendar_result

                        if calendar_result.get('success') and calendar_result.get('found'):
                            event_count = calendar_result.get('count', 0)
                            actual_cal_name = calendar_result.get('calendar_name', calendar_name)
                            date_label = calendar_result.get('date', 'today')
                            # Use AI to generate natural response
                            ai_response = generate_response(
                                'calendar_specific',
                                f"User has {event_count} events {date_label} in {actual_cal_name} calendar",
                                language=detected_lang,
                                parameters={'count': event_count, 'calendar_name': actual_cal_name, 'date': date_label}
                            )
                            final_output = speak(ai_response, language=speak_lang)
                            response_text = final_output
                            success = True
                        elif not calendar_result.get('found'):
                            # Calendar not found
                            if speak_lang == 'italian':
                                final_output = speak(f"Mi dispiace signore, non ho trovato il calendario {calendar_name}.", language="italian")
                            else:
                                final_output = speak(f"Apologies sir, I could not find the {calendar_name} calendar.", language="english")
                            response_text = final_output
                            success = False
                        else:
                            error_msg = calendar_result.get('error', 'Unknown error')
                            logger.error(f"Calendar check failed: {error_msg}")
                            if speak_lang == 'italian':
                                final_output = speak("Mi dispiace signore, non riesco ad accedere al calendario.", language="italian")
                            else:
                                final_output = speak("Apologies sir, I cannot access the calendar at the moment.", language="english")
                            response_text = final_output
                            success = False
                    else:
                        # No calendar name provided
                        if speak_lang == 'italian':
                            final_output = speak("Mi dispiace signore, quale calendario vuole controllare?", language="italian")
                        else:
                            final_output = speak("Which calendar would you like me to check, sir?", language="english")
                        response_text = final_output
                        success = False

                # General chat fallback (use Ollama for conversational responses)
                elif intent == 'general_chat':
                    query = params.get('query', command)
                    work_output = {'query': query, 'success': True}

                    # Use Ollama to generate a conversational response
                    ai_response = generate_response('general_chat', query, language=detected_lang, parameters={'query': query})
                    final_output = speak(ai_response, language=speak_lang)
                    response_text = final_output
                    success = True

                # Generic acknowledgment for other intents
                elif intent != 'general_chat':
                    work_output = {'intent': intent, 'success': True}
                    if speak_lang == 'italian':
                        final_output = speak(f"Capito signore, richiesta {intent} ricevuta.", language="italian")
                    else:
                        final_output = speak(f"Understood sir, {intent} request received.", language="english")
                    ai_response = "Generic acknowledgment"
                    response_text = final_output
                    success = True

                # Log the complete conversation turn
                if not response_text:
                    # If no response was explicitly tracked, use fallback
                    response_text = f"Intent {intent} executed"
                    final_output = response_text
                    success = True

                # Log complete data flow: Input → Parser → Work → AI → Output
                logger.log_conversation_turn(
                    user_input=user_input,
                    parser_output=parser_output,
                    work_output=work_output,
                    ai_response=ai_response,
                    final_output=final_output
                )

                # Add conversation turn to context
                context.add_turn(
                    command=command,
                    intent=intent,
                    language=detected_lang,
                    parameters=params,
                    response=response_text,
                    success=success
                )

                logger.debug(f"Context updated: {len(context.history)} turns in history")

            if os.path.exists(audio_file):
                os.remove(audio_file)

            print("Listening again...\n")

    except KeyboardInterrupt:
        print("\n🛑 Exiting gracefully.")
        logger.log_shutdown("User interrupt (Ctrl+C)")
        speak("Goodbye sir, until next time.", language="english")
        break
    except Exception as e:
        logger.log_exception(e, "in main loop")
        print(f"\n❌ Unexpected error: {e}")
        print("Continuing...")
        continue
