#!/usr/bin/env python3
"""Block X redevelopment: low-rise glazed base, roof landscape and circulation.
The planted roof is supported by PolyU's 2018 GreenNet article and tour; no
outdoor rooftop sports court/floodlight assembly is inferred from indoor uses.
"""
import pathlib,sys,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from architecture import reset,landmark,Frame,clip,extrude
from referenced_facades import *
from facade_alignment import boolean
reset();lm=landmark('Block X');F=Frame(lm);m=palette('BLKX');textured(m['concrete'],'stone')
p=F.polyxy(F.poly)
extrude('BLKX_base',p,0,.3,m['concrete'])
extrude('BLKX_glazed_base',p,.3,4.1,m['glass'])
extrude('BLKX_main_deck',p,4.1,4.4,m['concrete'])
ribbon_facade('BLKX_ground',p,[(.4,3.95)],m['glass'],m['metal'],m['metal'],2.2)
# Narrow low service/office wing on the campus side; the broad roof stays open.
bar=clip(F.poly,-43,12,-17.1,-9.6);bar=F.polyxy(bar)
extrude('BLKX_service_wing',bar,4.4,7.8,m['shadow'])
ribbon_facade('BLKX_service',bar,[(4.65,7.45)],m['glass'],m['metal'],m['concrete'],1.8)
roof_cap('BLKX_wing_cap',bar,7.8,m['concrete'])
# Supported angular planting beds follow the photographed roof paths. They are
# integral landscape surfaces, not scattered lawn boxes or floating planters.
greenpolys=[[( -39,-6),(-8,-6),(8,5),(-24,9),(-39,6)],
            [(-15,13),(13,7),(26,1),(30,12)],[(14,-7),(30,-6),(36,-1),(23,3)]]
for i,q in enumerate(greenpolys):
 q=clip(q,-44,39,-8,14)
 surface=F.extrude(f'BLKX_verified_vegetated_surface_{i}',q,4.4,4.55,m['green'])
 boolean(surface,extrude('landscape_clip',p,4.3,4.7,m['green']),'INTERSECT')
# A supported ramp connects the open deck to the upper service-wing roof.
from mathutils import Vector
from architecture import mesh,box
A=Vector((-35,12));B=Vector((8,-11));t=(B-A).normalized();n=Vector((-t.y,t.x))*1.65
q=[A-n,B-n,B+n,A+n];bottom=4.4;tops=[4.57,8.08,8.08,4.57]
vv=[(*F.xy(*v),bottom) for v in q]+[(*F.xy(*v),z) for v,z in zip(q,tops)]
ramp=mesh('BLKX_accessible_ramp',vv,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],m['concrete'])
boolean(ramp,extrude('ramp_clip',p,4.3,9,m['concrete']),'INTERSECT')
# Rails are complete supported assemblies: every post is seated on the ramp.
for side in (-1,1):
 a=A+side*n*.95+t*.08;b=B+side*n*.95-t*.08
 dz=(8.08-4.57)*.08/(B-A).length;za=4.57+dz;zb=8.08-dz
 pa=Vector((*F.xy(*a),za+.95));pb=Vector((*F.xy(*b),zb+.95))
 mid=(pa+pb)/2
 ob=box(f'BLKX_ramp_guard_top_{side}',*mid,.07,.07,(pb-pa).length,m['metal'])
 ob.rotation_euler=(pb-pa).to_track_quat('Z','Y').to_euler()
 for j in range(9):
  f=j/8;pos=a.lerp(b,f);z=za+(zb-za)*f
  F.box(f'BLKX_ramp_guard_post_{side}_{j}',pos.x,pos.y,z+.475,.055,.055,.95,m['metal'])
# Stepped seating/circulation near JCIT; each solid starts at the main deck.
for k in range(5):
 q=clip(F.poly,12+k*5,17+k*5,-5,9)
 if len(q)>2:F.extrude(f'BLKX_amphitheatre_deck_{k}',q,4.4,4.6+k*.42,m['concrete'])
# Horizontal louvres belong to the service wall, not isolated roof posts.
for i in range(len(bar)):
 f=Face(bar,i)
 if f.length<4:continue
 for k in range(13):f.box(f'BLKX_service_louvre_{i}_{k}',0,.10,4.7+k*.22,f.length,.18,.09,m['metal'])
f=longest_front(p,lm['center']);label('BLKX_identity','BLOCK X   ASRC',f,0,3.6,min(16,f.length*.8),m['concrete'])
finish('blockx',f)
