#!/usr/bin/env python3
"""
Alfred Wake Word Training Pipeline
Custom PyTorch-based wake word detection optimized for Raspberry Pi

Usage:
    python train.py              # Train with default settings
    python train.py --epochs 150 # Train with more epochs
    python train.py --help       # See all options
"""

import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from lib.trainer import train_model, export_to_onnx
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description='Train custom wake word detector for Alfred',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic training
  python train.py

  # Train with more epochs for better accuracy
  python train.py --epochs 150

  # Train and export to ONNX for Raspberry Pi
  python train.py --epochs 100 --export-onnx

  # Custom data directory
  python train.py --data-dir my_data --epochs 100
        """
    )

    parser.add_argument(
        '--data-dir',
        default='data',
        help='Directory containing train/test data (default: data)'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=100,
        help='Number of training epochs (default: 100, recommended: 100-150)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Training batch size (default: 32)'
    )
    parser.add_argument(
        '--lr',
        type=float,
        default=0.001,
        help='Learning rate (default: 0.001)'
    )
    parser.add_argument(
        '--export-onnx',
        action='store_true',
        help='Export to ONNX format after training (for Raspberry Pi deployment)'
    )

    args = parser.parse_args()

    # Create models directory
    Path('models').mkdir(exist_ok=True)

    print("=" * 60)
    print("Alfred Wake Word Trainer")
    print("Custom PyTorch Model - Optimized for Raspberry Pi")
    print("=" * 60)
    print(f"\nConfiguration:")
    print(f"  Data directory: {args.data_dir}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Batch size: {args.batch_size}")
    print(f"  Learning rate: {args.lr}")
    print(f"  Export to ONNX: {args.export_onnx}")
    print()

    # Train
    model = train_model(
        data_dir=args.data_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr
    )

    # Export to ONNX if requested
    if args.export_onnx:
        export_to_onnx()
        print("\n💡 Tip: Use models/alfred.onnx for deployment on Raspberry Pi")
        print("   It's optimized for faster inference!")


if __name__ == '__main__':
    main()
