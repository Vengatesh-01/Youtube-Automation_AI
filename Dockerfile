# Use a lightweight Python base
FROM python:3.11-slim

# Install system dependencies
# ffmpeg: For video processing
# libmagic1: For file type detection
# imagemagick: For text overlays in moviepy
# fonts-dejavu: For cross-platform font support
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    imagemagick \
    fonts-dejavu-core \
    libespeak-ng1 \
    blender \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 🧠 Install Rhubarb Lip Sync (Linux binary)
RUN curl -L https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Linux.zip -o rhubarb.zip && \
    unzip rhubarb.zip -d /opt/rhubarb && \
    rm rhubarb.zip && \
    ln -s /opt/rhubarb/rhubarb /usr/local/bin/rhubarb

# 🎙️ Install Piper TTS (Linux binary)
RUN curl -L https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_linux_x86_64.tar.gz -o piper.tar.gz && \
    tar -xf piper.tar.gz -C /opt && \
    rm piper.tar.gz && \
    ln -s /opt/piper/piper /usr/local/bin/piper

# Fix ImageMagick policy (MoviePy requirement)
RUN if [ -f /etc/ImageMagick-7/policy.xml ]; then \
        sed -i 's/pixel" value="1GiB"/pixel" value="4GiB"/' /etc/ImageMagick-7/policy.xml || true; \
        sed -i 's/disk" value="1GiB"/disk" value="8GiB"/' /etc/ImageMagick-7/policy.xml || true; \
        sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@\*"/g' /etc/ImageMagick-7/policy.xml || true; \
    elif [ -f /etc/ImageMagick-6/policy.xml ]; then \
        sed -i 's/pixel" value="1GiB"/pixel" value="4GiB"/' /etc/ImageMagick-6/policy.xml || true; \
        sed -i 's/disk" value="1GiB"/disk" value="8GiB"/' /etc/ImageMagick-6/policy.xml || true; \
        sed -i 's/none"/read,write"/g' /etc/ImageMagick-6/policy.xml || true; \
    fi

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port for the keep-alive server
EXPOSE 8080

# Set permissions for the startup script
RUN chmod +x start.sh

# Run the project via start.sh
CMD ["./start.sh"]
