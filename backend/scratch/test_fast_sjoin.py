import time
import sys
sys.path.insert(0, '.')

from services import load_geodata, load_desa_boundaries
import geopandas as gpd
from shapely.geometry import Point

t0 = time.time()
gdf_desa = load_desa_boundaries()
print(f"Loaded desa in {time.time()-t0:.2f}s", flush=True)

df_raw = load_geodata('output/sdss_result.geojson')
print(f"Loaded {len(df_raw)} raw points in {time.time()-t0:.2f}s", flush=True)

adm_cols = [c for c in gdf_desa.columns if c.startswith('ADM')]
cols_to_join = ['geometry'] + adm_cols

gdf_points = gpd.GeoDataFrame(
    df_raw,
    geometry=[Point(lon, lat) for lon, lat in zip(df_raw['lon'], df_raw['lat'])],
    crs="EPSG:4326"
)
clean_points = gdf_points[[c for c in gdf_points.columns if c not in adm_cols and c != 'index_right']]

t1 = time.time()
joined = gpd.sjoin(clean_points, gdf_desa[cols_to_join], how='left', predicate='within')
joined = joined[~joined.index.duplicated(keep='first')]
print(f"sjoin completed in {time.time()-t1:.2f}s! Total rows: {len(joined)}", flush=True)
matched_count = joined['index_right'].notna().sum()
print(f"Matched on land: {matched_count}/{len(joined)}", flush=True)

# For unmatched (offshore quakes)
unmatched = joined[joined['index_right'].isna()]
print(f"Unmatched points: {len(unmatched)}", flush=True)
if not unmatched.empty:
    print(unmatched[['source', 'wilayah', 'lat', 'lon']].head(5), flush=True)
