from shapely.geometry import Polygon as ShapelyPolygon


def desa_to_polygon(geom, simplify_tol=0.0005, shrink_m=50):
    try:
        simplified = geom.simplify(simplify_tol, preserve_topology=True).buffer(0)
        if simplified.is_empty:
            return None
        shrink_deg = shrink_m / 111320.0
        shrunk = simplified.buffer(-shrink_deg)
        if shrunk.is_empty:
            shrunk = simplified
        target = shrunk
        if target.geom_type == 'MultiPolygon':
            largest = max(target.geoms, key=lambda p: p.area)
            return [[round(c[0], 6), round(c[1], 6)] for c in largest.exterior.coords]
        elif target.geom_type == 'Polygon':
            return [[round(c[0], 6), round(c[1], 6)] for c in target.exterior.coords]
    except Exception:
        pass
    return None


def remove_overlaps(zone_list):
    geoms = []
    valid_indices = []
    for i, z in enumerate(zone_list):
        try:
            poly = ShapelyPolygon(z['polygon'])
            if poly.is_valid and not poly.is_empty:
                geoms.append(poly)
                valid_indices.append(i)
        except Exception:
            continue

    if len(geoms) <= 1:
        return zone_list

    result = []
    claimed = None
    for idx, gi in enumerate(geoms):
        if claimed is None:
            cleaned = gi
        else:
            cleaned = gi.difference(claimed)
        if cleaned.is_empty:
            continue
        if cleaned.geom_type == 'MultiPolygon':
            cleaned = max(cleaned.geoms, key=lambda p: p.area)
        if cleaned.is_empty or cleaned.geom_type != 'Polygon':
            continue
        z = zone_list[valid_indices[idx]].copy()
        z['polygon'] = [[round(c[0], 6), round(c[1], 6)] for c in cleaned.exterior.coords]
        result.append(z)
        if claimed is None:
            claimed = cleaned
        else:
            claimed = claimed.union(cleaned)

    return result
