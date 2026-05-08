from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
import numpy as np
import services
from shapely.geometry import Point, box
import geopandas as gpd
import os
import threading

app = FastAPI(title="SDSS Logistik Bencana API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Jenis Bencana: Fallback per Pulau (jika tidak ada data event BMKG) ===
DISASTER_BY_ISLAND = {
    'sumatera': 'Gempa Bumi',
    'jawa': 'Gempa Bumi',
    'kalimantan': 'Banjir',
    'sulawesi': 'Gempa Bumi',
    'nusa_tenggara': 'Gempa Bumi',
    'maluku': 'Gempa Bumi',
    'papua': 'Banjir',
    'bali': 'Gempa Bumi',
    'lombok': 'Gempa Bumi',
    'nias': 'Tsunami',
    'simeulue': 'Tsunami',
    'mentawai': 'Tsunami',
    'bangka': 'Banjir',
    'belitung': 'Banjir',
    'madura': 'Banjir Rob',
    'batu': 'Gempa Bumi',
    'other': 'Bencana Alam',
}

def get_current_disaster_type(island_fallback='other', lat=None, lon=None):
    """
    Ambil jenis bencana. Logika:
    1. Jika ada event BMKG terbaru DAN titik kerusakan dekat dengan event → pakai tipe event
    2. Jika tidak → fallback ke mapping per pulau
    """
    import json
    flag_path = "output/new_event.flag"
    try:
        if os.path.exists(flag_path) and lat is not None and lon is not None:
            with open(flag_path) as f:
                event = json.load(f)
            event_data = event.get("event", {})
            event_type = event_data.get("type", "")
            event_lat = event_data.get("lat")
            event_lon = event_data.get("lon")
            # Cek apakah titik kerusakan dekat dengan lokasi event (< 2 derajat ≈ 220km)
            if event_type and event_lat is not None and event_lon is not None:
                dist = ((lat - event_lat)**2 + (lon - event_lon)**2)**0.5
                if dist < 2.0:
                    return event_type
    except Exception:
        pass
    return DISASTER_BY_ISLAND.get(island_fallback, 'Bencana Alam')

def desa_to_polygon(geom, simplify_tol=0.002):
    """Convert desa geometry to simplified polygon coordinates for frontend."""
    try:
        simplified = geom.simplify(simplify_tol)
        if simplified.is_empty:
            return None
        if simplified.geom_type == 'MultiPolygon':
            largest = max(simplified.geoms, key=lambda p: p.area)
            return [[round(c[0], 6), round(c[1], 6)] for c in largest.exterior.coords]
        elif simplified.geom_type == 'Polygon':
            return [[round(c[0], 6), round(c[1], 6)] for c in simplified.exterior.coords]
    except Exception:
        pass
    return None

print("Loading geodata boundaries...")
gdf_desa = services.load_desa_boundaries()
if gdf_desa is not None and not gdf_desa.empty:
    print(f"  Shapefile loaded: {len(gdf_desa)} desa polygons")
else:
    print("  ⚠ Shapefile batas desa TIDAK DITEMUKAN — menggunakan fallback mode")

@app.get("/")
def get_dashboard_data():
    df_raw = services.load_geodata(services.OUTPUT_GEOJSON)
    if df_raw is None or df_raw.empty:
        return {"error": "standby"}

    # Filter: hanya titik dari satelit yang harus di dalam desa
    # Titik dari BMKG (sumber event) tidak di-filter karena koordinat episenter bisa di laut
    if gdf_desa is not None and not gdf_desa.empty:
        # Pisahkan data BMKG dan data satelit
        is_bmkg = df_raw.get('source', pd.Series(dtype=str)).fillna('') == 'BMKG'
        df_bmkg = df_raw[is_bmkg].copy()
        df_satelit = df_raw[~is_bmkg].copy()

        # Filter hanya data satelit yang di dalam polygon desa
        if not df_satelit.empty:
            gdf_points = gpd.GeoDataFrame(
                df_satelit,
                geometry=[Point(lon, lat) for lon, lat in zip(df_satelit['lon'], df_satelit['lat'])],
                crs="EPSG:4326"
            )
            joined = gpd.sjoin(gdf_points, gdf_desa[['geometry']], how='inner', predicate='within')
            df_satelit = df_satelit.loc[df_satelit.index.isin(joined.index.unique())].copy()

        # Gabungkan kembali
        df_raw = pd.concat([df_bmkg, df_satelit], ignore_index=True)

    if df_raw.empty:
        return {"error": "no_land_points"}

    conf_thresh = 0.2
    df_raw = df_raw[df_raw['confidence'] >= conf_thresh].copy()
    if df_raw.empty:
        return {"error": "no_confident_points"}

    # Spatial join: temukan desa untuk setiap titik kerusakan
    desa_col = None
    if gdf_desa is not None and not gdf_desa.empty:
        adm_cols = [c for c in gdf_desa.columns if c.startswith('ADM')]
        if adm_cols:
            gdf_points_proj = gpd.GeoDataFrame(
                df_raw,
                geometry=[Point(lon, lat) for lon, lat in zip(df_raw['lon'], df_raw['lat'])],
                crs="EPSG:4326"
            ).to_crs(epsg=3857)
            gdf_desa_proj = gdf_desa[adm_cols + ['geometry']].to_crs(epsg=3857)
            joined = gpd.sjoin_nearest(gdf_points_proj, gdf_desa_proj, how='left', max_distance=55000)
            joined = joined[~joined.index.duplicated(keep='first')]
            if 'index_right' in joined.columns:
                df_raw['_desa_idx'] = joined['index_right'].values
            for col in adm_cols:
                if col in joined.columns:
                    df_raw[col] = joined[col].values
            desa_col = next(
                (c for c in ['ADM4_EN', 'ADM3_EN', 'ADM2_EN']
                 if c in df_raw.columns and df_raw[c].notna().any()),
                None
            )

    if not desa_col:
        # Gunakan kolom 'wilayah' dari BMKG jika ada
        if 'wilayah' in df_raw.columns and df_raw['wilayah'].notna().any():
            desa_col = 'wilayah'
        else:
            df_raw['_desa'] = 'Tidak Diketahui'
            desa_col = '_desa'
    else:
        df_raw[desa_col] = df_raw[desa_col].fillna('Tidak Diketahui')

    df_raw['island'] = df_raw.apply(lambda r: services.assign_island(r['lat'], r['lon']), axis=1)

    # === Bangun zona kerusakan per desa (tanpa clustering/hub) ===
    rz_data = []
    if gdf_desa is not None and not gdf_desa.empty and '_desa_idx' in df_raw.columns:
        # === MODE NORMAL: Gunakan polygon dari shapefile ===
        desa_damage = df_raw.groupby('_desa_idx').agg(
            count=('lat', 'count'),
            desa=(desa_col, 'first'),
            island=('island', 'first'),
            avg_lon=('lon', 'mean'),
            avg_lat=('lat', 'mean'),
        ).reset_index()

        for _, row in desa_damage.iterrows():
            try:
                desa_idx = int(row['_desa_idx'])
                desa_geom = gdf_desa.geometry.iloc[desa_idx]
                polygon = desa_to_polygon(desa_geom)
                if polygon is None:
                    continue
                island = row['island']
                disaster_type = get_current_disaster_type(island, float(row['avg_lat']), float(row['avg_lon']))
                damage_count = int(row['count'])

                # Estimasi logistik pangan per desa berdasarkan jumlah kerusakan
                logistics = {
                    "beras": damage_count * services.LOGISTIK_PER_KK['Beras (kg)'],
                    "air": damage_count * services.LOGISTIK_PER_KK['Air Minum (liter)'],
                    "mie": damage_count * services.LOGISTIK_PER_KK['Mie Instan (Dus)'],
                    "minyak": damage_count * services.LOGISTIK_PER_KK['Minyak Goreng (liter)'],
                    "lauk": damage_count * services.LOGISTIK_PER_KK['Lauk Kaleng (paket)'],
                }

                rz_data.append({
                    "polygon": polygon,
                    "desa": str(row['desa']),
                    "count": damage_count,
                    "disaster_type": disaster_type,
                    "logistics": logistics,
                    "lon": float(desa_geom.centroid.x),
                    "lat": float(desa_geom.centroid.y),
                })
            except Exception:
                continue
    else:
        # === FALLBACK MODE: Shapefile tidak ada, bangun zona dari data geojson ===
        # Gunakan kolom ADM yang sudah tertanam di sdss_result.geojson
        print("  [Fallback] Membangun zona kerusakan tanpa shapefile...")
        desa_damage = df_raw.groupby(desa_col).agg(
            count=('lat', 'count'),
            island=('island', 'first'),
            avg_lon=('lon', 'mean'),
            avg_lat=('lat', 'mean'),
            min_lon=('lon', 'min'),
            max_lon=('lon', 'max'),
            min_lat=('lat', 'min'),
            max_lat=('lat', 'max'),
        ).reset_index()

        for _, row in desa_damage.iterrows():
            try:
                damage_count = int(row['count'])
                island = row['island']
                disaster_type = get_current_disaster_type(island, float(row['avg_lat']), float(row['avg_lon']))

                # Buat polygon bounding box dari titik-titik kerusakan per desa
                # Tambahkan padding kecil agar polygon tidak terlalu kecil
                pad = 0.005  # ~500m padding
                lon_min = row['min_lon'] - pad
                lon_max = row['max_lon'] + pad
                lat_min = row['min_lat'] - pad
                lat_max = row['max_lat'] + pad
                polygon = [
                    [round(lon_min, 6), round(lat_min, 6)],
                    [round(lon_max, 6), round(lat_min, 6)],
                    [round(lon_max, 6), round(lat_max, 6)],
                    [round(lon_min, 6), round(lat_max, 6)],
                    [round(lon_min, 6), round(lat_min, 6)],  # close ring
                ]

                logistics = {
                    "beras": damage_count * services.LOGISTIK_PER_KK['Beras (kg)'],
                    "air": damage_count * services.LOGISTIK_PER_KK['Air Minum (liter)'],
                    "mie": damage_count * services.LOGISTIK_PER_KK['Mie Instan (Dus)'],
                    "minyak": damage_count * services.LOGISTIK_PER_KK['Minyak Goreng (liter)'],
                    "lauk": damage_count * services.LOGISTIK_PER_KK['Lauk Kaleng (paket)'],
                }

                rz_data.append({
                    "polygon": polygon,
                    "desa": str(row[desa_col]),
                    "count": damage_count,
                    "disaster_type": disaster_type,
                    "logistics": logistics,
                    "lon": float(row['avg_lon']),
                    "lat": float(row['avg_lat']),
                })
            except Exception:
                continue
        print(f"  [Fallback] {len(rz_data)} zona berhasil dibangun")

    # Kumpulkan jenis bencana unik
    disaster_types = list(set(r['disaster_type'] for r in rz_data if 'disaster_type' in r))
    disaster_summary = ', '.join(sorted(disaster_types)) if disaster_types else 'Bencana Alam'

    # Hitung total logistik
    total_damage = int(len(df_raw))
    total_logistics = {
        "beras": total_damage * services.LOGISTIK_PER_KK['Beras (kg)'],
        "air": total_damage * services.LOGISTIK_PER_KK['Air Minum (liter)'],
        "mie": total_damage * services.LOGISTIK_PER_KK['Mie Instan (Dus)'],
        "minyak": total_damage * services.LOGISTIK_PER_KK['Minyak Goreng (liter)'],
        "lauk": total_damage * services.LOGISTIK_PER_KK['Lauk Kaleng (paket)'],
    }

    return {
        "disaster_info": {
            "types": disaster_types,
            "summary": disaster_summary,
        },
        "metrics": {
            "active_areas": int(df_raw[desa_col].nunique()),
            "total_damage": total_damage,
            "estimated_impacts": total_damage * 4,
        },
        "total_logistics": total_logistics,
        "map_data": {
            "red_zones": rz_data,
        }
    }


# === Endpoint: status scheduler ===
@app.get("/status")
def get_status():
    """Cek apakah scheduler sedang berjalan."""
    flag_path = "output/new_event.flag"
    last_event = None
    if os.path.exists(flag_path):
        try:
            import json
            with open(flag_path) as f:
                last_event = json.load(f)
        except Exception:
            pass
    return {
        "scheduler": "running",
        "last_event": last_event
    }


# === Background Scheduler ===
def start_scheduler_background():
    """Jalankan multi-hazard scheduler sebagai background thread."""
    try:
        from scheduler import check_all_sources, CHECK_INTERVAL_MINUTES
        import time
        from datetime import datetime

        def scheduler_loop():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Background scheduler started")
            print(f"  Interval: {CHECK_INTERVAL_MINUTES} menit")
            # Cek pertama saat startup
            check_all_sources()
            # Loop periodik
            while True:
                time.sleep(CHECK_INTERVAL_MINUTES * 60)
                check_all_sources()

        t = threading.Thread(target=scheduler_loop, daemon=True)
        t.start()
        print("✅ Multi-Hazard Scheduler aktif (background thread)")
    except Exception as e:
        print(f"⚠ Scheduler gagal start: {e}")
        print("  Backend tetap berjalan tanpa realtime monitoring")


@app.on_event("startup")
async def on_startup():
    """Jalankan scheduler saat FastAPI startup."""
    start_scheduler_background()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
