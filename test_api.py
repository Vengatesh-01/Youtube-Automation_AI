import requests
import urllib.parse

def test_api(name, url):
    print(f"Testing {name}...")
    try:
        res = requests.get(url, timeout=10)
        print(f"[{name}] Status: {res.status_code}")
        if res.status_code == 200:
            print(f"[{name}] Success! Received {len(res.content)} bytes.")
            return True
        else:
            print(f"[{name}] Failed with response: {res.text[:200]}")
    except Exception as e:
        print(f"[{name}] Exception: {e}")
    return False

prompt = urllib.parse.quote("a beautiful sunrise over the mountains, 3d animation style")

apis = {
    "Pollinations (Turbo)": f"https://image.pollinations.ai/prompt/{prompt}?model=turbo",
    "Pollinations (Flux)": f"https://image.pollinations.ai/prompt/{prompt}?model=flux",
    "Pollinations (No model)": f"https://image.pollinations.ai/prompt/{prompt}",
    "Airforce (v1/imagine)": f"https://api.airforce/v1/imagine?prompt={prompt}",
    "Airforce (imagine)": f"https://api.airforce/imagine?prompt={prompt}",
}

for name, url in apis.items():
    test_api(name, url)
    print("-" * 40)
