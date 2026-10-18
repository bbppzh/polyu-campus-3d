#!/usr/bin/env python3
"""Generate GLBs for the remaining ordinary named buildings from one template.

Run inside Blender:
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
        --python tools/build_auto_batch.py

Writes assets/models/auto/<slug>.glb and data/custom-models.json.
"""
import bpy
import bmesh
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(ROOT, 'data', 'campus.json'), encoding='utf-8') as f:
    DATA = json.load(f)

TARGETS = [
    'Fong Shu Chuen Hall', 'Anita Chan Lai Ling Building', 'House of Innovation',
]
OUTDIR = os.path.join(ROOT, 'assets', 'models', 'auto')
os.makedirs(OUTDIR, exist_ok=True)


def slug(name):
    return name.lower().replace(' ', '_').replace('-', '_')


def mat(name, color, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1.0)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    m.diffuse_color = (*color, 1.0)
    return m


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


def build(lm):
    name = lm['name']; h = float(lm['height']); fp = lm['footprint']; cx, cz = lm['center']
    loc = [(x - cx, -(z - cz)) for x, z in fp]
    xs = [x for x, y in loc]; ys = [y for x, y in loc]
    minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
    midx, midy = (minx + maxx) / 2, (miny + maxy) / 2
    area = abs(sum(fp[i][0] * fp[i + 1][1] - fp[i + 1][0] * fp[i][1] for i in range(len(fp) - 1)) / 2)
    seed = sum(ord(c) for c in name)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    BRICK = mat('GEN_brick', (0.55 + (seed % 9) * 0.005, 0.21, 0.16), 0.8)
    WHITE = mat('GEN_white', (0.90, 0.87, 0.81), 0.6)
    UPPER = mat('GEN_upper', (0.88, 0.85, 0.79), 0.6)
    GLASS = mat('GEN_glass', (0.16, 0.28, 0.32), 0.12, 0.35)
    GREEN = mat('GEN_green', (0.28, 0.42, 0.24), 1.0)
    DARK = mat('GEN_dark', (0.08, 0.12, 0.14), 0.25, 0.4)

    if h < 9:
        extrude(loc, 0.0, h, f'{name}_mass', UPPER)
        base_h = h
    else:
        base_h = h * (0.48 + (seed % 5) * 0.02)
        scale = 0.88 + (seed % 4) * 0.02
        upper = [(midx + (x - midx) * scale, midy + (y - midy) * scale) for x, y in loc]
        extrude(loc, 0.0, base_h, f'{name}_base', BRICK)
        extrude(upper, base_h, h, f'{name}_upper', UPPER)
        # horizontal band at the setback
        band = [(midx + (x - midx) * 1.012, midy + (y - midy) * 1.012) for x, y in loc]
        extrude(band, base_h - 0.35, base_h, f'{name}_band', WHITE)
    # parapet / roof edge
    extrude(loc, h, h + 0.55, f'{name}_parapet', WHITE)

    # roof plant and equipment
    box(f'{name}_roof_plant', midx - 3, midy + 3, h + 1.2, 8.0, 6.0, 1.8, 0.0, WHITE)
    for i in range(2):
        box(f'{name}_ac_{i}', midx + 5 + i * 3.5, midy - 2, h + 0.8, 2.0, 1.5, 1.0, 0.0, WHITE)
    for i in range(2):
        box(f'{name}_vent_{i}', midx - 6 + i * 2.5, midy - 5, h + 1.0, 0.6, 0.6, 1.8, 0.0, DARK)

    # roof garden for wide low buildings
    if area > 600 and h < 25:
        box(f'{name}_garden', midx + 6, midy + 6, h + 0.85, min(16, area ** 0.5 * 0.4), 5.0, 0.5, 0.0, GREEN)
        box(f'{name}_pavilion', midx + 6, midy + 6, h + 2.2, 6.0, 4.0, 2.4, 0.0, WHITE)

    # entrance on nearest edge, with an outward probe
    poly = [(x - cx, z - cz) for x, z in fp]
    best = None
    for i in range(len(fp) - 1):
        ax, az = fp[i][0] - cx, fp[i][1] - cz
        bx, bz = fp[i + 1][0] - cx, fp[i + 1][1] - cz
        dx, dz = bx - ax, bz - az; leng = math.hypot(dx, dz)
        if leng < 5: continue
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
        score = facing * (leng ** 0.3)
        if best is None or score > best[6]: best = (math.hypot(mx, mz), mx, mz, dx / leng, dz / leng, leng, score, nx, nz)
    if best:
        _, mx, mz, edx, edz, elen, _, nx, nz = best
        bx, by = mx, -mz; bvx, bvy = edx, -edz; bnx, bny = nx, -nz
        rot = math.atan2(bvy, bvx)
        width = min(max(elen * 0.5, 6.0), 16.0)
        box(f'{name}_canopy', bx + bnx * 2.2, by + bny * 2.2, 3.4, width, 3.2, 0.3, rot, WHITE)
        box(f'{name}_door', bx + bnx * 0.9, by + bny * 0.9, 1.5, width * 0.55, 0.5, 3.0, rot, GLASS)
        for k in range(3):
            off = -width / 2 + width * (k + 0.5) / 3
            box(f'{name}_mullion_{k}', bx + bnx * 2.1 + bvx * off, by + bny * 2.1 + bvy * off, 1.5, 0.12, 0.15, 3.0, rot, WHITE)

    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from roof_support import finalize_scene
    finalize_scene()
    bpy.context.view_layer.update()
    path = os.path.join(OUTDIR, slug(name) + '.glb')
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTDIR, slug(name) + '.blend'))
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=False, export_apply=True)
    return name, path


registry = []
for t in TARGETS:
    lm = next(l for l in DATA['landmarks'] if l['name'] == t)
    n, p = build(lm)
    registry.append({'name': n, 'file': 'assets/models/auto/' + os.path.basename(p)})
    print('AUTO_OK', n, os.path.getsize(p))
with open(os.path.join(ROOT, 'data', 'custom-models.json'), 'w', encoding='utf-8') as f:
    json.dump(registry, f, ensure_ascii=False, indent=1)
print('REGISTRY', len(registry))
