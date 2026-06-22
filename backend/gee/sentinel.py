import ee
import numpy as np

from config import GEE_PROJECT, CLOUD_THRESHOLD

_gee_initialized = False


def init_gee():
    global _gee_initialized
    if _gee_initialized:
        return True
    try:
        from datetime import datetime
        ee.Initialize(project=GEE_PROJECT)
        _gee_initialized = True
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] GEE berhasil diinisialisasi")
        return True
    except Exception as e:
        from datetime import datetime
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] GEE init gagal: {e}")
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

        if built_ratio is None or built_ratio < 0.10:
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


def generate_event_grid(center_lat, center_lon, radius_deg):
    from config import INDONESIA_LAND

    def is_land_area(lon_min, lat_min, lon_max, lat_max):
        for llon_min, llat_min, llon_max, llat_max in INDONESIA_LAND:
            if (lon_min < llon_max and lon_max > llon_min and
                    lat_min < llat_max and lat_max > llat_min):
                return True
        return False

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
