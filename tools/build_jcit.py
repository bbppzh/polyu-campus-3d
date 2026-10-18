#!/usr/bin/env python3
"""JCIT photo-referenced long slab with a sloping crown and continuous ribbons.
Source: ZHA built-project exterior photographs (Iwan Baan), 15 storeys.
71.2 m overall height: CVU/CTBUH record. Plan/profile proportions remain visual
approximations; no invented dome, pointed fin or 15-metre tower lean.
Only numpy is needed. Run python3 tools/build_jcit.py.
"""
import json,math,os,struct
import numpy as np
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,'assets','models','jcit.glb')
data=json.load(open(os.path.join(ROOT,'data','campus.json')))
lm=next(l for l in data['landmarks'] if l['name']=='Jockey Club Innovation Tower')
height=float(lm['height']);fp=np.array(lm['footprint'])-lm['center']
# Fit the long slab to the mapped compound rather than its longest single
# boundary edge (that edge faces Block X and is not the tower's long axis).
# Select the best-contained orientation while rejecting neighbouring footprints.
def contains(points,poly):
    result=np.zeros(len(points),bool)
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        if abs(b[1]-a[1])<1e-9:continue
        result ^= ((a[1]>points[:,1])!=(b[1]>points[:,1])) & (points[:,0]<(b[0]-a[0])*(points[:,1]-a[1])/(b[1]-a[1])+a[0])
    return result
sample=np.array([(x,z) for x in np.arange(-35.5,35.6,1) for z in np.arange(-14.5,14.6,1)
                 if max(abs(x)-30.5,0)**2+max(abs(z)-9.5,0)**2<=5.0**2])
axis=np.linalg.eigh(np.cov(fp.T))[1][:,-1]
if axis[0]>0:axis=-axis
reference=math.atan2(axis[1],axis[0]);scores=[]
neighbours=[np.array(l['footprint'])-lm['center'] for l in data['landmarks'] if l is not lm]
for angle in np.arange(reference-math.radians(35),reference+math.radians(35),math.radians(.5)):
    cu=np.array([math.cos(angle),math.sin(angle)]);cv=np.array([-cu[1],cu[0]])
    points=sample@np.array([cu,cv])
    outside=np.count_nonzero(~contains(points,fp))
    collision=sum(np.count_nonzero(contains(points,poly)) for poly in neighbours)
    scores.append((outside+collision*20,abs(angle-reference),angle))
angle=min(scores)[2];u=np.array([math.cos(angle),math.sin(angle)]);v=np.array([-u[1],u[0]])
mid=np.zeros(2) # landmark centre is the compound anchor, not a rotated bbox corner
print('JCIT compound alignment degrees',round(math.degrees(angle),2))
M=128;BASE=9.2
# Rounded rectangles have straight long faces and small rounded ends.
def rounded(a,b,r):
    pts=[]
    for sx,sy,ang in [(1,1,0),(-1,1,math.pi/2),(-1,-1,math.pi),(1,-1,math.pi*1.5)]:
        for j in range(12):
            t=ang+math.pi*.5*j/11;pts.append([sx*(a-r)+r*math.cos(t),sy*(b-r)+r*math.sin(t)])
    pts=np.array(pts);dist=np.linalg.norm(np.roll(pts,-1,axis=0)-pts,axis=1);cum=np.r_[0,np.cumsum(dist)]
    ans=[]
    for s in np.arange(M)*cum[-1]/M:
        k=min(len(pts)-1,np.searchsorted(cum,s,side='right')-1);t=(s-cum[k])/max(dist[k],1e-9);ans.append(pts[k]*(1-t)+pts[(k+1)%len(pts)]*t)
    return np.array(ans)
# Centre the slab in the mapped compound. The previous 15 m lateral offset
# displaced the podium into the Communal Building.
plan=rounded(34.5,13.6,5.0)
def ring(t,offset=0):
    # Full-height slab has gently varying width; the high end and sloped crown
    # are visible in the architect's opposite-side exterior photographs.
    scale=1+.045*math.sin(math.pi*t)-.035*t
    uv=plan*scale
    uv[:,0]+=1.8*t;uv[:,1]+=.7*math.sin(math.pi*t)
    uv[:,1]+=.65*np.sin(uv[:,0]/11+.4)*math.sin(math.pi*t)**2
    if offset:
        radial=uv/np.maximum(np.linalg.norm(uv,axis=1)[:,None],1e-9);uv+=radial*offset
    yy=BASE+(height-.35-BASE)*t-10.0*((plan[:,0]+34.5)/69)*(t**5)
    uv+=mid+np.array([0,0.0]);xz=uv[:,0,None]*u+uv[:,1,None]*v
    return np.c_[xz[:,0],yy,xz[:,1]]
def loft(rows):
    vv=np.vstack(rows);ff=[]
    for i in range(len(rows)-1):
        for j in range(M):
            a=i*M+j;b=i*M+(j+1)%M;c=(i+1)*M+(j+1)%M;d=(i+1)*M+j;ff.extend([[a,b,d],[b,c,d]])
    return vv,np.array(ff)
def solid_loft(rows,mat):
    vv,ff=loft(rows)
    for k,up in [(0,False),(len(rows)-1,True)]:
        ci=len(vv);vv=np.vstack([vv,rows[k].mean(0)])
        for j in range(M):
            a=k*M+j;b=k*M+(j+1)%M;ff=np.vstack([ff,[a,ci,b] if up else [a,b,ci]])
    return Prim(vv,orient_outward(vv,ff),mat)
def normals_smooth(verts, faces):
    normals = np.zeros_like(verts)
    tri = verts[faces]
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    for k in range(3):
        np.add.at(normals, faces[:, k], fn)
    lens = np.linalg.norm(normals, axis=1, keepdims=True)
    lens[lens == 0] = 1
    return normals / lens


def orient_outward(verts, faces):
    # make sure the averaged vertex normals point away from the local vertical axis
    n = normals_smooth(verts, faces)
    radial = verts.copy()
    radial[:, 1] = 0
    if np.mean(np.sum(n * radial, axis=1)) < 0:
        faces = faces[:, [0, 2, 1]]
    return faces


def cap_faces(ring_idx, center_idx, up=True):
    faces = []
    n = len(ring_idx)
    for j in range(n):
        a = ring_idx[j]
        b = ring_idx[(j + 1) % n]
        if up:
            faces.append([a, center_idx, b])
        else:
            faces.append([a, b, center_idx])
    return np.array(faces, dtype=np.int64)


class Prim:
    def __init__(self, verts, faces, material, smooth=True):
        if not smooth:
            tri = np.asarray(faces)
            p = verts[tri].reshape(-1, 3)
            nn = np.cross(p[1::3] - p[0::3], p[2::3] - p[0::3])
            nn /= np.linalg.norm(nn, axis=1, keepdims=True) + 1e-12
            nrm = np.repeat(nn, 3, axis=0)
            idx = np.arange(len(p), dtype=np.uint32)
            self.positions = p.astype(np.float32)
            self.normals = nrm.astype(np.float32)
            self.indices = idx
        else:
            self.positions = np.asarray(verts, dtype=np.float32)
            self.normals = normals_smooth(verts, faces).astype(np.float32)
            self.indices = np.asarray(faces, dtype=np.uint32).reshape(-1)
        self.material = material



prims=[]
prims.append(solid_loft([ring(i/40,-.22) for i in range(41)],'glass'))
# Each white ribbon is a closed 0.3-metre shell that follows the glazing.
for y in np.arange(BASE+4.2,height-1,4.2):
    t0=(y-BASE)/(height-BASE);t1=min(1,t0+1.05/(height-BASE))
    outer0,outer1=ring(t0,.12),ring(t1,.12);inner0,inner1=ring(t0,-.25),ring(t1,-.25)
    verts=np.vstack([outer0,outer1,inner0,inner1]);faces=[]
    for j in range(M):
        k=(j+1)%M
        faces.extend([[j,k,M+j],[k,M+k,M+j],[2*M+j,3*M+j,2*M+k],[2*M+k,3*M+j,3*M+k],
                      [j,2*M+j,k],[k,2*M+j,2*M+k],[M+j,M+k,3*M+j],[M+k,3*M+k,3*M+j]])
    prims.append(Prim(verts,orient_outward(verts,np.array(faces)),'white'))
# Sloping planar roof joins the actual crown; no dome or mast.
r=ring(1,.12);top=r.copy();top[:,1]+=.35
cv=np.vstack([r,top,r.mean(0),top.mean(0)]);cf=[]
for j in range(M):
    k=(j+1)%M
    cf.extend([[j,k,M+j],[k,M+k,M+j],[M+j,2*M+1,M+k],[j,k,2*M]])
prims.append(Prim(cv,np.array(cf),'white',smooth=False))
# Compact low podium aligned with the tower, avoiding an unrelated circular base.
rows=[]
for yy,a,b in [(0,31.5,12.0),(BASE,36,15)]:
    base=rounded(a,b,5.5)+mid+np.array([0,0.0]);xz=base[:,0,None]*u+base[:,1,None]*v
    rows.append(np.c_[xz[:,0],np.full(M,yy),xz[:,1]])
prims.append(solid_loft(rows,'white'))
# --- write GLB ---------------------------------------------------------------
materials = [
    {"name": "white", "pbrMetallicRoughness": {"baseColorFactor": [0.90, 0.88, 0.84, 1.0],
                                                "metallicFactor": 0.0, "roughnessFactor": 0.62},
     "doubleSided": True},
    {"name": "glass", "pbrMetallicRoughness": {"baseColorFactor": [0.18, 0.27, 0.30, 1.0],
                                                "metallicFactor": 0.35, "roughnessFactor": 0.14},
     "doubleSided": True},
]

buffers = []
views = []
accessors = []
primitives = []

def add_view(data, target=None):
    pad = (-len(data)) % 4
    data = data + b"\x00" * pad
    offset = sum(len(b) for b in buffers)
    buffers.append(data)
    view = {"buffer": 0, "byteOffset": offset, "byteLength": len(data)}
    if target:
        view["target"] = target
    views.append(view)
    return len(views) - 1

def add_accessor(view, comp, count, typ, minv=None, maxv=None):
    acc = {"bufferView": view, "componentType": comp, "count": count, "type": typ}
    if minv is not None:
        acc["min"] = [float(x) for x in minv]
        acc["max"] = [float(x) for x in maxv]
    accessors.append(acc)
    return len(accessors) - 1

for prim in prims:
    pos = np.asarray(prim.positions, dtype=np.float32).reshape(-1, 3)
    nrm = np.asarray(prim.normals, dtype=np.float32).reshape(-1, 3)
    ind = np.asarray(prim.indices, dtype=np.uint32).reshape(-1)
    pv = add_view(pos.tobytes(), 34962)
    nv = add_view(nrm.tobytes(), 34962)
    iv = add_view(ind.tobytes(), 34963)
    pa = add_accessor(pv, 5126, len(pos), "VEC3", pos.min(axis=0), pos.max(axis=0))
    na = add_accessor(nv, 5126, len(nrm), "VEC3")
    ia = add_accessor(iv, 5125, len(ind), "SCALAR")
    primitives.append({
        "attributes": {"POSITION": pa, "NORMAL": na},
        "indices": ia,
        "material": 0 if prim.material == "white" else 1,
    })

binary = b"".join(buffers)
gltf = {
    "asset": {"version": "2.0", "generator": "polyu-campus-3d jcit builder"},
    "scene": 0,
    "scenes": [{"nodes": [0]}],
    "nodes": [{"mesh": 0, "name": "JCIT"}],
    "meshes": [{"name": "JCIT", "primitives": primitives}],
    "materials": materials,
    "buffers": [{"byteLength": len(binary)}],
    "bufferViews": views,
    "accessors": accessors,
}
json_text = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
json_pad = (-len(json_text)) % 4
json_text += b" " * json_pad
bin_pad = (-len(binary)) % 4
binary += b"\x00" * bin_pad
total = 12 + 8 + len(json_text) + 8 + len(binary)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "wb") as f:
    f.write(struct.pack("<III", 0x46546C67, 2, total))
    f.write(struct.pack("<II", len(json_text), 0x4E4F534A))
    f.write(json_text)
    f.write(struct.pack("<II", len(binary), 0x004E4942))
    f.write(binary)
print("wrote", OUT, os.path.getsize(OUT), "bytes", "prims", len(primitives))
