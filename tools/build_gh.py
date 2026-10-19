#!/usr/bin/env python3
"""Repair component alignment using the existing mapped footprint and massing.
Facade positions are approximate; this is not a measured building survey.
"""
import math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from architecture import (reset, landmark, clean, material, extrude, box,
                          cylinder, export, clip)
from facade_alignment import (Face, nearest_face, entrance, boolean,
                              corner_partition, perimeter_wall)
reset()
lm = landmark('GH Block')
cx, cz = lm['center']
loc = clean([(x-cx, -(z-cz)) for x,z in lm['footprint']])
xs, ys = [p[0] for p in loc], [p[1] for p in loc]
midx, midy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
BRICK = material('GHB'+'_brick', (.56,.22,.17), .8)
WHITE = material('GHB'+'_white', (.90,.87,.81), .6)
GLASS = material('GHB'+'_glass', (.16,.29,.33), .12, .35)
GREEN = material('GHB'+'_green', (.28,.42,.24), 1)

# Fit the glass corner to two actual adjoining footprint edges.
# The brick and glass share a cut plane; no rotated cube hangs beyond the roof.
main,corner=corner_partition(loc,(min(xs)+3,min(ys)+3),4)
extrude('GHB_podium',loc,0,5,BRICK)
for k,(z0,z1) in enumerate(((5.4,11),(11.4,17),(17.4,21))):
    extrude(f'GHB_tower_{k}',main,z0,z1,BRICK)
    extrude(f'GHB_corner_glass_{k}',corner,z0,z1,GLASS)
for k,z in enumerate((5,11,17)):
    extrude(f'GHB_band_{k}',loc,z,z+.4,WHITE)
extrude('GHB_roof_slab',loc,21,21.6,WHITE)
# Frames follow exposed corner edges only; the internal cut is left unframed.
for i in range(len(loc)):
    f=Face(loc,i)
    for k,p in enumerate(corner):
        u=sum((p[j]-f.mid[j])*f.t[j] for j in range(2))
        n=sum((p[j]-f.mid[j])*f.n[j] for j in range(2))
        if abs(n)<.001 and abs(u)<f.length/2-.1:
            f.box(f'GHB_corner_frame_{i}_{k}',u,.025,13.2,.12,.10,15.6,WHITE)
entrance('GHB',loc,(midx,max(ys)),12,5.6,GLASS,WHITE,steps=True)

export('gh')
