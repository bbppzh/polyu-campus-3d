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
lm = landmark('House of Innovation')
cx, cz = lm['center']
loc = clean([(x-cx, -(z-cz)) for x,z in lm['footprint']])
xs, ys = [p[0] for p in loc], [p[1] for p in loc]
midx, midy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
BRICK = material('HOI'+'_brick', (.56,.22,.17), .8)
WHITE = material('HOI'+'_white', (.90,.87,.81), .6)
GLASS = material('HOI'+'_glass', (.16,.29,.33), .12, .35)
GREEN = material('HOI'+'_green', (.28,.42,.24), 1)

extrude('HOI_podium',loc,0,4,BRICK)
extrude('HOI_band',loc,4,4.4,WHITE)
glasspoly=[(midx+(x-midx)*.94,midy+(y-midy)*.94) for x,y in loc]
extrude('HOI_roof_slab',loc,16,16.55,WHITE)
# Partition in the footprint plane, so glass and core share exact vertices.
# The notch opens onto the selected wall, avoiding a coplanar boolean sliver.
f=nearest_face(glasspoly,(min(xs)+3.2,midy),8.4)
notch=[f.xy(-4,0),f.xy(-4,-4),f.xy(4,-4),f.xy(4,0)]
from architecture import inside
assert all(inside(glasspoly,*p) for p in notch[1:3])
corepoly=[notch[0],notch[3],notch[2],notch[1]]
lantern=glasspoly[:f.index+1]+notch+glasspoly[f.index+1:]
extrude('HOI_glass',lantern,4.4,16,GLASS)
extrude('HOI_core',corepoly,4.4,16,BRICK)
for i in range(len(glasspoly)):
    face=Face(glasspoly,i)
    count=max(1,int(face.length/2.6))
    # On the core side, split all horizontal and vertical frames at the brick.
    spans=[(-face.length/2,face.length/2)]
    if i==f.index:spans=[(-face.length/2,-4),(4,face.length/2)]
    for j in range(count):
        u=face.length*((j+.5)/count-.5)
        if i==f.index and abs(u)<4:continue
        face.box(f'HOI_glazing_frame_{i}_{j}',u,.035,10.2,.12,.12,11.6,WHITE)
    for k,z in enumerate((7,10,13)):
        for j,(u0,u1) in enumerate(spans):
            if u1-u0>.01:face.box(f'HOI_transom_{k}_{i}_{j}',(u0+u1)/2,.035,z,u1-u0,.12,.14,WHITE)
entrance('HOI',loc,(midx,max(ys)),9,5.4,GLASS,WHITE,count=4)

export('hoi')
