import os
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

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

def generate_thumbnail(title: str, category: str = "Trending") -> str:
    """
    Create a JPG thumbnail with gradient background and title text.
    Returns the path to the saved thumbnail file.
    """
    img = Image.new("RGB", (THUMBNAIL_WIDTH, THUMBNAIL_HEIGHT))
    colors = random.choice(BG_COLORS)
    _draw_gradient(img, colors[0], colors[1])
    draw = ImageDraw.Draw(img)

    try:
        if os.name == 'nt':
            title_font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 80)
            cat_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 48)
        else:
            # Linux (Render/Docker)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            cat_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
    except Exception:
        title_font = ImageFont.load_default()
        cat_font = ImageFont.load_default()

    # Category badge
    cat_text = f"  {category.upper()}  "
    badge_x, badge_y = 60, 60
    bbox = draw.textbbox((badge_x, badge_y), cat_text, font=cat_font)
    draw.rectangle(bbox, fill=(255, 200, 0))
    draw.text((badge_x, badge_y), cat_text, font=cat_font, fill=(0, 0, 0))

    # Title text (word-wrapped)
    words = title.split()
    lines, line = [], ""
    for word in words:
        test = (line + " " + word).strip()
        if len(test) <= 22:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)

    start_y = (THUMBNAIL_HEIGHT - len(lines) * 90) // 2 + 40
    for i, ln in enumerate(lines):
        draw.text((82, start_y + i * 90 + 2), ln, font=title_font, fill=(0, 0, 0))
        draw.text((80, start_y + i * 90), ln, font=title_font, fill=(255, 255, 255))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(OUTPUT_DIR, f"thumbnail_{timestamp}.jpg")
    img.save(output_file, quality=95)
    print(f"Thumbnail saved to {output_file}")
    return output_file

# Backward-compatible alias
create_thumbnail = generate_thumbnail

if __name__ == "__main__":
    import sys
    title = sys.argv[1] if len(sys.argv) > 1 else "Trending Topic Today"
    category = sys.argv[2] if len(sys.argv) > 2 else "Trending"
    generate_thumbnail(title, category)
