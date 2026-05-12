import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

BASE = os.path.join(os.path.dirname(__file__), "data")
GEOJSON_PATH = os.path.join(BASE, "../backend/output/sdss_result.geojson")

def point_to_bbox_polygon(lon, lat, pad=0.01):
    return [
        [round(lon - pad, 6), round(lat - pad, 6)],
        [round(lon + pad, 6), round(lat - pad, 6)],
        [round(lon + pad, 6), round(lat + pad, 6)],
        [round(lon - pad, 6), round(lat + pad, 6)],
        [round(lon - pad, 6), round(lat - pad, 6)],
    ]

@app.get("/")
def root():
    if not os.path.isfile(GEOJSON_PATH):
        raise HTTPException(status_code=404, detail="sdss_result.geojson not found")

    try:
        with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
            gj = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read geojson: {e}")

    red_zones = []
    for feat in gj.get("features", []):
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})
        if geom.get("type") == "Point" and geom.get("coordinates"):
            lon, lat = geom["coordinates"][0], geom["coordinates"][1]
            red_zones.append({
                "polygon": point_to_bbox_polygon(lon, lat, pad=0.02),
                "desa": props.get("wilayah", "Tidak Diketahui"),
                "count": 1,
                "disaster_type": props.get("disaster_type", "Bencana Alam"),
                "logistics": {},
                "lon": lon,
                "lat": lat
            })

    return JSONResponse({
        "disaster_info": {
            "types": list({r["disaster_type"] for r in red_zones}),
            "summary": ""
        },
        "metrics": {
            "active_areas": len({r["desa"] for r in red_zones}),
            "total_damage": len(red_zones),
            "estimated_impacts": len(red_zones) * 4
        },
        "total_logistics": {},
        "map_data": {"red_zones": red_zones}
    })