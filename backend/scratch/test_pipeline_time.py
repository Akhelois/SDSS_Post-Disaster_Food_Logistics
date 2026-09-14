import time
import sys
sys.path.insert(0, '.')

t0 = time.time()
print(f"[{time.time()-t0:.2f}s] Importing main...", flush=True)
import main
print(f"[{time.time()-t0:.2f}s] Calling get_dashboard_data()...", flush=True)
res = main.get_dashboard_data()
print(f"[{time.time()-t0:.2f}s] Done! Result summary: {res.get('summary')}", flush=True)
print(f"[{time.time()-t0:.2f}s] Total red zones: {len(res.get('map_data', {}).get('red_zones', []))}", flush=True)
