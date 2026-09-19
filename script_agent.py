import os
import json
import re
import random
import uuid
from datetime import datetime
from utils import safe_print

# CRITICAL: Load .env at module level so GEMINI_API_KEY is always available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ============================================================
#   DYNAMIC FALLBACK SCRIPTS — Topic-Aware Templates
#   Each template adapts to the given topic title so that
#   even without Gemini, every video gets a unique script.
# ============================================================

_FALLBACK_TEMPLATES = [
    # Template 0 — Stoic Challenge
    lambda t: (
        f"TITLE:\n{t}\n\n"
        "DESCRIPTION:\n"
        f"This will change how you think about {t.lower()}. #stoicism #mindset #shorts\n\n"
        "TAGS:\nstoicism, mindset, motivation, psychology, discipline\n\n"
        "--------------------------------------\n\n"
        "SCENES:\n\n"
        f"Scene 1:\nText: A lone figure stands in pouring rain\n"
        f"Image Prompt: Pixar-style 3D animation, cinematic rain scene, lone figure standing in heavy rain at night, city lights reflecting on wet ground, dramatic volumetric lighting\n"
        f"Voiceover: Most people don't understand {t.lower()}. Here's why it matters.\n"
        "Duration: 5s\n\n"
        f"Scene 2:\nText: Close-up of clenched fist\n"
        f"Image Prompt: Pixar-style 3D animation, extreme close-up of a clenched fist, veins visible, dramatic side lighting, dark background, determination\n"
        f"Voiceover: The ancient Stoics discovered something powerful about {t.lower()}.\n"
        "Duration: 5s\n\n"
        f"Scene 3:\nText: Person meditating on mountain peak\n"
        f"Image Prompt: Pixar-style 3D animation, person meditating cross-legged on a misty mountain peak at sunrise, golden hour light, clouds below, serene\n"
        f"Voiceover: It's not about what happens to you. It's about how you respond.\n"
        "Duration: 5s\n\n"
        f"Scene 4:\nText: Two paths diverging in a forest\n"
        f"Image Prompt: Pixar-style 3D animation, two paths diverging in an enchanted dark forest, one path lit with golden light, the other dark and thorny\n"
        f"Voiceover: Every single day you have a choice. Will you choose growth or comfort?\n"
        "Duration: 5s\n\n"
        f"Scene 5:\nText: Person climbing a steep cliff\n"
        f"Image Prompt: Pixar-style 3D animation, determined person climbing a steep rocky cliff face, dramatic sunset behind, sweat on brow, epic scale\n"
        f"Voiceover: The ones who master {t.lower()} become unstoppable.\n"
        "Duration: 5s\n\n"
        f"Scene 6:\nText: Person standing victorious on summit\n"
        f"Image Prompt: Pixar-style 3D animation, silhouette of person standing on mountain summit with arms raised, golden sunrise, clouds parting, triumphant\n"
        f"Voiceover: Remember this next time you want to give up. Subscribe for more.\n"
        "Duration: 5s\n"
    ),
    # Template 1 — Dark Psychology Reveal
    lambda t: (
        f"TITLE:\n{t}\n\n"
        "DESCRIPTION:\n"
        f"The hidden truth about {t.lower()} that nobody tells you. #darkpsychology #manipulation #shorts\n\n"
        "TAGS:\npsychology, dark psychology, manipulation, body language, secrets\n\n"
        "--------------------------------------\n\n"
        "SCENES:\n\n"
        f"Scene 1:\nText: Mysterious figure in shadows\n"
        f"Image Prompt: Pixar-style 3D animation, mysterious hooded figure standing in deep shadows, only glowing eyes visible, noir lighting, suspenseful atmosphere\n"
        f"Voiceover: There's a dark secret about {t.lower()} that manipulators don't want you to know.\n"
        "Duration: 5s\n\n"
        f"Scene 2:\nText: Chess pieces on a board\n"
        f"Image Prompt: Pixar-style 3D animation, dramatic close-up of chess pieces on a marble board, a hand moving the king piece, dramatic spotlight, strategic\n"
        f"Voiceover: Think about it like a chess game. Every move is calculated.\n"
        "Duration: 5s\n\n"
        f"Scene 3:\nText: Person reading body language\n"
        f"Image Prompt: Pixar-style 3D animation, two people in conversation, one person subtly reading the other's body language, highlighted micro-expressions, split lighting\n"
        f"Voiceover: The most dangerous people in the room are the ones who understand this.\n"
        "Duration: 5s\n\n"
        f"Scene 4:\nText: Brain with glowing neural connections\n"
        f"Image Prompt: Pixar-style 3D animation, translucent human brain with glowing neural pathways lighting up in sequence, dark space background, bioluminescent\n"
        f"Voiceover: Your subconscious mind processes {t.lower()} before you even realize it.\n"
        "Duration: 5s\n\n"
        f"Scene 5:\nText: Mirror reflection showing different face\n"
        f"Image Prompt: Pixar-style 3D animation, person looking in ornate mirror but reflection shows a different darker version of themselves, eerie lighting, duality theme\n"
        f"Voiceover: Once you see this pattern, you can never unsee it.\n"
        "Duration: 5s\n\n"
        f"Scene 6:\nText: Person walking away with knowledge\n"
        f"Image Prompt: Pixar-style 3D animation, confident person walking through a doorway of light, leaving darkness behind, powerful stride, cinematic composition\n"
        f"Voiceover: Now you know the truth about {t.lower()}. Use it wisely. Subscribe.\n"
        "Duration: 5s\n"
    ),
    # Template 2 — Success Habits
    lambda t: (
        f"TITLE:\n{t}\n\n"
        "DESCRIPTION:\n"
        f"The secret habit behind {t.lower()}. Billionaires use this daily. #success #habits #shorts\n\n"
        "TAGS:\nsuccess, habits, productivity, billionaire, morning routine\n\n"
        "--------------------------------------\n\n"
        "SCENES:\n\n"
        f"Scene 1:\nText: Alarm clock at 4 AM\n"
        f"Image Prompt: Pixar-style 3D animation, close-up of vintage alarm clock showing 4:00 AM, dim blue morning light, cozy bedroom background, dramatic focus\n"
        f"Voiceover: The most successful people in the world wake up before everyone else. Here's why {t.lower()} is their secret.\n"
        "Duration: 5s\n\n"
        f"Scene 2:\nText: Person writing in journal\n"
        f"Image Prompt: Pixar-style 3D animation, focused person writing intently in a leather journal at a wooden desk, warm lamp light, steam from coffee cup\n"
        f"Voiceover: They start every morning with this one ritual.\n"
        "Duration: 5s\n\n"
        f"Scene 3:\nText: Person exercising at dawn\n"
        f"Image Prompt: Pixar-style 3D animation, athletic person doing pushups on a rooftop at dawn, city skyline in background, golden light breaking through clouds\n"
        f"Voiceover: Discipline is not punishment. It is freedom.\n"
        "Duration: 5s\n\n"
        f"Scene 4:\nText: Time-lapse of building being built\n"
        f"Image Prompt: Pixar-style 3D animation, stylized time-lapse of a skyscraper being built brick by brick, workers moving fast, day turning to night repeatedly\n"
        f"Voiceover: {t} is built one day at a time. There are no shortcuts.\n"
        "Duration: 5s\n\n"
        f"Scene 5:\nText: Person helping others up\n"
        f"Image Prompt: Pixar-style 3D animation, person reaching down from a high ledge to help pull another person up, dramatic perspective, teamwork, golden hour\n"
        f"Voiceover: The greatest sign of mastery is lifting others while you climb.\n"
        "Duration: 5s\n\n"
        f"Scene 6:\nText: Person looking at stars\n"
        f"Image Prompt: Pixar-style 3D animation, person lying on a grassy hill gazing at a spectacular starry night sky, milky way visible, peaceful, contemplative\n"
        f"Voiceover: Start today. Your future self will thank you. Hit subscribe.\n"
        "Duration: 5s\n"
    ),
    # Template 3 — Body Language Secret
    lambda t: (
        f"TITLE:\n{t}\n\n"
        "DESCRIPTION:\n"
        f"Learn to decode {t.lower()} through body language. #bodylanguage #psychology #shorts\n\n"
        "TAGS:\nbody language, psychology, nonverbal, social skills, influence\n\n"
        "--------------------------------------\n\n"
        "SCENES:\n\n"
        f"Scene 1:\nText: Eyes scanning a crowded room\n"
        f"Image Prompt: Pixar-style 3D animation, intense close-up of observant eyes scanning across a crowded dimly-lit room, reflections of people in the irises\n"
        f"Voiceover: You can tell everything about a person in 3 seconds. Here's how {t.lower()} reveals the truth.\n"
        "Duration: 5s\n\n"
        f"Scene 2:\nText: Person crossing arms defensively\n"
        f"Image Prompt: Pixar-style 3D animation, person in business attire crossing arms with a guarded expression, office setting, cool blue lighting, tension\n"
        f"Voiceover: When someone does THIS, they are hiding something from you.\n"
        "Duration: 5s\n\n"
        f"Scene 3:\nText: Handshake with power dynamics\n"
        f"Image Prompt: Pixar-style 3D animation, dramatic close-up of two people shaking hands, one hand clearly dominant on top, power dynamics visible, dramatic lighting\n"
        f"Voiceover: The handshake tells you who controls the conversation.\n"
        "Duration: 5s\n\n"
        f"Scene 4:\nText: Person with genuine vs fake smile\n"
        f"Image Prompt: Pixar-style 3D animation, split-screen face showing genuine Duchenne smile on one side and fake forced smile on the other, detailed expressions\n"
        f"Voiceover: A real smile uses the eyes. A fake one only moves the mouth.\n"
        "Duration: 5s\n\n"
        f"Scene 5:\nText: Person leaning in during conversation\n"
        f"Image Prompt: Pixar-style 3D animation, two people at a cafe table, one leaning forward with interest, warm lighting, engaged body language, rapport\n"
        f"Voiceover: Master {t.lower()} and you will never be deceived again.\n"
        "Duration: 5s\n\n"
        f"Scene 6:\nText: Confident person walking forward\n"
        f"Image Prompt: Pixar-style 3D animation, confident person striding forward through a grand hallway, power pose, dramatic backlighting, authority\n"
        f"Voiceover: Now you see what others miss. Subscribe for more secrets.\n"
        "Duration: 5s\n"
    ),
    # Template 4 — Mind Control / Influence
    lambda t: (
        f"TITLE:\n{t}\n\n"
        "DESCRIPTION:\n"
        f"This ancient influence technique about {t.lower()} will blow your mind. #influence #persuasion #shorts\n\n"
        "TAGS:\ninfluence, persuasion, psychology, social engineering, power\n\n"
        "--------------------------------------\n\n"
        "SCENES:\n\n"
        f"Scene 1:\nText: Puppet strings being cut\n"
        f"Image Prompt: Pixar-style 3D animation, dramatic shot of marionette puppet strings being cut by scissors, puppet falling free, dark stage background, liberation\n"
        f"Voiceover: Someone is using {t.lower()} to control you right now. And you don't even know it.\n"
        "Duration: 5s\n\n"
        f"Scene 2:\nText: Crowd following one leader\n"
        f"Image Prompt: Pixar-style 3D animation, aerial view of large crowd of people all walking in one direction following a single glowing figure, herd mentality visual\n"
        f"Voiceover: 95% of people follow blindly. Only 5% question the system.\n"
        "Duration: 5s\n\n"
        f"Scene 3:\nText: Person breaking free from chains\n"
        f"Image Prompt: Pixar-style 3D animation, powerful person breaking glowing chains from their wrists, explosive energy burst, dramatic backlighting, freedom moment\n"
        f"Voiceover: But once you understand {t.lower()}, the chains break instantly.\n"
        "Duration: 5s\n\n"
        f"Scene 4:\nText: Ancient scroll with secrets\n"
        f"Image Prompt: Pixar-style 3D animation, ancient glowing scroll unrolling to reveal mysterious symbols and text, candlelit dark library, mystical atmosphere\n"
        f"Voiceover: This technique was used by kings and conquerors for centuries.\n"
        "Duration: 5s\n\n"
        f"Scene 5:\nText: Person whispering a secret\n"
        f"Image Prompt: Pixar-style 3D animation, person leaning in to whisper something into another's ear, conspiratorial atmosphere, dramatic shadows, intrigue\n"
        f"Voiceover: The most powerful weapon isn't force. It's knowing what people really want.\n"
        "Duration: 5s\n\n"
        f"Scene 6:\nText: Shield of knowledge\n"
        f"Image Prompt: Pixar-style 3D animation, person holding a glowing shield made of light and knowledge symbols, protecting themselves, heroic pose, epic\n"
        f"Voiceover: Now you hold the shield. Never be manipulated again. Subscribe.\n"
        "Duration: 5s\n"
    ),
    # Template 5 — Emotional Intelligence
    lambda t: (
        f"TITLE:\n{t}\n\n"
        "DESCRIPTION:\n"
        f"Unlock the power of emotional intelligence through {t.lower()}. #eq #emotions #shorts\n\n"
        "TAGS:\nemotional intelligence, EQ, self-awareness, relationships, growth\n\n"
        "--------------------------------------\n\n"
        "SCENES:\n\n"
        f"Scene 1:\nText: Heart and brain connected by lightning\n"
        f"Image Prompt: Pixar-style 3D animation, glowing heart and brain connected by crackling electrical bolts, floating in dark space, emotional and logical duality\n"
        f"Voiceover: Your IQ gets you hired. But {t.lower()} determines if you succeed.\n"
        "Duration: 5s\n\n"
        f"Scene 2:\nText: Person staying calm in chaos\n"
        f"Image Prompt: Pixar-style 3D animation, serene person meditating while a storm of papers and chaos swirls around them, eye of the storm, peaceful center\n"
        f"Voiceover: Emotionally intelligent people don't react. They respond.\n"
        "Duration: 5s\n\n"
        f"Scene 3:\nText: Two people having deep conversation\n"
        f"Image Prompt: Pixar-style 3D animation, two friends sitting on a bench at golden hour having a deep heartfelt conversation, warm tones, emotional connection\n"
        f"Voiceover: They listen more than they speak. That's their superpower.\n"
        "Duration: 5s\n\n"
        f"Scene 4:\nText: Ripple effect in water\n"
        f"Image Prompt: Pixar-style 3D animation, perfect stone dropped into still water creating expanding ripple circles, symbolic of emotional impact, serene lake\n"
        f"Voiceover: Every emotion you project creates a ripple in everyone around you.\n"
        "Duration: 5s\n\n"
        f"Scene 5:\nText: Person forgiving and letting go\n"
        f"Image Prompt: Pixar-style 3D animation, person releasing glowing butterflies from cupped hands into a sunset sky, letting go, forgiveness, beautiful\n"
        f"Voiceover: The ultimate strength isn't fighting. It's knowing when to let go.\n"
        "Duration: 5s\n\n"
        f"Scene 6:\nText: Sunrise over calm ocean\n"
        f"Image Prompt: Pixar-style 3D animation, breathtaking sunrise over a perfectly calm ocean, person standing at water's edge in silhouette, new beginning\n"
        f"Voiceover: Master your emotions. Master your life. Subscribe for daily wisdom.\n"
        "Duration: 5s\n"
    ),
    # Template 6 — Fear & Courage
    lambda t: (
        f"TITLE:\n{t}\n\n"
        "DESCRIPTION:\n"
        f"Face your fear of {t.lower()} with this mindset shift. #courage #fear #shorts\n\n"
        "TAGS:\ncourage, fear, bravery, mindset, self-improvement\n\n"
        "--------------------------------------\n\n"
        "SCENES:\n\n"
        f"Scene 1:\nText: Giant shadow looming over small person\n"
        f"Image Prompt: Pixar-style 3D animation, tiny person standing in front of their own massive dark shadow that towers over them, dramatic low angle, fear personified\n"
        f"Voiceover: The thing you're most afraid of about {t.lower()} is exactly what you need to face.\n"
        "Duration: 5s\n\n"
        f"Scene 2:\nText: Door with light behind it\n"
        f"Image Prompt: Pixar-style 3D animation, ominous closed door with brilliant white light streaming through the cracks, dark hallway, courage test, suspenseful\n"
        f"Voiceover: Behind every fear is a version of you that you've never met.\n"
        "Duration: 5s\n\n"
        f"Scene 3:\nText: Person taking first step forward\n"
        f"Image Prompt: Pixar-style 3D animation, close-up of a foot taking one bold step forward off a cliff edge, clouds below, leap of faith, breathtaking\n"
        f"Voiceover: Courage isn't the absence of fear. It's acting despite it.\n"
        "Duration: 5s\n\n"
        f"Scene 4:\nText: Lion roaring with determination\n"
        f"Image Prompt: Pixar-style 3D animation, majestic lion roaring with full power on a rocky outcrop, dramatic wind, golden mane flowing, power and courage\n"
        f"Voiceover: The lion doesn't ask permission. It takes what it deserves.\n"
        "Duration: 5s\n\n"
        f"Scene 5:\nText: Person standing in fire unburned\n"
        f"Image Prompt: Pixar-style 3D animation, determined person standing calmly in the center of roaring flames completely unharmed, phoenix-like resilience\n"
        f"Voiceover: What doesn't destroy you forges you into something unbreakable.\n"
        "Duration: 5s\n\n"
        f"Scene 6:\nText: Wings spreading from person's back\n"
        f"Image Prompt: Pixar-style 3D animation, person spreading magnificent glowing wings from their back, ascending into clouds, transformation, epic cinematic\n"
        f"Voiceover: Stop running from {t.lower()}. Start flying. Hit subscribe.\n"
        "Duration: 5s\n"
    ),
    # Template 7 — Social Dynamics
    lambda t: (
        f"TITLE:\n{t}\n\n"
        "DESCRIPTION:\n"
        f"The social dynamics rule about {t.lower()} they don't teach in school. #social #power #shorts\n\n"
        "TAGS:\nsocial dynamics, power, charisma, leadership, social skills\n\n"
        "--------------------------------------\n\n"
        "SCENES:\n\n"
        f"Scene 1:\nText: Person entering a room and everyone noticing\n"
        f"Image Prompt: Pixar-style 3D animation, charismatic person pushing open double doors and entering a grand room, everyone turning to look, dramatic entrance, power\n"
        f"Voiceover: Some people walk into a room and everything changes. Here's why {t.lower()} is their weapon.\n"
        "Duration: 5s\n\n"
        f"Scene 2:\nText: Wolf pack with alpha leading\n"
        f"Image Prompt: Pixar-style 3D animation, wolf pack running through snowy forest, alpha wolf leading with confidence, moonlight, pack dynamics, raw power\n"
        f"Voiceover: In every group, there's an unspoken hierarchy. Most people never even see it.\n"
        "Duration: 5s\n\n"
        f"Scene 3:\nText: Person speaking with authority\n"
        f"Image Prompt: Pixar-style 3D animation, powerful speaker at podium addressing large crowd, spotlight on them, dramatic shadows, commanding presence, influence\n"
        f"Voiceover: The person who speaks last always has the most power.\n"
        "Duration: 5s\n\n"
        f"Scene 4:\nText: Silent observer watching everything\n"
        f"Image Prompt: Pixar-style 3D animation, mysterious figure sitting quietly in corner of busy room, observing everything with sharp eyes, strategic patience, shadows\n"
        f"Voiceover: The loudest person in the room is rarely the strongest.\n"
        "Duration: 5s\n\n"
        f"Scene 5:\nText: Crown being placed on head\n"
        f"Image Prompt: Pixar-style 3D animation, golden crown slowly being placed on person's bowed head, rays of light, coronation moment, earned respect, regal\n"
        f"Voiceover: True authority about {t.lower()} is not demanded. It is earned through action.\n"
        "Duration: 5s\n\n"
        f"Scene 6:\nText: Person walking confidently into distance\n"
        f"Image Prompt: Pixar-style 3D animation, person in sharp suit walking confidently down a long corridor towards bright exit, determined stride, cinematic\n"
        f"Voiceover: Now you understand the game. Play it wisely. Subscribe for more power moves.\n"
        "Duration: 5s\n"
    ),
    # Template 8 — Kaizen / Self-Improvement
    lambda t: (
        f"TITLE:\n{t}\n\n"
        "DESCRIPTION:\n"
        f"The Japanese philosophy of continuous improvement applied to {t.lower()}. #kaizen #japan #shorts\n\n"
        "TAGS:\nkaizen, japan, self-improvement, growth, discipline\n\n"
        "--------------------------------------\n\n"
        "SCENES:\n\n"
        f"Scene 1:\nText: Bonsai tree being carefully trimmed\n"
        f"Image Prompt: Pixar-style 3D animation, elderly master carefully trimming a beautiful bonsai tree with small scissors, zen garden, soft natural light, patience\n"
        f"Voiceover: The Japanese have a word for mastering {t.lower()}. They call it Kaizen.\n"
        "Duration: 5s\n\n"
        f"Scene 2:\nText: Single drop of water on stone\n"
        f"Image Prompt: Pixar-style 3D animation, single water drop falling onto a stone surface, creating a small impression, macro shot, patience and persistence\n"
        f"Voiceover: One percent better every day. That's the only rule.\n"
        "Duration: 5s\n\n"
        f"Scene 3:\nText: Samurai practicing sword kata alone\n"
        f"Image Prompt: Pixar-style 3D animation, lone samurai practicing sword forms in misty bamboo forest at dawn, fluid motion, discipline, traditional\n"
        f"Voiceover: A samurai doesn't practice until he gets it right. He practices until he can't get it wrong.\n"
        "Duration: 5s\n\n"
        f"Scene 4:\nText: Small seedling growing into mighty tree\n"
        f"Image Prompt: Pixar-style 3D animation, time-lapse of tiny seedling growing into a massive ancient oak tree, seasons changing around it, growth metaphor\n"
        f"Voiceover: Massive results come from tiny consistent actions repeated daily.\n"
        "Duration: 5s\n\n"
        f"Scene 5:\nText: Craftsman perfecting pottery\n"
        f"Image Prompt: Pixar-style 3D animation, skilled potter's hands shaping clay on spinning wheel, warm kiln light, dedication to craft, wabi-sabi beauty\n"
        f"Voiceover: Don't aim for perfection. Aim for progress in {t.lower()}.\n"
        "Duration: 5s\n\n"
        f"Scene 6:\nText: Cherry blossoms falling peacefully\n"
        f"Image Prompt: Pixar-style 3D animation, beautiful cherry blossom petals falling in slow motion, person standing beneath with eyes closed, Japanese garden, serene\n"
        f"Voiceover: Start small. Stay consistent. Become legendary. Subscribe.\n"
        "Duration: 5s\n"
    ),
    # Template 9 — Thriller / Mystery
    lambda t: (
        f"TITLE:\n{t}\n\n"
        "DESCRIPTION:\n"
        f"The terrifying truth about {t.lower()} that's hidden in plain sight. #mystery #truth #shorts\n\n"
        "TAGS:\nmystery, truth, thriller, hidden, revelation\n\n"
        "--------------------------------------\n\n"
        "SCENES:\n\n"
        f"Scene 1:\nText: Flickering light in dark corridor\n"
        f"Image Prompt: Pixar-style 3D animation, long dark corridor with a single flickering fluorescent light, shadows dancing on walls, horror atmosphere, suspense\n"
        f"Voiceover: What if everything you knew about {t.lower()} was a lie?\n"
        "Duration: 5s\n\n"
        f"Scene 2:\nText: Hidden camera watching someone\n"
        f"Image Prompt: Pixar-style 3D animation, security camera POV watching a person walking through empty parking garage, green-tinted surveillance footage, eerie\n"
        f"Voiceover: They've been watching. And they know exactly what you're going to do next.\n"
        "Duration: 5s\n\n"
        f"Scene 3:\nText: Documents stamped CLASSIFIED\n"
        f"Image Prompt: Pixar-style 3D animation, stack of official documents with large red CLASSIFIED stamp, manila folder, dim desk lamp, government secrets\n"
        f"Voiceover: This information about {t.lower()} was buried for decades.\n"
        "Duration: 5s\n\n"
        f"Scene 4:\nText: Person connecting red strings on wall\n"
        f"Image Prompt: Pixar-style 3D animation, detective connecting photos and notes with red string on a cork board wall, intense focus, conspiracy investigation\n"
        f"Voiceover: But when you connect the dots, the pattern becomes terrifyingly clear.\n"
        "Duration: 5s\n\n"
        f"Scene 5:\nText: Truth revealed in bright flash\n"
        f"Image Prompt: Pixar-style 3D animation, dark room suddenly illuminated by blinding flash of light, truth revealed, dramatic shadows retreating, revelation moment\n"
        f"Voiceover: The truth has always been right in front of you.\n"
        "Duration: 5s\n\n"
        f"Scene 6:\nText: Person looking directly at camera\n"
        f"Image Prompt: Pixar-style 3D animation, intense person looking directly at camera breaking the fourth wall, serious expression, dramatic close-up, urgent\n"
        f"Voiceover: Now you know about {t.lower()}. The question is — what will you do about it? Subscribe.\n"
        "Duration: 5s\n"
    ),
]


def get_fallback_script(topic_title=None):
    """Generate a UNIQUE fallback script adapted to the topic title.
    
    Uses a pool of 10 distinct templates and randomly selects one,
    then inserts the topic title throughout to create unique content.
    """
    title = topic_title or "The Secret to Unlocking Your True Potential"
    safe_print(f"[SCRIPT] Generating dynamic fallback script for: {title}")
    
    # Pick a random template — ensures variety across runs
    template_fn = random.choice(_FALLBACK_TEMPLATES)
    return template_fn(title)


def _validate_gemini_output(script_text: str) -> bool:
    """Check if Gemini's output has the required format markers."""
    has_scenes = bool(re.search(r'Scene\s*\d', script_text, re.IGNORECASE))
    has_image_prompts = bool(re.search(r'Image\s*Prompt\s*:', script_text, re.IGNORECASE))
    has_voiceover = bool(re.search(r'Voiceover\s*:', script_text, re.IGNORECASE))
    
    # Count scenes — need at least 3
    scene_count = len(re.findall(r'Scene\s*\d', script_text, re.IGNORECASE))
    prompt_count = len(re.findall(r'Image\s*Prompt\s*:', script_text, re.IGNORECASE))
    voiceover_count = len(re.findall(r'Voiceover\s*:', script_text, re.IGNORECASE))
    
    safe_print(f"[SCRIPT] Validation: {scene_count} scenes, {prompt_count} image prompts, {voiceover_count} voiceovers")
    
    return has_scenes and has_image_prompts and has_voiceover and scene_count >= 3


def _normalize_gemini_script(raw_text: str) -> str:
    """Normalize Gemini's output to the standard format expected by the pipeline.
    
    Handles variations like:
    - **Scene 1:** -> Scene 1:
    - ### Scene 1 -> Scene 1:
    - **Image Prompt:** -> Image Prompt:
    - **Voiceover:** -> Voiceover:
    """
    text = raw_text
    
    # Remove markdown bold/italic markers around known tags
    text = re.sub(r'\*{1,3}(Scene\s*\d+)\*{1,3}', r'\1', text, flags=re.IGNORECASE)
    text = re.sub(r'\*{1,3}(Image\s*Prompt\s*:)', r'\1', text, flags=re.IGNORECASE)
    text = re.sub(r'\*{1,3}(Voiceover\s*:)', r'\1', text, flags=re.IGNORECASE)
    text = re.sub(r'\*{1,3}(Text\s*:)', r'\1', text, flags=re.IGNORECASE)
    text = re.sub(r'\*{1,3}(Duration\s*:)', r'\1', text, flags=re.IGNORECASE)
    text = re.sub(r'\*{1,3}(TITLE\s*:)', r'\1', text, flags=re.IGNORECASE)
    text = re.sub(r'\*{1,3}(DESCRIPTION\s*:)', r'\1', text, flags=re.IGNORECASE)
    text = re.sub(r'\*{1,3}(TAGS\s*:)', r'\1', text, flags=re.IGNORECASE)
    text = re.sub(r'\*{1,3}(SCENES\s*:?)\*{1,3}', r'\1', text, flags=re.IGNORECASE)
    
    # Remove markdown heading markers (### Scene 1 -> Scene 1)
    text = re.sub(r'^#{1,4}\s*', '', text, flags=re.MULTILINE)
    
    return text.strip()


def generate_script(topic: dict) -> str:
    """Generate script using Gemini API; falls back to dynamic topic-aware content if unavailable."""
    title = topic.get('title', 'Unknown Topic')
    safe_print(f"[SCRIPT] Generating script for: {title}")

    script_text = ""
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        safe_print("⚠️ [SCRIPT] GEMINI_API_KEY not found. Checking .env file directly...")
        # Manual .env fallback
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if line.strip().startswith("GEMINI_API_KEY="):
                        api_key = line.strip().split("=", 1)[1].strip()
                        os.environ["GEMINI_API_KEY"] = api_key
                        safe_print("[SCRIPT] Loaded GEMINI_API_KEY from .env file manually.")
                        break

    if api_key:
        try:
            import requests
            
            # Generate a unique session ID to prevent Gemini from caching responses
            session_id = uuid.uuid4().hex[:12]
            timestamp_seed = datetime.now().strftime("%Y%m%d%H%M%S")
            
            prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "gemini_system.txt")
            if os.path.exists(prompt_path):
                with open(prompt_path, "r", encoding="utf-8") as f:
                    system_rules = f.read()
            else:
                system_rules = (
                    "You are a master YouTube Shorts scriptwriter whose videos regularly get 1M+ views. "
                    "Write a 6-scene faceless video script optimized for MAXIMUM viewer retention and virality. "
                    "RULES:\n"
                    "1. The first 3 seconds MUST have a 'hook' that makes it impossible to scroll away.\n"
                    "2. The pacing must be fast, aggressive, and highly engaging.\n"
                    "3. Each scene MUST have a line starting with 'Image Prompt:' describing a Pixar 3D style cinematic visual.\n"
                    "4. Each scene MUST have a line starting with 'Voiceover:' with the narrator text.\n"
                    "5. Each scene MUST have a line starting with 'Text:' with a short scene description.\n"
                    "6. Each scene MUST have 'Duration: 5s' at the end.\n"
                    "7. The final scene must loop perfectly back to the beginning hook.\n"
                    "Total duration must be 30-60 seconds.\n\n"
                    "OUTPUT FORMAT (follow this EXACTLY):\n"
                    "TITLE:\n<title>\n\n"
                    "DESCRIPTION:\n<description with hashtags>\n\n"
                    "TAGS:\n<comma separated tags>\n\n"
                    "--------------------------------------\n\n"
                    "SCENES:\n\n"
                    "Scene 1:\nText: <scene description>\n"
                    "Image Prompt: <detailed Pixar 3D cinematic image description>\n"
                    "Voiceover: <narrator text>\nDuration: 5s\n\n"
                    "Scene 2:\n... (repeat for all 6 scenes)"
                )

            creative_angles = [
                "Make it an intense, fast-paced psychological thriller short.",
                "Make it highly philosophical, stoic, and deeply thought-provoking.",
                "Make it an aggressive, high-energy motivational wake-up call.",
                "Make it a spooky, mysterious 'dark psychology' secret.",
                "Make it a highly relatable everyday scenario that blows the viewer's mind.",
                "Make it an ancient wisdom parable adapted for modern life.",
                "Make it a mind-bending reverse psychology trick.",
                "Make it a rapid-fire '5 signs' listicle with shocking reveals.",
            ]
            chosen_angle = random.choice(creative_angles)
            
            full_prompt = (
                f"{system_rules}\n\n"
                f"STRICT TOPIC TO FOCUS ON: {title}\n"
                f"CREATIVE DIRECTION: {chosen_angle}\n\n"
                f"UNIQUENESS SEED: {session_id}-{timestamp_seed}\n"
                f"CRITICAL REQUIREMENT: Do NOT repeat old scripts. Invent completely NEW scenes, "
                f"NEW visual descriptions, and a UNIQUE storyline that has never been told before. "
                f"Be wildly creative and original. Every image prompt must be unique and vivid."
            )
            
            safe_print(f"[SCRIPT] Calling Gemini REST API (Angle: {chosen_angle[:40]}..., Session: {session_id}).")
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {
                    "temperature": 1.2,      # High creativity
                    "topP": 0.95,
                    "topK": 40,
                    "maxOutputTokens": 2048,
                }
            }
            
            # 30 second timeout — Gemini can be slow for complex prompts
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                try:
                    raw_text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                    # Normalize markdown formatting variations
                    script_text = _normalize_gemini_script(raw_text)
                    
                    # Validate the script has proper structure
                    if _validate_gemini_output(script_text):
                        safe_print("[SCRIPT] ✅ Successfully retrieved and validated script from Gemini.")
                    else:
                        safe_print("[SCRIPT] ⚠️ Gemini script missing required format. Retrying with stricter prompt...")
                        # RETRY with an even stricter format prompt
                        retry_prompt = (
                            f"Write a YouTube Shorts script about '{title}' with EXACTLY this format:\n\n"
                            "TITLE:\n<title>\n\nDESCRIPTION:\n<desc>\n\nTAGS:\n<tags>\n\n"
                            "--------------------------------------\n\nSCENES:\n\n"
                            "Scene 1:\nText: <desc>\nImage Prompt: Pixar-style 3D animation, <visual>\n"
                            "Voiceover: <narration>\nDuration: 5s\n\n"
                            "(Repeat for 6 scenes total. Each scene MUST have Text, Image Prompt, Voiceover, Duration.)\n\n"
                            f"UNIQUENESS SEED: RETRY-{uuid.uuid4().hex[:8]}\n"
                            f"CREATIVE DIRECTION: {chosen_angle}\n"
                            "Be original. Do NOT reuse any previous content."
                        )
                        retry_payload = {
                            "contents": [{"parts": [{"text": retry_prompt}]}],
                            "generationConfig": {"temperature": 1.0, "maxOutputTokens": 2048}
                        }
                        retry_resp = requests.post(url, json=retry_payload, headers={'Content-Type': 'application/json'}, timeout=30)
                        if retry_resp.status_code == 200:
                            retry_data = retry_resp.json()
                            try:
                                retry_raw = retry_data['candidates'][0]['content']['parts'][0]['text'].strip()
                                retry_text = _normalize_gemini_script(retry_raw)
                                if _validate_gemini_output(retry_text):
                                    script_text = retry_text
                                    safe_print("[SCRIPT] ✅ Retry successful — valid script obtained.")
                                else:
                                    safe_print("[SCRIPT] ⚠️ Retry also produced invalid format. Using dynamic fallback.")
                                    script_text = get_fallback_script(title)
                            except (KeyError, IndexError):
                                safe_print("[SCRIPT] Retry returned malformed JSON. Using dynamic fallback.")
                                script_text = get_fallback_script(title)
                        else:
                            safe_print(f"[SCRIPT] Retry failed HTTP {retry_resp.status_code}. Using dynamic fallback.")
                            script_text = get_fallback_script(title)
                except (KeyError, IndexError):
                    safe_print("[SCRIPT] Gemini returned malformed JSON. Using dynamic fallback.")
                    script_text = get_fallback_script(title)
            else:
                safe_print(f"[SCRIPT] Gemini REST API error HTTP {response.status_code}. Using dynamic fallback.")
                try:
                    error_detail = response.json().get("error", {}).get("message", "Unknown")
                    safe_print(f"[SCRIPT] Error detail: {error_detail}")
                except Exception:
                    pass
                script_text = get_fallback_script(title)
        
        except Exception as e:
            if "Timeout" in type(e).__name__:
                safe_print(f"⚠️ [SCRIPT] Gemini API timed out after 30 seconds! Falling back.")
            else:
                safe_print(f"⚠️ [SCRIPT] Gemini REST API exception: {e}. Falling back.")
            script_text = get_fallback_script(title)
    else:
        safe_print("⚠️ [SCRIPT] GEMINI_API_KEY not found anywhere. Using dynamic fallback.")
        script_text = get_fallback_script(title)

    os.makedirs("scripts", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    script_file = f"scripts/script_{timestamp}.txt"
    with open(script_file, "w", encoding="utf-8") as f:
        f.write(script_text)

    safe_print(f"[SUCCESS] Script saved to {script_file}")
        
    return script_file


def sync_to_github():
    """Automatically push new scripts to GitHub so Render can see them."""
    safe_print("[SYNC] Pushing new scripts to GitHub...")
    try:
        import subprocess
        subprocess.run(["git", "add", "scripts/*.txt"], check=True)
        subprocess.run(["git", "commit", "-m", "Automated AI script generation"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        safe_print("[SYNC] Successfully pushed to Cloud!")
    except Exception as e:
        safe_print(f"[SYNC] Error pushing to GitHub: {e}")

if __name__ == "__main__":
    import sys, json
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            topic = json.load(f)
        generate_script(topic)
    else:
        safe_print("Usage: python script_agent.py <path_to_topic_json>")
