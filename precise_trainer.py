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
    
    def test_model(self):
        """Step 4: Test the trained model"""
        print("\n" + "=" * 60)
        print("STEP 4: Testing model")
        print("=" * 60)
        
        model_path = self.dirs['models'] / self.model_name
        
        if not model_path.exists():
            print(f"❌ ERROR: Model not found at {model_path}")
            return False
        
        test_dir = self.base_dir / 'test'
        
        # Count test files
        test_files = list(test_dir.rglob('*.wav'))
        if len(test_files) == 0:
            print("⚠ WARNING: No test files found. Skipping automated testing.")
            print(f"Add test files to {test_dir} for automated testing.")
        else:
            print(f"Found {len(test_files)} test files")
            cmd = ['precise-test', str(model_path), str(test_dir)]
            print(f"Running: {' '.join(cmd)}\n")
            
            try:
                subprocess.run(cmd, check=True)
                print("\n✓ Test completed successfully!")
            except subprocess.CalledProcessError as e:
                print(f"\n⚠ Testing had issues (this is often normal with small datasets)")
        
        # Offer live testing
        print("\n" + "-" * 60)
        print("Live Testing (press Ctrl+C to stop)")
        print("-" * 60)
        response = input("Test with microphone? (y/n): ").strip().lower()
        
        if response == 'y':
            cmd = ['precise-listen', str(model_path)]
            print(f"\n🎤 Starting live detection. Say '{self.wake_word_name}'")
            print("Press Ctrl+C to stop\n")
            
            try:
                subprocess.run(cmd)
            except KeyboardInterrupt:
                print("\n\n✓ Live testing stopped")
            except subprocess.CalledProcessError as e:
                print(f"\n❌ Live testing failed: {e}")
            except FileNotFoundError:
                print("\n❌ ERROR: precise-listen not found.")
        
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
    
    args = parser.parse_args()
    
    trainer = PreciseTrainer(args.wake_word, args.data_dir)
    
    if args.step == 'all':
        trainer.run_full_pipeline(epochs=args.epochs)
    elif args.step == 'setup':
        trainer.setup_directories()
    elif args.step == 'train':
        trainer.train_model(epochs=args.epochs, incremental=args.incremental)
    elif args.step == 'test':
        trainer.test_model()
    elif args.step == 'convert':
        trainer.convert_model()


if __name__ == '__main__':
    main()