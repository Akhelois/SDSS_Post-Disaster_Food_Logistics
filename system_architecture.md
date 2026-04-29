# Arsitektur Sistem SDSS Logistik Bencana

## Diagram Alur Sistem Lengkap

```mermaid
flowchart TD
    subgraph DATA_SOURCE["📡 Sumber Data"]
        GEE["GEE\n(Google Earth Engine)"]
        DW["Google Dynamic World\n(Built Area Filter)"]
        S2["Sentinel-2 SR\n(Citra Satelit)"]
    end

    subgraph DOWNLOADER["⬇ GEE Downloader (gee_downloader.py)"]
        GRID["Generate Grid Indonesia\n(1.5° x 1.5°)"]
        NDVI["Deteksi Perubahan NDVI\n(Pre vs Post Disaster)"]
        FILTER["Filter Built Area\n(Dynamic World > 20%)"]
        DL["Download Citra PNG\n(256x256 RGB)"]
        LABEL["Generate Label JSON\n(Geotransform + Koordinat)"]
    end

    subgraph INPUT["📂 Data Input"]
        IMG["data/citra/input/\n*.png"]
        LBL["data/citra/labels/\n*.json"]
        DESA_SHP["data/batas_desa/\nIDN_Final_WGS84.shp"]
    end

    subgraph MODEL["🧠 Model (pipeline.py)"]
        RESNET["ResNet50-UNet\n(Pretrained ImageNet)"]
        PREDICT["Prediksi Damage Mask\n(Segmentasi Biner)"]
        M2P["Mask → Damage Points\n(Confidence ≥ 0.2)"]
        CL["Continual Learning\n(Fine-tune 3 epoch, LR=1e-5)"]
    end

    subgraph SPATIAL["🗺 Spatial Processing (main.py)"]
        SJOIN["Spatial Join\n(Titik → Batas Desa)"]
        ISLAND["Assign Island\n(16 Wilayah Indonesia)"]
        DISASTER["Assign Disaster Type\n(Per Pulau)"]
        POLYGON["Desa → Polygon\n(Simplify 0.002°)"]
    end

    subgraph LOGISTICS["📦 Estimasi Logistik"]
        CALC["Hitung per Desa:\nKerusakan × Standar BNPB"]
        BERAS["Beras: 10 kg/KK"]
        AIR["Air: 50 L/KK"]
        MIE["Mie: 2 dus/KK"]
        LAUK["Lauk: 4 pkt/KK"]
    end

    subgraph API["🔌 FastAPI Backend (main.py)"]
        ENDPOINT["GET /\n(JSON Response)"]
    end

    subgraph FRONTEND["💻 Frontend Dashboard (React + Deck.gl)"]
        MAP["Peta Satelit\n(MapLibre + ArcGIS Tiles)"]
        POLY_LAYER["PolygonLayer\n(Zona Kerusakan per Desa)"]
        SIDEBAR["Sidebar\n(Daftar Area Terdampak)"]
        TOOLTIP["Tooltip Hover\n(Info Lengkap + Logistik)"]
        FLYTO["FlyTo Animation\n(Klik → Zoom ke Desa)"]
        METRICS["Metric Cards\n(Wilayah, Kerusakan, Terdampak)"]
    end

    subgraph SCHEDULER["⏱ Scheduler (scheduler.py)"]
        CRON["Loop setiap 2 jam"]
    end

    %% Flow connections
    GEE --> S2
    GEE --> DW
    S2 --> GRID
    DW --> FILTER
    GRID --> NDVI
    NDVI -->|"Change > 0.03"| FILTER
    FILTER --> DL
    DL --> IMG
    DL --> LABEL
    LABEL --> LBL

    IMG --> RESNET
    LBL --> M2P
    RESNET --> PREDICT
    PREDICT --> M2P
    M2P -->|"sdss_result.geojson"| SJOIN
    PREDICT --> CL
    CL -->|"Update model_sdss.h5"| RESNET

    DESA_SHP --> SJOIN
    SJOIN --> ISLAND
    ISLAND --> DISASTER
    SJOIN --> POLYGON

    DISASTER --> CALC
    POLYGON --> ENDPOINT
    CALC --> ENDPOINT

    CALC --> BERAS
    CALC --> AIR
    CALC --> MIE
    CALC --> LAUK

    ENDPOINT -->|"HTTP JSON"| MAP
    ENDPOINT --> SIDEBAR
    ENDPOINT --> METRICS
    MAP --> POLY_LAYER
    POLY_LAYER --> TOOLTIP
    SIDEBAR --> FLYTO
    FLYTO --> MAP

    CRON -->|"Trigger"| GRID
    CRON -->|"Trigger"| RESNET

    style DATA_SOURCE fill:#1e3a5f,stroke:#3b82f6,color:#e2e8f0
    style DOWNLOADER fill:#1a2e1a,stroke:#22c55e,color:#e2e8f0
    style INPUT fill:#2d1f3d,stroke:#a855f7,color:#e2e8f0
    style MODEL fill:#3d1f1f,stroke:#ef4444,color:#e2e8f0
    style SPATIAL fill:#1f2d3d,stroke:#38bdf8,color:#e2e8f0
    style LOGISTICS fill:#3d2d1f,stroke:#f97316,color:#e2e8f0
    style API fill:#1f3d1f,stroke:#4ade80,color:#e2e8f0
    style FRONTEND fill:#1f1f3d,stroke:#818cf8,color:#e2e8f0
    style SCHEDULER fill:#3d3d1f,stroke:#facc15,color:#e2e8f0
```

## Mapping File ↔ Komponen

| Komponen | File | Fungsi Utama |
|----------|------|-------------|
| **GEE Downloader** | `gee_downloader.py` | Scan grid Indonesia, deteksi perubahan NDVI, download citra Sentinel-2 |
| **Scheduler** | `scheduler.py` | Loop setiap 2 jam: GEE scan → Pipeline deteksi |
| **Pipeline Model** | `pipeline.py` | Load ResNet50-UNet, prediksi mask, extract damage points, continual learning |
| **Backend API** | `main.py` | Spatial join ke desa, assign disaster type, estimasi logistik, serve JSON |
| **Services** | `services.py` | Utility: haversine, snap_to_road, load geodata, island assignment |
| **Frontend App** | `App.jsx` | Layout utama: Map + Sidebar, fetch data, build PolygonLayer |
| **Map Component** | `DeckMap.jsx` | Deck.gl + MapLibre, satellite tiles, tooltip |
| **Sidebar Header** | `SidebarHeader.jsx` | Judul + badge jenis bencana |
| **Metric Cards** | `MetricCards.jsx` | Wilayah aktif, titik kerusakan, est. terdampak |
| **Logistics Table** | `LogisticsTable.jsx` | Daftar desa terdampak + estimasi logistik pangan |

## Alur Data End-to-End

```
GEE Sentinel-2 → PNG 256x256 → ResNet50-UNet → Damage Mask → Points + Confidence
    → Spatial Join (Batas Desa) → Per-Desa Aggregation
        → Polygon Boundaries (dari Shapefile)
        → Disaster Type (dari mapping pulau)
        → Logistik Pangan (Kerusakan × Standar BNPB)
            → FastAPI JSON → React Dashboard
                → Peta (PolygonLayer + Tooltip)
                → Sidebar (Daftar + FlyTo)
                → Metrics (Ringkasan)
```
