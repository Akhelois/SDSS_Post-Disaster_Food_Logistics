import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from core.disaster import fetch_buildings_near
from shapely.geometry import Point, Polygon as ShapelyPolygon

lat = -0.18
lon = 119.84
pts = [[119.84, -0.18]]

buildings = fetch_buildings_near(lat, lon, 1500)
print(f"Fetched {len(buildings)} buildings.")

for b in buildings:
    poly = ShapelyPolygon(b)
    pt = Point(lon, lat)
    dist = pt.distance(poly)
    print(dist)
