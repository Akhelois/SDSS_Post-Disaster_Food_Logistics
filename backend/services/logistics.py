import json
import os
import numpy as np
import pandas as pd

from config import LOGISTIK_PER_KK, GUDANG_BNPB, BPS_DATA_FILE
from services.routing import haversine_distance_m


def nearest_gudang_distance_km(lat, lon):
    min_dist = float('inf')
    nearest_name = ""
    nearest_coords = None
    for g in GUDANG_BNPB:
        dist = haversine_distance_m(lat, lon, g['lat'], g['lon']) / 1000.0
        if dist < min_dist:
            min_dist = dist
            nearest_name = g['nama']
            nearest_coords = [g['lon'], g['lat']]
    return min_dist, nearest_name, nearest_coords


def merge_nearby_hubs(cc, min_dist_m):
    min_dist_deg = min_dist_m / 111320
    coords = cc[['safe_lat', 'safe_lon']].values
    merged, used = [], set()
    for i in range(len(coords)):
        if i in used:
            continue
        group = [i]
        for j in range(i + 1, len(coords)):
            if j not in used:
                same_island = cc.iloc[i]['island'] == cc.iloc[j]['island']
                dist = np.sqrt((coords[i][0] - coords[j][0]) ** 2 + (coords[i][1] - coords[j][1]) ** 2)
                if dist < min_dist_deg and same_island:
                    group.append(j)
                    used.add(j)
        used.add(i)
        rows = cc.iloc[group]
        all_desa = set()
        for dl in rows['desa_list'].dropna():
            for d in str(dl).split(', '):
                d = d.strip()
                if d and d != 'Tidak Diketahui':
                    all_desa.add(d)
        best_hub = rows.loc[rows['jumlah_red'].idxmax()]
        merged.append({
            'safe_lat': best_hub['safe_lat'],
            'safe_lon': best_hub['safe_lon'],
            'desa_list': ', '.join(sorted(all_desa)) if all_desa else '',
            'jumlah_red': int(rows['jumlah_red'].sum()),
            'avg_confidence': float(rows['avg_confidence'].max()),
            'island': str(rows['island'].iloc[0]),
            'cluster_ids': list(rows['cluster_id'])
        })
    return pd.DataFrame(merged).reset_index().rename(columns={'index': 'hub_id'})


def calculate_priority_scores(zones):
    """
    Multi-Criteria Priority Scoring untuk distribusi logistik pasca-bencana.

    PARAMETER (sumber resmi):
    1. Damage Density    — Perka BNPB No. 2/2012 (JITUPASNA: jumlah kerusakan bangunan)
    2. Population        — BPS SP2020 + Perka BNPB No. 7/2008 (estimasi jiwa/KK per pulau)
    3. Proximity         — Perka BNPB No. 13/2008 (aksesibilitas logistik ke zona terdampak)
    4. Temporal Urgency  — Sphere Handbook 2018, Ch.6 (Golden Time 72 jam respons darurat)

    BOBOT:
    Equal weighting method (Dawes, 1979) — masing-masing 0.25.
    Untuk bobot yang divalidasi pakar, gunakan AHP (Saaty, 1980).

    KATEGORI PRIORITAS:
    3 level: Tinggi, Sedang, Kecil — berdasarkan distribusi skor tercile.
    """
    if not zones:
        return zones

    densities = []
    populations = []
    distances = []
    urgencies = []
    gudang_names = []
    gudang_coords_list = []

    default_bps = {
        'jawa': 4.5, 'sumatera': 4.2, 'sulawesi': 4.0, 'kalimantan': 3.8,
        'papua': 5.0, 'maluku': 4.8, 'bali': 4.1, 'nusa tenggara': 4.5, 'nasional': 4.0
    }

    BPS_DENSITY = default_bps
    if os.path.exists(BPS_DATA_FILE):
        try:
            with open(BPS_DATA_FILE, 'r') as f:
                BPS_DENSITY = json.load(f)
        except Exception:
            pass
    else:
        try:
            with open(BPS_DATA_FILE, 'w') as f:
                json.dump(default_bps, f, indent=4)
        except Exception:
            pass

    def get_bps_multiplier(wilayah):
        w = str(wilayah).lower()
        for region, density in BPS_DENSITY.items():
            if region in w:
                return density
        return BPS_DENSITY.get('nasional', 4.0)

    for z in zones:
        count = z.get('count', 0)
        desa = z.get('desa', '')

        bps_multiplier = get_bps_multiplier(desa)
        pop_estimate = int(count * bps_multiplier)

        z['population'] = pop_estimate

        densities.append(count)
        populations.append(pop_estimate)

        dist_km, g_name, g_coords = nearest_gudang_distance_km(z['lat'], z['lon'])
        distances.append(dist_km)
        gudang_names.append(g_name)
        gudang_coords_list.append(g_coords)

        # Temporal Urgency: Golden Time 72 jam (Sphere Standards 2018)
        # Semakin baru kejadian → urgency semakin tinggi
        elapsed = z.get('elapsed_hours', 0)
        urgency = max(0.0, 1.0 - min(elapsed / 72.0, 1.0))
        urgencies.append(urgency)

    def normalize(values):
        min_v = min(values)
        max_v = max(values)
        if max_v == min_v:
            return [0.5] * len(values)
        return [(v - min_v) / (max_v - min_v) for v in values]

    d_norm = normalize(densities)
    p_norm = normalize(populations)
    dist_norm = normalize(distances)
    # Urgency sudah dalam range 0-1, tidak perlu normalisasi ulang

    # Equal Weighting Method (Dawes, 1979; Einhorn & Hogarth, 1975)
    # Baseline sebelum validasi AHP oleh expert
    W_DENSITY = 0.25
    W_POPULATION = 0.25
    W_PROXIMITY = 0.25
    W_URGENCY = 0.25

    for i, z in enumerate(zones):
        proximity = 1.0 - dist_norm[i]

        score = (W_DENSITY * d_norm[i] +
                 W_POPULATION * p_norm[i] +
                 W_PROXIMITY * proximity +
                 W_URGENCY * urgencies[i])

        z['priority_score'] = round(score, 4)
        z['gudang_terdekat'] = gudang_names[i]
        z['gudang_coords'] = gudang_coords_list[i]
        z['jarak_gudang_km'] = round(distances[i], 1)

    zones.sort(key=lambda x: x['priority_score'], reverse=True)

    # Kategori Prioritas: 3 level (Tinggi, Sedang, Kecil)
    # Menggunakan distribusi tercile berdasarkan skor
    n = len(zones)
    for rank, z in enumerate(zones, 1):
        z['priority_rank'] = rank
        # Tercile: top 1/3 = Tinggi, mid 1/3 = Sedang, bottom 1/3 = Kecil
        if rank <= n / 3:
            z['priority_label'] = 'Tinggi'
        elif rank <= 2 * n / 3:
            z['priority_label'] = 'Sedang'
        else:
            z['priority_label'] = 'Kecil'

    return zones

