"""
main.py — Simplified YouTube Automation Orchestrator
"""

import os
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
                <label><input type="radio" name="video_type" value="long" checked> Long Video (16:9)</label>
                <label><input type="radio" name="video_type" value="short"> Short (9:16)</label>
            </div>

            <label>Topic</label>
            <input type="text" name="topic" placeholder="e.g., Day 1 of 30 Days English Speaking Challenge" required>
            
            <label>Script (Use BOY: and GIRL: labels)</label>
            <textarea name="script" rows="15" required placeholder="BOY:\nHey everyone, welcome to today's podcast.\n\nGIRL:\nHi everyone! Today we're going to learn..."></textarea>
            
            <label>Background Image</label>
            <input type="file" name="bg_image" accept="image/*" required>
            <span class="help">Upload 16:9 for long video, or 9:16 for shorts.</span>
            
            <label>Thumbnail Image</label>
            <input type="file" name="thumbnail" accept="image/*" required>
            
            <button type="submit" class="btn">🚀 Generate & Upload</button>
        </form>
    </div>
    
    <div class="card">
        <h2>📜 Recent Logs</h2>
        <pre>{{ logs }}</pre>
    </div>
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
    with open("outputs/pipeline.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")

def parse_script(script_text):
    lines = script_text.split('\n')
    dialogues = []
    current_speaker = None
    current_text = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        upper_line = line.upper().replace(' ', '')
        if upper_line in ('BOY:', '[BOY]', 'BOY'):
            if current_speaker and current_text:
                dialogues.append({"speaker": current_speaker, "text": " ".join(current_text)})
            current_speaker = "boy"
            current_text = []
        elif upper_line in ('GIRL:', '[GIRL]', 'GIRL'):
            if current_speaker and current_text:
                dialogues.append({"speaker": current_speaker, "text": " ".join(current_text)})
            current_speaker = "girl"
            current_text = []
        elif upper_line in ('PAUSE:', '[PAUSE]', 'PAUSE'):
            if current_speaker and current_text:
                dialogues.append({"speaker": current_speaker, "text": " ".join(current_text)})
            current_speaker = "pause"
            current_text = []
        else:
            if current_speaker:
                current_text.append(line)
                
    if current_speaker and current_text:
        dialogues.append({"speaker": current_speaker, "text": " ".join(current_text)})
        
    return dialogues

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
    try:
        log_msg("--- STARTING PIPELINE ---")
        log_msg(f"Topic: {topic} (Format: {video_type})")
        
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
            success = generate_voice(text, output_mp3, voice)
            if not success:
                raise Exception(f"TTS generation failed for {speaker} dialogue {i}")
                
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
        final_video = "outputs/video/final_video.mp4"
        video_result = assemble_podcast_video(bg_path, final_audio, sub_file, final_video, video_type)
        if not video_result:
            raise Exception("Video assembly failed.")
            
        # 6. YouTube Metadata
        log_msg("Generating YouTube metadata...")
        metadata = generate_metadata(topic, script_text)
        
        # Adjust metadata for shorts
        title = metadata.get("title", f"{topic}")
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
        log_msg("Uploading to YouTube...")
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


@app.route('/')
def index():
    return render_template_string(INDEX_HTML, logs=get_logs())

@app.route('/generate', methods=['POST'])
def generate():
    topic = request.form.get('topic')
    script = request.form.get('script')
    video_type = request.form.get('video_type', 'long')
    
    bg = request.files.get('bg_image')
    thumb = request.files.get('thumbnail')
    
    if bg and thumb and bg.filename and thumb.filename:
        bg_path = os.path.join(app.config['UPLOAD_FOLDER'], "bg_" + secure_filename(bg.filename))
        thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], "thumb_" + secure_filename(thumb.filename))
        bg.save(bg_path)
        thumb.save(thumb_path)
        
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

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
