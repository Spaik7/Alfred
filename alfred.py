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

args = parser.parse_args()

# =============================
#        SPEECH OUTPUT
# =============================
def speak(text):
    print(f"[TTS skipped] -> {text}")
    pass

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
print(f"\nSay 'Hey {wake_word_name}' to wake me up.")
print(f"[TTS skipped] -> Ciao! Sono {wake_word_name}, pronto ad aiutarti.")
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
            print("[TTS skipped] -> Yes sir, what is your command?")

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
            if command:
                print(f"[TTS skipped] -> You said: {command}")

            if os.path.exists(audio_file):
                os.remove(audio_file)

            print("Listening again...\n")

    except KeyboardInterrupt:
        print("\n🛑 Exiting gracefully.")
        break
