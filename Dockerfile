FROM python:3.13-slim

# Install system dependencies + Node.js 20
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ffmpeg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest \
    && rm -rf /var/lib/apt/lists/*

# Verify installations (optional but useful for debugging)
RUN node -v && npm -v && ffmpeg -version

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Upgrade pip
RUN pip install --upgrade pip

# Install python dependencies
RUN pip install -r requirements.txt

# Start bot
CMD ["python3", "-m", "Pronova"]
