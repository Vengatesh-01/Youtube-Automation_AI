import subprocess
import os

def text_to_speech(text, output_file="outputs/audio.wav", model_path="assets/piper_model.onnx"):
    """
    Converts text to speech using Piper TTS with pacing refinements.
    """
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 🕒 VIRAL PACING REFINEMENT
    # Convert '...' into long pauses for dramatic delivery
    refined_text = text.replace("...", ", , , ") # Adding virtual commas for Piper to slow down
    refined_text = refined_text.replace(".", ". ").replace("?", "? ").replace("!", "! ")
    
    try:
        process = subprocess.Popen(
            ['piper', '--model', model_path, '--output_file', output_file],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input=refined_text)
        
        if process.returncode == 0:
            print(f"Audio generated: {output_file}")
            return True
        else:
            print(f"Piper error: {stderr}")
            return False
    except Exception as e:
        print(f"Error running Piper: {e}")
        return False

if __name__ == "__main__":
    test_text = "Hello, this is a test of the Piper TTS system for my YouTube Shorts."
    text_to_speech(test_text)
