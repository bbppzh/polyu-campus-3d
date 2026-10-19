#!/usr/bin/env python3
"""Hand-authored CMA Building: brick slab with planted terraces + rooftop pergola."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'cma building')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
PODIUM = 5.0
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


BRICK = mat('CMA_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('CMA_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('CMA_glass', (0.16, 0.29, 0.33), 0.12, 0.35)
GREEN = mat('CMA_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('CMA_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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


extrude(loc, 0.0, PODIUM, 'CMA_podium', BRICK)
extrude(loc, PODIUM, PODIUM + 0.45, 'CMA_band', WHITE)
extrude(loc, PODIUM, TOWER_TOP, 'CMA_tower', BRICK)
extrude(loc, TOWER_TOP, TOWER_TOP + 0.5, 'CMA_roof_slab', WHITE)

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

# three planted terraces
for k, y in enumerate((9.0, 14.0, 19.0)):
    box(f'CMA_terrace_{k}', bx + bnx * 0.9, by + bny * 0.9, y, elen * 0.8, 1.8, 0.25, rot, WHITE)
    box(f'CMA_rail_{k}', bx + bnx * 1.70, by + bny * 1.70, y + 0.55, elen * 0.8, 0.12, 0.85, rot, GLASS)
    box(f'CMA_planter_{k}', bx + bnx * 1.25, by + bny * 1.25, y + 0.45, elen * 0.7, 0.7, 0.6, rot, GREEN)

# A complete supported pergola; dimensions are visual approximations.
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
box('CMA_roof_plant', midx + 5, midy - 6, TOWER_TOP + 1.2, 6.0, 4.0, 1.8, 0.0, WHITE)

# entrance
width = min(elen * 0.4, 15.0)
box('CMA_atrium', bx + bnx * 1.3, by + bny * 1.3, 2.8, width, 2.2, 5.6, rot, GLASS)
box('CMA_canopy', bx + bnx * 2.5, by + bny * 2.5, 6.0, width + 2.4, 3.4, 0.35, rot, WHITE)
for k in range(5):
    off = -width / 2 + width * (k + 0.5) / 5
    box(f'CMA_mull_{k}', bx + bnx * 2.4 + bvx * off, by + bny * 2.4 + bvy * off, 2.8, 0.14, 0.18, 5.6, rot, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_cma', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'cma.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'cma.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('CMA_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'cma.glb')))
