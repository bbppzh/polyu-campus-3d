#!/usr/bin/env python3
"""Hand-authored Seal of Love Foundation Building: brick slab + cylindrical glass stair tower."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'seal of love foundation building')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
PODIUM = 5.0
ROOF = 19.0

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('SOL_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('SOL_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('SOL_glass', (0.16, 0.29, 0.33), 0.12, 0.35)
GREEN = mat('SOL_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('SOL_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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


def cyl(name, radius, depth, x, y, z, material, vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=(x, y, z))
    ob = bpy.context.view_layer.objects.active
    ob.name = name; ob.data.materials.append(material)
    return ob


def parapet(poly, z0, z1, material):
    for i in range(len(poly) - 1):
        a = poly[i]; b = poly[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        leng = math.hypot(dx, dy)
        if leng < 0.2:
            continue
        box(f'SOL_parapet_{i}', (a[0] + b[0]) / 2, (a[1] + b[1]) / 2,
            (z0 + z1) / 2, leng + 0.2, 0.45, z1 - z0, math.atan2(dy, dx), material)

extrude(loc, 0.0, PODIUM, 'SOL_podium', BRICK)
extrude(loc, PODIUM, PODIUM + 0.4, 'SOL_band_0', WHITE)
extrude(loc, PODIUM, ROOF, 'SOL_tower', BRICK)
extrude(loc, ROOF, ROOF + 0.6, 'SOL_roof_slab', WHITE)
parapet(loc, ROOF + 0.6, h, WHITE)

# cylindrical glass stair tower at one end
cyl_x = min(xs) + 3.2
cyl('SOL_glass_tower', 5.2, ROOF - PODIUM, cyl_x, midy, (PODIUM + ROOF) / 2, GLASS)
for k in range(8):
    ang = k / 8 * math.pi * 2
    px = cyl_x + math.cos(ang) * 5.2
    py = midy + math.sin(ang) * 5.2
    box(f'SOL_tower_mull_{k}', px, py, (PODIUM + ROOF) / 2, 0.14, 0.14, ROOF - PODIUM, 0.0, WHITE)
for y, rr in ((PODIUM, 5.35), (ROOF, 5.35)):
    cyl(f'SOL_ring_{int(y)}', rr, 0.35, cyl_x, midy, y, WHITE)

# roof garden + pavilion
for k, t in enumerate((-0.25, 0.05, 0.3)):
    box(f'SOL_planter_{k}', midx + t * 18, midy + 8, ROOF + 1.1, 6.0, 1.5, 0.55, 0.0, GREEN)
cyl('SOL_pavilion', 2.8, 2.4, midx - 8, midy - 8, ROOF + 1.6, WHITE, 16)
cyl('SOL_pavilion_roof', 3.2, 0.3, midx - 8, midy - 8, ROOF + 2.9, WHITE, 16)

# entrance on the long south-facing side
ent_y = max(ys) + 0.2
width = 14.0
box('SOL_atrium', midx + 6, ent_y, 2.8, width, 1.8, 5.6, 0.0, GLASS)
box('SOL_canopy', midx + 6, ent_y + 1.5, 6.0, width + 2.6, 3.2, 0.35, 0.0, WHITE)
for k in range(5):
    box(f'SOL_mull_{k}', midx + 6 - 5.6 + k * 2.8, ent_y + 1.3, 2.8, 0.14, 0.18, 5.6, 0.0, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_seal', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'seal.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'seal.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('SOL_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'seal.glb')))
