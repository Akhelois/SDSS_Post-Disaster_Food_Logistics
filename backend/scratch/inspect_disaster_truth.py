import json

with open("output/sdss_result.geojson", "r", encoding="utf-8") as f:
    data = json.load(f)

features = data.get("features", [])
print(f"Total titik bencana dalam geojson: {len(features)}")

disasters_by_type = {}
for feat in features:
    props = feat.get("properties", {})
    geom = feat.get("geometry", {})
    coords = geom.get("coordinates", [0, 0])
    dtype = props.get("disaster_type", "Tidak Terdefinisi")
    wilayah = props.get("wilayah", props.get("desa", "Unknown"))
    date = props.get("event_date", props.get("scene_id", "-"))
    source = props.get("source", "Unknown")
    
    if dtype not in disasters_by_type:
        disasters_by_type[dtype] = []
    disasters_by_type[dtype].append({
        "wilayah": wilayah,
        "coords": coords,
        "date": date,
        "source": source
    })

print("\n=== RINGKASAN BENCANA DI DALAM SISTEM ===")
for dtype, items in disasters_by_type.items():
    print(f"\n[Jenis Bencana: {dtype}] - Total Titik: {len(items)}")
    # Print distinct locations
    locations = {}
    for it in items:
        w = it["wilayah"]
        locations[w] = locations.get(w, 0) + 1
    for loc, count in list(locations.items())[:8]:
        print(f"  - Wilayah: {loc} ({count} titik/scene)")
