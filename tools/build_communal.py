#!/usr/bin/env python3
"""Photo-referenced Communal Building: brick ribbons, recessed ground colonnade."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from architecture import reset,landmark,clean,extrude
from referenced_facades import *
reset();lm=landmark('Communal Building');cx,cz=lm['center']
p=clean([(x-cx,-(z-cz)) for x,z in lm['footprint']]);m=palette('COM');textured(m['brick'])
extrude('COM_base',p,0,.25,m['stone'])
# Dark inset ground floor is visually open between load-bearing concrete columns.
for i in range(len(p)):
 f=Face(p,i)
 if f.length<1:continue
 f.box(f'COM_ground_glass_{i}',0,-1.1,2.2,f.length-.2,.12,3.9,m['glass'])
columns('COM_portico',p,.25,4.2,m['concrete'],5.5,.3)
extrude('COM_upper_mass',p,4.2,19.2,m['brick'])
extrude('COM_soffit',p,4,4.2,m['concrete'])
ribbon_facade('COM',p,[(5.0,6.5),(8.3,9.8),(11.6,13.1),(14.9,16.4),(18,18.9)],m['glass'],m['metal'],m['stone'],1.7)
roof_cap('COM_roof_slab',p,19.2,m['stone'])
for i in range(len(p)):
 f=Face(p,i)
 if f.length<1:continue
 f.box(f'COM_roof_edge_{i}',0,-.15,19.65,f.length,.3,.4,m['brick'])
f=longest_front(p,lm['center'])
label('COM_identity','COMMUNAL BUILDING',f,0,7.3,min(22,f.length*.75),m['concrete'])
finish('communal',f)
