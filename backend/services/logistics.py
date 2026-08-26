import json
import os
import numpy as np
import pandas as pd

from config import LOGISTIK_PER_KK
from services.population import get_population_for_desa


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
    2. Population        — WorldPop (University of Southampton, 100m gridded population)
    3. Temporal Urgency  — Sphere Handbook 2018, Ch.6 (Golden Time 72 jam respons darurat)

    BOBOT (tetap/deterministik):
    Equal weighting method (Dawes, 1979) — masing-masing 1/3.

    KATEGORI PRIORITAS:
    3 level: Tinggi, Sedang, Kecil — berdasarkan distribusi skor tercile.
    """
    if not zones:
        return zones

    densities = []
    populations = []
    urgencies = []

    for z in zones:
        count = z.get('count', 0)
        desa_name = z.get('desa', '')
        polygon = z.get('polygon', [])

        wp_pop = get_population_for_desa(desa_name, polygon)
        if wp_pop and wp_pop > 0:
            z['population'] = wp_pop
            z['pop_source'] = 'WorldPop'
        else:
            z['population'] = count
            z['pop_source'] = 'Damage Count'

        densities.append(count)
        populations.append(z['population'])

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

    W_DENSITY = 1.0 / 3.0
    W_POPULATION = 1.0 / 3.0
    W_URGENCY = 1.0 / 3.0

    for i, z in enumerate(zones):
        score = (W_DENSITY * d_norm[i] +
                 W_POPULATION * p_norm[i] +
                 W_URGENCY * urgencies[i])

        z['priority_score'] = round(score, 4)

    zones.sort(key=lambda x: x['priority_score'], reverse=True)

    n = len(zones)
    for rank, z in enumerate(zones, 1):
        z['priority_rank'] = rank
        if rank <= n / 3:
            z['priority_label'] = 'Tinggi'
        elif rank <= 2 * n / 3:
            z['priority_label'] = 'Sedang'
        else:
            z['priority_label'] = 'Kecil'

    return zones
