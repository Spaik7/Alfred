import sounddevice as sd
import numpy as np
import librosa
import tensorflow as tf
import subprocess
import time
from tqdm import tqdm
from scipy.io.wavfile import write
import gc
import requests
import os

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
    print(f"Loading model '{path}' ...")
    with tqdm(total=100) as pbar:
        for i in range(10):
            time.sleep(0.05)
            pbar.update(10)
    model = tf.keras.models.load_model(path)
    print("✅ Model loaded successfully!")
    return model

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
wakeword_model = load_model_with_progress("WWD.h5")

# =============================
#       CONFIGURATION
# =============================
duration = 1.5        # seconds for wake word listening
fs = 48000            # sample rate
wake_word_name = "Alfred"
wake_threshold = 0.9  # sensitivity threshold
audio_file = "last_command.wav"

# =============================
#     AUDIO HELPERS
# =============================
def record_audio(duration=1.5, rate=48000):
    recording = sd.rec(int(duration * rate),
                       samplerate=rate,
                       channels=1,
                       device=device_index,
                       dtype='float32')
    sd.wait()
    return recording.flatten()

def extract_features(audio, sr=48000):
    audio = librosa.util.normalize(audio)
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
    mfccs_mean = np.mean(mfccs.T, axis=0)
    return np.expand_dims(mfccs_mean, axis=0)

# =============================
#    WHISPER DOCKER TRANSCRIPTION
# =============================
WHISPER_API = "http://192.168.1.5:9999/audio"  # change if your Docker host is different

def transcribe_with_whisper_docker(file_path):
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(WHISPER_API, files=files, timeout=60)
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

# =============================
#        MAIN LOOP
# =============================
print(f"{wake_word_name} is ready. Say 'Hey {wake_word_name}' to wake me up.")
print(f"[TTS skipped] -> Ciao! Sono {wake_word_name}, pronto ad aiutarti.")

while True:
    try:
        audio = record_audio(duration, fs)
        features = extract_features(audio, sr=fs)
        del audio
        gc.collect()

        prediction = wakeword_model.predict(features, verbose=0)
        wake_prob = float(prediction[0][1])
        del features
        del prediction
        gc.collect()

        print(f"Wake word probability: {wake_prob:.3f}")

        if wake_prob > wake_threshold:
            print("🚀 Wake word detected! Listening for command...")
            print("[TTS skipped] -> Yes sir, what is your command?")

            command_audio = record_audio(2, fs)
            write(audio_file, fs, (command_audio * 32767).astype(np.int16))
            del command_audio
            gc.collect()

            print("🎧 Sending command to Whisper Docker API...")
            command = transcribe_with_whisper_docker(audio_file)
            print(f"🗣 You said: {command}")
            if command:
                print(f"[TTS skipped] -> You said: {command}")

            if os.path.exists(audio_file):
                os.remove(audio_file)

            print("Listening again...\n")

    except KeyboardInterrupt:
        print("\n🛑 Exiting gracefully.")
        break
