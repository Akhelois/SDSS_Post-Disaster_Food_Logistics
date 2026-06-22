import os
import json
import requests
from datetime import datetime, timedelta
from PIL import Image
import io

from config import (
    INPUT_IMAGES, INPUT_LABELS, PROCESSED_MANIFEST,
    IMG_SIZE, CHANGE_THRESHOLD, MAG_RADIUS, WEATHER_RADIUS
)
from gee.sentinel import init_gee, get_sentinel2, detect_change, generate_event_grid

os.makedirs(INPUT_IMAGES, exist_ok=True)
os.makedirs(INPUT_LABELS, exist_ok=True)
os.makedirs("output", exist_ok=True)


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


def create_label_json(bbox, scene_id, image_date, pre_img_name=None):
    lon_min, lat_min, lon_max, lat_max = bbox
    label = {
        "metadata": {
            "img_name": f"{scene_id}_post_disaster.png",
            "pre_img_name": pre_img_name,
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
            return False

        mean_change = detect_change(pre_col.first(), post_col.first(), region_geom)

        if mean_change < CHANGE_THRESHOLD:
            return False

        image_date = post_col.first().date().format('YYYY-MM-dd').getInfo()
        if not image_date:
            return False

        scene_id = f"{name}_{image_date.replace('-', '')}"
        filename_post = f"{scene_id}_post_disaster.png"
        filename_pre = f"{scene_id}_pre_disaster.png"

        if scene_id in processed_scenes:
            return False

        if os.path.exists(os.path.join(INPUT_IMAGES, filename_post)):
            return False

        if not download_image_as_png(post_col.first(), region_geom, filename_post):
            return False

        pre_img_name = None
        try:
            if download_image_as_png(pre_col.first(), region_geom, filename_pre):
                pre_img_name = filename_pre
                print(f"[{name}] Pre-disaster image tersimpan: {filename_pre}")
        except Exception as e:
            print(f"[{name}] Pre-disaster download gagal (lanjut tanpa pre): {e}")

        create_label_json(bbox, scene_id, image_date, pre_img_name=pre_img_name)
        processed_scenes.add(scene_id)
        save_manifest(processed_scenes)
        return True

    except Exception as e:
        print(f"    [{name}] Error: {e}")
        return False


def scan_disaster_area(lat, lon, magnitude, event_id, wilayah="", disaster_type="Gempa Bumi"):
    print(f"Jenis: {disaster_type}")
    print(f"Event: {event_id}")
    print(f"Lokasi: {lat:.4f}, {lon:.4f}")
    print(f"Wilayah: {wilayah}")

    if not init_gee():
        return 0

    if disaster_type == "Gempa Bumi":
        radius = get_scan_radius(magnitude)
        days_before = 7 if magnitude < 6.0 else 14
    else:
        radius = WEATHER_RADIUS.get(disaster_type, 0.5)
        days_before = 7

    grids = generate_event_grid(lat, lon, radius)
    print(f"Radius scan: {radius:.1f} deg (~{radius * 111:.0f} km)")
    print(f"Grid cells: {len(grids)}")

    downloaded = 0
    for cell in grids:
        if process_cell(cell, days_before):
            downloaded += 1

    print(f"[{now()}] Scan selesai - {downloaded} citra baru dari {len(grids)} cell")
    return downloaded
