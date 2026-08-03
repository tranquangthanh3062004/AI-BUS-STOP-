import os
import urllib.request

LIBS_DIR = "kiosk_ui/static/libs"
os.makedirs(LIBS_DIR, exist_ok=True)

files_to_download = [
    ("https://unpkg.com/leaflet@1.9.4/dist/leaflet.css", "leaflet.css"),
    ("https://unpkg.com/leaflet@1.9.4/dist/leaflet.js", "leaflet.js"),
    ("https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.css", "leaflet-routing-machine.css"),
    ("https://unpkg.com/leaflet-routing-machine@latest/dist/leaflet-routing-machine.js", "leaflet-routing-machine.js")
]

for url, filename in files_to_download:
    filepath = os.path.join(LIBS_DIR, filename)
    print(f"Downloading {filename}...")
    try:
        urllib.request.urlretrieve(url, filepath)
        print(f"Success: {filename}")
    except Exception as e:
        print(f"Failed to download {filename}: {e}")
