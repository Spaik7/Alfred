#!/usr/bin/env python3
"""
Custom PyTorch Wake Word Detector
Optimized for Raspberry Pi with minimal data requirements

Features:
- Data augmentation (multiply samples 10x)
- Lightweight CNN + GRU architecture
- Model size < 1MB
- Real-time inference on RPi
- Works with 50+ wake word samples
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import librosa
import numpy as np
from pathlib import Path
import argparse
from tqdm import tqdm
import random


class AudioAugmentor:
    """Augment audio data to multiply training samples"""

    @staticmethod
    def add_noise(audio, noise_factor=0.005):
        """Add random noise"""
        noise = np.random.randn(len(audio))
        return audio + noise_factor * noise

    @staticmethod
    def time_shift(audio, shift_max=0.2):
        """Shift audio in time"""
        shift = int(np.random.uniform(-shift_max, shift_max) * len(audio))
        return np.roll(audio, shift)

    @staticmethod
    def change_pitch(audio, sr, n_steps=2):
        """Change pitch slightly"""
        return librosa.effects.pitch_shift(audio, sr=sr, n_steps=n_steps)

    @staticmethod
    def change_speed(audio, rate=1.1):
        """Change speed slightly"""
        return librosa.effects.time_stretch(audio, rate=rate)

    @staticmethod
    def augment(audio, sr):
        """Apply random augmentation"""
        aug_type = random.choice(['noise', 'shift', 'pitch', 'speed', 'none'])

        if aug_type == 'noise':
            return AudioAugmentor.add_noise(audio)
        elif aug_type == 'shift':
            return AudioAugmentor.time_shift(audio)
        elif aug_type == 'pitch':
            return AudioAugmentor.change_pitch(audio, sr)
        elif aug_type == 'speed':
            return AudioAugmentor.change_speed(audio)
        else:
            return audio


class WakeWordDataset(Dataset):
    """Dataset for wake word detection with augmentation"""

    def __init__(self, data_dir, augment=True, augment_factor=5):
        self.data_dir = Path(data_dir)
        self.augment = augment
        self.augment_factor = augment_factor

        # Load file lists
        wake_dir = self.data_dir / 'wake-word'
        not_wake_dir = self.data_dir / 'not-wake-word'

        self.wake_files = list(wake_dir.glob('*.wav')) if wake_dir.exists() else []
        self.not_wake_files = list(not_wake_dir.glob('*.wav')) if not_wake_dir.exists() else []

        # Create dataset: each file will be augmented multiple times
        self.samples = []

        # Wake word samples (label = 1)
        for f in self.wake_files:
            if augment:
                for _ in range(augment_factor):
                    self.samples.append((f, 1, True))  # (file, label, should_augment)
            else:
                self.samples.append((f, 1, False))

        # Not-wake word samples (label = 0)
        for f in self.not_wake_files:
            if augment:
                for _ in range(augment_factor):
                    self.samples.append((f, 0, True))
            else:
                self.samples.append((f, 0, False))

        # Shuffle
        random.shuffle(self.samples)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        filepath, label, should_augment = self.samples[idx]

        # Load audio
        audio, sr = librosa.load(filepath, sr=16000)

        # Augment if needed
        if should_augment:
            audio = AudioAugmentor.augment(audio, sr)

        # Extract MFCC features (same as Precise: 29 frames x 13 coefficients)
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
        mfcc = mfcc.T  # (time, features)

        # Pad or truncate to 29 frames
        if len(mfcc) < 29:
            mfcc = np.pad(mfcc, ((0, 29 - len(mfcc)), (0, 0)), mode='constant')
        else:
            mfcc = mfcc[:29]

        # Normalize
        mfcc = (mfcc - np.mean(mfcc)) / (np.std(mfcc) + 1e-8)

        return torch.FloatTensor(mfcc), torch.FloatTensor([label])


class LightweightWakeWordModel(nn.Module):
    """
    Lightweight CNN + GRU model for wake word detection
    Optimized for Raspberry Pi: ~500KB model size
    """

    def __init__(self, input_size=13, hidden_size=32, num_layers=1):
        super().__init__()

        # 1D Convolution to extract local features
        self.conv = nn.Sequential(
            nn.Conv1d(input_size, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.BatchNorm1d(32),
            nn.Dropout(0.2)
        )

        # GRU for temporal modeling
        self.gru = nn.GRU(
            input_size=32,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2 if num_layers > 1 else 0
        )

        # Classifier
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 16),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        # x shape: (batch, time, features)
        batch_size = x.size(0)

        # Conv expects (batch, features, time)
        x = x.transpose(1, 2)
        x = self.conv(x)

        # Back to (batch, time, features) for GRU
        x = x.transpose(1, 2)

        # GRU
        out, _ = self.gru(x)

        # Take last output
        out = out[:, -1, :]

        # Classify
        out = self.fc(out)

        return out


def train_model(data_dir, epochs=100, batch_size=32, learning_rate=0.001, device='cpu'):
    """Train the wake word model"""

    print("=" * 60)
    print("Training Custom PyTorch Wake Word Model")
    print("=" * 60)

    # Create datasets
    train_dir = Path(data_dir) / 'train'
    test_dir = Path(data_dir) / 'test'

    print(f"Loading training data from {train_dir}...")
    train_dataset = WakeWordDataset(train_dir, augment=True, augment_factor=5)

    print(f"Loading test data from {test_dir}...")
    test_dataset = WakeWordDataset(test_dir, augment=False)

    print(f"\nTraining samples: {len(train_dataset)}")
    print(f"Test samples: {len(test_dataset)}")

    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # Create model
    model = LightweightWakeWordModel().to(device)

    # Count parameters
    num_params = sum(p.numel() for p in model.parameters())
    print(f"\nModel parameters: {num_params:,} (~{num_params * 4 / 1024:.1f}KB)")

    # Loss and optimizer
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # Training loop
    print(f"\nTraining for {epochs} epochs...")
    best_accuracy = 0

    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        train_correct = 0
        train_total = 0

        for mfcc, labels in train_loader:
            mfcc, labels = mfcc.to(device), labels.to(device)

            # Forward
            outputs = optimizer.zero_grad()
            outputs = model(mfcc)
            loss = criterion(outputs, labels)

            # Backward
            loss.backward()
            optimizer.step()

            # Stats
            train_loss += loss.item()
            predictions = (outputs > 0.5).float()
            train_correct += (predictions == labels).sum().item()
            train_total += labels.size(0)

        train_accuracy = train_correct / train_total

        # Validation
        model.eval()
        test_loss = 0
        test_correct = 0
        test_total = 0

        with torch.no_grad():
            for mfcc, labels in test_loader:
                mfcc, labels = mfcc.to(device), labels.to(device)

                outputs = model(mfcc)
                loss = criterion(outputs, labels)

                test_loss += loss.item()
                predictions = (outputs > 0.5).float()
                test_correct += (predictions == labels).sum().item()
                test_total += labels.size(0)

        test_accuracy = test_correct / test_total if test_total > 0 else 0

        # Print progress
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{epochs} - "
                  f"Train Loss: {train_loss/len(train_loader):.4f}, "
                  f"Train Acc: {train_accuracy:.2%}, "
                  f"Test Acc: {test_accuracy:.2%}")

        # Save best model
        if test_accuracy > best_accuracy:
            best_accuracy = test_accuracy
            torch.save(model.state_dict(), 'models/alfred_pytorch.pt')

    print("\n" + "=" * 60)
    print(f"✓ Training completed!")
    print(f"Best test accuracy: {best_accuracy:.2%}")
    print(f"Model saved to: models/alfred_pytorch.pt")
    print("=" * 60)

    return model


def export_to_onnx(model_path='models/alfred_pytorch.pt', output_path='models/alfred.onnx'):
    """Export model to ONNX for faster inference on RPi"""
    print(f"\nExporting to ONNX...")

    model = LightweightWakeWordModel()
    model.load_state_dict(torch.load(model_path))
    model.eval()

    # Dummy input
    dummy_input = torch.randn(1, 29, 13)

    # Export
    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=11,
        input_names=['mfcc'],
        output_names=['probability'],
        dynamic_axes={'mfcc': {0: 'batch_size'}}
    )

    print(f"✓ ONNX model saved to: {output_path}")
    print(f"  Use this for deployment on Raspberry Pi!")


def main():
    parser = argparse.ArgumentParser(description='Train custom PyTorch wake word model')
    parser.add_argument('--data-dir', default='../precise_data', help='Data directory')
    parser.add_argument('--epochs', type=int, default=100, help='Training epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--export-onnx', action='store_true', help='Export to ONNX after training')

    args = parser.parse_args()

    # Create models directory
    Path('models').mkdir(exist_ok=True)

    # Train
    model = train_model(
        data_dir=args.data_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr
    )

    # Export to ONNX
    if args.export_onnx:
        export_to_onnx()


if __name__ == '__main__':
    main()
