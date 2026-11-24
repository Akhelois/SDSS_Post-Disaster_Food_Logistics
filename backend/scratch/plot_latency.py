"""Render backend/output/latency_plot.png dari backend/output/latency_results.json.

Tiga panel: (a) latensi per tahap pipeline (skala log), (b) ekstrapolasi AOI,
(c) skala inferensi DNN logistik vs jumlah desa (baru, key "dnn_skala_desa").
Panel (a) dan (b) mempertahankan isi/angka plot lama; hanya (c) tambahan baru.

Jalankan dari root repo:  python backend/scratch/plot_latency.py
"""

import json

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

with open("backend/output/latency_results.json", encoding="utf-8") as f:
    R = json.load(f)

# ------------------------------------------------------------- data panel (a)
stages = [
    ("Thresholding mask (1 tile)", R["threshold_mask"]["mean_ms"], "0.06 ms"),
    ("Skor MCDA (100 rb desa)", R["skor_mcda_100k_desa"]["mean_ms"], "0.35 ms"),
    ("Spatial join (1.000 titik)", R["spatial_join_1000_titik"]["mean_ms"], "75.62 ms"),
    ("Inferensi DNN (1 vektor)", R["dnn_vektor_tunggal"]["mean_ms"], "48.36 ms"),
    ("Inferensi segmentasi (1 tile)", R["segmentasi_batch1"]["mean_ms"], "284.16 ms"),
    ("Inferensi segmentasi (per tile, batch 8)",
     R["segmentasi_batch8"]["per_tile_ms"], "107.07 ms"),
    ("Inferensi DNN (81.912 desa)", R["dnn_81912_desa"]["mean_ms"], "2.68 s"),
]
labels_a = [s[0] for s in stages]
vals_ms = [s[1] for s in stages]
texts_a = [s[2] for s in stages]
cold_ms = R["model_load"]["resnet50_unet_s"] * 1000.0
labels_a.append("Muat ResNet50-UNet (cold start)")
vals_ms.append(cold_ms)
texts_a.append(f"{R['model_load']['resnet50_unet_s']:.2f} s")
aoi_keys = ["AOI kecamatan 5 km2", "AOI kota 25 km2", "AOI provinsi 100 km2"]
aoi_min = [R["ekstrapolasi_aoi"][k]["estimasi_inferensi_menit"] for k in aoi_keys]
aoi_names = ["5 km\u00b2\n(kecamatan)", "25 km\u00b2\n(kota)", "100 km\u00b2\n(luas)"]
aoi_tiles = [R["ekstrapolasi_aoi"][k]["jumlah_tile_256px"] for k in aoi_keys]

# ------------------------------------------------------------- data panel (c)
scale = R["dnn_skala_desa"]
ns_c = np.array([int(k) for k in scale.keys()])
order = np.argsort(ns_c)
ns_c = ns_c[order]
mean_c = np.array([scale[str(int(n))]["mean_ms"] for n in ns_c])
p95_c = np.array([scale[str(int(n))]["p95_ms"] for n in ns_c])

# ------------------------------------------------------------------ render
cmap_a = plt.cm.viridis(np.linspace(0.25, 0.75, len(labels_a)))
fig, axes = plt.subplots(1, 3, figsize=(15.6, 5.2), dpi=200,
                         gridspec_kw={"width_ratios": [1.15, 0.85, 1.0]})
fig.suptitle("Hasil Simulasi Pengukuran Latensi Pipeline SDSS (TensorFlow 2.10, CPU)",
             fontsize=13, fontweight="bold", y=0.98)

# (a) tahapan pipeline, sumbu log
ax = axes[0]
ax.set_title("(a) Latensi per tahap pipeline SDSS (CPU)", fontsize=10)
y = np.arange(len(labels_a))
bars = ax.barh(y, vals_ms, color=cmap_a, edgecolor="black", linewidth=0.5)
ax.set_yticks(y)
ax.set_yticklabels(labels_a, fontsize=8)
ax.invert_yaxis()
ax.set_xscale("log")
ax.set_xlabel("Latensi rata-rata (milidetik, skala log)", fontsize=9)
for b, t in zip(bars, texts_a):
    ax.text(b.get_width() * 1.04, b.get_y() + b.get_height() / 2, t,
            va="center", fontsize=8)
ax.grid(True, axis="x", which="both", alpha=0.25)

# (b) ekstrapolasi AOI
ax = axes[1]
ax.set_title("(b) Ekstrapolasi AOI (asumsi VHR 0,5 m/piksel)", fontsize=10)
bars = ax.bar([0, 1, 2], aoi_min, color=["#2ca02c", "#1f77b4", "#ff7f0e"],
              edgecolor="black", linewidth=0.5, width=0.6)
ax.set_xticks([0, 1, 2])
ax.set_xticklabels(aoi_names, fontsize=9)
ax.set_ylabel("Estimasi inferensi segmentasi (menit)", fontsize=9)
ax.set_ylim(0, 36)
ax.axhline(30, color="red", linestyle="--", linewidth=1.2)
ax.text(2.55, 30.6, "ambang 30 menit", color="red", fontsize=8, ha="right", va="bottom")
for b, m, t in zip(bars, aoi_min, aoi_tiles):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.35,
            f"{m:.1f} menit\n{t:,} tile".replace(",", "."),
            ha="center", va="bottom", fontsize=8)
ax.grid(True, axis="y", alpha=0.25)

# (c) skala DNN vs jumlah desa
ax = axes[2]
ax.set_title("(c) Skala inferensi DNN vs jumlah desa (CPU)", fontsize=10)
ax.fill_between(ns_c, mean_c, p95_c, color="#7f7f7f", alpha=0.25, label="rentang mean–p95")
ax.plot(ns_c, mean_c, marker="o", markersize=4, linewidth=1.5,
        color="#9467bd", label="rata-rata")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("Jumlah desa (skala log)", fontsize=9)
ax.set_ylabel("Latensi inferensi DNN (ms, skala log)", fontsize=9)
ax.grid(True, which="both", alpha=0.25)
# anotasi 3 titik jangkar
for n_pick, txt in [(500, "500 desa\n~78 ms"), (10000, "10.000 desa\n~0,4 dtk"),
                    (81912, "81.912 desa\n~2,6 dtk")]:
    i = int(np.where(ns_c == n_pick)[0][0])
    ax.annotate(txt, (ns_c[i], mean_c[i]), fontsize=7.5,
                xytext=(8, 10 if n_pick != 81912 else -22), textcoords="offset points",
                arrowprops={"arrowstyle": "-", "color": "gray", "lw": 0.7})
ax.legend(fontsize=7.5, loc="upper left")

fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig("backend/output/latency_plot.png", bbox_inches="tight")
print("tersimpan backend/output/latency_plot.png")
