#!/usr/bin/env python3
"""
Alfred Wake Word Detector - Master Script
Run all steps or individual steps for wake word training

Usage:
    python run.py --all              # Run complete workflow
    python run.py --step 1           # Record data only
    python run.py --step 2           # Augment data only
    python run.py --step 3           # Train model only
    python run.py --step 4           # Test model only
    python run.py --steps 1,2,3      # Run specific steps
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print("\n" + "=" * 60)
    print(f"{description}")
    print("=" * 60)

    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"\n❌ Error during: {description}")
        sys.exit(1)
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Alfred Wake Word Detector - Master Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete workflow (record → augment → train → test)
  python run.py --all

  # Run individual steps
  python run.py --step 1    # Record data
  python run.py --step 2    # Augment data
  python run.py --step 3    # Train model
  python run.py --step 4    # Test model

  # Run specific sequence
  python run.py --steps 2,3,4    # Augment → Train → Test

  # Pass arguments to specific step
  python run.py --step 3 --args "--epochs 150 --export-onnx"
  python run.py --step 4 --args "--listen --threshold 0.6"

Available Arguments by Step:

  STEP 1 (Record):
    --wake-word WORD         Wake word to record (default: "hey mycroft")
    --mode {wake,not-wake,guided}  Recording mode (default: guided)
    --count COUNT            Number of wake samples (default: 150)
    --duration SECONDS       Duration per recording (default: 3)
    --device INDEX           Audio input device index
    --list-devices           List available audio devices
    --data-dir DIR           Base data directory (default: data)
    --resume                 Resume from existing recordings
    --auto                   Auto-record mode (no Enter key)

  STEP 2 (Augment):
    --data-dir DIR           Data directory (default: data)
    --multiplier N           Augmented versions per file (default: 5)
    --only-wake              Only augment wake-word samples
    --only-not-wake          Only augment not-wake-word samples

  STEP 3 (Train):
    --data-dir DIR           Data directory (default: data)
    --epochs N               Training epochs (default: 100, recommended: 100-150)
    --batch-size N           Batch size (default: 32)
    --lr RATE                Learning rate (default: 0.001)
    --export-onnx            Export to ONNX format for Raspberry Pi

  STEP 4 (Test):
    --model PATH             Model path (default: models/alfred_pytorch.pt)
    --test                   Test against test dataset
    --listen                 Live microphone detection
    --test-dir DIR           Test directory (default: data/test)
    --threshold N            Detection threshold 0-1 (default: 0.5)
    --test-file PATH         Test a single audio file

Common Usage Examples:
  # Record with wake word "Alfred"
  python run.py --step 1 --args "--wake-word Alfred --count 150"

  # Augment 10x
  python run.py --step 2 --args "--multiplier 10"

  # Train with 150 epochs and export ONNX
  python run.py --step 3 --args "--epochs 150 --export-onnx"

  # Test with live microphone at 0.6 threshold
  python run.py --step 4 --args "--listen --threshold 0.6"

  # Complete workflow with custom wake word
  python run.py --step 1 --args "--wake-word Alfred"
  python run.py --steps 2,3,4
        """
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Run complete workflow (all steps)'
    )
    parser.add_argument(
        '--step',
        type=int,
        choices=[1, 2, 3, 4],
        help='Run a specific step (1=record, 2=augment, 3=train, 4=test)'
    )
    parser.add_argument(
        '--steps',
        type=str,
        help='Run specific steps (e.g., "2,3,4" or "1,3")'
    )
    parser.add_argument(
        '--args',
        type=str,
        default='',
        help='Additional arguments to pass to the step script'
    )

    args = parser.parse_args()

    # Determine which steps to run
    steps_to_run = []

    if args.all:
        steps_to_run = [1, 2, 3, 4]
    elif args.step:
        steps_to_run = [args.step]
    elif args.steps:
        try:
            steps_to_run = [int(s.strip()) for s in args.steps.split(',')]
        except ValueError:
            print("❌ Error: --steps must be comma-separated numbers (e.g., '2,3,4')")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)

    # Define step commands
    step_commands = {
        1: {
            'cmd': f'python tools/1_record.py {args.args}',
            'description': 'STEP 1: Record Training Data'
        },
        2: {
            'cmd': f'python tools/2_augment.py {args.args}',
            'description': 'STEP 2: Augment Training Data'
        },
        3: {
            'cmd': f'python tools/3_train.py {args.args}',
            'description': 'STEP 3: Train Wake Word Model'
        },
        4: {
            'cmd': f'python tools/4_test.py {args.args}',
            'description': 'STEP 4: Test Wake Word Model'
        }
    }

    print("\n" + "=" * 60)
    print("Alfred Wake Word Detector")
    print("=" * 60)
    print(f"Running steps: {steps_to_run}")

    # Run each step
    for step in steps_to_run:
        if step not in step_commands:
            print(f"\n❌ Invalid step: {step}")
            continue

        step_info = step_commands[step]
        run_command(step_info['cmd'], step_info['description'])

    print("\n" + "=" * 60)
    print("✓ All steps completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()
