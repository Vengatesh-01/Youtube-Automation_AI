import os
from moviepy import ColorClip, AudioFileClip, TextClip, CompositeVideoClip

def test_write():
    print("[TEST] MoviePy Writing Test...")
    
    # Simple color clip
    clip = ColorClip(size=(1080, 1920), color=(20, 20, 30), duration=2)
    
    # Try to add a simple voice if available
    voice_file = r"voiceovers\voiceover_20260312_214223.mp3"
    if os.path.exists(voice_file):
        audio = AudioFileClip(voice_file).with_duration(2)
        clip = clip.with_audio(audio)
    
    # Try to add text
    txt = TextClip(text="TEST MOVIEPY", font_size=50, color='white', size=(1000, 200), text_align='center')
    txt = txt.with_start(0).with_duration(2).with_position(("center", "center"))
    
    final = CompositeVideoClip([clip, txt])
    
    print("[TEST] Writing file...")
    try:
        final.write_videofile("test_output.mp4", fps=24, logger="bar")
        print("[TEST] Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_write()
