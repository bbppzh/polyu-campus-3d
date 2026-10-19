"""Place facade assemblies in the host wall's coordinates, not its world AABB.
Geometry repair only: these dimensions retain the existing approximate massing.
"""
import math
import bpy
from architecture import clean, inside, box, mesh, extrude


class Face:
    def __init__(self, poly, index):
        self.poly = clean(poly)
        self.index = index
        self.a = self.poly[index]
        self.b = self.poly[(index + 1) % len(self.poly)]
        self.length = math.dist(self.a, self.b)
        self.t = tuple((self.b[k] - self.a[k]) / self.length for k in range(2))
        self.n = (self.t[1], -self.t[0])
        self.mid = tuple((self.a[k] + self.b[k]) / 2 for k in range(2))
        if inside(self.poly, *self.xy(0, .05)):
            self.n = tuple(-v for v in self.n)
        self.angle = math.atan2(self.t[1], self.t[0])

    def xy(self, u=0, outward=0):
        return tuple(self.mid[k] + self.t[k]*u + self.n[k]*outward for k in range(2))

    def box(self, name, u, outward, z, width, depth, height, material):
        return box(name, *self.xy(u, outward), z, width, depth, height, material, self.angle)


def nearest_face(poly, anchor, min_length=0):
    faces = [Face(poly, i) for i in range(len(clean(poly)))
             if math.dist(clean(poly)[i], clean(poly)[(i+1) % len(clean(poly))]) >= max(.01, min_length)]
    if not faces:
        raise ValueError('No host edge long enough for the assembly')
    # Distance to the usable centre, reserving the assembly's half-width at ends.
    def distance(f):
        along = sum((anchor[k]-f.mid[k])*f.t[k] for k in range(2))
        along = max(-(f.length-min_length)/2, min((f.length-min_length)/2, along))
        return math.dist(anchor, f.xy(along, 0))
    return min(faces, key=distance)


def entrance(prefix, poly, anchor, width, height, glass, trim, count=5, steps=False):
    face = nearest_face(poly, anchor, width+2.8)
    # Back edge is seated 4 cm into the host wall; all front edges share a plane.
    face.box(prefix+'_atrium', 0, .88, height/2, width, 1.84, height, glass)
    face.box(prefix+'_canopy', 0, 1.55, height+.175, width+2.6, 3.3, .35, trim)
    for k in range(count):
        u = -width/2 + .12 + (width-.24)*k/(count-1)
        face.box(f'{prefix}_entry_frame_{k}', u, 1.83, height/2, .14, .14, height, trim)
    if steps:
        # Highest landing meets the ground-level doors; no risers across them.
        face.box(prefix+'_landing', 0, 1.55, .08, width+.6, 3.3, .16, trim)
    return face


def halfplane(poly, point, normal, positive=True):
    """Clip a polygon by a plane. Used only for a single convex corner cut."""
    p = clean(poly); result=[]; sign=1 if positive else -1
    for a,b in zip(p,p[1:]+p[:1]):
        da=sum((a[k]-point[k])*normal[k] for k in range(2))*sign
        db=sum((b[k]-point[k])*normal[k] for k in range(2))*sign
        if da>=-1e-8: result.append(a)
        if (da>=0)!=(db>=0):
            t=da/(da-db);result.append(tuple(a[k]+t*(b[k]-a[k]) for k in range(2)))
    return clean(result)


def corner_partition(poly, anchor, depth=4):
    p=clean(poly)
    area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1]))
    convex=[]
    for i,v in enumerate(p):
        a=p[i-1];b=p[(i+1)%len(p)]
        cross=(v[0]-a[0])*(b[1]-v[1])-(v[1]-a[1])*(b[0]-v[0])
        if cross*area>0:convex.append(i)
    i=min(convex,key=lambda j:math.dist(p[j],anchor));v=p[i]
    f1=Face(p,(i-1)%len(p));f2=Face(p,i)
    inward=tuple(-(f1.n[k]+f2.n[k]) for k in range(2));n=math.hypot(*inward)
    inward=tuple(c/n for c in inward);point=tuple(v[k]+depth*inward[k] for k in range(2))
    return halfplane(p,point,inward),halfplane(p,point,inward,False)


def boolean(host, cutter, operation='DIFFERENCE', remove=True):
    bpy.ops.object.select_all(action='DESELECT');host.select_set(True)
    bpy.context.view_layer.objects.active=host
    mod=host.modifiers.new('Fitted component joint','BOOLEAN');mod.operation=operation;mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    if remove:bpy.data.objects.remove(cutter,do_unlink=True)
    return host


def perimeter_wall(name, poly, z0, z1, thickness, material):
    """One closed, mitred ring, including the final footprint edge."""
    p=clean(poly);inner=[]
    for i,v in enumerate(p):
        a=Face(p,(i-1)%len(p));b=Face(p,i)
        aa=a.xy(0,-thickness);bb=b.xy(0,-thickness)
        cross=a.t[0]*b.t[1]-a.t[1]*b.t[0]
        if abs(cross)<1e-7:inner.append(tuple(v[k]-b.n[k]*thickness for k in range(2)));continue
        d=(bb[0]-aa[0],bb[1]-aa[1]);t=(d[0]*b.t[1]-d[1]*b.t[0])/cross
        inner.append(tuple(aa[k]+a.t[k]*t for k in range(2)))
    n=len(p);verts=[(x,y,z) for z in (z0,z1) for ring in (p,inner) for x,y in ring];faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(i,j,2*n+j,2*n+i),(n+j,n+i,3*n+i,3*n+j),
                      (2*n+i,2*n+j,3*n+j,3*n+i),(j,i,n+i,n+j)])
    return mesh(name,verts,faces,material)
