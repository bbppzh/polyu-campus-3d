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
lm = landmark('Chung Sze Yuen Building')
cx, cz = lm['center']
loc = clean([(x-cx, -(z-cz)) for x,z in lm['footprint']])
xs, ys = [p[0] for p in loc], [p[1] for p in loc]
midx, midy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
BRICK = material('CSY'+'_brick', (.56,.22,.17), .8)
WHITE = material('CSY'+'_white', (.90,.87,.81), .6)
GLASS = material('CSY'+'_glass', (.16,.29,.33), .12, .35)
GREEN = material('CSY'+'_green', (.28,.42,.24), 1)

# Replace coincident shells with contiguous, non-overlapping storeys.
extrude('CSY_podium',loc,0,4,BRICK)
extrude('CSY_band',loc,4,4.4,WHITE)
levels=[(4.4,5.4,WHITE),(5.4,6.6,GLASS),(6.6,6.8,WHITE),
        (6.8,8.2,WHITE),(8.2,9.4,GLASS),(9.4,9.6,WHITE),
        (9.6,11,WHITE),(11,12.2,GLASS),(12.2,13,WHITE)]
for k,(z0,z1,mat) in enumerate(levels):
    extrude(f'CSY_storey_{k}',loc,z0,z1,mat)
extrude('CSY_roof_slab',loc,13,13.8,WHITE)
perimeter_wall('CSY_parapet',loc,13.8,float(lm['height']),.45,WHITE)
entrance('CSY',loc,(midx,max(ys)),14,5.4,GLASS,WHITE)

export('chung')
