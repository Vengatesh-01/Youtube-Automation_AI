import os
from google import genai
from utils import safe_print

def generate_metadata(topic: str, script_text: str):
    """
    Generate YouTube Title, Description, and Tags based on the topic and script.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    safe_topic = topic.strip() if topic and topic.strip() else "English Practice"
    if not api_key:
        safe_print("[Metadata] GEMINI_API_KEY not found. Using simple fallback metadata.")
        return {
            "title": f"{safe_topic} | English Podcast",
            "description": f"Listen to our podcast about {safe_topic}.\n\n#english #podcast #learning",
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
    # Try models in order of preference, falling back if unavailable
    MODELS_TO_TRY = ['gemini-2.0-flash-lite', 'gemini-1.5-flash', 'gemini-2.5-flash', 'gemini-3.8-flash']
    try:
        client = genai.Client(api_key=api_key)
        response = None
        last_err = None
        for model_name in MODELS_TO_TRY:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                safe_print(f"[Metadata] Using model: {model_name}")
                break
            except Exception as model_err:
                safe_print(f"[Metadata] Model {model_name} unavailable: {model_err}")
                last_err = model_err
        if response is None:
            raise last_err
        
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
            "title": f"{safe_topic} | English Podcast",
            "description": f"Listen to our podcast about {safe_topic}.\n\n#english #podcast #learning",
            "tags": ["english", "podcast", "learning", "spoken english"]
        }
