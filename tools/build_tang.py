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
lm = landmark('Tang Ping Yuan Building')
cx, cz = lm['center']
loc = clean([(x-cx, -(z-cz)) for x,z in lm['footprint']])
xs, ys = [p[0] for p in loc], [p[1] for p in loc]
midx, midy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
BRICK = material('TPY'+'_brick', (.56,.22,.17), .8)
WHITE = material('TPY'+'_white', (.90,.87,.81), .6)
GLASS = material('TPY'+'_glass', (.16,.29,.33), .12, .35)
GREEN = material('TPY'+'_green', (.28,.42,.24), 1)

def scaled(s):return [(midx+(x-midx)*s,midy+(y-midy)*s) for x,y in loc]
extrude('TPY_podium',loc,0,5,BRICK)
extrude('TPY_band_0',loc,5,5.4,WHITE)
glass=scaled(.92)
extrude('TPY_glass',glass,5.4,12.5,GLASS)
extrude('TPY_band_1',glass,12.5,13,WHITE)
upper=scaled(.78)
extrude('TPY_upper',upper,13,20,WHITE)
extrude('TPY_roof_slab',upper,20,20.6,WHITE)
for i in range(len(glass)):
    f=Face(glass,i)
    if f.length<1:continue
    count=max(1,int(f.length/2.4))
    for j in range(count):
        f.box(f'TPY_glazing_frame_{i}_{j}',f.length*((j+.5)/count-.5),.035,8.95,.12,.12,7.1,WHITE)
    for k,z in enumerate((8,10.5)):
        f.box(f'TPY_transom_{k}_{i}',0,.035,z,f.length,.12,.12,WHITE)
# Old windows used x=-13.5..13.5, y=-7, cutting diagonally through the tower.
f=nearest_face(upper,(0,-7),8)
span=min(12,f.length-2)
for k in range(5):
    u=span*(k/4-.5)
    f.box(f'TPY_slit_{k}',u,.035,16.2,.8,.10,5.6,GLASS)
    f.box(f'TPY_sill_{k}',u,.12,13.3,1.1,.30,.2,WHITE)
entrance('TPY',loc,(midx,max(ys)),12,5.4,GLASS,WHITE,count=4)

export('tang')
