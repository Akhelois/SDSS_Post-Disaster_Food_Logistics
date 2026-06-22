import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from shapely.geometry import Point
import geopandas as gpd

import services
from gee.downloader import scan_disaster_area
from config import (
    BMKG_GEMPA_URL, BMKG_NOWCAST_URL, MIN_MAGNITUDE, MIN_SEVERITY,
    PROCESSED_EVENTS_FILE, HEADERS
)
from scheduler.runner import (
    now, load_processed_events, save_processed_events,
    write_event_flag, write_event_to_geojson
)


def is_residential_area(lat, lon, min_built_ratio=0.03):
    try:
        gdf_desa = services.load_desa_boundaries()
        if gdf_desa is None or gdf_desa.empty:
            print(f"[Residential Check] Shapefile tidak tersedia, skip validasi")
            return True

        pt = Point(lon, lat)
        contains = gdf_desa.geometry.contains(pt)
        if contains.any():
            print(f"[Residential Check] ({lat:.4f}, {lon:.4f}) -> DALAM polygon desa")
            return True

        pt_gdf = gpd.GeoDataFrame(geometry=[pt], crs="EPSG:4326").to_crs(epsg=3857)
        desa_proj = gdf_desa.to_crs(epsg=3857)
        distances = desa_proj.geometry.distance(pt_gdf.geometry.iloc[0])
        min_dist_m = distances.min()

        if min_dist_m <= 5000:
            nearest_idx = distances.idxmin()
            nearest_desa = gdf_desa.iloc[nearest_idx]
            desa_name = nearest_desa.get('ADM4_EN', 'Unknown')
            print(f"[Residential Check] ({lat:.4f}, {lon:.4f}) -> {min_dist_m:.0f}m dari desa {desa_name} -> PERMUKIMAN")
            return True
        else:
            print(f"[Residential Check] ({lat:.4f}, {lon:.4f}) -> {min_dist_m:.0f}m dari desa terdekat -> BUKAN PERMUKIMAN (skip)")
            return False

    except Exception as e:
        print(f"[Residential Check] Error: {e} -> fallback allow")
        return True


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


def check_gempa():
    processed_events = load_processed_events()
    new_images = False

    try:
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
                            print(f"Skip: bukan daerah permukiman")
                    else:
                        skip_count += 1

            print(f"[Gempa] {len(quakes)} gempa ditemukan, {new_count} baru M>={MIN_MAGNITUDE}, {skip_count} kecil di-skip")
        else:
            print(f"[Gempa] HTTP {response.status_code}")
    except Exception as e:
        print(f"[Gempa] Error: {e}")

    return new_images


def check_cuaca_ekstrem():
    processed_events = load_processed_events()
    new_images = False

    try:
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
        print(f"[Cuaca] {len(items)} peringatan ditemukan")

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
                print(f"[{now()}] {disaster_type.upper()} di {wilayah} (Severity: {severity_text})")
                write_event_flag({
                    "type": disaster_type,
                    "severity": severity_text,
                    "wilayah": wilayah,
                    "lat": lat, "lon": lon
                })
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
                    print(f"Skip: bukan daerah permukiman")

            except Exception as e:
                print(f"[{now()}] Error parsing CAP {cap_url}: {e}")
                continue

        print(f"[Cuaca] {alert_count} alert diproses, {trigger_count} trigger GEE, {skip_processed} sudah diproses, {skip_severity} severity rendah")

    except Exception as e:
        print(f"[Cuaca] Error: {e}")

    return new_images
