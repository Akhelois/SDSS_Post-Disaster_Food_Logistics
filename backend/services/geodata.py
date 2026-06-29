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
    def extract_event_date(scene_id, processed_at):
        scene_id = str(scene_id)
        if 'T' in scene_id and '-' in scene_id:
            try:
                return pd.to_datetime(scene_id).replace(tzinfo=None)
            except:
                pass
        match = re.search(r'(\d{8})$', scene_id)
        if match:
            try:
                return datetime.datetime.strptime(match.group(1), '%Y%m%d')
            except:
                pass
        match = re.search(r'(\d{4}\.\d{2}\.\d{2})', scene_id)
        if match:
            try:
                return datetime.datetime.strptime(match.group(1), '%Y.%m.%d')
            except:
                pass
        if pd.notna(processed_at):
            try:
                return pd.to_datetime(processed_at).replace(tzinfo=None)
            except:
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
            # Fallback: try loading as raw JSON
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
            gdf = gdf[gdf['status'] == 'active'].copy()

        now = datetime.datetime.now()
        if 'scene_id' in gdf.columns:
            gdf['event_date'] = gdf.apply(
                lambda r: extract_event_date(r['scene_id'], r.get('processed_at')), axis=1
            )
            gdf['age_days'] = (now - gdf['event_date']).dt.total_seconds() / 86400.0
            gdf = gdf[gdf['age_days'] <= 3.0].copy()

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
