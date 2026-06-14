import time
import subprocess
import sys
import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from gee_downloader import scan_disaster_area
from shapely.geometry import Point
import geopandas as gpd
import services

BMKG_GEMPA_URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json"
BMKG_NOWCAST_URL = "https://www.bmkg.go.id/alerts/nowcast/id"

CHECK_INTERVAL_MINUTES = 2
MIN_MAGNITUDE = 5.0
MIN_SEVERITY = ["Moderate", "Severe", "Extreme"]
PROCESSED_EVENTS_FILE = "output/processed_events.json"
NEW_EVENT_FLAG = "output/new_event.flag"

HEADERS = {
    "User-Agent": "SDSS-Bencana/1.0 (Thesis Research; contact: support@bmkg.go.id)",
    "Accept": "application/json, application/xml, text/xml, */*"
}

os.makedirs("output", exist_ok=True)


def is_residential_area(lat, lon, min_built_ratio=0.03):
    """
    Validasi apakah koordinat berada di daerah permukiman.
    Menggunakan shapefile batas desa + opsional GEE Dynamic World.
    Return True jika di area permukiman, False jika lautan/hutan/gunung.
    """
    try:
        gdf_desa = services.load_desa_boundaries()
        if gdf_desa is None or gdf_desa.empty:
            print(f"  [Residential Check] Shapefile tidak tersedia, skip validasi")
            return True  # Fallback: allow if no shapefile

        pt = Point(lon, lat)
        # Cek apakah titik jatuh di dalam polygon desa manapun
        contains = gdf_desa.geometry.contains(pt)
        if contains.any():
            print(f"  [Residential Check] ({lat:.4f}, {lon:.4f}) -> DALAM polygon desa")
            return True

        # Cek jarak ke desa terdekat (buffer 5km ≈ 0.045 derajat)
        pt_gdf = gpd.GeoDataFrame(geometry=[pt], crs="EPSG:4326").to_crs(epsg=3857)
        desa_proj = gdf_desa.to_crs(epsg=3857)
        distances = desa_proj.geometry.distance(pt_gdf.geometry.iloc[0])
        min_dist_m = distances.min()

        if min_dist_m <= 5000:  # 5km threshold
            nearest_idx = distances.idxmin()
            nearest_desa = gdf_desa.iloc[nearest_idx]
            desa_name = nearest_desa.get('ADM4_EN', 'Unknown')
            print(f"  [Residential Check] ({lat:.4f}, {lon:.4f}) -> {min_dist_m:.0f}m dari desa {desa_name} -> PERMUKIMAN")
            return True
        else:
            print(f"  [Residential Check] ({lat:.4f}, {lon:.4f}) -> {min_dist_m:.0f}m dari desa terdekat -> BUKAN PERMUKIMAN (skip)")
            return False

    except Exception as e:
        print(f"  [Residential Check] Error: {e} -> fallback allow")
        return True  # Fallback: allow on error


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
    print(f"\n[{now()}] Menjalankan pipeline deteksi kerusakan & incremental learning...")
    r = subprocess.run([sys.executable, "pipeline.py"], capture_output=False)
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


RESULT_GEOJSON = "output/sdss_result.geojson"

def write_event_to_geojson(lat, lon, disaster_type, wilayah, severity="Moderate", event_id=""):
    try:
        if os.path.exists(RESULT_GEOJSON) and os.path.getsize(RESULT_GEOJSON) > 10:
            with open(RESULT_GEOJSON, 'r') as f:
                geojson = json.load(f)
        else:
            geojson = {
                "type": "FeatureCollection",
                "name": "sdss_result",
                "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
                "features": []
            }

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
                "processed_at": now(),
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

        with open(RESULT_GEOJSON, 'w') as f:
            json.dump(geojson, f, indent=2)

        print(f"  -> Event ditulis ke sdss_result.geojson ({len(geojson['features'])} total)")
    except Exception as e:
        print(f"  Error menulis geojson: {e}")


def check_gempa():
    processed_events = load_processed_events()
    new_images = False

    try:
        print(f"  [Gempa] Mengambil data dari BMKG...")
        response = requests.get(BMKG_GEMPA_URL, headers=HEADERS, timeout=15)
        if response.status_code == 200:
            data = response.json()
            quakes = data.get("Infogempa", {}).get("gempa", [])
            new_count = 0
            skip_count = 0

            for quake in reversed(quakes):
                event_id = quake.get("DateTime")

                if event_id not in processed_events:
                    magnitude = float(quake.get("Magnitude", 0))
                    coords = quake.get("Coordinates", "0,0").split(",")
                    lat, lon = float(coords[0]), float(coords[1])
                    wilayah = quake.get("Wilayah", "")

                    processed_events.add(event_id)
                    save_processed_events(processed_events)

                    if magnitude >= MIN_MAGNITUDE:
                        new_count += 1
                        print(f"\n[{now()}] [!] GEMPA M{magnitude} di {wilayah}")
                        write_event_flag({
                            "type": "Gempa Bumi",
                            "magnitude": magnitude,
                            "wilayah": wilayah,
                            "lat": lat, "lon": lon
                        })
                        # Validasi: hanya proses jika daerah permukiman
                        if is_residential_area(lat, lon):
                            write_event_to_geojson(lat, lon, "Gempa Bumi", wilayah,
                                                  severity="Severe", event_id=event_id)
                            count = scan_disaster_area(
                                lat, lon, magnitude, event_id, wilayah,
                                disaster_type="Gempa Bumi"
                            )
                            if count > 0:
                                new_images = True
                        else:
                            print(f"  -> Skip: bukan daerah permukiman")
                    else:
                        skip_count += 1

            print(f"  [Gempa] {len(quakes)} gempa ditemukan, {new_count} baru M>={MIN_MAGNITUDE}, {skip_count} kecil di-skip")
        else:
            print(f"  [Gempa] HTTP {response.status_code}")
    except Exception as e:
        print(f"  [Gempa] Error: {e}")

    return new_images


def parse_polygon_centroid(polygon_text):
    try:
        points = polygon_text.strip().split()
        lats, lons = [], []
        for point in points:
            parts = point.split(",")
            if len(parts) == 2:
                lats.append(float(parts[0]))
                lons.append(float(parts[1]))
        if lats and lons:
            return sum(lats) / len(lats), sum(lons) / len(lons)
    except Exception:
        pass
    return None, None


def classify_weather_event(event_text, description_text):
    text = (event_text + " " + description_text).lower()

    if "banjir" in text:
        return "Banjir"
    elif "longsor" in text or "tanah longsor" in text:
        return "Tanah Longsor"
    elif "puting beliung" in text or "angin kencang" in text:
        return "Angin Kencang"
    elif "hujan lebat" in text or "hujan sangat lebat" in text:
        if "banjir" in text:
            return "Banjir"
        return "Hujan Lebat"
    elif "tsunami" in text:
        return "Tsunami"
    else:
        return "Cuaca Ekstrem"


def check_cuaca_ekstrem():
    processed_events = load_processed_events()
    new_images = False

    try:
        print(f"  [Cuaca] Mengambil peringatan nowcast BMKG...")
        response = requests.get(BMKG_NOWCAST_URL, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"  [Cuaca] HTTP {response.status_code} - gagal")
            return False

        root = ET.fromstring(response.content)

        items = root.findall(".//item")
        alert_count = 0
        trigger_count = 0
        skip_severity = 0
        skip_processed = 0
        print(f"  [Cuaca] {len(items)} peringatan ditemukan")

        for item in items:
            guid_el = item.find("guid")
            if guid_el is None:
                continue
            event_id = f"nowcast_{guid_el.text}"

            if event_id in processed_events:
                skip_processed += 1
                continue

            processed_events.add(event_id)
            save_processed_events(processed_events)

            title = item.find("title")
            link = item.find("link")
            description = item.find("description")

            title_text = title.text if title is not None else ""
            desc_text = description.text if description is not None else ""
            cap_url = link.text if link is not None else ""

            if not cap_url:
                continue

            try:
                cap_response = requests.get(cap_url, headers=HEADERS, timeout=15)
                if cap_response.status_code != 200:
                    continue

                ns = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}
                cap_root = ET.fromstring(cap_response.content)

                info = cap_root.find("cap:info", ns)
                if info is None:
                    continue

                event = info.find("cap:event", ns)
                severity = info.find("cap:severity", ns)
                area = info.find("cap:area", ns)

                event_text = event.text if event is not None else ""
                severity_text = severity.text if severity is not None else ""

                if severity_text not in MIN_SEVERITY:
                    skip_severity += 1
                    continue

                disaster_type = classify_weather_event(event_text, desc_text)

                polygons = area.findall("cap:polygon", ns) if area is not None else []
                if not polygons:
                    continue

                best_polygon = max(polygons, key=lambda p: len(p.text.split()) if p.text else 0)
                lat, lon = parse_polygon_centroid(best_polygon.text)

                if lat is None or lon is None:
                    continue

                area_desc = area.find("cap:areaDesc", ns) if area is not None else None
                wilayah = area_desc.text if area_desc is not None else title_text

                alert_count += 1
                print(f"\n[{now()}] {disaster_type.upper()} di {wilayah} (Severity: {severity_text})")
                write_event_flag({
                    "type": disaster_type,
                    "severity": severity_text,
                    "wilayah": wilayah,
                    "lat": lat, "lon": lon
                })
                # Validasi: hanya proses jika daerah permukiman
                if is_residential_area(lat, lon):
                    write_event_to_geojson(lat, lon, disaster_type, wilayah,
                                           severity=severity_text, event_id=event_id)

                    pseudo_magnitude = 6.0 if severity_text == "Extreme" else 5.5
                    count = scan_disaster_area(
                        lat, lon, pseudo_magnitude, event_id, wilayah,
                        disaster_type=disaster_type
                    )
                    if count > 0:
                        trigger_count += 1
                        new_images = True
                else:
                    print(f"  -> Skip: bukan daerah permukiman")

            except Exception as e:
                print(f"[{now()}] Error parsing CAP {cap_url}: {e}")
                continue

        print(f"  [Cuaca] {alert_count} alert diproses, {trigger_count} trigger GEE, {skip_processed} sudah diproses, {skip_severity} severity rendah")

    except Exception as e:
        print(f"  [Cuaca] Error: {e}")

    return new_images


def check_all_sources():
    print(f"[{now()}] Mengecek semua sumber bencana BMKG...")

    new_from_gempa = check_gempa()
    new_from_cuaca = check_cuaca_ekstrem()

    if new_from_gempa or new_from_cuaca:
        run_pipeline()


def update_bps_data_monthly():
    """Tugas latar belakang untuk sinkronisasi data BPS bulanan."""
    bps_file = "bps_data.json"
    print(f"[{now()}] Sinkronisasi Data Kepadatan Penduduk BPS (Bulanan)...")
    try:
        # Simulasi fetch ke BPS API / Central Repo
        import urllib.request
        import json
        
        # Endpoint simulasi
        url = "https://raw.githubusercontent.com/BPS-Indonesia/OpenData/main/kepadatan_penduduk.json"
        
        # Jika dalam mode produksi, URL ini akan mengunduh data terbaru
        # Untuk tujuan demo, jika gagal fetch kita biarkan saja (akan menggunakan lokal)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if isinstance(data, dict) and 'jawa' in data:
                with open(bps_file, 'w') as f:
                    json.dump(data, f, indent=4)
                print(f"[{now()}] Data BPS berhasil diupdate!")
    except Exception as e:
        print(f"[{now()}] Sync BPS gagal atau menggunakan data lokal: {e}")


if __name__ == "__main__":
    print(f"[{now()}] === Multi-Hazard Event-Driven Scheduler ===")
    print(f"[{now()}] Sumber Data:")
    print(f"  1. Gempa Bumi    : {BMKG_GEMPA_URL}")
    print(f"  2. Cuaca Ekstrem : {BMKG_NOWCAST_URL}")
    print(f"[{now()}] Interval: {CHECK_INTERVAL_MINUTES} menit")
    print(f"[{now()}] Filter: Gempa M>={MIN_MAGNITUDE}, Cuaca severity {MIN_SEVERITY}")
    print(f"[{now()}] Tekan Ctrl+C untuk berhenti\n")

    check_all_sources()
    update_bps_data_monthly()
    last_bps_update = datetime.now()

    while True:
        time.sleep(CHECK_INTERVAL_MINUTES * 60)
        check_all_sources()
        
        # Cek apakah sudah 30 hari sejak update BPS terakhir
        if (datetime.now() - last_bps_update).days >= 30:
            update_bps_data_monthly()
            last_bps_update = datetime.now()