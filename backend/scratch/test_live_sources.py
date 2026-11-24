import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

# 1. BMKG Autogempa (Latest)
print("=== 1. BMKG Autogempa ===")
try:
    r = requests.get("https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json", headers=headers, timeout=10)
    if r.status_code == 200:
        g = r.json().get('Infogempa', {}).get('gempa', {})
        print(f"Latest Quake: M{g.get('Magnitude')} - {g.get('Wilayah')} ({g.get('Tanggal')} {g.get('Jam')})")
        print(f"Coords: {g.get('Coordinates')}, Kedalaman: {g.get('Kedalaman')}, Potensi: {g.get('Potensi')}")
    else:
        print(f"BMKG Autogempa HTTP {r.status_code}")
except Exception as e:
    print(f"BMKG Autogempa error: {e}")

# 2. BMKG Gempaterkini (M5.0+)
print("\n=== 2. BMKG Gempaterkini (M5.0+) ===")
try:
    r = requests.get("https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json", headers=headers, timeout=10)
    if r.status_code == 200:
        quakes = r.json().get('Infogempa', {}).get('gempa', [])
        print(f"Total M5.0+ quakes listed: {len(quakes)}")
        for q in quakes[:3]:
            print(f"  - M{q.get('Magnitude')} | {q.get('Wilayah')} | {q.get('Tanggal')} {q.get('Jam')}")
    else:
        print(f"BMKG Gempaterkini HTTP {r.status_code}")
except Exception as e:
    print(f"BMKG Gempaterkini error: {e}")

# 3. BMKG Gempa Dirasakan
print("\n=== 3. BMKG Gempa Dirasakan ===")
try:
    r = requests.get("https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json", headers=headers, timeout=10)
    if r.status_code == 200:
        quakes = r.json().get('Infogempa', {}).get('gempa', [])
        print(f"Total felt quakes: {len(quakes)}")
        for q in quakes[:3]:
            print(f"  - M{q.get('Magnitude')} | {q.get('Wilayah')} | Dirasakan: {q.get('Dirasakan')}")
    else:
        print(f"BMKG Gempa Dirasakan HTTP {r.status_code}")
except Exception as e:
    print(f"BMKG Gempa Dirasakan error: {e}")

# 4. PetaBencana Reports (72 hours)
print("\n=== 4. PetaBencana Reports (72h) ===")
try:
    r = requests.get("https://api.petabencana.id/reports?timeperiod=259200", headers=headers, timeout=15)
    if r.status_code == 200:
        data = r.json()
        geoms = data.get('result', {}).get('objects', {}).get('output', {}).get('geometries', [])
        print(f"Total PetaBencana raw geometries: {len(geoms)}")
        confirmed = [g for g in geoms if g.get('properties', {}).get('status') == 'confirmed']
        print(f"Confirmed reports: {len(confirmed)}")
        for g in geoms[:5]:
            p = g.get('properties', {})
            print(f"  - [{p.get('status')}] {p.get('disaster_type')} in {p.get('tags', {}).get('city', p.get('text', 'Unknown'))[:40]} | created_at: {p.get('created_at')}")
    else:
        print(f"PetaBencana HTTP {r.status_code}")
except Exception as e:
    print(f"PetaBencana error: {e}")
