import sys
import os
import subprocess
import time
import json
from datetime import datetime

from config import (
    CHECK_INTERVAL_MINUTES, NEW_EVENT_FLAG, PROCESSED_EVENTS_FILE,
    OUTPUT_GEOJSON, BPS_DATA_FILE
)


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_processed_events():
    if os.path.exists(PROCESSED_EVENTS_FILE):
        try:
            with open(PROCESSED_EVENTS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_processed_events(events):
    try:
        with open(PROCESSED_EVENTS_FILE, "w") as f:
            json.dump(list(events), f)
    except Exception as e:
        print(f"[{now()}] Error saving events: {e}")


def run_pipeline():
    print(f"[{now()}] Menjalankan pipeline deteksi kerusakan & incremental learning...")
    r = subprocess.run([sys.executable, "-m", "pipeline.inference"], capture_output=False)
    if r.returncode != 0:
        print(f"[{now()}] Pipeline error (code {r.returncode})")
    else:
        print(f"[{now()}] Pipeline selesai dengan sukses")


def write_event_flag(event_info):
    try:
        with open(NEW_EVENT_FLAG, 'w') as f:
            json.dump({
                "timestamp": now(),
                "event": event_info
            }, f)
    except Exception:
        pass


def write_event_to_geojson(lat, lon, disaster_type, wilayah, severity="Moderate", event_id=""):
    import services
    from shapely.geometry import Point
    import geopandas as gpd
    from datetime import datetime, timedelta

    try:
        if os.path.exists(OUTPUT_GEOJSON) and os.path.getsize(OUTPUT_GEOJSON) > 10:
            with open(OUTPUT_GEOJSON, 'r') as f:
                geojson = json.load(f)
        else:
            geojson = {
                "type": "FeatureCollection",
                "name": "sdss_result",
                "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                "features": []
            }

        # === 72-hour TTL: buang fitur yang sudah lewat golden time ===
        cutoff = datetime.now() - timedelta(hours=72)
        fresh_features = []
        for feat in geojson.get("features", []):
            pa = feat.get("properties", {}).get("processed_at", "")
            try:
                feat_time = datetime.fromisoformat(pa.replace("Z", "+00:00")).replace(tzinfo=None)
                if feat_time >= cutoff:
                    fresh_features.append(feat)
            except Exception:
                fresh_features.append(feat)  # keep if unparseable
        geojson["features"] = fresh_features

        # === Deduplikasi spasial: skip jika sudah ada titik dalam radius ~5km ===
        DEDUP_THRESHOLD = 0.05  # ~5.5km
        for feat in geojson["features"]:
            coords = feat.get("geometry", {}).get("coordinates", [])
            if len(coords) >= 2:
                existing_lon, existing_lat = coords[0], coords[1]
                if abs(lat - existing_lat) < DEDUP_THRESHOLD and abs(lon - existing_lon) < DEDUP_THRESHOLD:
                    print(f"  -> Skip duplikat: ({lat:.4f}, {lon:.4f}) terlalu dekat dengan titik existing")
                    return

        conf_map = {"Extreme": 0.9, "Severe": 0.7, "Moderate": 0.5}
        confidence = conf_map.get(severity, 0.5)

        final_lon, final_lat = round(lon, 6), round(lat, 6)
        try:
            gdf_desa = services.load_desa_boundaries()
            if gdf_desa is not None:
                pt = Point(lon, lat)
                pt_gdf = gpd.GeoDataFrame(geometry=[pt], crs="EPSG:4326").to_crs(epsg=3857)
                desa_proj = gdf_desa.to_crs(epsg=3857)
                distances = desa_proj.geometry.distance(pt_gdf.geometry.iloc[0])
                nearest_idx = distances.idxmin()
                nearest_desa = gdf_desa.iloc[nearest_idx]

                centroid = nearest_desa.geometry.centroid

                snapped_lon, snapped_lat = services.snap_to_road(centroid.x, centroid.y, max_snap_m=5000)
                final_lon, final_lat = round(snapped_lon, 6), round(snapped_lat, 6)

                wilayah = f"{wilayah} (Desa {nearest_desa['ADM4_EN']})"
        except Exception as e:
            print(f"[{now()}] Gagal snap BMKG ke permukiman: {e}")

        feature = {
            "type": "Feature",
            "properties": {
                "confidence": confidence,
                "scene_id": event_id,
                "processed_at": datetime.now().isoformat(),
                "status": "active",
                "disaster_type": disaster_type,
                "wilayah": wilayah,
                "source": "BMKG"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [final_lon, final_lat]
            }
        }
        geojson["features"].append(feature)

        with open(OUTPUT_GEOJSON, 'w') as f:
            json.dump(geojson, f, indent=2)

        print(f"  -> Event ditulis ke sdss_result.geojson ({len(geojson['features'])} total)")
    except Exception as e:
        print(f"  Error menulis geojson: {e}")


def check_all_sources():
    from scheduler.bmkg import check_gempa, check_cuaca_ekstrem
    new_from_gempa = check_gempa()
    new_from_cuaca = check_cuaca_ekstrem()

    if new_from_gempa or new_from_cuaca:
        run_pipeline()


def update_bps_data_monthly():
    print(f"[{now()}] Sinkronisasi Data Kepadatan Penduduk BPS (Bulanan)...")
    try:
        import urllib.request
        
        url = "https://raw.githubusercontent.com/BPS-Indonesia/OpenData/main/kepadatan_penduduk.json"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if isinstance(data, dict) and 'jawa' in data:
                with open(BPS_DATA_FILE, 'w') as f:
                    json.dump(data, f, indent=4)
                print(f"[{now()}] Data BPS berhasil diupdate!")
    except Exception as e:
        print(f"[{now()}] Sync BPS gagal atau menggunakan data lokal: {e}")
