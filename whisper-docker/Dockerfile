FROM python:3.11-slim

# Build argument for Whisper model selection
# Options: tiny, base, small, medium, large, turbo (default: turbo)
ARG WHISPER_MODEL=turbo

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    wget \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirement.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirement.txt

# Copy app code
COPY . /app

# Pre-download the Whisper model during build
# This saves time on first container startup
RUN python -c "import whisper; whisper.load_model('${WHISPER_MODEL}')"

# Store model name as environment variable
ENV WHISPER_MODEL=${WHISPER_MODEL}

EXPOSE 9999
CMD ["python", "app.py"]
