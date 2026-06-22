import requests

query = """
[out:json][timeout:15];
way["building"](around:1500,-0.18,119.84);
out geom;
"""
headers = {'User-Agent': 'SDSS-Disaster-Logistics-Research/1.0'}

endpoints = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter"
]

for url in endpoints:
    print("Fetching from", url)
    try:
        r = requests.get(url, params={'data': query}, headers=headers, timeout=25)
        print("Status:", r.status_code)
        if r.status_code == 200:
            data = r.json()
            print("Success! Found", len(data.get('elements', [])), "elements.\n")
        else:
            print("Response:", r.text[:200], "\n")
    except Exception as e:
        print("Error:", e, "\n")
