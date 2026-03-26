"""
run_cinematic.bat helper — shows usage and launches cinematic_pipeline.py
This is here for reference; run cinematic_pipeline.py directly from Python.

===========================================================================
📋 CINEMATIC PIPELINE — QUICK REFERENCE
===========================================================================

STANDARD RUN:
  python cinematic_pipeline.py "AI wealth mindset"

QUICK TEST (no Ollama, no ComfyUI portrait gen, reuses existing portrait/voice):
  python cinematic_pipeline.py --quick

WITH YOUTUBE UPLOAD:
  python cinematic_pipeline.py "morning routine tips" --upload

SCHEDULED UPLOAD (10 AM or 6 PM):
  python cinematic_pipeline.py "motivation" --upload --publish_at 2026-03-26T10:00:00Z
  python cinematic_pipeline.py "motivation" --upload --publish_at 2026-03-26T18:00:00Z

SKIP PORTRAIT REGENERATION (use existing inputs/portrait.png):
  python cinematic_pipeline.py "motivation" --skip-portrait

SKIP BACKGROUND GEN (no ComfyUI needed):
  python cinematic_pipeline.py "motivation" --skip-bg --skip-portrait

SCENE TYPES AUTO-DETECTED from topic:
  motivation  → sunrise city skyline, golden light
  technology  → futuristic workspace, neon screens
  casual      → cozy room, warm ambient light
  lifestyle   → sunset outdoor café

OUTPUT:
  outputs/cine_<timestamp>/final_vertical.mp4   (1080x1920, 9:16)
  cinematic_run.log  (full pipeline log)

REQUIREMENTS:
  - SadTalker installed: C:/Users/User/Downloads/SadTalker-main/
  - ComfyUI running:     http://127.0.0.1:8188  (for portrait/BG gen)
  - Ollama running:      http://127.0.0.1:11434  (for script gen)
  - FFmpeg in PATH or C:/ffmpeg/bin/ffmpeg.exe
  - pyttsx3 installed in project Python
"""
print(__doc__)
