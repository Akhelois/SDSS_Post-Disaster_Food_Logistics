import os
import json
import time
import numpy as np
import cv2
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from datetime import datetime

from config import (
    INPUT_IMAGES, INPUT_LABELS, PROCESSED_DIR, OUTPUT_GEOJSON,
    PROCESSED_MANIFEST, DESA_SHP, IMG_SIZE, CONF_THRESHOLD, GRID_SIZE,
    INDONESIA_BBOX, INDONESIA_LAND
)
from pipeline.training import incremental_train

os.makedirs(INPUT_IMAGES,  exist_ok=True)
os.makedirs(INPUT_LABELS,  exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs("output",      exist_ok=True)


def now():
    return datetime.now().strftime("%H:%M:%S")


def load_manifest():
    if os.path.exists(PROCESSED_MANIFEST):
        try:
            with open(PROCESSED_MANIFEST, 'r') as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_manifest(scene_ids):
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


def is_residential_cluster(points, min_points=2, max_spread_deg=0.15):
    if len(points) <= 1:
        return points

    filtered = []
    for p in points:
        neighbors = sum(
            1 for q in points
            if q is not p
            and abs(p['lon'] - q['lon']) < max_spread_deg
            and abs(p['lat'] - q['lat']) < max_spread_deg
        )
        if neighbors >= min_points - 1:
            filtered.append(p)

    return filtered if filtered else points


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


def predict_mask(model, img_path, pre_img_path=None):
    post_img = cv2.imread(img_path)
    post_img = cv2.cvtColor(post_img, cv2.COLOR_BGR2RGB)
    post_img = cv2.resize(post_img, IMG_SIZE) / 255.0

    if pre_img_path and os.path.exists(pre_img_path):
        pre_img = cv2.imread(pre_img_path)
        pre_img = cv2.cvtColor(pre_img, cv2.COLOR_BGR2RGB)
        pre_img = cv2.resize(pre_img, IMG_SIZE) / 255.0
        combined = np.concatenate([pre_img, post_img], axis=-1)
    else:
        combined = np.concatenate([post_img, post_img], axis=-1)

    return model.predict(np.expand_dims(combined, 0), verbose=0)[0, :, :, 0]


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
    h, w = mask.shape

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

    train_images = []
    train_masks  = []

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

            pre_img_path = None
            try:
                with open(label_path, 'r') as f:
                    label_data = json.load(f)
                pre_img_name = label_data.get('metadata', {}).get('pre_img_name')
                if pre_img_name:
                    pre_img_path = os.path.join(INPUT_IMAGES, pre_img_name)
            except Exception:
                pass

            mask = predict_mask(model, img_path, pre_img_path=pre_img_path)
            pts  = mask_to_points(mask, buildings, bbox)

            print(f"    {len(pts)} titik kerusakan terdeteksi (conf >= {CONF_THRESHOLD})")

            pts_before = len(pts)
            pts = is_residential_cluster(pts)
            if len(pts) < pts_before:
                print(f"    Post-filter: {pts_before} -> {len(pts)} titik (removed isolated non-residential)")

            post_for_train = cv2.imread(img_path)
            if post_for_train is not None:
                post_for_train = cv2.cvtColor(post_for_train, cv2.COLOR_BGR2RGB)
                post_for_train = cv2.resize(post_for_train, IMG_SIZE).astype(np.float32) / 255.0
                
                if pre_img_path and os.path.exists(pre_img_path):
                    pre_for_train = cv2.imread(pre_img_path)
                    pre_for_train = cv2.cvtColor(pre_for_train, cv2.COLOR_BGR2RGB)
                    pre_for_train = cv2.resize(pre_for_train, IMG_SIZE).astype(np.float32) / 255.0
                    combined_train = np.concatenate([pre_for_train, post_for_train], axis=-1)
                else:
                    combined_train = np.concatenate([post_for_train, post_for_train], axis=-1)

                train_images.append(combined_train)
                mask_binary = (mask > 0.5).astype(np.float32)
                train_masks.append(mask_binary)

            for p in pts:
                new_records.append({
                    'geometry':     Point(p['lon'], p['lat']),
                    'confidence':   p['confidence'],
                    'scene_id':     scene_id,
                    'processed_at': datetime.now().isoformat(),
                    'status':       'active'
                })

            os.remove(img_path)
            os.remove(label_path)
            print(f"    File {fname} dihapus setelah diproses.")

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

            pts_within = gpd.sjoin(new_gdf, gdf_desa[['geometry']], how='inner', predicate='within')
            kept_indices = pts_within.index.unique()
            before_count = len(new_gdf)
            new_gdf = new_gdf.loc[new_gdf.index.isin(kept_indices)].copy()
            removed = before_count - len(new_gdf)
            if removed > 0:
                print(f"[{now()}] Filter permukiman: {removed} titik di luar polygon desa dibuang")

            new_gdf = gpd.sjoin_nearest(new_gdf, gdf_desa[adm_cols + ['geometry']],
                                          how='left', max_distance=0.5)
            new_gdf = new_gdf.drop(columns=['index_right'], errors='ignore')
        except Exception as e:
            print(f"[{now()}] Spatial join gagal: {e}")

    combined = gpd.GeoDataFrame(
        pd.concat([existing, new_gdf], ignore_index=True), crs="EPSG:4326"
    )
    combined.to_file(OUTPUT_GEOJSON, driver='GeoJSON')
    print(f"[{now()}] Output diupdate: {OUTPUT_GEOJSON} ({len(combined)} titik aktif)")

    if train_images:
        incremental_train(model, train_images, train_masks)

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
    from pipeline.model import load_model
    model = load_model()
    run_pipeline(model)
    print(f"[{now()}] Selesai.")


if __name__ == "__main__":
    main()
