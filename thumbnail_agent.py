import os
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import requests
import urllib.parse
from utils import safe_print

OUTPUT_DIR = "thumbnails"
THUMBNAIL_WIDTH = 1280
THUMBNAIL_HEIGHT = 720

BG_COLORS = [
    [(255, 0, 100), (255, 150, 0)], # Neon Pink to Orange
    [(0, 255, 200), (0, 100, 255)], # Cyan to Deep Blue
    [(255, 255, 0), (255, 0, 0)],   # Bright Yellow to Red
    [(200, 255, 0), (0, 200, 0)],   # Lime to Emerald
]

def _draw_gradient(image, color_start, color_end):
    draw = ImageDraw.Draw(image)
    w, h = image.size
    for y in range(h):
        r = int(color_start[0] + (color_end[0] - color_start[0]) * y / h)
        g = int(color_start[1] + (color_end[1] - color_start[1]) * y / h)
        b = int(color_start[2] + (color_end[2] - color_start[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

def generate_pollinations_thumbnail(prompt, output_path):
    enhanced_prompt = (
        f"3D Pixar Disney style animation, highly expressive character showing emotion, "
        f"{prompt}, subsurface scattering, warm volumetric lighting, soft shadows, "
        "vibrant colors, highly detailed textures, 8k, cinematic composition, 16:9 aspect ratio"
    )
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&model=flux&nologo=true"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code == 200 and len(response.content) > 5000:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        safe_print(f"Thumbnail API failed: {e}")
    return False

def generate_thumbnail(title: str, category: str = "Trending") -> str:
    """
    Create a JPG thumbnail with AI background and bold text.
    Returns the path to the saved thumbnail file.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_img_path = os.path.join(OUTPUT_DIR, f"temp_bg_{timestamp}.jpg")
    output_file = os.path.join(OUTPUT_DIR, f"thumbnail_{timestamp}.jpg")
    
    topic_prompt = f"character feeling {category.lower()} or thinking about {title.lower()}"
    success = generate_pollinations_thumbnail(topic_prompt, temp_img_path)
    
    if success:
        try:
            img = Image.open(temp_img_path).convert("RGB")
        except:
            img = Image.new("RGB", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
            colors = random.choice(BG_COLORS)
            _draw_gradient(img, colors[0], colors[1])
    else:
        img = Image.new("RGB", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
        colors = random.choice(BG_COLORS)
        _draw_gradient(img, colors[0], colors[1])

    draw = ImageDraw.Draw(img)

    try:
        if os.name == 'nt':
            title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 100)
            cat_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 48)
        else:
            # Linux (Render/Docker)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
            cat_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
    except Exception:
        title_font = ImageFont.load_default()
        cat_font = ImageFont.load_default()

    # Title text (word-wrapped)
    words = title.split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if len(test) <= 18:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)

    # Drawing text (Excuse Erased Style: Bold White with thick Black Stroke)
    start_y = (THUMBNAIL_HEIGHT - len(lines) * 110) // 2 + 150
    for i, ln in enumerate(lines):
        x, y = 80, start_y + i * 110
        try:
            # Pillow 9.2+ supports stroke_fill and stroke_width
            draw.text((x, y), ln, font=title_font, fill=(255, 255, 255), stroke_width=8, stroke_fill=(0, 0, 0))
        except:
            # Fallback for older Pillow versions
            for dx, dy in [(-4,-4), (-4,4), (4,-4), (4,4), (-4,0), (4,0), (0,-4), (0,4)]:
                draw.text((x+dx, y+dy), ln, font=title_font, fill=(0, 0, 0))
            draw.text((x, y), ln, font=title_font, fill=(255, 255, 255))

    img.save(output_file, quality=95)
    safe_print(f"Thumbnail saved to {output_file}")
    
    if success and os.path.exists(temp_img_path):
        os.remove(temp_img_path)
        
    return output_file

# Backward-compatible alias
create_thumbnail = generate_thumbnail

if __name__ == "__main__":
    import sys
    title = sys.argv[1] if len(sys.argv) > 1 else "Trending Topic Today"
    category = sys.argv[2] if len(sys.argv) > 2 else "Trending"
    generate_thumbnail(title, category)
