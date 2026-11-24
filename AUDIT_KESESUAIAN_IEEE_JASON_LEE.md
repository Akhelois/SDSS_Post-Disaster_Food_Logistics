# REVISI MANUSKRIPT — IEEE_Jason_Lee.docx (ronda 3: simbol & caption)

Fokus ronda ini sesuai permintaan:

- Poin 1: soal AUC 0.9838 (harus dibaca dengan benar dulu, dua opsi teks disediakan)
- Poin 2: scan semua simbol `;`, `~`, `≈` yang masih ada di docx, lengkap dengan penggantinya
- Poin 3: semua caption figure & table dibuat pendek, dengan catatan ke mana isi yang dipotong pindah (tidak ada konten hilang)

Format: **LOKASI → LAPA (teks lama) → BARU (teks pengganti, siap paste, bebas ; ~ ≈)**

---

## 1. AUC — 0.9838 adalah AUC validation set, 0.9813 adalah AUC test set

Fakta dari notebook (sudah dicek ulang):

- `0.9838` berasal dari cell ROC lama (cell 59) yang datanya dari cell 55, dan cell 55 loop di `val_pairs`. Artinya 0.9838 = **AUC validation set** (subsample 2M piksel, tanpa seed tetap, makanya 0.9836 → 0.9838 berubah antar run).
- `0.9813` berasal dari sel B1_FIX (2/2) = **AUC test set** (subsample 2M piksel, seed 42).
- Fig. 6 yang sekarang tertancap di docx memang gambar kurva ROC di validation set (judul di gambar: AUC 0.9838).

Makanya angka yang "makin bagus" (0.9838) bukan AUC yang lebih baik secara model, tapi AUC di data yang berbeda (validation). Yang jujur untuk klaim "held-out test set" adalah 0.9813. Cara terbaik yang tetap mempertahankan 0.9838 di paper: tulis keduanya dengan label split yang benar seperti di bawah, dan cukup ganti caption Fig. 6 saja (gambar tidak perlu diganti).

### 1a. Section IV-B (Best-Model Diagnostics, kalimat ROC) — GANTI SATU KALIMAT

LAPA:

> The ROC curve (Fig. 6, AUC = 0.9838) indicates strong ranking quality across thresholds. With only approximately 6% positive pixels, the threshold-dependent metrics remain the more informative view of the damage class.

BARU (rekomendasi, jujur dan tetap menampilkan 0.9838):

> The ROC curve on the validation set (Fig. 6, AUC = 0.9838) indicates strong ranking quality across thresholds, with an AUC of 0.9813 on the held-out test set. With only approximately 6% positive pixels, the threshold-dependent metrics remain the more informative view of the damage class.

### 1b. Caption Fig. 6 — GANTI

LAPA:

> ROC curve of ResNet50-UNet (AUC = 0.9838) on the held-out test set.

BARU:

> ROC curve of ResNet50-UNet on the validation set (AUC = 0.9838).

### 1c. Abstract — GANTI POTONGAN ANGKA AUC (angka test saja, biar konsisten)

LAPA:

> …a pooled F1 of 0.7255 (IoU 0.5692, AUC-ROC 0.9838), compared with…

BARU:

> …a pooled F1 of 0.7255 (IoU 0.5692, AUC-ROC 0.9813), compared with…

### 1d. Conclusion — GANTI POTONGAN ANGKA AUC

LAPA:

> …pooled F1 0.7255, IoU 0.5692, AUC-ROC 0.9838, versus 0.5934…

BARU:

> …pooled F1 0.7255, IoU 0.5692, AUC-ROC 0.9813 (test set), versus 0.5934…

Catatan: kalau Anda tetap ingin satu angka AUC tunggal di abstract/conclusion dan itu 0.9838, satu-satunya cara yang jujur adalah menulis "AUC-ROC 0.9838 on the validation set" di dua tempat itu. Tidak boleh ditulis sebagai angka test set karena artefaknya memang validation.

### 1e. KENAPA BISA DUA ANGKA AUC (0.9813 di abstract, 0.9838 di figure)

Alur artefaknya begini, bisa ditelusuri di notebook:

| | Fig. 6 / cell 59 | Abstract & Conclusion / B1_FIX cell 65 |
|---|---|---|
| Data yang dievaluasi | **Validation set** (cell 55 loop `val_pairs`, 420 mask) | **Test set** (cell B1_FIX, 420 mask) |
| Proporsi piksel kerusakan | 5.84% | 5.12% (TP+FN = 1,795,198) |
| Cara hitung AUC | Subsample acak 2M piksel, **tanpa seed tetap** | Subsample acak 2M piksel, **seed 42** |
| Hasil | 0.9836 (run pertama) → 0.9838 (run ulang Anda) | 0.9813 (stabil, seed terkunci) |
| Kenapa nilainya beda | (1) Split data beda. (2) Checkpoint terbaik dan threshold t* = 0.9 dipilih memakai validation data, jadi metrik validation selalu sedikit lebih optimistis. (3) Subsample tanpa seed membuat val AUC bergoyang kecil antar run (0.9836 → 0.9838), sementara test AUC terkunci di 0.9813 | |

Jadi dua angka itu bukan kontradiksi melainkan dua split yang berbeda. Selama setiap angka membawa label split-nya (0.9838 = validation, 0.9813 = test) pembaca tidak akan bingung dan reviewer tidak bisa menuduh mislabeling.

Kalimat penjelas siap pakai untuk manuskrip (tambahkan di §IV-B setelah kalimat ROC di poin 1a). Kalimat ini juga mencegah reviewer bertanya kenapa angkanya beda:

> The validation-set AUC (0.9838) is slightly higher than the test-set AUC (0.9813). The difference is expected, because both the best checkpoint and the decision threshold were selected on validation data, which mildly favors validation-set performance.

(Perhatikan: kalimat ini bebas tanda ";", "~", dan "≈".)

### 1f. OPSIONAL — AUC test exact tanpa subsample (kalau mau angka paling solid)

Subsample 2M dari 27.5M piksel memberi galat kecil (puluhan angka desimal keempat). Kalau mau angka yang paling solid, menghitung AUC exact di seluruh piksel test (tanpa subsample), jalankan satu cell kecil ini SETELAH cell B1_FIX (2/2), karena variabelnya sudah tersimpan di memori:

```python
# AUC test exact (semua 27,525,120 piksel, tanpa subsample)
from sklearn.metrics import roc_auc_score
print(f"Test AUC-ROC (full pixels) = {roc_auc_score(_b1_t, _b1_p):.4f}")
```

Kalau hasilnya dipakai, tinggal ganti angka 0.9813 di abstract, §IV-B, dan conclusion dengan hasil full-pixel tersebut (dan label tetap "test set").

---

## 2. PEMBERSIHAN SIMBOL `;` `~` `≈` (semua yang masih tersisa di docx)

### 2.1 Abstract — tiga titik-koma, pecah jadi kalimat

LAPA 1:

> …(CNN U-Net) and 0.5372 (VGG16-UNet); a pooled ranking of the baselines is not available.

BARU 1:

> …(CNN U-Net) and 0.5372 (VGG16-UNet). A pooled ranking of the baselines is not available.

LAPA 2:

> …(ANN/MLP 0.99834, DCN 0.99838, DNN 0.99838); the DNN achieved the lowest…

BARU 2:

> …(ANN/MLP 0.99834, DCN 0.99838, DNN 0.99838). The DNN achieved the lowest…

LAPA 3:

> …on a pair-level split and synthetic demand targets; they do not establish…

BARU 3:

> …on a pair-level split and synthetic demand targets. They do not establish…

### 2.2 Introduction paragraf 2, kalimat terakhir

LAPA:

> None of these ambiguities changes a model's quality; all of them change its apparent ranking…

BARU:

> None of these ambiguities changes a model's quality. All of them change its apparent ranking, which is the quantity a comparison exists to report.

### 2.3 Introduction paragraf 4 (kontribusi)

LAPA:

> …three multi-output regressors (ANN/MLP, DCN, DNN) for 17-item demand estimation are compared on identical splits; no end-to-end link…

BARU:

> …three multi-output regressors (ANN/MLP, DCN, DNN) for 17-item demand estimation are compared on identical splits. No end-to-end link…

### 2.4 Section II-A paragraf 2

LAPA:

> …report only pooled pixel metrics, or leave the decision threshold implicit; reviews of xBD-style benchmarks…

BARU:

> …report only pooled pixel metrics, or leave the decision threshold implicit. Reviews of xBD-style benchmarks…

### 2.5 Section II-C — tiga titik-koma (paragraf arsitektur)

LAPA 1:

> …restoring the spatial precision that deep encoders lose to downsampling; improved U-Net variants…

BARU 1:

> …restoring the spatial precision that deep encoders lose to downsampling. Improved U-Net variants…

LAPA 2 (deret tiga backbone):

> Three backbone families are considered: a plain CNN encoder of four convolutional blocks without pre-training; VGG16 [13], whose thirteen convolution layers with small 3×3 kernels provide a deep plain feature hierarchy; and ResNet50 [14], whose fifty layers are organized as residual blocks…

BARU 2:

> Three backbone families are considered: a plain CNN encoder of four convolutional blocks without pre-training, VGG16 [13] with a deep plain feature hierarchy of thirteen small 3×3 convolution layers, and ResNet50 [14] with fifty layers organized as residual blocks…

(Isi "identity shortcuts give gradients a direct path through five downsampling stages" dan "bottleneck 8×8×2048" tetap dipertahankan di kalimat lanjutannya, sudah ada di teks yang sama.)

### 2.6 Section II-C (setelah Eq. (5))

LAPA:

> …applied identically to all compared encoders (Section III); it is treated as a fixed protocol component, not as a contribution, and its isolated effect versus single-phase training is not established by this study.

BARU:

> …applied identically to all compared encoders (Section III). It is treated as a fixed protocol component, not as a contribution. Its isolated effect versus single-phase training is not established by this study.

### 2.7 Section II-D, kalimat pertama

LAPA:

> Each segmentation model outputs a damage probability map p = σ(z); the binary mask follows from a decision threshold t.

BARU:

> Each segmentation model outputs a damage probability map p = σ(z). The binary mask follows from a decision threshold t.

### 2.8 Section II-D, kalimat setelah paragraf threshold

LAPA:

> …while per-image metrics are computed per image and averaged; the two are not expected to coincide…

BARU:

> …while per-image metrics are computed per image and averaged. The two are not expected to coincide…

### 2.9 Section II-E, kalimat terakhir

LAPA:

> …the two criteria can rank regressors differently; a comparison therefore reports both…

BARU:

> …the two criteria can rank regressors differently. A comparison therefore reports both…

### 2.10 Section III (paragraf CRISP-DM)

LAPA:

> The full CRISP-DM cycle includes a Deployment phase; because this paper is a comparative evaluation rather than a system development effort, the methodology covers…

BARU:

> The full CRISP-DM cycle includes a Deployment phase. Because this paper is a comparative evaluation rather than a system development effort, the methodology covers…

### 2.11 Section III-C Data Preparation, paragraf pertama

LAPA:

> Images are resized to 256×256 and normalized to [0,1]; masks are resized with nearest-neighbor interpolation…

BARU:

> Images are resized to 256×256 and normalized to [0,1]. Masks are resized with nearest-neighbor interpolation…

### 2.12 Section III-D Modeling, paragraf pertama — dua titik-koma

LAPA 1:

> …split into two three-channel streams processed by a shared-weight encoder; the deepest features of both streams are fused…

BARU 1:

> …split into two three-channel streams processed by a shared-weight encoder. The deepest features of both streams are fused…

LAPA 2 (deret encoder):

> The encoders are: a plain four-block CNN trained from scratch; a VGG16 backbone [13] with frozen randomly-initialized weights; and a 50-layer residual ResNet50 backbone…

BARU 2:

> The encoders are a plain four-block CNN trained from scratch, a VGG16 backbone [13] with frozen randomly-initialized weights, and a 50-layer residual ResNet50 backbone…

### 2.13 Section III-D, "Shared settings" pertama (daftar titik-koma)

LAPA:

> Shared settings: checkpoint selection by validation Dice; learning rate halved after 3 epochs without validation-loss improvement (floor 1e-6); early stopping after 5 epochs without validation-Dice improvement; batch size 4; seed 42.

BARU:

> Shared settings are checkpoint selection by validation Dice, a learning rate halved after 3 epochs without validation-loss improvement with a floor of 1e-6, early stopping after 5 epochs without validation-Dice improvement, batch size 4, and seed 42.

### 2.14 Section III-D, "Shared settings" kedua (tiga titik-koma)

LAPA 1:

> …(0.10-0.90, step 0.05; random seed 42 for numpy and TensorFlow).

BARU 1:

> …(0.10-0.90, step 0.05, with random seed 42 for numpy and TensorFlow).

LAPA 2:

> …with batch size 4; the two baselines were trained in a single phase with batch size 2.

BARU 2:

> …with batch size 4. The two baselines were trained in a single phase with batch size 2.

LAPA 3:

> …(compute capability 12.0); TensorFlow 2.10 did not support this GPU, so training ran on CPU.

BARU 3:

> …(compute capability 12.0). TensorFlow 2.10 did not support this GPU, so training ran on CPU.

### 2.15 Section III-E, kalimat kriteria

LAPA:

> The technical criteria of Section III-A serve as reference levels for reporting; no threshold-triggered retraining was performed, and each result comes from a single training run per model.

BARU:

> The technical criteria of Section III-A serve as reference levels for reporting. No threshold-triggered retraining was performed. Each result comes from a single training run per model.

### 2.16 Section III-E, paragraf "five auditable rules"

LAPA:

> The protocol reduces to five auditable rules: (1) one corpus and one split for all models, with the seed fixed and reported; (2) a shared data-processing and training protocol, with differences in encoder depth, capacity, and initialization stated explicitly (Table II); (3) per-model thresholds selected on validation data only, with test labels never consulted for tuning; (4) pooled and per-image metrics reported as separate, labeled columns and never averaged together; and (5) claims restricted to what the protocol supports, namely a within-dataset comparison and a reporting discipline, not a new predictor.

BARU:

> The protocol reduces to five auditable rules. (1) One corpus and one split for all models, with the seed fixed and reported. (2) A shared data-processing and training protocol, with differences in encoder depth, capacity, and initialization stated explicitly (Table II). (3) Per-model thresholds selected on validation data only, with test labels never consulted for tuning. (4) Pooled and per-image metrics reported as separate, labeled columns and never averaged together. (5) Claims restricted to what the protocol supports, namely a within-dataset comparison and a reporting discipline, not a new predictor.

### 2.17 Section IV-A paragraf pertama

LAPA:

> Each row uses the model's own validation-selected threshold; per-image Dice and IoU are averaged over the test images…

BARU:

> Each row uses the model's own validation-selected threshold. Per-image Dice and IoU are averaged over the test images…

### 2.18 Section IV-B paragraf kualitatif Fig. 7

LAPA:

> …(99.76-100.00%) across wildfire and clustered-urban damage; these are uncalibrated sigmoid outputs σ(z), not calibrated confidence.

BARU:

> …(99.76-100.00%) across wildfire and clustered-urban damage. These are uncalibrated sigmoid outputs σ(z), not calibrated confidence.

### 2.19 Section IV-C, kalimat "≈1.4" — GANTI ≈

LAPA:

> …with errors between ≈1.4 and 7.4 units depending on the item scale.

BARU:

> …with errors between approximately 1.4 and 7.4 units depending on the item scale.

### 2.20 Conclusion paragraf 2 (daftar future work)

LAPA:

> Future work therefore proceeds in four directions: event-held-out evaluation including Indonesian events unseen in training, with multi-seed runs; a one-phase versus two-phase ablation of the loss schedule; external validation of the demand estimators against historical BNPB distribution records; and benchmarking of further backbones, including DenseNet [25] and transformer encoders.

BARU:

> Future work therefore proceeds in four directions: event-held-out evaluation including Indonesian events unseen in training with multi-seed runs, a one-phase versus two-phase ablation of the loss schedule, external validation of the demand estimators against historical BNPB distribution records, and benchmarking of further backbones including DenseNet [25] and transformer encoders.

### 2.21 Table II, kolom Params — GANTI ~ dengan angka pasti (dari model summary)

| LAPA        | BARU        |
| ----------- | ----------- |
| `~4.7 M`  | `4.77 M`  |
| `~20.1 M` | `20.13 M` |
| `~49.4 M` | `49.40 M` |

(Angka persis hasil summary: 4,774,449 / 20,127,921 / 49,403,201, jadi pembulatan dua desimal di atas aman dan kehilangan konten nol.)

---

## 3. SHORT CAPTION SEMUA FIGURE & TABLE

Isi yang dipotong dari caption sudah dicek: semuanya sudah ada di teks badan (disebut di kolom "isi pindah ke" di bawah), jadi tidak ada konten hilang.

| Elemen    | CAPTION BARU (pendek)                                                                  | Isi yang dipotong & lokasinya sekarang                                                                                                                                                             |
| --------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fig. 1    | CRISP-DM adaptation for the controlled encoder comparison (Phases 1–5).               | "Deployment outside scope" sudah dijelaskan di paragraf pertama Section III                                                                                                                        |
| Fig. 2    | Training partition distribution across ten disaster categories (1,959 of 2,799 pairs). | Rasio 6.35% sudah ada di kalimat terakhir Data Understanding                                                                                                                                       |
| Fig. 3    | ResNet50-UNet architecture with five encoder stages and skip connections.              | Kalimat "other two models replace the encoder only" tidak perlu, karena §III-D sudah bilang "share the U-Net decoder topology … differ in the encoder" + Table II caption "shared U-Net decoder" |
| Fig. 4    | Architecture of the multi-output DNN regressor (seven inputs, 17 outputs).             | Detail blok (256/128/64, 32-unit, Dropout 0.3) pindah ke teks §III-D, lihat 3a di bawah                                                                                                           |
| Fig. 5    | Pooled confusion matrix of ResNet50-UNet on the held-out test set (t* = 0.9).          | Jumlah mask & piksel sudah ada di kalimat pertama §IV-B                                                                                                                                           |
| Fig. 6    | ROC curve of ResNet50-UNet on the validation set (AUC = 0.9838).                       | (Sesuai opsi poin 1, AUC test 0.9813 disebut di teks §IV-B)                                                                                                                                       |
| Fig. 7    | Damage heatmaps of eight validation samples (red = predicted damage).                  | Frasa "Ground-truth masks are not shown." dipertahankan sebagai kalimat kedua caption kalau mau, atau cukup caption pendek ini karena teks sudah menyebut prediction scores + keterbatasan         |
| Fig. 8    | Actual versus predicted values for all 17 logistics items (initial pipeline DNN).      | Frasa "released dataset [23]" + kesetaraan generator sudah dipindah ke teks paragraf Fig. 8, lihat 3b di bawah                                                                                     |
| Table I   | xView2 split across ten disaster events (2,799 pairs total).                           | Tidak ada yang hilang, kolom Train/Val/Test tetap di tabel                                                                                                                                         |
| Table II  | Encoder configurations compared (shared U-Net decoder).                                | Tetap, sudah pendek                                                                                                                                                                                |
| Table III | Segmentation comparison on the held-out test set.                                      | Info "validation-selected thresholds" sudah ada di kalimat pertama §IV-A                                                                                                                          |
| Table IV  | Multi-output regressor comparison (macro-averaged over 17 items).                      | Info "10,000 test samples" sudah ada di §III-E dan §IV-C                                                                                                                                         |
| Table V   | Per-item MAE for five representative items and the 17-item macro average.              | Satuan tiap item sudah ada di dalam tabelnya                                                                                                                                                       |

### 3a. Tambahan SATU kalimat di §III-D supaya detail Fig. 4 tidak hilang

Sisipkan setelah kalimat "…the DNN architecture is shown in Fig. 4." (atau gabung):

BARU (tambahan):

> The DNN stacks Dense-BatchNorm-Dropout(0.3) blocks of 256, 128, and 64 units, followed by a 32-unit Dense layer and 17 linear outputs.

### 3b. Tambahan SATU kalimat di paragraf Fig. 8 supaya catatan kesetaraan generator tidak hilang

Setelah kalimat "…visualizes this bimodal allocation." tambahkan:

BARU (tambahan):

> The regressors compared in Tables IV and V are trained on an equivalent synthetic generator with identical splits.

---

## 4. SISA KECIL SEKALIGUS DISELESAIKAN

1. Ref [1] masih `(accessed Mar. 25, 2026)` — tahun masih di masa depan. Ganti ke tanggal akses riil, contoh `Mar. 25, 2025`.
2. Table I baris terakhir `Total / average | 1,959 | 420 | 420` — ganti label jadi `Total` saja.
3. Konsistensi penulisan threshold: §IV-B dan caption Fig. 5 sekarang memakai `t* = 0.9`, sedangkan markdown/hasil run menulis `0.90`. Pilih satu (saran: `0.9` di semua tempat, sama dengan Table III).

---

## CHECKLIST STATUS

- [sudah] CM test set t* = 0.9 masuk §IV-B dan abstract/conclusion (F1 0.7255, IoU 0.5692)
- [sudah] Eq. (6) Dice_val, Table I, fan rule, rotasi, residu, macro-R² Conclusion
- [tinggal] Poin 1a-1d (label split AUC)
- [tinggal] Poin 2.1-2.21 (semua ; ~ ≈ yang tersisa)
- [tinggal] Poin 3 (semua caption pendek) + 3a-3b (pemindahan isi ke teks)
- [tinggal] Poin 4 (tanggal akses, label Total, konsistensi 0.9)
