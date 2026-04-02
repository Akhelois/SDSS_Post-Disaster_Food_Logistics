import time
import subprocess
import sys
import os
from datetime import datetime

INTERVAL_JAM = 6


def has_new_input():
    img_dir = os.path.join("data", "citra", "input")
    lbl_dir = os.path.join("data", "citra", "labels")
    if not os.path.isdir(img_dir) or not os.path.isdir(lbl_dir):
        return False
    for name in os.listdir(img_dir):
        if name.endswith("_post_disaster.png"):
            label_name = name.replace(".png", ".json")
            if os.path.exists(os.path.join(lbl_dir, label_name)):
                return True
    return False

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def run():
    print(f"\n[{now()}] GEE -> scan seluruh Indonesia...")
    r1 = subprocess.run([sys.executable, "gee_downloader.py"], capture_output=False)
    if r1.returncode != 0:
        print(f"[{now()}] GEE error -> tetap lanjut pipeline")

    if has_new_input():
        print(f"[{now()}] Pipeline deteksi kerusakan...")
        r2 = subprocess.run([sys.executable, "pipeline.py"], capture_output=False)
        if r2.returncode != 0:
            print(f"[{now()}] Pipeline error (code {r2.returncode})")
    else:
        print(f"[{now()}] Tidak ada perubahan citra, pipeline dilewati")

if __name__ == "__main__":
    print(f"[{now()}] Interval : setiap {INTERVAL_JAM} jam")
    print(f"[{now()}] Coverage : seluruh Indonesia")
    print(f"[{now()}] Ctrl+C untuk berhenti\n")
    run()
    while True:
        print(f"[{now()}] Menunggu {INTERVAL_JAM} jam...")
        time.sleep(INTERVAL_JAM * 3600)
        run()