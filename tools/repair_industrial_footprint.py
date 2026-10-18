#!/usr/bin/env python3
"""Restore the Industrial Centre footprint from the raw OSM way.

The extracted footprint was self-intersecting (shoelace area ~60 m² instead of
~1418 m²), because the simplification joined points across the courtyard. This
script reads the raw OSM way 220428422 and rebuilds a valid closed ring using the
same local projection scale as the existing extracted footprint.

Run: python3 tools/repair_industrial_footprint.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(ROOT), '_recon', 'buildings.json')
DATA = os.path.join(ROOT, 'data', 'campus.json')
OSM_ID = 220428422

with open(RAW, encoding='utf-8') as f:
    raw = json.load(f)
items = raw.get('elements', raw) if isinstance(raw, dict) else raw
way = next(w for w in items if w.get('id') == OSM_ID)
geom = way['geometry']
with open(DATA, encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'industrial centre')
fp = lm['footprint']
lons = [g['lon'] for g in geom]
lats = [g['lat'] for g in geom]
xs = [p[0] for p in fp]
zs = [p[1] for p in fp]
ax = (max(xs) - min(xs)) / (max(lons) - min(lons))
az = (max(zs) - min(zs)) / (max(lats) - min(lats))
bx = min(xs) - ax * min(lons)
bz = min(zs) - az * min(lats)
pts = [[round(ax * g['lon'] + bx, 2), round(az * g['lat'] + bz, 2)] for g in geom]
if pts[0] != pts[-1]:
    pts.append(pts[0])
area = 0.0
cx = cz = 0.0
for i in range(len(pts) - 1):
    cross = pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]
    area += cross
    cx += (pts[i][0] + pts[i + 1][0]) * cross
    cz += (pts[i][1] + pts[i + 1][1]) * cross
area /= 2
cx /= 6 * area
cz /= 6 * area
lm['footprint'] = pts
lm['center'] = [round(cx, 2), round(cz, 2)]
with open(DATA, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
print('repaired Industrial Centre:', len(pts) - 1, 'points, area', round(area, 1), 'm2, center', lm['center'])
