from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist
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

    if gdf_desa is not None and not gdf_desa.empty:
        gdf_points = gpd.GeoDataFrame(df_raw, geometry=[Point(lon, lat) for lon, lat in zip(df_raw['lon'], df_raw['lat'])], crs="EPSG:4326")
        joined = gpd.sjoin(gdf_points, gdf_desa[['geometry']], how='inner', predicate='within')
        df_raw = df_raw.loc[df_raw.index.isin(joined.index.unique())].copy()

    if df_raw.empty: return {"error": "no_land_points"}

    conf_thresh = 0.2
    df_raw = df_raw[df_raw['confidence'] >= conf_thresh].copy()
    if df_raw.empty: return {"error": "no_confident_points"}

    desa_col = None
    if gdf_desa is not None and not gdf_desa.empty:
        adm_cols = [c for c in gdf_desa.columns if c.startswith('ADM')]
        if adm_cols:
            gdf_points_proj = gpd.GeoDataFrame(df_raw, geometry=[Point(lon, lat) for lon, lat in zip(df_raw['lon'], df_raw['lat'])], crs="EPSG:4326").to_crs(epsg=3857)
            gdf_desa_proj = gdf_desa[adm_cols + ['geometry']].to_crs(epsg=3857)
            joined = gpd.sjoin_nearest(gdf_points_proj, gdf_desa_proj, how='left', max_distance=55000)
            joined = joined[~joined.index.duplicated(keep='first')]
            if 'index_right' in joined.columns:
                df_raw['_desa_idx'] = joined['index_right'].values
            for col in adm_cols:
                if col in joined.columns: df_raw[col] = joined[col].values
            desa_col = next((c for c in ['ADM4_EN', 'ADM3_EN', 'ADM2_EN'] if c in df_raw.columns and df_raw[c].notna().any()), None)
    
    if not desa_col:
        df_raw['_desa'] = 'Tidak Diketahui'
        desa_col = '_desa'
    else:
        df_raw[desa_col] = df_raw[desa_col].fillna('Tidak Diketahui')

    df_raw['island'] = df_raw.apply(lambda r: services.assign_island(r['lat'], r['lon']), axis=1)

    cluster_offset = 0
    for island_name, island_df in df_raw.groupby('island'):
        coords_i = island_df[['lat', 'lon']].values
        lat_span_km = (island_df['lat'].max() - island_df['lat'].min()) * 111.32
        lon_span_km = (island_df['lon'].max() - island_df['lon'].min()) * 111.32 * np.cos(np.radians(island_df['lat'].mean()))
        span_km = max(lat_span_km, lon_span_km)
        n_load = int(np.ceil(len(coords_i) / 6.0))
        n_span = int(np.ceil(span_km / 140.0)) if span_km > 0 else 1
        n = max(n_load, n_span)
        if len(coords_i) >= 4 and span_km >= 18: n = max(n, 2)
        if len(coords_i) >= 8 and span_km >= 35: n = max(n, 3)
        n = min(max(1, min(n, 12)), len(coords_i))
        labels = KMeans(n_clusters=n, random_state=42, n_init=10).fit_predict(coords_i)
        df_raw.loc[island_df.index, 'cluster_id'] = labels + cluster_offset
        cluster_offset += n
    df_raw['cluster_id'] = df_raw['cluster_id'].astype(int)

    cluster_centers = df_raw.groupby('cluster_id').agg(
        center_lat=('lat', 'mean'), center_lon=('lon', 'mean'), jumlah_red=('lat', 'count'),
        avg_confidence=('confidence', 'max'), island=('island', 'first'), # <-- INI PERUBAHANNYA: Mean menjadi Max
        desa_list=(desa_col, lambda x: ', '.join(x.dropna().unique()))
    ).reset_index()

    safe_pos = []
    for _, row in cluster_centers.iterrows():
        slon, slat = services.snap_to_road(round(row['center_lon'], 5), round(row['center_lat'], 5), 150)
        safe_pos.append({'cluster_id': row['cluster_id'], 'safe_lon': slon, 'safe_lat': slat})
    cluster_centers = cluster_centers.merge(pd.DataFrame(safe_pos), on='cluster_id')

    df_hubs = services.merge_nearby_hubs(cluster_centers, min_dist_m=600)
    hub_status = services.load_status()
    active_ids = [r['hub_id'] for _, r in df_hubs.iterrows() if not hub_status.get(f"hub_{int(r['hub_id'])}", False)]
    df_hubs_active = df_hubs[df_hubs['hub_id'].isin(active_ids)].copy()

    if df_hubs_active.empty: return {"error": "done"}

    dist_matrix = cdist(df_raw[['lat', 'lon']].values, df_hubs_active[['safe_lat', 'safe_lon']].values)
    valid_mask = dist_matrix.min(axis=0) < 1.2
    df_hubs_active = df_hubs_active[valid_mask].copy().reset_index(drop=True)
    if df_hubs_active.empty: return {"error": "no_valid_hubs"}

    def assign_nearest_hub(row, hubs):
        island_hubs = hubs[hubs['island'] == row['island']]
        target_hubs = island_hubs if not island_hubs.empty else hubs
        dists = cdist([[row['lat'], row['lon']]], target_hubs[['safe_lat', 'safe_lon']].values)
        return target_hubs.iloc[dists.argmin()]['hub_id']

    df_raw['hub_id'] = df_raw.apply(lambda r: assign_nearest_hub(r, df_hubs_active), axis=1)
    df_mapped = df_raw.merge(df_hubs_active[['hub_id', 'safe_lon', 'safe_lat', 'island']], on='hub_id', suffixes=('', '_hub'))

    red_zones = df_mapped.groupby('cluster_id').agg(
        lon=('lon', 'mean'), lat=('lat', 'mean'), desa=(desa_col, lambda x: ', '.join(pd.Series(x).dropna().unique())),
        confidence=('confidence', 'max'), jumlah=('lat', 'count'), hub_id=('hub_id', 'first'), # <-- INI PERUBAHANNYA: Mean menjadi Max
        safe_lon=('safe_lon', 'first'), safe_lat=('safe_lat', 'first'), island_hub=('island_hub', 'first'), round_island=('island', 'first')
    ).reset_index()

    path_outline, path_blue, path_blue_link, path_fallback, path_air_line = [], [], [], [], []
    hub_dists = {hid: [] for hid in active_ids}
    
    for i, row in red_zones.iterrows():
        hid = row['hub_id']
        if services.haversine_distance_m(row['safe_lat'], row['safe_lon'], row['lat'], row['lon']) < 300:
            if hid in hub_dists: hub_dists[hid].append(0)
            continue
            
        pts, dist_m = services.get_route_info(row['safe_lon'], row['safe_lat'], row['lon'], row['lat'])
        mode, effective_dist = services.choose_route_mode(
            row['safe_lon'], row['safe_lat'], row['lon'], row['lat'],
            row['island_hub'], row['round_island'], pts, dist_m
        )

        d_name = row.get('desa', '')
        if mode == 'road':
            if pts is not None and len(pts) >= 2:
                path_outline.append({'path': pts})
                path_blue.append({'path': pts, 'desa': d_name})
                if services.haversine_distance_m(row['safe_lat'], row['safe_lon'], pts[0][1], pts[0][0]) > 50:
                    path_blue_link.append({'path': [[row['safe_lon'], row['safe_lat']], pts[0]], 'desa': d_name})
                if services.haversine_distance_m(pts[-1][1], pts[-1][0], row['lat'], row['lon']) > 50:
                    path_blue_link.append({'path': [pts[-1], [row['lon'], row['lat']]], 'desa': d_name})
            else:
                p = [[row['safe_lon'], row['safe_lat']], [row['lon'], row['lat']]]
                path_outline.append({'path': p})
                path_blue.append({'path': p, 'desa': d_name})
            if hid in hub_dists: hub_dists[hid].append(effective_dist)
        else:
            path_air_line.append({'path': [[row['safe_lon'], row['safe_lat']], [row['lon'], row['lat']]], 'desa': d_name})
            path_fallback.append({'source': [row['safe_lon'], row['safe_lat']], 'target': [row['lon'], row['lat']], 'desa': d_name})
            if hid in hub_dists: hub_dists[hid].append(effective_dist)

    # Hitung jangkauan berdasarkan jarak hub ke tiap titik kerusakan yang dilayani
    def compute_hub_coverage(hid):
        hub_row = df_hubs_active[df_hubs_active['hub_id'] == hid]
        if hub_row.empty:
            return 0
        hub_row = hub_row.iloc[0]
        pts = df_raw[df_raw['hub_id'] == hid]
        if pts.empty:
            return 0
        dists = pts.apply(
            lambda r: services.haversine_distance_m(hub_row['safe_lat'], hub_row['safe_lon'], r['lat'], r['lon']),
            axis=1
        )
        return round(dists.mean() / 1000, 2)

    df_hubs_active['jarak_rata_km'] = df_hubs_active['hub_id'].apply(compute_hub_coverage)
    
    df_hubs_active['priority_score'] = df_hubs_active.apply(
        lambda r: round(r['jumlah_red'] / max(r.get('jarak_rata_km', 0.1) or 0.1, 0.1), 1), axis=1
    )
    df_hubs_active = df_hubs_active.sort_values('priority_score', ascending=False)

    hubs_data = []
    for _, h in df_hubs_active.iterrows():
        damage_val = int(h['jumlah_red'])
        hubs_data.append({
            "id": int(h['hub_id']),
            "desa": str(h['desa_list']),
            "damage": damage_val,
            "confidence": f"{(h['avg_confidence']*100):.1f}%",
            "distance": h.get('jarak_rata_km', 0),
            "priority": "TINGGI",
            "lon": float(h['safe_lon']),
            "lat": float(h['safe_lat']),
            "logistics": {
                "beras": damage_val * services.LOGISTIK_PER_KK['Beras (kg)'],
                "air": damage_val * services.LOGISTIK_PER_KK['Air Minum (liter)'],
                "mie": damage_val * services.LOGISTIK_PER_KK['Mie Instan (Dus)'],
                "minyak": damage_val * services.LOGISTIK_PER_KK['Minyak Goreng (liter)'],
                "lauk": damage_val * services.LOGISTIK_PER_KK['Lauk Kaleng (paket)']
            }
        })

    # === Bangun zona kerusakan berdasarkan batas desa ===
    rz_data = []
    if gdf_desa is not None and '_desa_idx' in df_mapped.columns:
        desa_damage = df_mapped.groupby('_desa_idx').agg(
            count=('lat', 'count'),
            desa=(desa_col, 'first'),
            island=('island', 'first'),
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
                rz_data.append({
                    "polygon": polygon,
                    "desa": str(row['desa']),
                    "count": int(row['count']),
                    "disaster_type": disaster_type,
                    "lon": float(desa_geom.centroid.x),
                    "lat": float(desa_geom.centroid.y),
                })
            except Exception:
                continue

    # Kumpulkan jenis bencana unik untuk info
    disaster_types = list(set(r['disaster_type'] for r in rz_data if 'disaster_type' in r))
    disaster_summary = ', '.join(sorted(disaster_types)) if disaster_types else 'Bencana Alam'

    return {
        "disaster_info": {
            "types": disaster_types,
            "summary": disaster_summary,
        },
        "metrics": {
            "active_areas": int(df_mapped[desa_col].nunique()),
            "total_damage": int(len(df_mapped)),
            "estimated_impacts": int(df_hubs_active['jumlah_red'].sum() * 4),
            "total_hubs": len(df_hubs_active)
        },
        "hubs": hubs_data,
        "map_data": {
            "red_zones": rz_data,
            "paths": {
                "outline": path_outline,
                "blue": path_blue,
                "link": path_blue_link,
                "air": path_air_line,
                "fallback": path_fallback
            }
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
