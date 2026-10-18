#!/usr/bin/env python3
"""Block Z: two rectilinear academic wings, low teaching podium and sky link.
University gallery C0088/C0132 establishes the massing/vertical pier language;
12-storey wings and a low block are described by the project's contractor.
48 m is a visual height estimate. Platform levels are not survey measurements.
"""
import os,sys,math
sys.path.insert(0,os.path.dirname(__file__))
from architecture import *
reset();lm=landmark('Block Z');f=Frame(lm);TOP=float(lm['height'])
brick=material('Z_terracotta',(.55,.31,.23),.84);glass=material('Z_blue_glass',(.21,.40,.48),.25,.22);stone=material('Z_pale_piers',(.67,.67,.59),.8);metal=material('Z_aluminium',(.62,.69,.69),.4,.3);green=material('Z_planting',(.27,.40,.20),1)
# Split the actual T-shaped mapped outline into two wings and the low courtyard block.
low=clip(f.poly,-100,100,-50,2.0);left=clip(f.poly,-100,-8,2,50);right=clip(f.poly,8,100,2,50);middle=clip(f.poly,-8,8,2,50)
f.extrude('Z_low_teaching_block',low,0,14.4,stone)
f.extrude('Z_courtyard_podium',middle,0,10.8,stone)
for name,p in [('south',left),('north',right)]:
    f.extrude('Z_'+name+'_wing',p,0,TOP-.22,brick)
    window_grid('Z_'+name,f.polyxy(p),0,TOP,glass,metal,spacing=4.0,floor=TOP/12,vertical_piers=stone,punched=True)
    f.extrude('Z_'+name+'_roof',p,TOP-.22,TOP,stone)
    edges('Z_'+name+'_roof_guard',f.polyxy(p),TOP+.50,1.0,.16,metal)
# A supported enclosed link connects the two wings above the open courtyard.
f.extrude('Z_sky_link',middle,23.2,27.2,glass)
f.extrude('Z_link_floor',middle,23.0,23.2,stone)
f.extrude('Z_link_roof',middle,27.2,27.45,stone)
window_grid('Z_low',f.polyxy(low),0,14.4,glass,metal,spacing=3.8,floor=3.6,punched=True)
# Real perimeter walls, leaving a usable platform instead of filling it solid.
edges('Z_platform_guard',f.polyxy(low),14.9,1.0,.2,metal)
# Garden beds are wholly contained by the low platform and sit directly on it.
for i,(u,v,w,d) in enumerate([(-9,-11,12,3),(10,-20,12,3),(-8,-29,10,3),(16,-8,8,3)]):
    points=[(u+su*w/2,v+sv*d/2) for su in (-1,0,1) for sv in (-1,0,1)]
    if not all(inside(low,x,y) for x,y in points):continue
    f.box(f'Z_planter_base_{i}',u,v,14.65,w,d,.50,stone)
    f.box(f'Z_planter_lawn_{i}',u,v,14.95,w-.3,d-.3,.10,green)
# Low glass canopy, columns touch the terrace. No arbitrary roof pavilion.
can=clip(low,-10,10,-8,-2)
if len(can)>2:
    f.extrude('Z_terrace_glass_canopy',can,17.5,17.65,glass)
    for i,(u,v) in enumerate(can):
        if inside(low,u*.995,v*.995):f.box(f'Z_terrace_canopy_column_{i}',u,v,15.95,.18,.18,3.1,metal)
export('blockz')
