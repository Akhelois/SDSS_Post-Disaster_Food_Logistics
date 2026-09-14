import time
import sys
sys.path.insert(0, '.')

from services import load_geodata, load_desa_boundaries
import geopandas as gpd
from shapely.geometry import Point

t0 = time.time()
gdf = load_desa_boundaries()
df = load_geodata('output/sdss_result.geojson')
print(f"Loaded in {time.time()-t0:.2f}s", flush=True)

pts = gpd.GeoDataFrame(df, geometry=[Point(lon, lat) for lon, lat in zip(df['lon'], df['lat'])], crs='EPSG:4326')
t1 = time.time()
joined = gpd.sjoin(pts, gdf[['geometry', 'ADM4_EN', 'ADM2_EN', 'ADM1_EN']], how='left', predicate='within')
matched = joined['ADM4_EN'].notna().sum()
print(f"sjoin within all {len(df)} points: {time.time()-t1:.2f}s. Matched on land: {matched}/{len(df)}", flush=True)

unmatched = joined[joined['ADM4_EN'].isna()]
print(f"Unmatched (offshore) points: {len(unmatched)}", flush=True)
if not unmatched.empty:
    print("Unmatched sources:", unmatched['source'].value_counts().to_dict(), flush=True)
