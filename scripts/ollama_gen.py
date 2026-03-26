import requests
import json
import os

def generate_script(prompt, model="llama3"):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": f"""
        Act as a World-Class Viral Script Strategist for YouTube Shorts. 
        Your goal is absolute viewer retention for a 20-40 second video about: {prompt}.
        
        SCRIPT RULES (STRICT ENFORCEMENT):
        1. LENGTH: 20-40 seconds of speaking duration.
        2. HOOK: Strong hook in the first 3 seconds to grab attention.
        3. PACING: Use "..." for dramatic pauses to control pacing.
        4. ENDING: Must have a clear message and a satisfying ending/mic-drop statement.
        
        Output ONLY the spoken words. 
        NO stage directions. NO labels like 'Hook:'. 
        Include "..." where a dramatic pause is needed.
        """,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        script = response.json().get('response', '')
        # Clean up any potential AI artifact like "Here is your script:"
        lines = script.strip().split('\n')
        if len(lines) > 0 and (":" in lines[0] or "script" in lines[0].lower()):
             script = "\n".join(lines[1:])
        return script.strip()
    except Exception as e:
        print(f"Error generating script: {e}")
        return None
