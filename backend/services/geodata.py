import geopandas as gpd
import pandas as pd
import numpy as np
import os
import re
import datetime
from shapely.geometry import Point
from functools import lru_cache

from config import (
    OUTPUT_GEOJSON, DESA_SHP, ISLANDS
)


def load_geodata(path):
    def extract_event_date(scene_id, processed_at, event_date_val=None):
        if pd.notna(event_date_val) and str(event_date_val).strip() != '':
            try:
                dt = pd.to_datetime(event_date_val)
                return dt.tz_convert('Asia/Jakarta').tz_localize(None) if getattr(dt, 'tzinfo', None) else dt.replace(tzinfo=None)
            except Exception:
                pass

        scene_id_str = str(scene_id) if pd.notna(scene_id) else ''
        
        if 'T' in scene_id_str and '-' in scene_id_str:
            try:
                dt = pd.to_datetime(scene_id_str)
                if getattr(dt, 'tzinfo', None) is not None:
                    dt = dt.tz_convert('Asia/Jakarta').tz_localize(None)
                else:
                    dt = dt.replace(tzinfo=None)
                return dt
            except Exception:
                pass

        match_nowcast = re.search(r'(\d{4}\.\d{2}\.\d{2}\.\d{2}\.\d{2})', scene_id_str)
        if match_nowcast:
            try:
                dt_utc = datetime.datetime.strptime(match_nowcast.group(1), '%Y.%m.%d.%H.%M')
                return dt_utc + datetime.timedelta(hours=7)
            except Exception:
                pass

        match_date = re.search(r'(\d{4}\.\d{2}\.\d{2})', scene_id_str)
        if match_date:
            try:
                return datetime.datetime.strptime(match_date.group(1), '%Y.%m.%d')
            except Exception:
                pass

        match_ymd = re.search(r'(\d{8})', scene_id_str)
        if match_ymd:
            try:
                return datetime.datetime.strptime(match_ymd.group(1), '%Y%m%d')
            except Exception:
                pass

        if pd.notna(processed_at) and str(processed_at).strip() != '':
            try:
                dt = pd.to_datetime(processed_at)
                return dt.tz_convert('Asia/Jakarta').tz_localize(None) if getattr(dt, 'tzinfo', None) else dt.replace(tzinfo=None)
            except Exception:
                pass

        return datetime.datetime.now()

    for attempt in range(5):
        try:
            gdf = gpd.read_file(path).to_crs(epsg=4326)
            break
        except Exception as e:
            if attempt < 4:
                import time as _time
                _time.sleep(0.5)
                continue
            try:
                import json
                with open(path, 'r') as f:
                    raw = json.load(f)
                gdf = gpd.GeoDataFrame.from_features(
                    raw.get('features', []), crs="EPSG:4326"
                )
                break
            except Exception:
                print(f"Error loading geodata: {e}")
                return None

    try:
        if 'status' in gdf.columns:
            gdf = gdf[gdf['status'] != 'resolved'].copy()

        now = datetime.datetime.now()
        if 'scene_id' in gdf.columns:
            gdf['event_date'] = gdf.apply(
                lambda r: extract_event_date(r['scene_id'], r.get('processed_at'), r.get('event_date') if 'event_date' in r else None), axis=1
            )
            gdf['age_days'] = (now - gdf['event_date']).dt.total_seconds() / 86400.0

        if gdf.empty:
            return gdf

        gdf['lat'] = gdf.geometry.centroid.y
        gdf['lon'] = gdf.geometry.centroid.x
        if 'confidence' not in gdf.columns:
            gdf['confidence'] = 0.5
        return gdf
    except Exception as e:
        print(f"Error loading geodata: {e}")
        return None


@lru_cache(maxsize=1)
def load_desa_boundaries():
    if os.path.exists(DESA_SHP):
        try:
            return gpd.read_file(DESA_SHP).to_crs(epsg=4326)
        except Exception:
            pass
    return None


def assign_island(lat, lon):
    for name, (lon_min, lat_min, lon_max, lat_max) in ISLANDS.items():
        if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
            return name
    return 'other'


def load_status():
    from config import STATUS_FILE
    if os.path.exists(STATUS_FILE):
        try:
            content = open(STATUS_FILE).read().strip()
            return json.loads(content) if content else {}
        except Exception:
            return {}
    return {}
