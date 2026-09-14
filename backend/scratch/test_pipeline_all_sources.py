import json, os, sys
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, MultiPoint

sys.path.insert(0, 'backend')
from services import load_geodata, load_desa_boundaries
from services.petabencana import fetch_petabencana_reports

OUTPUT_GEOJSON = "backend/output/sdss_result.geojson"
df_raw = load_geodata(OUTPUT_GEOJSON)
print(f"1. Raw geojson points: {len(df_raw)}")
print("   Sources in geojson:", df_raw['source'].value_counts().to_dict() if 'source' in df_raw.columns else 'no source')
print("   Types in geojson:", df_raw['disaster_type'].value_counts().to_dict() if 'disaster_type' in df_raw.columns else 'no type')

# Fetch PetaBencana
try:
    df_pb = fetch_petabencana_reports(hours=72)
    print(f"2. PetaBencana live points: {len(df_pb)}")
    if not df_pb.empty:
        df_raw = pd.concat([df_raw, df_pb], ignore_index=True)
except Exception as e:
    print(f"PetaBencana error: {e}")

print(f"3. Combined points: {len(df_raw)}")
print("   Combined Sources:", df_raw['source'].value_counts().to_dict())
print("   Combined Disaster Types:", df_raw['disaster_type'].value_counts().to_dict())

# Spatial join with desa
gdf_desa = load_desa_boundaries()
if gdf_desa is not None and not gdf_desa.empty:
    print(f"4. Shapefile loaded: {len(gdf_desa)} desas")
    adm_cols = [c for c in gdf_desa.columns if c.startswith('ADM')]
    gdf_points = gpd.GeoDataFrame(
        df_raw,
        geometry=[Point(lon, lat) for lon, lat in zip(df_raw['lon'], df_raw['lat'])],
        crs="EPSG:4326"
    )
    # Inner join to ensure only land points inside Indonesia
    joined = gpd.sjoin(gdf_points, gdf_desa[adm_cols + ['geometry']], how='inner', predicate='within')
    print(f"5. Points inside Indonesian land boundaries: {len(joined)}")
    print("   Sources inside Indonesia:", joined['source'].value_counts().to_dict())
    print("   Disasters inside Indonesia:", joined['disaster_type'].value_counts().to_dict())
