#!/usr/bin/env python3
"""Photo-referenced Li Ka Shing Tower: interlocking blocks and elevated drum.
Sources: Wong Tung project photographs and project description (see docs).
Dimensions below are visual massing estimates, not surveyed measurements.
Run with Blender --background --python tools/build_lks.py.
"""
import os,sys,math
sys.path.insert(0,os.path.dirname(__file__))
from architecture import *
reset();lm=landmark('Li Ka Shing Tower');f=Frame(lm);TOP=float(lm['height'])
brick=material('LKS_terracotta',(.53,.25,.20),.83);glass=material('LKS_glazing',(.20,.34,.40),.22,.22);stone=material('LKS_stone',(.72,.72,.68));trim=material('LKS_metal',(.66,.70,.70),.35,.35)
# The annex follows the mapped footprint; the tower is composed of straight blocks.
f.extrude('LKS_annex',f.poly,0,4.2,brick)
body=[(-17,-18),(17,-18),(17,18),(-17,18)]
f.extrude('LKS_tower_body',body,4.2,44.0,glass)
wing=[(-17,-18),(0,-18),(0,18),(-17,18)]
f.extrude('LKS_rectangular_upper_wing',wing,44,53.2,glass)
for k in range(15):
    y=4.2+k*(49/15)
    p=body if y<44 else wing
    if y<53.2:
        f.extrude(f'LKS_spandrel_{k}',p,y,min(y+1.05,53.2),brick)
        edges(f'LKS_sill_{k}',f.polyxy(p),min(y+1.12,53.2),.12,.20,trim)
# Thin vertical mullions preserve the glazing rhythm rather than round the whole tower.
for p,z0,z1 in [(body,4.2,44),(wing,44,53.2)]:
    q=f.polyxy(p)
    for e,(a,b) in enumerate(zip(q,q[1:]+q[:1])):
        n=max(1,int(math.dist(a,b)/2.7))
        for j in range(1,n):
            t=j/n;box(f'LKS_glazing_mull_{z0}_{e}_{j}',a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,(z0+z1)/2,.10,.10,z1-z0,trim)
# Four executive floors in a true cylindrical drum, carried by visible columns.
ux,vy=7.8,0.0;rad=10.5;drum_base=47.2
for i in range(6):
    a=i*math.tau/6;f.cyl(f'LKS_drum_column_{i}',ux+7.1*math.cos(a),vy+7.1*math.sin(a),45.6,.52,3.2,stone,20)
f.cyl('LKS_executive_drum',ux,vy,(drum_base+TOP-.16)/2,rad,TOP-.16-drum_base,glass)
for i in range(5):
    z=drum_base+i*(TOP-drum_base)/4
    center=TOP-.34 if i==4 else z+.18
    f.cyl(f'LKS_drum_spandrel_{i}',ux,vy,center,rad+.12,.36 if i==4 else .95,brick)
for i in range(32):
    a=i*math.tau/32;f.cyl(f'LKS_drum_mullion_{i}',ux+rad*math.cos(a),vy+rad*math.sin(a),(drum_base+TOP-.16)/2,.065,TOP-.16-drum_base,trim,8)
f.cyl('LKS_drum_roof',ux,vy,TOP-.08,rad+.16,.16,trim)
f.extrude('LKS_upper_wing_roof',wing,53.2,53.45,trim)
export('lks')
