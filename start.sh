#!/bin/bash

# Setup environment
export PYTHONPATH=$PYTHONPATH:.
export PORT="${PORT:-8080}"

echo "--- [BOOT] Starting YouTube Automation System ---"
echo "  Working directory: $(pwd)"
echo "  PORT: $PORT"
echo "  Python: $(python --version)"

# Create required directories
mkdir -p videos thumbnails scripts topics voiceovers

# Launch Gunicorn immediately (scheduler starts in background via main.py)
export PYTHONPATH=$PYTHONPATH:./YouTube_Automation_Free:.
echo "Launching Gunicorn on port $PORT..."
exec gunicorn main:app \
    --bind "0.0.0.0:$PORT" \
    --workers 1 \
    --threads 4 \
    --timeout 0 \
    --keep-alive 5 \
    --log-level info \
    --access-logfile - \
    --error-logfile -
