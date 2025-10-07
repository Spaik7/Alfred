#!/usr/bin/env python3
"""
Alfred Wake Word Detector Testing
Test your trained model against dataset or live microphone

Usage:
    python test.py --test           # Test against test dataset
    python test.py --listen         # Live microphone detection
    python test.py --test --listen  # Both
"""

import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from lib.detector import PyTorchWakeWordDetector


def main():
    parser = argparse.ArgumentParser(
        description='Test Alfred wake word detector',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test against test dataset
  python test.py --test

  # Live microphone detection
  python test.py --listen

  # Test dataset then go live
  python test.py --test --listen

  # Test with custom threshold
  python test.py --listen --threshold 0.6

  # Test single audio file
  python test.py --test-file precise_data/test/wake-word/sample_0001.wav
        """
    )

    parser.add_argument(
        '--model',
        default='models/alfred_pytorch.pt',
        help='Path to trained model (default: models/alfred_pytorch.pt)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test model against test dataset'
    )
    parser.add_argument(
        '--listen',
        action='store_true',
        help='Listen to microphone for wake word detection'
    )
    parser.add_argument(
        '--test-dir',
        default='data/test',
        help='Test dataset directory (default: data/test)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Detection threshold 0-1 (default: 0.5, higher=more strict)'
    )
    parser.add_argument(
        '--test-file',
        help='Test a single audio file'
    )

    args = parser.parse_args()

    # Load detector
    print("=" * 60)
    print("Alfred Wake Word Detector")
    print("=" * 60)

    detector = PyTorchWakeWordDetector(args.model)

    # Test single file
    if args.test_file:
        print(f"\nTesting file: {args.test_file}")
        score = detector.predict(args.test_file)
        print(f"Confidence score: {score:.3f}")
        if score >= args.threshold:
            print("✓ Wake word detected!")
        else:
            print("✗ Not wake word")

    # Test against dataset
    if args.test:
        detector.test_dataset(args.test_dir, threshold=args.threshold)

    # Live microphone detection
    if args.listen:
        detector.listen_microphone(threshold=args.threshold)

    # If no action specified, show help
    if not (args.test or args.listen or args.test_file):
        print("\n💡 No action specified. Use --help to see options.\n")
        parser.print_help()


if __name__ == '__main__':
    main()
