#!/bin/bash
export PORT="${PORT:-8080}"

echo "--- [BOOT] Starting YouTube Automation System ---"
echo "  Root directory: $(pwd)"

# Ensure secrets are available in the subdirectory if they exist in root
if [ -f "client_secrets.json" ]; then
    cp client_secrets.json YouTube_Automation_Free/
fi
if [ -f "token.json" ]; then
    cp token.json YouTube_Automation_Free/
fi

# Switch to the application directory
cd YouTube_Automation_Free || exit 1
echo "  Changed directory to: $(pwd)"

# Create required directories locally
mkdir -p videos thumbnails scripts topics voiceovers

# Launch Gunicorn
echo "Launching Gunicorn on port $PORT..."
exec gunicorn main:app \
    --bind "0.0.0.0:$PORT" \
    --workers 1 \
    --threads 4 \
    --timeout 0 \
    --log-level info
