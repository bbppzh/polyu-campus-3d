#!/usr/bin/env python3
"""Build a custom Shaw Sports Complex with a barrel-vault roof and glazed entrance."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'shaw sports complex')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
RX = (max(xs) - min(xs)) / 2 + 1.2
RY = (max(ys) - min(ys)) / 2 + 1.2
HALL = h

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('SHAW_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('SHAW_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('SHAW_glass', (0.16, 0.28, 0.32), 0.12, 0.35)
DARK = mat('SHAW_dark', (0.08, 0.12, 0.14), 0.25, 0.4)
BLUE = mat('SHAW_blue', (0.17, 0.34, 0.42), 0.8)


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


extrude(loc, 0.0, 5.5, 'SHAW_plinth', BRICK)
extrude(loc, 5.5, HALL, 'SHAW_hall', WHITE)
extrude(loc, HALL - 0.4, HALL, 'SHAW_band', WHITE)


def rp(u, v, dz=0.0):
    x = midx + u * RX
    y = midy + v * RY
    z = HALL + 5.3 * ((1 - v * v) ** 0.85) * (0.82 + 0.18 * math.cos(u * math.pi / 2))
    return (x, y, z + dz)


U, V = 30, 20
top = []
bot = []
for i in range(U + 1):
    u = -1 + 2 * i / U
    for j in range(V + 1):
        v = -1 + 2 * j / V
        top.append(rp(u, v, 0.0))
        bot.append(rp(u, v, -0.5))
n = (U + 1) * (V + 1)
verts = top + bot
faces = []
for i in range(U):
    for j in range(V):
        a = i * (V + 1) + j; b = a + 1
        c = (i + 1) * (V + 1) + j + 1; d = (i + 1) * (V + 1) + j
        faces += [[a, b, d], [b, c, d]]
        a2, b2, c2, d2 = a + n, b + n, c + n, d + n
        faces += [[a2, d2, b2], [b2, d2, c2]]
for i in range(U):
    for j in (0, V):
        a = i * (V + 1) + j; b = (i + 1) * (V + 1) + j
        faces += [[a, b, a + n], [b, b + n, a + n]]
for j in range(V):
    for i in (0, U):
        a = i * (V + 1) + j; b = i * (V + 1) + j + 1
        faces += [[a, a + n, b], [b, a + n, b + n]]
mesh_obj('SHAW_vault', verts, faces, WHITE, smooth=True)

# glass strips along the vault
for off in (-0.28, 0.28):
    rv = []
    for i in range(U + 1):
        u = -1 + 2 * i / U
        for dv in (-0.055, 0.055):
            rv.append(rp(u, off + dv, 0.08))
    rf = []
    for i in range(U):
        a = i * 2; b = a + 1; c = (i + 1) * 2 + 1; d = (i + 1) * 2
        rf += [[a, b, d], [b, c, d]]
    mesh_obj(f'SHAW_vault_glass_{int(off*100)}', rv, rf, GLASS, smooth=True)

# hall roof equipment on the flat perimeter
box('SHAW_roof_plant', midx - 18, midy - 19, HALL + 1.2, 7.0, 5.0, 2.0, 0.0, WHITE)
for i in range(3):
    box(f'SHAW_roof_ac_{i}', midx + 15 + i * 4, midy - 20, HALL + 0.7, 2.2, 1.6, 1.0, 0.0, WHITE)

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
width = min(elen * 0.8, 20.0)

box('SHAW_atrium', bx + bnx * 1.4, by + bny * 1.4, 3.0, width, 2.6, 6.0, rot, GLASS)
box('SHAW_canopy', bx + bnx * 2.8, by + bny * 2.8, 6.4, width + 3.0, 4.4, 0.4, rot, WHITE)
for k in range(5):
    off = -width / 2 + width * (k + 0.5) / 5
    box(f'SHAW_mullion_{k}', bx + bnx * 2.75 + bvx * off, by + bny * 2.75 + bvy * off, 3.0, 0.16, 0.22, 6.0, rot, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_assemblies import fit_vault
fit_vault('SHAW_vault',['SHAW_vault_glass_-28','SHAW_vault_glass_28'],'SHAW_hall',loc,5.5,WHITE,remove=['SHAW_band'])
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_shaw', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'shaw.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'shaw.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('SHAW_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'shaw.glb')))
