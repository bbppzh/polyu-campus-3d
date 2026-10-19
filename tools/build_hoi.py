#!/usr/bin/env python3
"""Hand-authored House of Innovation: brick podium, glass lantern tower, roof pergola."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'house of innovation')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
PODIUM = 4.0
GLASS_TOP = 16.0

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('HOI_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('HOI_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('HOI_glass', (0.16, 0.29, 0.33), 0.12, 0.35)
GREEN = mat('HOI_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('HOI_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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

extrude(loc, 0.0, PODIUM, 'HOI_podium', BRICK)
extrude(loc, PODIUM, PODIUM + 0.4, 'HOI_band', WHITE)
glass_poly = scale_poly(0.94)
extrude(glass_poly, PODIUM, GLASS_TOP, 'HOI_glass', GLASS)
extrude(loc, GLASS_TOP, GLASS_TOP + 0.55, 'HOI_roof_slab', WHITE)

# mullions and transoms around the glass lantern
for k in range(len(glass_poly)):
    a = glass_poly[k]; b = glass_poly[(k + 1) % len(glass_poly)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    leng = math.hypot(dx, dy)
    if leng < 1:
        continue
    steps = max(1, int(leng / 2.6))
    rot = math.atan2(dy, dx)
    for j in range(steps):
        t = (j + 0.5) / steps
        x = a[0] + dx * t; y = a[1] + dy * t
        box(f'HOI_mull_{k}_{j}', x, y, (PODIUM + GLASS_TOP) / 2, 0.12, 0.12, GLASS_TOP - PODIUM, rot, WHITE)
for k, z in enumerate((7.0, 10.0, 13.0)):
    for e in range(len(glass_poly)):
        a = glass_poly[e]; b = glass_poly[(e + 1) % len(glass_poly)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        leng = math.hypot(dx, dy)
        if leng < 1:
            continue
        rot = math.atan2(dy, dx)
        box(f'HOI_transom_{k}_{e}', (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, z, leng + 0.2, 0.16, 0.14, rot, WHITE)

# brick service core at one side
box('HOI_core', min(xs) + 3.2, midy, (PODIUM + GLASS_TOP) / 2, 4.0, 8.0, GLASS_TOP - PODIUM, 0.0, BRICK)

# A complete supported pergola; dimensions are visual approximations.
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
for k, t in enumerate((-0.2, 0.15)):
    box(f'HOI_planter_{k}', midx + t * 12, midy + 6, GLASS_TOP + 1.0, 5.0, 1.4, 0.55, 0.0, GREEN)
box('HOI_roof_plant', midx + 3, midy + 2, GLASS_TOP + 1.0, 4.0, 3.0, 1.4, 0.0, WHITE)

# entrance
width = 9.0
box('HOI_atrium', midx, max(ys) + 0.2, 2.7, width, 1.8, 5.4, 0.0, GLASS)
box('HOI_canopy', midx, max(ys) + 1.5, 5.8, width + 2.6, 3.2, 0.35, 0.0, WHITE)
for k in range(4):
    box(f'HOI_mull_ent_{k}', midx - 3.6 + k * 2.4, max(ys) + 1.3, 2.7, 0.14, 0.18, 5.4, 0.0, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_hoi', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'hoi.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'hoi.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('HOI_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'hoi.glb')))
