import time
import sys
sys.path.insert(0, '.')

t0 = time.time()
print(f"[{time.time()-t0:.2f}s] Importing main...", flush=True)
import main

print(f"[{time.time()-t0:.2f}s] Loading geodata...", flush=True)
df_raw = main.load_geodata(main.OUTPUT_GEOJSON)

print(f"[{time.time()-t0:.2f}s] Spatial join...", flush=True)
gdf_desa = main.gdf_desa
adm_cols = [c for c in gdf_desa.columns if c.startswith('ADM')]
cols_to_join = ['geometry'] + adm_cols

import geopandas as gpd
from shapely.geometry import Point, Polygon
clean_pts = gpd.GeoDataFrame(
    df_raw,
    geometry=[Point(lon, lat) for lon, lat in zip(df_raw['lon'], df_raw['lat'])],
    crs="EPSG:4326"
)[[c for c in df_raw.columns if c not in adm_cols and c != 'index_right' and c != 'geometry'] + ['geometry']]

joined = gpd.sjoin(clean_pts, gdf_desa[cols_to_join], how='left', predicate='within')
joined = joined[~joined.index.duplicated(keep='first')]

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
df_raw['island'] = df_raw.apply(lambda r: main.assign_island(r['lat'], r['lon']), axis=1)

print(f"[{time.time()-t0:.2f}s] Grouping...", flush=True)
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

desa_damage = df_valid.groupby('_desa_idx').agg(**agg_dict).reset_index()
print(f"[{time.time()-t0:.2f}s] Total {len(desa_damage)} zones. Iterating zones...", flush=True)

rz_data = []
t_iter = time.time()
for i, (_, row) in enumerate(desa_damage.iterrows()):
    desa_idx = int(row['_desa_idx'])
    desa_geom = gdf_desa.geometry.iloc[desa_idx]
    polygon = main.desa_to_polygon(desa_geom)
    if polygon is None:
        continue
    rz_data.append({
        "polygon": polygon,
        "desa": str(row['desa']),
        "count": int(row['count']),
        "adm1": str(row.get('adm1', '')),
        "adm2": str(row.get('adm2', '')),
        "lon": float(row['avg_lon']),
        "lat": float(row['avg_lat']),
        "elapsed_hours": 12.0
    })

print(f"[{time.time()-t0:.2f}s] Built {len(rz_data)} zones in {time.time()-t_iter:.2f}s", flush=True)

t_ro = time.time()
print(f"[{time.time()-t0:.2f}s] Running remove_overlaps...", flush=True)
rz_data = main.remove_overlaps(rz_data)
print(f"[{time.time()-t0:.2f}s] remove_overlaps took {time.time()-t_ro:.2f}s", flush=True)

t_ps = time.time()
print(f"[{time.time()-t0:.2f}s] Running calculate_priority_scores...", flush=True)
rz_data = main.calculate_priority_scores(rz_data)
print(f"[{time.time()-t0:.2f}s] calculate_priority_scores took {time.time()-t_ps:.2f}s", flush=True)

print(f"[{time.time()-t0:.2f}s] ALL COMPLETE!", flush=True)
