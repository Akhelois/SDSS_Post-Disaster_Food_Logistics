"""
Simulasi pengukuran latensi pipeline SDSS (uji perfoma).

Mengukur latensi nyata tiap tahap pipeline pada perangkat ini:
  1. Model load (cold start) ResNet50-UNet dan DNN
  2. Inferensi segmentasi per tile 256x256x6 (CPU, batch 1 dan batch 8)
  3. Post-processing mask (threshold + mosaic)
  4. Spatial join titik kerusakan ke poligon desa (GeoPandas sindex)
  5. Inferensi DNN 17 item (vektor tunggal dan batch seluruh desa)
  6. Skor prioritas MCDA Equal Weighting

Ekstrapolasi ke 3 skenario luasan AOI disimpan ke latency_results.json.

Jalankan:  python backend/scratch/benchmark_latency.py
Catatan  : CPU dipaksa (CUDA_VISIBLE_DEVICES kosong) agar hasil
           dapat direproduksi di komputer mana pun.
"""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # paksa CPU agar hasil reproducible

import json
import time
import numpy as np

RESULTS = {}
RNG = np.random.default_rng(42)


def timed(fn, repeats, warmup=2):
    """Kembalikan (hasil_terakhir, list_latensi_detik) dengan warm-up."""
    for _ in range(warmup):
        out = fn()
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        out = fn()
        times.append(time.perf_counter() - t0)
    return out, times


def stats(times):
    a = np.asarray(times) * 1000.0  # ms
    return {"mean_ms": round(float(a.mean()), 2),
            "median_ms": round(float(np.median(a)), 2),
            "p95_ms": round(float(np.percentile(a, 95)), 2),
            "n": len(a)}


# ---------------------------------------------------------------- 1. load model
import tensorflow as tf

t0 = time.perf_counter()
seg = tf.keras.models.load_model("backend/model/model_sdss.h5", compile=False)
seg_load_s = time.perf_counter() - t0

t0 = time.perf_counter()
dnn = tf.keras.models.load_model("backend/model/model_logistics.h5", compile=False)
dnn_load_s = time.perf_counter() - t0

RESULTS["model_load"] = {"resnet50_unet_s": round(seg_load_s, 2),
                         "dnn_s": round(dnn_load_s, 3),
                         "seg_params": int(seg.count_params()),
                         "dnn_params": int(dnn.count_params())}
print(f"[load] ResNet50-UNet {seg_load_s:.1f} s, DNN {dnn_load_s:.3f} s")

# ------------------------------------------------- 2. inferensi segmentasi per tile
tile = RNG.random((1, 256, 256, 6), dtype=np.float32)
_, t_single = timed(lambda: seg.predict(tile, verbose=0), repeats=10, warmup=3)
RESULTS["segmentasi_batch1"] = stats(t_single)
print("[seg batch1]", RESULTS["segmentasi_batch1"])

batch8 = RNG.random((8, 256, 256, 6), dtype=np.float32)
_, t_b8 = timed(lambda: seg.predict(batch8, verbose=0), repeats=5, warmup=2)
RESULTS["segmentasi_batch8"] = stats(t_b8)
RESULTS["segmentasi_batch8"]["per_tile_ms"] = round(RESULTS["segmentasi_batch8"]["mean_ms"] / 8, 2)
print("[seg batch8]", RESULTS["segmentasi_batch8"])

# ------------------------------------------------- 3. post-processing mask
mask_prob = RNG.random((256, 256), dtype=np.float32)
_, t_post = timed(lambda: (mask_prob > 0.90).astype(np.uint8), repeats=50, warmup=5)
RESULTS["threshold_mask"] = stats(t_post)
print("[threshold]", RESULTS["threshold_mask"])

# ------------------------------------------------- 4. spatial join ke poligon desa
import geopandas as gpd
from shapely.geometry import Point

t0 = time.perf_counter()
gdf_desa = gpd.read_file("backend/data/sdss_indonesia_final.shp",
                         columns=["geometry"])
RESULTS["load_shapefile_desa"] = {"detik": round(time.perf_counter() - t0, 2),
                                  "n_poligon": len(gdf_desa)}
print("[shapefile]", RESULTS["load_shapefile_desa"])

# sampel 1.000 titik kerusakan di dalam bounding box Indonesia
xmin, ymin, xmax, ymax = gdf_desa.total_bounds
pts = gpd.GeoDataFrame(
    geometry=[Point(RNG.uniform(xmin, xmax), RNG.uniform(ymin, ymax)) for _ in range(1000)],
    crs=gdf_desa.crs)

sindex = gdf_desa.sindex  # index spasial dibangun sekali (di-cache)
_, t_join = timed(lambda: gpd.sjoin(pts, gdf_desa, predicate="within"), repeats=5, warmup=1)
RESULTS["spatial_join_1000_titik"] = stats(t_join)
points_per_s = 1000.0 / (RESULTS["spatial_join_1000_titik"]["mean_ms"] / 1000.0)
print("[sjoin 1k]", RESULTS["spatial_join_1000_titik"], f"~{points_per_s:.0f} titik/detik")

# ------------------------------------------------- 5. inferensi DNN 17 item
x1 = RNG.random((1, 7), dtype=np.float32)
_, t_dnn1 = timed(lambda: dnn.predict(x1, verbose=0), repeats=50, warmup=5)
RESULTS["dnn_vektor_tunggal"] = stats(t_dnn1)

x_desa = RNG.random((81912, 7), dtype=np.float32)
_, t_dnn_all = timed(lambda: dnn.predict(x_desa, verbose=0), repeats=3, warmup=1)
RESULTS["dnn_81912_desa"] = stats(t_dnn_all)
print("[dnn 1]", RESULTS["dnn_vektor_tunggal"])
print("[dnn 81.912 desa]", RESULTS["dnn_81912_desa"])

# ------------------------------------------------- 6. skor MCDA Equal Weighting
d = RNG.random(100000)
p = RNG.random(100000)
u = RNG.random(100000)
_, t_mcda = timed(lambda: (d / max(d.max(), 1e-9) + p / max(p.max(), 1e-9) + u) / 3.0,
                  repeats=50, warmup=5)
RESULTS["skor_mcda_100k_desa"] = stats(t_mcda)
print("[mcda]", RESULTS["skor_mcda_100k_desa"])

# ------------------------------------------------- 7. ekstrapolasi AOI
per_tile_s = RESULTS["segmentasi_batch8"]["per_tile_ms"] / 1000.0
# citra VHR 0,5 m/piksel, tile 256 px = 128 m sisinya, atau 0,0164 km2 per tile
km2_per_tile = (256 * 0.5 / 1000.0) ** 2
aoi = {"AOI kecamatan 5 km2": 5.0, "AOI kota 25 km2": 25.0, "AOI provinsi 100 km2": 100.0}
RESULTS["ekstrapolasi_aoi"] = {}
for name, km2 in aoi.items():
    tiles = int(np.ceil(km2 / km2_per_tile))
    RESULTS["ekstrapolasi_aoi"][name] = {
        "jumlah_tile_256px": tiles,
        "estimasi_inferensi_menit": round(tiles * per_tile_s / 60.0, 1),
    }
    print(f"[aoi] {name}: {tiles} tile, ~{tiles * per_tile_s / 60.0:.1f} menit (CPU)")

RESULTS["meta"] = {
    "tensorflow": tf.__version__,
    "perangkat": "CPU only (reproducible)",
    "catatan": ("Waktu akuisisi citra satelit dan latensi API eksternal "
                "(NASA GIBS, WorldPop) tidak termasuk karena bergantung jaringan."),
}

os.makedirs("backend/output", exist_ok=True)
with open("backend/output/latency_results.json", "w", encoding="utf-8") as f:
    json.dump(RESULTS, f, indent=2, ensure_ascii=False)
print("\nTersimpan ke backend/output/latency_results.json")
