#!/usr/bin/env python3
"""Photo-referenced 14-storey Lee Shau Kee Building; heights are visual estimates."""
import pathlib,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from architecture import reset,landmark,clean,extrude
from facade_alignment import Face
from referenced_facades import *
reset();lm=landmark('Lee Shau Kee Building');cx,cz=lm['center']
p=clean([(x-cx,-(z-cz)) for x,z in lm['footprint']]);m=palette('LSKB');textured(m['brick'])
H=47.1;ground=4.2;step=3.3
# Entire curved/angled footprint retained; terracotta, blue ribbons, deep cornice.
extrude('LSKB_ground_glass',p,.25,ground,m['shadow'])
extrude('LSKB_main_mass',p,ground,H,m['brick'])
columns('LSKB_ground',p,.25,ground,m['concrete'],5.5,.3)
levels=[(1.0,3.5)]+[(ground+k*step+.25,ground+k*step+1.95) for k in range(13) if ground+k*step+1.95<H]
ribbon_facade('LSKB',p,levels,m['blue'],m['metal'],m['stone'],2.1)
# Thin continuous projecting terracotta floor edges accent the curved elevation.
for i in range(len(p)):
 f=Face(p,i)
 if f.length<1:continue
 for k in range(13):
  z=ground+k*step+2.65
  if z>H:continue
  f.box(f'LSKB_floor_lip_{i}_{k}',0,.11,z,f.length,.24,.18,m['brick'])
 f.box(f'LSKB_roof_cornice_{i}',0,.30,H+.15,f.length,.75,.3,m['brick'])
roof_cap('LSKB_roof_slab',p,H,m['stone'])
# Inset louvred crown seen above the blue window ribbons.
front=longest_front(p,lm['center'])
# A bounded roof-edge screen follows the real perimeter, not a rooftop box.
for i in range(len(p)):
 f=Face(p,i)
 for k in range(8):f.box(f'LSKB_crown_louvre_{i}_{k}',0,-.55,H+.4+k*.17,f.length,.12,.07,m['metal'])
label('LSKB_identity','LEE SHAU KEE BUILDING',front,0,32,min(front.length*.82,24),m['concrete'])
finish('leeshaukee',front)
