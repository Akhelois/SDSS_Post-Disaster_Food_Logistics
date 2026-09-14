import json, os, sys
import pandas as pd
import numpy as np

with open("output/sdss_result.geojson", "r", encoding="utf-8") as f:
    data = json.load(f)

features = data.get("features", [])
records = []
for feat in features:
    props = feat.get("properties", {})
    geom = feat.get("geometry", {})
    coords = geom.get("coordinates", [0, 0])
    props["lon"] = coords[0]
    props["lat"] = coords[1]
    records.append(props)

df = pd.DataFrame(records)
print(f"Loaded {len(df)} points. Columns: {list(df.columns)}")

desa_col = 'desa' if 'desa' in df.columns else 'wilayah'
df_valid = df[df[desa_col].notna()].copy()
print(f"Valid desa rows: {len(df_valid)}, unique desa: {df_valid[desa_col].nunique()}")

zones = []
for name, group in df_valid.groupby(desa_col):
    damage_count = len(group)
    if damage_count < 5:
        # Check if simulated or keep real
        damage_count = damage_count
    
    dt_list = [v for v in group.get('disaster_type', []) if pd.notna(v) and str(v).strip() != '']
    dt = dt_list[0] if dt_list else 'Bencana Alam'
    
    event_date = group.get('event_date', pd.Series()).dropna()
    elapsed = 24.0 # default
    if not event_date.empty:
        try:
            ed = pd.to_datetime(event_date.iloc[0])
            elapsed = (pd.Timestamp.now() - ed).total_seconds() / 3600.0
        except Exception:
            pass
            
    zones.append({
        'desa': str(name),
        'count': damage_count,
        'disaster_type': dt,
        'elapsed_hours': round(elapsed, 1)
    })

sys.path.insert(0, '.')
from services.logistics import calculate_priority_scores
rz = calculate_priority_scores(zones)

print(f"\nTotal red zones: {len(rz)}")
for z in rz[:15]:
    pct = round(z['priority_score'] * 100, 1)
    print(f"{z['desa']:<35} | Score: {z['priority_score']:.4f} ({pct:5.1f}%) | Label: {z['priority_label']:<6} | Count: {z['count']:<3} | Pop: {z['population']:<6} | Elapsed: {z.get('elapsed_hours')}h")
