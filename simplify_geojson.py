#!/usr/bin/env python3
"""Create a smaller display GeoJSON from detailed country polygons."""

import argparse
import json
import math


def point_line_distance(point, start, end):
    px, py = point[:2]
    sx, sy = start[:2]
    ex, ey = end[:2]
    dx = ex - sx
    dy = ey - sy

    if dx == 0 and dy == 0:
        return math.hypot(px - sx, py - sy)

    t = max(0, min(1, ((px - sx) * dx + (py - sy) * dy) / (dx * dx + dy * dy)))
    nearest_x = sx + t * dx
    nearest_y = sy + t * dy
    return math.hypot(px - nearest_x, py - nearest_y)


def douglas_peucker(points, tolerance):
    if len(points) <= 2:
        return points

    max_distance = 0
    index = 0
    start = points[0]
    end = points[-1]

    for i in range(1, len(points) - 1):
        distance = point_line_distance(points[i], start, end)
        if distance > max_distance:
            index = i
            max_distance = distance

    if max_distance <= tolerance:
        return [start, end]

    left = douglas_peucker(points[: index + 1], tolerance)
    right = douglas_peucker(points[index:], tolerance)
    return left[:-1] + right


def round_coord(coord, precision):
    return [round(value, precision) for value in coord]


def remove_consecutive_duplicates(points):
    deduped = []
    for point in points:
        if not deduped or point[:2] != deduped[-1][:2]:
            deduped.append(point)
    return deduped


def simplify_ring(ring, tolerance, precision):
    if len(ring) < 4:
        return [round_coord(point, precision) for point in ring]

    rounded = [round_coord(point, precision) for point in ring]
    open_ring = remove_consecutive_duplicates(rounded[:-1])
    simplified = douglas_peucker(open_ring, tolerance)

    if len(simplified) < 3:
        simplified = open_ring

    simplified.append(simplified[0])
    return simplified


def simplify_geometry(geometry, tolerance, precision):
    if geometry is None:
        return None

    geom_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if geom_type == "Polygon":
        geometry["coordinates"] = [
            simplify_ring(ring, tolerance, precision) for ring in coordinates
        ]
    elif geom_type == "MultiPolygon":
        geometry["coordinates"] = [
            [simplify_ring(ring, tolerance, precision) for ring in polygon]
            for polygon in coordinates
        ]

    return geometry


def simplify_geojson(input_path, output_path, tolerance, precision):
    with open(input_path, "r", encoding="utf-8") as source:
        data = json.load(source)

    for feature in data.get("features", []):
        feature["geometry"] = simplify_geometry(
            feature.get("geometry"), tolerance, precision
        )

    with open(output_path, "w", encoding="utf-8") as target:
        json.dump(data, target, ensure_ascii=False, separators=(",", ":"))


def main():
    parser = argparse.ArgumentParser(
        description="Simplify Polygon and MultiPolygon geometries in a GeoJSON file."
    )
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.03,
        help="Douglas-Peucker tolerance in coordinate units. EPSG:4326 uses degrees.",
    )
    parser.add_argument(
        "--precision",
        type=int,
        default=5,
        help="Decimal places to keep in coordinates.",
    )
    args = parser.parse_args()

    simplify_geojson(args.input, args.output, args.tolerance, args.precision)


if __name__ == "__main__":
    main()
