import numpy as np
import requests
from functools import lru_cache


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
    if src_island != dst_island:
        return 'air', geo_m
    if pts is None or dist_m is None or len(pts) == 0:
        return 'air', geo_m
    start_gap = haversine_distance_m(src_lat, src_lon, pts[0][1], pts[0][0])
    end_gap   = haversine_distance_m(dst_lat, dst_lon, pts[-1][1], pts[-1][0])
    if start_gap > 2500 or end_gap > 2500:
        return 'air', geo_m
    if len(pts) <= 2 and dist_m > 2000:
        return 'air', geo_m
    arr = np.asarray(pts)
    if len(arr) >= 2:
        seg_lon = np.diff(arr[:, 0]) * 111320 * np.cos(np.radians(dst_lat))
        seg_lat = np.diff(arr[:, 1]) * 111320
        max_seg_m = np.sqrt(seg_lon**2 + seg_lat**2).max()
        if max_seg_m > 2000:
            return 'air', geo_m
    if dist_m >= 60000:
        return 'air', geo_m
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
    except Exception:
        pass
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
    except Exception:
        pass
    return lon, lat
