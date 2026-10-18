#!/usr/bin/env python3
"""Build a custom Block X sports complex with a rooftop court and terrace."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'block x')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
LOWER = 26.0

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('BLKX_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('BLKX_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('BLKX_glass', (0.16, 0.28, 0.32), 0.12, 0.35)
BLUE = mat('BLKX_blue', (0.16, 0.34, 0.42), 0.8)
GREEN = mat('BLKX_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('BLKX_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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


def cyl(name, x, y, z, r, depth, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=r, depth=depth, location=(x, y, z))
    ob = bpy.context.view_layer.objects.active; ob.name = name
    ob.data.materials.append(material)
    return ob


upper = [(midx + (x - midx) * 0.82, midy + (y - midy) * 0.78) for x, y in loc]
extrude(loc, 0.0, LOWER, 'BLKX_lower', BRICK)
extrude(upper, LOWER, h, 'BLKX_upper', WHITE)
extrude(loc, LOWER - 0.5, LOWER, 'BLKX_terrace_edge', WHITE)
extrude(upper, h, h + 0.8, 'BLKX_roof_edge', WHITE)

# rooftop sports court on the lower terrace, fitted to the footprint
court_x, court_y = midx, midy
DECK = h + 1.0
court_w = min(24.0, (max(xs) - min(xs)) * 0.45)
court_d = min(12.0, (max(ys) - min(ys)) * 0.40)
box('BLKX_court', court_x, court_y, DECK, court_w, court_d, 0.35, 0.0, BLUE)
# white court lines
for i, (lx, ly, lw, ld) in enumerate((
    (court_x, court_y - court_d / 2 + 0.5, court_w, 0.18), (court_x, court_y + court_d / 2 - 0.5, court_w, 0.18),
    (court_x - court_w / 2 + 0.5, court_y, 0.18, court_d), (court_x + court_w / 2 - 0.5, court_y, 0.18, court_d),
    (court_x, court_y, 0.18, court_d),
)):
    box(f'BLKX_line_{i}', lx, ly, DECK + 0.23, lw, ld, 0.08, 0.0, WHITE)
# fence posts around court
for side in (-1, 1):
    for i in range(6):
        bx = court_x + side * (court_w / 2)
        by = court_y - court_d / 2 + (i + 0.5) * court_d / 6
        box(f'BLKX_fence_{side}_{i}', bx, by, DECK + 1.4, 0.14, 0.14, 2.8, 0.0, DARK)
    for i in range(9):
        by = court_y + side * (court_d / 2)
        bx = court_x - court_w / 2 + (i + 0.5) * court_w / 9
        box(f'BLKX_fence2_{side}_{i}', bx, by, DECK + 1.4, 0.14, 0.14, 2.8, 0.0, DARK)
# floodlights
for i, (fx, fy) in enumerate(((court_x - court_w/2 + .5, court_y - court_d/2 + .5), (court_x + court_w/2 - .5, court_y - court_d/2 + .5), (court_x - court_w/2 + .5, court_y + court_d/2 - .5), (court_x + court_w/2 - .5, court_y + court_d/2 - .5))):
    cyl(f'BLKX_pole_{i}', fx, fy, DECK + 4.175, 0.22, 8.0, DARK)
    box(f'BLKX_lamp_{i}', fx, fy, DECK + 8.35, 1.6, 0.5, 0.35, 0.0, WHITE)

# upper roof plant
box('BLKX_roof_plant', midx - 22, midy + 15, h + 1.6, 10.0, 7.0, 2.2, 0.0, WHITE)
for i in range(3):
    box(f'BLKX_roof_ac_{i}', midx + 10 + i * 4, midy - 5, h + 0.7, 2.2, 1.6, 1.0, 0.0, WHITE)

# entrance
best = None
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
bx, by = mx, -mz; bvx, bvy = edx, -edz; bnx, bny = nx, -nz
rot = math.atan2(bvy, bvx)
box('BLKX_canopy', bx + bnx * 3.0, by + bny * 3.0, 4.4, 20.0, 5.0, 0.45, rot, WHITE)
box('BLKX_door', bx + bnx * 1.4, by + bny * 1.4, 2.2, 14.0, 1.0, 4.4, rot, GLASS)
for k in range(4):
    off = -6.5 + 13.0 * (k + 0.5) / 4
    box(f'BLKX_mullion_{k}', bx + bnx * 2.4 + bvx * off, by + bny * 2.4 + bvy * off, 2.2, 0.18, 0.22, 4.4, rot, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_blockx', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'blockx.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'blockx.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('BLOCKX_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'blockx.glb')))
