import geopandas as gpd
import pandas as pd
import numpy as np
import requests
import json
import os
import datetime
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist
from shapely.geometry import Point
from functools import lru_cache

OUTPUT_GEOJSON = "output/sdss_result.geojson"
STATUS_FILE = "output/hub_status.json"
DESA_SHP = "data/batas_desa/IDN_Final_WGS84.shp"
LOGISTIK_PER_KK = {
    'Beras (kg)': 10,
    'Air Minum (liter)': 50,
    'Mie Instan (Dus)': 2,
    'Minyak Goreng (liter)': 2,
    'Lauk Kaleng (paket)': 4,
}

ISLANDS = {
    'nias': (97.0, 0.4, 98.2, 1.6),
    'simeulue': (95.7, 2.2, 96.6, 3.1),
    'mentawai': (98.3, -3.5, 100.3, -0.9),
    'batu': (97.7, -0.8, 98.9, 0.2),
    'bangka': (105.0, -3.5, 107.0, -1.5),
    'belitung': (107.2, -3.3, 108.5, -2.5),
    'madura': (112.6, -7.3, 114.1, -6.9),
    'bali': (114.4, -8.9, 115.8, -8.0),
    'lombok': (115.9, -9.1, 116.9, -8.1),
    'sumatera': (95.2, -6.0, 105.8, 4.0),
    'jawa': (105.1, -8.8, 114.5, -5.8),
    'kalimantan': (108.0, -4.2, 117.8, 1.5),
    'sulawesi': (119.3, -5.7, 125.2, 1.8),
    'nusa_tenggara': (115.7, -9.0, 124.5, -7.9),
    'maluku': (124.5, -7.0, 132.0, 2.0),
    'papua': (130.5, -8.5, 140.5, -0.5),
}

def load_status():
    if os.path.exists(STATUS_FILE):
        try:
            content = open(STATUS_FILE).read().strip()
            return json.loads(content) if content else {}
        except Exception:
            return {}
    return {}

def assign_island(lat, lon):
    for name, (lon_min, lat_min, lon_max, lat_max) in ISLANDS.items():
        if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
            return name
    return 'other'

def haversine_distance_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1 = np.radians(lat1)
    p2 = np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2.0) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2.0) ** 2
    return 2.0 * r * np.arcsin(np.sqrt(a))

def choose_route_mode(src_lon, src_lat, dst_lon, dst_lat, src_island, dst_island, pts, dist_m):
    geo_m = haversine_distance_m(src_lat, src_lon, dst_lat, dst_lon)
    if src_island != dst_island: return 'air', geo_m
    if pts is None or dist_m is None or len(pts) == 0: return 'air', geo_m
    start_gap = haversine_distance_m(src_lat, src_lon, pts[0][1], pts[0][0])
    end_gap   = haversine_distance_m(dst_lat, dst_lon, pts[-1][1], pts[-1][0])
    if start_gap > 2500 or end_gap > 2500: return 'air', geo_m
    if len(pts) <= 2 and dist_m > 2000: return 'air', geo_m
    arr = np.asarray(pts)
    if len(arr) >= 2:
        seg_lon = np.diff(arr[:, 0]) * 111320 * np.cos(np.radians(dst_lat))
        seg_lat = np.diff(arr[:, 1]) * 111320
        max_seg_m = np.sqrt(seg_lon**2 + seg_lat**2).max()
        if max_seg_m > 2000: return 'air', geo_m
    if dist_m >= 60000: return 'air', geo_m
    return 'road', dist_m

@lru_cache(maxsize=1024)
def get_route_info(slon, slat, elon, elat):
    try:
        r = requests.get(
            f"http://router.project-osrm.org/route/v1/driving/{slon},{slat};{elon},{elat}?overview=full&geometries=geojson",
            timeout=8)
        d = r.json()
        if d.get('code') == 'Ok':
            coords = [[c[0], c[1]] for c in d['routes'][0]['geometry']['coordinates']]
            return coords, d['routes'][0]['distance']
    except Exception: pass
    return None, None

@lru_cache(maxsize=1024)
def snap_to_road(lon, lat, max_snap_m=200):
    try:
        r = requests.get(
            f"http://router.project-osrm.org/nearest/v1/driving/{lon},{lat}?number=1",
            timeout=3)
        d = r.json()
        if d['code'] == 'Ok':
            wp = d['waypoints'][0]
            if float(wp.get('distance', 0.0)) <= max_snap_m:
                return wp['location'][0], wp['location'][1]
    except Exception: pass
    return lon, lat

def merge_nearby_hubs(cc, min_dist_m):
    min_dist_deg = min_dist_m / 111320
    coords = cc[['safe_lat', 'safe_lon']].values
    merged, used = [], set()
    for i in range(len(coords)):
        if i in used: continue
        group = [i]
        for j in range(i + 1, len(coords)):
            if j not in used:
                same_island = cc.iloc[i]['island'] == cc.iloc[j]['island']
                dist = np.sqrt((coords[i][0] - coords[j][0]) ** 2 + (coords[i][1] - coords[j][1]) ** 2)
                if dist < min_dist_deg and same_island:
                    group.append(j)
                    used.add(j)
        used.add(i)
        rows = cc.iloc[group]
        all_desa = set()
        for dl in rows['desa_list'].dropna():
            for d in str(dl).split(', '):
                d = d.strip()
                if d and d != 'Tidak Diketahui':
                    all_desa.add(d)
        best_hub = rows.loc[rows['jumlah_red'].idxmax()]
        merged.append({
            'safe_lat': best_hub['safe_lat'],
            'safe_lon': best_hub['safe_lon'],
            'desa_list': ', '.join(sorted(all_desa)) if all_desa else '',
            'jumlah_red': int(rows['jumlah_red'].sum()),
            'avg_confidence': float(rows['avg_confidence'].max()), # <-- INI PERUBAHANNYA: Mean menjadi Max
            'island': str(rows['island'].iloc[0]),
            'cluster_ids': list(rows['cluster_id'])
        })
    return pd.DataFrame(merged).reset_index().rename(columns={'index': 'hub_id'})

def load_geodata(path):
    """Load geojson data — tanpa cache agar data baru langsung terbaca."""
    try:
        gdf = gpd.read_file(path).to_crs(epsg=4326)
        if 'status' in gdf.columns:
            gdf = gdf[gdf['status'] == 'active'].copy()
        gdf['lat'] = gdf.geometry.centroid.y
        gdf['lon'] = gdf.geometry.centroid.x
        if 'confidence' not in gdf.columns:
            gdf['confidence'] = 0.5
        return gdf
    except Exception: return None

@lru_cache(maxsize=1)
def load_desa_boundaries():
    if os.path.exists(DESA_SHP):
        try: return gpd.read_file(DESA_SHP).to_crs(epsg=4326)
        except Exception: pass
    return None

