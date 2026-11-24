import numpy as np

def calculate_priority_scores(zones):
    if not zones:
        return zones

    AVG_KK_SIZE = 4

    densities = []
    populations = []
    urgencies = []

    for z in zones:
        count = z.get('count', 0)
        desa_name = z.get('desa', '')
        polygon = z.get('polygon', [])

        # Affected population calculation
        affected_est = max(count * AVG_KK_SIZE, AVG_KK_SIZE)
        z['population'] = affected_est
        z['pop_source'] = 'Estimasi KK'

        densities.append(count)
        populations.append(z['population'])

        elapsed = z.get('elapsed_hours', 24)
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

    # Log-transform for heavy-tailed disaster impact (CRED EM-DAT / BNPB)
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

    # Scale to operational range [0.15, 0.98]
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
            z['priority_label'] = 'Tinggi'
        elif score >= 0.40:
            z['priority_label'] = 'Sedang'
        else:
            z['priority_label'] = 'Kecil'

    return zones

# Test edge cases
print("1. Empty list:", calculate_priority_scores([]))
single = calculate_priority_scores([{'desa': 'Solo', 'count': 5, 'elapsed_hours': 10}])
print("2. Single item:", single[0]['priority_score'], single[0]['priority_label'])
two = calculate_priority_scores([
    {'desa': 'A', 'count': 10, 'elapsed_hours': 10},
    {'desa': 'B', 'count': 1, 'elapsed_hours': 100}
])
print("3. Two items A:", two[0]['priority_score'], two[0]['priority_label'])
print("   Two items B:", two[1]['priority_score'], two[1]['priority_label'])
