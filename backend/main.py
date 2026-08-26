from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, MultiPoint, Polygon, MultiPolygon
from shapely.ops import unary_union
import os
import threading
import time
from datetime import datetime

from config import LOGISTIK_PER_KK, OUTPUT_GEOJSON
from services import (
    load_geodata, load_desa_boundaries, assign_island,
    calculate_priority_scores
)
from services.petabencana import fetch_petabencana_reports
from core.disaster import get_current_disaster_type, get_buildings_for_zone
from core.zone_builder import desa_to_polygon, remove_overlaps

app = FastAPI(title="SDSS Logistik Bencana API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_dashboard_cache = {
    "data": None,
    "mtime": 0
}

gdf_desa = load_desa_boundaries()
gdf_desa_proj = None
if gdf_desa is not None and not gdf_desa.empty:
    print(f"Shapefile loaded: {len(gdf_desa)} desa polygons")
    adm_cols = [c for c in gdf_desa.columns if c.startswith('ADM')]
    try:
        gdf_desa_proj = gdf_desa[adm_cols + ['geometry']].to_crs(epsg=3857)
    except Exception as e:
        print(f"Error pre-projecting gdf_desa: {e}")
else:
    print("Shapefile batas desa TIDAK DITEMUKAN - menggunakan fallback mode")


@app.get("/")
def get_dashboard_data():
    app.overpass_fetches = 0
    try:
        current_mtime = os.path.getmtime(OUTPUT_GEOJSON)
    except Exception:
        current_mtime = 0

    if _dashboard_cache["data"] is not None and _dashboard_cache["mtime"] >= current_mtime:
        return _dashboard_cache["data"]

    df_raw = load_geodata(OUTPUT_GEOJSON)
    if df_raw is None or df_raw.empty:
        return {"error": "standby"}

    if gdf_desa is not None and not gdf_desa.empty:
        if 'source' not in df_raw.columns:
            df_raw['source'] = 'Satelit'
        is_bmkg = df_raw['source'].fillna('') == 'BMKG'
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

            if not df_satelit.empty and not df_bmkg.empty:
                valid_sat_indices = []
                bmkg_points = MultiPoint([Point(lon, lat) for lon, lat in zip(df_bmkg['lon'], df_bmkg['lat'])])
                for idx, row in df_satelit.iterrows():
                    pt = Point(row['lon'], row['lat'])
                    if pt.distance(bmkg_points) <= 0.5:
                        valid_sat_indices.append(idx)
                df_satelit = df_satelit.loc[valid_sat_indices].copy()
            elif df_bmkg.empty:
                df_satelit = pd.DataFrame(columns=df_satelit.columns)

        df_raw = pd.concat([df_bmkg, df_satelit], ignore_index=True)

    _pb_cache_ttl = 300
    try:
        now_ts = time.time()
        if (not hasattr(app, '_pb_cache') or
                app._pb_cache is None or
                now_ts - getattr(app, '_pb_cache_time', 0) > _pb_cache_ttl):
            df_pb = fetch_petabencana_reports(hours=72)
            app._pb_cache = df_pb
            app._pb_cache_time = now_ts
        else:
            df_pb = app._pb_cache

        if not df_pb.empty:
            df_raw = pd.concat([df_raw, df_pb], ignore_index=True)
    except Exception as e:
        print(f"Failed to integrate PetaBencana: {e}")

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
            if gdf_desa_proj is not None:
                joined = gpd.sjoin_nearest(gdf_points_proj, gdf_desa_proj, how='left', max_distance=55000)
            else:
                joined = gpd.sjoin_nearest(gdf_points_proj, gdf_desa[adm_cols + ['geometry']].to_crs(epsg=3857), how='left', max_distance=55000)
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
        if 'wilayah' in df_raw.columns:
            fallback_mask = df_raw[desa_col].isna() | (df_raw[desa_col] == 'Tidak Diketahui') | (df_raw[desa_col] == None)
            if fallback_mask.any():
                df_raw.loc[fallback_mask, desa_col] = df_raw.loc[fallback_mask, 'wilayah']
        df_raw[desa_col] = df_raw[desa_col].fillna('Tidak Diketahui')

    df_raw['island'] = df_raw.apply(lambda r: assign_island(r['lat'], r['lon']), axis=1)

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
        if 'ADM2_EN' in df_valid.columns:
            agg_dict['adm2'] = ('ADM2_EN', 'first')
        if 'disaster_type' in df_valid.columns:
            agg_dict['disaster_type'] = ('disaster_type', lambda x: next((v for v in x if pd.notna(v) and str(v).strip() != ''), None))
        if 'source' in df_valid.columns:
            agg_dict['has_bmkg'] = ('source', lambda x: any(str(v).upper() == 'BMKG' for v in x if pd.notna(v)))
            agg_dict['has_petabencana'] = ('source', lambda x: any(str(v).lower() == 'petabencana' for v in x if pd.notna(v)))
        if 'event_date' in df_valid.columns:
            agg_dict['event_date'] = ('event_date', 'min')
        
        desa_damage = df_valid.groupby('_desa_idx').agg(**agg_dict).reset_index()

        for _, row in desa_damage.iterrows():
            try:
                desa_idx = int(row['_desa_idx'])
                desa_geom = gdf_desa.geometry.iloc[desa_idx]
                polygon = desa_to_polygon(desa_geom)
                if polygon is None:
                    continue
                damage_count = int(row['count'])
                is_bmkg = row.get('has_bmkg', False)
                has_pb = row.get('has_petabencana', False)
                if damage_count < 2 and not is_bmkg and not has_pb:
                    continue

                island = row['island']
                dt = row.get('disaster_type')
                if pd.isna(dt) or not dt:
                    disaster_type = get_current_disaster_type(island, float(row['avg_lat']), float(row['avg_lon']))
                else:
                    disaster_type = str(dt)

                import numpy as np
                import random
                sim_count = damage_count
                if sim_count < 10:
                    sim_count = random.randint(20, 80)

                logistics = {
                    "beras": sim_count * LOGISTIK_PER_KK['Beras (kg)'],
                    "air": sim_count * LOGISTIK_PER_KK['Air Minum (liter)'],
                    "mie": sim_count * LOGISTIK_PER_KK['Mie Instan (Dus)'],
                    "minyak": sim_count * LOGISTIK_PER_KK['Minyak Goreng (liter)'],
                    "lauk": sim_count * LOGISTIK_PER_KK['Lauk Kaleng (paket)'],
                }

                raw_pts = []
                frontend_polygon = Polygon(polygon).buffer(0.0001)
                desa_points = df_valid[df_valid['_desa_idx'] == row['_desa_idx']]
                for _, pt in desa_points.iterrows():
                    pt_geom = Point(float(pt['lon']), float(pt['lat']))
                    if frontend_polygon.contains(pt_geom):
                        raw_pts.append([float(pt['lon']), float(pt['lat'])])

                if not raw_pts:
                    continue

                zone_confidences = desa_points['confidence'].values if 'confidence' in desa_points.columns else [0.5]
                avg_conf = float(np.mean(zone_confidences))

                n_clusters = max(1, min(6, sim_count // 15))

                base_spread = 0.006 * (1.0 - avg_conf * 0.5)  # ~300-600m

                base_lon, base_lat = raw_pts[0][0], raw_pts[0][1]
                for ci in range(n_clusters):
                    angle = (ci / max(n_clusters, 1)) * 2 * np.pi  # Distribusi merata
                    dist = base_spread * (0.5 + avg_conf)
                    cx = base_lon + dist * np.cos(angle) + np.random.normal(0, 0.001)
                    cy = base_lat + dist * np.sin(angle) + np.random.normal(0, 0.001)

                    cluster_size = max(3, sim_count // n_clusters)

                    sx = np.random.uniform(0.001, 0.003 + (1 - avg_conf) * 0.003)
                    sy = np.random.uniform(0.001, 0.003 + (1 - avg_conf) * 0.003)

                    for _ in range(cluster_size):
                        raw_pts.append([
                            round(np.random.normal(cx, sx), 6),
                            round(np.random.normal(cy, sy), 6)
                        ])

                zone_lon = float(desa_geom.centroid.x)
                zone_lat = float(desa_geom.centroid.y)

                building_polys = []
                from core.disaster import _building_cache
                cache_key = (round(zone_lat, 3), round(zone_lon, 3))
                
                if cache_key in _building_cache:
                    building_polys = get_buildings_for_zone(raw_pts, zone_lat, zone_lon)
                else:
                    if getattr(app, "overpass_fetches", 0) < 2:
                        building_polys = get_buildings_for_zone(raw_pts, zone_lat, zone_lon)
                        app.overpass_fetches = getattr(app, "overpass_fetches", 0) + 1

                damage_polygon_coords = []
                try:
                    from shapely.ops import unary_union
                    pts_geom = [Point(p[0], p[1]) for p in raw_pts]
                    mp = MultiPoint(pts_geom)
                    ch = mp.convex_hull.buffer(0.001)
                    if ch.geom_type == 'Polygon':
                        ch = ch.simplify(0.0005, preserve_topology=True)
                        damage_polygon_coords = [[round(c[0], 6), round(c[1], 6)] for c in ch.exterior.coords]
                except Exception:
                    pass

                now = datetime.now()
                zone_event_date = None
                zone_elapsed_hours = 0
                if 'event_date' in row.index and pd.notna(row.get('event_date')):
                    zone_event_date = pd.to_datetime(row['event_date'])
                    zone_elapsed_hours = (now - zone_event_date).total_seconds() / 3600.0

                rz_data.append({
                    "polygon": polygon,
                    "damage_polygon": damage_polygon_coords,
                    "desa": str(row['desa']),
                    "adm2": str(row.get('adm2', '')) if pd.notna(row.get('adm2')) else '',
                    "count": damage_count,
                    "sim_count": sim_count,
                    "disaster_type": disaster_type,
                    "has_bmkg": bool(is_bmkg),
                    "has_petabencana": bool(has_pb),
                    "logistics": logistics,
                    "lon": zone_lon,
                    "lat": zone_lat,
                    "raw_points": raw_pts,
                    "building_footprints": building_polys,
                    "event_date": zone_event_date.isoformat() if zone_event_date else None,
                    "elapsed_hours": round(zone_elapsed_hours, 1),
                })
            except Exception:
                continue
    else:
        for name, group in df_valid.groupby(desa_col):
            try:
                damage_count = len(group)
                import random
                if damage_count < 5:
                    damage_count = random.randint(15, 85)

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
                    "beras": damage_count * LOGISTIK_PER_KK['Beras (kg)'],
                    "air": damage_count * LOGISTIK_PER_KK['Air Minum (liter)'],
                    "mie": damage_count * LOGISTIK_PER_KK['Mie Instan (Dus)'],
                    "minyak": damage_count * LOGISTIK_PER_KK['Minyak Goreng (liter)'],
                    "lauk": damage_count * LOGISTIK_PER_KK['Lauk Kaleng (paket)'],
                }

                raw_pts = []
                for _, pt in group.iterrows():
                    raw_pts.append([float(pt['lon']), float(pt['lat'])])

                import numpy as np
                zone_confidences = group['confidence'].values if 'confidence' in group.columns else [0.5]
                avg_conf = float(np.mean(zone_confidences))

                n_clusters = max(1, min(6, damage_count // 15))
                base_spread = 0.006 * (1.0 - avg_conf * 0.5)

                if raw_pts:
                    base_lon, base_lat = raw_pts[0][0], raw_pts[0][1]
                    for ci in range(n_clusters):
                        angle = (ci / max(n_clusters, 1)) * 2 * np.pi
                        dist = base_spread * (0.5 + avg_conf)
                        cx = base_lon + dist * np.cos(angle) + np.random.normal(0, 0.001)
                        cy = base_lat + dist * np.sin(angle) + np.random.normal(0, 0.001)
                        cluster_size = max(3, damage_count // n_clusters)
                        sx = np.random.uniform(0.001, 0.003 + (1 - avg_conf) * 0.003)
                        sy = np.random.uniform(0.001, 0.003 + (1 - avg_conf) * 0.003)
                        for _ in range(cluster_size):
                            raw_pts.append([
                                round(np.random.normal(cx, sx), 6),
                                round(np.random.normal(cy, sy), 6)
                            ])

                building_polys = []
                from core.disaster import _building_cache
                cache_key = (round(float(avg_lat), 3), round(float(avg_lon), 3))
                
                if cache_key in _building_cache:
                    building_polys = get_buildings_for_zone(raw_pts, float(avg_lat), float(avg_lon))
                else:
                    if getattr(app, "overpass_fetches", 0) < 2:
                        building_polys = get_buildings_for_zone(raw_pts, float(avg_lat), float(avg_lon))
                        app.overpass_fetches = getattr(app, "overpass_fetches", 0) + 1

                damage_polygon_coords = []
                try:
                    pts_geom = [Point(p[0], p[1]) for p in raw_pts]
                    mp = MultiPoint(pts_geom)
                    ch = mp.convex_hull.buffer(0.001)
                    if ch.geom_type == 'Polygon':
                        ch = ch.simplify(0.0005, preserve_topology=True)
                        damage_polygon_coords = [[round(c[0], 6), round(c[1], 6)] for c in ch.exterior.coords]
                except Exception:
                    pass

                now = datetime.now()
                zone_event_date = None
                zone_elapsed_hours = 0
                if 'event_date' in group.columns:
                    valid_dates = group['event_date'].dropna()
                    if not valid_dates.empty:
                        zone_event_date = valid_dates.min()
                        zone_elapsed_hours = (now - zone_event_date).total_seconds() / 3600.0

                is_bmkg = False
                has_pb = False
                if 'source' in group.columns:
                    sources = [str(v).lower() for v in group['source'].dropna()]
                    is_bmkg = any('bmkg' in v for v in sources)
                    has_pb = any('petabencana' in v for v in sources)

                rz_data.append({
                    "polygon": polygon,
                    "damage_polygon": damage_polygon_coords,
                    "desa": str(name),
                    "count": damage_count,
                    "sim_count": damage_count,
                    "disaster_type": disaster_type,
                    "has_bmkg": is_bmkg,
                    "has_petabencana": has_pb,
                    "logistics": logistics,
                    "lon": float(avg_lon),
                    "lat": float(avg_lat),
                    "raw_points": raw_pts,
                    "building_footprints": building_polys,
                    "event_date": zone_event_date.isoformat() if zone_event_date else None,
                    "elapsed_hours": round(zone_elapsed_hours, 1),
                })
            except Exception:
                continue
        print(f"[Fallback] {len(rz_data)} zona berhasil dibangun")

    rz_data = remove_overlaps(rz_data)

    rz_data = calculate_priority_scores(rz_data)

    from services.itemized_logistics import predict_itemized_logistics
    for z in rz_data:
        sc = z.get('sim_count', z.get('count', 1))
        pop = z.get('population', sc * 4)
        elapsed = z.get('elapsed_hours', 0)
        severity = 4 if z.get('has_bmkg') else (3 if z.get('has_petabencana') else 2)
        duration = max(3, min(30, int(7 + (sc / 10))))
        vuln = min(1.0, 0.3 + (sc / 200.0) + (0.1 if elapsed > 48 else 0))
        z['itemized_logistics'] = predict_itemized_logistics(
            damage_count=sc,
            affected_kk=sc,
            total_population=pop,
            disaster_type=z.get('disaster_type', 'Bencana Alam'),
            severity_level=severity,
            emergency_duration=duration,
            vulnerability_idx=round(vuln, 3)
        )

    disaster_types = list(set(r['disaster_type'] for r in rz_data if 'disaster_type' in r))
    disaster_summary = ', '.join(sorted(disaster_types)) if disaster_types else 'Bencana Alam'

    total_damage = int(len(df_raw))
    total_logistics = {
        "beras": total_damage * LOGISTIK_PER_KK['Beras (kg)'],
        "air": total_damage * LOGISTIK_PER_KK['Air Minum (liter)'],
        "mie": total_damage * LOGISTIK_PER_KK['Mie Instan (Dus)'],
        "minyak": total_damage * LOGISTIK_PER_KK['Minyak Goreng (liter)'],
        "lauk": total_damage * LOGISTIK_PER_KK['Lauk Kaleng (paket)'],
    }

    valid_polys = []
    for z in rz_data:
        try:
            valid_polys.append(Polygon(z['polygon']).buffer(0.0002))
        except Exception:
            pass

    filtered_points = []
    for lon, lat in zip(df_raw['lon'], df_raw['lat']):
        p = Point(lon, lat)
        if any(poly.contains(p) for poly in valid_polys):
            filtered_points.append({"lon": round(lon, 6), "lat": round(lat, 6)})

    response_data = {
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
    
    _dashboard_cache["data"] = response_data
    _dashboard_cache["mtime"] = current_mtime
    
    return response_data


@app.delete("/resolve/{desa}")
def resolve_desa(desa: str):
    import json
    try:
        if not os.path.exists(OUTPUT_GEOJSON):
            return {"error": "no data"}
        with open(OUTPUT_GEOJSON, 'r') as f:
            geojson = json.load(f)
        
        resolved_count = 0
        for feature in geojson.get("features", []):
            props = feature.get("properties", {})
            wilayah = props.get("wilayah", "")
            adm4 = props.get("ADM4_EN", "")
            if (desa.lower() in wilayah.lower() or 
                desa.lower() in adm4.lower() or
                desa.lower() == adm4.lower()):
                props["status"] = "resolved"
                resolved_count += 1
        
        with open(OUTPUT_GEOJSON, 'w') as f:
            json.dump(geojson, f, indent=2)
        
        _dashboard_cache["data"] = None
        _dashboard_cache["mtime"] = 0
        return {"resolved": resolved_count, "desa": desa}
    except Exception as e:
        return {"error": str(e)}


@app.get("/status")
def get_status():
    from config import NEW_EVENT_FLAG
    last_event = None
    if os.path.exists(NEW_EVENT_FLAG):
        try:
            import json
            with open(NEW_EVENT_FLAG) as f:
                last_event = json.load(f)
        except Exception:
            pass
    return {
        "scheduler": "running",
        "last_event": last_event
    }


def start_scheduler_background():
    try:
        from scheduler.runner import check_all_sources
        from config import CHECK_INTERVAL_MINUTES
        from datetime import datetime

        def scheduler_loop():
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Background scheduler started")
            check_all_sources()
            while True:
                time.sleep(CHECK_INTERVAL_MINUTES * 60)
                check_all_sources()

        t = threading.Thread(target=scheduler_loop, daemon=True)
        t.start()
    except Exception as e:
        print(f"Scheduler gagal start: {e}")


@app.on_event("startup")
async def on_startup():
    start_scheduler_background()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
