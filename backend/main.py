from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
import numpy as np
import services
from shapely.geometry import Point, box, MultiPoint
from shapely.ops import unary_union
import geopandas as gpd
import os
import threading

app = FastAPI(title="SDSS Logistik Bencana API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    'other': 'Banjir / Tanah Longsor',
}

def get_current_disaster_type(island_fallback='other', lat=None, lon=None):
    import json
    flag_path = "output/new_event.flag"
    try:
        if os.path.exists(flag_path) and lat is not None and lon is not None:
            with open(flag_path) as f:
                event = json.load(f)
            event_data = event.get("event", {})
            event_type = event_data.get("type", "")
            event_lat = event_data.get("lat")
            event_lon = event_data.get("lon")
            if event_type and event_lat is not None and event_lon is not None:
                dist = ((lat - event_lat)**2 + (lon - event_lon)**2)**0.5
                if dist < 2.0:
                    return event_type
    except Exception:
        pass
    return DISASTER_BY_ISLAND.get(island_fallback, 'Banjir / Tanah Longsor')

def desa_to_polygon(geom, simplify_tol=0.0005, shrink_m=50):
    try:
        simplified = geom.simplify(simplify_tol, preserve_topology=True).buffer(0)
        if simplified.is_empty:
            return None
        shrink_deg = shrink_m / 111320.0
        shrunk = simplified.buffer(-shrink_deg)
        if shrunk.is_empty:
            shrunk = simplified
        target = shrunk
        if target.geom_type == 'MultiPolygon':
            largest = max(target.geoms, key=lambda p: p.area)
            return [[round(c[0], 6), round(c[1], 6)] for c in largest.exterior.coords]
        elif target.geom_type == 'Polygon':
            return [[round(c[0], 6), round(c[1], 6)] for c in target.exterior.coords]
    except Exception:
        pass
    return None

def remove_overlaps(zone_list):
    from shapely.geometry import Polygon as ShapelyPolygon
    geoms = []
    valid_indices = []
    for i, z in enumerate(zone_list):
        try:
            poly = ShapelyPolygon(z['polygon'])
            if poly.is_valid and not poly.is_empty:
                geoms.append(poly)
                valid_indices.append(i)
        except Exception:
            continue

    if len(geoms) <= 1:
        return zone_list

    result = []
    claimed = None
    for idx, gi in enumerate(geoms):
        if claimed is None:
            cleaned = gi
        else:
            cleaned = gi.difference(claimed)
        if cleaned.is_empty:
            continue
        if cleaned.geom_type == 'MultiPolygon':
            cleaned = max(cleaned.geoms, key=lambda p: p.area)
        if cleaned.is_empty or cleaned.geom_type != 'Polygon':
            continue
        z = zone_list[valid_indices[idx]].copy()
        z['polygon'] = [[round(c[0], 6), round(c[1], 6)] for c in cleaned.exterior.coords]
        result.append(z)
        if claimed is None:
            claimed = cleaned
        else:
            claimed = claimed.union(cleaned)

    return result

print("Loading geodata boundaries...")
gdf_desa = services.load_desa_boundaries()
if gdf_desa is not None and not gdf_desa.empty:
    print(f"  Shapefile loaded: {len(gdf_desa)} desa polygons")
else:
    print("  Shapefile batas desa TIDAK DITEMUKAN - menggunakan fallback mode")

@app.get("/")
def get_dashboard_data():
    df_raw = services.load_geodata(services.OUTPUT_GEOJSON)
    if df_raw is None or df_raw.empty:
        return {"error": "standby"}

    if gdf_desa is not None and not gdf_desa.empty:
        is_bmkg = df_raw.get('source', pd.Series(dtype=str)).fillna('') == 'BMKG'
        df_bmkg = df_raw[is_bmkg].copy()
        df_satelit = df_raw[~is_bmkg].copy()

        if not df_satelit.empty:
            gdf_points = gpd.GeoDataFrame(
                df_satelit,
                geometry=[Point(lon, lat) for lon, lat in zip(df_satelit['lon'], df_satelit['lat'])],
                crs="EPSG:4326"
            )
            joined = gpd.sjoin(gdf_points, gdf_desa[['geometry']], how='inner', predicate='within')
            df_satelit = df_satelit.loc[df_satelit.index.isin(joined.index.unique())].copy()

        df_raw = pd.concat([df_bmkg, df_satelit], ignore_index=True)

    if df_raw.empty:
        return {"error": "no_land_points"}

    conf_thresh = 0.2
    df_raw = df_raw[df_raw['confidence'] >= conf_thresh].copy()
    if df_raw.empty:
        return {"error": "no_confident_points"}

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
        if 'wilayah' in df_raw.columns and df_raw['wilayah'].notna().any():
            desa_col = 'wilayah'
        else:
            df_raw['_desa'] = 'Tidak Diketahui'
            desa_col = '_desa'
    else:
        df_raw[desa_col] = df_raw[desa_col].fillna('Tidak Diketahui')

    df_raw['island'] = df_raw.apply(lambda r: services.assign_island(r['lat'], r['lon']), axis=1)

    rz_data = []
    df_valid = df_raw[df_raw[desa_col] != 'Tidak Diketahui'].copy()
    if gdf_desa is not None and not gdf_desa.empty and '_desa_idx' in df_valid.columns:
        agg_dict = {
            'count': ('lat', 'count'),
            'desa': (desa_col, 'first'),
            'island': ('island', 'first'),
            'avg_lon': ('lon', 'mean'),
            'avg_lat': ('lat', 'mean')
        }
        if 'disaster_type' in df_valid.columns:
            agg_dict['disaster_type'] = ('disaster_type', lambda x: next((v for v in x if pd.notna(v) and str(v).strip() != ''), None))
        
        desa_damage = df_valid.groupby('_desa_idx').agg(**agg_dict).reset_index()

        for _, row in desa_damage.iterrows():
            try:
                desa_idx = int(row['_desa_idx'])
                desa_geom = gdf_desa.geometry.iloc[desa_idx]
                polygon = desa_to_polygon(desa_geom)
                if polygon is None:
                    continue
                damage_count = int(row['count'])
                if damage_count < 2:
                    continue

                island = row['island']
                dt = row.get('disaster_type')
                if pd.isna(dt) or not dt:
                    disaster_type = get_current_disaster_type(island, float(row['avg_lat']), float(row['avg_lon']))
                else:
                    disaster_type = str(dt)

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
    else:
        print("  [Fallback] Membangun zona kerusakan tanpa shapefile...")

        for name, group in df_valid.groupby(desa_col):
            try:
                damage_count = len(group)
                if damage_count < 2:
                    continue

                island = group['island'].iloc[0]
                avg_lat = group['lat'].mean()
                avg_lon = group['lon'].mean()
                
                dt_list = [v for v in group.get('disaster_type', []) if pd.notna(v) and str(v).strip() != '']
                dt = dt_list[0] if dt_list else None
                if pd.isna(dt) or not dt:
                    disaster_type = get_current_disaster_type(island, float(avg_lat), float(avg_lon))
                else:
                    disaster_type = str(dt)

                points = [Point(lon, lat) for lon, lat in zip(group['lon'], group['lat'])]
                if damage_count == 2:
                    geom = MultiPoint(points).buffer(0.001)
                else:
                    geom = MultiPoint(points).convex_hull.buffer(0.001)

                if geom.geom_type == 'Polygon':
                    polygon = [[round(c[0], 6), round(c[1], 6)] for c in geom.exterior.coords]
                elif geom.geom_type == 'MultiPolygon':
                    largest = max(geom.geoms, key=lambda p: p.area)
                    polygon = [[round(c[0], 6), round(c[1], 6)] for c in largest.exterior.coords]
                else:
                    continue

                logistics = {
                    "beras": damage_count * services.LOGISTIK_PER_KK['Beras (kg)'],
                    "air": damage_count * services.LOGISTIK_PER_KK['Air Minum (liter)'],
                    "mie": damage_count * services.LOGISTIK_PER_KK['Mie Instan (Dus)'],
                    "minyak": damage_count * services.LOGISTIK_PER_KK['Minyak Goreng (liter)'],
                    "lauk": damage_count * services.LOGISTIK_PER_KK['Lauk Kaleng (paket)'],
                }

                rz_data.append({
                    "polygon": polygon,
                    "desa": str(name),
                    "count": damage_count,
                    "disaster_type": disaster_type,
                    "logistics": logistics,
                    "lon": float(avg_lon),
                    "lat": float(avg_lat),
                })
            except Exception:
                continue
        print(f"  [Fallback] {len(rz_data)} zona berhasil dibangun")

    rz_data = remove_overlaps(rz_data)

    rz_data = services.calculate_priority_scores(rz_data)

    disaster_types = list(set(r['disaster_type'] for r in rz_data if 'disaster_type' in r))
    disaster_summary = ', '.join(sorted(disaster_types)) if disaster_types else 'Banjir / Tanah Longsor'

    total_damage = int(len(df_raw))
    total_logistics = {
        "beras": total_damage * services.LOGISTIK_PER_KK['Beras (kg)'],
        "air": total_damage * services.LOGISTIK_PER_KK['Air Minum (liter)'],
        "mie": total_damage * services.LOGISTIK_PER_KK['Mie Instan (Dus)'],
        "minyak": total_damage * services.LOGISTIK_PER_KK['Minyak Goreng (liter)'],
        "lauk": total_damage * services.LOGISTIK_PER_KK['Lauk Kaleng (paket)'],
    }

    from shapely.geometry import Polygon as ShapelyPolygon
    valid_polys = []
    for z in rz_data:
        try:
            valid_polys.append(ShapelyPolygon(z['polygon']).buffer(0.0002))
        except Exception:
            pass

    filtered_points = []
    for lon, lat in zip(df_raw['lon'], df_raw['lat']):
        p = Point(lon, lat)
        if any(poly.contains(p) for poly in valid_polys):
            filtered_points.append({"lon": round(lon, 6), "lat": round(lat, 6)})

    return {
        "disaster_info": {
            "types": disaster_types,
            "summary": disaster_summary,
        },
        "metrics": {
            "active_areas": len({z['desa'] for z in rz_data}),
            "total_damage": total_damage,
            "estimated_impacts": total_damage * 4,
        },
        "total_logistics": total_logistics,
        "map_data": {
            "red_zones": rz_data,
            "raw_points": filtered_points
        }
    }


@app.get("/status")
def get_status():
    flag_path = "output/new_event.flag"
    last_event = None
    if os.path.exists(flag_path):
        try:
            import json
            with open(flag_path) as f:
                last_event = json.load(f)
        except Exception:
            pass
    return {
        "scheduler": "running",
        "last_event": last_event
    }


def start_scheduler_background():
    try:
        from scheduler import check_all_sources, CHECK_INTERVAL_MINUTES
        import time
        from datetime import datetime

        def scheduler_loop():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Background scheduler started")
            print(f"  Interval: {CHECK_INTERVAL_MINUTES} menit")
            check_all_sources()
            while True:
                time.sleep(CHECK_INTERVAL_MINUTES * 60)
                check_all_sources()

        t = threading.Thread(target=scheduler_loop, daemon=True)
        t.start()
        print("Multi-Hazard Scheduler aktif (background thread)")
    except Exception as e:
        print(f"Scheduler gagal start: {e}")
        print("  Backend tetap berjalan tanpa realtime monitoring")


@app.on_event("startup")
async def on_startup():
    start_scheduler_background()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
