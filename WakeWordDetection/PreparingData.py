import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import os

def list_input_devices():
    """Print all available audio input devices."""
    print("🎙️ Available input devices:")
    for i, dev in enumerate(sd.query_devices()):
        if dev['max_input_channels'] > 0:
            print(f"{i}: {dev['name']}")


def record_clip(filename, duration=2, fs=48000, device=None):
    """Record one clip and save normalized WAV."""
    print(f"🎧 Recording: {filename}")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, device=device)
    sd.wait()

    # Normalize safely
    if np.max(np.abs(audio)) > 0:
        audio = np.int16(audio / np.max(np.abs(audio)) * 32767)
    else:
        audio = np.int16(audio)

    write(filename, fs, audio)
    print("✅ Saved", filename)


def record_audio_and_save(save_path, n_times=50, device=None):
    """
    Record the wake word n_times; each time press Enter before speaking.
    """
    os.makedirs(save_path, exist_ok=True)
    input("🔴 Press Enter to start recording Wake Word...")
    for i in range(n_times):
        filename = os.path.join(save_path, f"{i}.wav")
        record_clip(filename, duration=2, fs=48000, device=device)
        input(f"Press Enter to record next or Ctrl+C to stop ({i + 1}/{n_times}): ")


def record_background_sound(save_path, n_times=50, device=None):
    """
    Record background/gibberish automatically.
    """
    os.makedirs(save_path, exist_ok=True)
    input("🎤 Press Enter to start recording BACKGROUND sounds...")
    for i in range(n_times):
        filename = os.path.join(save_path, f"{i}.wav")
        record_clip(filename, duration=2, fs=48000, device=device)
        print(f"Background clip {i + 1}/{n_times} done.")


if __name__ == "__main__":
    # Step 0: choose mic
    list_input_devices()
    device = int(input("Select input device number: "))

    # Step 1: record wake word
    print("\n=== Recording Wake Word ===")
    record_audio_and_save("audio_data/", n_times=100, device=device)

    # Step 2: record background
    print("\n=== Recording Background ===")
    record_background_sound("background_sound/", n_times=100, device=device)

    print("\n✅ Dataset collection complete!")
