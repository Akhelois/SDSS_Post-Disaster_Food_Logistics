import streamlit as st
import geopandas as gpd
import pandas as pd
import pydeck as pdk
import numpy as np
import requests
import json
import os
import datetime
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist
from shapely.geometry import Point

st.set_page_config(page_title="SDSS Logistik Bencana", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    .stApp { background: #0d1117; color: #e6edf3; }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 700 !important; color: #58a6ff !important; }
    [data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.8rem !important; }
    .legend-box {
        background: #161b22; border: 1px solid #30363d; border-radius: 10px;
        padding: 14px 18px; display: flex; gap: 24px; align-items: center;
        margin-bottom: 12px; font-size: 0.85rem; color: #8b949e;
    }
    .legend-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 6px; }
    h1 { color: #e6edf3 !important; font-weight: 700 !important; letter-spacing: -0.5px; }
    h3 { color: #8b949e !important; font-weight: 400 !important; }
    .stDownloadButton > button {
        background: #1f6feb !important; color: white !important;
        border: none !important; border-radius: 8px !important; font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] { background: #161b22 !important; border-right: 1px solid #30363d; }
    section[data-testid="stSidebar"] * { color: #e6edf3 !important; }
</style>
""", unsafe_allow_html=True)

OUTPUT_GEOJSON = "output/sdss_result.geojson"
STATUS_FILE = "output/hub_status.json"
DESA_SHP = "data/batas_desa/IDN_Final_WGS84.shp"
LOGISTIK_PER_KK = {
    'Beras (kg)': 10,
    'Air Minum (liter)': 50,
    'Mie Instan (Dus)': 2,
    'Minyak Goreng (liter)': 2,
    'Lauk Kaleng (paket)': 4,
}

ISLANDS = {
    'nias': (97.0, 0.4, 98.2, 1.6),
    'simeulue': (95.7, 2.2, 96.6, 3.1),
    'mentawai': (98.3, -3.5, 100.3, -0.9),
    'batu': (97.7, -0.8, 98.9, 0.2),
    'bangka': (105.0, -3.5, 107.0, -1.5),
    'belitung': (107.2, -3.3, 108.5, -2.5),
    'madura': (112.6, -7.3, 114.1, -6.9),
    'bali': (114.4, -8.9, 115.8, -8.0),
    'lombok': (115.9, -9.1, 116.9, -8.1),
    'sumatera': (95.2, -6.0, 105.8, 4.0),
    'jawa': (105.1, -8.8, 114.5, -5.8),
    'kalimantan': (108.0, -4.2, 117.8, 1.5),
    'sulawesi': (119.3, -5.7, 125.2, 1.8),
    'nusa_tenggara': (115.7, -9.0, 124.5, -7.9),
    'maluku': (124.5, -7.0, 132.0, 2.0),
    'papua': (130.5, -8.5, 140.5, -0.5),
}

ESRI_SATELLITE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"


def load_status():
    if os.path.exists(STATUS_FILE):
        try:
            content = open(STATUS_FILE).read().strip()
            return json.loads(content) if content else {}
        except Exception:
            return {}
    return {}


def save_status(d):
    os.makedirs("output", exist_ok=True)
    json.dump(d, open(STATUS_FILE, 'w'))


def get_mtime(path):
    return os.path.getmtime(path) if os.path.exists(path) else 0


def assign_island(lat, lon):
    for name, (lon_min, lat_min, lon_max, lat_max) in ISLANDS.items():
        if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
            return name
    return 'other'


def haversine_distance_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1 = np.radians(lat1)
    p2 = np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2.0) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2.0) ** 2
    return 2.0 * r * np.arcsin(np.sqrt(a))


def choose_route_mode(src_lon, src_lat, dst_lon, dst_lat, src_island, dst_island, pts, dist_m):
    geo_m = haversine_distance_m(src_lat, src_lon, dst_lat, dst_lon)
    
    # 1. Beda pulau
    if src_island != dst_island:
        return 'air', geo_m
        
    # 2. OSRM gagal
    if pts is None or dist_m is None or len(pts) == 0:
        return 'air', geo_m

    start_gap = haversine_distance_m(src_lat, src_lon, pts[0][1], pts[0][0])
    end_gap   = haversine_distance_m(dst_lat, dst_lon, pts[-1][1], pts[-1][0])
    
    # 3. Terlalu jauh dari jalan darat (titik red zone ada di tengah laut/hutan) (> 2.5 km)
    if start_gap > 2500 or end_gap > 2500:
        return 'air', geo_m

    # 4. OSRM lurus tapi panjang (ferry/jalur laut palsu)
    if len(pts) <= 2 and dist_m > 2000:
        return 'air', geo_m
        
    # 5. Cek lompatan antar waypoint (mendeteksi rute ferry yang pakai waypoint banyak)
    arr = np.asarray(pts)
    if len(arr) >= 2:
        seg_lon = np.diff(arr[:, 0]) * 111320 * np.cos(np.radians(dst_lat))
        seg_lat = np.diff(arr[:, 1]) * 111320
        max_seg_m = np.sqrt(seg_lon**2 + seg_lat**2).max()
        if max_seg_m > 2000:
            return 'air', geo_m

    # 6. Jarak OSRM terlalu jauh
    if dist_m >= 60000:
        return 'air', geo_m

    # Jika semua aman, gunakan rute darat
    return 'road', dist_m


@st.cache_data(ttl=3600, show_spinner=False)
def get_route_distance(slon, slat, elon, elat):
    try:
        r = requests.get(
            f"http://router.project-osrm.org/route/v1/driving/{slon},{slat};{elon},{elat}?overview=false",
            timeout=5)
        d = r.json()
        if d['code'] == 'Ok':
            return d['routes'][0]['distance']
    except Exception:
        pass
    return 999999


@st.cache_data(ttl=3600, show_spinner=False)
def get_route_info(slon, slat, elon, elat):
    try:
        r = requests.get(
            f"http://router.project-osrm.org/route/v1/driving/{slon},{slat};{elon},{elat}"
            f"?overview=full&geometries=geojson", timeout=8)
        d = r.json()
        if d.get('code') == 'Ok':
            coords = [[c[0], c[1]] for c in d['routes'][0]['geometry']['coordinates']]
            return coords, d['routes'][0]['distance']
    except Exception:
        pass
    return None, None


def snap_to_road(lon, lat, max_snap_m=200):
    try:
        r = requests.get(
            f"http://router.project-osrm.org/nearest/v1/driving/{lon},{lat}?number=1",
            timeout=3)
        d = r.json()
        if d['code'] == 'Ok':
            wp = d['waypoints'][0]
            snap_dist = float(wp.get('distance', 0.0))
            if snap_dist <= max_snap_m:
                return wp['location'][0], wp['location'][1]
    except Exception:
        pass
    return lon, lat


def merge_nearby_hubs(cc, min_dist_m):
    min_dist_deg = min_dist_m / 111320
    coords = cc[['safe_lat', 'safe_lon']].values
    merged, used = [], set()
    for i in range(len(coords)):
        if i in used:
            continue
        group = [i]
        for j in range(i + 1, len(coords)):
            if j not in used:
                same_island = cc.iloc[i]['island'] == cc.iloc[j]['island']
                dist = np.sqrt((coords[i][0] - coords[j][0]) ** 2 + (coords[i][1] - coords[j][1]) ** 2)
                if dist < min_dist_deg and same_island:
                    group.append(j)
                    used.add(j)
        used.add(i)
        rows = cc.iloc[group]
        all_desa = set()
        for dl in rows['desa_list'].dropna():
            for d in str(dl).split(', '):
                d = d.strip()
                if d and d != 'Tidak Diketahui':
                    all_desa.add(d)
        # KUNCI: Pilih koordinator Hub dengan kerusakan terbanyak, JANGAN di-rata-rata agar tidak terlempar ke hutan
        best_hub = rows.loc[rows['jumlah_red'].idxmax()]
        merged.append({
            'safe_lat': best_hub['safe_lat'],
            'safe_lon': best_hub['safe_lon'],
            'desa_list': ', '.join(sorted(all_desa)) if all_desa else '',
            'jumlah_red': rows['jumlah_red'].sum(),
            'avg_confidence': rows['avg_confidence'].mean(),
            'island': rows['island'].iloc[0],
            'cluster_ids': list(rows['cluster_id'])
        })
    return pd.DataFrame(merged).reset_index().rename(columns={'index': 'hub_id'})


@st.cache_data(ttl=30, show_spinner=False)
def load_geodata(path, _mtime):
    try:
        gdf = gpd.read_file(path).to_crs(epsg=4326)
        if 'status' in gdf.columns:
            gdf = gdf[gdf['status'] == 'active'].copy()
        gdf['lat'] = gdf.geometry.centroid.y
        gdf['lon'] = gdf.geometry.centroid.x
        if 'confidence' not in gdf.columns:
            gdf['confidence'] = 0.5
        return gdf
    except Exception:
        return None


@st.cache_data(ttl=600, show_spinner=False)
def load_desa_boundaries():
    if os.path.exists(DESA_SHP):
        try:
            return gpd.read_file(DESA_SHP).to_crs(epsg=4326)
        except Exception:
            pass
    return None


def filter_land_points(gdf, gdf_desa):
    if gdf_desa is not None and not gdf_desa.empty:
        gdf_points = gpd.GeoDataFrame(
            gdf, geometry=[Point(lon, lat) for lon, lat in zip(gdf['lon'], gdf['lat'])], crs="EPSG:4326"
        )
        joined = gpd.sjoin(gdf_points, gdf_desa[['geometry']], how='inner', predicate='within')
        valid_indices = joined.index.unique()
        return gdf.loc[gdf.index.isin(valid_indices)].copy()
    return gdf


def enrich_desa_names(gdf, gdf_desa):
    if gdf_desa is None or gdf_desa.empty:
        return gdf

    adm_cols = [c for c in gdf_desa.columns if c.startswith('ADM')]
    if not adm_cols:
        return gdf

    gdf_points = gpd.GeoDataFrame(
        gdf, geometry=[Point(lon, lat) for lon, lat in zip(gdf['lon'], gdf['lat'])], crs="EPSG:4326"
    )

    try:
        # Reproject ke EPSG:3857 (Web Mercator) agar sjoin_nearest pakai meter, bukan derajat
        gdf_points_proj = gdf_points.to_crs(epsg=3857)
        gdf_desa_proj = gdf_desa[adm_cols + ['geometry']].to_crs(epsg=3857)
        joined = gpd.sjoin_nearest(gdf_points_proj, gdf_desa_proj, how='left', max_distance=55000)
        joined = joined[~joined.index.duplicated(keep='first')]
        for col in adm_cols:
            if col in joined.columns:
                gdf[col] = joined[col].values
    except Exception:
        try:
            joined = gpd.sjoin(gdf_points, gdf_desa[adm_cols + ['geometry']], how='left', predicate='within')
            joined = joined[~joined.index.duplicated(keep='first')]
            for col in adm_cols:
                if col in joined.columns:
                    gdf[col] = joined[col].values
        except Exception:
            pass

    return gdf


with st.sidebar:
    st.markdown("## Parameter")
    merge_dist = st.slider("Jarak merge hub (m)", 200, 1000, 600, 50)
    snap_offset = st.slider("Offset snap ke jalan (m)", 50, 300, 150, 25)
    conf_thresh = st.slider("Min confidence tampil", 0.0, 1.0, 0.2, 0.05)
    st.markdown("---")
    if st.button("Proses Ulang", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    mtime = get_mtime(OUTPUT_GEOJSON)
    if mtime:
        ts = datetime.datetime.fromtimestamp(mtime).strftime("%d %b %Y, %H:%M:%S")
        st.caption(f"Update terakhir: {ts}")

st.title("SDSS Logistik Pangan Bencana Nasional")
st.write("---")

df_raw = load_geodata(OUTPUT_GEOJSON, get_mtime(OUTPUT_GEOJSON))

if df_raw is None or df_raw.empty:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;color:#8b949e;">
        <div style="font-size:1.2rem;font-weight:600;color:#e6edf3;margin-bottom:8px">Sistem Standby</div>
        <div>Belum ada data kerusakan aktif.<br>
        Jalankan <code>python scheduler.py</code></div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

gdf_desa = load_desa_boundaries()

df_raw = filter_land_points(df_raw, gdf_desa)

if df_raw.empty:
    st.warning("Tidak ada titik kerusakan yang berada di daratan.")
    st.stop()

df_raw = enrich_desa_names(df_raw, gdf_desa)

df_raw = df_raw[df_raw['confidence'] >= conf_thresh].copy()
if df_raw.empty:
    st.warning(f"Tidak ada titik dengan confidence >= {conf_thresh}.")
    st.stop()

desa_col = next((c for c in ['ADM4_EN', 'ADM3_EN', 'ADM2_EN'] if c in df_raw.columns
                 and df_raw[c].notna().any()), None)
if not desa_col:
    df_raw['_desa'] = 'Tidak Diketahui'
    desa_col = '_desa'
else:
    df_raw[desa_col] = df_raw[desa_col].fillna('Tidak Diketahui')

df_raw['island'] = df_raw.apply(lambda r: assign_island(r['lat'], r['lon']), axis=1)
cluster_offset = 0
for island_name, island_df in df_raw.groupby('island'):
    coords_i = island_df[['lat', 'lon']].values
    lat_span_km = (island_df['lat'].max() - island_df['lat'].min()) * 111.32
    lon_span_km = (island_df['lon'].max() - island_df['lon'].min()) * 111.32 * np.cos(np.radians(island_df['lat'].mean()))
    span_km = max(lat_span_km, lon_span_km)
    n_load = int(np.ceil(len(coords_i) / 6.0))
    n_span = int(np.ceil(span_km / 140.0)) if span_km > 0 else 1
    n = max(n_load, n_span)
    if len(coords_i) >= 4 and span_km >= 18:
        n = max(n, 2)
    if len(coords_i) >= 8 and span_km >= 35:
        n = max(n, 3)
    n = min(max(1, n), 12)
    
    # KUNCI PERBAIKAN: Mencegah error n_clusters > n_samples. 
    # Jika jarak (span_km) dipaksa besar tapi jumlah titik sedikit (karena false positive sudah bersih!), batasi n.
    n = min(n, len(coords_i))
    
    labels = KMeans(n_clusters=n, random_state=42, n_init=10).fit_predict(coords_i)
    df_raw.loc[island_df.index, 'cluster_id'] = labels + cluster_offset
    cluster_offset += n
df_raw['cluster_id'] = df_raw['cluster_id'].astype(int)

cluster_centers = df_raw.groupby('cluster_id').agg(
    center_lat=('lat', 'mean'),
    center_lon=('lon', 'mean'),
    jumlah_red=('lat', 'count'),
    avg_confidence=('confidence', 'mean'),
    island=('island', 'first'),
    desa_list=(desa_col, lambda x: ', '.join(x.dropna().unique()))
).reset_index()

with st.spinner("Menghitung posisi Hub..."):
    safe_pos = []
    for _, row in cluster_centers.iterrows():
        slon, slat = snap_to_road(round(row['center_lon'], 5), round(row['center_lat'], 5), max_snap_m=snap_offset)
        safe_pos.append({'cluster_id': row['cluster_id'], 'safe_lon': slon, 'safe_lat': slat})
    cluster_centers = cluster_centers.merge(pd.DataFrame(safe_pos), on='cluster_id')

df_hubs = merge_nearby_hubs(cluster_centers, min_dist_m=merge_dist)
hub_status = load_status()

with st.sidebar:
    st.markdown("---")
    st.markdown("## Status Penanganan")
    st.caption("Centang = selesai (hilang dari peta)")
    updated_status = {}
    for _, hub_row in df_hubs.iterrows():
        hub_key = f"hub_{hub_row['hub_id']}"
        checked = st.checkbox(
            f"Hub {hub_row['hub_id']} - {str(hub_row['desa_list'])[:25]}",
            value=hub_status.get(hub_key, False),
            key=f"cb_{hub_key}"
        )
        updated_status[hub_key] = checked
    if st.button("Simpan Status", use_container_width=True):
        save_status(updated_status)
        st.success("Tersimpan!")
        st.rerun()

active_ids = [r['hub_id'] for _, r in df_hubs.iterrows()
              if not hub_status.get(f"hub_{r['hub_id']}", False)]
df_hubs_active = df_hubs[df_hubs['hub_id'].isin(active_ids)].copy()

if df_hubs_active.empty:
    st.success("Semua wilayah sudah selesai ditangani!")
    st.stop()

dist_matrix = cdist(df_raw[['lat', 'lon']].values, df_hubs_active[['safe_lat', 'safe_lon']].values)
valid_mask = dist_matrix.min(axis=0) < 1.2
df_hubs_active = df_hubs_active[valid_mask].copy().reset_index(drop=True)
active_ids = list(df_hubs_active['hub_id'])

if df_hubs_active.empty:
    st.warning("Tidak ada hub yang valid dalam jangkauan.")
    st.stop()

def assign_nearest_hub(row, hubs):
    island_hubs = hubs[hubs['island'] == row['island']]
    target_hubs = island_hubs if not island_hubs.empty else hubs
    dists = cdist([[row['lat'], row['lon']]], target_hubs[['safe_lat', 'safe_lon']].values)
    return target_hubs.iloc[dists.argmin()]['hub_id']

df_raw['hub_id'] = df_raw.apply(lambda r: assign_nearest_hub(r, df_hubs_active), axis=1)
df_mapped = df_raw.merge(df_hubs_active[['hub_id', 'safe_lon', 'safe_lat', 'island']], on='hub_id', suffixes=('', '_hub'))

# Group titik-titik kerusakan menjadi sentral wilayah Red Zone
# Lakukan SEBELUM menghitung rute, lalu hitung rute menuju Red Zone tersebut saja
red_zones = df_mapped.groupby('cluster_id').agg(
    lon=('lon', 'mean'),
    lat=('lat', 'mean'),
    desa=(desa_col, lambda x: ', '.join(pd.Series(x).dropna().unique())),
    confidence=('confidence', 'mean'),
    jumlah=('lat', 'count'),
    hub_id=('hub_id', 'first'),
    safe_lon=('safe_lon', 'first'),
    safe_lat=('safe_lat', 'first'),
    island_hub=('island_hub', 'first'),
    island=('island', 'first')
).reset_index()

with st.spinner("Menghitung rute jalan ke Pusat Red Zone..."):
    path_outline, path_blue, path_blue_link, path_fallback = [], [], [], []
    path_air_line = []
    hub_dists = {hid: [] for hid in active_ids}
    
    # KUNCI PERBAIKAN: Hitung rute cukup menuju 'red_zones' (pusat cluster) saja
    # JANGAN mengulang komputasi rute ke 225 raw points yang tersembunyi
    for i, row in red_zones.iterrows():
        # JANGAN gambar garis path jika Posko Hub sudah didirikan persis di dalam Zona Merah tersebut!
        if haversine_distance_m(row['safe_lat'], row['safe_lon'], row['lat'], row['lon']) < 300:
            hub_dists[row['hub_id']].append(0)
            continue
            
        pts, dist_m = get_route_info(row['safe_lon'], row['safe_lat'], row['lon'], row['lat'])
        mode, effective_dist = choose_route_mode(
            row['safe_lon'], row['safe_lat'], row['lon'], row['lat'],
            row['island_hub'], row['island'], pts, dist_m
        )

        if mode == 'road':
            if pts is not None and len(pts) >= 2:
                full_path = pts
                start_gap = haversine_distance_m(row['safe_lat'], row['safe_lon'], full_path[0][1], full_path[0][0])
                end_gap = haversine_distance_m(full_path[-1][1], full_path[-1][0], row['lat'], row['lon'])
                if start_gap > 50:
                    path_blue_link.append({'path': [[row['safe_lon'], row['safe_lat']], full_path[0]], 'desa': row.get(desa_col, '')})
                if end_gap > 50:
                    path_blue_link.append({'path': [full_path[-1], [row['lon'], row['lat']]], 'desa': row.get(desa_col, '')})
            else:
                full_path = [[row['safe_lon'], row['safe_lat']], [row['lon'], row['lat']]]
            path_outline.append({'path': full_path})
            path_blue.append({'path': full_path, 'desa': row.get(desa_col, '')})
            hub_dists[row['hub_id']].append(effective_dist)
        else:
            path_air_line.append({'path': [[row['safe_lon'], row['safe_lat']], [row['lon'], row['lat']]], 'desa': row.get(desa_col, '')})
            path_fallback.append({
                'source': [row['safe_lon'], row['safe_lat']],
                'target': [row['lon'], row['lat']],
                'desa': row.get(desa_col, '')
            })
            hub_dists[row['hub_id']].append(effective_dist)
    df_outline = pd.DataFrame(path_outline)
    df_blue = pd.DataFrame(path_blue)
    if not df_blue.empty:
        df_blue['tingkat_keyakinan'] = '-'
        df_blue['jumlah'] = '-'
        df_blue['prioritas'] = '-'
        
    df_blue_link = pd.DataFrame(path_blue_link)
    
    df_fallback = pd.DataFrame(path_fallback)
    if not df_fallback.empty:
        df_fallback['tingkat_keyakinan'] = '-'
        df_fallback['jumlah'] = '-'
        df_fallback['prioritas'] = '-'
        
    df_air_line = pd.DataFrame(path_air_line)

df_hubs_active['jarak_rata_km'] = df_hubs_active['hub_id'].apply(
    lambda hid: round(np.mean(hub_dists[hid]) / 1000, 2) if hub_dists.get(hid) else None
)
for item, per_kk in LOGISTIK_PER_KK.items():
    df_hubs_active[item] = (df_hubs_active['jumlah_red'] * per_kk).apply(lambda x: f"{x:,.0f}")

df_hubs_active['priority_score'] = df_hubs_active.apply(
    lambda r: round(r['jumlah_red'] / max(r['jarak_rata_km'] or 0.1, 0.1), 1), axis=1
)
df_hubs_active = df_hubs_active.sort_values('priority_score', ascending=False).reset_index(drop=True)
total_h = len(df_hubs_active)


def plabel(i):
    if i < total_h * 0.33:
        return "TINGGI"
    elif i < total_h * 0.66:
        return "SEDANG"
    return "RENDAH"


df_hubs_active['Prioritas'] = [plabel(i) for i in range(total_h)]

df_hubs_active['desa_list'] = df_hubs_active['desa_list'].replace('', 'Tidak Diketahui')
df_hubs_active['desa_list'] = df_hubs_active['desa_list'].fillna('Tidak Diketahui')

m1, m2, m3, m4 = st.columns(4)
m1.metric("Wilayah Aktif", f"{df_mapped[desa_col].nunique()} Desa")
m2.metric("Titik Kerusakan", f"{len(df_mapped):,} Unit")
m3.metric("Est. Korban Terdampak", f"{df_hubs_active['jumlah_red'].sum() * 4:,} Orang")
m4.metric("Hub Aktif", f"{len(df_hubs_active)} Titik")

st.write("---")
st.markdown("""
<div class="legend-box">
    <span><span class="legend-dot" style="background:#dc2626"></span>Red Zone</span>
    <span><span class="legend-dot" style="background:#16a34a"></span>Safe Hub</span>
    <span><span style="display:inline-block;width:20px;height:4px;background:#38bdf8;margin-right:6px;vertical-align:middle;border-radius:2px"></span>Rute Darat</span>
    <span><span style="display:inline-block;width:20px;height:4px;background:linear-gradient(90deg, #a855f7, #f97316);margin-right:6px;vertical-align:middle;border-radius:2px"></span>Jalur Laut/Udara</span>
</div>
""", unsafe_allow_html=True)

st.write("---")
st.subheader("Navigasi Peta Cepat")
# Buat daftar opsi untuk dropdown navigasi
hub_options = ["Tampilkan Seluruh Wilayah"] + [
    f"Hub {row['hub_id']} - {str(row['desa_list']).split(',')[0]}" 
    for _, row in df_hubs_active.iterrows()
]
selected_view = st.selectbox("Pilih desa/hub untuk langsung memfokuskan kamera peta:", hub_options)

if selected_view == "Tampilkan Seluruh Wilayah":
    avg_lat = df_mapped['lat'].mean()
    avg_lon = df_mapped['lon'].mean()
    spread = max(df_mapped['lat'].max() - df_mapped['lat'].min(),
                 df_mapped['lon'].max() - df_mapped['lon'].min())
    zoom = 14 if spread < 0.05 else (12 if spread < 0.2 else (10 if spread < 1 else 7))
else:
    # Ambil ID Hub dari string pilihan (contoh format: "Hub 12 - Sukasari")
    selected_id = int(selected_view.split(" ")[1])
    focused_hub = df_hubs_active[df_hubs_active['hub_id'] == selected_id].iloc[0]
    avg_lat = focused_hub['safe_lat']
    avg_lon = focused_hub['safe_lon']
    zoom = 13.5 # Zoom dekat ke desa yang dipilih

# Perbesar base radius untuk merepresentasikan skala kerusakan desa
base_r = 60 if zoom >= 13 else (150 if zoom >= 11 else 350)
hub_r = 80 if zoom >= 13 else (180 if zoom >= 11 else 400)

cluster_norm = (red_zones['jumlah'] - 1) / max(red_zones['jumlah'].max() - 1, 1)
conf_vals = red_zones['confidence']
conf_min = conf_vals.min()
conf_max = conf_vals.max()
conf_range = conf_max - conf_min if conf_max > conf_min else 1
conf_norm = (conf_vals - conf_min) / conf_range

severity_scale = 0.6 + (1.5 * conf_norm) + (1.2 * cluster_norm) + 0.5
radius_vals = np.clip((base_r * severity_scale).astype(int), int(base_r * 0.6), int(base_r * 4.0))

red_df = pd.DataFrame({
    'lon': red_zones['lon'].values,
    'lat': red_zones['lat'].values,
    'desa': red_zones['desa'].values,
    'tingkat_keyakinan': (red_zones['confidence'] * 100).round(1).astype(str) + '%',
    'jumlah': red_zones['jumlah'].astype(str),
    'prioritas': '-',
    'radius': radius_vals
})

layers = []
if not df_outline.empty:
    layers += [
        pdk.Layer("PathLayer", df_outline, get_path="path",
                  get_color=[255, 255, 255, 70], get_width=12,
                  width_min_pixels=8, rounded=True, pickable=False),
        pdk.Layer("PathLayer", df_blue, get_path="path",
                  get_color=[56, 189, 248, 230], get_width=7,
                  width_min_pixels=5, rounded=True, pickable=True),
    ]

if not df_blue_link.empty:
    layers.append(
        pdk.Layer("PathLayer", df_blue_link, get_path="path",
                  get_color=[56, 189, 248, 210], get_width=4,
                  width_min_pixels=3, rounded=True, pickable=False)
    )

if not df_air_line.empty:
    layers.append(
        pdk.Layer("PathLayer", df_air_line, get_path="path",
                  get_color=[249, 115, 22, 190], get_width=3,
                  width_min_pixels=2, rounded=True, pickable=False)
    )

if not df_fallback.empty:
    layers.append(
        pdk.Layer("ArcLayer", df_fallback,
                  get_source_position="source",
                  get_target_position="target",
                  get_source_color=[168, 85, 247, 200],
                  get_target_color=[249, 115, 22, 200],
                  get_width=4,
                  pickable=True)
    )

layers += [
    # Red Zone: Opacity dikurangi agar citra satelit terlihat
    pdk.Layer("ScatterplotLayer", red_df,
              get_position=["lon", "lat"], get_radius="radius",
              get_fill_color=[239, 68, 68, 80], get_line_color=[248, 113, 113, 200],
              line_width_min_pixels=2, radius_scale=1, pickable=True),
    # Safe Hub
    pdk.Layer("ScatterplotLayer",
              pd.DataFrame({'lon': df_hubs_active['safe_lon'], 'lat': df_hubs_active['safe_lat'],
                            'desa': df_hubs_active['desa_list'], 'jumlah': df_hubs_active['jumlah_red'],
                            'prioritas': df_hubs_active['Prioritas'],
                            'tingkat_keyakinan': '-'}),
              get_position=["lon", "lat"], get_radius=hub_r,
              get_fill_color=[34, 197, 94, 255], get_line_color=[20, 83, 45, 200],
              line_width_min_pixels=3, pickable=True),
]

st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/satellite-streets-v11",
    map_provider="mapbox",
    initial_view_state=pdk.ViewState(latitude=avg_lat, longitude=avg_lon, zoom=zoom, pitch=20),
    layers=layers,
    tooltip={"text": "{desa}\nTingkat Keyakinan: {tingkat_keyakinan}\nHub: {jumlah} unit\nPrioritas: {prioritas}"}
))

st.write("---")
st.subheader("Daftar Hub Logistik Aktif")
display_cols = ['hub_id', 'Prioritas', 'desa_list', 'jumlah_red', 'avg_confidence',
                'jarak_rata_km', 'priority_score',
                'Beras (kg)', 'Air Minum (liter)', 'Mie Instan (Dus)',
                'Minyak Goreng (liter)', 'Lauk Kaleng (paket)']
rename_map = {
    'hub_id': 'Hub ID', 'desa_list': 'Desa Terlayani', 'jumlah_red': 'Unit Kerusakan',
    'avg_confidence': 'Tingkat Keyakinan', 'jarak_rata_km': 'Jarak Rata (km)',
    'priority_score': 'Skor Prioritas'
}

df_display = df_hubs_active[display_cols].copy()
df_display['avg_confidence'] = (df_display['avg_confidence'] * 100).round(1).astype(str) + '%'
df_display = df_display.rename(columns=rename_map)

st.dataframe(df_display, use_container_width=True, hide_index=True)
st.caption("Skor Prioritas = Unit Kerusakan / Jarak. Circle merah lebih besar = tingkat keyakinan & jumlah kerusakan lebih tinggi.")
st.caption("Standar BNPB: 1 unit = 1 KK = 4 orang terdampak. Estimasi digunakan untuk menghitung kebutuhan logistik.")

csv = df_display.to_csv(index=False).encode('utf-8')
st.download_button("Download Laporan CSV", csv, "sdss_result.csv", "text/csv")