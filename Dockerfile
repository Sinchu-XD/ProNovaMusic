FROM python:3.11-slim

# Install system deps + Node 20 + FFmpeg
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ffmpeg \
    build-essential \
    gcc \
    python3-dev \
    libffi-dev \
    libssl-dev \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "-m", "Pronova"]
