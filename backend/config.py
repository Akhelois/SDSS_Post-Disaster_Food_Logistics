import os

# === Path ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = "model/model_sdss.h5"
MODEL_BACKUP_DIR = "model/backup"
DESA_SHP = "data/batas_desa/IDN_Final_WGS84.shp"
INPUT_IMAGES = "data/citra/input"
INPUT_LABELS = "data/citra/labels"
PROCESSED_DIR = "data/citra/processed"
OUTPUT_GEOJSON = "output/sdss_result.geojson"
STATUS_FILE = "output/hub_status.json"
PROCESSED_MANIFEST = "output/processed_scenes.json"
PROCESSED_EVENTS_FILE = "output/processed_events.json"
NEW_EVENT_FLAG = "output/new_event.flag"
BPS_DATA_FILE = "bps_data.json"

# === Model Hyperparameters ===
IMG_SIZE = (256, 256)
CONF_THRESHOLD = 0.2
GRID_SIZE = 16
INCREMENTAL_EPOCHS = 3
INCREMENTAL_LR = 1e-5

# === GEE ===
GEE_PROJECT = "sdss-bencana"
CLOUD_THRESHOLD = 30
CHANGE_THRESHOLD = 0.03

# === Scheduler ===
BMKG_GEMPA_URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json"
BMKG_NOWCAST_URL = "https://www.bmkg.go.id/alerts/nowcast/id"
CHECK_INTERVAL_MINUTES = 2
MIN_MAGNITUDE = 5.0
MIN_SEVERITY = ["Moderate", "Severe", "Extreme"]
HEADERS = {
    "User-Agent": "SDSS-Bencana/1.0",
    "Accept": "application/json, application/xml, text/xml, */*"
}

# === Geografi Indonesia ===
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

# === Logistik per KK ===
LOGISTIK_PER_KK = {
    'Beras (kg)': 10,
    'Air Minum (liter)': 50,
    'Mie Instan (Dus)': 2,
    'Minyak Goreng (liter)': 2,
    'Lauk Kaleng (paket)': 4,
}

# === Gudang BNPB ===
GUDANG_BNPB = [
    {"nama": "Gudang BNPB Jakarta",       "lat": -6.1751, "lon": 106.8650},
    {"nama": "Gudang BPBD Jawa Barat",    "lat": -6.9175, "lon": 107.6191},
    {"nama": "Gudang BPBD Jawa Tengah",   "lat": -7.0051, "lon": 110.4381},
    {"nama": "Gudang BPBD Jawa Timur",    "lat": -7.2575, "lon": 112.7521},
    {"nama": "Gudang BPBD Sumatera Utara","lat":  3.5952, "lon":  98.6722},
    {"nama": "Gudang BPBD Sulawesi Sel.", "lat": -5.1477, "lon": 119.4327},
    {"nama": "Gudang BPBD Bali",          "lat": -8.6705, "lon": 115.2126},
    {"nama": "Gudang BPBD NTT",           "lat":-10.1772, "lon": 123.6070},
    {"nama": "Gudang BPBD Kalimantan Sel.","lat": -3.3194, "lon": 114.5908},
    {"nama": "Gudang BPBD Maluku",        "lat": -3.6554, "lon": 128.1903},
    {"nama": "Gudang BPBD Papua",         "lat": -2.5337, "lon": 140.7183},
]

# === Konstanta TTL ===
DATA_TTL_HOURS = 2
BUILDING_CACHE_TTL = 3600
