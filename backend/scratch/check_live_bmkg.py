import urllib.request
import json

try:
    req = urllib.request.Request('https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    quakes = data.get('Infogempa', {}).get('gempa', [])
    print(f"Total gempa BMKG M5.0+ terbaru: {len(quakes)}")
    for i, q in enumerate(quakes[:10]):
        mag = q.get('Magnitude')
        tgl = q.get('Tanggal')
        jam = q.get('Jam')
        wil = q.get('Wilayah')
        ked = q.get('Kedalaman')
        coords = q.get('Coordinates')
        print(f"{i+1}. M{mag} | {tgl} {jam} | {wil} | Kedalaman: {ked} | Coords: {coords}")
except Exception as e:
    print(f"Error: {e}")
