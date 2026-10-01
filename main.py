"""
main.py — Simplified YouTube Automation Orchestrator
"""

import os
import sys
import time
import threading
import subprocess
from flask import Flask, request, render_template_string, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
import json

from utils import safe_print, get_ffmpeg, get_audio_duration
from voice_agent import generate_voice
from subtitle_agent import generate_srt
from video_agent import assemble_podcast_video
from metadata_agent import generate_metadata
from upload_agent import upload_video

# --- Flask Setup ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'inputs'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('outputs/audio', exist_ok=True)
os.makedirs('outputs/video', exist_ok=True)
os.makedirs('outputs/subtitles', exist_ok=True)
os.makedirs('outputs/youtube', exist_ok=True)

# Lock to prevent concurrent pipeline runs corrupting shared output files
_pipeline_lock = threading.Lock()
_pipeline_running = False

# --- UI Templates ---
INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Podcast Generator</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; background: #121212; color: #fff; }
        .card { background: #1e1e1e; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); margin-bottom: 20px; }
        h1 { color: #bb86fc; }
        label { font-weight: bold; display: block; margin-top: 15px; color: #e0e0e0; }
        input[type="text"], textarea { width: 100%; padding: 12px; margin-top: 8px; border-radius: 6px; border: 1px solid #333; background: #2d2d2d; color: #fff; font-family: inherit; }
        .radio-group { margin-top: 15px; background: #2d2d2d; padding: 15px; border-radius: 6px; }
        .radio-group label { display: inline-block; margin-right: 20px; font-weight: normal; margin-top: 0; cursor: pointer; }
        .radio-group input { margin-right: 8px; }
        input[type="file"] { margin-top: 8px; color: #bbb; }
        .btn { display: block; width: 100%; background: #bb86fc; color: #121212; padding: 15px; text-decoration: none; border-radius: 8px; font-weight: bold; text-align: center; font-size: 1.1em; border: none; cursor: pointer; margin-top: 25px; transition: background 0.2s; }
        .btn:hover { background: #9b59b6; }
        .help { font-size: 0.9em; color: #888; }
        pre { background: #000; padding: 15px; border-radius: 8px; color: #4caf50; overflow-x: auto; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="card">
        <h1>🎙️ Create English Podcast</h1>
        <form action="/generate" method="post" enctype="multipart/form-data">
            <label>Video Format</label>
            <div class="radio-group">
                <label><input type="radio" name="video_type" value="long" checked id="fmt_long"> Long Video (16:9)</label>
                <label><input type="radio" name="video_type" value="short" id="fmt_short"> Short (9:16)</label>
            </div>

            <label>Topic</label>
            <input type="text" name="topic" placeholder="e.g., Day 1 of 30 Days English Speaking Challenge" required>
            
            <label>Script (Use BOY: and GIRL: labels)</label>
            <textarea name="script" rows="15" required placeholder="BOY:\nHey everyone, welcome to today's podcast.\n\nGIRL:\nHi everyone! Today we're going to learn..."></textarea>
            
            <label id="bg_label">Background Image</label>
            <input type="file" name="bg_image" id="bg_image" accept="image/*" required>
            <span class="help" id="bg_help">Upload 16:9 for long video, or 9:16 for shorts.</span>
            
            <div id="thumb_section">
                <label>Thumbnail Image</label>
                <input type="file" name="thumbnail" id="thumbnail" accept="image/*">
                <span class="help">Separate thumbnail for long videos.</span>
            </div>
            
            <button type="submit" class="btn">🚀 Generate & Upload</button>
        </form>
        <script>
            function updateImageFields() {
                var isShort = document.getElementById('fmt_short').checked;
                var thumbSection = document.getElementById('thumb_section');
                var bgHelp = document.getElementById('bg_help');
                var bgLabel = document.getElementById('bg_label');
                if (isShort) {
                    thumbSection.style.display = 'none';
                    document.getElementById('thumbnail').removeAttribute('required');
                    bgHelp.textContent = 'Upload your 9:16 image — used as both background and thumbnail.';
                    bgLabel.textContent = 'Background & Thumbnail Image';
                } else {
                    thumbSection.style.display = 'block';
                    bgHelp.textContent = 'Upload 16:9 for long video, or 9:16 for shorts.';
                    bgLabel.textContent = 'Background Image';
                }
            }
            document.getElementById('fmt_long').addEventListener('change', updateImageFields);
            document.getElementById('fmt_short').addEventListener('change', updateImageFields);
            updateImageFields();
        </script>
    </div>
    
    <div class="card">
        <h2>📜 Recent Logs</h2>
        <pre>{{ logs }}</pre>
    </div>

    {% if last_video_ready %}
    <div class="card" style="border: 1px solid #bb86fc;">
        <h2 style="color:#ff7043;">⚠️ Last Video Ready but Not Uploaded</h2>
        <p style="color:#aaa;">The video was assembled but the upload failed (network error). Click below to retry the upload without re-generating the video.</p>
        <form action="/retry_upload" method="post">
            <button type="submit" class="btn" style="background:#ff7043;">🔁 Retry Last Upload</button>
        </form>
    </div>
    {% endif %}
</body>
</html>
"""

def get_logs():
    if os.path.exists("outputs/pipeline.log"):
        with open("outputs/pipeline.log", "r", encoding="utf-8") as f:
            return "".join(f.readlines()[-30:])
    return "No logs yet."

def log_msg(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    safe_print(line)
    sys.stdout.flush()  # Force terminal output from background threads
    with open("outputs/pipeline.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")

def parse_script(script_text):
    import re
    lines = script_text.split('\n')
    raw_dialogues = []
    current_speaker = None
    current_text = []
    
    def flush():
        if current_speaker and current_text:
            text = " ".join(current_text).strip()
            if text:
                raw_dialogues.append({"speaker": current_speaker, "text": text})
    
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # --- Inline label format: "BOY: some text" / "GIRL: some text" ---
        inline_match = re.match(r'^(BOY|GIRL|BOTH|PAUSE)\s*:\s*(.*)', line, re.IGNORECASE)
        if inline_match:
            label = inline_match.group(1).upper()
            rest  = inline_match.group(2).strip()
            flush()
            if label == 'BOY':
                current_speaker = "boy"
                current_text = [rest] if rest else []
            elif label == 'GIRL':
                current_speaker = "girl"
                current_text = [rest] if rest else []
            elif label == 'BOTH':
                current_speaker = "boy"
                current_text = [rest] if rest else []
            elif label == 'PAUSE':
                current_speaker = None
                try:
                    duration = str(float(rest)) if rest else "2.0"
                except ValueError:
                    duration = "2.0"
                raw_dialogues.append({"speaker": "pause", "text": duration})
                current_text = []
            continue

        upper_line = line.upper().replace(' ', '')

        # Speaker labels (standalone line, no inline text)
        if upper_line in ('BOY:', '[BOY]', 'BOY'):
            flush()
            current_speaker = "boy"
            current_text = []
        elif upper_line in ('GIRL:', '[GIRL]', 'GIRL'):
            flush()
            current_speaker = "girl"
            current_text = []
        elif upper_line in ('BOTH:', '[BOTH]', 'BOTH'):
            flush()
            current_speaker = "boy"  # Use boy voice for BOTH
            current_text = []
        elif upper_line in ('PAUSE:', '[PAUSE]', 'PAUSE'):
            flush()
            raw_dialogues.append({"speaker": "pause", "text": "2.0"})
            current_text = []
        else:
            # Check for [PAUSE X SECONDS] or [PAUSE X] inline format
            pause_match = re.match(r'\[PAUSE\s*([\d.]+)\s*(?:SECONDS?)?\]', line, re.IGNORECASE)
            if pause_match:
                flush()
                duration = pause_match.group(1)
                raw_dialogues.append({"speaker": "pause", "text": duration})
                current_text = []
            elif current_speaker:
                current_text.append(line)
                
    flush()
    
    # Merge consecutive same-speaker dialogues into one TTS request.
    # This reduces 120+ individual TTS calls down to ~30-40,
    # preventing Edge TTS rate limiting on long scripts.
    merged = []
    for d in raw_dialogues:
        if d["speaker"] == "pause":
            merged.append(d)
        elif merged and merged[-1]["speaker"] == d["speaker"]:
            # Same speaker as last entry — append text
            merged[-1]["text"] = merged[-1]["text"] + " " + d["text"]
        else:
            merged.append({"speaker": d["speaker"], "text": d["text"]})
    
    return merged



def prepend_thumbnail_frame(thumbnail_path, video_path, output_path, duration=2.0):
    """
    Prepend the thumbnail image as a still frame at the start of the video.
    YouTube Shorts uses the first frame as the feed thumbnail, so burning
    the custom thumbnail image here guarantees it appears in the Shorts feed.

    Uses full re-encode during concat to avoid codec/sample-rate mismatch
    failures that cause the concat to silently fall back to the original video.
    """
    ffmpeg = get_ffmpeg()
    thumb_clip_audio = "outputs/video/thumb_frame_audio.mp4"

    # Step 1: Create thumbnail still clip WITH silent audio, matching the main
    #         video's audio spec (48000 Hz stereo AAC) so concat always works.
    thumb_cmd = [
        ffmpeg, "-y", "-nostdin",
        "-loop", "1", "-t", str(duration),
        "-i", thumbnail_path,
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
        "-shortest",
        thumb_clip_audio
    ]
    r1 = subprocess.run(thumb_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r1.returncode != 0:
        safe_print(f"⚠️ Could not create thumbnail frame clip: {r1.stderr.decode('utf-8', errors='replace')[-500:]}")
        return video_path  # fall back to original

    # Step 2: Concat thumbnail clip + main video using full re-encode so
    #         frame/audio specs are guaranteed to match.
    concat_list = "outputs/video/thumb_concat.txt"
    with open(concat_list, "w") as f:
        f.write(f"file '{os.path.abspath(thumb_clip_audio)}'\n")
        f.write(f"file '{os.path.abspath(video_path)}'\n")

    concat_cmd = [
        ffmpeg, "-y", "-nostdin",
        "-f", "concat", "-safe", "0",
        "-i", concat_list,
        # Re-encode both streams so specs are guaranteed compatible
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
        output_path
    ]
    r2 = subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if r2.returncode == 0 and os.path.exists(output_path):
        safe_print(f"✅ Thumbnail frame prepended to video ({duration}s still at start).")
        return output_path
    else:
        err = r2.stderr.decode('utf-8', errors='replace')[-500:]
        safe_print(f"⚠️ Concat failed (returncode={r2.returncode}), using original video.\n   FFmpeg error: {err}")
        return video_path


def assemble_audio(audio_files, output_file):
    list_file = "outputs/audio/concat_list.txt"
    with open(list_file, "w") as f:
        for audio in audio_files:
            f.write(f"file '{os.path.abspath(audio)}'\n")
    cmd = [get_ffmpeg(), "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output_file]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return output_file

def generate_silence(duration, output_file):
    cmd = [
        get_ffmpeg(), "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-t", str(duration), "-q:a", "9", "-acodec", "libmp3lame", output_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def run_pipeline(topic, script_text, bg_path, thumb_path, video_type="long"):
    global _pipeline_running
    try:
        log_msg("--- STARTING PIPELINE ---")
        log_msg(f"Topic: {topic} (Format: {video_type})")

        # 🧹 Clear ALL previous outputs so new script is always used fresh
        import glob, shutil
        for folder in ["outputs/audio", "outputs/subtitles", "outputs/video"]:
            for f in glob.glob(f"{folder}/*"):
                try:
                    os.remove(f)
                except Exception:
                    pass
        log_msg("Cleared old audio/subtitle/video outputs.")
        
        intro_text = """
BOY:
Welcome to the English Practice Podcast.

GIRL:
Listen. Speak. Improve.

BOY:
Real conversations, useful English, and practice you can use in real life.

GIRL:
So don't just listen.

BOY:
Speak with us.

GIRL:
Let's begin.
"""
        if video_type == "long":
            script_text = intro_text + "\n" + script_text
        
        # 1. Parse Script
        log_msg("Parsing script...")
        dialogues = parse_script(script_text)
        if not dialogues:
            raise Exception("No valid BOY: or GIRL: labels found in the script.")
        
        with open("outputs/script.json", "w") as f:
            json.dump(dialogues, f, indent=2)
            
        # 2. TTS Generation
        audio_files = []
        durations = []
        
        log_msg("Generating TTS voices and pauses...")
        for i, d in enumerate(dialogues):
            speaker = d["speaker"]
            text = d["text"]
            
            if speaker == "pause":
                try:
                    duration_sec = float(text.strip())
                except:
                    duration_sec = 3.0
                output_mp3 = f"outputs/audio/pause_{i:03d}.mp3"
                generate_silence(duration_sec, output_mp3)
                audio_files.append(output_mp3)
                durations.append(duration_sec)
                # Keep text as empty for subtitles so we don't display the number
                d["text"] = ""
                continue
                
            voice = "en-US-GuyNeural" if speaker == "boy" else "en-US-JennyNeural"
            
            output_mp3 = f"outputs/audio/{speaker}_{i:03d}.mp3"
            
            # Skip already-generated files so pipeline can resume after failure
            if os.path.exists(output_mp3) and os.path.getsize(output_mp3) > 0:
                log_msg(f"Skipping TTS for {speaker} dialogue {i} (already generated)")
            else:
                success = generate_voice(text, output_mp3, voice)
                if not success:
                    raise Exception(f"TTS generation failed for {speaker} dialogue {i}")
                # Delay between TTS requests to avoid Edge TTS rate limiting
                time.sleep(1.5)
                
            audio_files.append(output_mp3)
            # Measure duration
            duration = get_audio_duration(output_mp3)
            durations.append(duration)
            
        # 3. Audio Assembly
        log_msg("Assembling audio...")
        final_audio = "outputs/audio/final_audio.mp3"
        assemble_audio(audio_files, final_audio)
        
        # 4. Subtitles
        log_msg("Generating subtitles...")
        sub_file = "outputs/subtitles/subtitles.srt"
        generate_srt(dialogues, durations, sub_file)
        
        # 5. Video Assembly
        log_msg("Assembling video...")
        raw_video   = "outputs/video/raw_video.mp4"
        final_video = "outputs/video/final_video.mp4"
        video_result = assemble_podcast_video(bg_path, final_audio, sub_file, raw_video, video_type)
        if not video_result:
            raise Exception("Video assembly failed.")

        # 5b. For Shorts: prepend thumbnail image as the first 1-second still frame.
        #     YouTube Shorts displays the first video frame in the feed — burning the
        #     custom thumbnail here guarantees the correct image is always shown.
        # 5b. For Shorts: prepend the thumbnail image as a clean 2-second still frame
        #     at the very start of the video. YouTube Shorts displays the first frame
        #     as the feed thumbnail — this guarantees the correct image is always shown.
        if video_type == "short" and thumb_path and os.path.isfile(thumb_path):
            log_msg("Prepending thumbnail frame to Short...")
            result = prepend_thumbnail_frame(thumb_path, raw_video, final_video, duration=2.0)
            if not os.path.exists(final_video):
                log_msg("⚠️ Thumbnail prepend produced no output — copying raw video instead.")
                import shutil
                shutil.copy2(raw_video, final_video)
        else:
            import shutil
            shutil.copy2(raw_video, final_video)

            
        # 6. YouTube Metadata
        log_msg("Generating YouTube metadata...")
        metadata = generate_metadata(topic, script_text)
        
        # Adjust metadata for shorts — ensure title is never empty or invalid
        title = metadata.get("title", "") or topic or "English Practice Podcast"
        title = title.strip() or "English Practice Podcast"
        # Strip characters YouTube rejects (< > angle brackets, leading/trailing special chars)
        import re as _re
        title = _re.sub(r'[<>]', '', title)          # strip < >
        title = title.encode('ascii', 'ignore').decode('ascii').strip()  # strip non-ASCII (emojis)
        title = title.strip(' |:-') or "English Practice Podcast"        # strip stray separators
        title = title[:100]                           # YouTube max title length
        desc = metadata.get("description", topic)
        tags = metadata.get("tags", [])
        
        if video_type == "short":
            if "#shorts" not in title.lower():
                title += " #shorts"
            if "#shorts" not in desc.lower():
                desc += "\n#shorts"
            if "shorts" not in [t.lower() for t in tags]:
                tags.append("shorts")
                
        with open("outputs/youtube/metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        # 7. YouTube Upload
        log_msg(f"Uploading to YouTube... [title={repr(title)}]")
        url = upload_video(
            video_file=final_video,
            title=title,
            description=desc,
            thumbnail_file=thumb_path,
            tags=tags,
            privacy="public" # Set to public so video is visible to everyone
        )
        
        if url:
            log_msg(f"✅ SUCCESS! Video uploaded: {url}")
        else:
            log_msg("❌ Upload failed. Please check credentials or upload manually.")

    except Exception as e:
        log_msg(f"❌ PIPELINE ERROR: {str(e)}")
    finally:
        global _pipeline_running
        _pipeline_running = False
        log_msg("--- PIPELINE FINISHED ---")


def last_video_ready():
    """True when assembled video + metadata exist but last log line shows upload failure."""
    video_ok = os.path.isfile("outputs/video/final_video.mp4")
    meta_ok  = os.path.isfile("outputs/youtube/metadata.json")
    if not (video_ok and meta_ok):
        return False
    # Check last pipeline result from log
    log_lines = get_logs().splitlines()
    for line in reversed(log_lines):
        if "PIPELINE FINISHED" in line:
            break
        if "SUCCESS! Video uploaded" in line:
            return False  # already uploaded successfully
        if "Upload failed" in line or "PIPELINE ERROR" in line:
            return True
    return False

@app.route('/')
def index():
    return render_template_string(INDEX_HTML, logs=get_logs(), last_video_ready=last_video_ready())

@app.route('/generate', methods=['POST'])
def generate():
    topic = request.form.get('topic')
    script = request.form.get('script')
    video_type = request.form.get('video_type', 'long')
    
    bg = request.files.get('bg_image')
    thumb = request.files.get('thumbnail')
    
    # For Shorts, the background image doubles as the thumbnail — no separate upload needed
    if video_type == 'short' and bg and bg.filename and (not thumb or not thumb.filename):
        thumb = None  # Will be handled below by reusing bg_path

    if bg and bg.filename:
        # Block concurrent pipeline runs
        global _pipeline_running
        if _pipeline_running:
            return """
            <html>
                <body style="font-family: sans-serif; text-align: center; padding: 50px; background:#121212; color:#fff;">
                    <h1 style="color:#ff5555;">⏳ Pipeline Already Running!</h1>
                    <p>Please wait for the current video to finish before starting a new one.</p>
                    <p>Check the <a href="/" style="color:#bb86fc;">logs on the dashboard</a> for progress.</p>
                    <script>setTimeout(() => { window.location.href = "/"; }, 4000);</script>
                </body>
            </html>
            """
        _pipeline_running = True
        bg_path = os.path.join(app.config['UPLOAD_FOLDER'], "bg_" + secure_filename(bg.filename))
        bg.save(bg_path)
        if thumb and thumb.filename:
            thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], "thumb_" + secure_filename(thumb.filename))
            thumb.save(thumb_path)
        else:
            # Shorts: reuse the background image as the thumbnail
            thumb_path = bg_path
        
        # Start in background
        thread = threading.Thread(target=run_pipeline, args=(topic, script, bg_path, thumb_path, video_type), daemon=True)
        thread.start()
        
        return """
        <html>
            <body style="font-family: sans-serif; text-align: center; padding: 50px; background:#121212; color:#fff;">
                <h1 style="color:#bb86fc;">✅ Pipeline Triggered!</h1>
                <p>The podcast is now being generated in the background.</p>
                <p><a href="/" style="color:#bb86fc;">Return to Dashboard to view logs</a></p>
                <script>setTimeout(() => { window.location.href = "/"; }, 3000);</script>
            </body>
        </html>
        """
    return "Missing inputs.", 400


@app.route('/retry_upload', methods=['POST'])
def retry_upload():
    """Re-upload the last assembled video using saved metadata, no re-generation."""
    global _pipeline_running
    if _pipeline_running:
        return """
        <html><body style="font-family:sans-serif;text-align:center;padding:50px;background:#121212;color:#fff;">
            <h1 style="color:#ff5555;">⏳ Pipeline Already Running!</h1>
            <p>Please wait for the current pipeline to finish.</p>
            <script>setTimeout(() => { window.location.href = "/"; }, 3000);</script>
        </body></html>
        """

    video_file    = "outputs/video/final_video.mp4"
    metadata_file = "outputs/youtube/metadata.json"

    if not os.path.isfile(video_file) or not os.path.isfile(metadata_file):
        return "<p style='color:red'>No assembled video or metadata found.</p>", 400

    def _do_retry():
        global _pipeline_running
        _pipeline_running = True
        try:
            import json, re as _re
            with open(metadata_file, "r", encoding="utf-8") as fh:
                meta = json.load(fh)
            title = meta.get("title", "").strip()
            title = _re.sub(r'[<>]', '', title)
            title = title.encode('ascii', 'ignore').decode('ascii').strip()
            title = title.strip(' |:-') or "English Practice Podcast"
            title = title[:100]
            desc  = meta.get("description", "")
            tags  = meta.get("tags", [])

            # Find latest thumbnail
            inputs_dir = app.config['UPLOAD_FOLDER']
            thumbs = sorted(
                [f for f in os.listdir(inputs_dir) if f.startswith("thumb_")],
                key=lambda f: os.path.getmtime(os.path.join(inputs_dir, f)),
                reverse=True
            )
            thumb = os.path.join(inputs_dir, thumbs[0]) if thumbs else None

            log_msg(f"🔁 Retrying upload... title={repr(title)}")
            url = upload_video(
                video_file=video_file,
                title=title,
                description=desc,
                thumbnail_file=thumb,
                tags=tags,
                privacy="public",
            )
            if url:
                log_msg(f"✅ Retry SUCCESS! Video uploaded: {url}")
            else:
                log_msg("❌ Retry upload failed. Check credentials or internet connection.")
        except Exception as exc:
            log_msg(f"❌ Retry error: {exc}")
        finally:
            _pipeline_running = False
            log_msg("--- RETRY FINISHED ---")

    _pipeline_running = True
    threading.Thread(target=_do_retry, daemon=True).start()

    return """
    <html><body style="font-family:sans-serif;text-align:center;padding:50px;background:#121212;color:#fff;">
        <h1 style="color:#bb86fc;">🔁 Retry Upload Triggered!</h1>
        <p>Uploading the last assembled video in the background.</p>
        <p><a href="/" style="color:#bb86fc;">Return to Dashboard to view logs</a></p>
        <script>setTimeout(() => { window.location.href = "/"; }, 3000);</script>
    </body></html>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
