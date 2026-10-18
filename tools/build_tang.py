#!/usr/bin/env python3
"""Hand-authored Tang Ping Yuan Building: stacked brick/glass/white volumes + roof garden."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'tang ping yuan building')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
PODIUM = 5.0
GLASS_TOP = 12.5
UPPER_TOP = 20.0

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('TPY_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('TPY_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('TPY_glass', (0.16, 0.29, 0.33), 0.12, 0.35)
GREEN = mat('TPY_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('TPY_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


def mesh_obj(name, verts, faces, material):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(material)
    return ob


def extrude(poly, z0, z1, name, material):
    n = len(poly)
    verts = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
    faces.append(list(range(n, 2 * n))); faces.append(list(reversed(range(n))))
    return mesh_obj(name, verts, faces, material)


def box(name, x, y, z, sx, sy, sz, rot, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
    ob = bpy.context.view_layer.objects.active
    ob.name = name; ob.scale = (sx, sy, sz); ob.rotation_euler.z = rot
    ob.data.materials.append(material)
    return ob


def scale_poly(scale):
    return [(midx + (x - midx) * scale, midy + (y - midy) * scale) for x, y in loc]

extrude(loc, 0.0, PODIUM, 'TPY_podium', BRICK)
extrude(loc, PODIUM, PODIUM + 0.4, 'TPY_band_0', WHITE)
glass_poly = scale_poly(0.92)
extrude(glass_poly, PODIUM, GLASS_TOP, 'TPY_glass', GLASS)
extrude(glass_poly, GLASS_TOP, GLASS_TOP + 0.5, 'TPY_band_1', WHITE)

upper = scale_poly(0.78)
extrude(upper, GLASS_TOP + 0.5, UPPER_TOP, 'TPY_upper', WHITE)
extrude(upper, UPPER_TOP, UPPER_TOP + 0.6, 'TPY_roof_slab', WHITE)

# mullions on the glass middle volume
for k in range(len(glass_poly)):
    a = glass_poly[k]; b = glass_poly[(k + 1) % len(glass_poly)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    leng = math.hypot(dx, dy)
    if leng < 1:
        continue
    steps = max(1, int(leng / 2.4))
    rot = math.atan2(dy, dx)
    for j in range(steps):
        t = (j + 0.5) / steps
        box(f'TPY_mull_{k}_{j}', a[0] + dx * t, a[1] + dy * t, (PODIUM + GLASS_TOP) / 2, 0.12, 0.12, GLASS_TOP - PODIUM, rot, WHITE)
for k, z in enumerate((8.0, 10.5)):
    for e in range(len(glass_poly)):
        a = glass_poly[e]; b = glass_poly[(e + 1) % len(glass_poly)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        leng = math.hypot(dx, dy)
        if leng < 1:
            continue
        rot = math.atan2(dy, dx)
        box(f'TPY_transom_{k}_{e}', (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z, leng + 0.2, 0.16, 0.12, rot, WHITE)

# upper vertical slit windows
for k in range(5):
    t = 0.15 + 0.7 * k / 4
    box(f'TPY_slit_{k}', -13.5 + t * 27, -7.0, 16.0, 0.8, 0.25, 5.6, 0.0, GLASS)
    box(f'TPY_sill_{k}', -13.5 + t * 27, -7.1, 13.1, 1.1, 0.35, 0.2, 0.0, WHITE)

# roof garden / pergola
for k, t in enumerate((-0.3, 0.0, 0.3)):
    box(f'TPY_planter_{k}', midx + t * 18, midy + 8, UPPER_TOP + 1.1, 6.0, 1.4, 0.55, 0.0, GREEN)
for k in range(4):
    t = 0.2 + 0.6 * k / 3
    box(f'TPY_pergola_col_{k}', midx + (t - 0.5) * 22, midy - 6, UPPER_TOP + 1.2, 0.35, 0.35, 1.5, 0.0, WHITE)
for k in range(3):
    box(f'TPY_pergola_beam_{k}', midx, midy - 8 + k * 2.5, UPPER_TOP + 2.0, 22.0, 0.15, 0.15, 0.0, WHITE)

# entrance
width = 12.0
box('TPY_atrium', midx, max(ys) + 0.2, 2.7, width, 1.8, 5.4, 0.0, GLASS)
box('TPY_canopy', midx, max(ys) + 1.5, 5.8, width + 2.6, 3.2, 0.35, 0.0, WHITE)
for k in range(4):
    box(f'TPY_mull_ent_{k}', midx - 4.8 + k * 3.2, max(ys) + 1.3, 2.7, 0.14, 0.18, 5.4, 0.0, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_tang', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'tang.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'tang.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('TPY_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'tang.glb')))
