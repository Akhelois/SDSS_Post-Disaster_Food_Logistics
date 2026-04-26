"""
Event-Driven Scheduler
======================
Memantau API BMKG (Gempa Terkini).
Jika ada gempa baru dengan Magnitude >= 5.0, trigger GEE Downloader
hanya untuk area di sekitar episenter gempa.
Jika ada citra baru yang diunduh, jalankan pipeline deteksi & model update.
"""

import time
import subprocess
import sys
import os
import json
import requests
from datetime import datetime
from gee_downloader import scan_disaster_area

BMKG_URL = "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json"
CHECK_INTERVAL_MINUTES = 5
MIN_MAGNITUDE = 5.0
PROCESSED_EVENTS_FILE = "output/processed_events.json"

os.makedirs("output", exist_ok=True)

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_processed_events():
    if os.path.exists(PROCESSED_EVENTS_FILE):
        try:
            with open(PROCESSED_EVENTS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()

def save_processed_events(events):
    try:
        with open(PROCESSED_EVENTS_FILE, "w") as f:
            json.dump(list(events), f)
    except Exception as e:
        print(f"[{now()}] Error saving events: {e}")

def run_pipeline():
    print(f"\n[{now()}] Menjalankan pipeline deteksi kerusakan & incremental learning...")
    r = subprocess.run([sys.executable, "pipeline.py"], capture_output=False)
    if r.returncode != 0:
        print(f"[{now()}] Pipeline error (code {r.returncode})")
    else:
        print(f"[{now()}] Pipeline selesai dengan sukses")

def check_bmkg_and_trigger():
    print(f"[{now()}] Mengecek data gempa BMKG terkini...")
    processed_events = load_processed_events()
    new_images_downloaded = False
    
    try:
        response = requests.get(BMKG_URL, timeout=15)
        if response.status_code == 200:
            data = response.json()
            quakes = data.get("Infogempa", {}).get("gempa", [])
            
            # Balik urutan agar memproses gempa terlama dulu jika ada banyak yang baru
            for quake in reversed(quakes):
                # Gunakan DateTime sebagai unique ID
                event_id = quake.get("DateTime")
                
                if event_id not in processed_events:
                    magnitude = float(quake.get("Magnitude", 0))
                    # BMKG format coordinates: "Lat,Lon"
                    coords = quake.get("Coordinates", "0,0").split(",")
                    lat, lon = float(coords[0]), float(coords[1])
                    wilayah = quake.get("Wilayah", "")
                    
                    processed_events.add(event_id)
                    save_processed_events(processed_events)
                    
                    if magnitude >= MIN_MAGNITUDE:
                        print(f"\n[{now()}] 🚨 GEMPA BARU M{magnitude} terdeteksi di {wilayah}!")
                        # Trigger GEE Downloader spesifik ke episenter
                        download_count = scan_disaster_area(lat, lon, magnitude, event_id, wilayah)
                        
                        if download_count > 0:
                            new_images_downloaded = True
                    else:
                        pass # Abaikan log untuk gempa kecil agar konsol bersih
                        
    except Exception as e:
        print(f"[{now()}] Error mengambil data BMKG: {e}")
        
    # Jika ada citra baru yang didownload dari event apapun, jalankan pipeline
    # Pipeline ini yang berisi Model ResNet50-UNet dan Continual Learning
    if new_images_downloaded:
        run_pipeline()

if __name__ == "__main__":
    print(f"[{now()}] === Event-Driven Scheduler Dimulai ===")
    print(f"[{now()}] Memantau BMKG setiap {CHECK_INTERVAL_MINUTES} menit")
    print(f"[{now()}] Trigger threshold: Magnitude >= {MIN_MAGNITUDE}")
    print(f"[{now()}] Tekan Ctrl+C untuk berhenti\n")
    
    # Cek langsung saat pertama dijalankan
    check_bmkg_and_trigger()
    
    # Loop secara periodik
    while True:
        time.sleep(CHECK_INTERVAL_MINUTES * 60)
        check_bmkg_and_trigger()