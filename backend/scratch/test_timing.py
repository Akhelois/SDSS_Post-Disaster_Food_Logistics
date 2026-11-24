import time
import os

t0 = time.time()
print(f"[{time.time()-t0:.2f}s] Importing pandas & geopandas...")
import pandas as pd
import geopandas as gpd

print(f"[{time.time()-t0:.2f}s] Importing config & services...")
from config import OUTPUT_GEOJSON
from services import load_geodata, load_desa_boundaries, assign_island

print(f"[{time.time()-t0:.2f}s] Loading desa boundaries...")
gdf_desa = load_desa_boundaries()
print(f"[{time.time()-t0:.2f}s] Loaded {len(gdf_desa) if gdf_desa is not None else 0} desa boundaries.")

print(f"[{time.time()-t0:.2f}s] Loading geodata ({OUTPUT_GEOJSON})...")
df_raw = load_geodata(OUTPUT_GEOJSON)
print(f"[{time.time()-t0:.2f}s] Loaded {len(df_raw) if df_raw is not None else 0} raw points.")

print(f"[{time.time()-t0:.2f}s] Running spatial filter...")
if gdf_desa is not None and not gdf_desa.empty:
    from shapely.geometry import Point
    if 'source' not in df_raw.columns:
        df_raw['source'] = 'Satelit'
    is_bmkg = df_raw['source'].fillna('') == 'BMKG'
    df_bmkg = df_raw[is_bmkg].copy()
    df_satelit = df_raw[~is_bmkg].copy()
    print(f"[{time.time()-t0:.2f}s] df_bmkg: {len(df_bmkg)}, df_satelit: {len(df_satelit)}")
    if not df_satelit.empty:
        gdf_points = gpd.GeoDataFrame(
            df_satelit,
            geometry=[Point(lon, lat) for lon, lat in zip(df_satelit['lon'], df_satelit['lat'])],
            crs="EPSG:4326"
        )
        print(f"[{time.time()-t0:.2f}s] Starting sjoin on satelit points vs 83,000 desa...")
        joined = gpd.sjoin(gdf_points, gdf_desa[['geometry']], how='inner', predicate='within')
        print(f"[{time.time()-t0:.2f}s] Finished sjoin! Matched {len(joined)} points.")
