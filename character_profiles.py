"""
character_profiles.py — Pixar-style character definitions.
Each video dynamically generates a unique character, using a fixed seed
so all scenes within that specific video look visually consistent.
"""
import random
import uuid

GENDERS = ["man", "woman", "boy", "girl"]
HAIR_COLORS = ["dark black", "golden blonde", "auburn red", "ash brown", "silver", "chestnut brown", "platinum blonde"]
HAIR_STYLES = {
    "man": ["short messy", "slicked back", "fade haircut", "curly mop", "shoulder-length wavy"],
    "woman": ["long wavy", "short bob", "messy bun", "long straight", "braided", "curly volume"],
    "boy": ["messy", "bowl cut", "short spiky", "curly"],
    "girl": ["pigtails", "long straight", "short bob", "wavy with a headband"]
}
SKIN_TONES = ["fair", "pale", "warm olive", "rich brown", "dark ebony", "tanned", "golden"]
EYE_COLORS = ["warm brown", "ocean blue", "emerald green", "hazel", "grey", "amber"]
OUTFITS = {
    "man": ["cozy grey hoodie and jeans", "sharp navy blazer over white tee", "plaid flannel shirt and dark denim", "simple black t-shirt and cargo pants"],
    "woman": ["cozy pink ribbed sweater and light blue jeans", "elegant floral summer dress", "oversized vintage sweater and leggings", "professional white blouse and slacks"],
    "boy": ["colorful striped t-shirt and shorts", "red hoodie and blue jeans", "dinosaur print shirt and overalls"],
    "girl": ["yellow polka dot dress", "pink t-shirt and denim skirt", "purple sweater with star patterns"]
}
ACCESSORIES = ["minimalist glasses", "small gold necklace", "beanie hat", "simple stud earrings", "none", "none", "none"]

def get_random_character() -> dict:
    """Generate a completely unique procedural character."""
    gender = random.choice(GENDERS)
    hair_color = random.choice(HAIR_COLORS)
    hair_style = random.choice(HAIR_STYLES[gender])
    skin_tone = random.choice(SKIN_TONES)
    eye_color = random.choice(EYE_COLORS)
    outfit = random.choice(OUTFITS[gender])
    accessory = random.choice(ACCESSORIES)
    
    acc_text = f", wearing {accessory}" if accessory != "none" else ""
    
    # Generate a descriptive visual string for the prompt
    visual = f"{skin_tone} skin {gender}, {hair_style} {hair_color} hair, {eye_color} eyes, wearing {outfit}{acc_text}"
    
    return {
        "name": f"Character_{uuid.uuid4().hex[:6]}",
        "seed": random.randint(1000, 999999),
        "visual": visual
    }

BACKGROUNDS = [
    "cozy modern living room, warm amber lighting, comfortable sofa, indoor plants",
    "bright airy bedroom with fairy string lights, pastel walls, soft bed",
    "sunny outdoor park, lush green trees, blurred flower bokeh background",
    "stylish coffee shop interior, warm wooden shelves, soft bokeh cafe lights",
    "modern clean kitchen, marble countertops, golden morning light through window",
    "school hallway with lockers, warm afternoon sunlight streaming in",
    "cozy home library, tall bookshelves, reading nook, candle light",
    "rooftop at golden hour, city skyline blurred in background, warm sunset glow",
]

EMOTIONS = ["happy", "sad", "surprised", "thoughtful", "nervous", "determined", "worried", "excited"]


def get_random_character() -> dict:
    return random.choice(CHARACTERS)


def get_scene_prompt(character: dict, scene_text: str = "", emotion: str = "neutral") -> str:
    bg = random.choice(BACKGROUNDS)
    return (
        f"Pixar 3D Disney animation style, ultra-realistic photorealistic rendering, "
        f"{character['visual']}, {emotion} emotional expression, "
        f"standing in {bg}, "
        f"subsurface scattering skin, volumetric warm cinematic lighting, soft shadows, "
        f"ultra-detailed face and hair textures, 8K resolution, "
        f"full body portrait, vertical 9:16 composition, depth of field"
    )
