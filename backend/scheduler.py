"""
Event-Driven Multi-Hazard Scheduler
====================================
Memantau SEMUA jenis bencana dari BMKG:
  1. Gempa Bumi — via API gempaterkini.json (M≥5.0)
  2. Cuaca Ekstrem (Banjir, Hujan Lebat, Angin Kencang) — via Nowcast CAP XML

Jika ada event bencana baru, trigger GEE Downloader
hanya untuk area di sekitar lokasi bencana.
Jika ada citra baru yang diunduh, jalankan pipeline deteksi & model update.
"""

import time
import subprocess
import sys
import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from gee_downloader import scan_disaster_area

# === DATA SOURCES ===
BMKG_GEMPA_URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json"
BMKG_NOWCAST_URL = "https://www.bmkg.go.id/alerts/nowcast/id"

# === CONFIG ===
CHECK_INTERVAL_MINUTES = 2  # Cek setiap 2 menit
MIN_MAGNITUDE = 5.0
MIN_SEVERITY = ["Moderate", "Severe", "Extreme"]  # Trigger untuk semua peringatan bencana
PROCESSED_EVENTS_FILE = "output/processed_events.json"
NEW_EVENT_FLAG = "output/new_event.flag"

# Headers agar BMKG tidak memblokir request (HTTP 403)
HEADERS = {
    "User-Agent": "SDSS-Bencana/1.0 (Thesis Research; contact: support@bmkg.go.id)",
    "Accept": "application/json, application/xml, text/xml, */*"
}

os.makedirs("output", exist_ok=True)


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
    """Tulis signal file agar frontend tahu ada event baru (auto-refresh)."""
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
    """
    Tulis event BMKG langsung ke sdss_result.geojson agar frontend
    bisa menampilkan data meskipun citra satelit belum tersedia.
    """
    try:
        # Load existing geojson or create new
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

        # Confidence berdasarkan severity BMKG
        conf_map = {"Extreme": 0.9, "Severe": 0.7, "Moderate": 0.5}
        confidence = conf_map.get(severity, 0.5)

        # Tambahkan feature baru
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
                "coordinates": [round(lon, 6), round(lat, 6)]
            }
        }
        geojson["features"].append(feature)

        with open(RESULT_GEOJSON, 'w') as f:
            json.dump(geojson, f, indent=2)

        print(f"  \u2192 Event ditulis ke sdss_result.geojson ({len(geojson['features'])} total)")
    except Exception as e:
        print(f"  Error menulis geojson: {e}")


# ==============================================================
# SOURCE 1: GEMPA BUMI (API JSON)
# ==============================================================
def check_gempa():
    """Cek data gempa terkini dari BMKG API."""
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
                        print(f"\n[{now()}] 🚨 GEMPA M{magnitude} di {wilayah}")
                        write_event_flag({
                            "type": "Gempa Bumi",
                            "magnitude": magnitude,
                            "wilayah": wilayah,
                            "lat": lat, "lon": lon
                        })
                        # Langsung tulis ke geojson agar frontend tampil
                        write_event_to_geojson(lat, lon, "Gempa Bumi", wilayah,
                                              severity="Severe", event_id=event_id)
                        count = scan_disaster_area(
                            lat, lon, magnitude, event_id, wilayah,
                            disaster_type="Gempa Bumi"
                        )
                        if count > 0:
                            new_images = True
                    else:
                        skip_count += 1

            print(f"  [Gempa] {len(quakes)} gempa ditemukan, {new_count} baru M≥{MIN_MAGNITUDE}, {skip_count} kecil di-skip")
        else:
            print(f"  [Gempa] HTTP {response.status_code}")
    except Exception as e:
        print(f"  [Gempa] Error: {e}")

    return new_images


# ==============================================================
# SOURCE 2: CUACA EKSTREM / BANJIR (Nowcast CAP XML)
# ==============================================================
def parse_polygon_centroid(polygon_text):
    """
    Parse BMKG CAP polygon string dan hitung centroid.
    Format BMKG: "lat1,lon1 lat2,lon2 lat3,lon3 ..."
    """
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
    """
    Klasifikasikan jenis bencana dari teks event BMKG.
    """
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
    """
    Cek peringatan dini cuaca dari BMKG Nowcast RSS.
    Parse detail CAP XML untuk mendapat koordinat polygon presisi.
    """
    processed_events = load_processed_events()
    new_images = False

    try:
        # 1. Ambil RSS feed
        print(f"  [Cuaca] Mengambil peringatan nowcast BMKG...")
        response = requests.get(BMKG_NOWCAST_URL, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"  [Cuaca] HTTP {response.status_code} — gagal")
            return False

        # 2. Parse RSS XML
        root = ET.fromstring(response.content)

        # RSS namespace tidak perlu, tapi CAP perlu
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

            # 3. Ambil detail CAP XML untuk koordinat polygon
            try:
                cap_response = requests.get(cap_url, headers=HEADERS, timeout=15)
                if cap_response.status_code != 200:
                    continue

                # Parse CAP XML (namespace: urn:oasis:names:tc:emergency:cap:1.2)
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

                # Filter: hanya proses severity yang memenuhi threshold
                if severity_text not in MIN_SEVERITY:
                    skip_severity += 1
                    continue

                # Klasifikasi jenis bencana
                disaster_type = classify_weather_event(event_text, desc_text)

                # 4. Extract centroid dari polygon pertama (terbesar)
                polygons = area.findall("cap:polygon", ns) if area is not None else []
                if not polygons:
                    continue

                # Ambil polygon terbesar (paling banyak titik)
                best_polygon = max(polygons, key=lambda p: len(p.text.split()) if p.text else 0)
                lat, lon = parse_polygon_centroid(best_polygon.text)

                if lat is None or lon is None:
                    continue

                # Tentukan wilayah dari areaDesc
                area_desc = area.find("cap:areaDesc", ns) if area is not None else None
                wilayah = area_desc.text if area_desc is not None else title_text

                alert_count += 1
                print(f"\n[{now()}] ⛈ {disaster_type.upper()} di {wilayah} (Severity: {severity_text})")
                write_event_flag({
                    "type": disaster_type,
                    "severity": severity_text,
                    "wilayah": wilayah,
                    "lat": lat, "lon": lon
                })
                # Langsung tulis ke geojson agar frontend tampil
                write_event_to_geojson(lat, lon, disaster_type, wilayah,
                                      severity=severity_text, event_id=event_id)

                # Trigger GEE scan — magnitude fiktif berdasarkan severity
                pseudo_magnitude = 6.0 if severity_text == "Extreme" else 5.5
                count = scan_disaster_area(
                    lat, lon, pseudo_magnitude, event_id, wilayah,
                    disaster_type=disaster_type
                )
                if count > 0:
                    trigger_count += 1
                    new_images = True

            except Exception as e:
                print(f"[{now()}] Error parsing CAP {cap_url}: {e}")
                continue

        print(f"  [Cuaca] {alert_count} alert diproses, {trigger_count} trigger GEE, {skip_processed} sudah diproses, {skip_severity} severity rendah")

    except Exception as e:
        print(f"  [Cuaca] Error: {e}")

    return new_images


# ==============================================================
# MAIN LOOP
# ==============================================================
def check_all_sources():
    """Cek SEMUA sumber bencana dan trigger pipeline jika ada citra baru."""
    print(f"[{now()}] Mengecek semua sumber bencana BMKG...")

    new_from_gempa = check_gempa()
    new_from_cuaca = check_cuaca_ekstrem()

    # Jika ada citra baru dari sumber manapun, jalankan pipeline
    if new_from_gempa or new_from_cuaca:
        run_pipeline()


if __name__ == "__main__":
    print(f"[{now()}] === Multi-Hazard Event-Driven Scheduler ===")
    print(f"[{now()}] Sumber Data:")
    print(f"  1. Gempa Bumi    : {BMKG_GEMPA_URL}")
    print(f"  2. Cuaca Ekstrem : {BMKG_NOWCAST_URL}")
    print(f"[{now()}] Interval: {CHECK_INTERVAL_MINUTES} menit")
    print(f"[{now()}] Filter: Gempa M≥{MIN_MAGNITUDE}, Cuaca severity {MIN_SEVERITY}")
    print(f"[{now()}] Tekan Ctrl+C untuk berhenti\n")

    # Cek langsung saat pertama dijalankan
    check_all_sources()

    # Loop secara periodik
    while True:
        time.sleep(CHECK_INTERVAL_MINUTES * 60)
        check_all_sources()