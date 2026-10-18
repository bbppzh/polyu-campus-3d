#!/usr/bin/env python3
"""Build a custom Industrial Centre after repairing its OSM footprint."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'industrial centre')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('IND_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('IND_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('IND_glass', (0.16, 0.28, 0.32), 0.12, 0.35)
GREEN = mat('IND_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('IND_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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
    poly = [p for i,p in enumerate(poly) if i == 0 or math.dist(p,poly[i-1]) > 1e-7]
    if len(poly)>1 and math.dist(poly[0],poly[-1]) < 1e-7: poly = poly[:-1]
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


extrude(loc, 0.0, h, 'IND_mass', BRICK)
extrude(loc, h, h + 0.7, 'IND_parapet', WHITE)
extrude(loc, 12.0, 12.5, 'IND_band', WHITE)

xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
# roof plant / AC / vents
box('IND_roof_plant', midx - 4, midy + 3, h + 1.6, 10.0, 7.0, 2.4, 0.0, WHITE)
for i in range(3):
    box(f'IND_roof_ac_{i}', midx + 6 + i * 4, midy - 4, h + 0.8, 2.4, 1.8, 1.2, 0.0, WHITE)
for i in range(3):
    box(f'IND_vent_{i}', midx - 8 + i * 3, midy - 8, h + 1.2, 0.7, 0.7, 2.4, 0.0, DARK)

# entrance
best = None
poly = [(x - cx, z - cz) for x, z in fp]
for i in range(len(fp) - 1):
    ax, az = fp[i][0] - cx, fp[i][1] - cz
    bx, bz = fp[i + 1][0] - cx, fp[i + 1][1] - cz
    dx, dz = bx - ax, bz - az; leng = math.hypot(dx, dz)
    if leng < 8: continue
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
width = min(elen * 0.7, 24.0)
box('IND_atrium', bx + bnx * 1.5, by + bny * 1.5, 5.0, width, 2.8, 10.0, rot, GLASS)
box('IND_canopy', bx + bnx * 2.9, by + bny * 2.9, 10.4, width + 3.0, 4.6, 0.4, rot, WHITE)
for k in range(6):
    off = -width / 2 + width * (k + 0.5) / 6
    box(f'IND_mullion_{k}', bx + bnx * 2.85 + bvx * off, by + bny * 2.85 + bvy * off, 5.0, 0.16, 0.22, 10.0, rot, WHITE)
for k in range(3):
    box(f'IND_transom_{k}', bx + bnx * 2.86, by + bny * 2.86, 2.5 + k * 3.3, width, 0.2, 0.16, rot, WHITE)
for k in range(2):
    box(f'IND_step_{k}', bx + bnx * (1.8 + k * 0.45), by + bny * (1.8 + k * 0.45), 0.1 + k * 0.18, width * 0.7, 2.2 + k * 0.8, 0.18, rot, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_industrial', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'industrial.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'industrial.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('IND_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'industrial.glb')))
