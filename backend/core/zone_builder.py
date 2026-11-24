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
    if len(zone_list) <= 1:
        return zone_list

    geoms = []
    valid = []
    for z in zone_list:
        try:
            poly = ShapelyPolygon(z['polygon'])
            if poly.is_valid and not poly.is_empty:
                geoms.append(poly)
                valid.append(z)
        except Exception:
            continue

    if not geoms:
        return zone_list

    from shapely.strtree import STRtree
    tree = STRtree(geoms)
    result = []

    for idx, (poly, z) in enumerate(zip(geoms, valid)):
        overlapping = [i for i in tree.query(poly) if i < idx]
        cleaned = poly
        for prev_idx in overlapping:
            prev_poly = geoms[prev_idx]
            if cleaned.intersects(prev_poly):
                try:
                    diff = cleaned.difference(prev_poly)
                    if diff.geom_type == 'MultiPolygon':
                        diff = max(diff.geoms, key=lambda p: p.area)
                    if not diff.is_empty and diff.geom_type == 'Polygon':
                        cleaned = diff
                    else:
                        cleaned = None
                        break
                except Exception:
                    pass

        if cleaned is not None and not cleaned.is_empty and cleaned.geom_type == 'Polygon':
            item = z.copy()
            item['polygon'] = [[round(c[0], 6), round(c[1], 6)] for c in cleaned.exterior.coords]
            result.append(item)

    return result
