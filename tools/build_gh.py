#!/usr/bin/env python3
"""Hand-authored GH Block: brick slab with white bands, diamond glass corner, water tank."""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if l['name'].lower() == 'gh block')
fp = lm['footprint']; cx, cz = lm['center']; h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for x, z in fp]
xs = [x for x, y in loc]; ys = [y for x, y in loc]
midx, midy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
PODIUM = 5.0
TOWER_TOP = 21.0

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('GHB_brick', (0.56, 0.22, 0.17), 0.8)
WHITE = mat('GHB_white', (0.90, 0.87, 0.81), 0.6)
GLASS = mat('GHB_glass', (0.16, 0.29, 0.33), 0.12, 0.35)
GREEN = mat('GHB_green', (0.28, 0.42, 0.24), 1.0)
DARK = mat('GHB_dark', (0.08, 0.12, 0.14), 0.25, 0.4)


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


extrude(loc, 0.0, PODIUM, 'GHB_podium', BRICK)
extrude(loc, PODIUM, TOWER_TOP, 'GHB_tower', BRICK)
for k, y in enumerate((PODIUM, 11.0, 17.0, TOWER_TOP)):
    extrude(loc, y, y + 0.4, f'GHB_band_{k}', WHITE)
extrude(loc, TOWER_TOP, TOWER_TOP + 0.6, 'GHB_roof_slab', WHITE)

# diamond glass corner volume at one end
corner_x = min(xs) + 3.0
corner_y = min(ys) + 3.0
box('GHB_corner_glass', corner_x, corner_y, (PODIUM + TOWER_TOP) / 2, 5.0, 5.0, TOWER_TOP - PODIUM, math.radians(45), GLASS)
for k in range(3):
    off = -1.8 + k * 1.8
    box(f'GHB_corner_mull_{k}', corner_x + off * 0.707, corner_y + off * 0.707,
        (PODIUM + TOWER_TOP) / 2, 0.14, 0.14, TOWER_TOP - PODIUM, math.radians(45), WHITE)

# roof water tank + plant + green roof
bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=2.2, depth=3.2, location=(midx - 5, midy + 6, TOWER_TOP + 2.1))
tank = bpy.context.view_layer.objects.active
tank.name = 'GHB_water_tank'; tank.data.materials.append(WHITE)
box('GHB_roof_plant', midx + 3, midy - 7, TOWER_TOP + 1.4, 7.0, 4.0, 2.0, 0.0, WHITE)
for k, t in enumerate((-0.25, 0.05)):
    box(f'GHB_planter_{k}', midx + t * 16, midy + 1, TOWER_TOP + 0.9, 6.0, 1.4, 0.55, 0.0, GREEN)

# entrance
width = min(16.0, 0.45 * math.hypot(xs[-1] - xs[0], ys[-1] - ys[0]))
# place entrance on the south-facing bounding side
ent_x = midx
ent_y = max(ys) + 0.2
box('GHB_atrium', ent_x, ent_y, 2.8, 12.0, 2.0, 5.6, 0.0, GLASS)
box('GHB_canopy', ent_x, ent_y + 1.6, 6.0, 15.0, 3.6, 0.35, 0.0, WHITE)
for k in range(5):
    box(f'GHB_mull_{k}', ent_x - 5 + k * 2.5, ent_y + 1.4, 2.8, 0.14, 0.18, 5.6, 0.0, WHITE)
for k in range(2):
    box(f'GHB_step_{k}', ent_x, ent_y + 1.0 + k * 0.45, 0.1 + k * 0.16, 10.0, 2.0 + k * 0.7, 0.16, 0.0, WHITE)

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_gh', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'gh.blend'))
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT, 'assets', 'models', 'gh.glb'), export_format='GLB', use_selection=False, export_apply=True)
print('GHB_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'gh.glb')))
