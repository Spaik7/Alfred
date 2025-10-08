#!/usr/bin/env python3
"""
Audio Data Augmentation Script
Multiplies your training samples by creating augmented versions

Usage:
    python augment_data.py                    # Augment all training data (5x)
    python augment_data.py --multiplier 10    # Create 10x more samples
    python augment_data.py --only-wake        # Only augment wake word samples
"""

import librosa
import numpy as np
from pathlib import Path
import argparse
import soundfile as sf
from tqdm import tqdm
import random


class AudioAugmentor:
    """Create augmented versions of audio files"""

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
    def change_pitch(audio, sr, n_steps=None):
        """Change pitch"""
        if n_steps is None:
            n_steps = random.choice([-2, -1, 1, 2])
        return librosa.effects.pitch_shift(audio, sr=sr, n_steps=n_steps)

    @staticmethod
    def change_speed(audio, rate=None):
        """Change speed"""
        if rate is None:
            rate = random.choice([0.9, 0.95, 1.05, 1.1])
        return librosa.effects.time_stretch(audio, rate=rate)

    @staticmethod
    def change_volume(audio, factor=None):
        """Change volume"""
        if factor is None:
            factor = random.uniform(0.7, 1.3)
        return audio * factor

    @staticmethod
    def add_background_noise(audio, noise_factor=None):
        """Add colored noise"""
        if noise_factor is None:
            noise_factor = random.uniform(0.001, 0.01)
        noise = np.random.normal(0, noise_factor, len(audio))
        return audio + noise


def augment_file(input_file, output_file, augmentation_type, sr=16000):
    """Apply augmentation to a file and save"""
    # Load audio
    audio, _ = librosa.load(input_file, sr=sr)

    # Apply augmentation
    if augmentation_type == 'noise':
        augmented = AudioAugmentor.add_noise(audio)
    elif augmentation_type == 'shift':
        augmented = AudioAugmentor.time_shift(audio)
    elif augmentation_type == 'pitch':
        augmented = AudioAugmentor.change_pitch(audio, sr)
    elif augmentation_type == 'speed':
        augmented = AudioAugmentor.change_speed(audio)
    elif augmentation_type == 'volume':
        augmented = AudioAugmentor.change_volume(audio)
    elif augmentation_type == 'background':
        augmented = AudioAugmentor.add_background_noise(audio)
    elif augmentation_type == 'combined':
        # Apply multiple augmentations
        augmented = audio
        augmented = AudioAugmentor.add_noise(augmented)
        if random.random() > 0.5:
            augmented = AudioAugmentor.change_pitch(augmented, sr)
        if random.random() > 0.5:
            augmented = AudioAugmentor.change_speed(augmented)
    else:
        augmented = audio

    # Normalize to prevent clipping
    augmented = np.clip(augmented, -1.0, 1.0)

    # Save
    sf.write(output_file, augmented, sr)


def augment_dataset(data_dir='precise_data', multiplier=5, only_wake=False, only_not_wake=False):
    """Augment the training dataset"""

    data_path = Path(data_dir)
    train_path = data_path / 'train'

    # Determine which directories to process
    dirs_to_process = []
    if only_wake:
        dirs_to_process = [('wake-word', train_path / 'wake-word')]
    elif only_not_wake:
        dirs_to_process = [('not-wake-word', train_path / 'not-wake-word')]
    else:
        dirs_to_process = [
            ('wake-word', train_path / 'wake-word'),
            ('not-wake-word', train_path / 'not-wake-word')
        ]

    augmentation_types = ['noise', 'shift', 'pitch', 'speed', 'volume', 'background', 'combined']

    print("=" * 60)
    print("Audio Data Augmentation")
    print("=" * 60)
    print(f"Data directory: {data_dir}")
    print(f"Multiplier: {multiplier}x")
    print(f"Processing: {', '.join([d[0] for d in dirs_to_process])}")
    print()

    total_created = 0

    for dir_name, dir_path in dirs_to_process:
        if not dir_path.exists():
            print(f"⚠ Warning: {dir_path} doesn't exist, skipping...")
            continue

        # Get existing files
        existing_files = list(dir_path.glob('sample_*.wav'))
        original_count = len(existing_files)

        if original_count == 0:
            print(f"⚠ Warning: No files in {dir_path}, skipping...")
            continue

        # Find highest existing number
        max_num = 0
        for f in existing_files:
            try:
                num = int(f.stem.split('_')[1])
                if num > max_num:
                    max_num = num
            except (IndexError, ValueError):
                continue

        print(f"\n📁 {dir_name}/")
        print(f"   Original samples: {original_count}")
        print(f"   Creating {multiplier}x augmentations...")

        # Create augmented versions
        next_num = max_num + 1
        created = 0

        # Progress bar
        total_to_create = original_count * multiplier
        with tqdm(total=total_to_create, desc=f"   Augmenting", unit="file") as pbar:
            for original_file in existing_files:
                for i in range(multiplier):
                    # Choose augmentation type
                    aug_type = random.choice(augmentation_types)

                    # Generate output filename
                    output_file = dir_path / f'sample_{next_num:04d}.wav'

                    # Apply augmentation
                    try:
                        augment_file(original_file, output_file, aug_type)
                        created += 1
                        next_num += 1
                    except Exception as e:
                        print(f"\n   ❌ Error processing {original_file}: {e}")

                    pbar.update(1)

        total_created += created
        new_total = original_count + created
        print(f"   ✓ Created: {created} augmented samples")
        print(f"   ✓ Total now: {new_total} samples ({new_total/original_count:.1f}x)")

    print("\n" + "=" * 60)
    print("✓ Augmentation Complete!")
    print("=" * 60)
    print(f"Total new samples created: {total_created}")
    print(f"\nYou can now train with more data:")
    print(f"  python train.py --epochs 100")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Augment audio training data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create 5x more training samples (default)
  python augment_data.py

  # Create 10x more samples
  python augment_data.py -m 10

  # Only augment wake word samples
  python augment_data.py -w

  # Only augment not-wake samples
  python augment_data.py -n

  # Custom data directory
  python augment_data.py --data-dir my_data -m 3
        """
    )

    parser.add_argument(
        '--data-dir',
        default='data',
        help='Data directory (default: data)'
    )
    parser.add_argument(
        '-m', '--multiplier',
        type=int,
        default=5,
        help='How many augmented versions per file (default: 5)'
    )
    parser.add_argument(
        '-w', '--only-wake',
        action='store_true',
        help='Only augment wake-word samples'
    )
    parser.add_argument(
        '-n', '--only-not-wake',
        action='store_true',
        help='Only augment not-wake-word samples'
    )

    args = parser.parse_args()

    # Check for conflicting options
    if args.only_wake and args.only_not_wake:
        print("❌ Error: Can't use both --only-wake and --only-not-wake")
        return

    try:
        augment_dataset(
            data_dir=args.data_dir,
            multiplier=args.multiplier,
            only_wake=args.only_wake,
            only_not_wake=args.only_not_wake
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
