#!/usr/bin/env python3
"""Hand-authored Mong Man Wai Building: brick slab with balcony bands + glass stair core."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'mong man wai building')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
PODIUM = 6.0
ROOF = 26.5

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('MMW_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('MMW_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('MMW_glass', (0.16, 0.29, 0.33), 0.12, 0.35)
GREEN = mat('MMW_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('MMW_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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


extrude(loc, 0.0, PODIUM, 'MMW_podium', BRICK)
extrude(loc, PODIUM, PODIUM + 0.45, 'MMW_band', WHITE)
extrude(loc, PODIUM, ROOF, 'MMW_tower', BRICK)
extrude(loc, ROOF, ROOF + 0.55, 'MMW_roof', WHITE)

# pick the long facade facing the core
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

# balcony slabs + glass balustrades
for k, y in enumerate((9.0, 12.2, 15.4, 18.6, 21.8, 25.0)):
    box(f'MMW_balcony_{k}', bx + bnx * 0.8, by + bny * 0.8, y, elen * 0.78, 1.6, 0.22, rot, WHITE)
    box(f'MMW_balustrade_{k}', bx + bnx * 1.55, by + bny * 1.55, y + 0.5, elen * 0.78, 0.12, 0.85, rot, GLASS)

# vertical glass stair core near one end of the facade
core_x = bx + bvx * (0.18 - 0.5) * elen + bnx * 1.1
core_y = by + bvy * (0.18 - 0.5) * elen + bny * 1.1
box('MMW_core', core_x, core_y, (PODIUM + ROOF) / 2, 4.2, 2.6, ROOF - PODIUM, rot, GLASS)
for k in range(3):
    off = -1.4 + k * 1.4
    box(f'MMW_core_mull_{k}', core_x + bvx * off + bnx * 1.35, core_y + bvy * off + bny * 1.35,
        (PODIUM + ROOF) / 2, 0.14, 0.16, ROOF - PODIUM, rot, WHITE)

# roof terrace: planters + small pavilion
for k, t in enumerate((-0.25, 0.1, 0.35)):
    box(f'MMW_planter_{k}', midx + t * 18, midy + 14, ROOF + 0.6, 6.0, 1.6, 0.6, 0.0, GREEN)
box('MMW_pavilion', midx - 6, midy - 10, ROOF + 1.8, 7.0, 5.0, 2.6, 0.0, WHITE)
box('MMW_roof_plant', midx + 7, midy + 2, ROOF + 1.3, 6.0, 4.0, 1.8, 0.0, WHITE)

# entrance on the same facade
width = min(elen * 0.45, 18.0)
box('MMW_atrium', bx + bnx * 1.2, by + bny * 1.2, 2.9, width, 2.4, 5.6, rot, GLASS)
box('MMW_canopy', bx + bnx * 2.4, by + bny * 2.4, 6.0, width + 2.8, 4.0, 0.35, rot, WHITE)
for k in range(6):
    off = -width / 2 + width * (k + 0.5) / 6
    box(f'MMW_mull_{k}', bx + bnx * 2.3 + bvx * off, by + bny * 2.3 + bvy * off, 2.9, 0.15, 0.2, 5.6, rot, WHITE)
for k in range(2):
    box(f'MMW_step_{k}', bx + bnx * (1.4 + k * 0.4), by + bny * (1.4 + k * 0.4), 0.1 + k * 0.15, width * 0.8, 2.0 + k * 0.7, 0.16, rot, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_mong', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'mong.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'mong.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('MMW_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'mong.glb')))
