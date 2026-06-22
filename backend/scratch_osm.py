import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from core.disaster import fetch_buildings_near, get_buildings_for_zone

lat = -0.18
lon = 119.84
pts = [[119.84, -0.18]]

buildings = fetch_buildings_near(lat, lon, 1500)
print(f"Fetched {len(buildings)} buildings.")

matched = get_buildings_for_zone(pts, lat, lon)
print(f"Matched {len(matched)} buildings.")
