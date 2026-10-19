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
lm = landmark('Seal of Love Foundation Building')
cx, cz = lm['center']
loc = clean([(x-cx, -(z-cz)) for x,z in lm['footprint']])
xs, ys = [p[0] for p in loc], [p[1] for p in loc]
midx, midy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
BRICK = material('SOL'+'_brick', (.56,.22,.17), .8)
WHITE = material('SOL'+'_white', (.90,.87,.81), .6)
GLASS = material('SOL'+'_glass', (.16,.29,.33), .12, .35)
GREEN = material('SOL'+'_green', (.28,.42,.24), 1)

x,y=min(xs)+3.2,midy
# Retain the existing stair-tower location, with a full ground support and a
# matching circular roof. Remove the unrelated small rooftop pavilion.
podium=extrude('SOL_podium',loc,0,5,BRICK)
boolean(podium,cylinder('stair_base',x,y,2.5,5.2,5,BRICK),'UNION')
band=extrude('SOL_band_0',loc,5,5.4,WHITE)
boolean(band,cylinder('stair_base_band',x,y,5.2,5.35,.4,WHITE),'UNION')
tower=extrude('SOL_tower',loc,5.4,19,BRICK)
glass=cylinder('SOL_glass_tower',x,y,12.2,5.2,13.6,GLASS,n=64)
boolean(tower,glass,remove=False)
roof=extrude('SOL_roof_slab',loc,19,19.6,WHITE)
boolean(roof,cylinder('stair_roof',x,y,19.3,5.35,.6,WHITE),'UNION')
perimeter_wall('SOL_parapet',loc,19.6,float(lm['height']),.45,WHITE)
# Exposed mullions only; buried rear half does not protrude through brick.
from architecture import inside
for k in range(16):
    a=k/16*2*math.pi;px=x+math.cos(a)*5.2;py=y+math.sin(a)*5.2
    if inside(loc,px,py):continue
    box(f'SOL_tower_frame_{k}',px,py,12.2,.14,.14,13.6,WHITE,angle=a)
entrance('SOL',loc,(midx+6,max(ys)),14,5.6,GLASS,WHITE)

export('seal')
