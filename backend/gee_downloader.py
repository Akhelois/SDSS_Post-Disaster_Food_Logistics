import ee
import os
import json
import requests
import numpy as np
from datetime import datetime, timedelta
from PIL import Image
import io

INPUT_IMAGES = "data/citra/input"
INPUT_LABELS = "data/citra/labels"
PROCESSED_MANIFEST = "output/processed_scenes.json"

os.makedirs(INPUT_IMAGES, exist_ok=True)
os.makedirs(INPUT_LABELS, exist_ok=True)
os.makedirs("output", exist_ok=True)

GEE_PROJECT      = "sdss-bencana"
CLOUD_THRESHOLD  = 30
CHANGE_THRESHOLD = 0.05
DAYS_LOOKBACK    = 14
IMG_SIZE         = (256, 256)
GRID_DEG         = 2.0

INDONESIA_LON_MIN = 95.0
INDONESIA_LON_MAX = 141.0
INDONESIA_LAT_MIN = -11.0
INDONESIA_LAT_MAX = 6.0

INDONESIA_LAND = [
    (95.2,  -6.0, 105.8,  4.0),
    (105.1, -8.8, 114.5, -5.8),
    (108.0, -4.2, 117.8,  1.5),
    (119.3, -5.7, 125.2,  1.8),
    (115.7, -9.0, 124.5, -7.9),
    (124.5, -7.0, 132.0,  2.0),
    (130.5, -8.5, 140.5, -0.5),
]

PROCESSED_SCENES = set()


def now():
    return datetime.now().strftime("%H:%M:%S")


def load_manifest():
    """Muat daftar scene yang sudah pernah diproses."""
    if os.path.exists(PROCESSED_MANIFEST):
        try:
            with open(PROCESSED_MANIFEST, 'r') as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def is_land_area(lon_min, lat_min, lon_max, lat_max):
    for land in INDONESIA_LAND:
        llon_min, llat_min, llon_max, llat_max = land
        if (lon_min < llon_max and lon_max > llon_min and
                lat_min < llat_max and lat_max > llat_min):
            return True
    return False


def generate_indonesia_grid():
    grids = []
    lon   = INDONESIA_LON_MIN
    while lon < INDONESIA_LON_MAX:
        lat = INDONESIA_LAT_MIN
        while lat < INDONESIA_LAT_MAX:
            lon_max = min(lon + GRID_DEG, INDONESIA_LON_MAX)
            lat_max = min(lat + GRID_DEG, INDONESIA_LAT_MAX)
            if is_land_area(lon, lat, lon_max, lat_max):
                center_lon = (lon + lon_max) / 2
                center_lat = (lat + lat_max) / 2
                name = f"idn_{abs(center_lat):.0f}{'s' if center_lat < 0 else 'n'}_{center_lon:.0f}e"
                grids.append({"name": name, "bbox": [lon, lat, lon_max, lat_max]})
            lat += GRID_DEG
        lon += GRID_DEG
    return grids


def init_gee():
    try:
        ee.Initialize(project=GEE_PROJECT)
        print(f"[{now()}] GEE berhasil diinisialisasi")
        return True
    except Exception as e:
        print(f"[{now()}] GEE init gagal: {e}")
        return False


def get_sentinel2(bbox, date_start, date_end):
    region     = ee.Geometry.Rectangle(bbox)
    collection = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(region)
        .filterDate(date_start, date_end)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CLOUD_THRESHOLD))
        .sort('CLOUDY_PIXEL_PERCENTAGE')
    )
    return collection, region


def detect_change(pre_image, post_image, region):
    pre_ndvi  = pre_image.normalizedDifference(['B8', 'B4'])
    post_ndvi = post_image.normalizedDifference(['B8', 'B4'])
    diff      = pre_ndvi.subtract(post_ndvi).abs()
    
    # KUNCI PERBAIKAN: Hanya deteksi area "permukiman" (built area). 
    # Gunakan Google Dynamic World untuk mendeteksi probabilitas bangunan/permukiman.
    try:
        dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1') \
               .filterBounds(region) \
               .select('built') \
               .mean()
        # threshold probability > 20% untuk menghindari false positive (misal: area logging/sawit yang gundul)
        built_mask = dw.gt(0.20)
        diff = diff.updateMask(built_mask)
    except Exception:
        pass # jika Dynamic World gagal, fallback ke diff awal
        
    stats     = diff.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=500,
        bestEffort=True,
        maxPixels=1e9
    )
    result = stats.getInfo().get('nd', 0)
    return result if result is not None else 0


def download_image_as_png(image, region, filename):
    url = image.select(['B4', 'B3', 'B2']).getThumbURL({
        'region': region,
        'dimensions': f'{IMG_SIZE[0]}x{IMG_SIZE[1]}',
        'format': 'png',
        'min': 0,
        'max': 3000,
        'gamma': 1.4
    })
    response = requests.get(url, timeout=60)
    if response.status_code == 200:
        img = Image.open(io.BytesIO(response.content)).convert('RGB')
        img = img.resize(IMG_SIZE)
        img.save(os.path.join(INPUT_IMAGES, filename))
        return True
    return False


def create_label_json(bbox, scene_id, image_date):
    lon_min, lat_min, lon_max, lat_max = bbox
    label = {
        "metadata": {
            "img_name":     f"{scene_id}_post_disaster.png",
            "geotransform": [lon_min, (lon_max-lon_min)/1024, 0,
                             lat_max, 0, -(lat_max-lat_min)/1024],
            "capture_date": image_date,
            "source":       "Sentinel-2 via GEE",
            "lng_lat":      [(lon_min+lon_max)/2, (lat_min+lat_max)/2]
        },
        "features": {"lng_lat": []}
    }
    label_path = os.path.join(INPUT_LABELS, f"{scene_id}_post_disaster.json")
    with open(label_path, 'w') as f:
        json.dump(label, f, indent=2)


def process_region(region_info):
    name = region_info["name"]
    bbox = region_info["bbox"]

    date_end   = datetime.now()
    date_mid   = date_end   - timedelta(days=DAYS_LOOKBACK // 2)
    date_start = date_end   - timedelta(days=DAYS_LOOKBACK)

    try:
        post_col, region_geom = get_sentinel2(bbox, date_mid.strftime("%Y-%m-%d"), date_end.strftime("%Y-%m-%d"))
        pre_col,  _           = get_sentinel2(bbox, date_start.strftime("%Y-%m-%d"), date_mid.strftime("%Y-%m-%d"))

        if post_col.size().getInfo() == 0 or pre_col.size().getInfo() == 0:
            return False

        mean_change = detect_change(pre_col.first(), post_col.first(), region_geom)

        if mean_change < CHANGE_THRESHOLD:
            return False

        print(f"  [{name}] NDVI change: {mean_change:.4f} - Downloading...")

        image_date = post_col.first().date().format('YYYY-MM-dd').getInfo()
        if not image_date:
            return False

        scene_id = f"{name}_{image_date.replace('-', '')}"
        filename = f"{scene_id}_post_disaster.png"

        if scene_id in PROCESSED_SCENES:
            return False

        if os.path.exists(os.path.join(INPUT_IMAGES, filename)):
            return False

        if not download_image_as_png(post_col.first(), region_geom, filename):
            return False

        create_label_json(bbox, scene_id, image_date)
        print(f"  [{name}] Tersimpan: {filename}")
        return True

    except Exception as e:
        print(f"  [{name}] Error: {e}")
        return False


def run_downloader():
    print(f"[{now()}] === GEE Downloader - Seluruh Indonesia ===")
    if not init_gee():
        return 0

    grids      = generate_indonesia_grid()
    print(f"[{now()}] Total grid: {len(grids)} sel (2x2 derajat) - mulai scanning...")

    downloaded = 0
    checked    = 0

    for region in grids:
        result   = process_region(region)
        checked += 1
        if result:
            downloaded += 1
        if checked % 10 == 0:
            print(f"  [{now()}] Progress: {checked}/{len(grids)} grid, {downloaded} citra didownload")

    print(f"\n[{now()}] Selesai - {checked} grid dicek, {downloaded} citra baru didownload")
    return downloaded


if __name__ == "__main__":
    PROCESSED_SCENES = load_manifest()
    count = run_downloader()
    raise SystemExit(0 if count is not None else 1)