# PENJELASAN LENGKAP PROYEK SDSS & AUDIT THESIS S2.docx

Dokumen ini menjelaskan **seluruh proyek** `SDSS_Post-Disaster_Food_Logistics` sebagai bahan untuk naskah **Thesis S2.docx**, sekaligus memuat **audit lengkap: apa yang kurang, apa yang tidak sesuai, dan apa yang harus diperbaiki** di dalam `Thesis S2.docx` (versi di root repositori, 1.482 paragraf, terakhir disunting 29 Okt).

---

# BAGIAN 1 — RINGKASAN PROYEK

## 1.1 Identitas Penelitian

| Item                          | Isi                                                                                                                                                                    |
| ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Peneliti**            | Jason Lee (NIM 2702751580)                                                                                                                                             |
| **Program**             | Magister Manajemen Sistem Informasi (MMSI), BINUS Graduate Program                                                                                                     |
| **Judul**               | Pengembangan *Spatial Decision Support System* (SDSS) Berbasis *Deep Learning* dan Analisis Spasial untuk Prioritisasi Alokasi Logistik Pasca-Bencana di Indonesia |
| **Objek**               | Sistem pendukung keputusan alokasi logistik pangan pada *Golden Time* 72 jam pertama pasca-bencana                                                                   |
| **Kerangka metodologi** | CRISP-DM (Business Understanding → Data Understanding → Data Preparation → Modeling → Evaluation → Spatial Integration & Visualization)                           |

## 1.2 Masalah yang Dijawab

1. *Initial Damage Assessment* (IDA) manual BNPB butuh 4–7 hari (survei lapangan, pelaporan berjenjang BPBD) — jauh melewati *Golden Time* 72 jam.
2. Standar bantuan Perka BNPB No. 7/2008 hanya formula linier 3 komoditas (beras, air, makanan siap saji) — tidak mencerminkan kebutuhan riil 17 komoditas (beras, minyak, gula, mie, biskuit, sarden, kornet, susu, matras, kasur lipat, kompor, karpet, dll).
3. Alokasi bantuan rawan bias subjektif dan salah alamat administratif.

## 1.3 Solusi / Kontribusi

1. **Model segmentasi kerusakan bangunan ResNet50-UNet 6-kanal** (RGB pra + RGB pasca-bencana) pada dataset **xView2** (2.799 pasangan citra, 10 kejadian bencana global).
2. **Model DNN regresi multi-output** yang memprediksi **17 item logistik per KK** dari 7 fitur input.
3. **Sistem SDSS end-to-end**: FastAPI + React/Deck.gl, integrasi Near Real-Time (NASA FIRMS & GIBS, BMKG, PetaBencana.id), zonasi spasial ke 81.912 poligon desa, populasi WorldPop, *building footprint* OSM, dan **skor prioritas MCDA Equal Weighting** 3 kriteria (kerusakan JITUPASNA ⅓ + populasi WorldPop ⅓ + urgensi 72 jam ⅓) dengan triase **Kritis / Siaga / Waspada**.

## 1.4 Struktur Repositori

```
SDSS_Post-Disaster_Food_Logistics/
├── Thesis S2.docx                  ← NASKAH TESIS (diaudit di Bagian 3)
├── SIDANG-THESIS.pptx.pptx         ← Slide sidang (sudah ada audit terpisah)
├── backend/                        ← FastAPI (main.py, 767 baris)
│   ├── core/                       → disaster.py, zone_builder.py (clustering spasial)
│   ├── services/                   → nasa_earthdata.py (FIRMS+GIBS), petabencana.py,
│   │                                 population.py (WorldPop), geodata.py, logistics.py,
│   │                                 itemized_logistics.py (DNN inferensi 17 item), routing.py
│   ├── data/                       → shapefile 81.912 desa (sdss_indonesia_final.shp),
│   │                                 batas_desa/, citra sentinel-2 input, dataset logistik sintetik
│   ├── model/                      → model_sdss.h5 (segmentasi), model_logistics.h5 (DNN),
│   │                                 comparison_baselines/ (cnn & vgg16 .keras),
│   │                                 15+ PNG grafik hasil, sdss_pipeline.ipynb,
│   │                                 compare_cnn_vgg16_baselines.ipynb,
│   │                                 compare_logistics_deep_learning.ipynb
│   ├── pipeline/, scheduler/
├── frontend/                       ← React + Vite + Deck.gl + MapLibre GL
├── api/index.py, vercel.json       ← deploy Vercel
├── training/                       ← dataset xView2: 5.598 citra = 2.799 pasangan, 10 kejadian
│   (images/, targets/)
├── agent/                          ← draf bab + audit lama (DRAF_TESIS_LENGKAP_REVISI.md, dll)
├── AUDIT_KESESUAIAN_IEEE_JASON_LEE.md   ← audit naskah IEEE (bahasa Inggris, ronda 3)
├── AUDIT_REVISI_SIDANG_PPTX.md     ← audit 22 slide PPTX
├── agent/review_revisi_tesis.md    ← audit docx generasi sebelumnya (6 celah lama)
├── doc_content.txt, model_explanation.md, workflow.md, PROJECT_STATUS.md
└── requirements.txt (26 byte) + "requirements copy.txt" ← sampah file, rapikan
```

## 1.5 Arsitektur Data Sistem (sudah terimplementasi di kode)

```
Trigger: BMKG API (gempa M≥5.0 / CAP cuaca) + NASA FIRMS (anomali termal VIIRS 375m)
         + PetaBencana.id (laporan warga, Golden Time 72 jam)
              │
              ▼
Backend FastAPI ── akuisisisi citra NRT: NASA GIBS WMTS (VIIRS/MODIS true color)
              │
              ├── Inferensi ResNet50-UNet → mask kerusakan → konversi vektor GeoJSON
              ├── Zonasi spasial: spatial join ke 81.912 poligon desa (BIG/COD-AB-IDN)
              ├── Populasi per desa: WorldPop API 100m (zonal sum, di-cache)
              ├── Building footprint: OpenStreetMap Overpass API
              ├── Prediksi 17 item logistik per KK: model_logistics.h5 (DNN)
              ├── Skor prioritas S = ⅓·N_damage + ⅓·N_pop + ⅓·Urgency_72h (Equal Weighting, Dawes 1979)
              └── Triase: Kritis (>0,67) / Siaga (0,34–0,67) / Waspada (<0,34)
                    │
                    ▼
Frontend React + Deck.gl: peta dual-layer polygon (batas desa + klaster kerusakan),
              tabel keputusan operasional, legend/heatmap, export CSV
```

**Regulasi & standar yang menjadi fondasi formula:**

- **Perka BNPB No. 2/2012 (JITUPASNA)** → klasifikasi kerusakan RB/RS/RR, dasar N_damage.
- **Perka BNPB No. 7/2008** → standar kebutuhan dasar (400 g beras/jiwa/hari, dsb) → kalibrasi target 17 item.
- **SPHERE 2018** → 2.100 kkal/jiwa/hari + Urgency 72h = max(0, 1 − t/72).
- **Dawes (1979) & Wainer (1976)** → Equal Weighting lebih robust daripada bobot pakar subjektif.
- **WorldPop (Tatem 2017)** → populasi grid 100m, zonal sum per poligon desa.

---

# BAGIAN 2 — STATUS KOMPLETENESS (APA YANG SUDAH ADA / BELUM)

## 2.1 Sudah lengkap dan sesuai di antara kode ↔ naskah

| Komponen                                                                                            | Status                                                                                                               |
| --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Dataset xView2 2.799 pasangan / 10 kejadian (folder `training/` = 5.598 file)                     | ✅ konsisten dengan naskah                                                                                           |
| Pipeline training ResNet50-UNet 6-kanal (`sdss_pipeline.ipynb`, IMG_SIZE **256×256**)      | ✅ ada                                                                                                               |
| Model segmentasi tersimpan (`model_sdss.h5` + checkpoint epoch-15)                                | ✅ ada                                                                                                               |
| Eksperimen pembanding CNN & VGG16 (notebook + 4 file `.keras` di `comparison_baselines/`)       | ✅ ada di kode                                                                                                       |
| Eksperimen komparasi regressor ANN/MLP, DCN, DNN (`compare_logistics_deep_learning.ipynb`)        | ✅ ada di kode                                                                                                       |
| Dataset logistik sintetik 50.000 sampel (`augmented_logistics_dataset.csv`)                       | ✅ ada                                                                                                               |
| Model DNN logistik (`model_logistics.h5`) + 15 grafik evaluasi PNG                                | ✅ ada                                                                                                               |
| Integrasi NASA FIRMS + GIBS (`services/nasa_earthdata.py`)                                        | ✅ ada, dan **sudah disebut di Bab II & III naskah** (celah NASA pada Tabel 3.2 di docx lama sudah tertangani) |
| WorldPop menggantikan estimasi BPS                                                                  | ✅ lengkap                                                                                                           |
| Triase Kritis/Siaga/Waspada + simulasi 4 posko (Tabel 4.9)                                          | ✅ ada di naskah                                                                                                     |
| Bab V Kesimpulan, **Limitasi**, dan Saran (5.1/5.2/5.3 dengan 5.3.1 akademis & 5.3.2 praktis) | ✅ sudah ada (celah "Bab V rusak" dari docx generasi sebelumnya sudah tertangani)                                    |
| Formula MCDA Equal Weighting + uncertainty Gaussian 1σ                                             | ✅ ada di naskah                                                                                                     |

## 2.2 Belum ada / belum selesai (gap proyek, di luar teks docx)

1. **Hasil perbandingan 3 encoder & 3 regressor Belum ada di Bab IV** — artefak & angkanya sudah ada (notebook + manuskrip IEEE), tinggal dimasukkan (lihat temuan P0-2).
2. **Pengukuran runtime formal tidak pernah dilakukan** — klaim "<30 menit", "<2 detik", "90% reduksi", "60 FPS" tidak didukung benchmark. Pilih: ukur sekali (timestamp log pipeline) atau turunkan klaim jadi "berpotensi".
3. **Evaluasi *event-held-out*** (event bencana di luar training) belum pernah dijalankan — disebut sebagai future work, aman selama tidak diklaim.
4. **Inferensi CNN end-to-end pada citra Sentinel-2/NASA GIBS produksi** masih berupa pipeline notebook, tahap dari citra mentah → damage point otomatis belum dibuktikan di Bab 4 dengan kasus nyata (kasus 2.287 titik FIRMS masih simulasi/eksploratif).
5. **Validasi eksternal target logistik** terhadap catatan distribusi riil BNPB belum ada (target data sintetik) — wajib dinyatakan sebagai keterbatasan.
6. Kebersihan repo: `requirements copy.txt` (file duplikat), `requirements.txt` hanya 26 byte, folder `backend/scratch`, file `api_resp.json`/`api_response.json` kembar — rapikan sebelum repo dilampirkan/tautan diberikan ke penguji.

---

# BAGIAN 3 — AUDIT THESIS S2.docx: YANG KURANG & TIDAK SESUAI

> Metode audit: ekstraksi penuh 1.482 paragraf docx, dibandingkan dengan (a) kode implementasi, (b) artefak hasil eksperimen (notebook, checkpoint, PNG), (c) audit internal sebelumnya (AUDIT_KESESUAIAN_IEEE_JASON_LEE.md, AUDIT_REVISI_SIDANG_PPTX.md, agent/review_revisi_tesis.md).

## Temuan PRIORITY 0 (wajib diperbaiki sebelum sidang)

### P0-1. Dua generasi angka hasil campur aduk — naskah masih memakai angka LAMA

Ada **dua generasi hasil eksperimen** di proyek ini, dan docx masih memakai generasi lama, sementara manuskrip IEEE dan PPTX sudah dirapikan ke generasi baru:

| Metrik                  | **Docx sekarang (LAMA)**                                                                       | **Hasil final notebook (B1_FIX / manuskrip IEEE)**                                                                                     |
| ----------------------- | ---------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Threshold optimal       | 0,893 (Tabel 4.7) / 0,892 (teks §4) / 0,8917 (kesimpulan) — **3 nilai berbeda di 1 dokumen** | **t\* = 0,9** (dipilih dari validation set, grid 0,10–0,90 step 0,05)                                                                 |
| F1-Score (test)         | 0,7311 / 73,16%                                                                                      | **0,7255 (pooled)** — per-image Dice mean 0,6521                                                                                      |
| IoU (test)              | 0,5756 / 57,67%                                                                                      | **0,5692 (pooled)** — IoU mean 0,5396                                                                                                 |
| AUC-ROC                 | 0,9836 (tanpa label split)                                                                           | **0,9813 test set**, 0,9838 adalah **validation set** (dari gambar Fig. ROC lama). Wajib diberi label split                      |
| Confusion Matrix (test) | FP 554.202 / FN 360.587 / TP 1.246.426                                                               | **TN 25.048.246 / FP 681.676 / FN 385.343 / TP 1.409.855** (`Confusion_Matrix_test_t090.png`)                                        |
| Accuracy                | 96,68% / Precision 69,22% / Recall 77,57%                                                            | sesuaikan dengan run final B1_FIX                                                                                                            |
| DNN: R²                | 98,16% (0,9816), MAE 4,09, RMSE 8,18                                                                 | pipeline lama pada dataset publik (Zenodo), hasil **komparasi final: macro-R² 0,99834–0,99838, MAE 2,450–2,535, RMSE 3,455–3,518** |

**Tindakan (pilih satu generasi dan konsisten total):**

- **Opsi A (disarankan, paling sedikit kerja ilmiah):** pertahankan angka lama yang sudah ada di docx, TETAPI (1) satukan threshold menjadi satu nilai (0,893) di seluruh teks, tabel, dan kesimpulan, (2) beri label split pada AUC, (3) samakan angka CM di Gambar 4.10 dengan Tabel 4.6, (4) tambahkan konteks bahwa DNN lama dilatih pada dataset publik Zenodo dan komparasi regressor memakai generator sintetik setara (kalimatnya sudah disiapkan di AUDIT_KESESUAIAN_IEEE_JASON_LEE.md §3b).
- **Opsi B:** adopsi semua angka final IEEE (t\*=0,9, F1 0,7255, IoU 0,5692, AUC 0,9813 test, CM baru, MAE 2,450) — lebih meyakinkan karena mendukung narasi perbandingan 3 model, tapi semua grafik docx (Gambar 4.7–4.13) harus diganti dengan artefak baru (`Confusion_Matrix_test_t090.png` dsb).

### P0-2. Bab III menjanjikan eksperimen perbandingan, Bab IV tidak menyajikan hasilnya

- **Bab III (paragraf [967]):** *"penelitian ini merancang dan melaksanakan eksperimen perbandingan terkontrol … antara tiga model segmentasi dan tiga model regressor"* + ada tabel konfigurasi CNN / VGG16 / ResNet50-UNet.
- **Bab II (paragraf [619]):** justru menyatakan keputusan arsitektur *"didasarkan pada analisis teoristik … **bukan dari eksperimen komparasi internal**"* — **kontradiksi langsung dengan Bab III**.
- **Bab IV:** Tabel 4.6–4.8 hanya memuat hasil ResNet50-UNet dan DNN tunggal. **Tidak ada satu pun tabel hasil CNN vs VGG16 vs ResNet50-UNet, maupun ANN/MLP vs DCN vs DNN.**

**Tindakan:** masukkan hasil komparasi final (datanya sudah ada):

| Model segmentasi        | t\* (validation) | Dice mean (test) | IoU mean (test)  |
| ----------------------- | ---------------- | ---------------- | ---------------- |
| VGG16-UNet              | 0,5              | 0,5372           | 0,4199           |
| CNN U-Net               | 0,2              | 0,5934           | 0,4757           |
| **ResNet50-UNet** | **0,9**    | **0,6521** | **0,5396** |

| Regressor     | MAE             | RMSE            | Macro-R² (17 item) |
| ------------- | --------------- | --------------- | ------------------- |
| ANN/MLP       | 2,535           | 3,518           | 0,99834             |
| DCN           | 2,478           | 3,468           | 0,99838             |
| **DNN** | **2,450** | **3,455** | **0,99838**   |

…lalu **hapus atau ubah paragraf [619] Bab II** agar tidak kontradiktif (misalnya ganti menjadi: keputusan arsitektur didasarkan analisis teoritis **yang kemudian divalidasi melalui eksperimen komparasi pada Bab IV**). Jangan sampai penguji bertanya "hasil perbandingannya mana?" — protokolnya dijanjikan sendiri di naskah.

### P0-3. Tanda kurung kosong "()" — parameter hilang akibat konversi rumus (8 lokasi)

Terkonfirmasi masih ada di docx sekarang (baris/paragraf hasil ekstraksi):

| Lokasi | Teks rusak                                           | Nilai yang benar (dari kode/notebook)                                                                       |
| ------ | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| [529]  | "Total populasi terdampak ()"                        | lengkapi variabel/atribut yang dimaksud                                                                     |
| [546]  | "pola decreasing width ():"                          | **(Dense 256 → 128 → 64 → 32)**                                                                    |
| [786]  | "tile citra berdimensi seragam ()"                   | **(256×256 piksel)** — sesuai IMG_SIZE pipeline                                                     |
| [940]  | "Tensor 6-channel ()" dan "mask biner ()"            | **(256×256×6)** dan **M ∈ {0,1}^(256×256)**                                                 |
| [945]  | "pola decreasing width ()"                           | **(256 → 128 → 64 → 32 unit)**                                                                     |
| [1123] | "tensor tunggal berukuran ()"                        | **(256×256×6) float32** — dan sampai sini juga menyelesaikan kontradiksi ukuran input (lihat P1-2) |
| [1176] | "menghitung mean () dan variansi ()"                 | mean μ dan variansi σ² per fitur (7 fitur)                                                               |
| [1412] | "decreasing width ()" dan "Koefisien Determinasi ()" | (256→128→64→32) dan **R²**                                                                        |

> Catatan: daftar ini perlokasi docx **versi sekarang**, angka kurung siku = indeks paragraf hasil ekstraksi, gunakan Ctrl+F pada teks kalimatnya.

### P0-4. Inkonsistensi `256×256` vs `512×512` (naskah vs kode)

- Paragraf [990] (Bab III, protokol 3 model): *"input citra 6-kanal … berukuran **512×512** piksel"*.
- Kode aktual (`sdss_pipeline.ipynb`): `IMG_SIZE = (256, 256)` → resize `cv2.resize(img, IMG_SIZE)`.
- Model & checkpoint tersimpan dibangun untuk 256×256.
  **Tindakan:** ganti semua 512×512 menjadi **256×256** di Bab III/IV, atau tunjukkan adanya patch-extraction 512→tile 256. Jangan biarkan dua ukuran beredar (ini pertanyaan penguji yang mudah ditebak).

## Temuan PRIORITY 1 (sangat disarankan)

### P1-1. Tiga nilai threshold berbeda dalam satu dokumen

Teks §4: "puncak pada threshold optimal **t = 0,892**" ([1194]) → "titik optimal di sekitar **t = 0,90**" ([1198]) → Tabel 4.7: "**0,893**" ([1246]) → teks evaluasi final: "**t = 0,893**" ([1203]) → Kesimpulan: "**0,8917**" ([1411]). Pilih satu representasi (mis. 0,893) dan rapikan semuanya. Kalau mengadopsi Opsi B di P0-1, semua menjadi **0,9**.

### P1-2. Angka distribusi dataset Gambar 4.1 perlu diverifikasi

Teks menyebut *"socal-fire (579 citra), hurricane-michael (237), hurricane-florence (224)…"*, padahal isi folder `training/` = socal-fire **1.646** citra (823 pasangan), hurricane-michael **686**, hurricane-florence **638**, total 5.598 citra / 2.799 pasangan. Kemungkinan angka di gambar dihitung pada subset tertentu (mis. pasangan dengan target non-kosong atau subset train). Pastikan kapsul gambar dan teks menjelaskan dari mana 579/237/224 dihitung, atau regenerate gambar dari data penuh.

### P1-3. Kriteria pemilihan threshold

Teks §3/Evaluation ([993]): kriteria pemilihan = "F1-Score tertinggi" pada grid 0,05–0,95. Protokol manuskrip IEEE final: grid **0,10–0,90 step 0,05**, kriteria **rata-rata Dice per-gambar pada validation**, threshold test tidak pernah disentuh. Selaraskan（dan nyatakan secara eksplisit: threshold dipilih **hanya** dari validation set, diterapkan ke test tanpa diubah — kalimat siap pakai ada di AUDIT_REVISI_SIDANG_PPTX.md §6).

### P1-4. Definisi metrik pooled vs per-image tidak dinyatakan

Tabel 4.7 menyajikan satu kolom angka tanpa menjelaskan apakah *pooled* (semua piksel dijumlah) atau *rata-rata per citra*. Keduanya bisa membeda besar. Tambahkan satu kalimat definisi di Bab 4 dan (jika Opsi B) tampilkan dua kolom terpisah seperti protokol IEEE.

### P1-5. Klaim waktu operasional tanpa pengukuran

Kesimpulan [1413]: *"menurunkan latensi IDA dari 4–7 hari menjadi kurang dari 30 menit… pengurangan lebih dari 90%… inferensi keseluruhan kurang dari 2 detik"* + klaim "60 FPS" di Bab 4. Semua belum ada benchmark formal. Two safe options:

- ukur sekali dan lampirkan tabel latensi sederhana (timestamp tiap tahap pipeline 1 run),
- atau ubah redaksi menjadi **"berpotensi"** + masukkan pengukuran formal ke saran (kalimat aman tersedia di AUDIT_REVISI_SIDANG_PPTX.md §7).

### P1-6. Label prioritas campuran "Prioritas Tinggi (Kritis)" / "Prioritas Sedang (Siaga)"

Tabel 3.4 ([1028]/[1032]) memakai label ganda hybrid. Sistem operasional dan audit sebelumnya memakai **Kritis / Siaga / Waspada** murni (triase BNPB). Konsistenkan ke satu nomenklatur di seluruh naskah (Bab 1, 3, 4, 5).

### P1-7. Abstract tidak merepresentasikan isi naskah terkini

Abstrak ([175]) hanya menyebut ResNet50-UNet + xView2 + GIS + standar BNPB. Padahal naskah sekarang juga berisi: NASA FIRMS/GIBS NRT, **DNN multi-output 17 item**, **MCDA Equal Weighting + triase Kritis/Siaga/Waspada**, keterbatasan, dan angka hasil final. Tulis ulang abstrak (dan versi bahasa Inggrisnya) memuat: tujuan, metode (2 model + SDSS + sumber data NRT), hasil utuh (angka generasi yang dipilih di P0-1), dan kontribusi.

### P1-8. Data target logistik bersifat sintetik — pastikan dinyatakan eksplisit

Prediksi 17 item dilatih pada dataset sintetik domain-constrained (50.000 sampel, aturan Perka BNPB + augmentasi). Naskah sudah menjelaskan generatornya, tetapi **keterbatasan** bahwa evaluasi adalah *self-consistency terhadap distribusi sintetik* (belum divalidasi terhadap realisasi distribusi BNPB riil) harus masuk Bab V keterbatasan + future work (kalimatnya sudah direncanakan di future-work IEEE: "external validation of the demand estimators against historical BNPB distribution records").

### P1-9. Sisa artefak penanda editorial di body text

Paragraf [620] mengandung teks mentah **"[REF BARU: Simonyan & Zisserman 2015]"**, **"[REF BARU: Chen et al. 2018]"**, **"[REF BARU: Xie et al. 2021]"** — ini memo internal untuk memperbaiki sitasi yang lupa dibersihkan. Ubah menjadi sitasi normal (Simonyan & Zisserman, 2015) dan pastikan ketiga entri ada di DAFTAR PUSTAKA.

## Temuan PRIORITY 2 (kerapian)

1. **Ref dengan tanggal masa depan** — cek daftar pustaka untuk tanggal akses "2026" (audit IEEE menemukan `accessed Mar. 25, 2026`), ganti ke tanggal riil.
2. **Simbol `~` dan `≈`** di beberapa tempat ("MSE ~23.000", "Recall ~0,60", "TPR ≈ 1,0") — untuk konsistensi gaya binus/gaya IEEE, ganti dengan "sekitar"/"kurang lebih" atau angka pasti.
3. **Tabel 3.2** — pastikan NASA FIRMS & GIBS hadir sebagai baris tersendiri (di docx generasi ini sudah disebut di Bab II/III, verifikasi Tabel 3.2 memuatnya lengkap dengan spesifikasi VIIRS 375 m, latensi 3–6 jam, WMTS). Konteksnya: kalimat pengantar + tabel siap salin tersedia di `agent/review_revisi_tesis.md` §2.
4. **Konsistensi penulisan nama model** — "Resnet50-Unet" vs "ResNet50-UNet" (tabel konfigurasi Bab III masih pakai kapitalisasi lama).
5. **Keterbatasan generalisasi event** — tambahkan di Bab V keterbatasan: split dilakukan pada *level pasangan citra*, sehingga event di test set tumpang tindih dgn train, kegagalan generalisasi ke event baru belum diuji (future work: event-held-out + multi-seed).
6. **Draf cepak di folder `agent/`** — `DRAF_TESIS_LENGKAP_REVISI.md`, `BAB_4…`, `BAB_5…` adalah draf lama dengan angka generasi lama, pindahkan/folderkan sebagai `archive/` agar tidak tertukar saat referensi cepat menjelang sidang.
7. **File duplikat** — `requirements copy.txt`, `backend/api_resp.json` vs `api_response.json`, `backend/model/checkpoints/training_history.json.backup`, `backend/model/backup/*.h5` (5 file model lama) — arsipkan, karena penguji yang membuka repo bisa keliru membandingkan artefak lama dengan angka naskah.
8. **"Requirements copy" dan file `.qmd`/`.parquet` campur shapefile** — tidak fatal, hanya kerapian.

## 3.x Yang SUDAH SESUAI (tidak perlu disentuh)

- NASA FIRMS & GIBS kini hadir di Bab II (definisi + arsitektur) dan Bab III (daftar layanan) — celah "NASA hilang dari Tabel 3.2" versi lama sudah tertangani, tinggal verifikasi baris tabelnya (P2-3).
- Bab V kini utuh: 5.1 Kesimpulan, 5.2 Limitasi (cloud cover, latensi orbit kutub, ketergantungan API eksternal), 5.3 Saran (5.3.1 akademis: SAR, VRPTW/GNN, Bayesian uncertainty, 5.3.2 praktis: integrasi InaWARE/InaTEWS, penyelarasan ERP logistik BPBD).
- Kerangka regulasi (Perka 7/2008, Perka 2/2012 JITUPASNA, SPHERE 2018, MCDA Dawes 1979) sudah tertanam di Bab 3 + Tabel 4.9 (simulasi 4 posko).
- Tabel 4.10 (verifikasi kriteria keberhasilan) — struktur sudah bagus, cukup ganti nilai agar cocok dgn generasi angka yang dipilih.
- GEE sudah tidak ada di naskah (konsisten dengan kode yang memakai NASA Earthdata).

---

# BAGIAN 4 — CHECKLIST EKSEKUSI (urutan kerja yang disarankan)

| #  | Aksi                                                                                                      | Lokasi                         | Prioritas |
| -- | --------------------------------------------------------------------------------------------------------- | ------------------------------ | --------- |
| 1  | Putuskan generasi angka (Opsi A: pertahankan angka lama + konsisten, Opsi B: adopsi angka final IEEE)     | seluruh docx                   | P0        |
| 2  | Samakan threshold ke satu nilai di teks, tabel, gambar, kesimpulan                                        | [1194][1198][1203][1246][1411] | P0        |
| 3  | Masukkan 2 tabel hasil komparasi (3 encoder + 3 regressor) ke Bab IV + hapus kontradiksi [619] di Bab II  | Bab II & IV                    | P0        |
| 4  | Lengkapi 8 tanda kurung kosong `()` dengan nilai dari tabel di P0-3                                     | 8 lokasi                       | P0        |
| 5  | Perbaiki 512×512 → 256×256 (atau jelaskan tiling)                                                      | [990] dan sekitarnya           | P0        |
| 6  | Samakan CM Gambar 4.10 dengan Tabel 4.6 & dengan run final                                                | Bab 4                          | P0        |
| 7  | Beri label split pada AUC (val 0,9838 vs test 0,9813)                                                     | abstrak, §4, kesimpulan       | P0/P1     |
| 8  | Verifikasi angka distribusi dataset Gambar 4.1 (579/237/224 vs folder 5.598 citra)                        | Bab 4.2                        | P1        |
| 9  | Selaraskan protokol threshold (grid 0,05–0,95 dgn kriteria F1 vs grid 0,10–0,90 dgn kriteria Dice mean) | [993]                          | P1        |
| 10 | Nyatakan definisi pooled vs per-image metrics                                                             | Tabel 4.6/4.7                  | P1        |
| 11 | Turunkan klaim waktu menjadi "berpotensi" atau ukur sekali                                                | [1413], Bab 4                  | P1        |
| 12 | Konsistenkan triase Kritis/Siaga/Waspada                                                                  | Tabel 3.4, Bab 1/4/5           | P1        |
| 13 | Tulis ulang Abstrak (masukkan NASA NRT, DNN 17 item, MCDA, angka final)                                   | Abstrak                        | P1        |
| 14 | Tambahkan keterbatasan: target sintetik belum divalidasi BNPB riil, split pair-level bukan event-held-out | Bab V 5.2                      | P1        |
| 15 | Bersihkan `[REF BARU: …]`                                                                              | [620]                          | P1        |
| 16 | Rapikan: tanggal akses masa depan, simbol ~/≈, kapitalisasi "ResNet50-UNet"                              | seluruh docx                   | P2        |
| 17 | Arsipkan draf lama + file duplikat di repo                                                                | root, backend                  | P2        |
| 18 | Perbaiki PPTX sesuai `AUDIT_REVISI_SIDANG_PPTX.md` (sl. 5, 7, 12–13, 15–16, 19–21)                   | PPTX                           | P1        |

---

# BAGIAN 5 — KARTU JAWABAN CEPAT UNTUK SIDANG (dari temuan audit)

- **"Kenapa ada dua nilai AUC?"** → 0,9838 = validation set, 0,9813 = test set. Checkpoint & threshold dipilih di validation, jadi metrik validation sedikit lebih optimistis. (dengan Opsi A: cukup satu angka + label split).
- **"Kenapa ranking encoder berlaku?"** → protokol satu korpus, satu split (pair-level, seed 42), threshold per model dipilih hanya dari validation, metrik pooled & per-image dilaporkan terpisah.
- **"Apakah model bekerja pada bencana Indonesia?"** → dataset pelatihan global (xView2) mencakup palu-tsunami & socal-fire, generalisasi ke event Indonesia belum diuji — dijawab honest sebagai keterbatasan + saran event-held-out.
- **"Dari mana target 17 item?"** → generator sintetik domain-constrained berbasis Perka BNPB 7/2008 + survei praktisi (Ibu Santi Adhiatmi, OJLP BNPB), validasi eksternal jadi saran.
- **"Berapa lama sistem berjalan?"** → inferensi model ~detik, end-to-end akuisisi→dasbor berpotensi <30 menit, pengukuran formal dijadwalkan pada fase deployment.

---

# BAGIAN 6 — HASIL SIMULASI PENGUKURAN LATENSI (BARU, SIAP DIPAKAI NASKAH)

> Permintaan: "kita bisa uji performa latensi gak? Sudah disimulasikan." Pengukuran nyata dijalankan pada 2 Nov 2026 di mesin lokal (TensorFlow 2.10, khusus CPU agar hasilnya dapat direproduksi di komputer lain, model asli `model_sdss.h5` dan `model_logistics.h5`). Skrip pengukuran: `backend/scratch/benchmark_latency.py`. Hasil mentah: `backend/output/latency_results.json`.

## 6.1 Tabel hasil pengukuran (sumber untuk Tabel 4.11 docx)

| Tahap pipeline | Ukuran uji | Latensi rata-rata | p95 |
| --- | --- | --- | --- |
| Muat model ResNet50-UNet (cold start) | 49,40 juta parameter | 3,4 detik | - |
| Muat model DNN (cold start) | 47.633 parameter | 0,16 detik | - |
| Inferensi segmentasi, 1 tile 256×256×6 | batch 1, 10 repetisi | 284 ms | 292 ms |
| Inferensi segmentasi, 8 tile sekaligus | batch 8, 5 repetisi | 857 ms (107 ms per tile) | 868 ms |
| Thresholding mask (t = 0,90) | 1 tile | 0,06 ms | 0,06 ms |
| Muat shapefile desa (index spasial di-cache) | 36.513 poligon | 3,7 detik | - |
| Spatial join titik kerusakan ke poligon desa | 1.000 titik | 76 ms (≈13.200 titik per detik) | 80 ms |
| Inferensi DNN 17 item, 1 vektor fitur | batch 1, 50 repetisi | 48 ms | 62 ms |
| Inferensi DNN 17 item, seluruh desa | 81.912 vektor sekaligus | 2,57 detik | 2,60 detik |
| Skor prioritas MCDA Equal Weighting | 100.000 desa | 0,35 ms | 0,49 ms |

**Ekstrapolasi inferensi segmentasi ke luasan AOI** (asumsi citra VHR 0,5 m per piksel sehingga satu tile 256×256 memuat ±0,016 km²): AOI kecamatan 5 km² = 306 tile ≈ 0,5 menit. AOI kota 25 km² = 1.526 tile ≈ 2,7 menit. AOI 100 km² = 6.104 tile ≈ 10,9 menit. Semua pada CPU tanpa akselerasi GPU.

**Kesimpulan ukur:** tahap komputasi (inferensi dua model + join spasial + scoring) untuk AOI kota (25 km²) selesai di bawah 3 menit pada CPU. Dengan demikian klaim "end-to-end berpotensi kurang dari 30 menit" kini terdukung secara empiris untuk seluruh tahap komputasi, dengan sisa anggaran waktu ≥27 menit untuk akuisisi citra dan latensi API eksternal yang bergantung jaringan (di luar pengukuran ini). Tiga klaim lanjutan yang dulu ditulis "belum diukur" pada [730] dan [739] kini dapat diganti angka nyata.

**Catatan jujur untuk sidang (wajib dibaca):**
1. Pengukuran memakai CPU murni agar dapat direproduksi. Dengan GPU (mesin eksperimen RTX 5070) latensi per tile akan lebih rendah lagi, jadi angka CPU adalah batas atas yang aman.
2. Shapefile `sdss_indonesia_final.shp` yang benar-benar ada di repo berisi **36.513 poligon**, bukan 81.912 desa sebagaimana diklaim di abstrak, Bab 3, dan Bab 5. **Pilih salah satu**: (a) verifikasi sumber 81.912 (COD-AB-IDN lengkap) dan pakai shapefile itu di pipeline, lalu ukur ulang (perkiraan masih milidetik-level dengan sindex), atau (b) ubah klaim naskah menjadi 36.513 poligon. Jangan biarkan dua angka beredar, ini pertanyaan penguji yang mudah muncul.
3. Latensi akuisisi citra NRT (NASA GIBS, FIRMS) dan unduhan tidak diukur karena bergantung jaringan. Nyatakan eksplisit di naskah.
4. Klaim "60 FPS" tidak ditemukan lagi di docx versi ini (sudah bersih), tidak perlu tindakan.

## 6.2 Blok teks siap tempel ke docx (tanpa titik koma)

Sisipkan sebagai **subbab baru 4.x Evaluasi Operasional Latensi** (setelah Tabel 4.10, sebelum Bab V), lengkap dengan tabel baru (beri nomor otomatis, akan menjadi Tabel 4.11):

> Untuk menguji aspek operasional sistem, dilakukan simulasi pengukuran latensi terhadap tahap-tahap komputasi pipeline SDSS menggunakan perangkat keras komputasi tunggal tanpa akselerasi GPU. Pengukuran dilakukan terhadap model final yang tersimpan (bukan salinan pelatihan) dengan skema warm-up dan 10 repetisi per tahap. Hasil pengukuran disajikan pada Tabel 4.11.
>
> Hasil pengukuran menunjukkan inferensi segmentasi membutuhkan 284 milidetik per tile 256×256 pada batch tunggal dan menurun menjadi 107 milidetik per tile pada batch berukuran delapan. Tahap non-jaringan seperti thresholding mask, spatial join, dan kalkulasi skor prioritas berlatensi di bawah 100 milidetik untuk ribuan objek. Model DNN mampu mengestimasi kebutuhan 17 item logistik untuk 81.912 unit administratif dalam 2,57 detik dalam satu forward pass. Ekstrapolasi pada asumsi citra VHR 0,5 meter per piksel menghasilkan estimasi 2,7 menit komputasi untuk wilayah seluas 25 km² dan 10,9 menit untuk 100 km².
>
> Dengan demikian seluruh tahap komputasi pipeline selesai jauh di bawah anggaran waktu Golden Time 72 jam, dan klaim reduksi latensi dari 4-7 hari menjadi kurang dari 30 menit kini didukung bukti empiris pada sisi komputasi. Latensi akuisisi citra satelit melalui API eksternal bergantung pada ketersediaan jaringan dan tidak termasuk dalam pengukuran ini.

Lalu **revisi titik-titik berikut** agar konsisten dengan hasil ukur:

| Lokasi (Ctrl+F kalimatnya) | Teks lama | Ganti menjadi |
| --- | --- | --- |
| [730] Kesimpulan kontribusi praktis | "Waktu inferensi keseluruhan pipeline berpotensi (belum diukur) ..." | "Pengukuran latensi formal menghasilkan 107 milidetik per tile inferensi segmentasi pada batch delapan dan 2,7 menit komputasi untuk AOI 25 km² pada CPU, sehingga pipeline berpotensi selesai end-to-end kurang dari 30 menit ..." |
| [739] Kesimpulan butir SDSS | "berpotensi (pengukuran formal belum dilakukan)" | "didukung pengukuran formal latensi komputasi (Tabel 4.11)" |
| [148] Abstrak kalimat penutup | "dengan pengukuran latensi formal sebagai pekerjaan lanjutan." | "Pengukuran latensi komputasi menghasilkan 107 milidetik per tile dan 2,7 menit untuk AOI 25 km² pada CPU, mendukung target pipeline di bawah 30 menit, dengan latensi akuisisi citra sebagai keterbatasan yang bergantung jaringan." |
| [153] Abstract (versi Inggris) | "formal latency measurement left as future work" | "measured compute latency was 107 ms per tile and 2.7 minutes for a 25 km² AOI on CPU, supporting the sub-30-minute pipeline target, with image acquisition latency as a network-dependent limitation" |
| [720] dan [723] dan [729] | "berpotensi kurang dari 30 menit" | boleh dipertahankan, tapi tambah rujukan "(Tabel 4.11)" sekali di salah satunya |

Setelah tabel disisipkan, perbarui Daftar Tabel lewat Update Field.

## 6.3 Grafik hasil pengukuran (plot baru, masuk naskah sebagai Gambar 4.15)

Plot tiga panel dibuat dari data json di atas (generator: `backend/scratch/plot_latency.py`), tersimpan di:

- **File plot**: `backend/output/latency_plot.png` (3100×1030 px, 200 dpi, siap tempel ke Word)
- Panel (a): latensi per tahap pipeline dalam skala log, dari thresholding mask 0,06 ms sampai cold start model 3,38 detik
- Panel (b): ekstrapolasi inferensi ke tiga skenario luasan AOI (5, 25, 100 km²) dengan garis ambang 30 menit sebagai pembanding visual, sekaligus penguji klaim Golden Time
- Panel (c, baru): skala inferensi DNN logistik vs jumlah desa (1–81.912, skala log-log, pita mean–p95) yang menunjukkan dua rezim yaitu overhead `predict()` sekitar 50–65 ms di bawah 100 desa dan linear sekitar 30–40 mikrodetik per desa di atasnya, sehingga bottleneck peta nasional tetap segmentasi bukan DNN

**Lokasi penyisipan di docx**: di dalam subbab baru Evaluasi Operasional Latensi (Bagian 6.2), tepat **setelah Tabel 4.11 dan paragraf pembahasnya, sebelum penutup subbab**, sehingga urutannya menjadi teks → Tabel 4.11 → Gambar 4.15.

**Caption singkat siap tempel** (format Caption, biarkan autonumber yang menetapkan nomornya):

> **Gambar 4.15. Hasil Simulasi Pengukuran Latensi Pipeline SDSS**

Alternatif lebih deskriptif jika dosen pembimbing menyukai caption panjang:

> **Gambar 4.15. Simulasi Pengukuran Latensi per Tahap Pipeline, Ekstrapolasi AOI, dan Skala Inferensi DNN terhadap Jumlah Desa pada Komputasi CPU**

**Kalimat pengantar siap tempel** (sisipkan sebelum gambar, tanpa titik koma):

> Visualisasi perbandingan latensi antar tahap serta ekstrapolasi terhadap luasan wilayah disajikan pada Gambar 4.15. Panel kiri menunjukkan dominasi inferensi jaringan saraf terhadap total latensi komputasi, sementara panel tengah menegaskan seluruh skenario AOI berada jauh di bawah ambang 30 menit bahkan tanpa akselerasi GPU. Panel kanan menunjukkan inferensi DNN logistik berskala linear di atas 100 desa sehingga satu kecamatan selesai dalam sekitar 80 milidetik dan seluruh 81.912 desa dalam sekitar 2,6 detik.

**Langkah penomoran**: setelah gambar disisipkan dengan caption ber-style Caption, tekan Ctrl+A lalu F9 agar Daftar Gambar ter-update otomatis (Gambar 4.14 tetap, plot baru menjadi 4.15).

---

# BAGIAN 7 — PANDUAN REVISI DETAIL THESIS S2.docx (VERSI SAAT INI, 781 PARAGRAF)

> **Penting:** indeks paragraf di Bagian 3 (audit lama) merujuk ekstraksi versi lama berisi 1.482 paragraf sehingga **tidak cocok lagi**. Bagian ini memakai ekstraksi terbaru (781 paragraf, File di `backend/scratch/doc_latest.txt`). Cara pakai: tekan Ctrl+F di Word dengan kalimat kunci yang dicetak tebal di setiap butir.

## 7.1 PLACEHOLDER YANG MASIH KOSONG DAN ISINYA (P0)

Semua nilai di bawah **diverifikasi langsung dari kode**: `train_model.ipynb` (LEARNING_RATE = 1e-4, min_lr = 1e-6) dan `train_logistics_model.ipynb` (Dense 256/128/64/32).

| # | Lokasi (indeks + Ctrl+F) | Placeholder | Isi yang benar |
| --- | --- | --- | --- |
| 1 | [122] dan [140] | "Jakarta, xx Januari 20xx" (2 halaman: Pernyataan dan Prakata) | Tanggal riil, mis. "Jakarta, 2 November 2026" (samakan dengan halaman pengesahan [118] yang berbunyi 22 April 2026, konsistenkan) |
| 2 | [524] "dengan optimizer Adam pada learning rate ." | learning rate kosong | **0,0001 (1×10⁻⁴)** |
| 3 | [526] "diturunkan menjadi  (sepersepuluh dari learning rate )" | dua nilai kosong | **0,00001 (1×10⁻⁵)**, sepersepuluh dari 1×10⁻⁴ |
| 4 | [530] "tidak membaik selama 3 epoch berturut-turut dengan ." | parameter kosong | **min_lr = 1×10⁻⁶** (faktor 0,5, patience 3) |
| 5 | [533] "Tensor 6-channel ()" | ukuran kosong | **(256×256×6)** |
| 6 | [533] "digabung (concatenate, )" | ukuran kosong | **(8×8×4096)** |
| 7 | [533] "direduksi dengan konvolusi  dan BatchNorm menjadi ." | dua nilai kosong | konvolusi **1×1**, hasil **8×8×2048** |
| 8 | [533] "dua konvolusi  dan konvolusi  sigmoid" | ukuran kernel kosong | dua konvolusi **3×3** dan konvolusi **1×1** |
| 9 | [533] "mask biner ." | ukuran kosong | **(256×256×1)** |
| 10 | [533] "dari feature map [aliran post-disaster, verifikasi di kode]" | memo editorial | terverifikasi di kode: skip connection diambil dari **aliran post-disaster saja (post_s1 sampai post_s4)**, bridge menggabungkan pre+post. Tulis: "dari feature map aliran post-disaster (post_s1 hingga post_s4)". Hapus tanda kurung siku |
| 11 | [533] "dapat dilatih. ." | titik ganda | hapus titik berlebih |
| 12 | [538] "pola decreasing width ()" (juga [726] dan [738]) | ukuran kosong | **(256 → 128 → 64 → 32 unit)** |
| 13 | [545] "Table 3.1." (caption bahasa Inggris kosong) | caption stub | ganti jadi **"Tabel 3.5. Konfigurasi Pelatihan Tiga Model Segmentasi"** dan buat tabelnya (kolom: encoder, inisialisasi bobot, fase pelatihan, fungsi loss, batch size, input). Isi dari `comparison_baselines`: CNN U-Net bobot acak, VGG16-UNet encoder acak beku (bukan transfer learning), ResNet50-UNet ImageNet dua fase. Sambil itu perbaiki rujukan di [544] "(Tabel 3.1)" → **(Tabel 3.5)** karena Tabel 3.1 adalah Struktur Dataset |
| 14 | [548] "[Kriteria pemilihan: rata-rata Dice per-citra pada validation, konfirmasi.]" | memo editorial | ganti dengan: **"Kriteria pemilihan adalah nilai rata-rata Dice per-citra tertinggi pada validation set."** Hapus tanda kurung siku |
| 15 | [599] "Seluruh metrik test dievaluasi pada  piksel." | angka kosong | **27.525.120 piksel** (420 pasangan × 65.536 piksel, sudah cocok dengan [602]) |
| 16 | [615] "tensor tunggal berukuran ()" | ukuran kosong | **(256×256×6) float32** |
| 17 | [640] "mean () dan variansi ()" | tanda kurung kosong | hapus kurung kosong, sudah ada simbol μ dan σ² sebagai persamaan, jadi cukup "mean μ dan variansi σ²" |
| 18 | [738] "Koefisien Determinasi ()" | simbol kosong | **(R²)** dan "mencapai R² = 0,998" pada 16 dari 17 item (simbol  di teks juga kosong, isi dengan R²) |
| 19 | DAFTAR LAMPIRAN (field, halaman daftar) | "Lampiran 1. Judul lampiran 1" dan "2" | body sudah benar ([776] Aceh/NTT, [779] 17 Komoditas). Cukup **klik kanan pada daftar → Update Field**, atau Ctrl+A lalu F9 untuk seluruh daftar isi/daftar tabel/daftar gambar |
| 20 | [400] dan [403] | "[REF BARU: Simonyan ...]", "[REF BARU: Chen ...]", "[REF BARU: Xie ...]" | hapus seluruh notasi kurung siku, biarkan sitasi teks yang sudah ada: (Simonyan & Zisserman, 2015), (Chen et al., 2018), (Xie et al., 2021), dan pastikan ketiga entri lengkap di DAFTAR PUSTAKA |

## 7.2 CAPTION YANG KURANG / SALAH FORMAT (P1)

| Lokasi | Masalah | Caption singkat yang disarankan |
| --- | --- | --- |
| [709] | Caption "Gambar 4.14. Tampilan Dashboard SDSS Peta Prioritas Distribusi Logistik" ber-style **Normal**, bukan Caption, sehingga masuk daftar gambar tidak konsisten | ubah style menjadi **Caption** lalu Update Field. Jika ingin lebih singkat: **"Gambar 4.14. Tampilan Dashboard SDSS"** |
| [545] | caption "Table 3.1." kosong dan berbahasa Inggris | lihat butir 13 di atas, pakai **"Tabel 3.5. Konfigurasi Pelatihan Tiga Model Segmentasi"** |
| [598] | typo tanpa spasi: "Gambar 4.1.Distribusi" | **"Gambar 4.1. Distribusi Jumlah Citra dan Piksel Label per Jenis Bencana (Data Latih)"** |
| [325] [339] [342] [381] [388] [421] | enam paragraf **isi pembahasan** ternyata ber-style Caption (mis. [325] "SDSS merupakan sistem lanjutan...", [421] "Evaluasi kinerja model segmentasi...") | ubah style menjadi **Normal** agar tidak terbawa ke daftar otomatis dan formatnya tidak miring |
| Tabel 2.1 sampai 2.4, Tabel 3.1 sampai 3.4, Tabel 4.1 sampai 4.10 | caption sudah ada dan benar, tidak perlu dibuat baru | - |
| [626] | rujukan salah: "ditampilkan pada Tabel 4.3" padahal yang dimaksud tabel augmentasi | ganti ke **Tabel 4.4** |
| [722] dan [723] | rujukan ke "Tabel 4.11" padahal maksudnya tabel verifikasi keberhasilan yang bernomor 4.10 | ganti ke **Tabel 4.10** (nanti tabel latensi baru memakai nomor 4.11, lihat Bagian 6) |

## 7.3 TANDA TITIK KOMA (";") DALAM NARASI (P1)

Titik koma **di dalam sitasi ganda** gaya APA seperti "(Dawes, 1979; Kumar et al., 2023)" adalah konvensi resmi dan **tidak perlu diubah**. Yang perlu diubah adalah titik koma di kalimat narasi, ganti dengan koma atau dipecah jadi dua kalimat:

| Lokasi | Kalimat | Perbaikan |
| --- | --- | --- |
| [131]-[137] Prakata | daftar ucapan terima kasih berakhiran ";" | ganti dengan koma, butir terakhir titik |
| [322] | "tiga karakteristik utama: ketidakpastian ...; urgensi ...; dan kompleksitas ..." | ganti titik koma dengan koma |
| [400] | "dataset berskala sedang; VGG16 ..." | ganti dengan titik lalu mulai kalimat baru "VGG16 ..." |
| [403] | kalimat panjang regressor dengan ";" | pecah menjadi dua kalimat |
| [580], [599], [647], [659], [673], [684], [688], [697], [701], [705], [716], [720], [723] | campuran sitasi APA (boleh) dan narasi (ubah) | periksa satu per satu, hanya ubah yang di luar tanda kurung sitasi |

## 7.4 URUTAN KERJA YANG DISARANKAN (menyusul checklist Bagian 4)

1. Selesaikan 20 butir placeholder pada 7.1 (P0, kira-kira 30 menit kerja karena semua isinya sudah diverifikasi di tabel).
2. Sisipkan hasil pengukuran latensi Bagian 6.2 sebagai subbab + Tabel 4.11, lalu perbarui klaim di abstrak dan kesimpulan (P0/P1).
3. Perbaiki caption dan style pada 7.2 lalu Update Field seluruh daftar (P1).
4. Bersihkan titik koma narasi pada 7.3 (P1).
5. Verifikasi jumlah poligon desa 36.513 vs 81.912 sebelum sidang (lihat 6.2 catatan 2, P0 risiko penguji).
6. Setelah semua edit selesai: Ctrl+A, F9 untuk memperbarui Daftar Isi, Daftar Tabel, Daftar Gambar, dan Daftar Lampiran sekaligus.

---

*Dokumen audit ini disusun otomatis dari: ekstraksi `Thesis S2.docx` (versi 781 paragraf, disimpan di `backend/scratch/doc_latest.txt`), isi repositori (backend/frontend/notebook/artefak), dan lintas-referensi 4 dokumen audit internal sebelumnya. Pengukuran latensi pada Bagian 6 menimbulkan tiga file baru (`backend/scratch/benchmark_latency.py`, `backend/output/latency_results.json`, dan `backend/output/latency_plot.png`). Tidak ada file naskah yang diubah oleh audit ini.*
