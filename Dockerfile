FROM python:3.11-slim

# Set working dir
WORKDIR /app

# Install dependencies for building Python packages
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        gcc \
        libffi-dev \
        python3-dev \
        curl \
        gnupg \
        libnss3 \
        libxss1 \
        libasound2 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
        libgbm1 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Copy source code
COPY . .

# ENTRYPOINT nicht festlegen – wir nutzen das über den Cronjob
CMD ["python", "bring_sync.py"]
