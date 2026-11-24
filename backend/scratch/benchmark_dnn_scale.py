"""Latensi inferensi DNN logistik vs jumlah desa (1 - 81.912), CPU only.

Melengkapi backend/scratch/benchmark_latency.py yang hanya mengukur 2 titik
(1 vektor vs 81.912 desa). Hasil digabung ke backend/output/latency_results.json
sebagai key "dnn_skala_desa". Plot latency_plot.png TIDAK diubah.

Jalankan dari root repo:  python backend/scratch/benchmark_dnn_scale.py
"""

import os

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # paksa CPU, konsisten dgn benchmark_latency.py

import json
import time

import numpy as np

RNG = np.random.default_rng(42)
NS = [1, 10, 50, 100, 500, 1000, 5000, 10000, 30000, 81912]


def timed(fn, repeats, warmup=2):
    for _ in range(warmup):
        fn()
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return times


def stats(times):
    a = np.asarray(times) * 1000.0  # ms
    return {"mean_ms": round(float(a.mean()), 2),
            "median_ms": round(float(np.median(a)), 2),
            "p95_ms": round(float(np.percentile(a, 95)), 2),
            "n": len(a)}


def repeats_for(n):
    if n <= 100:
        return 20
    if n <= 1000:
        return 10
    if n <= 10000:
        return 5
    return 3


import tensorflow as tf  # noqa: E402  (setelah CUDA_VISIBLE_DEVICES)

dnn = tf.keras.models.load_model("backend/model/model_logistics.h5", compile=False)

scale = {}
for n in NS:
    x = RNG.random((n, 7), dtype=np.float32)
    t = timed(lambda: dnn.predict(x, verbose=0), repeats=repeats_for(n), warmup=2)
    s = stats(t)
    s["per_desa_us"] = round(s["mean_ms"] * 1000.0 / n, 2)
    scale[str(n)] = s
    print(f"[dnn {n} desa]", s, flush=True)

path = "backend/output/latency_results.json"
with open(path, encoding="utf-8") as f:
    res = json.load(f)
res["dnn_skala_desa"] = scale
with open(path, "w", encoding="utf-8") as f:
    json.dump(res, f, indent=2, ensure_ascii=False)
print("merged dnn_skala_desa into", path)
