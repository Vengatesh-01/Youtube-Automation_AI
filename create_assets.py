from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder(path, text, color):
    img = Image.new('RGB', (1280, 720), color=color)
    d = ImageDraw.Draw(img)
    try:
        fnt = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 60)
    except:
        fnt = ImageFont.load_default()
    d.text((640, 360), text, font=fnt, fill=(255, 255, 255), anchor="mm")
    img.save(path)

os.makedirs('assets/avatars', exist_ok=True)
os.makedirs('assets/images', exist_ok=True)
os.makedirs('assets/music', exist_ok=True)

create_placeholder('assets/avatars/avatar_1.png', 'AI Avatar 1', (50, 50, 150))
create_placeholder('assets/avatars/avatar_2.png', 'AI Avatar 2', (150, 50, 50))
create_placeholder('assets/images/placeholder_tech.png', 'Tech Visual', (50, 150, 50))
create_placeholder('assets/images/placeholder_finance.png', 'Finance Visual', (100, 100, 50))
