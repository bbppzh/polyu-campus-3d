#!/usr/bin/env python3
"""Hand-authored Choi Kai Yau Building: banded long block + glass crown."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'choi kai yau building')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
PODIUM = 8.0
CROWN = 28.0

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('CHK_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('CHK_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('CHK_glass', (0.16, 0.29, 0.33), 0.12, 0.35)
GREEN = mat('CHK_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('CHK_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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

tower = scale_poly(0.92)
crown = scale_poly(0.96)
extrude(loc, 0.0, PODIUM, 'CHK_podium', BRICK)
extrude(loc, PODIUM, PODIUM + 0.45, 'CHK_podium_band', WHITE)
extrude(tower, PODIUM, CROWN, 'CHK_tower', BRICK)
# horizontal white floor bands wrapping the long block
for k, y in enumerate((11.2, 14.4, 17.6, 20.8, 24.0)):
    band = scale_poly(0.928)
    extrude(band, y - 0.18, y + 0.18, f'CHK_band_{k}', WHITE)
extrude(crown, CROWN, h, 'CHK_crown', GLASS)
extrude(crown, h, h + 0.55, 'CHK_roof', WHITE)

# mullions on the glass crown
for k in range(len(crown)):
    a = crown[k]; b = crown[(k + 1) % len(crown)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    leng = math.hypot(dx, dy)
    if leng < 1:
        continue
    steps = max(1, int(leng / 2.8))
    for j in range(steps):
        t = (j + 0.5) / steps
        x = a[0] + dx * t; y = a[1] + dy * t
        box(f'CHK_mull_{k}_{j}', x, y, (CROWN + h) / 2, 0.14, 0.14, h - CROWN, 0.0, WHITE)

# roof plant
box('CHK_roof_plant', midx - 4, midy + 2, h + 1.4, 8.0, 5.0, 2.0, 0.0, WHITE)
for i in range(2):
    box(f'CHK_ac_{i}', midx + 5 + i * 3.2, midy - 2, h + 0.8, 2.0, 1.5, 1.0, 0.0, WHITE)

# terrace planters at the 28m setback
for i, t in enumerate((-0.3, 0.0, 0.3)):
    box(f'CHK_planter_{i}', midx + t * 22, min(ys) + 3, CROWN + 0.55, 7.0, 1.5, 0.6, 0.0, GREEN)

# entrance
best = None
poly = [(x - cx, z - cz) for x, z in fp]
for i in range(len(fp) - 1):
    ax, az = fp[i][0] - cx, fp[i][1] - cz
    bx, bz = fp[i + 1][0] - cx, fp[i + 1][1] - cz
    dx, dz = bx - ax, bz - az; leng = math.hypot(dx, dz)
    if leng < 8: continue
    mx, mz = (ax + bx) / 2, (az + bz) / 2
    nx, nz = dz / leng, -dx / leng
    def inside(px, pz):
        ins = False
        for k in range(len(poly)):
            x1, z1 = poly[k]; x2, z2 = poly[(k + 1) % len(poly)]
            if (z1 > pz) != (z2 > pz):
                xin = (x2 - x1) * (pz - z1) / (z2 - z1 + 1e-12) + x1
                if px < xin: ins = not ins
        return ins
    if inside(mx + nx * 2.0, mz + nz * 2.0): nx, nz = -nx, -nz
    facing = nx * (-mx) + nz * (-mz)
    score = facing * (leng ** 0.3)
    if best is None or score > best[6]: best = (math.hypot(mx, mz), mx, mz, dx / leng, dz / leng, leng, score, nx, nz)
_, mx, mz, edx, edz, elen, _, nx, nz = best
bx, by = mx, -mz; bvx, bvy = edx, -edz; bnx, bny = nx, -nz
rot = math.atan2(bvy, bvx)
width = min(max(elen * 0.7, 10.0), 24.0)
box('CHK_atrium', bx + bnx * 1.4, by + bny * 1.4, 3.4, width, 2.5, 6.6, rot, GLASS)
box('CHK_canopy', bx + bnx * 2.7, by + bny * 2.7, 7.0, width + 3.0, 4.2, 0.4, rot, WHITE)
for k in range(7):
    off = -width / 2 + width * (k + 0.5) / 7
    box(f'CHK_mull_ent_{k}', bx + bnx * 2.6 + bvx * off, by + bny * 2.6 + bvy * off, 3.4, 0.15, 0.2, 6.6, rot, WHITE)
for k in range(2):
    box(f'CHK_step_{k}', bx + bnx * (1.6 + k * 0.45), by + bny * (1.6 + k * 0.45), 0.1 + k * 0.16, width * 0.75, 2.2 + k * 0.7, 0.16, rot, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_choi', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'choi.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'choi.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('CHK_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'choi.glb')))
