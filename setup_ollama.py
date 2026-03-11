import requests
import time
import subprocess
import sys

def setup_ollama_for_automation():
    print("🎬 [SETUP] Starting Ollama Configuration for YouTube Automation...")
    
    # 1. Check if Ollama is running
    url = "http://localhost:11434/api/tags"
    try:
        response = requests.get(url, timeout=5)
        print("✅ [CHECK] Ollama is running and accessible!")
    except Exception:
        print("❌ [ERROR] Ollama is not running. Please open the Ollama application first.")
        return

    # 2. Pull Llama3 model
    print("⏳ [PULL] Pulling Llama3 model (this may take a few minutes if first time)...")
    try:
        # Using subprocess to show progress in terminal
        process = subprocess.Popen(["ollama", "pull", "llama3"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            print(line, end="")
        process.wait()
        
        if process.returncode == 0:
            print("✅ [SUCCESS] Llama3 model is ready!")
        else:
            print("❌ [ERROR] Failed to pull Llama3 model.")
            return
    except FileNotFoundError:
        print("❌ [ERROR] 'ollama' command not found in PATH. Please restart your terminal or add Ollama to PATH.")
        return

    # 3. Final Verification
    print("\n🚀 [VERIFY] Running a quick test generation...")
    from script_agent import generate_script
    test_topic = {"title": "The Power of Consistency"}
    script_file = generate_script(test_topic)
    
    if script_file:
        print(f"\n✨ [COMPLETE] System is fully integrated! Test script saved to: {script_file}")
        print("You can now run your main automation pipeline, and it will use Llama3 automatically.")
    else:
        print("⚠️ [WARNING] Setup finished but test generation failed. Check if Ollama is responsive.")

if __name__ == "__main__":
    setup_ollama_for_automation()
