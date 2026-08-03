import os
import urllib.request
import re

FONTS_DIR = "e:/project/AI_Smart_Bus_Stop_Assistant/kiosk_ui/static/fonts"
os.makedirs(FONTS_DIR, exist_ok=True)

url = "https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap"

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        css_content = response.read().decode('utf-8')
except Exception as e:
    print("Error fetching CSS:", e)
    exit(1)

# Find all url() in css_content
urls = re.findall(r'url\((https://[^)]+)\)', css_content)
css_local = css_content

for i, font_url in enumerate(set(urls)):
    filename = f"font_{i}.woff2"
    filepath = os.path.join(FONTS_DIR, filename)
    
    # download font
    try:
        font_req = urllib.request.Request(font_url, headers=headers)
        with urllib.request.urlopen(font_req) as response:
            with open(filepath, 'wb') as f:
                f.write(response.read())
        print(f"Downloaded {filename}")
        
        # replace in css
        css_local = css_local.replace(font_url, f"./{filename}")
    except Exception as e:
        print("Error downloading font:", e)

with open(os.path.join(FONTS_DIR, "fonts.css"), 'w', encoding='utf-8') as f:
    f.write(css_local)
print("Finished downloading fonts and created fonts.css")
