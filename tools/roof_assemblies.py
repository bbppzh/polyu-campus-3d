"""Connected roof assemblies and a closed hall-to-vault junction (Blender)."""
import bpy,bmesh,math
from mathutils import Vector
from architecture import box,mesh

def fit_vault(roof_name,glass_names,hall_name,poly,base,mat,remove=()):
    """Clip a vault to the hall plan and close the walls up to its underside."""
    area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1]))
    for name in [roof_name,*glass_names]:
        ob=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(ob.data)
        for a,b in zip(poly,poly[1:]+poly[:1]):
            dx,dy=b[0]-a[0],b[1]-a[1];normal=Vector((dy,-dx,0)).normalized()*(1 if area>0 else -1)
            cut=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,
                plane_co=Vector((a[0],a[1],0)),plane_no=normal,clear_outer=True,clear_inner=False)
            if name==roof_name:
                border=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
                if border:bmesh.ops.holes_fill(bm,edges=border,sides=0)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
        bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
        if name==roof_name and bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
        bm.to_mesh(ob.data);bm.free();ob.data.update()
    roof=bpy.data.objects[roof_name];roof.data.calc_loop_triangles()
    # Bottom triangles of the closed shell are the new hall's top. This exact
    # shared surface removes both the open gap and wall/roof penetration.
    tris=[tuple(t.vertices) for t in roof.data.loop_triangles if t.normal.z<-.02]
    used=sorted({i for t in tris for i in t});idx={v:i for i,v in enumerate(used)}
    top=[roof.matrix_world@roof.data.vertices[i].co for i in used];n=len(top)
    verts=[tuple(v) for v in top]+[(v.x,v.y,base) for v in top]
    topfaces=[tuple(idx[i] for i in reversed(t)) for t in tris];faces=topfaces+[tuple(i+n for i in reversed(t)) for t in topfaces]
    edges={}
    for t in topfaces:
        for a,b in zip(t,t[1:]+t[:1]):
            key=tuple(sorted((a,b)));edges.setdefault(key,[]).append((a,b))
    for pairs in edges.values():
        if len(pairs)==1:
            a,b=pairs[0];faces.append((a,a+n,b+n,b))
    old=bpy.data.objects.get(hall_name)
    if old:bpy.data.objects.remove(old,do_unlink=True)
    mesh(hall_name,verts,faces,mat)
    for name in remove:
        ob=bpy.data.objects.get(name)
        if ob:bpy.data.objects.remove(ob,do_unlink=True)
