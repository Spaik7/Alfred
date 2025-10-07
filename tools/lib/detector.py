#!/usr/bin/env python3
"""
Test the custom PyTorch wake word model
"""

import torch
import numpy as np
import librosa
import pyaudio
import wave
from pathlib import Path
import argparse
from .trainer import LightweightWakeWordModel


class PyTorchWakeWordDetector:
    def __init__(self, model_path='models/alfred_pytorch.pt'):
        """Load the PyTorch model"""
        print(f"Loading model from {model_path}...")

        self.model = LightweightWakeWordModel()
        self.model.load_state_dict(torch.load(model_path))
        self.model.eval()

        print("✓ Model loaded successfully!")

    def extract_mfcc(self, audio_file):
        """Extract MFCC features from audio file"""
        # Load audio at 16kHz
        audio, sr = librosa.load(audio_file, sr=16000)

        # Extract MFCCs
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        mfcc = mfcc.T  # (time, features)

        # Pad or truncate to 29 frames
        if len(mfcc) < 29:
            mfcc = np.pad(mfcc, ((0, 29 - len(mfcc)), (0, 0)), mode='constant')
        else:
            mfcc = mfcc[:29]

        # Normalize
        mfcc = (mfcc - np.mean(mfcc)) / (np.std(mfcc) + 1e-8)

        return mfcc

    def predict(self, audio_file):
        """Predict if audio contains wake word"""
        mfcc = self.extract_mfcc(audio_file)
        mfcc_tensor = torch.FloatTensor(mfcc).unsqueeze(0)  # Add batch dimension

        with torch.no_grad():
            prediction = self.model(mfcc_tensor)

        return prediction.item()

    def test_dataset(self, test_dir, threshold=0.5):
        """Test model against test dataset"""
        test_path = Path(test_dir)

        wake_dir = test_path / 'wake-word'
        not_wake_dir = test_path / 'not-wake-word'

        wake_files = list(wake_dir.glob('*.wav')) if wake_dir.exists() else []
        not_wake_files = list(not_wake_dir.glob('*.wav')) if not_wake_dir.exists() else []

        print(f"\nTesting on {len(wake_files)} wake-word samples and {len(not_wake_files)} not-wake-word samples...")

        # Test wake word samples
        wake_correct = 0
        wake_scores = []
        for f in wake_files:
            score = self.predict(f)
            wake_scores.append(score)
            if score >= threshold:
                wake_correct += 1

        # Test not-wake-word samples
        not_wake_correct = 0
        not_wake_scores = []
        for f in not_wake_files:
            score = self.predict(f)
            not_wake_scores.append(score)
            if score < threshold:
                not_wake_correct += 1

        # Calculate metrics
        wake_accuracy = wake_correct / len(wake_files) if wake_files else 0
        not_wake_accuracy = not_wake_correct / len(not_wake_files) if not_wake_files else 0
        total_samples = len(wake_files) + len(not_wake_files)
        overall_accuracy = (wake_correct + not_wake_correct) / total_samples if total_samples > 0 else 0

        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        print(f"Wake word detection rate:     {wake_accuracy:.2%} ({wake_correct}/{len(wake_files)})")
        print(f"Not-wake word rejection rate: {not_wake_accuracy:.2%} ({not_wake_correct}/{len(not_wake_files)})")
        print(f"Overall accuracy:             {overall_accuracy:.2%}")
        if wake_scores:
            print(f"\nWake word scores:     min={min(wake_scores):.3f}, max={max(wake_scores):.3f}, avg={np.mean(wake_scores):.3f}")
        if not_wake_scores:
            print(f"Not-wake word scores: min={min(not_wake_scores):.3f}, max={max(not_wake_scores):.3f}, avg={np.mean(not_wake_scores):.3f}")
        print("=" * 60)

    def listen_microphone(self, threshold=0.5, chunk_duration=3):
        """Listen to microphone and detect wake word"""
        print("\n" + "=" * 60)
        print("LIVE WAKE WORD DETECTION - PyTorch Model")
        print("=" * 60)
        print(f"Listening for wake word...")
        print(f"Detection threshold: {threshold}")
        print(f"Press Ctrl+C to stop")
        print("=" * 60 + "\n")

        CHUNK = 2048
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RECORDING_RATE = 48000  # What device supports
        TARGET_RATE = 16000     # What model expects

        p = pyaudio.PyAudio()

        stream = None
        try:
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RECORDING_RATE,
                input=True,
                frames_per_buffer=CHUNK
            )

            temp_file = Path("/tmp/wake_word_temp.wav")

            while True:
                # Record chunk at 48kHz
                frames = []
                num_chunks = int(RECORDING_RATE / CHUNK * chunk_duration)

                for _ in range(num_chunks):
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    frames.append(data)

                # Resample from 48kHz to 16kHz
                audio_data = b''.join(frames)
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
                audio_np = audio_np / 32768.0  # Normalize

                # Resample using librosa
                resampled = librosa.resample(audio_np, orig_sr=RECORDING_RATE, target_sr=TARGET_RATE)
                resampled = np.clip(resampled * 32768.0, -32768, 32767).astype(np.int16)

                # Save to temp file at 16kHz
                with wave.open(str(temp_file), 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(p.get_sample_size(FORMAT))
                    wf.setframerate(TARGET_RATE)
                    wf.writeframes(resampled.tobytes())

                # Predict
                score = self.predict(temp_file)

                # Display result
                if score >= threshold:
                    print(f"🎯 WAKE WORD DETECTED! (confidence: {score:.3f})")
                else:
                    # Show dots for activity, scores occasionally
                    if np.random.random() < 0.1:  # 10% of the time
                        print(f"   Listening... (score: {score:.3f})")
                    else:
                        print(".", end="", flush=True)

        except KeyboardInterrupt:
            print("\n\n✓ Stopped listening.")
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
            p.terminate()
            if temp_file.exists():
                temp_file.unlink()


def main():
    parser = argparse.ArgumentParser(description='Test PyTorch wake word model')
    parser.add_argument('--model', default='models/alfred_pytorch.pt', help='Model path')
    parser.add_argument('--test', action='store_true', help='Test against test dataset')
    parser.add_argument('--listen', action='store_true', help='Listen to microphone')
    parser.add_argument('--test-dir', default='../precise_data/test', help='Test dataset directory')
    parser.add_argument('--threshold', type=float, default=0.5, help='Detection threshold (0-1)')
    parser.add_argument('--test-file', help='Test a single audio file')

    args = parser.parse_args()

    # Load detector
    detector = PyTorchWakeWordDetector(args.model)

    # Test single file
    if args.test_file:
        score = detector.predict(args.test_file)
        print(f"\nPrediction for {args.test_file}: {score:.3f}")
        if score >= args.threshold:
            print("✓ Wake word detected!")
        else:
            print("✗ Not wake word")

    # Test dataset
    if args.test:
        detector.test_dataset(args.test_dir, threshold=args.threshold)

    # Live microphone
    if args.listen:
        detector.listen_microphone(threshold=args.threshold)

    # If no action specified, show help
    if not (args.test or args.listen or args.test_file):
        parser.print_help()


if __name__ == '__main__':
    main()
