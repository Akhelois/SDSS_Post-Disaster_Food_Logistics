import streamlit as st
import geopandas as gpd
import pandas as pd
import pydeck as pdk
import numpy as np
import requests
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist

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
    .priority-high   { color: #f87171; font-weight: 700; }
    .priority-medium { color: #fbbf24; font-weight: 700; }
    .priority-low    { color: #34d399; font-weight: 700; }
    h1 { color: #e6edf3 !important; font-weight: 700 !important; letter-spacing: -0.5px; }
    h3 { color: #8b949e !important; font-weight: 400 !important; }
    .stDownloadButton > button {
        background: #1f6feb !important; color: white !important;
        border: none !important; border-radius: 8px !important; font-weight: 600 !important;
    }
    thead tr th { background: #161b22 !important; color: #8b949e !important; font-size: 0.78rem !important; }
</style>
""", unsafe_allow_html=True)

st.title("SDSS Logistik Bencana Nasional")
st.markdown("### Konsolidasi Strategis & Rute Distribusi Otomatis")
st.write("---")

# Standar logistik BNPB per KK (1 unit kerusakan = 1 KK = ~4 jiwa)
LOGISTIK_PER_KK = {
    'Beras (kg)':        10,
    'Air Bersih (liter)': 80,   # 20L x 4 jiwa
    'Selimut (lembar)':   2,
    'Obat-obatan (paket)': 1,
    'Tenda Darurat (unit)': 0.2, # 1 tenda per 5 KK
}

@st.cache_data(ttl=3600, show_spinner=False)
def get_route_info(start_lon, start_lat, end_lon, end_lat):
    """Return (koordinat path, jarak meter)"""
    try:
        url = (f"http://router.project-osrm.org/route/v1/driving/"
               f"{start_lon},{start_lat};{end_lon},{end_lat}"
               f"?overview=simplified&geometries=geojson")
        r = requests.get(url, timeout=6)
        data = r.json()
        if data['code'] == 'Ok':
            coords = [[c[0], c[1]] for c in data['routes'][0]['geometry']['coordinates']]
            distance = data['routes'][0]['distance']  # meter
            return coords, distance
    except Exception:
        pass
    return [[start_lon, start_lat], [end_lon, end_lat]], None

@st.cache_data(ttl=3600, show_spinner=False)
def get_route_distance(start_lon, start_lat, end_lon, end_lat):
    try:
        url = (f"http://router.project-osrm.org/route/v1/driving/"
               f"{start_lon},{start_lat};{end_lon},{end_lat}"
               f"?overview=false")
        r = requests.get(url, timeout=5)
        data = r.json()
        if data['code'] == 'Ok':
            return data['routes'][0]['distance']
    except Exception:
        pass
    return 999999

@st.cache_data(ttl=3600, show_spinner=False)
def find_best_snap(lon, lat, offset_m=300):
    try:
        offset_deg = offset_m / 111320
        candidates = []
        for angle_deg in range(0, 360, 45):
            rad = np.radians(angle_deg)
            tlon = lon + offset_deg * np.sin(rad)
            tlat = lat + offset_deg * np.cos(rad)
            r = requests.get(
                f"http://router.project-osrm.org/nearest/v1/driving/{tlon},{tlat}?number=3",
                timeout=3
            )
            d = r.json()
            if d['code'] != 'Ok':
                continue
            for wp in d['waypoints']:
                snap_lon, snap_lat = wp['location']
                snap_name = wp.get('name', '').strip()
                route_dist = get_route_distance(snap_lon, snap_lat, lon, lat)
                name_penalty = 0 if len(snap_name) > 0 else 300
                score = route_dist + name_penalty
                candidates.append((snap_lon, snap_lat, score))
        if candidates:
            best = min(candidates, key=lambda x: x[2])
            return best[0], best[1]
    except Exception:
        pass
    rng = np.random.default_rng(int(abs(lon * 1000) + abs(lat * 1000)))
    angle = rng.uniform(0, 2 * np.pi)
    d = 300 / 111320
    return lon + d * np.sin(angle), lat + d * np.cos(angle)

def merge_nearby_hubs(cluster_centers, min_dist_m=600):
    min_dist_deg = min_dist_m / 111320
    coords = cluster_centers[['safe_lat', 'safe_lon']].values
    merged = []
    used = set()
    for i in range(len(coords)):
        if i in used:
            continue
        group = [i]
        for j in range(i + 1, len(coords)):
            if j in used:
                continue
            dist = np.sqrt(
                (coords[i][0] - coords[j][0])**2 +
                (coords[i][1] - coords[j][1])**2
            )
            if dist < min_dist_deg:
                group.append(j)
                used.add(j)
        used.add(i)
        rows = cluster_centers.iloc[group]
        merged.append({
            'safe_lat': rows['safe_lat'].mean(),
            'safe_lon': rows['safe_lon'].mean(),
            'desa_list': ', '.join(rows['desa_list'].str.split(', ').explode().unique()),
            'jumlah_red': rows['jumlah_red'].sum(),
            'cluster_ids': list(rows['cluster_id'])
        })
    return pd.DataFrame(merged).reset_index().rename(columns={'index': 'hub_id'})

def hitung_prioritas(jumlah_unit, jarak_km):
    """
    Skor prioritas = unit kerusakan / jarak.
    Makin banyak unit & makin dekat = prioritas makin tinggi.
    """
    if jarak_km is None or jarak_km == 0:
        jarak_km = 0.1
    score = jumlah_unit / jarak_km
    return round(score, 1)

def label_prioritas(rank, total):
    if rank <= total * 0.33:
        return "🔴 TINGGI"
    elif rank <= total * 0.66:
        return "🟡 SEDANG"
    else:
        return "🟢 RENDAH"

@st.cache_data(ttl=5, show_spinner=False)
def load_data():
    try:
        gdf_ai = gpd.read_file("sdss_indonesia_final.shp").to_crs(epsg=4326)
        gdf_desa = gpd.read_file("IDN_Final_WGS84.shp").to_crs(epsg=4326)
        joined = gpd.sjoin(gdf_desa, gdf_ai, how="inner", predicate="intersects")
        tmp = joined.to_crs(epsg=3857)
        joined['lat'] = tmp.geometry.centroid.to_crs(epsg=4326).y
        joined['lon'] = tmp.geometry.centroid.to_crs(epsg=4326).x
        return joined
    except Exception as e:
        st.error(f"Gagal load data: {e}")
        return None

df_raw = load_data()

if df_raw is not None and not df_raw.empty:
    coords = df_raw[['lat', 'lon']].values
    n_clusters = min(max(1, len(coords) // 2), 20)
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df_raw['cluster_id'] = km.fit_predict(coords)

    cluster_centers = df_raw.groupby('cluster_id').agg(
        center_lat=('lat', 'mean'),
        center_lon=('lon', 'mean'),
        desa_list=('ADM4_EN', lambda x: ', '.join(x.unique())),
        jumlah_red=('lat', 'count')
    ).reset_index()

    with st.spinner("Menghitung posisi Hub optimal di jalan utama..."):
        safe_pos = []
        for _, row in cluster_centers.iterrows():
            slon, slat = find_best_snap(row['center_lon'], row['center_lat'], offset_m=300)
            safe_pos.append({'cluster_id': row['cluster_id'], 'safe_lon': slon, 'safe_lat': slat})
        cluster_centers = cluster_centers.merge(pd.DataFrame(safe_pos), on='cluster_id')

    df_hubs = merge_nearby_hubs(cluster_centers, min_dist_m=600)

    hub_coords = df_hubs[['safe_lat', 'safe_lon']].values
    red_coords = df_raw[['lat', 'lon']].values
    dist_matrix = cdist(red_coords, hub_coords)
    df_raw['hub_id'] = dist_matrix.argmin(axis=1)

    df_mapped = df_raw.merge(df_hubs[['hub_id', 'safe_lon', 'safe_lat']], on='hub_id')

    with st.spinner("Menghitung rute & jarak aktual..."):
        path_rows_outline = []
        path_rows_blue = []
        # Hitung rata-rata jarak rute per hub
        hub_distances = {hid: [] for hid in df_hubs['hub_id']}

        for _, row in df_mapped.iterrows():
            pts, dist_m = get_route_info(row['safe_lon'], row['safe_lat'], row['lon'], row['lat'])
            path_rows_outline.append({'path': pts})
            path_rows_blue.append({'path': pts, 'desa': row.get('ADM4_EN', '')})
            if dist_m is not None:
                hub_distances[row['hub_id']].append(dist_m)

        df_path_outline = pd.DataFrame(path_rows_outline)
        df_path_blue = pd.DataFrame(path_rows_blue)

    # Tambah kolom jarak rata-rata per hub
    df_hubs['jarak_rata_m'] = df_hubs['hub_id'].apply(
        lambda hid: np.mean(hub_distances[hid]) if hub_distances.get(hid) else None
    )
    df_hubs['jarak_rata_km'] = df_hubs['jarak_rata_m'].apply(
        lambda x: round(x / 1000, 2) if x is not None else None
    )

    # Hitung estimasi logistik
    for item, per_kk in LOGISTIK_PER_KK.items():
        df_hubs[item] = (df_hubs['jumlah_red'] * per_kk).apply(
            lambda x: f"{x:,.0f}"
        )

    # Hitung priority score & label
    df_hubs['priority_score'] = df_hubs.apply(
        lambda r: hitung_prioritas(r['jumlah_red'], r['jarak_rata_km']), axis=1
    )
    df_hubs = df_hubs.sort_values('priority_score', ascending=False).reset_index(drop=True)
    total_hubs = len(df_hubs)
    df_hubs['Prioritas'] = [label_prioritas(i, total_hubs) for i in range(total_hubs)]

    # METRIK UTAMA
    total_unit = df_hubs['jumlah_red'].sum()
    total_jiwa = total_unit * 4
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Wilayah Terdampak", f"{df_raw['ADM4_EN'].nunique()} Desa")
    m2.metric("Titik Kerusakan", f"{total_unit:,} Unit")
    m3.metric("Estimasi Jiwa Terdampak", f"{total_jiwa:,} Jiwa")
    m4.metric("Hub Logistik", f"{len(df_hubs)} Titik")

    st.write("---")

    st.markdown("""
    <div class="legend-box">
        <span><span class="legend-dot" style="background:#dc2626"></span>Red Zone — Titik kerusakan</span>
        <span><span class="legend-dot" style="background:#16a34a"></span>Safe Hub — Konsolidasi logistik</span>
        <span><span style="display:inline-block;width:20px;height:4px;background:#38bdf8;margin-right:6px;vertical-align:middle;border-radius:2px"></span>Rute distribusi via jalan</span>
    </div>
    """, unsafe_allow_html=True)

    avg_lat = df_raw['lat'].mean()
    avg_lon = df_raw['lon'].mean()
    spread = max(df_raw['lat'].max() - df_raw['lat'].min(),
                 df_raw['lon'].max() - df_raw['lon'].min())
    zoom = 14 if spread < 0.05 else (12 if spread < 0.2 else (10 if spread < 1 else 7))
    red_r = 30 if zoom >= 13 else (80 if zoom >= 11 else 200)
    hub_r = 50 if zoom >= 13 else (120 if zoom >= 11 else 300)

    layers = []

    if not df_path_outline.empty:
        layers.append(pdk.Layer(
            "PathLayer", df_path_outline,
            get_path="path",
            get_color=[255, 255, 255, 70],
            get_width=12, width_min_pixels=8,
            width_scale=1, rounded=True, pickable=False,
        ))
        layers.append(pdk.Layer(
            "PathLayer", df_path_blue,
            get_path="path",
            get_color=[56, 189, 248, 230],
            get_width=7, width_min_pixels=5,
            width_scale=1, rounded=True, pickable=True,
        ))

    layers.append(pdk.Layer(
        "ScatterplotLayer",
        pd.DataFrame({'lon': df_mapped['lon'], 'lat': df_mapped['lat'], 'desa': df_mapped['ADM4_EN']}),
        get_position=["lon", "lat"],
        get_fill_color=[220, 38, 38, 230],
        get_line_color=[254, 202, 202],
        line_width_min_pixels=1,
        get_radius=red_r, pickable=True,
    ))

    layers.append(pdk.Layer(
        "ScatterplotLayer",
        pd.DataFrame({
            'lon': df_hubs['safe_lon'], 'lat': df_hubs['safe_lat'],
            'desa': df_hubs['desa_list'], 'jumlah': df_hubs['jumlah_red'],
            'prioritas': df_hubs['Prioritas']
        }),
        get_position=["lon", "lat"],
        get_fill_color=[22, 163, 74, 240],
        get_line_color=[134, 239, 172],
        line_width_min_pixels=2,
        get_radius=hub_r, pickable=True,
    ))

    st.pydeck_chart(pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        initial_view_state=pdk.ViewState(latitude=avg_lat, longitude=avg_lon, zoom=zoom, pitch=0),
        layers=layers,
        tooltip={"text": "📍 {desa}\n🟢 Hub: {jumlah} unit\n⚡ {prioritas}"}
    ))

    st.write("---")
    st.subheader("Daftar Hub Logistik & Estimasi Kebutuhan")

    display_cols = [
        'hub_id', 'Prioritas', 'desa_list', 'jumlah_red',
        'jarak_rata_km', 'priority_score',
        'Beras (kg)', 'Air Bersih (liter)', 'Selimut (lembar)',
        'Obat-obatan (paket)', 'Tenda Darurat (unit)'
    ]
    rename_map = {
        'hub_id': 'Hub ID',
        'Prioritas': 'Prioritas',
        'desa_list': 'Desa Terlayani',
        'jumlah_red': 'Unit Kerusakan',
        'jarak_rata_km': 'Jarak Rata² (km)',
        'priority_score': 'Skor Prioritas',
    }

    st.dataframe(
        df_hubs[display_cols].rename(columns=rename_map),
        use_container_width=True, hide_index=True
    )

    st.caption("📌 Skor Prioritas = Unit Kerusakan ÷ Jarak (km). Makin tinggi = makin mendesak didatangi pertama.")
    st.caption("📦 Estimasi logistik berdasarkan standar BNPB: 1 unit kerusakan = 1 KK = ±4 jiwa.")

    csv = df_hubs[display_cols].rename(columns=rename_map).to_csv(index=False).encode('utf-8')
    st.download_button("⬇ Download Laporan Lengkap (CSV)", csv, "sdss_result.csv", "text/csv")

else:
    st.info("Sistem standby. Pastikan file SHP tersedia di folder proyek.")