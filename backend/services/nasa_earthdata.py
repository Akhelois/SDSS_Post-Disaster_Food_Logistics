import os
import json
import requests
import datetime
from shapely.geometry import Point
import geopandas as gpd

from config import OUTPUT_GEOJSON, HEADERS

NASA_GIBS_WMTS_BASE = "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best"
NASA_FIRMS_VIIRS_SNPP_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/SUOMI_VIIRS_C2_SouthEast_Asia_24h.csv"
NASA_FIRMS_VIIRS_NOAA20_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/noaa-20-viirs-c2/csv/J1_VIIRS_C2_SouthEast_Asia_24h.csv"

def get_nasa_gibs_tile_url(layer="VIIRS_SNPP_CorrectedReflectance_TrueColor", date_str=None):
    if not date_str:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    return f"{NASA_GIBS_WMTS_BASE}/{layer}/default/{date_str}/GoogleMapsCompatible_Level9/{{z}}/{{y}}/{{x}}.jpg"

def fetch_live_nasa_firms_hotspots(min_frp=15.0):
    hotspots = []
    urls = [NASA_FIRMS_VIIRS_SNPP_URL, NASA_FIRMS_VIIRS_NOAA20_URL]
    
    for url in urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=20)
            if res.status_code != 200:
                continue
            
            lines = res.text.strip().split("\n")
            if len(lines) <= 1:
                continue
            
            for line in lines[1:]:
                parts = line.split(",")
                if len(parts) >= 12:
                    try:
                        lat = float(parts[0])
                        lon = float(parts[1])
                        confidence = parts[8].strip()
                        frp = float(parts[11])
                        acq_date = parts[5].strip()
                        
                        if 95.0 <= lon <= 141.0 and -11.0 <= lat <= 6.0:
                            if frp >= min_frp or confidence == "high":
                                hotspots.append({
                                    "lat": lat,
                                    "lon": lon,
                                    "frp": frp,
                                    "confidence": confidence,
                                    "date": acq_date
                                })
                    except Exception:
                        continue
        except Exception as e:
            print(f"[NASA FIRMS] Fetch error from {url}: {e}")
            
    return hotspots

def cluster_hotspots(hotspots, grid_size=0.25):
    clusters = {}
    for h in hotspots:
        grid_key = (round(h["lat"] / grid_size) * grid_size, round(h["lon"] / grid_size) * grid_size)
        if grid_key not in clusters:
            clusters[grid_key] = []
        clusters[grid_key].append(h)
    
    aggregated = []
    for (glat, glon), pts in clusters.items():
        if len(pts) >= 2 or any(p["frp"] >= 30.0 for p in pts):
            avg_lat = sum(p["lat"] for p in pts) / len(pts)
            avg_lon = sum(p["lon"] for p in pts) / len(pts)
            max_frp = max(p["frp"] for p in pts)
            latest_date = max(p["date"] for p in pts)
            aggregated.append({
                "lat": avg_lat,
                "lon": avg_lon,
                "count": len(pts),
                "max_frp": max_frp,
                "date": latest_date,
                "points": [(p["lon"], p["lat"]) for p in pts]
            })
    return aggregated

def check_nasa_wildfires():
    import services
    from scheduler.runner import write_event_to_geojson
    
    print("[NASA FIRMS Real-Time] Mengunduh data sensor hotspot satelit NASA terkini...")
    hotspots = fetch_live_nasa_firms_hotspots(min_frp=15.0)
    print(f"[NASA FIRMS Real-Time] Ditemukan {len(hotspots)} titik anomali termal aktif di Indonesia")
    
    clusters = cluster_hotspots(hotspots, grid_size=0.20)
    print(f"[NASA FIRMS Real-Time] Ditemukan {len(clusters)} klaster kebakaran hutan aktif")
    
    gdf_desa = services.load_desa_boundaries()
    registered_count = 0

    gdf_desa_proj = None
    if gdf_desa is not None and not gdf_desa.empty:
        try:
            gdf_desa_proj = gdf_desa.to_crs(epsg=3857)
        except Exception:
            pass

    clusters = sorted(clusters, key=lambda c: c["max_frp"], reverse=True)[:30]

    for c in clusters:
        lat = c["lat"]
        lon = c["lon"]
        wilayah_label = "Indonesia"
        
        if gdf_desa is not None and gdf_desa_proj is not None:
            try:
                pt = Point(lon, lat)
                pt_gdf = gpd.GeoDataFrame(geometry=[pt], crs="EPSG:4326").to_crs(epsg=3857)
                distances = gdf_desa_proj.geometry.distance(pt_gdf.geometry.iloc[0])
                nearest_idx = distances.idxmin()
                nearest_desa = gdf_desa.iloc[nearest_idx]
                
                desa_name = nearest_desa.get("ADM4_EN", "")
                kab_name = nearest_desa.get("ADM2_EN", "")
                prov_name = nearest_desa.get("ADM1_EN", "")
                wilayah_label = f"{prov_name}, {kab_name} (Desa {desa_name})"
            except Exception:
                pass
                
        severity = "Extreme" if c["max_frp"] >= 50.0 else "Severe"
        event_id = f"nasa_firms_{round(lat, 2)}_{round(lon, 2)}_{c['date']}"
        
        write_event_to_geojson(
            lat=lat,
            lon=lon,
            disaster_type="Kebakaran Hutan",
            wilayah=wilayah_label,
            severity=severity,
            event_id=event_id,
            event_date=c["date"]
        )
        registered_count += 1
        
    return registered_count > 0

def scan_disaster_area_nasa(lat, lon, severity_level, event_id, wilayah, disaster_type="Bencana Alam"):
    from scheduler.runner import write_event_to_geojson
    
    print(f"[NASA Earthdata NRT] Scanning area {wilayah} ({lat:.4f}, {lon:.4f})...")
    write_event_to_geojson(
        lat=lat,
        lon=lon,
        disaster_type=disaster_type,
        wilayah=wilayah,
        severity="Severe",
        event_id=f"nasa_{event_id}_scan",
        event_date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    return 1
