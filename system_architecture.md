# Arsitektur Sistem SDSS Logistik Bencana

## Diagram Alur Sistem

```mermaid
flowchart TD
    BMKG["📡 BMKG API\n(Gempa + Cuaca Ekstrem)"] --> SCHEDULER["⏱ Scheduler\n(Cek tiap 2 menit)"]
    
    SCHEDULER -->|"Event terdeteksi"| GEOJSON["📄 sdss_result.geojson"]
    SCHEDULER -->|"Trigger scan"| GEE["🛰 GEE Downloader\n(Sentinel-2 + Dynamic World)"]
    
    GEE -->|"Citra permukiman"| MODEL["🧠 ResNet50-UNet\n(Prediksi Kerusakan)"]
    MODEL -->|"Damage points"| GEOJSON
    
    GEOJSON --> SPATIAL["🗺 Spatial Join\n(Titik → Batas Desa)"]
    SHP["📂 Shapefile\nBatas Desa"] --> SPATIAL
    
    SPATIAL --> LOGISTIK["📦 Estimasi Logistik\n(Standar BNPB)"]
    LOGISTIK --> API["🔌 FastAPI\nGET /"]
    API -->|"JSON"| FRONTEND["💻 React Dashboard\n(Deck.gl + MapLibre)"]

    style BMKG fill:#1e3a5f,stroke:#3b82f6,color:#e2e8f0
    style SCHEDULER fill:#3d3d1f,stroke:#facc15,color:#e2e8f0
    style GEE fill:#1a2e1a,stroke:#22c55e,color:#e2e8f0
    style MODEL fill:#3d1f1f,stroke:#ef4444,color:#e2e8f0
    style GEOJSON fill:#2d2d1f,stroke:#eab308,color:#e2e8f0
    style SHP fill:#2d1f3d,stroke:#a855f7,color:#e2e8f0
    style SPATIAL fill:#1f2d3d,stroke:#38bdf8,color:#e2e8f0
    style LOGISTIK fill:#3d2d1f,stroke:#f97316,color:#e2e8f0
    style API fill:#1f3d1f,stroke:#4ade80,color:#e2e8f0
    style FRONTEND fill:#1f1f3d,stroke:#818cf8,color:#e2e8f0
```

## Alur Data

```
python main.py
  ├── FastAPI Server (port 8000)
  └── Background Scheduler (tiap 2 menit)
        ├── BMKG Gempa API → Gempa M≥5.0
        └── BMKG Nowcast CAP → Banjir / Longsor / Hujan Lebat
              │
              ├── Langsung tulis ke sdss_result.geojson
              └── GEE Scan → Filter Permukiman → Model AI → APPEND ke geojson
                    │
                    └── Spatial Join → Estimasi Logistik → Dashboard
```

## Mapping File

| File | Fungsi |
|------|--------|
| `main.py` | Entry point: FastAPI + Scheduler background thread |
| `scheduler.py` | Monitor BMKG (Gempa + Cuaca), tulis event ke geojson, trigger GEE |
| `gee_downloader.py` | Download citra Sentinel-2, filter permukiman (Dynamic World > 30%) |
| `pipeline.py` | ResNet50-UNet prediksi kerusakan, continual learning |
| `services.py` | Utility: spatial join, island assignment, load geodata |
| `App.jsx` | Frontend: Peta + Sidebar + Metrics + News Panel |

## Jenis Bencana

| Sumber | Bencana | Trigger |
|--------|---------|---------|
| BMKG Gempa API | Gempa Bumi | M ≥ 5.0 |
| BMKG Nowcast CAP | Banjir, Hujan Lebat, Longsor, Angin Kencang | Severity Moderate+ |
