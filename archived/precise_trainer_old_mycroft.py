#!/usr/bin/env python3
"""
Mycroft Precise Wake Word Training Pipeline
Handles data organization, training, testing, and model conversion
"""

import os
import shutil
import subprocess
import argparse
from pathlib import Path
import numpy as np
import wave
import pyaudio
import librosa
from tensorflow import keras


class PreciseTrainer:
    def __init__(self, wake_word_name, base_dir="precise_data"):
        self.wake_word_name = wake_word_name
        self.base_dir = Path(base_dir)
        # Remove spaces and special characters, make lowercase
        clean_name = wake_word_name.replace(' ', '-').lower()
        self.model_name = f"{clean_name}.net"
        
        # Define directory structure
        self.dirs = {
            'train_wake': self.base_dir / 'train' / 'wake-word',
            'train_not_wake': self.base_dir / 'train' / 'not-wake-word',
            'test_wake': self.base_dir / 'test' / 'wake-word',
            'test_not_wake': self.base_dir / 'test' / 'not-wake-word',
            'models': Path('models')
        }
    
    def setup_directories(self):
        """Step 2: Create and organize directory structure"""
        print("=" * 60)
        print("STEP 2: Setting up directory structure")
        print("=" * 60)
        
        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created: {dir_path}")
        
        print(f"\nDirectory structure ready!")
        print(f"\nNow place your audio files:")
        print(f"  - Wake word samples → {self.dirs['train_wake']}")
        print(f"  - Not-wake samples → {self.dirs['train_not_wake']}")
        print(f"  - Test wake samples → {self.dirs['test_wake']}")
        print(f"  - Test not-wake samples → {self.dirs['test_not_wake']}")
        print()
    
    def count_samples(self):
        """Count audio samples in each directory"""
        counts = {}
        for name, path in self.dirs.items():
            if 'models' in name:
                continue
            wav_files = list(path.glob('*.wav'))
            counts[name] = len(wav_files)
        return counts
    
    def validate_data(self):
        """Validate that we have enough data to train"""
        counts = self.count_samples()
        
        print("\n" + "=" * 60)
        print("Data Summary:")
        print("=" * 60)
        for name, count in counts.items():
            print(f"{name:20s}: {count:4d} files")
        
        # Minimum requirements
        if counts['train_wake'] < 20:
            print("\n⚠ WARNING: Less than 20 wake word samples. Recommend 50+")
        if counts['train_not_wake'] < 50:
            print("⚠ WARNING: Less than 50 not-wake samples. Recommend 200+")
        
        return counts['train_wake'] > 0 and counts['train_not_wake'] > 0
    
    def train_model(self, epochs=60, incremental=False):
        """Step 3: Train the wake word model"""
        print("\n" + "=" * 60)
        print(f"STEP 3: Training model '{self.model_name}'")
        print("=" * 60)
        
        if not self.validate_data():
            print("\n❌ ERROR: Not enough training data!")
            return False
        
        model_path = self.dirs['models'] / self.model_name
        
        if incremental and model_path.exists():
            cmd = [
                'precise-train-incremental',
                str(model_path),
                str(self.base_dir / 'train')
            ]
            print(f"\n🔄 Incremental training on existing model...")
        else:
            cmd = [
                'precise-train',
                '-e', str(epochs),
                str(model_path),
                str(self.base_dir / 'train')
            ]
            print(f"\n🚀 Training new model for {epochs} epochs...")
        
        print(f"Command: {' '.join(cmd)}\n")
        
        try:
            result = subprocess.run(cmd, check=True)
            print(f"\n✓ Training completed successfully!")
            print(f"Model saved to: {model_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Training failed: {e}")
            return False
        except FileNotFoundError:
            print("\n❌ ERROR: precise-train not found. Is Mycroft Precise installed?")
            print("Install with: pip install mycroft-precise")
            return False
    
    def extract_mfcc(self, audio_file, n_mfcc=13, n_features=29):
        """Extract MFCC features from audio file (matching Precise's format)"""
        # Load audio at 16kHz (Precise's default)
        audio, sr = librosa.load(audio_file, sr=16000)

        # Extract MFCCs
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc)

        # Transpose to get time x features
        mfcc = mfcc.T

        # Pad or truncate to n_features frames
        if len(mfcc) < n_features:
            # Pad with zeros
            mfcc = np.pad(mfcc, ((0, n_features - len(mfcc)), (0, 0)), mode='constant')
        else:
            # Take first n_features
            mfcc = mfcc[:n_features]

        return mfcc

    def predict(self, model, audio_file):
        """Predict if audio contains wake word"""
        mfcc = self.extract_mfcc(audio_file)
        mfcc = np.expand_dims(mfcc, axis=0)  # Add batch dimension

        prediction = model.predict(mfcc, verbose=0)[0][0]
        return prediction

    def test_model_dataset(self, model, threshold=0.5):
        """Test model against test dataset"""
        test_path = self.base_dir / 'test'

        wake_dir = test_path / 'wake-word'
        not_wake_dir = test_path / 'not-wake-word'

        wake_files = list(wake_dir.glob('*.wav'))
        not_wake_files = list(not_wake_dir.glob('*.wav'))

        if not wake_files and not not_wake_files:
            print("⚠ WARNING: No test files found.")
            return

        print(f"\nTesting on {len(wake_files)} wake-word samples and {len(not_wake_files)} not-wake-word samples...")

        # Test wake word samples
        wake_correct = 0
        wake_scores = []
        for f in wake_files:
            score = self.predict(model, f)
            wake_scores.append(score)
            if score >= threshold:
                wake_correct += 1

        # Test not-wake-word samples
        not_wake_correct = 0
        not_wake_scores = []
        for f in not_wake_files:
            score = self.predict(model, f)
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

    def listen_microphone(self, model, threshold=0.5, chunk_duration=3):
        """Listen to microphone and detect wake word"""
        print("\n" + "=" * 60)
        print("LIVE WAKE WORD DETECTION")
        print("=" * 60)
        print(f"Listening for '{self.wake_word_name}'...")
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
                score = self.predict(model, temp_file)

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

    def test_model(self, threshold=0.5):
        """Step 4: Test the trained model"""
        print("\n" + "=" * 60)
        print("STEP 4: Testing model")
        print("=" * 60)

        model_path = self.dirs['models'] / self.model_name

        if not model_path.exists():
            print(f"❌ ERROR: Model not found at {model_path}")
            return False

        # Load model with TF 2.x compatibility
        print(f"Loading model from {model_path}...")
        try:
            model = keras.models.load_model(model_path, compile=False)
            model.compile(optimizer='rmsprop', loss='binary_crossentropy', metrics=['accuracy'])
            print("✓ Model loaded successfully!")
        except Exception as e:
            print(f"❌ ERROR loading model: {e}")
            return False

        # Test against dataset
        test_files = list((self.base_dir / 'test').rglob('*.wav'))
        if len(test_files) > 0:
            print(f"Found {len(test_files)} test files")
            self.test_model_dataset(model, threshold=threshold)
        else:
            print("⚠ WARNING: No test files found. Skipping automated testing.")

        # Offer live testing
        print("\n" + "-" * 60)
        print("Live Testing (press Ctrl+C to stop)")
        print("-" * 60)
        response = input("Test with microphone? (y/n): ").strip().lower()

        if response == 'y':
            try:
                self.listen_microphone(model, threshold=threshold)
            except Exception as e:
                print(f"\n❌ Live testing failed: {e}")

        return True
    
    def convert_model(self):
        """Step 5: Convert model to production format"""
        print("\n" + "=" * 60)
        print("STEP 5: Converting model to production format")
        print("=" * 60)
        
        model_path = self.dirs['models'] / self.model_name
        
        if not model_path.exists():
            print(f"❌ ERROR: Model not found at {model_path}")
            return False
        
        cmd = ['precise-convert', str(model_path)]
        print(f"Running: {' '.join(cmd)}\n")
        
        try:
            subprocess.run(cmd, check=True)
            pb_file = model_path.with_suffix('.pb')
            print(f"\n✓ Model converted successfully!")
            print(f"Production model: {pb_file}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Conversion failed: {e}")
            return False
        except FileNotFoundError:
            print("\n❌ ERROR: precise-convert not found.")
            return False
    
    def run_full_pipeline(self, epochs=60):
        """Run the complete training pipeline"""
        print("\n" + "=" * 60)
        print(f"Mycroft Precise Training Pipeline")
        print(f"Wake Word: {self.wake_word_name}")
        print("=" * 60)
        
        # Step 2: Setup directories
        self.setup_directories()
        
        input("\nPress Enter after adding your audio files...")
        
        # Step 3: Train
        if not self.train_model(epochs=epochs):
            print("\n❌ Pipeline stopped: Training failed")
            return
        
        # Step 4: Test
        self.test_model()
        
        # Step 5: Convert
        response = input("\nConvert model for production? (y/n): ").strip().lower()
        if response == 'y':
            self.convert_model()
        
        print("\n" + "=" * 60)
        print("✓ Pipeline completed!")
        print("=" * 60)
        print(f"\nYour model: {self.dirs['models'] / self.model_name}")


def main():
    parser = argparse.ArgumentParser(
        description='Mycroft Precise Wake Word Training Pipeline'
    )
    parser.add_argument(
        'wake_word',
        help='Name of your wake word (e.g., "hey mycroft")'
    )
    parser.add_argument(
        '--epochs', '-e',
        type=int,
        default=60,
        help='Number of training epochs (default: 60)'
    )
    parser.add_argument(
        '--step',
        choices=['setup', 'train', 'test', 'convert', 'all'],
        default='all',
        help='Run specific step or full pipeline (default: all)'
    )
    parser.add_argument(
        '--incremental', '-i',
        action='store_true',
        help='Use incremental training on existing model'
    )
    parser.add_argument(
        '--data-dir',
        default='precise_data',
        help='Base directory for data (default: precise_data)'
    )
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=0.5,
        help='Detection threshold for testing (0-1, default: 0.5)'
    )

    args = parser.parse_args()

    trainer = PreciseTrainer(args.wake_word, args.data_dir)

    if args.step == 'all':
        trainer.run_full_pipeline(epochs=args.epochs)
    elif args.step == 'setup':
        trainer.setup_directories()
    elif args.step == 'train':
        trainer.train_model(epochs=args.epochs, incremental=args.incremental)
    elif args.step == 'test':
        trainer.test_model(threshold=args.threshold)
    elif args.step == 'convert':
        trainer.convert_model()


if __name__ == '__main__':
    main()