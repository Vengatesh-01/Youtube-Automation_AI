import os
from google import genai
from utils import safe_print

def generate_metadata(topic: str, script_text: str):
    """
    Generate YouTube Title, Description, and Tags based on the topic and script.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        safe_print("[Metadata] GEMINI_API_KEY not found. Using simple fallback metadata.")
        return {
            "title": f"{topic} | English Podcast",
            "description": f"Listen to our podcast about {topic}.\n\n#english #podcast #learning",
            "tags": ["english", "podcast", "learning", "spoken english"]
        }

    prompt = f"""
You are an expert YouTube SEO specialist for an English speaking practice podcast channel.
The user is uploading a video with the following topic:
"{topic}"

Here is a snippet of the script for context:
{script_text[:500]}

Generate SEO-optimized metadata for this video in JSON format EXACTLY matching this structure:
{{
    "title": "A catchy, relevant YouTube title (max 70 chars)",
    "description": "A relevant description (2-3 sentences), followed by 3-5 relevant hashtags.",
    "tags": ["tag1", "tag2", "tag3"]
}}
Do NOT include markdown formatting like ```json ... ```, just output the raw JSON.
Ensure tags are highly relevant to English learning, speaking practice, etc.
"""
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
        )
        
        import json
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        data = json.loads(text)
        safe_print("[Metadata] Successfully generated SEO metadata via Gemini.")
        return data
    except Exception as e:
        safe_print(f"[Metadata] Error generating metadata: {e}")
        return {
            "title": f"{topic} | English Podcast",
            "description": f"Listen to our podcast about {topic}.\n\n#english #podcast #learning",
            "tags": ["english", "podcast", "learning", "spoken english"]
        }
