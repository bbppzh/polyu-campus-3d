"""Explicit, exportable facade geometry for the four photo-referenced repairs.
All lengths are visual estimates in metres, not survey dimensions. Materials
remain in the GLB; the campus must not overlay a generic window shader on them.
"""
import math,os,bpy
from mathutils import Vector
from architecture import (ROOT,clean,material,box,extrude,mesh,inside,export)
from facade_alignment import Face,halfplane

def fast_box(name,x,y,z,w,d,h,mat,angle=0):
    # Mesh data creation avoids thousands of context-sensitive cube operators.
    c,s=math.cos(angle),math.sin(angle)
    vv=[(x+c*u-s*v,y+s*u+c*v,z+t) for t in (-h/2,h/2) for u,v in [(-w/2,-d/2),(w/2,-d/2),(w/2,d/2),(-w/2,d/2)]]
    return mesh(name,vv,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat)

# Only builders importing this module use this equivalent fast implementation.
import facade_alignment
facade_alignment.box=fast_box

def palette(tag):
    return {k:material('REF_'+tag+'_'+k,c,rough,metal) for k,c,rough,metal in [
        ('brick',(.48,.23,.14),.88,0),('stone',(.69,.67,.60),.8,0),
        ('concrete',(.79,.78,.71),.75,0),('glass',(.16,.40,.48),.24,.18),
        ('blue',(.14,.49,.62),.21,.25),('metal',(.26,.29,.28),.45,.45),
        ('shadow',(.045,.07,.08),.85,0),('green',(.26,.37,.10),1,0)]}

def textured(mat,folder='brick'):
    # Clean campus brick, with a real-world 1.04 x .64 m tile. The old stock
    # texture depicts heavily weathered masonry and is unsuitable for these walls.
    if folder!='brick':return mat
    name='Campus_clean_terracotta'
    image=bpy.data.images.get(name)
    if image is None:
        image=bpy.data.images.new(name,width=256,height=256)
        values=[]
        for y in range(256):
            row=y//32
            for x in range(256):
                xx=(x+(32 if row%2 else 0))%256;col=xx//64
                grout=xx%64<1 or y%32<1
                n=(((row*37+col*71)%17)-8)*.0015
                color=(.48,.37,.29) if grout else (.66+n,.36+n*.7,.23+n*.5)
                values.extend((*color,1))
        image.pixels=values;image.pack()
    nodes=mat.node_tree.nodes;links=mat.node_tree.links;bsdf=nodes.get('Principled BSDF')
    tex=nodes.new('ShaderNodeTexImage');tex.image=image
    links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    return mat

def rect_in(poly,face,u0,u1,d0,d1):
    """Intersect a footprint with a wall-aligned rectangle; no AABB alignment."""
    p=poly
    for u,d,n,positive in [(u0,0,face.t,True),(u1,0,face.t,False),
                            (0,d0,face.n,True),(0,d1,face.n,False)]:
        p=halfplane(p,face.xy(u,d),n,positive)
    return p

def longest_front(poly,center):
    # Face the campus centre in actual map coordinates.
    direction=Vector((-center[0],center[1]));direction.normalize()
    fs=[Face(poly,i) for i in range(len(poly)) if math.dist(poly[i],poly[(i+1)%len(poly)])>18]
    return max(fs,key=lambda f:Vector(f.n).dot(direction)+min(f.length,60)*.003)

def wall_panel(name,f,u,z,w,h,mat,offset=.045,depth=.08):
    return f.box(name,u,offset,z,w,depth,h,mat)

def ribbon_facade(tag,poly,levels,glass,metal,stone,spacing=2.2):
    for i in range(len(poly)):
        f=Face(poly,i)
        if f.length<.8:continue
        for k,(z0,z1) in enumerate(levels):
            wall_panel(f'{tag}_window_{i}_{k}',f,0,(z0+z1)/2,f.length-.15,z1-z0,glass)
            f.box(f'{tag}_sill_{i}_{k}',0,.10,z0-.045,f.length,.20,.09,stone)
            cols=max(1,round(f.length/spacing))
            for j in range(1,cols):
                f.box(f'{tag}_mullion_{i}_{k}_{j}',f.length*(j/cols-.5),.10,(z0+z1)/2,.055,.08,z1-z0,metal)
            f.box(f'{tag}_transom_{i}_{k}',0,.10,(z0+z1)/2,f.length-.1,.08,.055,metal)

def roof_cap(name,poly,z,mat):return extrude(name,poly,z,z+.28,mat)

def columns(tag,poly,z0,z1,mat,spacing=5.4,inset=.5):
    for i in range(len(poly)):
        f=Face(poly,i)
        if f.length<4:continue
        count=max(1,int(f.length/spacing))
        for j in range(count):
            f.box(f'{tag}_column_{i}_{j}',f.length*((j+.5)/count-.5),-inset,(z0+z1)/2,.52,.65,z1-z0,mat)

def label(name,text,f,u,z,width,mat):
    cv=bpy.data.curves.new(name,'FONT');cv.body=text;cv.align_x='CENTER';cv.align_y='CENTER';cv.size=1;cv.extrude=.008
    ob=bpy.data.objects.new(name,cv);bpy.context.collection.objects.link(ob)
    ob.location=(*f.xy(u,.31),z)
    # Text local x follows the wall, local y is vertical, normal points outside.
    up=Vector((0,0,1));normal=Vector((*f.n,0));t=up.cross(normal)
    from mathutils import Matrix
    ob.rotation_euler=Matrix((t,up,normal)).transposed().to_euler();ob.data.materials.append(mat)
    bpy.context.view_layer.update();factor=width/max(max(v[0] for v in ob.bound_box)-min(v[0] for v in ob.bound_box),.01);ob.scale=(factor,factor,factor)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')

def uv_project():
    # Export ordinary UVs with the GLB: no browser-only procedural facade.
    bpy.context.view_layer.update()
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH':continue
        uv=ob.data.uv_layers.get('UVMap') or ob.data.uv_layers.new(name='UVMap')
        for p in ob.data.polygons:
            normal=ob.matrix_world.to_3x3()@p.normal
            axis=max(range(3),key=lambda k:abs(normal[k]));axes=([1,2],[0,2],[0,1])[axis]
            for li in p.loop_indices:
                v=ob.matrix_world@ob.data.vertices[ob.data.loops[li].vertex_index].co
                brick=ob.data.materials[p.material_index].name.endswith('_brick')
                uv.data[li].uv=(v[axes[0]]/(1.04 if brick else 3),v[axes[1]]/(.64 if brick else 3))

def finish(slug,front=None):
    # Bake real components but batch repeated facade surfaces by material.
    # Keep primary mass/roof/landscape names intact for independent QA.
    import re
    groups={}
    for ob in list(bpy.context.scene.objects):
        if ob.type=='MESH' and re.search(r'_(?:window_|mullion_|transom_|pier_|sill_|floor_lip_|crown_louvre_|slot_glass_|slot_window_|brick_pier_|service_louvre_|ground_glass_|column_|roof_edge_)',ob.name):
            groups.setdefault(ob.data.materials[0].name,[]).append(ob)
    for name,obs in groups.items():
        if len(obs)<2:continue
        bpy.ops.object.select_all(action='DESELECT')
        for ob in obs:ob.select_set(True)
        bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();bpy.context.object.name='DETAIL_baked_'+name
    uv_project();export(slug)
    if front is not None:
        import json,pathlib
        path=pathlib.Path(ROOT)/'data/review-views.json'
        views=json.loads(path.read_text()) if path.exists() else {}
        views[slug]={'front':list(front.n),'elevation':.72 if slug=='blockx' else .4}
        path.write_text(json.dumps(views,indent=2)+'\n')
