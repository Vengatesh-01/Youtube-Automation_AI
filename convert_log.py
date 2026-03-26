with open('sadtalker_run_out.txt', 'rb') as f:
    data = f.read()
try:
    text = data.decode('utf-16le')
except Exception:
    text = data.decode('utf-8', errors='replace')
with open('sadtalker_run_out_utf8.txt', 'w', encoding='utf-8') as f:
    f.write(text)
print("Converted sadtalker_run_out.txt to utf-8")
