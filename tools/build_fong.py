#!/usr/bin/env python3
"""Hand-authored Fong Shu Chuen Hall: low brick hall with clerestory lantern and deep canopy."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'fong shu chuen hall')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
BASE = 4.2

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('FSC_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('FSC_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('FSC_glass', (0.16, 0.29, 0.33), 0.12, 0.35)
GREEN = mat('FSC_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('FSC_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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

# base hall
extrude(loc, 0.0, BASE, 'FSC_base', BRICK)
extrude(loc, BASE, BASE + 0.5, 'FSC_fascia', WHITE)

# clerestory lantern
cler = scale_poly(0.86)
extrude(cler, BASE + 0.5, h - 0.5, 'FSC_clerestory', GLASS)
for k in range(len(cler)):
    a = cler[k]; b = cler[(k + 1) % len(cler)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    leng = math.hypot(dx, dy)
    if leng < 1:
        continue
    steps = max(1, int(leng / 2.4))
    rot = math.atan2(dy, dx)
    for j in range(steps):
        t = (j + 0.5) / steps
        box(f'FSC_mull_{k}_{j}', a[0] + dx * t, a[1] + dy * t, (BASE + h) / 2, 0.12, 0.12, h - BASE - 1.0, rot, WHITE)
extrude(cler, h - 0.5, h, 'FSC_roof', WHITE)

# choose front facade facing core
best = None
poly = [(x - cx, z - cz) for x, z in fp]
for i in range(len(fp) - 1):
    ax, az = fp[i][0] - cx, fp[i][1] - cz
    bx, bz = fp[i + 1][0] - cx, fp[i + 1][1] - cz
    dx, dz = bx - ax, bz - az; leng = math.hypot(dx, dz)
    if leng < 12: continue
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

# glazed lobby and deep canopy
lw = min(elen * 0.55, 18.0)
box('FSC_lobby', bx + bnx * 0.5, by + bny * 0.5, 2.1, lw, 0.5, 4.2, rot, GLASS)
for k in range(5):
    off = -lw / 2 + lw * (k + 0.5) / 5
    box(f'FSC_lobby_mull_{k}', bx + bnx * 0.75 + bvx * off, by + bny * 0.75 + bvy * off, 2.1, 0.14, 0.18, 4.2, rot, WHITE)

box('FSC_canopy', bx + bnx * 3.2, by + bny * 3.2, BASE + 0.65, lw + 5.0, 6.4, 0.4, rot, WHITE)
for k in range(4):
    off = -lw / 2 + lw * (k + 0.5) / 4
    box(f'FSC_col_{k}', bx + bnx * 5.8 + bvx * off, by + bny * 5.8 + bvy * off, BASE / 2, 0.4, 0.4, BASE, rot, WHITE)

# roof planters on base terrace
for k, t in enumerate((-0.3, 0.0, 0.3)):
    box(f'FSC_planter_{k}', midx + t * 18, midy + 9, BASE + 0.8, 6.0, 1.4, 0.55, 0.0, GREEN)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_fong', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'fong.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'fong.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('FSC_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'fong.glb')))
