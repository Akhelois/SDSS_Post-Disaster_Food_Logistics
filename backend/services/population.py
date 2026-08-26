import requests
import json
import os
import time
import threading

WORLDPOP_STATS_URL = "https://api.worldpop.org/v1/services/stats"
WORLDPOP_TASK_URL = "https://api.worldpop.org/v1/tasks"
WORLDPOP_YEAR = 2020
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "worldpop_cache.json")

_population_cache = {}
_cache_lock = threading.Lock()


def _load_cache():
    global _population_cache
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                _population_cache = json.load(f)
            print(f"[WorldPop] Cache loaded: {len(_population_cache)} desa")
    except Exception:
        _population_cache = {}


def _save_cache():
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(_population_cache, f)
    except Exception:
        pass


_load_cache()


def _safe_parse_json(text):
    """
    WorldPop API kadang menyisipkan PHP warning di response body.
    Fungsi ini mengekstrak JSON valid dari response text.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None


def _make_geojson_from_polygon(coords):
    """
    Membuat GeoJSON FeatureCollection dari koordinat polygon desa.
    coords: list of [lon, lat]
    """
    return {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]
            }
        }]
    }


def _simplify_polygon(coords, max_points=30):
    """
    Menyederhanakan polygon agar tidak terlalu besar untuk API request.
    """
    if len(coords) <= max_points:
        return coords
    step = max(1, len(coords) // max_points)
    simplified = coords[::step]
    if simplified[-1] != simplified[0]:
        simplified.append(simplified[0])
    return simplified


def fetch_worldpop_population(desa_name, polygon_coords):
    """
    Mengambil data populasi per desa dari WorldPop API.

    Sumber: WorldPop — University of Southampton
    Dataset: Global 100m Population (wpgppop)
    Metode: Zonal statistics atas raster populasi global
    Resolusi: ~100m per pixel, diagregasi ke batas desa (ADM4)

    Cara kerja:
    1. Kirim polygon desa ke WorldPop REST API
    2. API melakukan zonal sum atas raster populasi
    3. Hasilnya adalah total populasi aktual dalam polygon tsb

    Referensi:
    - https://www.worldpop.org/
    - Tatem, A.J. (2017). WorldPop, open data for spatial demography.
      Scientific Data, 4:170004. DOI: 10.1038/sdata.2017.4
    """
    cache_key = desa_name.strip().lower() if desa_name else None
    if cache_key and cache_key in _population_cache:
        return _population_cache[cache_key]

    if not polygon_coords or len(polygon_coords) < 4:
        return None

    try:
        simplified = _simplify_polygon(polygon_coords)
        geojson = _make_geojson_from_polygon(simplified)

        params = {
            "dataset": "wpgppop",
            "year": WORLDPOP_YEAR,
            "geojson": json.dumps(geojson),
            "runasync": "true"
        }

        taskid = None
        try:
            r = requests.get(WORLDPOP_STATS_URL, params=params, timeout=3)
            if r.status_code == 200:
                data = _safe_parse_json(r.text)
                if data:
                    taskid = data.get("taskid")
        except Exception:
            pass

        if not taskid:
            return None

        # Quick polling (max 2 attempts x 1.5s) to avoid blocking main HTTP thread
        for attempt in range(2):
            time.sleep(1.5)
            try:
                task_r = requests.get(f"{WORLDPOP_TASK_URL}/{taskid}", timeout=3)
                if task_r.status_code == 200:
                    task_data = _safe_parse_json(task_r.text)
                    if task_data and task_data.get("status") == "finished":
                        total_pop = task_data.get("data", {}).get("total_population")
                        if total_pop is not None and total_pop > 0:
                            population = int(round(total_pop))
                            with _cache_lock:
                                if cache_key:
                                    _population_cache[cache_key] = population
                                _save_cache()
                            print(f"[WorldPop] {desa_name}: {population} jiwa")
                            return population
            except Exception:
                pass

        # If task is still processing, launch background thread to finish fetching into cache for next refresh
        def _bg_fetch(tid, key, name):
            for _ in range(10):
                time.sleep(3)
                try:
                    tr = requests.get(f"{WORLDPOP_TASK_URL}/{tid}", timeout=5)
                    td = _safe_parse_json(tr.text)
                    if td and td.get("status") == "finished":
                        pop = td.get("data", {}).get("total_population")
                        if pop and pop > 0:
                            p_int = int(round(pop))
                            with _cache_lock:
                                if key:
                                    _population_cache[key] = p_int
                                _save_cache()
                            print(f"[WorldPop BG] {name}: {p_int} jiwa cached")
                            break
                except Exception:
                    pass

        threading.Thread(target=_bg_fetch, args=(taskid, cache_key, desa_name), daemon=True).start()
        return None
    except Exception as e:
        print(f"[WorldPop] Error for {desa_name}: {e}")
        return None


def get_population_for_desa(desa_name, polygon_coords=None):
    """
    Mengambil data populasi untuk satu desa.
    Menggunakan cache terlebih dahulu, jika tidak ada maka query WorldPop API.
    """
    if not desa_name:
        return None

    cache_key = desa_name.strip().lower()
    if cache_key in _population_cache:
        return _population_cache[cache_key]

    if polygon_coords:
        return fetch_worldpop_population(desa_name, polygon_coords)

    return None


def preload_population_batch(desa_list):
    """
    Pre-load data populasi untuk banyak desa sekaligus.
    desa_list: list of dict dengan keys 'name' dan 'polygon'
    Hanya query yang belum ada di cache.
    """
    missing = []
    for d in desa_list:
        name = d.get("name", "").strip().lower()
        if name and name not in _population_cache:
            missing.append(d)

    if not missing:
        return

    print(f"[WorldPop] Querying {len(missing)} desa (cached: {len(_population_cache)})...")
    for d in missing[:20]:
        fetch_worldpop_population(d["name"], d["polygon"])
