# from model import train_model
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
from tensorflow.keras.applications import ResNet50
from datetime import datetime

MODEL_PATH         = "model/model_sdss.h5"
MODEL_BACKUP_DIR   = "model/backup"
DESA_SHP           = "data/batas_desa/IDN_Final_WGS84.shp"
INPUT_IMAGES       = "data/citra/input"
INPUT_LABELS       = "data/citra/labels"
PROCESSED_DIR      = "data/citra/processed"
OUTPUT_GEOJSON     = "output/sdss_result.geojson"
PROCESSED_MANIFEST = "output/processed_scenes.json"
IMG_SIZE           = (256, 256)
CONF_THRESHOLD     = 0.2
GRID_SIZE          = 16
INCREMENTAL_EPOCHS = 3
INCREMENTAL_LR     = 1e-5

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
os.makedirs(MODEL_BACKUP_DIR, exist_ok=True)


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


def build_resnet_unet(input_shape=(256, 256, 6)):
    """
    DualResNet50-UNet: 6-channel input (pre+post disaster).
      Channel 0-2: Pre-disaster RGB
      Channel 3-5: Post-disaster RGB
    Shared encoder mengekstrak fitur dari kedua citra.
    Bridge: gabungan pre+post → Conv 2048.
    Decoder: U-Net dengan skip connections dari branch post-disaster.
    """
    # Shared ResNet50 encoder (weights ImageNet)
    _base = ResNet50(weights='imagenet', include_top=False, input_shape=(256, 256, 3))
    skip_names = ['conv1_relu', 'conv2_block3_out', 'conv3_block4_out',
                  'conv4_block6_out', 'conv5_block3_out']
    encoder_model = models.Model(
        inputs=_base.input,
        outputs=[_base.get_layer(n).output for n in skip_names],
        name='shared_resnet50'
    )

    # Input 6-channel
    inputs = layers.Input(shape=input_shape, name='input_6ch')
    pre_img  = inputs[:, :, :, :3]
    post_img = inputs[:, :, :, 3:]

    # Forward kedua cabang (shared weights)
    pre_s1, pre_s2, pre_s3, pre_s4, pre_bridge    = encoder_model(pre_img)
    post_s1, post_s2, post_s3, post_s4, post_bridge = encoder_model(post_img)

    # Fusi bridge: concat → reduksi ke 2048
    bridge = layers.concatenate([post_bridge, pre_bridge], name='bridge_fusion')
    bridge = layers.Conv2D(2048, (1, 1), activation='relu', padding='same', name='bridge_reduce')(bridge)
    bridge = layers.BatchNormalization(name='bridge_bn')(bridge)

    # Decoder U-Net (skip connections dari post branch)
    u4 = layers.Conv2DTranspose(512, (2, 2), strides=(2, 2), padding='same')(bridge)
    u4 = layers.concatenate([u4, post_s4])
    u4 = layers.Conv2D(512, (3, 3), activation='relu', padding='same')(u4)
    u4 = layers.BatchNormalization()(u4)
    u4 = layers.Conv2D(512, (3, 3), activation='relu', padding='same')(u4)
    u4 = layers.BatchNormalization()(u4)

    u3 = layers.Conv2DTranspose(256, (2, 2), strides=(2, 2), padding='same')(u4)
    u3 = layers.concatenate([u3, post_s3])
    u3 = layers.Conv2D(256, (3, 3), activation='relu', padding='same')(u3)
    u3 = layers.BatchNormalization()(u3)
    u3 = layers.Conv2D(256, (3, 3), activation='relu', padding='same')(u3)
    u3 = layers.BatchNormalization()(u3)

    u2 = layers.Conv2DTranspose(128, (2, 2), strides=(2, 2), padding='same')(u3)
    u2 = layers.concatenate([u2, post_s2])
    u2 = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(u2)
    u2 = layers.BatchNormalization()(u2)
    u2 = layers.Conv2D(128, (3, 3), activation='relu', padding='same')(u2)
    u2 = layers.BatchNormalization()(u2)

    u1 = layers.Conv2DTranspose(64, (2, 2), strides=(2, 2), padding='same')(u2)
    u1 = layers.concatenate([u1, post_s1])
    u1 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(u1)
    u1 = layers.BatchNormalization()(u1)
    u1 = layers.Conv2D(64, (3, 3), activation='relu', padding='same')(u1)
    u1 = layers.BatchNormalization()(u1)

    u0 = layers.Conv2DTranspose(32, (2, 2), strides=(2, 2), padding='same')(u1)
    u0 = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(u0)
    u0 = layers.Conv2D(32, (3, 3), activation='relu', padding='same')(u0)

    outputs = layers.Conv2D(1, (1, 1), activation='sigmoid', name='output_mask')(u0)
    return models.Model(inputs=inputs, outputs=outputs, name='DualResNet50_UNet_6ch')



def bce_dice_loss(y_true, y_pred):
    """Loss function gabungan untuk segmentasi optimal."""
    bce = tf.keras.losses.binary_crossentropy(y_true, y_pred)
    y_true_f = tf.cast(tf.reshape(y_true, [-1]), tf.float32)
    y_pred_f = tf.reshape(y_pred, [-1])
    intersection = tf.reduce_sum(y_true_f * y_pred_f)
    dice = 1 - (2. * intersection + 1.0) / (tf.reduce_sum(y_true_f) + tf.reduce_sum(y_pred_f) + 1.0)
    return bce + dice

def weighted_bce_dice_loss(y_true, y_pred):
    """
    Weighted Binary Cross-Entropy + Dice Loss (sesuai thesis).
    pos_weight=15: penalti 15x lebih besar pada false negative.
    """
    y_pred_clipped = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
    logits = tf.math.log(y_pred_clipped / (1 - y_pred_clipped))
    bce = tf.nn.weighted_cross_entropy_with_logits(
        labels=tf.cast(y_true, tf.float32),
        logits=logits,
        pos_weight=15.0
    )
    bce = tf.reduce_mean(bce)
    y_true_f = tf.cast(tf.reshape(y_true, [-1]), tf.float32)
    y_pred_f = tf.reshape(y_pred, [-1])
    intersection = tf.reduce_sum(y_true_f * y_pred_f)
    dice = 1 - (2. * intersection + 1.0) / (tf.reduce_sum(y_true_f) + tf.reduce_sum(y_pred_f) + 1.0)
    return bce + dice

def dice_coef(y_true, y_pred):
    y_true_f = tf.cast(tf.reshape(y_true, [-1]), tf.float32)
    y_pred_f = tf.reshape(y_pred, [-1])
    intersection = tf.reduce_sum(y_true_f * y_pred_f)
    return (2. * intersection + 1.0) / (tf.reduce_sum(y_true_f) + tf.reduce_sum(y_pred_f) + 1.0)


def load_model():
    """Load model dari .h5 file, atau bangun dari awal jika belum ada."""
    print(f"[{now()}] Loading model dari {MODEL_PATH}...")

    if os.path.exists(MODEL_PATH):
        try:
            model = tf.keras.models.load_model(
                MODEL_PATH,
                compile=False,
                custom_objects={
                    'bce_dice_loss': bce_dice_loss,
                    'weighted_bce_dice_loss': weighted_bce_dice_loss,
                    'dice_coef': dice_coef
                }
            )
            print(f"[{now()}] Model berhasil dimuat ({os.path.getsize(MODEL_PATH) / 1e6:.1f} MB)")
            return model
        except Exception as e:
            print(f"[{now()}] Gagal load model: {e}")

    print(f"[{now()}] Model .h5 tidak ditemukan. Membangun ResNet50-UNet baru...")
    print(f"[{now()}] PERINGATAN: Jalankan 'python train_model.py' untuk training yang optimal!")
    model = build_resnet_unet()
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=INCREMENTAL_LR),
        loss=weighted_bce_dice_loss,
        metrics=['accuracy', dice_coef]
    )
    model.save(MODEL_PATH)
    print(f"[{now()}] Model awal tersimpan ke {MODEL_PATH}")
    return model


def backup_model():
    """Simpan salinan model sebelum di-fine-tune (safety net)."""
    if not os.path.exists(MODEL_PATH):
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(MODEL_BACKUP_DIR, f"model_sdss_{timestamp}.h5")
    try:
        shutil.copy2(MODEL_PATH, backup_path)
        print(f"[{now()}] Backup model: {backup_path}")

        backups = sorted(
            [f for f in os.listdir(MODEL_BACKUP_DIR) if f.endswith('.h5')],
            reverse=True
        )
        for old in backups[5:]:
            os.remove(os.path.join(MODEL_BACKUP_DIR, old))
    except Exception as e:
        print(f"[{now()}] Gagal backup: {e}")


def incremental_train(model, processed_images, processed_masks):
    """
    CONTINUAL LEARNING: Fine-tune model dari data yang baru saja diproses.
    Learning rate sangat kecil agar tidak merusak pengetahuan lama.
    Hanya 2-3 epoch per batch (bukan training ulang dari nol).
    Model disimpan kembali ke .h5 yang sama.
    """
    if not processed_images or len(processed_images) == 0:
        return

    print(f"[{now()}] === Incremental Learning: {len(processed_images)} citra baru ===")

    backup_model()

    X = np.array(processed_images, dtype=np.float32)
    Y = np.expand_dims(np.array(processed_masks, dtype=np.float32), axis=-1)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=INCREMENTAL_LR),
        loss=bce_dice_loss,
        metrics=['accuracy', dice_coef]
    )

    history = model.fit(
        X, Y,
        epochs=INCREMENTAL_EPOCHS,
        batch_size=min(4, len(X)),
        verbose=1
    )

    model.save(MODEL_PATH)
    final_loss = history.history['loss'][-1]
    final_dice = history.history['dice_coef'][-1]
    print(f"[{now()}] Model updated: loss={final_loss:.4f}, dice={final_dice:.4f}")
    print(f"[{now()}] Tersimpan: {MODEL_PATH}")


def predict_mask(model, img_path, pre_img_path=None):
    """Prediksi mask dengan opsional pre-disaster image."""
    post_img = cv2.imread(img_path)
    post_img = cv2.cvtColor(post_img, cv2.COLOR_BGR2RGB)
    post_img = cv2.resize(post_img, IMG_SIZE) / 255.0
    
    if pre_img_path and os.path.exists(pre_img_path):
        pre_img = cv2.imread(pre_img_path)
        pre_img = cv2.cvtColor(pre_img, cv2.COLOR_BGR2RGB)
        pre_img = cv2.resize(pre_img, IMG_SIZE) / 255.0
        # Concatenate: [pre_R, pre_G, pre_B, post_R, post_G, post_B]
        combined = np.concatenate([pre_img, post_img], axis=-1)  # (256, 256, 6)
    else:
        # Fallback: duplicate post as pre (jika pre tidak tersedia)
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

            img_for_train = cv2.imread(img_path)
            if img_for_train is not None:
                img_for_train = cv2.cvtColor(img_for_train, cv2.COLOR_BGR2RGB)
                img_for_train = cv2.resize(img_for_train, IMG_SIZE).astype(np.float32) / 255.0
                train_images.append(img_for_train)
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

            # Filter: hanya titik yang jatuh di dalam polygon desa (permukiman)
            pts_within = gpd.sjoin(new_gdf, gdf_desa[['geometry']], how='inner', predicate='within')
            kept_indices = pts_within.index.unique()
            before_count = len(new_gdf)
            new_gdf = new_gdf.loc[new_gdf.index.isin(kept_indices)].copy()
            removed = before_count - len(new_gdf)
            if removed > 0:
                print(f"[{now()}] Filter permukiman: {removed} titik di luar polygon desa dibuang")

            # Spatial join untuk info administratif
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
    print(f"[{now()}] === SDSS Pipeline (ResNet50-UNet + Continual Learning) ===")
    model = load_model()
    run_pipeline(model)
    print(f"[{now()}] Selesai.")


if __name__ == "__main__":
    main()
