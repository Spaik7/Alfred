# Jarvis - Custom Wake Word Voice Assistant

A voice-activated assistant with custom wake word detection using Mycroft Precise. The system listens for a wake word ("Hey Alfred") and will transcribe voice commands locally (currently in development/testing phase).

## Features

- **Custom Wake Word Detection**: Train your own wake word using Mycroft Precise
- **Local Processing**: Fully local speech recognition (in development)
- **Real-time Audio Processing**: Continuous listening with efficient MFCC feature extraction
- **Memory Optimized**: Garbage collection for low-resource environments (Raspberry Pi compatible)
- **Complete Training Pipeline**: End-to-end tools for recording, training, and testing

## Project Structure

```
jarvis/
├── alfred.py              # Main voice assistant runtime
├── precise_recorder.py    # Audio recording tool for dataset collection
├── precise_trainer.py     # Model training pipeline
├── precise_test.py        # Model testing/listening tool
├── dataset.py             # Dataset utilities
├── WWD.h5                 # Trained wake word detection model
├── models/                # Trained model storage
├── precise_data/          # Training data directory
│   ├── train/
│   │   ├── wake-word/
│   │   └── not-wake-word/
│   └── test/
│       ├── wake-word/
│       └── not-wake-word/
└── myvenv/                # Python virtual environment
```

## Installation

### Prerequisites

- Python 3.11+
- Microphone input device

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Spaik7/Alfred.git
cd jarvis
```

2. Create and activate virtual environment:
```bash
python3 -m venv myvenv
source myvenv/bin/activate  # On Windows: myvenv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. **Fix Mycroft Precise compatibility** (required for TensorFlow 2.x):

Edit `myvenv/lib/python3.11/site-packages/precise/model.py` and replace lines 66-68:

**Old code (lines 66-68):**
```python
from keras.layers.core import Dense
from keras.layers.recurrent import GRU
from keras.models import Sequential
```

**New code:**
```python
from tensorflow.keras.layers import Dense, GRU
from tensorflow.keras.models import Sequential
```

> **Note:** This fixes compatibility issues with TensorFlow 2.x by using the updated import paths.

## Usage

### 1. Training a Custom Wake Word

#### Step 1: Setup Directory Structure
```bash
python precise_trainer.py "Name" --step setup
```
Replace "Name" with the Wake up Word/phrase you want to use 
I used "Alfred", you could use anything like "hey Jesus" or "hey Pi" or single word like i did


#### Step 2: Record Audio Samples

**Guided Recording (Recommended)**
```bash
python precise_recorder.py --wake-word "Alfred"
```

This will guide you through recording:
- 150 wake word samples (saying "Alfred")
- 300 not-wake-word samples (random speech/noise)

With 150 sample should be good, by default is set to 50, but you could run into some problem with the trainer/test with few sample

**Manual Recording Options**
```bash
# Display help message for instruction
python precise_recorder.py -h 

# Record only wake word samples
python precise_recorder.py --mode wake --count 150

# Record only not-wake-word samples
python precise_recorder.py --mode not-wake --count 300

# List audio devices
python precise_recorder.py --list-devices

# Use specific device
python precise_recorder.py --wake-word "Alfred" --device 2

# Resume previous session
python precise_recorder.py --wake-word "Alfred" --resume
```

#### Step 3: Train the Model
```bash
# Full training pipeline (60 epochs)
python precise_trainer.py "Alfred"

# Custom epochs
python precise_trainer.py "Alfred" --epochs 100

# Incremental training on existing model
python precise_trainer.py "Alfred" --incremental

# Only train (skip testing)
python precise_trainer.py "Alfred" --step train
```

#### Step 4: Test the Model
```bash
# Test with audio files
python precise_trainer.py "Alfred" --step test

# Live microphone testing
python precise_test.py models/alfred.net

# Custom threshold
python precise_test.py models/alfred.net --threshold 0.7
```

**Advice**
Use the custom threshold and test the model to see how much it work and then implement it to the code 

### 2. Running the Voice Assistant

```bash
python alfred.py
```

**On startup:**
1. Select your audio input device from the list
2. The model will load with a progress indicator
3. Start speaking your wake word

**Configuration (edit `alfred.py`):**
```python
duration = 1.5           # Wake word listening window (seconds)
fs = 48000               # Sample rate
wake_word_name = "Alfred"
wake_threshold = 0.9     # Detection sensitivity (0.0-1.0)
```

### 3. Workflow Example

Complete workflow for creating your assistant:

```bash
# 1. Setup directories
python precise_trainer.py "Alfred" --step setup

# 2. Record samples
python precise_recorder.py --wake-word "Alfred"

# 3. Train model
python precise_trainer.py "Alfred"

# 4. Test model
python precise_test.py models/alfred.net

# 5. Run assistant
python alfred.py
```

## Audio Requirements

### Recording Specifications
- **Sample Rate**: 16kHz (automatically converted from 48kHz)
- **Channels**: Mono (1 channel)
- **Format**: 16-bit WAV
- **Duration**: 3 seconds per sample (default)

### Recommended Dataset Size
- **Minimum**: 50 wake word + 100 not-wake-word samples
- **Recommended**: 150 wake word + 300 not-wake-word samples
- **Optimal**: 500+ wake word + 1000+ not-wake-word samples

### Tips for Better Accuracy
1. Record in different environments (quiet, noisy, echo)
1.1 Do 70% of Wake up recording into quiet environments and 30% with something
    playing (music, tv, people talking)
    
    So on the 150 sample that i reccomend: 
    Clean/Quiet Samples (70% = 105 total)

    Train: ~90 samples (clean, quiet room)
    Test: ~15 samples (clean, quiet room)

    Noisy Samples (30% = 45 total)

    Train: ~38 samples (with music/TV/background noise) \n
    Test: ~7 samples (with music/TV/background noise)

    Samples 1-90: Quiet room, various volumes/speeds
    
    Samples 91-128: Turn on music/TV, record with background noise
    
    Samples 129-144: Test set - quiet (these go to test folder automatically)
    
    Samples 145-150: Test set - noisy (these go to test folder automatically)
2. Vary your speaking speed and tone
3. Include similar-sounding words in not-wake-word samples
4. Record background noise (TV, music, conversations)
5. Use 15% of data for testing (automatically split)

## Model Performance

The trained model (`WWD.h5`) uses MFCC features and a neural network for classification:
- **Input**: 40 MFCC coefficients
- **Architecture**: Deep neural network with custom weighted loss
- **Threshold**: Configurable (default 0.9 for high precision)
- **Latency**: ~100ms detection time

## Troubleshooting

### Model not detecting wake word
- Lower the `wake_threshold` in `alfred.py` (try 0.7 or 0.8)
- Record more diverse training samples
- Check microphone input levels

### Microphone issues
```bash
# List available devices
python precise_recorder.py --list-devices

# Test specific device
python precise_recorder.py --wake-word "test" --device 1
```

### Training fails
- Ensure Mycroft Precise is installed: `pip install mycroft-precise`
- Verify you have enough training samples (50+ wake, 100+ not-wake)
- Check audio files are valid WAV format

## Hardware Compatibility

### Tested On
- Raspberry Pi 4 (4GB RAM)
- Linux systems with standard audio input
- Python 3.11 on ARM/x64 architectures

### Memory Optimization
The code includes garbage collection for Raspberry Pi:
```python
gc.collect()  # Called after audio processing
```

## Development

### File Descriptions

**alfred.py**
- Main runtime for wake word detection
- Continuous audio monitoring
- Local speech recognition (in development)

**precise_recorder.py**
- Interactive recording tool
- Auto-resampling from 48kHz to 16kHz
- Guided workflow for dataset creation

**precise_trainer.py**
- Complete training pipeline
- Directory management
- Model testing and conversion

**precise_test.py**
- Live microphone testing
- Custom loss function handling
- Real-time confidence visualization

## Command Line Options

### precise_recorder.py
```
usage: precise_recorder.py [-h] [--wake-word WAKE_WORD]
                           [--mode {wake,not-wake,guided}] [--count COUNT]
                           [--duration DURATION] [--device DEVICE]
                           [--list-devices] [--data-dir DATA_DIR] [--resume]

Record audio samples for Mycroft Precise training

optional arguments:
  -h, --help            show this help message and exit
  --wake-word WAKE_WORD
                        Wake word phrase (for guided mode)
  --mode {wake,not-wake,guided}
                        Recording mode (default: guided)
  --count COUNT, -c COUNT
                        Number of wake word samples to record (default: 150).
                        In guided mode, not-wake samples will be 2x this.
  --duration DURATION, -d DURATION
                        Duration of each recording in seconds (default: 3)
  --device DEVICE, -i DEVICE
                        Audio input device index (use --list-devices to see options)
  --list-devices        List available audio devices and exit
  --data-dir DATA_DIR   Base directory for data (default: precise_data)
  --resume, -r          Resume from existing recordings
```

### precise_trainer.py
```
usage: precise_trainer.py [-h] [--epochs EPOCHS]
                          [--step {setup,train,test,convert,all}]
                          [--incremental] [--data-dir DATA_DIR]
                          wake_word

Mycroft Precise Wake Word Training Pipeline

positional arguments:
  wake_word             Name of your wake word (e.g., "hey mycroft")

optional arguments:
  -h, --help            show this help message and exit
  --epochs EPOCHS, -e EPOCHS
                        Number of training epochs (default: 60)
  --step {setup,train,test,convert,all}
                        Run specific step or full pipeline (default: all)
  --incremental, -i     Use incremental training on existing model
  --data-dir DATA_DIR   Base directory for data (default: precise_data)
```

### precise_test.py
```
usage: precise_test.py [-h] [--threshold THRESHOLD] [--trigger-level TRIGGER_LEVEL]
                       [--chunk-size CHUNK_SIZE] [--recording-rate RECORDING_RATE]
                       model

Listen for Mycroft Precise wake word

positional arguments:
  model                 Path to .net model file

optional arguments:
  -h, --help            show this help message and exit
  --threshold THRESHOLD, -t THRESHOLD
                        Detection threshold (default: 0.5)
  --trigger-level TRIGGER_LEVEL, -l TRIGGER_LEVEL
                        Number of activations needed (default: 3)
  --chunk-size CHUNK_SIZE, -c CHUNK_SIZE
                        Audio chunk size (default: 2048)
  --recording-rate RECORDING_RATE, -r RECORDING_RATE
                        Microphone sample rate (default: 48000)
```

## License

[Add your license here]

## Acknowledgments

- [Mycroft Precise](https://github.com/MycroftAI/mycroft-precise) - Wake word detection engine
- Inspired by Jarvis/ALFRED AI assistants

## Contributing

Contributions welcome! Please submit pull requests or open issues for bugs and feature requests.

## Future Enhancements

- [ ] Intent recognition and command execution
- [ ] Multi-language support
- [ ] Cloud-based training option
- [ ] Web interface for configuration
- [ ] Mobile app integration
