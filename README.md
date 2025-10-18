# 🤖 Alfred - Your Personal Voice Assistant

**A British Butler in Your Raspberry Pi**

**Phase 1: ✅ COMPLETE** | Production Ready | 16 Intents Implemented

Train a custom "Alfred" wake word detector optimized for Raspberry Pi. Tiny model (~32KB), 100% accuracy, works offline.

---

## What You'll Do

1. **Record** your voice saying "Alfred" 150 times
2. **Record** background noise/speech 300 times
3. **Augment** data to create 5x more samples
4. **Train** the model (~15 minutes)
5. **Setup** Whisper (local or Docker)
6. **Run** Alfred assistant with wake word detection!

That's it!

---

## Quick Start (One Command)

```bash
# Setup
cd ~/jarvis
python3 -m venv myvenv
source myvenv/bin/activate
pip install -r requirements.txt

# Run complete workflow
python run.py --all
```

Or run individual steps:
```bash
python run.py -s 1    # Record
python run.py -s 2    # Augment
python run.py -s 3    # Train
python run.py -s 4    # Test
```

Then run Alfred:
```bash
python alfred.py    # Start the assistant
```

---

## Setup

```bash
# 1. Install
cd ~/jarvis
python3 -m venv myvenv
source myvenv/bin/activate
pip install -r requirements.txt

# 2. Create directories (optional - auto-created)
mkdir -p data/{train,test}/{wake-word,not-wake-word}
mkdir -p models
```

---

## Step-by-Step Guide

### Step 1: Record Training Data

**Using master script:**
```bash
python run.py --step 1
```

**Or directly:**
```bash
python tools/1_record.py --wake-word "Alfred" --count 150
```

**What happens:**
- Say "Alfred" 150 times (it prompts you)
- Say random words/make noise 300 times
- Press Enter between each sample
- Auto-splits into train/test sets

**Tips:**
- 70% quiet environment, 30% with background noise
- Vary your tone, speed, and volume
- For background samples: talk, play music, make noise

**Resume if interrupted:**
```bash
python tools/1_record.py --wake-word "Alfred" --resume
```

**Auto mode (no Enter key):**
```bash
python tools/1_record.py --wake-word "Alfred" --auto
```

---

### Step 2: Augment Data

**Using master script:**
```bash
python run.py --step 2
```

**Or directly:**
```bash
# Create 5x more samples (default)
python tools/2_augment.py

# Create 10x more samples
python tools/2_augment.py --multiplier 10

# Only augment wake word samples
python tools/2_augment.py --only-wake
```

**What it does:**
- Takes your 128 wake samples → creates 640 more
- Applies: noise, pitch shift, speed change, volume change
- Gives you more training data without recording

---

### Step 3: Train the Model

**Using master script:**
```bash
python run.py --step 3
```

**Or directly:**
```bash
# Basic training (100 epochs, ~15 minutes)
python tools/3_train.py

# More epochs for better accuracy
python tools/3_train.py --epochs 150

# Export for Raspberry Pi deployment
python tools/3_train.py --epochs 100 --export-onnx
```

**Pass arguments through master script:**
```bash
python run.py --step 3 --args "--epochs 150 --export-onnx"
```

**Expected output:**
```
Epoch 100/100 - Train Acc: 99.11%, Test Acc: 100.00%
✓ Training completed!
Model saved to: models/alfred_pytorch.pt
```

---

### Step 4: Test the Model

**Using master script:**
```bash
python run.py --step 4
```

**Or directly:**
```bash
# Test against your test dataset
python tools/4_test.py --test

# Live microphone test
python tools/4_test.py --listen

# Both
python tools/4_test.py --test --listen
```

**Pass arguments through master script:**
```bash
python run.py --step 4 --args "--listen --threshold 0.6"
```

**Expected results:**
```
Wake word detection:     100.00% (22/22)
Not-wake rejection:      100.00% (45/45)
Overall accuracy:        100.00%
```

---

### Step 5: Adjust Sensitivity (Optional)

```bash
# Default threshold (balanced)
python tools/4_test.py --listen --threshold 0.5

# More strict (fewer false positives)
python tools/4_test.py --listen --threshold 0.7

# More sensitive (catches more)
python tools/4_test.py --listen --threshold 0.3
```

---

## Run Multiple Steps

```bash
# Augment → Train → Test
python run.py -m 2,3,4

# Record → Train (skip augmentation)
python run.py -m 1,3

# Complete workflow
python run.py -a
```

---

## Complete Command Reference

### Master Script (run.py)

```bash
python run.py [--all | --step N | --steps N,N,N] [--args "arguments"]
```

**Options:**
- `--all` - Run complete workflow (steps 1-4)
- `--step N` - Run a specific step (1-4)
- `--steps N,N,N` - Run specific steps (e.g., "2,3,4")
- `--args "..."` - Pass arguments to the step script

---

### Step 1: Record (tools/1_record.py)

**All Arguments:**
```bash
--wake-word WORD         # Wake word to record (default: "hey mycroft")
--mode MODE              # Recording mode: wake, not-wake, guided (default: guided)
--count N                # Number of wake samples (default: 150)
--duration N             # Duration per recording in seconds (default: 3)
--device INDEX           # Audio input device index
--list-devices           # List available audio devices
--data-dir DIR           # Base data directory (default: data)
--resume                 # Resume from existing recordings
--auto                   # Auto-record mode (no Enter key)
```

**Examples:**
```bash
# Basic recording with custom wake word
python run.py --step 1 --args "--wake-word Alfred --count 150"

# List audio devices
python tools/1_record.py --list-devices

# Resume interrupted recording
python tools/1_record.py --wake-word Alfred --resume

# Auto-record mode (no Enter key)
python tools/1_record.py --wake-word Alfred --auto

# Only record wake word samples
python tools/1_record.py --mode wake --count 200

# Only record not-wake samples
python tools/1_record.py --mode not-wake --count 400
```

---

### Step 2: Augment (tools/2_augment.py)

**All Arguments:**
```bash
--data-dir DIR           # Data directory (default: data)
--multiplier N           # Augmented versions per file (default: 5)
--only-wake              # Only augment wake-word samples
--only-not-wake          # Only augment not-wake-word samples
```

**Examples:**
```bash
# Create 5x more samples (default)
python run.py --step 2

# Create 10x more samples
python run.py --step 2 --args "--multiplier 10"

# Only augment wake word samples
python tools/2_augment.py --only-wake --multiplier 8

# Only augment not-wake samples
python tools/2_augment.py --only-not-wake --multiplier 3

# Custom data directory
python tools/2_augment.py --data-dir my_data --multiplier 5
```

---

### Step 3: Train (tools/3_train.py)

**All Arguments:**
```bash
--data-dir DIR           # Data directory (default: data)
--epochs N               # Training epochs (default: 100, recommended: 100-150)
--batch-size N           # Batch size (default: 32)
--lr RATE                # Learning rate (default: 0.001)
--export-onnx            # Export to ONNX format for Raspberry Pi
```

**Examples:**
```bash
# Basic training
python run.py --step 3

# Train with 150 epochs
python run.py --step 3 --args "--epochs 150"

# Train and export ONNX
python run.py --step 3 --args "--epochs 100 --export-onnx"

# Custom learning rate and batch size
python tools/3_train.py --epochs 100 --lr 0.0005 --batch-size 64

# Custom data directory
python tools/3_train.py --data-dir my_data --epochs 120
```

---

### Step 4: Test (tools/4_test.py)

**All Arguments:**
```bash
--model PATH             # Model path (default: models/alfred_pytorch.pt)
--test                   # Test against test dataset
--listen                 # Live microphone detection
--test-dir DIR           # Test directory (default: data/test)
--threshold N            # Detection threshold 0-1 (default: 0.5)
--test-file PATH         # Test a single audio file
```

**Examples:**
```bash
# Test against dataset
python run.py --step 4 --args "--test"

# Live microphone detection
python run.py --step 4 --args "--listen"

# Both dataset and live
python tools/4_test.py --test --listen

# Custom threshold (more strict)
python tools/4_test.py --listen --threshold 0.7

# Custom threshold (more sensitive)
python tools/4_test.py --listen --threshold 0.3

# Test single audio file
python tools/4_test.py --test-file data/test/wake-word/sample_0001.wav

# Custom model
python tools/4_test.py --model models/my_model.pt --listen
```

---

## Running Alfred (Main Assistant)

After training your model, use `alfred.py` to run the full voice assistant with wake word detection and command transcription.

### Quick Start

```bash
# Use Docker Whisper (default)
python alfred.py

# Use local Whisper
python alfred.py -w local

# Custom settings
python alfred.py -t 0.95 -st 3.0 -s 0.02
```

### All Command Line Arguments

```bash
# Whisper Configuration
-w, --whisper          # Whisper mode: local or docker (default: docker)
-d, --docker-ip        # Docker API IP:PORT (default: 192.168.1.5:9999)
-wm, --whisper-model   # Model for local mode: tiny, base, small, medium, large (default: base)

# Wake Word Detection
-t, --threshold        # Wake detection threshold 0-1 (default: 0.98, lower = more sensitive)

# Voice Activity Detection (VAD)
-s, --silence-threshold    # Audio energy threshold for silence detection (default: 0.01)
                           # Lower (0.005) = detects silence faster
                           # Higher (0.05) = waits for louder silence, good for noisy rooms

-st, --silence-duration    # Seconds of silence before stopping recording (default: 2.0)
                           # Increase if your speech has long pauses
```

### Usage Examples

**Basic usage:**
```bash
# Docker Whisper (default)
python alfred.py

# Local Whisper with base model
python alfred.py -w local

# Local Whisper with faster model
python alfred.py -w local -wm tiny

# Local Whisper with better accuracy
python alfred.py -w local -wm medium
```

**Adjust wake word sensitivity:**
```bash
# More sensitive (catches more, may have false positives)
python alfred.py -t 0.9

# More strict (fewer false positives)
python alfred.py -t 0.98
```

**Adjust silence detection:**
```bash
# Quick response (stops after 1.5s of silence)
python alfred.py -st 1.5

# Wait longer (good for speech with pauses)
python alfred.py -st 3.5

# Noisier environment (higher threshold)
python alfred.py -s 0.03 -st 2.5

# Quiet environment (lower threshold)
python alfred.py -s 0.005 -st 2.0
```

**Combined settings:**
```bash
# Balanced setup
python alfred.py -w local -wm small -t 0.95 -s 0.015 -st 2.5

# Fast response setup
python alfred.py -w local -wm tiny -t 0.9 -st 1.5

# Accurate setup
python alfred.py -w local -wm medium -t 0.98 -st 3.0
```

### How It Works

1. **Continuous Listening:** Records 1.5s audio chunks at 48kHz
2. **Wake Word Detection:** Resamples to 16kHz, extracts MFCC features, runs through ONNX model
3. **Voice Command:** When wake word detected, records until silence (VAD)
4. **Transcription:** Sends audio to Whisper (local or Docker)
5. **Output:** Displays transcribed command

**Configuration Display:**
```
🤖 Alfred is ready!
Configuration:
  Wake threshold: 0.98
  Whisper mode: local
  Whisper model: base
  Silence threshold: 0.01 (audio energy level)
  Silence duration: 2.0s (continuous silence to stop)

Say 'Hey Alfred' to wake me up.
```

---

## Whisper Setup

Alfred supports two Whisper modes for command transcription:

### Option 1: Local Whisper (Simpler)

**Install:**
```bash
pip install openai-whisper
```

**Use:**
```bash
python alfred.py -w local -wm base
```

**Models:**
- `tiny` - Fastest, lowest accuracy (~1GB RAM, ~2s per 5s audio on RPi4)
- `base` - Good balance (~1GB RAM, ~5s per 5s audio on RPi4)
- `small` - Better accuracy (~2GB RAM, ~15s per 5s audio on RPi4)
- `medium` - High accuracy (~5GB RAM, too slow for RPi)
- `large` - Best accuracy (~10GB RAM, not for RPi)

### Option 2: Docker Whisper (Better Performance)

Docker provides better performance and isolation. See `whisper-docker/` directory.

**Build with default model (turbo):**
```bash
cd whisper-docker
docker build -t whisper-api .
docker run -d -p 9999:9999 --name whisper whisper-api
```

**Build with custom model:**
```bash
# For Raspberry Pi (use base model)
docker build --build-arg WHISPER_MODEL=base -t whisper-api:base .
docker run -d -p 9999:9999 --name whisper whisper-api:base

# For desktop/server (use turbo model)
docker build --build-arg WHISPER_MODEL=turbo -t whisper-api:turbo .
docker run -d -p 9999:9999 --name whisper whisper-api:turbo

# For high accuracy (use medium model)
docker build --build-arg WHISPER_MODEL=medium -t whisper-api:medium .
docker run -d -p 9999:9999 --name whisper whisper-api:medium
```

**Use with Alfred:**
```bash
# Local Docker
python alfred.py -w docker

# Remote Docker
python alfred.py -w docker -d 192.168.1.10:9999
```

**See `whisper-docker/README.md` for complete Docker documentation.**

---

## Deploy to Raspberry Pi

### Copy Files
```bash
# Copy model and library
scp models/alfred_pytorch.pt pi@raspberrypi:~/
scp -r tools/lib pi@raspberrypi:~/
```

### On Raspberry Pi
```bash
# Install dependencies
pip install torch librosa pyaudio numpy

# Run detector (copy a test script or use the library)
python -c "
from lib.detector import PyTorchWakeWordDetector
detector = PyTorchWakeWordDetector('alfred_pytorch.pt')
detector.listen_microphone(threshold=0.5)
"
```

### Or Use ONNX (Faster)
```bash
# Export on your computer
python tools/3_train.py --export-onnx

# Copy to RPi
scp models/alfred.onnx pi@raspberrypi:~/

# On RPi
pip install onnxruntime librosa pyaudio
# Use with onnxruntime for faster inference
```

---

## Use in Your Code

```python
import sys
sys.path.insert(0, 'tools')
from lib.detector import PyTorchWakeWordDetector

# Load detector
detector = PyTorchWakeWordDetector('models/alfred_pytorch.pt')

# Check a file
score = detector.predict('audio.wav')
if score > 0.5:
    print("Wake word detected!")

# Live detection
detector.listen_microphone(threshold=0.5)
```

---

## Quick Reference

### Training Workflow

```bash
# Complete workflow (short flags)
python run.py -a

# Individual steps (short flags)
python run.py -s 1              # Record
python run.py -s 2              # Augment
python run.py -s 3              # Train
python run.py -s 4              # Test

# With custom arguments
python run.py -s 3 --args "-e 150 -o"
python run.py -s 4 --args "-l -s 0.6"

# Multiple steps
python run.py -m 2,3,4          # Augment → Train → Test
```

### Running Alfred

```bash
# Basic (Docker Whisper)
python alfred.py

# Local Whisper
python alfred.py -w local -wm base

# Custom settings (short flags)
python alfred.py -t 0.95 -st 3.0 -s 0.015

# Full example
python alfred.py -w local -wm small -t 0.95 -s 0.015 -st 2.5
```

**Note:** All scripts support single-letter short flags (e.g., `-t` instead of `--threshold`). Use `-h` for help on any script.

---

## Troubleshooting

**Poor accuracy?**
- Collect more diverse not-wake samples
- Train more epochs: `python tools/3_train.py --epochs 150`
- Augment more: `python tools/2_augment.py --multiplier 10`
- Adjust threshold: `python tools/4_test.py --listen --threshold 0.6`

**Audio errors?**
- ALSA warnings are normal, ignore them
- Script handles 48kHz → 16kHz resampling automatically

**Model not learning?**
- Verify you have both wake and not-wake samples in `data/train/`
- Check audio files are valid WAV format
- Ensure directory structure is correct

**Import errors?**
- Make sure you're in the project root directory
- Activate virtual environment: `source myvenv/bin/activate`

---

## Project Structure

```
jarvis/
├── alfred.py               # Main assistant script (wake word + Whisper)
├── run.py                  # Master script - runs all training steps
├── tools/                  # All training/testing scripts
│   ├── 1_record.py        # Record training data
│   ├── 2_augment.py       # Create more samples
│   ├── 3_train.py         # Train the model
│   ├── 4_test.py          # Test the model
│   └── lib/               # Core libraries
│       ├── trainer.py     # Model architecture
│       └── detector.py    # Detection logic
├── whisper-docker/         # Docker setup for Whisper API
│   ├── Dockerfile         # Multi-model Docker build
│   ├── app.py             # Flask API server
│   ├── requirement.txt    # Python dependencies
│   └── README.md          # Docker documentation
├── data/                   # Your training data
│   ├── train/
│   │   ├── wake-word/
│   │   └── not-wake-word/
│   └── test/
│       ├── wake-word/
│       └── not-wake-word/
├── models/                 # Trained models
│   ├── alfred_pytorch.pt  # PyTorch model
│   └── alfred.onnx        # ONNX model (optimized)
├── archived/               # Old broken files (safe to delete)
├── requirements.txt        # Dependencies
└── README.md              # This file
```

---

## Model Details

- **Architecture:** CNN + GRU
- **Size:** ~32KB (60x smaller than alternatives)
- **Accuracy:** 95-100% with good data
- **Speed:** <20ms on Raspberry Pi 4
- **Features:** Automatic 5x data augmentation during training

---

## Archived Folder

The `archived/` directory contains old Mycroft Precise files that didn't work:
- Old broken trainer (32% accuracy vs our 100%)
- Old test scripts (TensorFlow 1.x incompatibility)
- Previous model files

See `archived/README.md` for details. **You can delete this folder if you want.**

---

## Support

Issues? Check:
1. Virtual environment active: `source myvenv/bin/activate`
2. Dependencies installed: `pip install -r requirements.txt`
3. Running from project root directory
4. Directory structure correct (`data/train/`, `data/test/`)
5. Audio files are valid WAV format

---

## Short Flags Reference

All scripts support single-letter short flags for convenience:

### alfred.py (Main Assistant)
- `-w` = `--whisper` (mode)
- `-d` = `--docker-ip`
- `-wm` = `--whisper-model`
- `-t` = `--threshold`
- `-s` = `--silence-threshold`
- `-st` = `--silence-duration`

### run.py (Master Script)
- `-a` = `--all`
- `-s` = `--step`
- `-m` = `--steps`

### 1_record.py
- `-w` = `--wake-word`
- `-m` = `--mode`
- `-c` = `--count`
- `-d` = `--duration`
- `-i` = `--device`
- `-l` = `--list-devices`
- `-r` = `--resume`
- `-a` = `--auto`

### 2_augment.py
- `-m` = `--multiplier`
- `-w` = `--only-wake`
- `-n` = `--only-not-wake`

### 3_train.py
- `-e` = `--epochs`
- `-b` = `--batch-size`
- `-l` = `--lr`
- `-o` = `--export-onnx`

### 4_test.py
- `-m` = `--model`
- `-t` = `--test`
- `-l` = `--listen`
- `-d` = `--test-dir`
- `-s` = `--threshold`
- `-f` = `--test-file`

Use `-h` on any script for full help and examples!

---

Built with PyTorch, Librosa, and custom CNN+GRU architecture.
Optimized for Raspberry Pi deployment.

Happy wake word detecting! 🎙️

---

## 📚 Documentation

- **[ROADMAP.md](ROADMAP.md)** - Development phases and progress tracker
- **[PROBLEMS.md](PROBLEMS.md)** - Known issues and future enhancements  
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[README.md](README.md)** - This file - setup and quick start

---

## 🎯 Current Status

**Phase 1: Complete ✅**

- Wake word detection
- Voice transcription (Whisper)
- Intent parsing (36 intents defined, 16 implemented)
- Template responses with British butler personality
- AI responses for weather and general chat
- Concatenation detection for multi-part queries
- Context management for follow-up questions
- Bilingual support (English & Italian)

**Implemented Intents (16):**
- Templates (8): Time, Date, Volume×3, Calculate, Joke, System Status
- AI (2): Weather, General Chat
- Special (6): News, Finance, Recipes, Transport

**Next:** Phase 2 - Mac Integration via SSH

---

## ⚡ Quick Examples

```bash
# Wake word
"Hey Alfred"

# Templates (instant)
"What time is it?"
"Che ore sono?"
"Set volume to 75"
"How's the Pi doing?"

# AI responses
"What's the weather?"
"Che tempo fa?"
"Hello"

# Concatenation (NEW!)
"Che tempo fa e che ore sono?"
"What's the weather and what's the news?"

# Complex queries (NEW!)
"What should I wear today?"
```

---
