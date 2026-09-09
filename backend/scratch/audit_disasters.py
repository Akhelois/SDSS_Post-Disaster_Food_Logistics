import urllib.request
import json

try:
    req = urllib.request.Request('http://localhost:8000/', headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    
    zones = data.get('priority_zones', [])
    print(f"Total priority zones returned: {len(zones)}")
    
    type_counts = {}
    for z in zones:
        dtype = z.get('disaster_type', 'Tidak Diketahui')
        type_counts[dtype] = type_counts.get(dtype, 0) + 1
    
    print("Breakdown per jenis bencana:")
    for k, v in type_counts.items():
        print(f"  - {k}: {v} zona")
        
    print("\nDaftar Desa / Zona:")
    for i, z in enumerate(zones):
        desa = z.get('desa', '-')
        dtype = z.get('disaster_type', '-')
        score = z.get('priority_score', 0)
        pop = z.get('population', 0)
        count = z.get('count', 0)
        date = z.get('event_date', '-')
        print(f"{i+1}. {desa} | Tipe: {dtype} | Skor: {score} | Bangunan Rusak: {count} | Jiwa: {pop} | Tanggal: {date}")

except Exception as e:
    print(f"Error fetching localhost:8000: {e}")
