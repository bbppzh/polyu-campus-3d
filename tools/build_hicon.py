#!/usr/bin/env python3
"""Hotel ICON: angular slabs, teaching block, recessed sky lobby and podium.
Massing based on Rocco Design's exterior photographs and exploded diagram.
114 m overall envelope follows the CVU/CTBUH building record; widths are OSM/
photo approximations. No invented rounded tower or antenna.
"""
import os,sys,math,json
sys.path.insert(0,os.path.dirname(__file__))
from architecture import *
# Refit controls from current campus footprints before every Hotel rebuild.
import runpy
runpy.run_path(os.path.join(ROOT,'tools','register_hotel_plan.py'),run_name='__main__')
reset();lm=landmark('Hotel ICON');f=Frame(lm);TOP=float(lm['height'])
with open(os.path.join(ROOT,'data/hotel-entrances.json')) as fh: entrance_registration=json.load(fh)
registered_entries=entrance_registration['entries']
glass=material('ICON_curtain_glass',(.22,.36,.40),.18,.28);dark=material('ICON_recess_glass',(.10,.22,.23),.22,.25);white=material('ICON_aluminium',(.77,.80,.77),.44,.3);stone=material('ICON_stone',(.72,.72,.66),.7)
# Mapped tower polygon is clipped into rectilinear wings, not scaled about a bbox.
p=f.poly
f.extrude('ICON_ground_atrium',p,0,5.5,glass)
f.extrude('ICON_teaching_block',p,5.5,43.8,glass)
# The upper tower has an L plan and a visible recessed sky level.
slab=clip(p,-30,30,3.0,30);core=clip(p,-30,-9,-30,30)
f.extrude('ICON_sky_level_recess',clip(p,-30,30,7,30),44,54,dark)
f.extrude('ICON_vertical_core',core,44,TOP-.25,glass)
f.extrude('ICON_main_hotel_slab',slab,54,TOP-.25,glass)
f.extrude('ICON_teaching_roof',p,43.8,44,white)
f.extrude('ICON_hotel_roof',slab,TOP-.25,TOP,white)
f.extrude('ICON_core_roof',core,TOP-.25,TOP,white)
# Vertical white blades and fine horizontal mullions are the distinctive facade.
for part,poly,z0,z1 in [('teaching',p,5.5,44),('hotel',slab,54,TOP),('core',core,44,TOP)]:
    q=f.polyxy(poly)
    for e,(a,b) in enumerate(zip(q,q[1:]+q[:1])):
        leng=math.dist(a,b)
        if leng<.5:continue
        ux=(b[0]-a[0])/leng;uy=(b[1]-a[1])/leng;nx,ny=uy,-ux;mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2
        if inside(q,mx+nx*.1,my+ny*.1):nx,ny=-nx,-ny
        angle=math.atan2(uy,ux);n=max(1,round(leng/2.8))
        for j in range(n+1):
            t=j/n;box(f'ICON_{part}_blade_{e}_{j}',a[0]+ux*leng*t+nx*.06,a[1]+uy*leng*t+ny*.06,(z0+z1)/2,.38 if j%3 else .78,.20,z1-z0,white,angle)
        floors=max(1,round((z1-z0)/3.7))
        for j in range(1,floors):
            z=z0+(z1-z0)*j/floors;box(f'ICON_{part}_transom_{e}_{j}',mx+nx*.07,my+ny*.07,z,leng,.13,.10,white,angle)
# Lower conference podium uses the adjacent mapped low-rise polygon.
with open(os.path.join(ROOT,'data','campus.json')) as h:d=json.load(h)
ctx=next(b for b in d['context'] if b['id']==236028379)
pod=[(x-lm['center'][0],-(z-lm['center'][1])) for x,z in ctx['footprint']]
extrude('ICON_conference_podium',pod,0,12.8,stone)
# A glazed entrance atrium is integrated into the podium envelope.
q=f.polyxy(clip(p,-30,30,-30,-8));extrude('ICON_lower_glazed_atrium',q,0,5.3,glass)
# Preserve University House as a separate staff-quarters wing, trimming only the
# mapped overlap with the taller teaching/hotel block. This replaces its generic
# context extrusion, rather than hiding the building to conceal intersections.
uh=next(b for b in d['context'] if b['id']==236028367)
uhp=clean([(x-lm['center'][0],-(z-lm['center'][1])) for x,z in uh['footprint']])
uhmat=material('ICON_UniversityHouse_stone',(.57,.57,.51),.8)
uho=extrude('ICON_UniversityHouse',uhp,0,float(uh['height']),uhmat)
cutter=extrude('UH_overlap_cutter',f.polyxy(p),-1,45,stone)
bpy.context.view_layer.objects.active=uho
mod=uho.modifiers.new('Remove mapped overlap with teaching block','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
# Windows follow only exposed parts of the original University House perimeter.
hp=f.polyxy(p)
for i,(a,b) in enumerate(zip(uhp,uhp[1:]+uhp[:1])):
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);nx,ny=dy/length,-dx/length
    if inside(uhp,(a[0]+b[0])/2+nx*.1,(a[1]+b[1])/2+ny*.1):nx,ny=-nx,-ny
    count=max(1,int(length/2.5))
    for j in range(count):
        t=(j+.5)/count;x=a[0]+dx*t;y=a[1]+dy*t
        if inside(hp,x+nx*.13,y+ny*.13) or inside(hp,x,y):continue
        for k in range(12):
            staff=next(e for e in registered_entries if e['id']=='staff')
            sx,sz=staff['wall_world_xz']
            if k<2 and math.hypot(x-(sx-lm['center'][0]),y+(sz-lm['center'][1]))<5:continue
            box(f'ICON_UH_window_{i}_{j}_{k}',x+nx*.045,y+ny*.045,1.6+k*3.2,length/count*.66,.08,1.8,glass,math.atan2(dy,dx))
# Entrances use the affine-registered G/F plan and explicit owning components.
# World x/z is converted to Blender x/y once; podium coordinates are not fed
# back through Frame.polyxy (which would rotate/translate them a second time).
def boolean_cut(obj,cutter):
    bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Registered ground floor portal','BOOLEAN')
    mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)

for entry in registered_entries:
    key=entry['id'];wx,wz=entry['wall_world_xz'];ux,uz=entry['tangent_world_xz'];nx,nz=entry['outward_world_xz']
    x,y=wx-lm['center'][0],-(wz-lm['center'][1]);uy=-uz;ny=-nz;ang=math.atan2(uy,ux)
    w=entry['door_width_m'];height=entry['door_height_m'];canw=entry['canopy_width_m'];cand=entry['canopy_depth_m']
    # Open a shallow doorway in the owner. Remove conflicting GF solids along
    # the outward approach, including the old mapped tower protrusion at school.
    # The approach height is a visual GF estimate, not a measured level.
    cutter=box('temporary_portal_'+key,x+nx*1.5,y+ny*1.5,2.15,canw+.8,7.0,4.5,white,ang)
    for name in ['ICON_ground_atrium','ICON_conference_podium','ICON_UniversityHouse','ICON_lower_glazed_atrium']:
        obj=bpy.data.objects.get(name)
        if obj: boolean_cut(obj,cutter)
    bpy.data.objects.remove(cutter,do_unlink=True)
    # All visible door/canopy corners are outside the registered owning wall.
    # Cantilever brackets join the rear canopy to the portal jambs.
    box(f'ICON_entrance_{key}_door',x+nx*.15,y+ny*.15,height/2+.02,w,.20,height,glass,ang)
    box(f'ICON_entrance_{key}_canopy',x+nx*(cand/2+.04),y+ny*(cand/2+.04),3.81,canw,cand,.18,white,ang)
    for sign in [-1,1]:
        box(f'ICON_entrance_{key}_jamb_{sign}',x+ux*sign*(w/2+.10)+nx*.16,y+uy*sign*(w/2+.10)+ny*.16,1.66,.16,.28,3.28,white,ang)
        box(f'ICON_entrance_{key}_bracket_{sign}',x+ux*sign*(w/2+.10)+nx*.65,y+uy*sign*(w/2+.10)+ny*.65,3.51,.14,1.30,.42,white,ang)
    box(f'ICON_entrance_{key}_header',x+nx*.16,y+ny*.16,3.27,w+.36,.28,.14,white,ang)
    box(f'ICON_entrance_{key}_divider',x+nx*.27,y+ny*.27,1.62,.06,.06,3.2,white,ang)

# The hotel frontage in the architect's exterior photograph is a glazed lobby
# next to the low conference block. Keep the entry bay visibly glazed; sizes
# below remain visual approximations rather than drawing dimensions.
e=next(e for e in registered_entries if e['id']=='hotel')
wx,wz=e['wall_world_xz'];ux,uz=e['tangent_world_xz'];nx,nz=e['outward_world_xz']
x,y=wx-lm['center'][0],-(wz-lm['center'][1]);uy=-uz;ny=-nz;ang=math.atan2(uy,ux);w=e['door_width_m'];bay=13.0
box('ICON_hotel_entry_glazing_upper',x+nx*.008,y+ny*.008,6.35,bay,.004,6.1,glass,ang)
side=(bay-w-.5)/2
for sign in [-1,1]:
    off=sign*(w/2+.25+side/2)
    box(f'ICON_hotel_entry_glazing_side_{sign}',x+ux*off+nx*.008,y+uy*off+ny*.008,1.66,side,.004,3.28,glass,ang)
for off in [-6.5,-4.5,4.5,6.5]:
    box(f'ICON_entry_bay_mull_{off}',x+ux*off+nx*.05,y+uy*off+ny*.05,4.7,.10,.08,9.4,white,ang)
export('hotel_icon')
