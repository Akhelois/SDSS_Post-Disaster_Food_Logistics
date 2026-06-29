import os
import json
from shapely.geometry import Point, Polygon as ShapelyPolygon
import requests
import time as _time

from config import (
    OUTPUT_GEOJSON, NEW_EVENT_FLAG, BUILDING_CACHE_TTL
)


def get_current_disaster_type(island_fallback='other', lat=None, lon=None):
    flag_path = NEW_EVENT_FLAG
    try:
        if os.path.exists(flag_path) and lat is not None and lon is not None:
            with open(flag_path) as f:
                event = json.load(f)
            event_data = event.get("event", {})
            event_type = event_data.get("type", "")
            event_lat = event_data.get("lat")
            event_lon = event_data.get("lon")
            if event_type and event_lat is not None and event_lon is not None:
                dist = ((lat - event_lat)**2 + (lon - event_lon)**2)**0.5
                if dist < 2.0:
                    return event_type
    except Exception:
        pass

    geojson_path = OUTPUT_GEOJSON
    try:
        if os.path.exists(geojson_path) and lat is not None and lon is not None:
            with open(geojson_path) as f:
                geojson = json.load(f)
            best_dist = float('inf')
            best_type = None
            for feature in geojson.get("features", []):
                props = feature.get("properties", {})
                if props.get("source") != "BMKG":
                    continue
                dt = props.get("disaster_type", "")
                if not dt:
                    continue
                coords = feature.get("geometry", {}).get("coordinates", [])
                if len(coords) >= 2:
                    d = ((lat - coords[1])**2 + (lon - coords[0])**2)**0.5
                    if d < best_dist:
                        best_dist = d
                        best_type = dt
            if best_type and best_dist < 2.0:
                return best_type
    except Exception:
        pass

    return "Bencana Alam"


import json
import os

BUILDING_CACHE_FILE = "output/building_cache.json"

_building_cache = {}
_building_cache_time = {}

if os.path.exists(BUILDING_CACHE_FILE):
    try:
        with open(BUILDING_CACHE_FILE, "r") as f:
            _disk_cache = json.load(f)
            for k_str, v in _disk_cache.items():
                if isinstance(v, dict) and "buildings" in v and "time" in v:
                    # keys in JSON are strings, convert back to tuple of floats
                    try:
                        lat_s, lon_s = k_str.split("_")
                        _building_cache[(float(lat_s), float(lon_s))] = v["buildings"]
                        _building_cache_time[(float(lat_s), float(lon_s))] = v["time"]
                    except:
                        pass
    except Exception as e:
        print(f"Failed to load building cache: {e}")

def save_building_cache():
    try:
        os.makedirs(os.path.dirname(BUILDING_CACHE_FILE), exist_ok=True)
        dump_data = {}
        for k, v in _building_cache.items():
            dump_data[f"{k[0]}_{k[1]}"] = {
                "buildings": v,
                "time": _building_cache_time.get(k, 0)
            }
        with open(BUILDING_CACHE_FILE, "w") as f:
            json.dump(dump_data, f)
    except Exception as e:
        print(f"Failed to save building cache: {e}")

def fetch_buildings_near(lat, lon, radius_m=500, max_buildings=200):
    cache_key = (round(lat, 3), round(lon, 3))
    now = _time.time()

    if cache_key in _building_cache:
        if now - _building_cache_time.get(cache_key, 0) < BUILDING_CACHE_TTL:
            return _building_cache[cache_key]

    try:
        overpass_endpoints = [
            "https://z.overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
            "https://overpass-api.de/api/interpreter"
        ]
        
        query = f"""
        [out:json][timeout:15];
        way["building"](around:{radius_m},{lat},{lon});
        out geom;
        """
        
        data = None
        headers = {'User-Agent': 'SDSS-Disaster-Logistics-Research/1.0'}
        for url in overpass_endpoints:
            try:
                r = requests.get(url, params={'data': query}, headers=headers, timeout=25)
                if r.status_code == 200:
                    data = r.json()
                    break
            except Exception:
                continue
                
        if not data:
            print(f"  [OSM] Error fetching buildings: All endpoints failed or timed out.")
            return []

        buildings = []
        for elem in data.get('elements', [])[:max_buildings]:
            if elem.get('type') == 'way' and 'geometry' in elem:
                coords = [[round(n['lon'], 6), round(n['lat'], 6)] for n in elem['geometry']]
                if len(coords) >= 4:
                    buildings.append(coords)

        _building_cache[cache_key] = buildings
        _building_cache_time[cache_key] = now
        save_building_cache()
        return buildings
    except Exception as e:
        print(f"  [OSM] Error fetching buildings: {e}")
        return []


def get_buildings_for_zone(raw_points, zone_lat, zone_lon):
    if not raw_points:
        return []

    buildings = fetch_buildings_near(zone_lat, zone_lon, radius_m=400)

    if not buildings:
        return []

    building_data = []
    for bcoords in buildings:
        try:
            bp = ShapelyPolygon(bcoords)
            if bp.is_valid and not bp.is_empty:
                building_data.append((bcoords, bp))
        except Exception:
            continue

    if not building_data:
        return []

    matched_indices = set()
    result = []

    for pt in raw_points:
        pt_geom = Point(pt[0], pt[1])

        min_dist = float('inf')
        nearest_idx = -1
        for i, (bcoords, bpoly) in enumerate(building_data):
            if i in matched_indices:
                continue
            dist = pt_geom.distance(bpoly)
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i

        if nearest_idx >= 0 and min_dist < 0.003:
            matched_indices.add(nearest_idx)
            result.append(building_data[nearest_idx][0])

    return result
