#!/usr/bin/env python3
"""Build a custom Pao Yue-kong Library shell and export GLB.

Run inside Blender:
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
        --python tools/build_library.py

Outputs assets/models/library.glb and assets/models/library.blend.
The app maps the LIB_* materials to its facade shader materials.
"""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    data = json.load(f)
lm = next(l for l in data['landmarks'] if 'library' in l['name'].lower())
fp = lm['footprint']
cx, cz = lm['center']
h = float(lm['height'])
loc = [(x - cx, -(z - cz)) for (x, z) in fp]

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, color, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


BRICK = mat('LIB_brick', (0.55, 0.20, 0.16), 0.78)
GLASS = mat('LIB_glass', (0.20, 0.32, 0.36), 0.12, 0.35)
WHITE = mat('LIB_white', (0.88, 0.85, 0.79), 0.62)
DARK = mat('LIB_dark', (0.10, 0.16, 0.18), 0.2, 0.4)


def mesh_object(name, verts, faces, material):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(material)
    return ob


def extrude_ring(poly, z0, z1, name, material, cap_top=True, cap_bottom=True):
    n = len(poly)
    verts = [(x, y, z0) for (x, y) in poly] + [(x, y, z1) for (x, y) in poly]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
    if cap_top:
        faces.append(list(range(n, 2 * n)))
    if cap_bottom:
        faces.append(list(reversed(range(n))))
    return mesh_object(name, verts, faces, material)


def box(name, x, y, z, sx, sy, sz, rot, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.scale = (sx, sy, sz)
    ob.rotation_euler.z = rot
    ob.data.materials.append(material)
    return ob


# brick mass
extrude_ring(loc, 0.0, 0.25, 'LIB_base', DARK)
extrude_ring(loc, 0.25, h, 'LIB_mass', BRICK)
# roof parapet band
extrude_ring(loc, h, h + 0.8, 'LIB_parapet', WHITE, cap_bottom=False)

# nearest edge to campus centre (local glTF coords)
tx, tz = 0.0, 0.0
def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xin = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1
            if x < xin:
                inside = not inside
    return inside

best = None
for i in range(len(fp) - 1):
    ax, az = fp[i][0] - cx, fp[i][1] - cz
    bx, bz = fp[i + 1][0] - cx, fp[i + 1][1] - cz
    dx, dz = bx - ax, bz - az
    leng = math.hypot(dx, dz)
    if leng < 12:
        continue
    mx, mz = (ax + bx) / 2, (az + bz) / 2
    nx1, nz1 = dz / leng, -dx / leng
    # pick the normal whose 2 m probe is outside the footprint
    if point_in_poly(mx + nx1 * 2.0, mz + nz1 * 2.0, [(x - cx, z - cz) for x, z in fp]):
        nx1, nz1 = -nx1, -nz1
    # the library's main entrance faces the campus core to the north:
    # use the north-most long edge (smallest local z)
    if best is None or mz < best[2] - 0.5:
        best = (math.hypot(mx, mz), mx, mz, dx / leng, dz / leng, leng, nx1, nz1, -mz)
if best is None:
    raise RuntimeError('no suitable library facade edge')
_, mx, mz, edx, edz, elen, nx, nz, _ = best
# map to Blender (x, -z)
bx, by = mx, -mz
bvx, bvy = edx, -edz
bnx, bny = nx, -nz
rot = math.atan2(bvy, bvx)
width = min(elen * 0.78, 34.0)

# glazed entrance volume
box('LIB_glass_front', bx + bnx * 1.35, by + bny * 1.35, 5.9,
    width, 2.7, 11.4, rot, GLASS)
# glass corner / side reveal
box('LIB_glass_side', bx + bnx * 1.2 + bvx * (width / 2 + 0.6),
    by + bny * 1.2 + bvy * (width / 2 + 0.6), 5.9, 1.6, 2.6, 11.4, rot, GLASS)
# white portal frames
box('LIB_frame_l', bx + bnx * 2.85 - bvx * (width / 2 + 0.35),
    by + bny * 2.85 - bvy * (width / 2 + 0.35), 5.9, 0.34, 0.5, 11.6, rot, WHITE)
box('LIB_frame_r', bx + bnx * 2.85 + bvx * (width / 2 + 0.35),
    by + bny * 2.85 + bvy * (width / 2 + 0.35), 5.9, 0.34, 0.5, 11.6, rot, WHITE)
# canopy
box('LIB_canopy', bx + bnx * 2.7, by + bny * 2.7, 12.3,
    width + 3.2, 4.6, 0.42, rot, WHITE)
# vertical mullions
count = max(5, int(width / 3.0))
for k in range(count):
    off = -width / 2 + width * (k + 0.5) / count
    box(f'LIB_mullion_{k:02d}',
        bx + bnx * 2.76 + bvx * off, by + bny * 2.76 + bvy * off, 5.9,
        0.16, 0.22, 11.2, rot, WHITE)
# horizontal transoms
for zz in (4.0, 8.0, 11.4):
    box(f'LIB_transom_{int(zz)}', bx + bnx * 2.78, by + bny * 2.78, zz,
        width, 0.22, 0.18, rot, WHITE)

# roof courtyard lantern
box('LIB_lantern', 0.0, 0.0, h + 1.6, 13.0, 10.0, 3.2, 0.0, GLASS)
box('LIB_lantern_frame', 0.0, 0.0, h + 3.25, 14.0, 11.0, 0.35, 0.0, WHITE)
# roof skylights, two strips either side of the lantern
for k, ox in ((-1, -22.0), (1, 22.0)):
    box(f'LIB_skylight_{k}', ox, 0.0, h + 0.45, 12.0, 22.0, 0.55, 0.0, GLASS)

# save + export
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from roof_support import finalize_scene
print('SUPPORT_QA', 'build_library', json.dumps(finalize_scene()), flush=True)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'assets', 'models', 'library.blend'))
bpy.ops.export_scene.gltf(
    filepath=os.path.join(ROOT, 'assets', 'models', 'library.glb'),
    export_format='GLB', use_selection=False, export_apply=True)
print('LIBRARY_OK', len(bpy.context.scene.objects), 'objects', os.path.getsize(os.path.join(ROOT, 'assets', 'models', 'library.glb')))
