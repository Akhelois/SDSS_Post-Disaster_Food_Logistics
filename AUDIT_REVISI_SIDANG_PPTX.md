# AUDIT & REVISI SIDANG-THESIS.pptx.pptx (22 slide)

Dibandingkan terhadap: manuskrip IEEE_Jason_Lee.docx versi terakhir (semua angka final dari
train_model.ipynb sel B1_FIX: test set 420 mask, t* = 0.9) dan hasil audit docx.
Format temuan: **LOKASI/SALINDIA (slide) → MASALAH → TEKS PENGGANTI SIAP SALIN** (bahasa Indonesia, mengikuti bahasa slide).

Tanggal PPTX: 29 Okt 16:06 — dibuat SEBELUM revisi angka & run B1_FIX (19:39), jadi wajar masih ada konten lama.

---

## RINGKASAN MASALAH (prioritas)

| # | Masalah                                                                                                                                                          | Slide    | Prioritas |
| - | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | --------- |
| 1 | Kesimpulan butir 01 dan 02 **duplikat persis** dan tidak memuat angka final                                                                                | 20       | P0        |
| 2 | Klaim kriteria/credential lama "MSE & MAE per epoch" untuk DNN (sudah ditegaskan reviewer di manuskrip)                                                          | 7        | P0        |
| 3 | Slide hasil DNN (15-16) memakai gambar **model DNN lama** (R² 0.9886, MAE 4-5) yang bertentangan dengan Table IV dokumen (R² 0.99834-0.99838, MAE 2.450) | 15, 16   | P0        |
| 4 | Tujuan Penelitian kalimat menggantung "yang mencapai nilai dan untuk segmentasi" (target IoU/F1 hilang)                                                          | 5        | P0        |
| 5 | Angka hasil segmentasi tidak final/ditampilkan sempit (CM lama t=0.894 vs hasil baru test t=0.9), TIDAK ada tabel perbandingan tiga encoder                      | 11-13    | P0        |
| 6 | Klaim "memangkas waktu IDA dari hitungan hari menjadi jam" tanpa angka pengukuran (di manuskrip kriteria runtime sudah dihapus karena tidak diukur)              | 19, 20   | P1        |
| 7 | Tidak ada keterangan split (pair-level, 2.799 pairs, 70:15:15) dan protokol threshold validation-based                                                           | 8-13     | P1        |
| 8 | Tidak ada batasan generalisasi (event-held-out) di slide Kesimpulan/Saran                                                                                        | 20, 21   | P2        |
| 9 | Judul slide pakai "Resnet50" (huruf kecil) vs "ResNet50" — konsistenkan]                                                                                        | 9, 11-13 | P2        |

---

## 1. Slide 20 (Kesimpulan) — P0, bug duplikat + ganti isi

**MASALAH:** Butir 01 dan 02 sekarang **sama persis** ("Model ResNet50-UNet berhasil dilatih pada dataset xView2 dan melewati threshold IoU & F1-Score untuk segmentasi kerusakan bangunan multi-bencana dari citra satelit.").. Selain duplikat, tidak ada angka hasil final dan tidak ada hasil perbandingan tiga encoder.

**PENGGANTI (3 butir lengkap):**

- **01** — Model ResNet50-UNet memenuhi kriteria teknis pada test set xView2 (2.799 pair citra, split 70:15:15, threshold t* = 0.9 dipilih dari validation set) dengan Dice per-gambar 0.6521, F1 pooled 0.7255, dan IoU pooled 0.5692 (target IoU dan F1 ≥ 0.50 terlampaui).
- **02** — Dibandingkan CNN U-Net (Dice 0.5934) dan VGG16-UNet (Dice 0.5372) di bawah protokol yang sama, ResNet50-UNet terbaik untuk segmentasi kerusakan bangunan dari citra satelit multi-bencana.
- **03** — Sistem SDSS menunjukkan potensi pengurangan latensi informasi signifikan dibandingkan IDA manual sesuai SOP BNPB, mendukung pengambilan keputusan logistik pangan yang lebih cepat dan berbasis data pada Golden Time 72 jam pertama.

*(Catatan: kalimat 03 dipertahankan sebagai klaim "potensi" karena waktu tidak diukur formal di manuskrip.)*

---

## 2. Slide 7 (Theoretical Framework, baris konsep No. 8) — P0

**MASALAH:** "Metrik Evaluasi — CNN: IoU & F1-Score ≥ 0,5 · DNN: MSE & MAE per epoch". Frasa "MSE & MAE per epoch" adalah deskripsi training history yang sudah ditegaskan reviewer di manuskrip (bukan kriteria evaluasi), dan kriteria DNN yang benar lain.

**PENGGANTI baris No. 8:**

> Metrik Evaluasi | CNN: IoU & F1-Score ≥ 0,5 · DNN: MAE, RMSE, dan macro-R² (17 item, R² ≥ 0,90)

---

## 3. Slide 15 & 16 (Hasil Penelitian DNN) — P0, artefak model lama

**MASALAH:** Kedua slide menampilkan gambar dari model DNN lama (single-model pipeline):

- Gambar di slide 15 = `Evaluation_Metrics_Summary_Logistics.png` (R² rata-rata 0.9816, MAE 1.1-4.8 per item — model lama, bukan hasil Table IV)
- Gambar di slide 16 = `Prediction_vs_Actual_Comparison_Logistics.png` (scatter 17 item model lama)

Angka-angka ini bertentangan dengan hasil komparasi di dokumen: MAE 2.535 / 2.478 / 2.450 dan macro-R² 0.99834 / 0.99838 / 0.99838. Penguji yang membaca dokumen akan menanyakan kenapa slide memakai angka lain.

**PENGGANTI (ganti isi slide 15 menjadi tabel sederhana, judul dipertahankan "Hasil Penelitian (DNN)":**

| Model   | MAE   | RMSE  | Macro-R² |
| ------- | ----- | ----- | --------- |
| ANN/MLP | 2.535 | 3.518 | 0.99834   |
| DCN     | 2.478 | 3.468 | 0.99838   |
| DNN     | 2.450 | 3.455 | 0.99838   |

Tambahkan bullet di bawah tabel:

> Macro-R² setara di ketiga model (setiap item berbobot sama). DNN terbaik pada absolute error (MAE 2.450). Target dibalik ke satuan asli (kg/pcs) sebelum MAE/RMSE dihitung.

**Slide 16:** gambar scatter model lama boleh dipertahankan asalkan diberi bullet konteks di bagian atas slide:

> Scatter plot dari pipeline DNN awal pada dataset publik (Zenodo). Regresi komparasi (tabel di slide sebelumnya) memakai generator sintetik yang setara dengan splits identik.

*(Alternatif terbaik: regenerate scatter yang sama dari prediksi DNN komparasi, satu kali inference pada 10.000 sample test — tanpa training ulang.)*

---

## 4. Slide 5 (Tujuan Penelitian) — P0, frasa menggantung

**MASALAH:** Butir pertama terbaca "…model CNN (ResNet50-UNet) yang mencapai nilai DAN untuk segmentasi kerusakan pasca-bencana" — ada kata kosong (target IoU/F1 tidak ditulis).

**PENGGANTI butir 1:**

> Untuk mengembangkan dan memvalidasi secara teknis model segmentasi ResNet50-UNet yang mencapai IoU pooled ≥ 0.50 dan F1 pooled ≥ 0.50 pada test set xView2 untuk segmentasi kerusakan bangunan pasca-bencana.

*(Butir 2 dan 3 tidak diubah.)*

---

## 5. Slide 11-13 (Hasil segmentasi) — P0, Pastikan angka final

Peta gambar yang tertancap (dari fingerprint):

- Slide 11 = `Training_History.png` (identik) → aman sebagai proses training, biarkan.
- Slide 12 = montase threshold/confusion matrix (kemungkinan `Threshold_Analysis/Threshold_Optimization/Confusion_Matrix.png` lama) → **CEK: semua confusion matrix di slide ini harus diganti** dengan `backend/model/Confusion_Matrix_test_t090.png` (test set, t* = 0.9, TN 25.048.246 / FP 681.676 / FN 385.343 / TP 1.409.855). Gambar lama dengan judul "threshold=0.894" dan sel lain JANGAN dipakai lagi.
- Slide 13 (vs CNN vs VGG16) = gambar montase → pastikan isinya tabel perbandingan berikut:

**Konten pengganti slide 13 (tabel + catatan):**

| Model         | t* (validation) | Dicemean (test) | IoU mean (test) |
| ------------- | --------------- | --------------- | --------------- |
| VGG16-UNet    | 0.5             | 0.5372          | 0.4199          |
| CNN U-Net     | 0.2             | 0.5934          | 0.4757          |
| ResNet50-UNet | 0.9             | 0.6521          | 0.5396          |

Bullet:

> Threshold dipilih per model dari validation set (grid 0.10-0.90, step 0.05, kriteria mean per-image Dice), dilaporkan terpisah dari metrik pooled.
> Ranking di atas berlaku untuk split pair-level pada dataset ini, belum membuktikan generalisasi ke event bencana baru.

---

## 6. Slide 8-13 (Metodologi) — P1, tambahkan protokol split & threshold

Tambahkan satu bullet di slide 8 (Metodologi) atau slide 9:

> Dataset: 2.799 pasangan citra pre/post-disaster dari 10 event xView2, split 70:15:15 di level pasangan citra (seed 42). Input 6-channel (RGB pre + RGB post). Threshold dipilih dari validation set per model, lalu diterapkan ke test set tanpa diubah.

*(Kalimat "diterapkan ke test set tanpa diubah" penting untuk menjawab pertanyaan penguji soal kebocoran data.)*

---

## 7. Slide 19 (Implikasi) & 20 (Kesimpulan 03) — P1

**MASALAH:** "Memangkas waktu IDA dari hitungan hari menjadi jam" adalah klaim waktu tanpa pengukuran formal (di manuskrip kriteria runtime sengaja dihapus karena tidak diukur). Penguji bisa meminta bukti benchmark-nya.

**PENGGANTI (versi aman):**

> Berpotensi memangkas waktu penilaian kerusakan (IDA) dari hitungan hari menjadi hitungan jam, dengan catatan pengukuran formal end-to-end masih perlu dilakukan pada fase deployment.

---

## 8. Slide 21 (Saran) — P2, selaraskan dengan future work dokumen

Tambahkan (atau ganti salah satu butir):

> Evaluasi event-held-out (event bencana yang tidak ada di training) dan pengulangan training dengan beberapa random seed untuk menguji stabilitas ranking antar encoder.


---

## 9. Konsistensi kecil — P2

1. Judul slide 9, 11, 12, 13: "Resnet50" / "ResNet50-Unet" → rapikan menjadi **ResNet50-UNet** (konsisten dengan dokumen).
2. Slide 1: judul tesis "Berbasis CNN" — pertimbangkan "Berbasis Deep Learning" atau "Berbasis ResNet50-UNet" karena modelnya bukan CNN generik (opsional, bukan wajib).
3. Kalau ada ROC curve di slide mana pun: label wajib — "AUC 0.9838 (validation set)" atau "AUC 0.9813 (test set)". Jangan tulis AUC tanpa label split.
4. Slide 14 "(Simulasi)": pastikan diberi label "eksploratif, event di luar dataset training" bila event-nya bukan bagian dari 10 event xView2 yang dipakai training.
5. Slide 22: tahun "2026" — cocokkan dengan tahun akademik sidang.

---

## PETA GAMBAR SLIDE → SUMBER (hasil fingerprint, untuk memudahkan pembersihan)

| Slide             | File di PPTX          | Kemiripan artefak                                                 | Status                                                                                       |
| ----------------- | --------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| 11                | image9                | Training_History.png (identik, diff 0.4)                          | aman                                                                                         |
| 15                | image13               | Evaluation_Metrics_Summary_Logistics.png (identik, diff 1.0)      | GANTI (model DNN lama)                                                                       |
| 16                | image14               | Prediction_vs_Actual_Comparison_Logistics.png (identik, diff 1.0) | relabel atau regenerate                                                                      |
| 12                | image10               | mirip montase threshold/CM lama (CEK visual)                      | pastikan CM = versi test t* = 0.9                                                            |
| 13                | image11               | montase perbandingan (CEK visual)                                 | pastikan tabel Dice/IoU = versi final                                                        |
| 9, 10, 14, 17, 18 | image7, 8, 12, 15, 16 | diagram pipeline / montase / dashboard                            | cek visual, pastikan tidak ada angka lama (0.8917, 0.7311, 0.9816, MAE 4.09, akurasi 97.23%) |

**Angka-angka lama yang HARUS TIDAK muncul di slide mana pun** (semua sudah digantikan di dokumen):

- threshold 0.8937 / 0.894 / 0.8917 / 0.8926 (sekarang: 0.9)
- F1 0.7311 / 0.7316 / 0.7321, IoU 0.5756 / 0.5767 (sekarang: F1 0.7255, IoU 0.5692)
- CM sel: TN 25,366,010 / TP 1,245,150 dst. (sekarang: TN 25,048,246 / FP 681,676 / FN 385,343 / TP 1,409,855)
- akurasi 97.23%, AUC 0.9836 (sekarang: val 0.9838, test 0.9813)
- R² 0.9886 / 0.9816, MAE 4.09 / 5.71, RMSE 8.18 / 9.07 (sekarang: R² 0.99834-0.99838, MAE 2.450-2.535, RMSE 3.455-3.518)

## CHECKLIST EKSEKUSI

1. [ ] Slide 20 — ganti butir 02 (duplikat) dengan hasil perbandingan encoder (teks di bagian 1)
2. [ ] Slide 7 — ganti baris Metrik Evaluasi No. 8 (teks di bagian 2)
3. [ ] Slide 15 — ganti gambar menjadi tabel komparasi regressor (teks di bagian 3); slide 16 — relabel scatter model lama
4. [ ] Slide 5 — lengkapi target IoU/F1 pada butir 1 (teks di bagian 4)
5. [ ] Slide 12-13 — pastikan semua confusion matrix = `Confusion_Matrix_test_t090.png`; tabel encoder = angka final (bagian 5)
6. [ ] Slide 8/9 — tambah bullet protokol split & threshold (bagian 6)
7. [ ] Slide 19/20 — alih-kata klaim latensi (bagian 7)
8. [ ] Slide 21 — tambah saran event-held-out dan multi-seed (bagian 8)
9. [ ] Sweep terakhir: cari angka-angka lama di daftar "HARUS TIDAK MUNCUL"
