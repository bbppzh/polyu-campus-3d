#!/usr/bin/env python3
"""Build a custom Communal Building with a glazed atrium and roof terrace."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'communal building')
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


BRICK = mat('COM_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('COM_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('COM_glass', (0.16, 0.28, 0.32), 0.12, 0.35)
GREEN = mat('COM_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('COM_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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


upper = [(midx + (x - midx) * 0.86, midy + (y - midy) * 0.84) for x, y in loc]
extrude(loc, 0.0, LOWER, 'COM_lower', BRICK)
extrude(upper, LOWER, h, 'COM_upper', WHITE)
extrude(loc, LOWER - 0.5, LOWER, 'COM_terrace_edge', WHITE)
extrude(upper, h, h + 0.7, 'COM_roof_edge', WHITE)

# roof atrium skylight
box('COM_skylight', midx - 3, midy + 2, h + 1.2, 14.0, 10.0, 1.0, 0.0, GLASS)
box('COM_skylight_rim', midx - 3, midy + 2, h + 1.75, 15.0, 11.0, 0.25, 0.0, WHITE)
box('COM_roof_plant', midx + 12, midy - 8, h + 1.5, 8.0, 6.0, 2.0, 0.0, WHITE)

# terrace planters on the setback
for i, t in enumerate((-0.3, 0.0, 0.3)):
    bx = midx + t * (max(xs) - min(xs))
    box(f'COM_terrace_planter_{i}', bx, min(ys) + 2.4, LOWER + 0.5, 8.0, 1.5, 0.8, 0.0, GREEN)

# nearest edge, outward probe
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
width = min(elen * 0.86, 24.0)

# glazed atrium: tall glass wall + mullions + canopy
box('COM_atrium', bx + bnx * 1.5, by + bny * 1.5, 5.0, width, 2.8, 10.0, rot, GLASS)
box('COM_canopy', bx + bnx * 3.0, by + bny * 3.0, 10.4, width + 3.0, 4.6, 0.4, rot, WHITE)
for k in range(6):
    off = -width / 2 + width * (k + 0.5) / 6
    box(f'COM_mullion_{k}', bx + bnx * 2.95 + bvx * off, by + bny * 2.95 + bvy * off, 5.0, 0.16, 0.22, 10.0, rot, WHITE)
for k in range(3):
    box(f'COM_transom_{k}', bx + bnx * 2.96, by + bny * 2.96, 2.5 + k * 3.3, width, 0.2, 0.16, rot, WHITE)
# steps
for k in range(2):
    box(f'COM_step_{k}', bx + bnx * (1.8 + k * 0.5), by + bny * (1.8 + k * 0.5), 0.1 + k * 0.18, width * 0.7, 2.2 + k * 0.8, 0.18, rot, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_communal', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'communal.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'communal.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('COM_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'communal.glb')))
