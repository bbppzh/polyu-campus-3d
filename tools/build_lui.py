#!/usr/bin/env python3
"""Hand-authored Lui Che Woo Building: white tower with vertical glass slits."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'lui che woo building')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
PODIUM = 6.0
TOWER_TOP = 20.0

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('LCW_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('LCW_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('LCW_glass', (0.16, 0.29, 0.33), 0.12, 0.35)
GREEN = mat('LCW_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('LCW_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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

extrude(loc, 0.0, PODIUM, 'LCW_podium', BRICK)
extrude(loc, PODIUM, PODIUM + 0.45, 'LCW_band', WHITE)
extrude(loc, PODIUM, TOWER_TOP, 'LCW_tower', WHITE)
extrude(loc, TOWER_TOP, TOWER_TOP + 0.6, 'LCW_roof_slab', WHITE)
pent = scale_poly(0.55)
extrude(pent, TOWER_TOP + 0.6, h, 'LCW_pavilion', GLASS)
extrude(pent, h, h + 0.4, 'LCW_roof', WHITE)

# choose long facade facing core
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

# vertical glass slit windows
for k in range(7):
    t = 0.12 + 0.76 * k / 6
    px = bx + bvx * (t - 0.5) * elen + bnx * 0.16
    py = by + bvy * (t - 0.5) * elen + bny * 0.16
    box(f'LCW_slit_{k}', px, py, 13.0, 0.7, 0.25, 11.0, rot, GLASS)
    box(f'LCW_sill_{k}', px + bnx * 0.08, py + bny * 0.08, 8.2, 1.0, 0.35, 0.25, rot, WHITE)

# glass corner volume at one end
core_t = 0.12
px = bx + bvx * (core_t - 0.5) * elen + bnx * 0.8
py = by + bvy * (core_t - 0.5) * elen + bny * 0.8
box('LCW_corner_glass', px, py, (PODIUM + TOWER_TOP) / 2, 3.2, 2.4, TOWER_TOP - PODIUM, rot, GLASS)
for k in range(3):
    off = -1.1 + k * 1.1
    box(f'LCW_corner_mull_{k}', px + bvx * off + bnx * 1.25, py + bvy * off + bny * 1.25,
        (PODIUM + TOWER_TOP) / 2, 0.14, 0.16, TOWER_TOP - PODIUM, rot, WHITE)

# roof terrace planters
for k, t in enumerate((-0.25, 0.05, 0.3)):
    box(f'LCW_planter_{k}', midx + t * 16, midy + 9, TOWER_TOP + 1.1, 6.0, 1.5, 0.6, 0.0, GREEN)
box('LCW_roof_plant', midx - 5, midy - 8, h + 1.2, 6.0, 4.0, 1.8, 0.0, WHITE)

# entrance
width = min(elen * 0.4, 15.0)
box('LCW_atrium', bx + bnx * 1.3, by + bny * 1.3, 2.8, width, 2.2, 5.6, rot, GLASS)
box('LCW_canopy', bx + bnx * 2.5, by + bny * 2.5, 6.0, width + 2.4, 3.4, 0.35, rot, WHITE)
for k in range(5):
    off = -width / 2 + width * (k + 0.5) / 5
    box(f'LCW_mull_{k}', bx + bnx * 2.4 + bvx * off, by + bny * 2.4 + bvy * off, 2.8, 0.14, 0.18, 5.6, rot, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_lui', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'lui.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'lui.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('LCW_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'lui.glb')))
