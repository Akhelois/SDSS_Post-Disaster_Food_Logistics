"""
Refresh timestamps pada sdss_result.geojson agar data tidak kadaluarsa.
Jalankan: python update_dates.py
"""
import json
from datetime import datetime

GEOJSON_PATH = 'output/sdss_result.geojson'

with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

now_iso = datetime.now().isoformat()
updated = 0

for feature in data.get('features', []):
    if 'properties' in feature:
        feature['properties']['processed_at'] = now_iso
        # Juga update scene_id jika formatnya datetime
        scene_id = feature['properties'].get('scene_id', '')
        if 'T' in str(scene_id) and '-' in str(scene_id):
            feature['properties']['scene_id'] = now_iso
        updated += 1

with open(GEOJSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print(f"Updated {updated} features in {GEOJSON_PATH}")
print(f"New timestamp: {now_iso}")
