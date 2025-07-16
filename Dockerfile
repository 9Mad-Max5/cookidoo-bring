FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        gnupg \
        ca-certificates \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libc6 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        xdg-utils \
        libu2f-udev \
        libvulkan1 \
        unzip \
        && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright + browser binaries
RUN pip install playwright && \
    playwright install --with-deps

# Copy project files
COPY . .

# Default CMD
CMD ["python", "bring_sync.py"]
