# Model Code & Architecture Documentation

Sistem SDSS (Spatial Decision Support System) untuk Logistik Pangan Pasca Bencana menggunakan kombinasi dari **Deep Learning Model (U-Net)** untuk mendeteksi kerusakan bangunan dari citra satelit dan sistem **Pipeline Filtering** untuk menggabungkan data dari BMKG.

Berikut adalah penjelasan detail mengenai kode model dan arsitektur pipeline yang berjalan di backend (`pipeline.py`).

## 1. Arsitektur Model: DualResNet50-UNet

Model utama yang digunakan untuk mendeteksi kerusakan dari citra satelit adalah **Siamese/Dual ResNet50-UNet**. Model ini bertugas membandingkan gambar suatu wilayah *sebelum* (pre-disaster) dan *sesudah* (post-disaster) bencana.

### a. Input (6-Channel)
Model menerima input berupa tensor dengan dimensi `(256, 256, 6)`.
- **Channel 0-2 (RGB):** Citra sebelum bencana (Pre-disaster).
- **Channel 3-5 (RGB):** Citra setelah bencana (Post-disaster).

### b. Shared Encoder (ResNet50)
Kedua citra (pre dan post) dilewatkan pada satu buah encoder **ResNet50** yang menggunakan bobot (weights) pre-trained dari *ImageNet*. 
- Karena model menggunakan beban berbagi (*shared weights*), model dapat memetakan fitur spasial dari kedua citra ke dalam representasi yang setara.
- Hasil dari *encoder* ini berupa serangkaian *skip connections* (`s1`, `s2`, `s3`, `s4`) dan representasi terdalam (`bridge`).

### c. Feature Fusion (Bridge)
Representasi terdalam dari citra sebelum bencana (`pre_bridge`) dan sesudah bencana (`post_bridge`) digabungkan (*concatenate*) di level bridge.
- Lapisan konvolusi (`Conv2D` dengan 2048 filter) dan `BatchNormalization` diterapkan untuk mempelajari perubahan/kerusakan yang membedakan kedua citra.

### d. Decoder (U-Net)
Fase *decoder* (U-Net) bertugas mengembalikan resolusi peta fitur menjadi gambar segmentasi utuh berukuran `(256, 256, 1)`.
- **Skip Connections:** Hanya fitur spasial resolusi tinggi dari cabang **post-disaster** (`post_s1` hingga `post_s4`) yang digunakan di fase ini. Hal ini memaksa model untuk memfokuskan pendeteksian pada kondisi pasca-bencana.
- Output akhir berupa probabilitas *sigmoid* antara 0 hingga 1. Jika nilai > threshold (misal `0.4`), piksel tersebut dianggap sebagai bangunan yang rusak.

---

## 2. Perbandingan: DualResNet50-UNet vs CNN Biasa

Mengapa sistem SDSS ini menggunakan **DualResNet50-UNet** alih-alih model Convolutional Neural Network (CNN) standar (seperti VGG16, Inception, atau ResNet standar)? Berikut adalah perbedaan utamanya:

| Aspek | CNN Biasa (Klasifikasi Gambar) | DualResNet50-UNet (Change Detection / Segmentasi) |
|---|---|---|
| **Output / Hasil** | Memberikan 1 label untuk seluruh gambar (misal: "Gambar ini mengandung kerusakan" atau "Tidak ada kerusakan"). | Menghasilkan **peta piksel (mask)** presisi tinggi. Memberitahu secara akurat *di koordinat mana* persisnya letak kerusakan berada. |
| **Input Data** | Biasanya hanya menerima 1 gambar pasca-bencana (3-channel RGB). | Menerima **2 gambar sekaligus** (6-channel: sebelum dan sesudah bencana) dan membandingkannya secara berdampingan. |
| **Konteks Perubahan** | Mudah tertipu. Bisa mengira lahan kosong alami atau puing bangunan lama sebagai "kerusakan bencana baru". | Sangat akurat. Karena melihat kondisi *sebelumnya*, model ini hanya bereaksi jika ada objek (bangunan) yang **berubah/hilang** setelah bencana (mendeteksi delta/perubahan). |
| **Tujuan Resolusi** | Dimensi fitur mengecil hingga menjadi satu set angka probabilitas (Flatten -> Dense layer). | Terdapat fase **Decoder (Upsampling)** yang mengembalikan peta fitur kembali ke resolusi spasial asli `256x256`. |

Secara singkat: CNN biasa cocok untuk mengenali gambar (kucing vs anjing), sedangkan **U-Net arsitektur Siamese** dirancang khusus untuk memetakan piksel demi piksel kerusakan infrastruktur bumi dengan akurasi tata ruang (geospasial) yang dibutuhkan untuk logistik bencana.

---

## 3. Threshold Analysis (Nilai Ambang Batas)

Berdasarkan *Threshold Optimization* di model, threshold deteksi piksel disetel secara matematis (dikonfigurasi di `pipeline.py`). 
Piksel yang dianggap sebagai kerusakan memiliki probabilitas klasifikasi minimum:
- **`conf_thresh = 0.2` (pada `main.py`):** Hanya prediksi titik koordinat yang probabilitasnya di atas 0.2 yang akan dipertimbangkan oleh sistem sebagai kerusakan (untuk menghindari noise deteksi).

---

## 4. Integrasi Pipeline (Data Ingestion)

Model inferensi tidak bekerja sendirian. Sistem memiliki `pipeline.py` dan `scheduler.py` yang bertugas menjalankan alur berikut:

1. **Pengambilan Citra:** Sistem GEE (Google Earth Engine) secara otomatis mendownload citra Sentinel-2 (optik) di atas wilayah Indonesia.
2. **Model Inference:** Gambar dilewatkan ke model `DualResNet50-UNet`. Peta segmentasi kerusakan (*damage mask*) dihasilkan.
3. **Ekstraksi Koordinat:** Kumpulan piksel rusak dikonversi kembali ke koordinat geografis (Longitude, Latitude) di atas peta bumi, dan diekspor ke dalam bentuk file `.geojson` (seperti `output/sdss_result.geojson`).

---

## 5. Penggabungan Data BMKG & Fallback Logic

Setelah titik-titik kerusakan satelit diekstrak, `main.py` melakukan logika filter tahap akhir:

> [!NOTE]
> Sistem memiliki multi-source intelligence: data Satelit (Visual) dan data peringatan dini (BMKG).

1. **Filtering Tanggal (*Freshness Rule*):**
   `services.py` akan mencoba membaca `scene_id` (seperti `idn_3s_129e_20260421` yang berarti 21 April 2026). Jika data satelit usianya lebih tua dari 5 hari, titik tersebut **dibuang** (dianggap bencana lampau/hantu).
   
2. **Spatial Join (Pemetaan ke Desa):**
   Titik kerusakan digabungkan dengan batas *shapefile* administrasi menggunakan Geopandas (`gpd.sjoin`). Jika suatu titik berada di tengah lautan atau di luar batas administrasi desa mana pun, maka titik tersebut diabaikan.
   
3. **Pengecualian BMKG (BMKG Bypass):**
   Khusus untuk data BMKG (yang merupakan laporan resmi dan *verified*), sistem tidak menerapkan aturan threshold densitas (`count < 2`). Jadi meskipun sistem hanya menerima 1 titik laporan BMKG, ia akan langsung dimunculkan di peta dan diberikan *building footprints* (dari Overpass API) atau heatmap radius.

---

## Kesimpulan

Sistem ini bersifat hibrida: AI/Deep Learning hanya bertugas mendeteksi perubahan fisik dari luar angkasa (sebagai sensor mentah). Hasil deteksi tersebut kemudian disaring oleh *business logic* di backend (`main.py` dan `services.py`) yang melakukan filter usia, *spatial check*, penggabungan data pemerintahan (BMKG), dan kalkulasi jumlah bantuan logistik per desa.
