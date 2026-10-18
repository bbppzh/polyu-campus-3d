"""Shared, deterministic geometry for photo-referenced campus massing (Blender)."""
import bpy, bmesh, math, json, os
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version=0

def landmark(name):
    with open(os.path.join(ROOT,'data','campus.json')) as f:d=json.load(f)
    return next(l for l in d['landmarks'] if l['name']==name)

def material(name,color,rough=.65,metal=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    return m

def mesh(name,verts,faces,mat,smooth=False):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob);ob.data.materials.append(mat)
    for p in me.polygons:p.use_smooth=smooth
    return ob

def clean(poly):
    p=[]
    for x,y in poly:
        if not p or math.hypot(x-p[-1][0],y-p[-1][1])>1e-5:p.append((float(x),float(y)))
    if len(p)>1 and math.dist(p[0],p[-1])<1e-5:p.pop()
    return p

def extrude(name,poly,z0,z1,mat):
    p=clean(poly)
    if len(p)<3:return None
    n=len(p);verts=[(x,y,z) for z in (z0,z1) for x,y in p];faces=[]
    for i in range(n):j=(i+1)%n;faces.append([i,j,n+j,n+i])
    vv=[Vector((x,y,0)) for x,y in p]
    for tri in tessellate_polygon([vv]):
        idx=[v if isinstance(v,int) else min(range(n),key=lambda j:(vv[j]-v).length_squared) for v in tri]
        faces.append([i+n for i in idx]);faces.append(list(reversed(idx)))
    return mesh(name,verts,faces,mat)

def box(name,x,y,z,w,d,h,mat,angle=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z));o=bpy.context.object;o.name=name;o.scale=(w,d,h);o.rotation_euler.z=angle;o.data.materials.append(mat);return o

def cylinder(name,x,y,z,r,h,mat,n=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n,radius=r,depth=h,location=(x,y,z));o=bpy.context.object;o.name=name;o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return o

def inside(p,x,y):
    ok=False
    for a,b in zip(p,p[1:]+p[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:ok=not ok
    return ok

def clip(poly,u0,u1,v0,v1):
    p=list(poly)
    for axis,edge,sign in [(0,u0,1),(0,u1,-1),(1,v0,1),(1,v1,-1)]:
        out=[]
        if not p:return []
        for a,b in zip(p,p[1:]+p[:1]):
            aa=(a[axis]-edge)*sign>=-1e-6;bb=(b[axis]-edge)*sign>=-1e-6
            if aa:out.append(a)
            if aa!=bb:
                t=(edge-a[axis])/(b[axis]-a[axis]);out.append(tuple(a[j]+t*(b[j]-a[j]) for j in range(2)))
        p=out
    return clean(p)

class Frame:
    def __init__(self,lm):
        p=clean([(x-lm['center'][0],-(z-lm['center'][1])) for x,z in lm['footprint']])
        a,b=max(zip(p,p[1:]+p[:1]),key=lambda ab:math.dist(*ab));ang=math.atan2(b[1]-a[1],b[0]-a[0]);self.angle=ang;self.c=math.cos(ang);self.s=math.sin(ang)
        q=[(x*self.c+y*self.s,-x*self.s+y*self.c) for x,y in p]
        self.mid=((min(x for x,y in q)+max(x for x,y in q))/2,(min(y for x,y in q)+max(y for x,y in q))/2)
        self.poly=[(x-self.mid[0],y-self.mid[1]) for x,y in q]
        self.w=max(x for x,y in self.poly)-min(x for x,y in self.poly);self.d=max(y for x,y in self.poly)-min(y for x,y in self.poly)
    def xy(self,u,v):
        u+=self.mid[0];v+=self.mid[1];return u*self.c-v*self.s,u*self.s+v*self.c
    def polyxy(self,p):return [self.xy(u,v) for u,v in p]
    def extrude(self,name,p,z0,z1,mat):return extrude(name,self.polyxy(p),z0,z1,mat)
    def box(self,name,u,v,z,w,d,h,mat):return box(name,*self.xy(u,v),z,w,d,h,mat,self.angle)
    def cyl(self,name,u,v,z,r,h,mat,n=64):return cylinder(name,*self.xy(u,v),z,r,h,mat,n)

def edges(name,poly,z,h,depth,mat):
    for i,(a,b) in enumerate(zip(poly,poly[1:]+poly[:1])):
        leng=math.dist(a,b)
        if leng<.08:continue
        box(name+'_'+str(i),(a[0]+b[0])/2,(a[1]+b[1])/2,z,leng,depth,h,mat,math.atan2(b[1]-a[1],b[0]-a[0]))

def window_grid(prefix,poly,z0,z1,glass,frame,spacing=3.2,floor=3.6,vertical_piers=None,punched=False):
    # Actual edge-aligned glazing; no world-axis shader windows on spandrels.
    for e,(a,b) in enumerate(zip(poly,poly[1:]+poly[:1])):
        length=math.dist(a,b)
        if length<1:continue
        ux=(b[0]-a[0])/length;uy=(b[1]-a[1])/length;nx=uy;ny=-ux
        mx=(a[0]+b[0])/2;my=(a[1]+b[1])/2
        if inside(poly,mx+nx*.2,my+ny*.2):nx=-nx;ny=-ny
        angle=math.atan2(uy,ux);nf=max(1,round((z1-z0)/floor));step=(z1-z0)/nf;cols=max(1,int(length/spacing))
        for k in range(nf):
            y=z0+k*step+.8;hh=min(step*.63,z1-y-.12)
            if hh<=0:continue
            if punched:
                for j in range(cols):
                    t=(j+.5)/cols
                    box(f'{prefix}_window_{e}_{k}_{j}',a[0]+ux*length*t+nx*.04,a[1]+uy*length*t+ny*.04,y+hh/2,length/cols*.57,.10,hh,glass,angle)
            else:
                box(f'{prefix}_glass_{e}_{k}',mx+nx*.025,my+ny*.025,y+hh/2,max(.1,length-.24),.08,hh,glass,angle)
        for k in ([] if punched else range(1,cols)):
            t=k/cols;x=a[0]+ux*length*t+nx*.08;y=a[1]+uy*length*t+ny*.08
            box(f'{prefix}_mullion_{e}_{k}',x,y,(z0+z1)/2,.10,.13,z1-z0,frame,angle)
        if vertical_piers:
            for k in range(cols+1):
                t=k/cols;x=a[0]+ux*length*t+nx*.16;y=a[1]+uy*length*t+ny*.16
                box(f'{prefix}_pier_{e}_{k}',x,y,(z0+z1)/2,.42,.25,z1-z0,vertical_piers,angle)

def batch_facade_details():
    # Preserve structural/roof object names for independent QA. Repeated facade
    # details share one draw per material instead of thousands of tiny meshes.
    import re
    groups={}
    for o in list(bpy.context.scene.objects):
        if o.type=='MESH' and re.search(r'_window_|_mullion_|_mull_|_blade_|_transom_|_pier_',o.name) and len(o.data.materials)==1:
            mat=o.data.materials[0];groups.setdefault(mat.name,[]).append(o)
    for name,parts in groups.items():
        if len(parts)<2:continue
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts:o.select_set(True)
        bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join()
        bpy.context.object.name='DETAIL_window_batch_'+name
    bpy.ops.object.select_all(action='DESELECT')

def export(slug):
    batch_facade_details()
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'assets','models',slug+'.blend'))
    bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'assets','models',slug+'.glb'),export_format='GLB',export_apply=True)
    print('BUILT',slug,len(bpy.context.scene.objects),flush=True)
