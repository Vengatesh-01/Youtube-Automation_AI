from PIL import Image, ImageDraw, ImageFont
import os

def create_avatar(path, text, color, detail_color):
    img = Image.new('RGB', (800, 800), color=color)
    d = ImageDraw.Draw(img)
    # Simple "head and shoulders" shape
    d.ellipse([200, 100, 600, 500], fill=detail_color) # Head
    d.rectangle([100, 500, 700, 800], fill=detail_color) # Shoulders
    try:
        fnt = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 40)
    except:
        fnt = ImageFont.load_default()
    d.text((400, 300), text, font=fnt, fill=(255, 255, 255), anchor="mm")
    img.save(path)

os.makedirs('assets/avatars', exist_ok=True)
create_avatar('assets/avatars/avatar_pose_1.png', 'Pose 1 (Intro)', (40, 40, 100), (60, 60, 150))
create_avatar('assets/avatars/avatar_pose_2.png', 'Pose 2 (Explaining)', (40, 100, 40), (60, 150, 60))
create_avatar('assets/avatars/avatar_pose_3.png', 'Pose 3 (Conclusion)', (100, 40, 40), (150, 60, 60))
print("Generated 3 diverse avatar poses.")
