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
    1. Damage Density    -- Perka BNPB No. 2/2012 (JITUPASNA: jumlah kerusakan bangunan)
    2. Population        -- WorldPop (University of Southampton, 100m gridded population)
    3. Temporal Urgency  -- Sphere Handbook 2018, Ch.6 (Golden Time 72 jam respons darurat)

    BOBOT (tetap/deterministik):
    Equal weighting method (Dawes, 1979) -- masing-masing 1/3.

    NORMALISASI:
    Min-max normalization per pilar, lalu skor akhir = weighted sum.

    KATEGORI PRIORITAS:
    3 level: Kritis, Siaga, Waspada -- berdasarkan distribusi skor tercile.
    """
    if not zones:
        return zones

    AVG_KK_SIZE = 4

    densities = []
    populations = []
    urgencies = []

    for z in zones:
        count = z.get('sim_count', z.get('count', 0))
        desa_name = z.get('desa', '')
        polygon = z.get('polygon', [])

        wp_pop = get_population_for_desa(desa_name, polygon)
        affected_est = max(count * AVG_KK_SIZE, AVG_KK_SIZE)
        if wp_pop and wp_pop > 0:
            z['population'] = min(wp_pop, max(affected_est, int(count * 4.5)))
            z['pop_source'] = 'WorldPop'
        else:
            z['population'] = affected_est
            z['pop_source'] = 'Estimasi KK'

        densities.append(count)
        populations.append(z['population'])

        elapsed = z.get('elapsed_hours', 0)
        if elapsed <= 0:
            urgency = 1.0
        elif elapsed <= 6:
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

    log_d = [np.log1p(c) for c in densities]
    log_p = [np.log1p(p) for p in populations]

    min_ld, max_ld = min(log_d), max(log_d)
    min_lp, max_lp = min(log_p), max(log_p)

    d_norm = [(v - min_ld) / (max_ld - min_ld) if max_ld > min_ld else 0.5 for v in log_d]
    p_norm = [(v - min_lp) / (max_lp - min_lp) if max_lp > min_lp else 0.5 for v in log_p]

    W_DENSITY = 1.0 / 3.0
    W_POPULATION = 1.0 / 3.0
    W_URGENCY = 1.0 / 3.0

    raw_scores = []
    for i in range(len(zones)):
        s = (W_DENSITY * d_norm[i] +
             W_POPULATION * p_norm[i] +
             W_URGENCY * urgencies[i])
        raw_scores.append(s)

    min_s = min(raw_scores)
    max_s = max(raw_scores)

    for i, z in enumerate(zones):
        if max_s > min_s:
            scaled_score = 0.15 + ((raw_scores[i] - min_s) / (max_s - min_s)) * 0.83
        else:
            scaled_score = 0.75

        pillar_damage = round(d_norm[i], 4)
        pillar_pop = round(p_norm[i], 4)
        pillar_urgency = urgencies[i]

        z['priority_score'] = round(scaled_score, 4)
        z['priority_pillars'] = {
            'kerusakan_fisik': pillar_damage,
            'demografi_terdampak': pillar_pop,
            'waktu_kritis': pillar_urgency,
            'bobot_kerusakan': round(W_DENSITY, 4),
            'bobot_demografi': round(W_POPULATION, 4),
            'bobot_waktu': round(W_URGENCY, 4),
            'kontribusi_kerusakan': round(W_DENSITY * pillar_damage, 4),
            'kontribusi_demografi': round(W_POPULATION * pillar_pop, 4),
            'kontribusi_waktu': round(W_URGENCY * pillar_urgency, 4)
        }

    zones.sort(key=lambda x: x['priority_score'], reverse=True)

    for rank, z in enumerate(zones, 1):
        z['priority_rank'] = rank
        score = z['priority_score']
        if score >= 0.65:
            z['priority_label'] = 'Kritis'
        elif score >= 0.40:
            z['priority_label'] = 'Siaga'
        else:
            z['priority_label'] = 'Waspada'

    return zones

