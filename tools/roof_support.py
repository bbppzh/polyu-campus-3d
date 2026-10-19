"""Place rooftop detail groups on actual mesh surfaces before every export.
Uses BVH triangle intersections rather than bounding boxes as support evidence.
Independent of the building's world-axis orientation and concave footprint.
"""
import bpy,math,re,json,os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
DETAIL=re.compile(r'planter|_bed_|_lawn_|_garden|tree|trunk|_court$|_line_|_fence|_pole_|_lamp_|_roof_plant|_roof_ac|_ac_\d|_vent_\d|_pergola|_pav')

# These objects were invented decoration/equipment rather than sourced campus
# features. Remove them at export, consistently for every named model.
UNVERIFIED_ROOF_PROPS=re.compile(r'pergola|planter|_bed_|_lawn_|_garden|tree|trunk|_roof_plant|_roof_ac|_ac_\d|_vent_\d|_water_tank|_tank(?:_|$)|_pav(?:_|$)|_roof_canopy|^Z_terrace_(?:glass_canopy|canopy_column)|^GSH_(?:rail|guard)_',re.I)

def remove_unverified_roof_props():
    removed=[]
    for ob in list(bpy.context.scene.objects):
        if ob.type=='MESH' and UNVERIFIED_ROOF_PROPS.search(ob.name):
            removed.append(ob.name);bpy.data.objects.remove(ob,do_unlink=True)
    return removed

def bounds(obs):
    vv=[o.matrix_world@Vector(p) for o in obs for p in o.bound_box]
    return Vector(tuple(min(v[k] for v in vv) for k in range(3))),Vector(tuple(max(v[k] for v in vv) for k in range(3)))

def finalize_scene():
    removed=remove_unverified_roof_props()
    if removed:print('UNVERIFIED_ROOF_PROPS_REMOVED',json.dumps(removed),flush=True)
    bpy.context.view_layer.update();objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    details=[o for o in objects if DETAIL.search(o.name.lower())]
    bodies=[o for o in objects if o not in details and not re.search(r'mull|transom|_fin_|_pier_|_step_|_door|_canopy|_atrium|_port|_frame|_slit|_sill|_ribbon',o.name.lower())]
    verts=[];faces=[];candidates=[]
    for ob in bodies:
        ob.data.calc_loop_triangles();off=len(verts);vv=[ob.matrix_world@v.co for v in ob.data.vertices];verts+=vv
        for tri in ob.data.loop_triangles:
            faces.append(tuple(off+i for i in tri.vertices));a,b,c=[vv[i] for i in tri.vertices]
            if max(a.z,b.z,c.z)-min(a.z,b.z,c.z)<.02 and a.z>.5:
                candidates.append(((a.x+b.x+c.x)/3,(a.y+b.y+c.y)/3,a.z))
    if not faces:return []
    bvh=BVHTree.FromPolygons(verts,faces,all_triangles=True);maxz=max(p.z for p in verts)+10;cache={}
    def surface(x,y):
        key=(round(x,4),round(y,4))
        if key not in cache:
            hit,norm,_,_=bvh.ray_cast(Vector((x,y,maxz)),Vector((0,0,-1)))
            cache[key]=float(hit.z) if hit is not None and norm is not None and abs(norm.z)>.98 else None
        return cache[key]
    groups={}
    for o in details:
        n=o.name.lower()
        if any(t in n for t in ('_court','_line_','_fence','_pole_','_lamp_')):key='sports_court'
        elif '_pergola' in n:key='pergola'
        elif '_pav' in n:key='pavilion'
        elif 'tree' in n or 'trunk' in n:key='tree_'+n.split('_')[-1]
        elif '_lawn_' in n or '_bed_' in n:key='bed_'+n.split('_')[-1]
        else:key=o.name
        groups.setdefault(key,[]).append(o)
    occupied=[];actions=[]
    # Large assemblies first, so small props do not displace a whole court.
    jobs=sorted(groups.items(),key=lambda it:-(bounds(it[1])[1]-bounds(it[1])[0]).x*(bounds(it[1])[1]-bounds(it[1])[0]).y)
    lo,hi=bounds(bodies)
    for key,obs in jobs:
        footprint_obs=[o for o in obs if 'trunk' in o.name.lower()] if key.startswith('tree_') else obs
        if not footprint_obs:footprint_obs=obs
        mn,mx=bounds(footprint_obs);allmn,allmx=bounds(obs);cx,cy=(mn.x+mx.x)/2,(mn.y+mx.y)/2;bottom=mn.z
        # Court markings are above the deck; poles belong to the assembly.
        if key=='sports_court':
            deck=next((o for o in obs if o.name.lower().endswith('_court')),None)
            if deck:mn,mx=bounds([deck]);cx,cy=(mn.x+mx.x)/2,(mn.y+mx.y)/2;bottom=mn.z
        ww,dd=mx.x-mn.x,mx.y-mn.y
        offsets=[(ww*(i/4-.5),dd*(j/4-.5)) for i in range(5) for j in range(5)]
        # Include the corners and edges with a small inward tolerance only.
        offsets=[(x*.995,y*.995) for x,y in offsets]
        spots=[(cx,cy)]+[(x,y) for x,y,z in candidates if abs(z-bottom)<2.0]
        # Search interior positions as well as face centroids on long skinny roofs.
        step=2.0
        for ix in range(math.ceil((hi.x-lo.x)/step)):
            for iy in range(math.ceil((hi.y-lo.y)/step)):
                x=lo.x+(ix+.5)*step;y=lo.y+(iy+.5)*step;z=surface(x,y)
                if z is not None and abs(z-bottom)<2:spots.append((x,y))
        spots=sorted(set(spots),key=lambda p:(p[0]-cx)**2+(p[1]-cy)**2)
        placed=None
        for x,y in spots:
            z=surface(x,y)
            if z is None or abs(z-bottom)>2:continue
            if any(x+ww/2>a and x-ww/2<c and y+dd/2>b and y-dd/2<d for a,b,c,d in occupied):continue
            heights=[surface(x+dx,y+dy) for dx,dy in offsets]
            if any(h is None or abs(h-z)>.035 for h in heights):continue
            placed=(x,y,z);break
        if placed:
            x,y,z=placed;delta=Vector((x-cx,y-cy,z-bottom+.002))
            for o in obs:o.location+=delta
            occupied.append((x-ww/2-.15,y-dd/2-.15,x+ww/2+.15,y+dd/2+.15))
            if delta.length>.025:actions.append({'group':key,'action':'placed_on_surface','delta':[round(v,3) for v in delta]})
        else:
            actions.append({'group':key,'action':'omitted_no_fitting_surface','objects':[o.name for o in obs]})
            for o in obs:bpy.data.objects.remove(o,do_unlink=True)
    bpy.context.view_layer.update()
    return actions
