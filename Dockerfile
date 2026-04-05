# Use a more robust base image to avoid l10n package conflicts
FROM python:3.11-bookworm

# Install system dependencies
# ffmpeg: For video processing
# libmagic1: For file type detection
# imagemagick: For text overlays in moviepy
# fonts-dejavu: For cross-platform font support
# Install system dependencies with robust practices
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ffmpeg \
    libmagic1 \
    imagemagick \
    fonts-dejavu-core \
    libespeak-ng1 \
    curl \
    unzip \
    xz-utils \
    libgl1 \
    libxrender1 \
    libxi6 \
    libxkbcommon0 \
    libsm6 \
    libxext6 \
    libxxf86vm1 \
    libxfixes3 \
    && rm -rf /var/lib/apt/lists/*

# 🧠 Install Rhubarb Lip Sync (Linux binary)
RUN curl -L https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Linux.zip -o rhubarb.zip && \
    unzip rhubarb.zip -d /opt/rhubarb && \
    rm rhubarb.zip && \
    ln -s /opt/rhubarb/rhubarb /usr/local/bin/rhubarb

# 🎙️ Install Piper TTS (Linux binary)
RUN curl -L https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz -o piper.tar.gz && \
    tar -xf piper.tar.gz -C /opt && \
    rm piper.tar.gz && \
    ln -s /opt/piper/piper /usr/local/bin/piper

# 🎬 Removed Blender (Transitioning to SadTalker Lip-Sync)
# 🎙️ SadTalker Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    git-lfs \
    libglade2-0 \
    libcanberra-gtk-module \
    libcanberra-gtk3-module \
    && rm -rf /var/lib/apt/lists/*

# Clone SadTalker
RUN git clone https://github.com/OpenTalker/SadTalker.git /app/SadTalker

# Download SadTalker weights (Using the official script if available, or manual curl)
# We use a subset of weights to keep the image size manageable
WORKDIR /app/SadTalker
RUN mkdir -p checkpoints gfpgan/weights
RUN curl -L https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-72000.pth.tar -o checkpoints/mapping_00109-72000.pth.tar && \
    curl -L https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-108000.pth.tar -o checkpoints/mapping_00229-108000.pth.tar && \
    curl -L https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors -o checkpoints/SadTalker_V0.0.2_256.safetensors && \
    curl -L https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/wav2lip.pth -o checkpoints/wav2lip.pth
# Note: Full weights are ~2GB, we only download the absolute essentials for 256px lip-sync

WORKDIR /app

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
