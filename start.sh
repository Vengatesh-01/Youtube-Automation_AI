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

# Ensure the required directories exist in root
mkdir -p videos thumbnails scripts topics voiceovers

# Defensive Cleanup: Remove any local Windows venv that might have been copied
if [ -d "venv" ]; then
    echo "  [CLEANUP] Removing local Windows venv..."
    rm -rf venv
fi

# Diagnostic: Verify files are present in root
echo "  [DIAGNOSTIC] Root Directory listing:"
ls -la

# Pre-flight Check: Verify Python can load the main app from root
echo "  [PRE-FLIGHT] Verifying app load..."
if ! PYTHONPATH=. python3 -c "import main; print('  [PRE-FLIGHT] App loaded successfully')" ; then
    echo "  [FATAL] Pre-flight check failed! Review the traceback above."
    # List files to help debug missing dependencies
    ls -la
    exit 3
fi

# Launch Gunicorn
echo "Launching Gunicorn on port $PORT..."
exec PYTHONPATH=. gunicorn main:app \
    --bind "0.0.0.0:$PORT" \
    --workers 1 \
    --threads 4 \
    --timeout 120 \
    --log-level debug
