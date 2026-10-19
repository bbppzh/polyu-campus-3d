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
lm = landmark('Stanley Ho Building')
cx, cz = lm['center']
loc = clean([(x-cx, -(z-cz)) for x,z in lm['footprint']])
xs, ys = [p[0] for p in loc], [p[1] for p in loc]
midx, midy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
BRICK = material('SHB'+'_brick', (.56,.22,.17), .8)
WHITE = material('SHB'+'_white', (.90,.87,.81), .6)
GLASS = material('SHB'+'_glass', (.16,.29,.33), .12, .35)
GREEN = material('SHB'+'_green', (.28,.42,.24), 1)

extrude('SHB_podium',loc,0,5,BRICK)
extrude('SHB_band',loc,5,5.4,WHITE)
extrude('SHB_tower',loc,5.4,18,BRICK)
extrude('SHB_roof_slab',loc,18,18.6,WHITE)
# Preserve the balcony side, but use the actual complete edge sequence.
faces=[Face(loc,i) for i in range(len(loc)) if math.dist(loc[i],loc[(i+1)%len(loc)])>=15]
face=max(faces,key=lambda f:-sum(f.n[k]*f.mid[k] for k in range(2))*f.length)
for k,z in enumerate((8.5,12.5,16.5)):
    w=face.length*.76
    face.box(f'SHB_balcony_{k}',0,.86,z,w,1.8,.24,WHITE)
    # Balustrade bottoms touch slab tops, including both return ends.
    face.box(f'SHB_rail_{k}',0,1.70,z+.57,w,.12,.9,GLASS)
    for j,u in enumerate((-w/2+.06,w/2-.06)):
        face.box(f'SHB_return_{k}_{j}',u,.86,z+.57,.12,1.8,.9,GLASS)
# The green-wall backing and every frame now share the host end-wall plane.
endfaces=[Face(loc,i) for i in range(len(loc))
          if 4 < math.dist(loc[i],loc[(i+1)%len(loc)]) < 12]
greenface=min(endfaces,key=lambda f:math.dist(f.mid,(max(xs)-1,midy)))
greenwidth=min(6,greenface.length-.6)
greenface.box('SHB_green_wall',0,.09,10.5,greenwidth,.22,11,GREEN)
for k in range(5):
    greenface.box(f'SHB_green_frame_{k}',greenwidth*((k+.5)/5-.5),.24,10.5,.12,.1,11,WHITE)
for k in range(4):
    greenface.box(f'SHB_green_cross_{k}',0,.24,6+k*3,greenwidth,.1,.12,WHITE)
entrance('SHB',loc,(midx,max(ys)),14,5.6,GLASS,WHITE)

export('stanley')
