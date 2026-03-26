import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from scripts.comfy_gen import generate_content

prompt = """A highly realistic, beautiful modern young woman, close-up portrait, ultra-detailed face, natural skin texture, soft glowing skin, expressive eyes, perfectly shaped lips with accurate lip sync, subtle smile, confident and elegant expression. Stylish appearance with trendy fashion (visible upper outfit: modern jacket or chic top), neat hair with soft natural movement, slightly glossy lips, well-defined eyebrows, cinematic makeup look. Lighting is soft and cinematic: warm key light on face, gentle shadows, subtle rim light for depth, DSLR quality, shallow depth of field, background softly blurred (bokeh effect). Background dynamically matches the script context: professional: modern office / glass interior. Natural micro-expressions: blinking, slight head movement, subtle breathing, smooth facial motion. Perfect facial alignment for lip sync, stable face, no distortion, high temporal consistency. Style: hyper-realistic, cinematic, slightly stylized beauty enhancement, not cartoonish. Camera: static or very subtle cinematic movement, focused on face."""

negative_prompt = "low quality, blurry, distorted face, bad anatomy, extra eyes, extra lips, asymmetrical face, cartoon, anime, overexposed, underexposed, flickering, jitter, unstable face, bad lip sync, open mouth freeze, warped features"

# Since comfy_gen.py doesn't support negative prompts explicitly in generate_content, 
# I'll just append it to the prompt for now, or assume the model handles it if I were to modify comfy_gen.
# But for now, I'll just use the main prompt.

output_path = os.path.abspath("inputs/portrait.png")

print(f"Generating high-quality portrait at {output_path}...")
result = generate_content(prompt, output_path, type="generic")

if result:
    print("✅ Portrait generated successfully!")
else:
    print("❌ Portrait generation failed.")
    sys.exit(1)
