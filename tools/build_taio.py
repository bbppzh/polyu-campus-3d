#!/usr/bin/env python3
"""Hand-authored Chan Tai Ho Building: stone tower with deep glazed atrium + portico."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'chan tai ho building')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
PODIUM = 5.0
TOWER_TOP = 19.0

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


STONE = mat('CTH_stone', (0.64, 0.55, 0.46), 0.85)
WHITE = mat('CTH_white', (0.92, 0.89, 0.83), 0.6)
GLASS = mat('CTH_glass', (0.16, 0.29, 0.33), 0.12, 0.35)
GREEN = mat('CTH_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('CTH_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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

extrude(loc, 0.0, PODIUM, 'CTH_podium', STONE)
extrude(loc, PODIUM, PODIUM + 0.45, 'CTH_band', WHITE)
extrude(loc, PODIUM, TOWER_TOP, 'CTH_tower', STONE)
extrude(loc, TOWER_TOP, TOWER_TOP + 0.55, 'CTH_roof_slab', WHITE)
pent = scale_poly(0.62)
extrude(pent, TOWER_TOP, h, 'CTH_penthouse', WHITE)
extrude(pent, h, h + 0.45, 'CTH_roof', WHITE)

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

# deep glazed atrium: dark reveal, glass, white frame
aw = min(elen * 0.55, 18.0)
box('CTH_reveal', bx + bnx * 0.25, by + bny * 0.25, 12.0, aw + 1.2, 0.5, 12.4, rot, DARK)
box('CTH_glass', bx + bnx * 0.65, by + bny * 0.65, 12.0, aw, 0.3, 12.0, rot, GLASS)
box('CTH_frame_top', bx + bnx * 0.9, by + bny * 0.9, 18.2, aw + 1.4, 0.8, 0.5, rot, WHITE)
box('CTH_frame_bot', bx + bnx * 0.9, by + bny * 0.9, 5.8, aw + 1.4, 0.8, 0.5, rot, WHITE)
for k in range(2):
    off = (-0.5 if k == 0 else 0.5) * (aw + 0.9)
    box(f'CTH_frame_side_{k}', bx + bnx * 0.9 + bvx * off, by + bny * 0.9 + bvy * off,
        12.0, 0.6, 0.8, 12.4, rot, WHITE)
for k in range(5):
    off = -aw / 2 + aw * (k + 0.5) / 5
    box(f'CTH_mull_{k}', bx + bnx * 0.95 + bvx * off, by + bny * 0.95 + bvy * off,
        12.0, 0.12, 0.16, 12.0, rot, LIGHT := WHITE)

# projecting portico at ground
for k in range(4):
    t = 0.25 + 0.5 * k / 3
    px = bx + bvx * (t - 0.5) * elen + bnx * 2.4
    py = by + bvy * (t - 0.5) * elen + bny * 2.4
    box(f'CTH_col_{k}', px, py, 3.0, 0.55, 0.55, 6.0, rot, STONE)
box('CTH_portico', bx + bnx * 2.4, by + bny * 2.4, 6.3, 16.0, 4.6, 0.4, rot, WHITE)

# roof terrace / plant
for k, t in enumerate((-0.25, 0.05, 0.3)):
    box(f'CTH_planter_{k}', midx + t * 16, midy + 8, TOWER_TOP + 0.9, 6.0, 1.5, 0.6, 0.0, GREEN)
box('CTH_roof_plant', midx - 5, midy - 8, h + 1.2, 6.0, 4.0, 1.8, 0.0, WHITE)

# entrance under portico
box('CTH_door', bx + bnx * 1.6, by + bny * 1.6, 2.6, 7.0, 1.6, 5.2, rot, GLASS)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_taio', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'taio.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'taio.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('CTH_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'taio.glb')))
