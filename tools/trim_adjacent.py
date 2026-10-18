"""Cut accidental intrusions at a named building's mapped shared boundary."""
import bpy,json,os
from architecture import extrude

def trim_neighbour(landmark_name,owner_center,clearance=.12):
    root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d=json.load(open(os.path.join(root,'data/campus.json')))
    lm=next(l for l in d['landmarks'] if l['name']==landmark_name)
    fp=lm['footprint'];cx=sum(x for x,z in fp)/len(fp);cz=sum(z for x,z in fp)/len(fp)
    # A small outward offset resolves near-coplanar wall seams. The polygon
    # itself remains the source boundary; no building is moved or hidden.
    import math
    poly=[]
    for x,z in fp:
        length=math.hypot(x-cx,z-cz) or 1
        poly.append((x+(x-cx)*clearance/length-owner_center[0],-(z+(z-cz)*clearance/length-owner_center[1])))
    targets=[o for o in bpy.context.scene.objects if o.type=='MESH']
    material=targets[0].data.materials[0]
    cutter=extrude('temporary_shared_boundary',poly,-.5,float(lm['height'])+.5,material)
    for ob in targets:
        bpy.context.view_layer.objects.active=ob
        mod=ob.modifiers.new('Neighbour clearance','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
