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

GEE_PROJECT = "sdss-bencana"
CLOUD_THRESHOLD = 30
CHANGE_THRESHOLD = 0.03
IMG_SIZE = (256, 256)

MAG_RADIUS = {
    5.0: 0.5,
    5.5: 0.8,
    6.0: 1.2,
    6.5: 1.8,
    7.0: 2.5,
}

WEATHER_RADIUS = {
    'Banjir': 0.5,
    'Hujan Lebat': 0.5,
    'Tanah Longsor': 0.3,
    'Angin Kencang': 0.5,
    'Tsunami': 1.0,
    'Cuaca Ekstrem': 0.5,
}

INDONESIA_LAND = [
    (95.2,  -6.0, 105.8,  4.0),
    (105.1, -8.8, 114.5, -5.8),
    (108.0, -4.2, 117.8,  1.5),
    (119.3, -5.7, 125.2,  1.8),
    (115.7, -9.0, 124.5, -7.9),
    (124.5, -7.0, 132.0,  2.0),
    (130.5, -8.5, 140.5, -0.5),
]

_gee_initialized = False


def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_manifest():
    if os.path.exists(PROCESSED_MANIFEST):
        try:
            with open(PROCESSED_MANIFEST, 'r') as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_manifest(scenes):
    try:
        with open(PROCESSED_MANIFEST, 'w') as f:
            json.dump(list(scenes), f)
    except Exception:
        pass


def is_land_area(lon_min, lat_min, lon_max, lat_max):
    for llon_min, llat_min, llon_max, llat_max in INDONESIA_LAND:
        if (lon_min < llon_max and lon_max > llon_min and
                lat_min < llat_max and lat_max > llat_min):
            return True
    return False


def init_gee():
    global _gee_initialized
    if _gee_initialized:
        return True
    try:
        ee.Initialize(project=GEE_PROJECT)
        _gee_initialized = True
        print(f"[{now()}] GEE berhasil diinisialisasi")
        return True
    except Exception as e:
        print(f"[{now()}] GEE init gagal: {e}")
        return False


def get_sentinel2(bbox, date_start, date_end):
    region = ee.Geometry.Rectangle(bbox)
    collection = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(region)
        .filterDate(date_start, date_end)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', CLOUD_THRESHOLD))
        .sort('CLOUDY_PIXEL_PERCENTAGE')
    )
    return collection, region


def detect_change(pre_image, post_image, region):
    try:
        dw = ee.ImageCollection('GOOGLE/DYNAMICWORLD/V1') \
               .filterBounds(region) \
               .select('built') \
               .mean()
        built_mask = dw.gt(0.30)

        built_stats = built_mask.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=region,
            scale=500,
            bestEffort=True,
            maxPixels=1e9
        )
        built_ratio = built_stats.getInfo().get('built', 0)

        if built_ratio is None or built_ratio < 0.03:
            return 0

    except Exception:
        built_mask = None

    pre_ndvi = pre_image.normalizedDifference(['B8', 'B4'])
    post_ndvi = post_image.normalizedDifference(['B8', 'B4'])
    diff = pre_ndvi.subtract(post_ndvi).abs()

    if built_mask is not None:
        diff = diff.updateMask(built_mask)

    stats = diff.reduceRegion(
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
            "img_name": f"{scene_id}_post_disaster.png",
            "geotransform": [lon_min, (lon_max - lon_min) / 1024, 0,
                             lat_max, 0, -(lat_max - lat_min) / 1024],
            "capture_date": image_date,
            "source": "Sentinel-2 via GEE (Event-Driven)",
            "lng_lat": [(lon_min + lon_max) / 2, (lat_min + lat_max) / 2]
        },
        "features": {"lng_lat": []}
    }
    label_path = os.path.join(INPUT_LABELS, f"{scene_id}_post_disaster.json")
    with open(label_path, 'w') as f:
        json.dump(label, f, indent=2)


def get_scan_radius(magnitude):
    for mag_threshold in sorted(MAG_RADIUS.keys(), reverse=True):
        if magnitude >= mag_threshold:
            return MAG_RADIUS[mag_threshold]
    return 0.5


def generate_event_grid(center_lat, center_lon, radius_deg):
    cell_size = 0.5
    grids = []
    lon = center_lon - radius_deg
    while lon < center_lon + radius_deg:
        lat = center_lat - radius_deg
        while lat < center_lat + radius_deg:
            lon_max = lon + cell_size
            lat_max = lat + cell_size
            if is_land_area(lon, lat, lon_max, lat_max):
                name = f"evt_{abs(lat + cell_size / 2):.1f}{'s' if lat < 0 else 'n'}_{lon + cell_size / 2:.1f}e"
                grids.append({"name": name, "bbox": [lon, lat, lon_max, lat_max]})
            lat += cell_size
        lon += cell_size
    return grids


def process_cell(cell_info, days_before=7):
    name = cell_info["name"]
    bbox = cell_info["bbox"]
    processed_scenes = load_manifest()

    date_end = datetime.now()
    date_mid = date_end - timedelta(days=days_before // 2)
    date_start = date_end - timedelta(days=days_before)

    try:
        post_col, region_geom = get_sentinel2(bbox, date_mid.strftime("%Y-%m-%d"), date_end.strftime("%Y-%m-%d"))
        pre_col, _ = get_sentinel2(bbox, date_start.strftime("%Y-%m-%d"), date_mid.strftime("%Y-%m-%d"))

        if post_col.size().getInfo() == 0 or pre_col.size().getInfo() == 0:
            print(f"    [{name}] Tidak ada citra Sentinel-2 tersedia")
            return False

        mean_change = detect_change(pre_col.first(), post_col.first(), region_geom)

        if mean_change < CHANGE_THRESHOLD:
            print(f"    [{name}] NDVI change: {mean_change:.4f} - tidak signifikan, skip")
            return False

        print(f"    [{name}] NDVI change: {mean_change:.4f} - TERDETEKSI! Downloading...")

        image_date = post_col.first().date().format('YYYY-MM-dd').getInfo()
        if not image_date:
            return False

        scene_id = f"{name}_{image_date.replace('-', '')}"
        filename = f"{scene_id}_post_disaster.png"

        if scene_id in processed_scenes:
            print(f"    [{name}] Scene sudah pernah diproses, skip")
            return False

        if os.path.exists(os.path.join(INPUT_IMAGES, filename)):
            return False

        if not download_image_as_png(post_col.first(), region_geom, filename):
            return False

        create_label_json(bbox, scene_id, image_date)
        processed_scenes.add(scene_id)
        save_manifest(processed_scenes)
        print(f"    [{name}] Tersimpan: {filename}")
        return True

    except Exception as e:
        print(f"    [{name}] Error: {e}")
        return False


def scan_disaster_area(lat, lon, magnitude, event_id, wilayah="", disaster_type="Gempa Bumi"):
    print(f"\n[{now()}] === EVENT-DRIVEN SCAN ===")
    print(f"  Jenis: {disaster_type}")
    print(f"  Event: {event_id}")
    print(f"  Lokasi: {lat:.4f}, {lon:.4f}")
    print(f"  Wilayah: {wilayah}")

    if not init_gee():
        return 0

    if disaster_type == "Gempa Bumi":
        radius = get_scan_radius(magnitude)
        days_before = 7 if magnitude < 6.0 else 14
    else:
        radius = WEATHER_RADIUS.get(disaster_type, 0.5)
        days_before = 7

    grids = generate_event_grid(lat, lon, radius)
    print(f"  Radius scan: {radius:.1f} deg (~{radius * 111:.0f} km)")
    print(f"  Grid cells: {len(grids)}")

    downloaded = 0
    for cell in grids:
        if process_cell(cell, days_before):
            downloaded += 1

    print(f"\n[{now()}] Scan selesai - {downloaded} citra baru dari {len(grids)} cell")
    return downloaded


if __name__ == "__main__":
    scan_disaster_area(
        lat=-0.18,
        lon=119.84,
        magnitude=7.5,
        event_id="test_palu_2024",
        wilayah="Sulawesi Tengah"
    )