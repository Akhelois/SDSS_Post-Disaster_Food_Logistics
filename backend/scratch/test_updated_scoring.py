import json, os, sys
import numpy as np
import pandas as pd

with open("output/sdss_result.geojson", "r", encoding="utf-8") as f:
    data = json.load(f)

features = data.get("features", [])
records = []
for feat in features:
    props = feat.get("properties", {})
    records.append(props)

df = pd.DataFrame(records)
desa_col = 'desa' if 'desa' in df.columns else 'wilayah'
df_valid = df[df[desa_col].notna()].copy()

zones = []
for name, group in df_valid.groupby(desa_col):
    damage_count = len(group)
    dt_list = [v for v in group.get('disaster_type', []) if pd.notna(v) and str(v).strip() != '']
    dt = dt_list[0] if dt_list else 'Bencana Alam'
    event_date = group.get('event_date', pd.Series()).dropna()
    elapsed = 24.0
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

print(f"Total zones: {len(zones)}")

def test_scoring_model(zones):
    AVG_KK_SIZE = 4
    
    # Calculate affected population consistently
    for z in zones:
        count = z.get('count', 1)
        z['population'] = max(count * AVG_KK_SIZE, AVG_KK_SIZE)

    # In disaster science (CRED EM-DAT, BNPB), damage count & population follow power-law / heavy-tailed distributions.
    # Log-scaling: log1p(x) prevents single extreme outliers from compressing all other critical zones to near zero.
    log_d = [np.log1p(z['count']) for z in zones]
    log_p = [np.log1p(z['population']) for z in zones]

    min_ld, max_ld = min(log_d), max(log_d)
    min_lp, max_lp = min(log_p), max(log_p)

    d_norm = [(v - min_ld) / (max_ld - min_ld) if max_ld > min_ld else 0.5 for v in log_d]
    p_norm = [(v - min_lp) / (max_lp - min_lp) if max_lp > min_lp else 0.5 for v in log_p]

    urgencies = []
    for z in zones:
        elapsed = z.get('elapsed_hours', 24)
        if elapsed <= 6:
            urgency = 1.0
        elif elapsed <= 24:
            urgency = 0.95 - ((elapsed - 6) / 18.0) * 0.15
        elif elapsed <= 72:
            urgency = 0.80 - ((elapsed - 24) / 48.0) * 0.25
        elif elapsed <= 168:
            urgency = 0.55 - ((elapsed - 72) / 96.0) * 0.20
        else:
            urgency = max(0.20, 0.35 - ((elapsed - 168) / 720.0) * 0.15)
        urgencies.append(round(urgency, 4))

    W_D = 1.0 / 3.0
    W_P = 1.0 / 3.0
    W_U = 1.0 / 3.0

    raw_scores = []
    for i, z in enumerate(zones):
        score = W_D * d_norm[i] + W_P * p_norm[i] + W_U * urgencies[i]
        raw_scores.append(score)

    min_s = min(raw_scores)
    max_s = max(raw_scores)

    # Relative Priority Index (RPI) scaled to [0.15, 0.95] (15% to 95%)
    for i, z in enumerate(zones):
        raw = raw_scores[i]
        if max_s > min_s:
            scaled_score = 0.15 + ((raw - min_s) / (max_s - min_s)) * 0.80
        else:
            scaled_score = 0.50

        scaled_score = round(scaled_score, 4)
        z['priority_score'] = scaled_score

    zones.sort(key=lambda x: x['priority_score'], reverse=True)

    for rank, z in enumerate(zones, 1):
        z['priority_rank'] = rank
        score = z['priority_score']
        # Absolute logical thresholds:
        if score >= 0.65:
            z['priority_label'] = 'Tinggi'
        elif score >= 0.40:
            z['priority_label'] = 'Sedang'
        else:
            z['priority_label'] = 'Kecil'

    return zones

rz = test_scoring_model(zones)

print("\n--- TOP 15 ZONES ---")
for z in rz[:15]:
    pct = round(z['priority_score'] * 100, 1)
    print(f"{z['desa'][:35]:<35} | Score: {z['priority_score']:.2f} ({pct:5.1f}%) | Label: {z['priority_label']:<6} | Count: {z['count']:<3} | Pop: {z['population']:<5} | Elapsed: {z.get('elapsed_hours')}h")

print("\n--- MIDDLE 5 ZONES (around boundary) ---")
for z in rz[115:120]:
    pct = round(z['priority_score'] * 100, 1)
    print(f"{z['desa'][:35]:<35} | Score: {z['priority_score']:.2f} ({pct:5.1f}%) | Label: {z['priority_label']:<6} | Count: {z['count']:<3} | Pop: {z['population']:<5} | Elapsed: {z.get('elapsed_hours')}h")

print("\n--- LOWEST 5 ZONES ---")
for z in rz[-5:]:
    pct = round(z['priority_score'] * 100, 1)
    print(f"{z['desa'][:35]:<35} | Score: {z['priority_score']:.2f} ({pct:5.1f}%) | Label: {z['priority_label']:<6} | Count: {z['count']:<3} | Pop: {z['population']:<5} | Elapsed: {z.get('elapsed_hours')}h")

labels_count = pd.Series([z['priority_label'] for z in rz]).value_counts()
print(f"\nLabel distribution:\n{labels_count}")
