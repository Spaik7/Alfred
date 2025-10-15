#!/usr/bin/env python3
"""
Core helper functions for Alfred - Audio processing, transcription, and response generation
"""

import sounddevice as sd
import numpy as np
import librosa
import onnxruntime as ort
import subprocess
import time
import requests
import os
from tqdm import tqdm
from scipy.io.wavfile import write
import gc
from pathlib import Path

from functions.response_generator import generate_response as generate_ai_response
from functions.response_templates import generate_template_response
from config import RESPONSE_MODE

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
    """Load ONNX model with progress indicator"""
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
#     AUDIO HELPERS
# =============================
def record_audio(duration=1.5, rate=48000, device_index=None):
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

def transcribe(file_path, whisper_mode='docker', whisper_model='base', docker_ip='192.168.1.5:9999'):
    """Main transcription function that routes to local or docker"""
    if whisper_mode == 'local':
        return transcribe_with_whisper_local(file_path, model=whisper_model)
    else:
        api_url = f"http://{docker_ip}/audio"
        return transcribe_with_whisper_docker(file_path, api_url)
