#!/usr/bin/env python3
"""Build a custom Jockey Club Auditorium shell and export GLB.

Run inside Blender:
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
        --python tools/build_jca.py

Outputs assets/models/jca.glb and assets/models/jca.blend.
"""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if 'auditorium' in l['name'].lower())
fp = lm['footprint']
cx, cz = lm['center']
h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for (x, z) in fp]
xs = [x for x, y in loc]
ys = [y for x, y in loc]
minx, maxx = min(xs), max(xs)
miny, maxy = min(ys), max(ys)
midx, midy = (minx + maxx) / 2, (miny + maxy) / 2
rx = (maxx - minx) / 2 + 1.6
ry = (maxy - miny) / 2 + 1.6
HALL_H = 11.2
ROOF_BASE = 11.6
ROOF_APEX = 18.4

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    m.use_nodes = True
    m.diffuse_color = (*color, 1.0)
    return m


WHITE = mat('JCA_white', (0.91, 0.88, 0.82), 0.58)
GLASS = mat('JCA_glass', (0.18, 0.30, 0.34), 0.12, 0.35)
BRICK = mat('JCA_brick', (0.55, 0.21, 0.16), 0.78)
DARK = mat('JCA_dark', (0.10, 0.15, 0.17), 0.2, 0.4)


def mesh_obj(name, verts, faces, material, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(material)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def extrude_ring(poly, z0, z1, name, material, cap=True):
    n = len(poly)
    verts = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
    if cap:
        faces.append(list(range(n, 2 * n)))
        faces.append(list(reversed(range(n))))
    return mesh_obj(name, verts, faces, material)


def box(name, x, y, z, sx, sy, sz, rot, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.scale = (sx, sy, sz)
    ob.rotation_euler.z = rot
    ob.data.materials.append(material)
    return ob


# hall: brick plinth + white upper volume
extrude_ring(loc, 0.0, 2.4, 'JCA_plinth', BRICK)
extrude_ring([(x, y) for x, y in loc], 2.4, HALL_H, 'JCA_hall', WHITE)


def roof_point(u, v, dz=0.0):
    x = midx + u * rx
    y = midy + v * ry
    # asymmetric vault: high towards the +u end, curling down at the edges
    shape = (0.50 + 0.50 * math.sin(math.pi * (u + 1) / 2))
    z = ROOF_BASE + (ROOF_APEX - ROOF_BASE) * ((1 - v * v) ** 0.85) * shape
    z -= 1.8 * (abs(u) ** 8)
    return (x, y, z + dz)


# roof shell: top surface + underside, with a fascia edge
U, V = 28, 18
top = []
bot = []
for i in range(U + 1):
    u = -1 + 2 * i / U
    for j in range(V + 1):
        v = -1 + 2 * j / V
        top.append(roof_point(u, v, 0.0))
        bot.append(roof_point(u, v, -0.65))
n = (U + 1) * (V + 1)
verts = top + bot
faces = []
for i in range(U):
    for j in range(V):
        a = i * (V + 1) + j
        b = a + 1
        c = (i + 1) * (V + 1) + j + 1
        d = (i + 1) * (V + 1) + j
        faces += [[a, b, d], [b, c, d]]
        a2, b2, c2, d2 = a + n, b + n, c + n, d + n
        faces += [[a2, d2, b2], [b2, d2, c2]]
# side fascia around the perimeter
for i in range(U):
    for j in (0, V):
        a = i * (V + 1) + j; b = (i + 1) * (V + 1) + j
        a2, b2 = a + n, b + n
        faces += [[a, b, a2], [b, b2, a2]]
for j in range(V):
    for i in (0, U):
        a = i * (V + 1) + j; b = i * (V + 1) + j + 1
        a2, b2 = a + n, b + n
        faces += [[a, a2, b], [b, a2, b2]]
mesh_obj('JCA_roof', verts, faces, WHITE, smooth=True)

# glazed roof strip along the ridge
ridge = []
for i in range(U + 1):
    u = -1 + 2 * i / U
    for v in (-0.13, 0.13):
        ridge.append(roof_point(u, v, 0.08))
ridge_f = []
for i in range(U):
    a = i * 2; b = a + 1; c = (i + 1) * 2 + 1; d = (i + 1) * 2
    ridge_f += [[a, b, d], [b, c, d]]
mesh_obj('JCA_roof_glass', ridge, ridge_f, GLASS, smooth=True)

# nearest edge to the campus core
best = None
for i in range(len(fp) - 1):
    ax, az = fp[i][0] - cx, fp[i][1] - cz
    bx, bz = fp[i + 1][0] - cx, fp[i + 1][1] - cz
    dx, dz = bx - ax, bz - az
    leng = math.hypot(dx, dz)
    if leng < 1e-6:
        continue
    t = max(0.0, min(1.0, (-ax * dx - az * dz) / (leng * leng)))
    mx, mz = ax + dx * t, az + dz * t
    d = math.hypot(mx, mz)
    if best is None or d < best[0]:
        best = (d, mx, mz, dx / leng, dz / leng, leng)
_, mx, mz, edx, edz, elen = best
nx, nz = -mx, -mz
nl = math.hypot(nx, nz) or 1.0
nx, nz = nx / nl, nz / nl

def _inside(px, pz):
    ins = False
    poly = [(x - cx, z - cz) for x, z in fp]
    for i in range(len(poly)):
        x1, z1 = poly[i]; x2, z2 = poly[(i + 1) % len(poly)]
        if (z1 > pz) != (z2 > pz):
            xin = (x2 - x1) * (pz - z1) / (z2 - z1 + 1e-12) + x1
            if px < xin: ins = not ins
    return ins
if _inside(mx + nx * 2.0, mz + nz * 2.0):
    nx, nz = -nx, -nz
bx, by = mx, -mz
bvx, bvy = edx, -edz
bnx, bny = nx, -nz
rot = math.atan2(bvy, bvx)
width = min(elen * 0.78, 18.0)

# glass foyer + canopy + mullions
box('JCA_foyer', bx + bnx * 1.5, by + bny * 1.5, 3.2, width, 2.6, 6.2, rot, GLASS)
box('JCA_canopy', bx + bnx * 2.8, by + bny * 2.8, 6.7, width + 3.0, 4.4, 0.4, rot, WHITE)
box('JCA_frame_l', bx + bnx * 2.86 - bvx * (width / 2 + 0.2), by + bny * 2.86 - bvy * (width / 2 + 0.2), 3.2, 0.32, 0.45, 6.2, rot, WHITE)
box('JCA_frame_r', bx + bnx * 2.86 + bvx * (width / 2 + 0.2), by + bny * 2.86 + bvy * (width / 2 + 0.2), 3.2, 0.32, 0.45, 6.2, rot, WHITE)
for k in range(5):
    off = -width / 2 + width * (k + 1) / 6
    box(f'JCA_mullion_{k}', bx + bnx * 2.8 + bvx * off, by + bny * 2.8 + bvy * off, 3.2, 0.15, 0.2, 6.0, rot, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_jca', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'jca.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'jca.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('JCA_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'jca.glb')))
