import sys, os
sys.path.insert(0, os.path.abspath('backend'))
from services.logistics import calculate_priority_scores

sample_zones = [
    {"desa": "Desa Pasir Madang", "count": 48, "population": 8420, "elapsed_hours": 8.5},
    {"desa": "Desa Cileuksa", "count": 27, "population": 6150, "elapsed_hours": 14.2},
    {"desa": "Desa Sukamaju", "count": 19, "population": 4300, "elapsed_hours": 36.0},
    {"desa": "Desa Kertajaya", "count": 14, "population": 2900, "elapsed_hours": 65.0},
    {"desa": "Desa Bojong", "count": 8, "population": 1800, "elapsed_hours": 110.0},
    {"desa": "Desa Wanasari", "count": 5, "population": 1200, "elapsed_hours": 140.0},
    {"desa": "Desa Mekarjaya", "count": 3, "population": 850, "elapsed_hours": 200.0},
    {"desa": "Desa Cibadak", "count": 2, "population": 450, "elapsed_hours": 350.0},
    {"desa": "Desa Sukaresmi", "count": 1, "population": 300, "elapsed_hours": 500.0}
]

res = calculate_priority_scores(sample_zones)
for z in res:
    score = z['priority_score']
    pct = round(score * 100, 1)
    label = z['priority_label']
    p = z['priority_pillars']
    print(f"{z['desa']:<20} | Score: {score:.4f} ({pct:5.1f}%) | Label: {label:<7} | Kerusakan: {p['kerusakan_fisik']:.3f} | Pop: {p['demografi_terdampak']:.3f} | Waktu: {p['waktu_kritis']:.3f}")
