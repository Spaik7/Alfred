import sounddevice as sd
import numpy as np
import librosa
import tensorflow as tf
import whisper
import subprocess
import time
from tqdm import tqdm
from scipy.io.wavfile import write
import gc  # add this at the top

# =============================
#        SPEECH OUTPUT
# =============================
def speak(text):
    """Disabled on Raspberry Pi until an audio output device is available."""
    # subprocess.run(["say", text])  # macOS only
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


def load_whisper_model(name):
    print(f"Loading Whisper model '{name}' ...")
    with tqdm(total=100) as pbar:
        for i in range(10):
            time.sleep(0.1)
            pbar.update(10)
    model = whisper.load_model(name)
    print("✅ Whisper model ready!")
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

# Load models
wakeword_model = load_model_with_progress("WWD.h5")
whisper_model = load_whisper_model("tiny")

# =============================
#       CONFIGURATION
# =============================
duration = 1.5        # seconds for wake word listening
fs = 48000            # sample rate
wake_word_name = "Alfred"
wake_threshold = 0.9  # sensitivity threshold

# =============================
#     AUDIO HELPERS
# =============================
def record_audio(duration=1.5, rate=48000):
    """Record audio snippet from selected device."""
    recording = sd.rec(int(duration * rate),
                       samplerate=rate,
                       channels=1,
                       device=device_index,
                       dtype='float32')
    sd.wait()
    return recording.flatten()

def extract_features(audio, sr=48000):
    """Extract 40 MFCC features averaged over time (must match training)."""
    audio = librosa.util.normalize(audio)
    mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
    mfccs_mean = np.mean(mfccs.T, axis=0)
    return np.expand_dims(mfccs_mean, axis=0)

# =============================
#        MAIN LOOP
# =============================
print(f"{wake_word_name} is ready. Say 'Hey {wake_word_name}' to wake me up.")
# speak(f"Ciao! Sono {wake_word_name}, pronto ad aiutarti.")  # disabled
print(f"[TTS skipped] -> Ciao! Sono {wake_word_name}, pronto ad aiutarti.")

while True:
    try:
        # Record short snippet
        audio = record_audio(duration, fs)

        # Extract MFCC features
        features = extract_features(audio, sr=fs)

        # Free raw audio if no longer needed
        del audio
        gc.collect()

        # Predict wake word
        prediction = wakeword_model.predict(features, verbose=0)
        wake_prob = float(prediction[0][1])

        # Free features after prediction
        del features
        del prediction
        gc.collect()

        print(f"Wake word probability: {wake_prob:.3f}")

        if wake_prob > wake_threshold:
            print("🚀 Wake word detected! Listening for command...")
            print("[TTS skipped] -> Yes sir, what is your command?")

            # Record longer audio for command
            command_audio = record_audio(2, fs)
            write("last_command.wav", fs, (command_audio * 32767).astype(np.int16))

            # Free command audio after saving
            del command_audio
            gc.collect()

            # Transcribe command using Whisper
            print("🎧 Transcribing command with Whisper...")
            result = whisper_model.transcribe(
                "last_command.wav",
                fp16=False,
                language="it",
                temperature=0.0,
                condition_on_previous_text=False,
            )
            command = result["text"].strip()

            print(f"🗣 You said: {command}")
            if command:
                print(f"[TTS skipped] -> You said: {command}")

            # Free transcription result
            del result
            del command
            gc.collect()

            print("Listening again...\n")

    except KeyboardInterrupt:
        print("\n🛑 Exiting gracefully.")
        break
