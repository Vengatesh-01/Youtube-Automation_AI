from video_agent import get_talking_avatar
from moviepy import ColorClip, CompositeVideoClip
import os

def test_render():
    os.makedirs('videos', exist_ok=True)
    # 2 second test
    bg = ColorClip(size=(1080, 1920), color=(30, 30, 30), duration=2)
    # Use one of the avatars
    avatar_path = 'assets/avatars/expert_male_v2.png'
    if not os.path.exists(avatar_path):
        avatar_path = 'assets/avatars/learner.png'
    
    avatar = get_talking_avatar(avatar_path, 2, volumes=[0.5]*20)
    final = CompositeVideoClip([bg, avatar])
    
    out = 'videos/minimal_test.mp4'
    print(f"Rendering to {out}...")
    final.write_videofile(out, fps=30, codec="libx264", audio_codec="aac", logger=None, preset="ultrafast")
    print("Done.")

if __name__ == "__main__":
    test_render()
