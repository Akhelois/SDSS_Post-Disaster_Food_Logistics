import os
import json
import shutil
import time
import numpy as np
import cv2
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import tensorflow as tf
from tensorflow.keras import layers, models
from datetime import datetime

MODEL_PATH         = "model/model_tesis_jason.h5"
DESA_SHP           = "data/batas_desa/IDN_Final_WGS84.shp"
INPUT_IMAGES       = "data/citra/input"
INPUT_LABELS       = "data/citra/labels"
PROCESSED_DIR      = "data/citra/processed"
OUTPUT_GEOJSON     = "output/sdss_result.geojson"
PROCESSED_MANIFEST = "output/processed_scenes.json"
IMG_SIZE           = (256, 256)
CONF_THRESHOLD     = 0.2
GRID_SIZE          = 16

INDONESIA_BBOX = (95.0, -11.0, 141.0, 6.0)

INDONESIA_LAND = [
    (95.2,  -6.0, 105.8,  4.0),
    (105.1, -8.8, 114.5, -5.8),
    (108.0, -4.2, 117.8,  1.5),
    (119.3, -5.7, 125.2,  1.8),
    (115.7, -9.0, 124.5, -7.9),
    (124.5, -7.0, 132.0,  2.0),
    (130.5, -8.5, 140.5, -0.5),
]

os.makedirs(INPUT_IMAGES,  exist_ok=True)
os.makedirs(INPUT_LABELS,  exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs("output",      exist_ok=True)


def now():
    return datetime.now().strftime("%H:%M:%S")


def load_manifest():
    """Muat daftar scene_id yang sudah pernah diproses."""
    if os.path.exists(PROCESSED_MANIFEST):
        try:
            with open(PROCESSED_MANIFEST, 'r') as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_manifest(scene_ids):
    """Simpan daftar scene_id yang sudah diproses."""
    try:
        with open(PROCESSED_MANIFEST, 'w') as f:
            json.dump(list(scene_ids), f)
    except Exception as e:
        print(f"[{now()}] Gagal simpan manifest: {e}")


def is_on_land(lon, lat):
    for lon_min, lat_min, lon_max, lat_max in INDONESIA_LAND:
        if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
            return True
    return False


def is_in_indonesia(buildings, bbox):
    if buildings:
        lon = np.mean([b[0] for b in buildings])
        lat = np.mean([b[1] for b in buildings])
    elif bbox:
        lon = (bbox[0] + bbox[2]) / 2
        lat = (bbox[1] + bbox[3]) / 2
    else:
        return False
    lon_min, lat_min, lon_max, lat_max = INDONESIA_BBOX
    return lon_min <= lon <= lon_max and lat_min <= lat <= lat_max


def build_unet(input_shape=(256, 256, 3)):
    inputs = layers.Input(input_shape)
    c1 = layers.Conv2D(32, (3,3), activation='relu', padding='same')(inputs)
    c1 = layers.Conv2D(32, (3,3), activation='relu', padding='same')(c1)
    p1 = layers.MaxPooling2D((2,2))(c1)
    c2 = layers.Conv2D(64, (3,3), activation='relu', padding='same')(p1)
    c2 = layers.Conv2D(64, (3,3), activation='relu', padding='same')(c2)
    p2 = layers.MaxPooling2D((2,2))(c2)
    c3 = layers.Conv2D(128, (3,3), activation='relu', padding='same')(p2)
    c3 = layers.Conv2D(128, (3,3), activation='relu', padding='same')(c3)
    p3 = layers.MaxPooling2D((2,2))(c3)
    c4 = layers.Conv2D(256, (3,3), activation='relu', padding='same')(p3)
    c4 = layers.Conv2D(256, (3,3), activation='relu', padding='same')(c4)
    u5 = layers.Conv2DTranspose(128, (2,2), strides=(2,2), padding='same')(c4)
    u5 = layers.concatenate([u5, c3])
    c5 = layers.Conv2D(128, (3,3), activation='relu', padding='same')(u5)
    c5 = layers.Conv2D(128, (3,3), activation='relu', padding='same')(c5)
    u6 = layers.Conv2DTranspose(64, (2,2), strides=(2,2), padding='same')(c5)
    u6 = layers.concatenate([u6, c2])
    c6 = layers.Conv2D(64, (3,3), activation='relu', padding='same')(u6)
    c6 = layers.Conv2D(64, (3,3), activation='relu', padding='same')(c6)
    u7 = layers.Conv2DTranspose(32, (2,2), strides=(2,2), padding='same')(c6)
    u7 = layers.concatenate([u7, c1])
    c7 = layers.Conv2D(32, (3,3), activation='relu', padding='same')(u7)
    c7 = layers.Conv2D(32, (3,3), activation='relu', padding='same')(c7)
    outputs = layers.Conv2D(1, (1,1), activation='sigmoid')(c7)
    return models.Model(inputs=[inputs], outputs=[outputs])


def load_model():
    print(f"[{now()}] Loading model...")
    try:
        return tf.keras.models.load_model(MODEL_PATH)
    except Exception:
        pass
    print(f"[{now()}] Rebuild arsitektur + load weights...")
    model = build_unet()
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    model.load_weights(MODEL_PATH)
    return model


def predict_mask(model, img_path):
    img = cv2.imread(img_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, IMG_SIZE) / 255.0
    return model.predict(np.expand_dims(img, 0), verbose=0)[0, :, :, 0]


def parse_label(label_path):
    with open(label_path, 'r') as f:
        data = json.load(f)
    buildings = []
    try:
        for feat in data['features']['lng_lat']:
            coords = feat['geometry']['coordinates'][0]
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            buildings.append((np.mean(lons), np.mean(lats)))
    except (KeyError, TypeError, IndexError):
        pass
    if not buildings:
        try:
            gt = data.get('metadata', {}).get('geotransform')
            if gt:
                lon_min = gt[0]
                lat_max = gt[3]
                lon_max = gt[0] + gt[1] * 1024
                lat_min = gt[3] + gt[5] * 1024
                return None, (lon_min, lat_min, lon_max, lat_max)
        except Exception:
            pass
    return buildings, None


def mask_to_points(mask, buildings, bbox):
    points = []
    h, w   = mask.shape

    if buildings:
        lons = [b[0] for b in buildings]
        lats = [b[1] for b in buildings]
        lon_min, lon_max = min(lons), max(lons)
        lat_min, lat_max = min(lats), max(lats)
        lon_range = lon_max - lon_min or 0.001
        lat_range = lat_max - lat_min or 0.001
        for lon, lat in buildings:
            if not is_on_land(lon, lat):
                continue
            px = int((lon - lon_min) / lon_range * (w - 1))
            py = int((lat_max - lat) / lat_range * (h - 1))
            px = min(max(px, 0), w - 1)
            py = min(max(py, 0), h - 1)
            r0, r1 = max(py-2, 0), min(py+3, h)
            c0, c1 = max(px-2, 0), min(px+3, w)
            conf = float(mask[r0:r1, c0:c1].mean())
            if conf >= CONF_THRESHOLD:
                points.append({'lon': lon, 'lat': lat, 'confidence': round(conf, 4)})

    elif bbox:
        lon_min, lat_min, lon_max, lat_max = bbox
        n_rows = h // GRID_SIZE
        n_cols = w // GRID_SIZE
        for r in range(n_rows):
            for c in range(n_cols):
                cell = mask[r*GRID_SIZE:(r+1)*GRID_SIZE, c*GRID_SIZE:(c+1)*GRID_SIZE]
                conf = float(cell.mean())
                if conf >= CONF_THRESHOLD:
                    lon = lon_min + (c + 0.5) / n_cols * (lon_max - lon_min)
                    lat = lat_max - (r + 0.5) / n_rows * (lat_max - lat_min)
                    if is_on_land(lon, lat):
                        points.append({'lon': lon, 'lat': lat, 'confidence': round(conf, 4)})
    return points


def load_existing():
    if os.path.exists(OUTPUT_GEOJSON):
        try:
            gdf = gpd.read_file(OUTPUT_GEOJSON)
            if 'status' in gdf.columns:
                return gdf[gdf['status'] == 'active'].copy()
            return gdf
        except Exception:
            pass
    return gpd.GeoDataFrame(columns=['geometry', 'confidence', 'scene_id', 'processed_at', 'status'])


def run_pipeline(model):
    png_files = [f for f in os.listdir(INPUT_IMAGES)
                 if f.endswith('.png') and 'post_disaster' in f]

    if not png_files:
        print(f"[{now()}] Tidak ada citra baru di {INPUT_IMAGES}/")
        return False

    print(f"[{now()}] {len(png_files)} citra baru ditemukan...")
    existing    = load_existing()
    new_records = []

    for fname in png_files:
        img_path   = os.path.join(INPUT_IMAGES, fname)
        label_name = fname.replace('.png', '.json')
        label_path = os.path.join(INPUT_LABELS, label_name)
        scene_id   = fname.replace('_post_disaster.png', '')

        print(f"  Memproses: {fname}")

        if not os.path.exists(label_path):
            print(f"    Label tidak ditemukan: {label_path} - skip")
            continue

        try:
            buildings, bbox = parse_label(label_path)

            if not is_in_indonesia(buildings, bbox):
                print(f"    Skip - bukan wilayah Indonesia")
                os.remove(img_path)
                os.remove(label_path)
                continue

            mask = predict_mask(model, img_path)
            pts  = mask_to_points(mask, buildings, bbox)

            print(f"    {len(pts)} titik kerusakan terdeteksi (conf >= {CONF_THRESHOLD})")

            for p in pts:
                new_records.append({
                    'geometry':     Point(p['lon'], p['lat']),
                    'confidence':   p['confidence'],
                    'scene_id':     scene_id,
                    'processed_at': datetime.now().isoformat(),
                    'status':       'active'
                })

            # Hapus file input setelah diproses (bukan dipindah)
            os.remove(img_path)
            os.remove(label_path)
            print(f"    File {fname} dihapus setelah diproses.")

            # Catat scene_id ke manifest agar tidak di-download ulang
            manifest = load_manifest()
            manifest.add(scene_id)
            save_manifest(manifest)

        except Exception as e:
            print(f"    Error: {e}")

    if not new_records:
        print(f"[{now()}] Tidak ada titik kerusakan baru.")
        return False

    new_gdf = gpd.GeoDataFrame(new_records, crs="EPSG:4326")

    if os.path.exists(DESA_SHP):
        try:
            gdf_desa = gpd.read_file(DESA_SHP).to_crs(epsg=4326)
            adm_cols = [c for c in gdf_desa.columns if c.startswith('ADM')]
            new_gdf  = gpd.sjoin_nearest(new_gdf, gdf_desa[adm_cols + ['geometry']],
                                          how='left', max_distance=0.5)
            new_gdf  = new_gdf.drop(columns=['index_right'], errors='ignore')
        except Exception as e:
            print(f"[{now()}] Spatial join gagal: {e}")

    combined = gpd.GeoDataFrame(
        pd.concat([existing, new_gdf], ignore_index=True), crs="EPSG:4326"
    )
    combined.to_file(OUTPUT_GEOJSON, driver='GeoJSON')
    print(f"[{now()}] Output diupdate: {OUTPUT_GEOJSON} ({len(combined)} titik aktif)")

    # Bersihkan PROCESSED_DIR dari file lama (> 7 hari) sebagai safety net
    cutoff = time.time() - 7 * 86400
    cleaned = 0
    for f in os.listdir(PROCESSED_DIR):
        fp = os.path.join(PROCESSED_DIR, f)
        try:
            if os.path.isfile(fp) and os.path.getmtime(fp) < cutoff:
                os.remove(fp)
                cleaned += 1
        except Exception:
            pass
    if cleaned:
        print(f"[{now()}] {cleaned} file lama dihapus dari processed dir.")
    return True


def main():
    print(f"[{now()}] === SDSS Pipeline ===")
    model = load_model()
    run_pipeline(model)
    print(f"[{now()}] Selesai.")


if __name__ == "__main__":
    main()