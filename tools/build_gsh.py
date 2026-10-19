#!/usr/bin/env python3
"""Build a custom Global Student Hub (glass pavilion + roof terrace)."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'global student hub')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
BASE = 4.5

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('GSH_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('GSH_white', (0.91, 0.88, 0.82), 0.6)
GLASS = mat('GSH_glass', (0.16, 0.29, 0.33), 0.1, 0.35)
GREEN = mat('GSH_green', (0.27, 0.43, 0.24), 1.0)
DARK = mat('GSH_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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


upper = [(midx + (x - midx) * 1.03, midy + (y - midy) * 1.03) for x, y in loc]
extrude(loc, 0.0, BASE, 'GSH_base', BRICK)
extrude(upper, BASE, h, 'GSH_glass', GLASS)
extrude(loc, BASE, BASE + 0.45, 'GSH_mid_band', WHITE)
extrude(upper, h, h + 0.5, 'GSH_roof_slab', WHITE)

# vertical mullions around the upper glass volume
n = len(upper)
for i in range(n):
    a = upper[i]; b = upper[(i + 1) % n]
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = math.hypot(dx, dy)
    if length < 1:
        continue
    steps = max(1, int(length / 3.4))
    for k in range(steps):
        t = (k + 0.5) / steps
        x = a[0] + dx * t; y = a[1] + dy * t
        box(f'GSH_mullion_{i}_{k}', x, y, (BASE + h) / 2, 0.14, 0.14, h - BASE, 0.0, WHITE)

# roof terrace
bw = max(xs) - min(xs); bd = max(ys) - min(ys)
for i, (tx, ty) in enumerate(((-0.18, -0.15), (0.18, 0.15), (0.0, 0.22))):
    box(f'GSH_planter_{i}', midx + tx * bw, midy + ty * bd, h + 0.9, bw * 0.18, bd * 0.14, 0.7, 0.0, GREEN)
# A complete supported pergola; dimensions are visual approximations.
import sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
# entrance on nearest edge
best = None
poly = [(x - cx, z - cz) for x, z in fp]
for i in range(len(fp) - 1):
    ax, az = fp[i][0] - cx, fp[i][1] - cz
    bx, bz = fp[i + 1][0] - cx, fp[i + 1][1] - cz
    dx, dz = bx - ax, bz - az; leng = math.hypot(dx, dz)
    if leng < 1e-6: continue
    t = max(0.0, min(1.0, (-ax * dx - az * dz) / (leng * leng)))
    mx, mz = ax + dx * t, az + dz * t; d = math.hypot(mx, mz)
    if best is None or d < best[0]: best = (d, mx, mz, dx / leng, dz / leng, leng)
_, mx, mz, edx, edz, elen = best
nx, nz = -mx, -mz; nl = math.hypot(nx, nz) or 1.0; nx /= nl; nz /= nl


def inside(px, pz):
    ins = False
    for i in range(len(poly)):
        x1, z1 = poly[i]; x2, z2 = poly[(i + 1) % len(poly)]
        if (z1 > pz) != (z2 > pz):
            xin = (x2 - x1) * (pz - z1) / (z2 - z1 + 1e-12) + x1
            if px < xin: ins = not ins
    return ins
if inside(mx + nx * 2.0, mz + nz * 2.0): nx, nz = -nx, -nz
bx, by = mx, -mz; bvx, bvy = edx, -edz; bnx, bny = nx, -nz
rot = math.atan2(bvy, bvx)
box('GSH_canopy', bx + bnx * 2.6, by + bny * 2.6, 4.2, 12.0, 4.2, 0.4, rot, WHITE)
box('GSH_door', bx + bnx * 1.2, by + bny * 1.2, 2.1, 9.0, 0.9, 4.2, rot, GLASS)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trim_adjacent import trim_neighbour
trim_neighbour('Chow Yei Ching Building', (cx,cz), .35)
trim_neighbour('Yip Kit Chuen Building', (cx,cz), .35)
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_gsh', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'gsh.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'gsh.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('GSH_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'gsh.glb')))
