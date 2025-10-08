#!/usr/bin/env python3
"""
Fixed Mycroft Precise Listener
Loads model with custom loss function registered
"""

import pyaudio
import numpy as np
from keras.models import load_model
import keras.backend as K
import argparse
from pathlib import Path

try:
    import sonopy
    HAS_SONOPY = True
except ImportError:
    HAS_SONOPY = False
    print("⚠️  Warning: sonopy not found, using simplified features")


def weighted_log_loss(y_true, y_pred):
    """Custom loss function used by Mycroft Precise"""
    false_pos = y_pred * (1.0 - y_true)
    false_neg = (1.0 - y_pred) * y_true
    return K.mean(false_pos + false_neg * 5.0)


class SimplePreciseListener:
    def __init__(self, model_path, chunk_size=2048, sample_rate=16000, recording_rate=48000):
        self.chunk_size = chunk_size
        self.sample_rate = sample_rate  # Target rate for model
        self.recording_rate = recording_rate  # Actual mic rate
        
        # Load model with custom objects
        print(f"Loading model: {model_path}")
        self.model = load_model(
            model_path, 
            custom_objects={'weighted_log_loss': weighted_log_loss},
            compile=False
        )
        print("✓ Model loaded successfully!")
        print(f"ℹ️  Recording at {recording_rate}Hz, processing at {sample_rate}Hz")
        
        self.audio = pyaudio.PyAudio()
        self.buffer = []
        self.buffer_size = 29  # Number of MFCC frames needed
        
    def extract_features(self, audio_data):
        """Extract MFCC features using sonopy or fallback"""
        from scipy import signal as sp_signal
        
        # Convert bytes to numpy array
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        
        # Downsample from recording_rate to sample_rate if needed
        if self.recording_rate != self.sample_rate:
            num_samples = int(len(audio_np) * self.sample_rate / self.recording_rate)
            audio_np = sp_signal.resample(audio_np, num_samples)
        
        # Normalize to -1.0 to 1.0
        audio_np = audio_np / 32768.0
        
        if HAS_SONOPY:
            # Use proper MFCC features
            try:
                mfcc_features = sonopy.mfcc_spec(
                    audio_np,
                    self.sample_rate,
                    window_stride=(self.sample_rate // 100, self.sample_rate // 50),
                    fft_size=512,
                    num_filt=20,
                    num_coeffs=13
                )
                # Return mean across time
                if len(mfcc_features.shape) > 1 and mfcc_features.shape[0] > 0:
                    return np.mean(mfcc_features, axis=0)
                else:
                    return np.zeros(13)
            except:
                pass
        
        # Fallback: simple spectral features
        from scipy.fft import rfft
        
        # Apply window
        window = np.hanning(len(audio_np))
        audio_windowed = audio_np * window
        
        # FFT
        fft_result = np.abs(rfft(audio_windowed))
        
        # Mel-scale binning (13 bins)
        mel_bins = 13
        bin_size = len(fft_result) // mel_bins
        
        features = []
        for i in range(mel_bins):
            start = i * bin_size
            end = start + bin_size
            if end <= len(fft_result):
                # Log energy in each bin
                energy = np.mean(fft_result[start:end])
                features.append(np.log(energy + 1e-10))
            else:
                features.append(-10.0)
        
        return np.array(features)
    
    def listen(self, threshold=0.5, trigger_level=3):
        """Listen for wake word"""
        stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.recording_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        print(f"\n🎤 Listening for wake word (threshold: {threshold})...")
        print("Press Ctrl+C to stop\n")
        
        activation_count = 0
        
        try:
            while True:
                # Read audio
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                
                # Extract features
                features = self.extract_features(data)
                
                # Add to buffer
                self.buffer.append(features)
                if len(self.buffer) > self.buffer_size:
                    self.buffer.pop(0)
                
                # Need full buffer before prediction
                if len(self.buffer) < self.buffer_size:
                    continue
                
                # Prepare input for model
                input_data = np.array([self.buffer])  # Shape: (1, 29, 13)
                
                # Predict
                prediction = self.model.predict(input_data, verbose=0)[0][0]
                
                # Check activation
                if prediction > threshold:
                    activation_count += 1
                    if activation_count >= trigger_level:
                        print(f"\n🔔 WAKE WORD DETECTED! (confidence: {prediction:.2f})")
                        activation_count = 0
                        self.buffer = []  # Clear buffer after detection
                else:
                    activation_count = max(0, activation_count - 1)
                    
                # Show activity indicator
                if prediction > 0.3:
                    bar_length = int(prediction * 20)
                    bar = '█' * bar_length + '░' * (20 - bar_length)
                    print(f"\r[{bar}] {prediction:.2f}", end='', flush=True)
                
        except KeyboardInterrupt:
            print("\n\n✓ Stopped listening")
        finally:
            stream.stop_stream()
            stream.close()
            self.audio.terminate()


def main():
    parser = argparse.ArgumentParser(description='Listen for Mycroft Precise wake word')
    parser.add_argument('model', help='Path to .net model file')
    parser.add_argument('--threshold', '-t', type=float, default=0.5, 
                       help='Detection threshold (default: 0.5)')
    parser.add_argument('--trigger-level', '-l', type=int, default=3,
                       help='Number of activations needed (default: 3)')
    parser.add_argument('--chunk-size', '-c', type=int, default=2048,
                       help='Audio chunk size (default: 2048)')
    parser.add_argument('--recording-rate', '-r', type=int, default=48000,
                       help='Microphone sample rate (default: 48000)')
    
    args = parser.parse_args()
    
    if not Path(args.model).exists():
        print(f"❌ Error: Model file not found: {args.model}")
        return
    
    listener = SimplePreciseListener(
        args.model, 
        chunk_size=args.chunk_size,
        recording_rate=args.recording_rate
    )
    
    listener.listen(
        threshold=args.threshold,
        trigger_level=args.trigger_level
    )


if __name__ == '__main__':
    main()