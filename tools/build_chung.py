#!/usr/bin/env python3
"""Hand-authored Chung Sze Yuen Building: wide white block with ribbon glazing and floating roof."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'chung sze yuen building')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
PODIUM = 4.0
ROOF = 13.0

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('CSY_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('CSY_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('CSY_glass', (0.16, 0.29, 0.33), 0.12, 0.35)
GREEN = mat('CSY_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('CSY_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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

def parapet(poly, z0, z1, material):
    for i in range(len(poly) - 1):
        a = poly[i]; b = poly[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        leng = math.hypot(dx, dy)
        if leng < 0.2:
            continue
        box(f'CSY_parapet_{i}', (a[0] + b[0]) / 2, (a[1] + b[1]) / 2,
            (z0 + z1) / 2, leng + 0.2, 0.45, z1 - z0, math.atan2(dy, dx), material)

extrude(loc, 0.0, PODIUM, 'CSY_podium', BRICK)
extrude(loc, PODIUM, PODIUM + 0.4, 'CSY_band', WHITE)
extrude(loc, PODIUM, ROOF, 'CSY_upper', WHITE)
extrude(loc, ROOF, ROOF + 0.8, 'CSY_roof_slab', WHITE)
parapet(loc, ROOF + 0.8, h, WHITE)

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

# ribbon glazing bands wrapping the footprint exactly
rw = min(elen * 0.82, 50.0)
for k, y in enumerate((6.0, 8.8, 11.6)):
    band = scale_poly(1.006)
    extrude(band, y - 0.6, y + 0.6, f'CSY_ribbon_{k}', GLASS)
    trim = scale_poly(1.014)
    extrude(trim, y + 0.6, y + 0.8, f'CSY_ribbon_top_{k}', WHITE)

# floating entrance canopy / roof terrace
box('CSY_roof_canopy', bx + bnx * 1.2, by + bny * 1.2, ROOF + 0.45, rw + 4.0, 3.8, 0.35, rot, WHITE)
for k, t in enumerate((-0.3, 0.0, 0.3)):
    box(f'CSY_planter_{k}', midx + t * 24, midy + 8, ROOF + 1.2, 7.0, 1.5, 0.55, 0.0, GREEN)
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))

# entrance
width = 14.0
box('CSY_atrium', midx, max(ys) + 0.2, 2.7, width, 1.8, 5.4, 0.0, GLASS)
box('CSY_canopy', midx, max(ys) + 1.5, 5.8, width + 2.6, 3.2, 0.35, 0.0, WHITE)
for k in range(5):
    box(f'CSY_mull_{k}', midx - 5.6 + k * 2.8, max(ys) + 1.3, 2.7, 0.14, 0.18, 5.4, 0.0, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_chung', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'chung.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'chung.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('CSY_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'chung.glb')))
