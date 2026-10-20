#!/usr/bin/env python3
"""Photo-referenced library: vertical brick fins, recessed entrance, end tower."""
import pathlib,sys,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from architecture import reset,landmark,clean,extrude,box
from facade_alignment import Face,boolean
from referenced_facades import *
reset();lm=landmark('Pao Yue-kong Library');cx,cz=lm['center']
p=clean([(x-cx,-(z-cz)) for x,z in lm['footprint']]);m=palette('LIB');textured(m['brick'])
front=max([Face(p,i) for i in range(len(p)) if math.dist(p[i],p[(i+1)%len(p)])>25],key=lambda f:f.mid[1])
# Main reading-room volume and a genuine end identity tower, not roof lanterns.
extrude('LIB_ground_plinth',p,0,.3,m['stone'])
reading=extrude('LIB_reading_rooms',p,4.5,23.0,m['brick'])
roof=roof_cap('LIB_main_roof',p,23.0,m['concrete'])
corepoly=rect_in(p,front,front.length*.27,front.length*.47,-12,0)
boolean(reading,extrude('reading_core_cut',corepoly,.2,28.1,m['brick']))
extrude('LIB_identity_tower',corepoly,.3,28.0,m['brick'])
boolean(roof,extrude('roof_core_cut',corepoly,22.9,28.1,m['brick']))
# Glazed crown visible in the official front photograph.
extrude('LIB_tower_glazed_crown',corepoly,28,29.4,m['shadow'])
ribbon_facade('LIB_crown',corepoly,[(28.05,29.3)],m['glass'],m['metal'],m['metal'],1.1)
roof_cap('LIB_tower_cap',corepoly,29.4,m['metal'])
# Main entry is recessed under the fin wall. No glass box hanging outside.
for i in range(len(p)):
 f=Face(p,i)
 if f.length<1:continue
 f.box(f'LIB_ground_glass_{i}',0,-.35,2.4,f.length-.15,.12,4.2,m['glass'])
 for j in range(max(1,int(f.length/2.2))):
  f.box(f'LIB_entry_mullion_{i}_{j}',f.length*((j+.5)/max(1,int(f.length/2.2))-.5),-.24,2.4,.08,.1,4.2,m['metal'])
columns('LIB_entry',p,.3,4.5,m['concrete'],5.6,.15)
# Seven slender vertical window slots between deep brick fins on the front.
for i in range(len(p)):
 f=Face(p,i)
 if f.length<6:continue
 count=max(2,round(f.length/5.7))
 for j in range(1,count):
  u=f.length*(j/count-.5)
  if i==front.index and front.length*.27-.4<u<front.length*.47+.4:continue
  wall_panel(f'LIB_slot_window_{i}_{j}',f,u,13.75,.72,18.5,m['shadow'],.055,.10)
  for k in range(5):
   wall_panel(f'LIB_slot_glass_{i}_{j}_{k}',f,u,6.2+k*3.5,.57,2.8,m['glass'],.11,.04)
  f.box(f'LIB_brick_pier_{i}_{j}',u+.65,.32,13.75,.40,.70,18.5,m['brick'])
# Stone fascia, shallow entrance landing and a wide run of steps.
front.box('LIB_entrance_fascia',0,.16,4.37,front.length,.52,.28,m['concrete'])
for k in range(6):
 front.box(f'LIB_entrance_step_{k}',0,1.8+k*.48,.3*(1-k/6),front.length*.67,3.6+k*.96,.1,m['stone'])
label('LIB_identity','PAO YUE-KONG LIBRARY',front,front.length*.37,26,front.length*.18,m['concrete'])
finish('library',front)
