import pyttsx3, os, re

script = open('scripts/overcoming_guilt.txt', encoding='utf-8').read()
speech = re.sub(r'\[.*?\]', '', script).strip()
print("Script text:\n", speech[:200], "...")

engine = pyttsx3.init()
voices = engine.getProperty('voices')
chosen = None
for v in voices:
    if any(k in v.name.lower() for k in ('david','zira','andrew','mark','aria')):
        chosen = v
        break
if chosen:
    engine.setProperty('voice', chosen.id)
    print(f'Using voice: {chosen.name}')

engine.setProperty('rate', 155)
engine.setProperty('volume', 0.95)

os.makedirs('voiceovers', exist_ok=True)
out = 'voiceovers/guilt_voice.wav'
engine.save_to_file(speech, out)
engine.runAndWait()

if os.path.exists(out):
    print(f'SUCCESS: {out}  ({os.path.getsize(out):,} bytes)')
else:
    print('ERROR: file not created')
