import time
import sys
sys.path.insert(0, '.')

t0 = time.time()
from services import load_desa_boundaries, load_geodata, assign_island, calculate_priority_scores
from core.zone_builder import remove_overlaps
import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPoint
import pandas as pd
import numpy as np
from config import OUTPUT_GEOJSON, LOGISTIK_PER_KK

print(f"[{time.time()-t0:.2f}s] Loading desa parquet...", flush=True)
gdf_desa = load_desa_boundaries()
print(f"[{time.time()-t0:.2f}s] Loaded {len(gdf_desa)} desas.", flush=True)

df_raw = load_geodata(OUTPUT_GEOJSON)
print(f"[{time.time()-t0:.2f}s] Loaded {len(df_raw)} raw points.", flush=True)

adm_cols = [c for c in gdf_desa.columns if c.startswith('ADM')]
cols_to_join = ['geometry'] + adm_cols

gdf_points = gpd.GeoDataFrame(
    df_raw,
    geometry=[Point(lon, lat) for lon, lat in zip(df_raw['lon'], df_raw['lat'])],
    crs="EPSG:4326"
)
clean_pts = gdf_points[[c for c in gdf_points.columns if c not in adm_cols and c != 'index_right']]
t_sj = time.time()
joined = gpd.sjoin(clean_pts, gdf_desa[cols_to_join], how='left', predicate='within')
joined = joined[~joined.index.duplicated(keep='first')]
print(f"[{time.time()-t0:.2f}s] sjoin within took {time.time()-t_sj:.2f}s.", flush=True)

if 'source' not in joined.columns:
    joined['source'] = 'Satelit'

mask_keep = (joined['source'].isin(['BMKG', 'PetaBencana'])) | joined['index_right'].notna()
df_raw = joined[mask_keep].copy()

if 'index_right' in df_raw.columns:
    df_raw['_desa_idx'] = df_raw['index_right']

desa_col = next(
    (c for c in ['ADM4_EN', 'ADM3_EN', 'ADM2_EN']
     if c in df_raw.columns and df_raw[c].notna().any()),
    None
)
if not desa_col:
    desa_col = 'wilayah' if 'wilayah' in df_raw.columns else '_desa'
    if '_desa' not in df_raw.columns:
        df_raw['_desa'] = 'Tidak Diketahui'
else:
    if 'wilayah' in df_raw.columns:
        fallback_mask = df_raw[desa_col].isna() | (df_raw[desa_col] == 'Tidak Diketahui')
        if fallback_mask.any():
            df_raw.loc[fallback_mask, desa_col] = df_raw.loc[fallback_mask, 'wilayah']
    df_raw[desa_col] = df_raw[desa_col].fillna('Tidak Diketahui')

df_raw['island'] = df_raw.apply(lambda r: assign_island(r['lat'], r['lon']), axis=1)

print(f"[{time.time()-t0:.2f}s] Aggregating desa zones...", flush=True)
df_valid = df_raw[df_raw[desa_col] != 'Tidak Diketahui'].copy()
agg_dict = {
    'count': ('lat', 'count'),
    'desa': (desa_col, 'first'),
    'island': ('island', 'first'),
    'avg_lon': ('lon', 'mean'),
    'avg_lat': ('lat', 'mean')
}
if 'ADM2_EN' in df_valid.columns:
    agg_dict['adm2'] = ('ADM2_EN', 'first')
if 'ADM1_EN' in df_valid.columns:
    agg_dict['adm1'] = ('ADM1_EN', 'first')
if 'disaster_type' in df_valid.columns:
    agg_dict['disaster_type'] = ('disaster_type', lambda x: next((v for v in x if pd.notna(v) and str(v).strip() != ''), None))
if 'source' in df_valid.columns:
    agg_dict['has_bmkg'] = ('source', lambda x: any(str(v).upper() == 'BMKG' for v in x if pd.notna(v)))
    agg_dict['has_petabencana'] = ('source', lambda x: any(str(v).lower() == 'petabencana' for v in x if pd.notna(v)))
if 'event_date' in df_valid.columns:
    agg_dict['event_date'] = ('event_date', 'min')

desa_damage = df_valid.groupby('_desa_idx').agg(**agg_dict).reset_index()
print(f"[{time.time()-t0:.2f}s] Grouped into {len(desa_damage)} unique desa locations.", flush=True)
print(f"[{time.time()-t0:.2f}s] ALL SUCCESS! Total execution time: {time.time()-t0:.2f}s", flush=True)
