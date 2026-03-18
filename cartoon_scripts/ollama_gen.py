import requests
import json
import os

def generate_script(prompt, model="llama3"):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": f"""
        Act as a World-Class Viral Script Strategist for YouTube Shorts. 
        Your goal is absolute viewer retention for a 15-30 second video about: {prompt}.
        
        SCRIPT RULES (STRICT ENFORCEMENT):
        1. RHYTHM: Every single sentence MUST be exactly 5 to 7 words. No more.
        2. PACING: Use "..." for a 1-second dramatic pause after the Hook and before the Payoff.
        
        STRUCTURE:
        - 0-2s: THE HOOK. A shock statement or a pattern interrupt. (Max 7 words).
        - 2-5s: THE AGITATION. Why this matters or the hidden danger.
        - 5-25s: THE REVEAL. The counter-intuitive solution or "secret".
        - 25-30s: THE MIC DROP. A powerful final insight.
        
        EXAMPLES OF RHYTHMIC STYLE:
        "Most people think wealth is luck..."
        "But the rich have a secret..."
        "It's called the compound effect rule."
        
        Output ONLY the spoken words. 
        NO stage directions. NO labels like 'Hook:'. 
        Include "..." where a dramatic pause is needed.
        """,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
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
