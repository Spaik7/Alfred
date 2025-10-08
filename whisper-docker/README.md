# Whisper Docker API

A Flask-based Whisper transcription API that runs in Docker. Supports English and Italian language detection.

## Quick Start

### Build with default model (turbo)
```bash
cd whisper-docker
docker build -t whisper-api .
docker run -d -p 9999:9999 --name whisper whisper-api
```

## Choose Whisper Model During Build

You can select which Whisper model to use by passing the `WHISPER_MODEL` build argument:

### Available Models

| Model    | Size    | Speed       | Accuracy | RAM Usage | Best For |
|----------|---------|-------------|----------|-----------|----------|
| `tiny`   | ~75MB   | Very Fast   | Low      | ~1GB      | Testing, low-end devices |
| `base`   | ~150MB  | Fast        | Good     | ~1GB      | Development, Raspberry Pi |
| `small`  | ~500MB  | Moderate    | Better   | ~2GB      | Balanced accuracy/speed |
| `medium` | ~1.5GB  | Slow        | High     | ~5GB      | High accuracy needed |
| `large`  | ~3GB    | Very Slow   | Highest  | ~10GB     | Best accuracy, powerful hardware |
| `turbo`  | ~800MB  | Fast        | High     | ~3GB      | **Default - best balance** |

### Build Examples

```bash
# Build with tiny model (fastest, lowest accuracy)
docker build --build-arg WHISPER_MODEL=tiny -t whisper-api:tiny .

# Build with base model (good for Raspberry Pi)
docker build --build-arg WHISPER_MODEL=base -t whisper-api:base .

# Build with small model (balanced)
docker build --build-arg WHISPER_MODEL=small -t whisper-api:small .

# Build with medium model (high accuracy)
docker build --build-arg WHISPER_MODEL=medium -t whisper-api:medium .

# Build with turbo model (default - recommended)
docker build --build-arg WHISPER_MODEL=turbo -t whisper-api:turbo .
```

### Run Container

```bash
# Run with default settings
docker run -d -p 9999:9999 --name whisper whisper-api:turbo

# Run with custom port
docker run -d -p 8080:9999 --name whisper whisper-api:turbo

# Run with logs visible
docker run -p 9999:9999 --name whisper whisper-api:turbo
```

## API Usage

### Endpoint: `/audio`

**Method:** `POST`

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file`: Audio file (WAV format recommended)

**Response:**
```json
{
  "success": true,
  "transcription": "your transcribed text here"
}
```

### Test the API

```bash
# From command line
curl -X POST -F "file=@test.wav" http://localhost:9999/audio

# Python example
import requests

with open("audio.wav", "rb") as f:
    response = requests.post("http://localhost:9999/audio", files={"file": f})
    result = response.json()
    print(result["transcription"])
```

## Features

- **Language Detection:** Automatically detects English or Italian
- **Language Whitelist:** Only processes English/Italian, forces fallback otherwise
- **Automatic Cleanup:** Removes uploaded files after transcription
- **Pre-downloaded Model:** Model is downloaded during build, not at runtime

## Configuration

### Supported Languages

By default, only English and Italian are supported. To add more languages, edit `app.py` on line 10:
```bash
LANGUAGE_WHITELIST = ["en", "it"]
```

```python
LANGUAGE_WHITELIST = ["en", "it", "es", "fr"]  # Add your languages
```

### Change Port

Edit the `Dockerfile` or override when running:
```bash
docker run -d -p 8888:9999 --name whisper whisper-api
```

## Docker Management

```bash
# View logs
docker logs whisper

# Stop container
docker stop whisper

# Remove container
docker rm whisper

# Remove image
docker rmi whisper-api:turbo
```

## Integration with Alfred

In `alfred.py`, configure Docker mode:

```bash
# Use Docker Whisper with default IP
python alfred.py -w docker

# Use Docker Whisper with custom IP
python alfred.py -w docker -d 192.168.1.10:9999
```

## Hardware Requirements

| Model  | Minimum RAM | Recommended CPU | Disk Space |
|--------|-------------|-----------------|------------|
| tiny   | 1GB         | 1 core          | 200MB      |
| base   | 1GB         | 2 cores         | 300MB      |
| small  | 2GB         | 2 cores         | 700MB      |
| medium | 5GB         | 4 cores         | 2GB        |
| large  | 10GB        | 8 cores         | 4GB        |
| turbo  | 3GB         | 4 cores         | 1.2GB      |

## Troubleshooting

**Container won't start:**
- Check if port 9999 is already in use: `lsof -i :9999`
- View logs: `docker logs whisper`

**Out of memory:**
- Use a smaller model (tiny or base)
- Increase Docker's memory limit

**Slow transcription:**
- Use a smaller/faster model (tiny or base)
- Check CPU usage: `docker stats whisper`

**Model not found:**
- Rebuild the image - model should download during build
- Check internet connection during build

## Development

### Local Testing (without Docker)

```bash
cd whisper-docker
pip install -r requirement.txt
python app.py
```

The API will run at `http://localhost:9999`

### Rebuild After Changes

```bash
docker stop whisper
docker rm whisper
docker build -t whisper-api .
docker run -d -p 9999:9999 --name whisper whisper-api
```

## Performance Comparison

On a Raspberry Pi 4 (4GB RAM):
- **tiny:** ~2 seconds per 5-second audio
- **base:** ~5 seconds per 5-second audio
- **small:** ~15 seconds per 5-second audio
- **turbo:** Not recommended (too slow)

On a standard PC (8GB RAM, i5):
- **turbo:** ~1 second per 5-second audio
- **medium:** ~3 seconds per 5-second audio
- **large:** ~8 seconds per 5-second audio

## Recommended Setups

**Raspberry Pi 4:**
```bash
docker build --build-arg WHISPER_MODEL=base -t whisper-api:base .
docker run -d -p 9999:9999 --name whisper whisper-api:base
```

**Desktop/Server:**
```bash
docker build --build-arg WHISPER_MODEL=turbo -t whisper-api:turbo .
docker run -d -p 9999:9999 --name whisper whisper-api:turbo
```

**Cloud/High Performance:**
```bash
docker build --build-arg WHISPER_MODEL=medium -t whisper-api:medium .
docker run -d -p 9999:9999 --name whisper whisper-api:medium
```
