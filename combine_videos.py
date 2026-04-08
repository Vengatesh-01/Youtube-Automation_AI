import os
import glob
import shutil
import subprocess

def combine(face_path, bg_path, out_path, mode="FINAL", audio_path=None, bgm_path=None):
    print(f"🎬 Combine Videos ({mode}): Face={face_path}, BG={bg_path}, Audio={audio_path}, Out={out_path}")
    
    has_face = bool(face_path and os.path.exists(face_path))
    if not has_face:
        print("No valid face_path provided or found. Proceeding without Talking Head overlay.")

    # Common overlay offset for lower center positioning
    y_offset = 250 

    if mode == "PREVIEW":
        preset = "ultrafast"
        bg_filter = "[0:v]scale=1080:1920,setpts=PTS-STARTPTS[bg];"
        if has_face:
            face_filter = "[1:v]scale=540:-2,colorkey=0x000000:0.25:0.15,format=yuva420p[face];"
            vignette_filter = f"[bg_shadow][face_main]overlay=x=(W-w)/2:y=H-h-{y_offset}[outv]"
            audio_map = "-map 2:a" if audio_path else "-map 1:a"
        else:
            face_filter = ""
            vignette_filter = "[bg]vignette=PI/3.5[outv]"
            audio_map = "-map 1:a" if audio_path else ""  # Wait, audio will be tracked later via map
            
    else:
        preset = "slow"
        bg_filter = (
            "[0:v]scale=1080:1920,setpts=PTS-STARTPTS,minterpolate=fps=30:mi_mode=blend,"
            "zoompan=z='min(zoom+0.0005,1.1)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920,"
            "colorbalance=rs=.02:bs=-.02,gblur=sigma=5[bg];"
        )
        
        if has_face:
            face_filter = (
                "[1:v]scale=540:-2,"
                "eq=contrast=1.05:brightness=0.01:saturation=1.02:gamma_r=1.02:gamma_b=0.98,"
                "chromashift=cbh=-1:crh=1:cbv=1:crv=-1,noise=c0s=2:allf=t+u,tmix=frames=2:weights='1 1',"
                "colorkey=0x000000:0.25:0.15,format=yuva420p[face];"
            )
        else:
            face_filter = ""

        # Standardize Background Music logic
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if not bgm_path:
            bgm_path = os.path.join(base_dir, "assets", "bg_music.mp3")

        # Fail-safe: Ensure BGM exists or fallback to generated tone
        if not os.path.exists(bgm_path):
            print(f"⚠️  BGM missing at {bgm_path}. Falling back to generated tone.")
            pads = "0.1*sin(110*2*PI*t)+0.05*sin(164.8*2*PI*t)"
            piano = "0.02*sin(440*2*PI*t)*exp(-3*mod(t,4))"
            bgm_input = f"aevalsrc='({pads}+{piano})':d=60,chorus=0.5:0.9:50|60:0.4:0.25:2,aecho=0.8:0.88:1000:0.3"
            bgm_src = "[bgm_fallback]"
            bgm_setup = f"{bgm_input}{bgm_src};"
        else:
            # We must map inputs correctly. 
            # 0=bg, 1=audio (if no face) OR 1=face, 2=audio. etc.
            # Let's dynamically track indices
            bgm_setup = ""

        duration = 60.0
        if audio_path and os.path.exists(audio_path):
            try:
                cmd_dur = [
                    r"C:\Users\User\OneDrive\Desktop\youtube automation system\YouTube_Automation_Free\venv\Lib\site-packages\imageio_ffmpeg\binaries\ffprobe-win-x86_64-v7.1.exe",
                    "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path
                ]
                res_dur = subprocess.run(cmd_dur, capture_output=True, text=True)
                if res_dur.returncode == 0:
                    duration = float(res_dur.stdout.strip())
            except: pass

        # Input indexing resolution
        # 0: bg
        idx = 1
        if has_face:
            idx += 1
        a_src_idx = idx if audio_path else (1 if has_face else 0)  # Need an audio source
        if audio_path:
            a_src = f"[{a_src_idx}:a]"
            idx += 1
        elif has_face:
            a_src = "[1:a]"
        else:
            # No voice audio provided, use a dummy or silence if needed.
            # Assuming audio_path is always present in production.
            a_src = "[0:a]" 

        if os.path.exists(bgm_path):
            bgm_src_str = f"[{idx}:a]"
        else:
            bgm_src_str = "[bgm_fallback]"

        if has_face:
            vignette_filter = (
                f"[bg_shadow][face_main]overlay=x='(W-w)/2':y='H-h-{y_offset}',"
                "vignette=PI/3.5[outv];"
                f"{bgm_setup}"
                f"{a_src}volume=1.0[voice]; "
                f"{bgm_src_str}volume=0.15,afade=t=in:st=0:d=0.5,afade=t=out:st={max(0, duration-0.5):.2f}:d=0.5[music]; "
                "[voice][music]amix=inputs=2:duration=first:weights=4 1[aout]"
            )
        else:
            vignette_filter = (
                "[bg]vignette=PI/3.5[outv];"
                f"{bgm_setup}"
                f"{a_src}volume=1.0[voice]; "
                f"{bgm_src_str}volume=0.15,afade=t=in:st=0:d=0.5,afade=t=out:st={max(0, duration-0.5):.2f}:d=0.5[music]; "
                "[voice][music]amix=inputs=2:duration=first:weights=4 1[aout]"
            )
        audio_map = "-map [aout]"

    if has_face:
        filter_complex = (
            bg_filter +
            face_filter +
            "[face]split[face_main][face_shadow];"
            "[face_shadow]colorchannelmixer=rr=0:rg=0:rb=0:ra=0:gr=0:gg=0:gb=0:ba=0:br=0:bg=0:bb=0:ba=0:aa=0.65,gblur=sigma=16[shadow];"
            f"[bg][shadow]overlay=x='(W-w)/2+15':y='H-h-{y_offset}+15'[bg_shadow];" +
            vignette_filter
        )
    else:
        filter_complex = bg_filter + vignette_filter

    # Command building
    cmd = [
        r"C:\Users\User\OneDrive\Desktop\youtube automation system\YouTube_Automation_Free\venv\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe", "-y",
        "-stream_loop", "-1", "-i", bg_path
    ]
    if has_face:
        cmd.extend(["-stream_loop", "-1", "-i", face_path])
    if audio_path:
        cmd.extend(["-i", audio_path])
    if os.path.exists(bgm_path):
        cmd.extend(["-stream_loop", "-1", "-i", bgm_path])
        
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]"
    ])
    
    if mode == "PREVIEW":
        if audio_path:
            # 1 or 2 based on face
            cmd.extend(["-map", f"{a_src_idx}:a"])
        else:
            cmd.extend(["-map", "1:a" if has_face else "0:a"])
    else:
        cmd.extend(["-map", "[aout]"])
        
    cmd.extend([
        "-c:v", "libx264", "-preset", preset, "-crf", "17",
        "-c:a", "aac", "-b:a", "320k",
        "-async", "1",
        "-shortest",
        out_path
    ])

    print("Executing FFmpeg command...")
    print(" ".join(cmd))
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"✅ Final video created successfully at {out_path}")
        return out_path
    else:
        print("❌ FFmpeg failed.")
        raise Exception("FFmpeg composition failed")

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 4:
        face = sys.argv[1]
        bg = sys.argv[2]
        out = sys.argv[3]
        audio = sys.argv[4] if len(sys.argv) > 4 else None
        bgm = sys.argv[5] if len(sys.argv) > 5 else None
        combine(face, bg, out, audio_path=audio, bgm_path=bgm)
    else:
        print("Usage: python combine_videos.py <face_video> <bg_video> <output_video> [audio_voice] [bg_music]")
        # Test paths
        test_face = r"C:\Users\User\Downloads\SadTalker-main\SadTalker-main\results\result.mp4"
        test_bg = r"C:\Users\User\OneDrive\Desktop\youtube automation system\YouTube_Automation_Free\outputs\AnimateDiff_FuturisticCity_00001.mp4"
        test_out = r"C:\Users\User\OneDrive\Desktop\youtube automation system\YouTube_Automation_Free\final_output.mp4"
        if os.path.exists(test_face):
            combine(test_face, test_bg, test_out)
