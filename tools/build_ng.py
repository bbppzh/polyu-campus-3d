#!/usr/bin/env python3
"""Hand-authored Ng Wing Hong Building: stepped brick/white tower with glass core."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'ng wing hong building')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
PODIUM = 7.0
SETBACK = 18.0

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('NWH_brick', (0.56, 0.22, 0.17), 0.8)
UPPER = mat('NWH_upper', (0.87, 0.84, 0.78), 0.6)
WHITE = mat('NWH_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('NWH_glass', (0.16, 0.29, 0.33), 0.12, 0.35)
GREEN = mat('NWH_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('NWH_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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

upper = scale_poly(0.82)
extrude(loc, 0.0, PODIUM, 'NWH_podium', BRICK)
extrude(loc, PODIUM, PODIUM + 0.45, 'NWH_band_0', WHITE)
extrude(loc, PODIUM, SETBACK, 'NWH_lower', BRICK)
extrude(loc, SETBACK, SETBACK + 0.45, 'NWH_band_1', WHITE)
extrude(upper, SETBACK, h, 'NWH_upper', UPPER)
extrude(upper, h, h + 0.55, 'NWH_roof', WHITE)

# pick long facade facing core
best = None
poly = [(x - cx, z - cz) for x, z in fp]
for i in range(len(fp) - 1):
    ax, az = fp[i][0] - cx, fp[i][1] - cz
    bx, bz = fp[i + 1][0] - cx, fp[i + 1][1] - cz
    dx, dz = bx - ax, bz - az; leng = math.hypot(dx, dz)
    if leng < 15: continue
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
    score = facing * leng
    if best is None or score > best[6]: best = (math.hypot(mx, mz), mx, mz, dx, dz, leng, score, nx, nz)
_, mx, mz, vx, vz, elen, _, nx, nz = best
edx, edz = vx / elen, vz / elen
bx, by = mx, -mz; bvx, bvy = edx, -edz; bnx, bny = nx, -nz
rot = math.atan2(bvy, bvx)

# vertical glass core near one end
core_t = 0.2
core_x = bx + bvx * (core_t - 0.5) * elen + bnx * 1.0
core_y = by + bvy * (core_t - 0.5) * elen + bny * 1.0
box('NWH_core', core_x, core_y, (PODIUM + h) / 2, 4.0, 2.4, h - PODIUM, rot, GLASS)
for k in range(3):
    off = -1.3 + k * 1.3
    box(f'NWH_core_mull_{k}', core_x + bvx * off + bnx * 1.25, core_y + bvy * off + bny * 1.25,
        (PODIUM + h) / 2, 0.14, 0.16, h - PODIUM, rot, WHITE)

# roof terrace at the 18m setback
for k, t in enumerate((-0.3, 0.0, 0.3)):
    box(f'NWH_planter_{k}', midx + t * 22, midy + 10, SETBACK + 0.6, 7.0, 1.6, 0.6, 0.0, GREEN)
box('NWH_pavilion', midx - 8, midy - 9, SETBACK + 1.7, 7.0, 5.0, 2.4, 0.0, WHITE)
box('NWH_roof_plant', midx + 6, midy + 2, h + 1.2, 6.0, 4.0, 1.8, 0.0, WHITE)
for i in range(2):
    box(f'NWH_ac_{i}', midx + 2 + i * 3, midy - 4, h + 0.8, 1.8, 1.4, 1.0, 0.0, WHITE)

# entrance
width = min(elen * 0.5, 18.0)
box('NWH_atrium', bx + bnx * 1.2, by + bny * 1.2, 3.0, width, 2.4, 6.0, rot, GLASS)
box('NWH_canopy', bx + bnx * 2.4, by + bny * 2.4, 6.3, width + 2.8, 4.0, 0.35, rot, WHITE)
for k in range(6):
    off = -width / 2 + width * (k + 0.5) / 6
    box(f'NWH_mull_{k}', bx + bnx * 2.3 + bvx * off, by + bny * 2.3 + bvy * off, 3.0, 0.15, 0.2, 6.0, rot, WHITE)
for k in range(2):
    box(f'NWH_step_{k}', bx + bnx * (1.4 + k * 0.4), by + bny * (1.4 + k * 0.4), 0.1 + k * 0.15, width * 0.8, 2.0 + k * 0.7, 0.16, rot, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_ng', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'ng.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'ng.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('NWH_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'ng.glb')))
