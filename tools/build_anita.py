#!/usr/bin/env python3
"""Hand-authored Anita Chan Lai Ling Building: low brick block, tall glass portal, roof pergola."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'anita chan lai ling building')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
PODIUM = 4.0
ROOF = 13.5

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('ACL_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('ACL_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('ACL_glass', (0.16, 0.29, 0.33), 0.12, 0.35)
GREEN = mat('ACL_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('ACL_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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


extrude(loc, 0.0, PODIUM, 'ACL_podium', BRICK)
extrude(loc, PODIUM, PODIUM + 0.4, 'ACL_band_0', WHITE)
extrude(loc, PODIUM, ROOF, 'ACL_tower', BRICK)
extrude(loc, ROOF, ROOF + 0.6, 'ACL_roof_slab', WHITE)
extrude(loc, ROOF + 0.6, h, 'ACL_parapet', WHITE)

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

# tall glazed portal
portal_w = min(elen * 0.5, 16.0)
box('ACL_portal_glass', bx + bnx * 0.5, by + bny * 0.5, 3.75, portal_w, 0.4, 7.5, rot, GLASS)
box('ACL_portal_top', bx + bnx * 0.7, by + bny * 0.7, 7.7, portal_w + 1.2, 0.9, 0.5, rot, WHITE)
for k in range(2):
    off = (-0.5 if k == 0 else 0.5) * (portal_w + 0.6)
    box(f'ACL_portal_side_{k}', bx + bnx * 0.7 + bvx * off, by + bny * 0.7 + bvy * off,
        3.75, 0.6, 0.9, 7.5, rot, WHITE)
for k in range(5):
    off = -portal_w / 2 + portal_w * (k + 0.5) / 5
    box(f'ACL_portal_mull_{k}', bx + bnx * 0.75 + bvx * off, by + bny * 0.75 + bvy * off,
        3.75, 0.14, 0.18, 7.5, rot, WHITE)
box('ACL_portal_canopy', bx + bnx * 2.4, by + bny * 2.4, 7.9, portal_w + 4.0, 3.6, 0.35, rot, WHITE)

# upper vertical slit windows
for k in range(5):
    off = -portal_w * 0.4 + portal_w * 0.8 * k / 4
    box(f'ACL_slit_{k}', bx + bnx * 0.2 + bvx * off, by + bny * 0.2 + bvy * off,
        11.0, 0.8, 0.25, 4.2, rot, GLASS)

# roof terrace pergola and planters
for k in range(4):
    t = 0.15 + 0.7 * k / 3
    box(f'ACL_pergola_col_{k}', midx + bvx * (t - 0.5) * elen, midy + bvy * (t - 0.5) * elen,
        h + 1.0, 0.35, 0.35, 1.6, 0.0, WHITE)
for k in range(4):
    box(f'ACL_pergola_beam_{k}', midx + bvx * (-0.35 + k * 0.23) * elen, midy + bvy * (-0.35 + k * 0.23) * elen,
        h + 1.8, 0.15, 0.15, 3.2, rot, WHITE)
for k, t in enumerate((-0.25, 0.05, 0.3)):
    box(f'ACL_planter_{k}', midx + t * 16, midy - 8, h + 0.5, 6.0, 1.4, 0.55, 0.0, GREEN)

# steps
for k in range(2):
    box(f'ACL_step_{k}', bx + bnx * (1.2 + k * 0.45), by + bny * (1.2 + k * 0.45), 0.1 + k * 0.16,
        portal_w * 0.8, 2.0 + k * 0.7, 0.16, rot, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_anita', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'anita.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'anita.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('ACL_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'anita.glb')))
