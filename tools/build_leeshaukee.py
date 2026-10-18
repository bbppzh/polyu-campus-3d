#!/usr/bin/env python3
"""Build a custom Lee Shau Kee Building (long block + glazed atrium/terrace)."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'lee shau kee building')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
LOWER = 10.0

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('LSKB_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('LSKB_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('LSKB_glass', (0.16, 0.28, 0.32), 0.12, 0.35)
GREEN = mat('LSKB_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('LSKB_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


def mesh_obj(name, verts, faces, material, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(material)
    if smooth:
        for p in me.polygons: p.use_smooth = True
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


upper = [(midx + (x - midx) * 0.90, midy + (y - midy) * 0.88) for x, y in loc]
extrude(loc, 0.0, LOWER, 'LSKB_lower', BRICK)
extrude(upper, LOWER, h, 'LSKB_upper', WHITE)
extrude(loc, LOWER - 0.5, LOWER, 'LSKB_terrace_edge', WHITE)
extrude(upper, h, h + 0.7, 'LSKB_roof_edge', WHITE)

# roof terrace planters and skylight
for i, t in enumerate((-0.35, 0.0, 0.35)):
    bx = midx + t * (max(xs) - min(xs))
    box(f'LSKB_planter_{i}', bx, midy - 18, LOWER + 0.6, 12.0, 2.0, 1.0, 0.0, GREEN)
box('LSKB_skylight', midx - 20, midy + 4, h + 1.2, 14.0, 8.0, 1.0, 0.0, GLASS)
box('LSKB_roof_plant', midx + 20, midy - 8, h + 1.5, 10.0, 6.0, 2.0, 0.0, WHITE)

# entrance on nearest long edge facing the core
best = None
poly = [(x - cx, z - cz) for x, z in fp]
for i in range(len(fp) - 1):
    ax, az = fp[i][0] - cx, fp[i][1] - cz
    bx, bz = fp[i + 1][0] - cx, fp[i + 1][1] - cz
    dx, dz = bx - ax, bz - az; leng = math.hypot(dx, dz)
    if leng < 12: continue
    mx, mz = (ax + bx) / 2, (az + bz) / 2
    nx1, nz1 = dz / leng, -dx / leng


    def inside(px, pz):
        ins = False
        for k in range(len(poly)):
            x1, z1 = poly[k]; x2, z2 = poly[(k + 1) % len(poly)]
            if (z1 > pz) != (z2 > pz):
                xin = (x2 - x1) * (pz - z1) / (z2 - z1 + 1e-12) + x1
                if px < xin: ins = not ins
        return ins
    if inside(mx + nx1 * 2.0, mz + nz1 * 2.0): nx1, nz1 = -nx1, -nz1
    facing = nx1 * (-mx) + nz1 * (-mz)
    score = facing * (leng ** 0.5)
    if best is None or score > best[6]: best = (math.hypot(mx, mz), mx, mz, dx / leng, dz / leng, leng, score, nx1, nz1)
_, mx, mz, edx, edz, elen, _, nx, nz = best
bx, by = mx, -mz; bvx, bvy = edx, -edz; bnx, bny = nx, -nz
rot = math.atan2(bvy, bvx)
width = min(elen * 0.72, 32.0)

box('LSKB_atrium', bx + bnx * 1.6, by + bny * 1.6, 4.5, width, 3.0, 9.0, rot, GLASS)
box('LSKB_canopy', bx + bnx * 3.1, by + bny * 3.1, 9.5, width + 3.0, 4.8, 0.45, rot, WHITE)
for k in range(8):
    off = -width / 2 + width * (k + 0.5) / 8
    box(f'LSKB_mullion_{k}', bx + bnx * 3.05 + bvx * off, by + bny * 3.05 + bvy * off, 4.5, 0.18, 0.22, 9.0, rot, WHITE)
for k in range(2):
    box(f'LSKB_transom_{k}', bx + bnx * 3.07, by + bny * 3.07, 3.0 + k * 3.4, width, 0.22, 0.16, rot, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_leeshaukee', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'leeshaukee.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'leeshaukee.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('LSKB_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'leeshaukee.glb')))
