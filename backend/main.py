from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
import numpy as np
import services
from shapely.geometry import Point
import geopandas as gpd

app = FastAPI(title="SDSS Logistik Bencana API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Jenis Bencana Per Wilayah ===
DISASTER_BY_ISLAND = {
    'sumatera': 'Gempa Bumi',
    'jawa': 'Gempa Bumi',
    'kalimantan': 'Banjir',
    'sulawesi': 'Gempa Bumi',
    'nusa_tenggara': 'Gempa Bumi',
    'maluku': 'Gempa Bumi',
    'papua': 'Banjir',
    'bali': 'Gempa Bumi',
    'lombok': 'Gempa Bumi',
    'nias': 'Tsunami',
    'simeulue': 'Tsunami',
    'mentawai': 'Tsunami',
    'bangka': 'Banjir',
    'belitung': 'Banjir',
    'madura': 'Banjir Rob',
    'batu': 'Gempa Bumi',
    'other': 'Bencana Alam',
}

def desa_to_polygon(geom, simplify_tol=0.002):
    """Convert desa geometry to simplified polygon coordinates for frontend."""
    try:
        simplified = geom.simplify(simplify_tol)
        if simplified.is_empty:
            return None
        if simplified.geom_type == 'MultiPolygon':
            largest = max(simplified.geoms, key=lambda p: p.area)
            return [[round(c[0], 6), round(c[1], 6)] for c in largest.exterior.coords]
        elif simplified.geom_type == 'Polygon':
            return [[round(c[0], 6), round(c[1], 6)] for c in simplified.exterior.coords]
    except Exception:
        pass
    return None

print("Loading geodata boundaries...")
gdf_desa = services.load_desa_boundaries()

@app.get("/")
def get_dashboard_data():
    df_raw = services.load_geodata(services.OUTPUT_GEOJSON)
    if df_raw is None or df_raw.empty:
        return {"error": "standby"}

    # Filter: hanya titik yang ada di daratan desa
    if gdf_desa is not None and not gdf_desa.empty:
        gdf_points = gpd.GeoDataFrame(
            df_raw,
            geometry=[Point(lon, lat) for lon, lat in zip(df_raw['lon'], df_raw['lat'])],
            crs="EPSG:4326"
        )
        joined = gpd.sjoin(gdf_points, gdf_desa[['geometry']], how='inner', predicate='within')
        df_raw = df_raw.loc[df_raw.index.isin(joined.index.unique())].copy()

    if df_raw.empty:
        return {"error": "no_land_points"}

    conf_thresh = 0.2
    df_raw = df_raw[df_raw['confidence'] >= conf_thresh].copy()
    if df_raw.empty:
        return {"error": "no_confident_points"}

    # Spatial join: temukan desa untuk setiap titik kerusakan
    desa_col = None
    if gdf_desa is not None and not gdf_desa.empty:
        adm_cols = [c for c in gdf_desa.columns if c.startswith('ADM')]
        if adm_cols:
            gdf_points_proj = gpd.GeoDataFrame(
                df_raw,
                geometry=[Point(lon, lat) for lon, lat in zip(df_raw['lon'], df_raw['lat'])],
                crs="EPSG:4326"
            ).to_crs(epsg=3857)
            gdf_desa_proj = gdf_desa[adm_cols + ['geometry']].to_crs(epsg=3857)
            joined = gpd.sjoin_nearest(gdf_points_proj, gdf_desa_proj, how='left', max_distance=55000)
            joined = joined[~joined.index.duplicated(keep='first')]
            if 'index_right' in joined.columns:
                df_raw['_desa_idx'] = joined['index_right'].values
            for col in adm_cols:
                if col in joined.columns:
                    df_raw[col] = joined[col].values
            desa_col = next(
                (c for c in ['ADM4_EN', 'ADM3_EN', 'ADM2_EN']
                 if c in df_raw.columns and df_raw[c].notna().any()),
                None
            )

    if not desa_col:
        df_raw['_desa'] = 'Tidak Diketahui'
        desa_col = '_desa'
    else:
        df_raw[desa_col] = df_raw[desa_col].fillna('Tidak Diketahui')

    df_raw['island'] = df_raw.apply(lambda r: services.assign_island(r['lat'], r['lon']), axis=1)

    # === Bangun zona kerusakan per desa (tanpa clustering/hub) ===
    rz_data = []
    if gdf_desa is not None and '_desa_idx' in df_raw.columns:
        desa_damage = df_raw.groupby('_desa_idx').agg(
            count=('lat', 'count'),
            desa=(desa_col, 'first'),
            island=('island', 'first'),
            avg_lon=('lon', 'mean'),
            avg_lat=('lat', 'mean'),
        ).reset_index()

        for _, row in desa_damage.iterrows():
            try:
                desa_idx = int(row['_desa_idx'])
                desa_geom = gdf_desa.geometry.iloc[desa_idx]
                polygon = desa_to_polygon(desa_geom)
                if polygon is None:
                    continue
                island = row['island']
                disaster_type = DISASTER_BY_ISLAND.get(island, 'Bencana Alam')
                damage_count = int(row['count'])

                # Estimasi logistik pangan per desa berdasarkan jumlah kerusakan
                logistics = {
                    "beras": damage_count * services.LOGISTIK_PER_KK['Beras (kg)'],
                    "air": damage_count * services.LOGISTIK_PER_KK['Air Minum (liter)'],
                    "mie": damage_count * services.LOGISTIK_PER_KK['Mie Instan (Dus)'],
                    "minyak": damage_count * services.LOGISTIK_PER_KK['Minyak Goreng (liter)'],
                    "lauk": damage_count * services.LOGISTIK_PER_KK['Lauk Kaleng (paket)'],
                }

                rz_data.append({
                    "polygon": polygon,
                    "desa": str(row['desa']),
                    "count": damage_count,
                    "disaster_type": disaster_type,
                    "logistics": logistics,
                    "lon": float(desa_geom.centroid.x),
                    "lat": float(desa_geom.centroid.y),
                })
            except Exception:
                continue

    # Kumpulkan jenis bencana unik
    disaster_types = list(set(r['disaster_type'] for r in rz_data if 'disaster_type' in r))
    disaster_summary = ', '.join(sorted(disaster_types)) if disaster_types else 'Bencana Alam'

    # Hitung total logistik
    total_damage = int(len(df_raw))
    total_logistics = {
        "beras": total_damage * services.LOGISTIK_PER_KK['Beras (kg)'],
        "air": total_damage * services.LOGISTIK_PER_KK['Air Minum (liter)'],
        "mie": total_damage * services.LOGISTIK_PER_KK['Mie Instan (Dus)'],
        "minyak": total_damage * services.LOGISTIK_PER_KK['Minyak Goreng (liter)'],
        "lauk": total_damage * services.LOGISTIK_PER_KK['Lauk Kaleng (paket)'],
    }

    return {
        "disaster_info": {
            "types": disaster_types,
            "summary": disaster_summary,
        },
        "metrics": {
            "active_areas": int(df_raw[desa_col].nunique()),
            "total_damage": total_damage,
            "estimated_impacts": total_damage * 4,
        },
        "total_logistics": total_logistics,
        "map_data": {
            "red_zones": rz_data,
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
