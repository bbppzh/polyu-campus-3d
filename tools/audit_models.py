#!/usr/bin/env python3
"""Independent numeric QA of exported geometry, not the Blender scene.
Run python3 tools/audit_models.py. Requires numpy.
Checks finite triangles and sampled support/embedding of named rooftop props.
Cantilevered architecture and intentionally connected structural masses are
not treated as collisions; this is not a real-building survey.
"""
import json,pathlib,struct,re,hashlib
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent.parent
def matrix(n):
    if 'matrix' in n: return np.array(n['matrix']).reshape(4,4,order='F')
    x,y,z,w=n.get('rotation',[0,0,0,1])
    r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    m=np.eye(4);m[:3,:3]=r@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0]);return m

def read_model(path):
    raw=path.read_bytes(); size,kind=struct.unpack_from('<II',raw,12)
    g=json.loads(raw[20:20+size]); binary=raw[28+size:]; meshes=[]
    def acc(i):
        a=g['accessors'][i];bv=g['bufferViews'][a['bufferView']]
        dtype={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
        cnt={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        offset=bv.get('byteOffset',0)+a.get('byteOffset',0)
        stride=bv.get('byteStride',np.dtype(dtype).itemsize*cnt)
        return np.ndarray((a['count'],cnt),dtype=dtype,buffer=binary,offset=offset,strides=(stride,np.dtype(dtype).itemsize))
    def walk(i,parent):
        n=g['nodes'][i];m=parent@matrix(n)
        if 'mesh' in n:
            for pr in g['meshes'][n['mesh']]['primitives']:
                v=acc(pr['attributes']['POSITION']).astype(float)
                v=(np.c_[v,np.ones(len(v))]@m.T)[:,:3]
                idx=acc(pr['indices']).reshape(-1).astype(int) if 'indices' in pr else np.arange(len(v))
                if pr.get('mode',4)==4:meshes.append({'name':n.get('name',''), 'v':v,'tri':v[idx.reshape(-1,3)]})
        for j in n.get('children',[]):walk(j,m)
    for i in g['scenes'][g.get('scene',0)]['nodes']:walk(i,np.eye(4))
    return meshes

def inside(points,poly):
    x=points[:,0];z=points[:,1];ok=np.zeros(len(points),bool)
    for i,a in enumerate(poly):
        b=poly[(i+1)%len(poly)]
        if abs(b[1]-a[1])<1e-10:continue
        ok ^= ((a[1]>z)!=(b[1]>z)) & (x < (b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0])
    return ok

DATA=json.loads((ROOT/'data/campus.json').read_text())
slugs=['lks','jcit','jca','gsh','shaw','blockx','blockz','chan','taio','anita','chow','mong','ng','yip','seal','cma','chung','lui','stanley','choi','shirley','gh','fong','tang','leeshaukee','hoi','industrial','communal','library','hotel_icon']
features=re.compile(r'planter|_bed_|_lawn_|tree_trunk|_court$|_roof_plant$|_roof_ac_|_ac_\d|_vent_\d|_pergola_col|_pole_|_rail_|_canopy_column_|_drum_column_')
issues=[];models=[];checked=0

def heights(tris,x,z):
 a,b,c=tris[:,0],tris[:,1],tris[:,2];p=b-a;q=c-a;det=p[:,0]*q[:,2]-q[:,0]*p[:,2];valid=np.abs(det)>1e-8;den=np.where(valid,det,1)
 u=((x-a[:,0])*q[:,2]-(z-a[:,2])*q[:,0])/den;v=(p[:,0]*(z-a[:,2])-p[:,2]*(x-a[:,0]))/den
 valid &= (u>=-1e-5)&(v>=-1e-5)&(u+v<=1+1e-5)
 return a[valid,1]+u[valid]*p[valid,1]+v[valid]*q[valid,1]

for lm,slug in zip(DATA['landmarks'],slugs):
 file=ROOT/'assets/models'/f'{slug}.glb';mm=read_model(file);allv=np.concatenate([m['v'] for m in mm]);tri=np.concatenate([m['tri'] for m in mm]);bad=not np.isfinite(allv).all();deg=int((np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)<1e-8).sum())
 models.append({'name':lm['name'],'slug':slug,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'meshes':len(mm),'triangles':len(tri),'finite':not bad,'degenerate_triangles':deg,'actual_y_min':float(allv[:,1].min()),'actual_y_max':float(allv[:,1].max())})
 if bad:issues.append({'building':lm['name'],'kind':'nonfinite geometry'})
 for i,m in enumerate(mm):
  if not features.search(m['name']):continue
  checked+=1;vv=m['v'];bottom=vv[:,1].min();top=vv[:,1].max();pts=np.unique(np.round(vv[np.abs(vv[:,1]-bottom)<.001][:,[0,2]],5),axis=0)
  if len(pts)>16:pts=pts[np.linspace(0,len(pts)-1,16).astype(int)]
  center=pts.mean(0);pts=np.vstack([center,center+(pts-center)*.995]);others=np.concatenate([n['tri'] for j,n in enumerate(mm) if j!=i]);gaps=[]
  for x,z in pts:
   hs=heights(others,x,z);below=hs[hs<=bottom+.025];gaps.append(float(bottom-below.max()) if len(below) else float(bottom))
  if max(gaps)>.06:issues.append({'building':lm['name'],'mesh':m['name'],'kind':'support gap at bottom samples','max_gap':round(max(gaps),4),'center_gap':round(gaps[0],4)})
  # The entire prop's centre buried in a structural solid is different from a
  # normal small insertion into its supporting slab.
  cy=(bottom+top)/2
  for n in mm:
   if n is m or not re.search(r'_(tower|upper|mass|lower|podium|crown|base|parapet)$',n['name']):continue
   hs=np.unique(np.round(heights(n['tri'],*center),4))
   if len(hs)>=2 and hs[0]+.03<bottom and hs[-1]>top+.03:issues.append({'building':lm['name'],'mesh':m['name'],'kind':'buried in structural solid','body':n['name']})
# Regression for the visible coplanar roof caps found in the browser.
roof_cap_checks=[]
for slug,pairs in {
 'lks':[('LKS_executive_drum','LKS_drum_roof'),('LKS_drum_spandrel_4','LKS_drum_roof')],
 'hotel_icon':[('ICON_teaching_block','ICON_teaching_roof'),('ICON_vertical_core','ICON_core_roof'),('ICON_main_hotel_slab','ICON_hotel_roof')],
 'blockz':[('Z_south_wing','Z_south_roof'),('Z_north_wing','Z_north_roof')]
}.items():
 mm=read_model(ROOT/'assets/models'/f'{slug}.glb')
 for body,roof in pairs:
  b=next(m for m in mm if m['name']==body);r=next(m for m in mm if m['name']==roof)
  separation=float(r['v'][:,1].max()-b['v'][:,1].max())
  roof_cap_checks.append({'model':slug,'body':body,'roof':roof,'upper_surface_separation':round(separation,5)})
  if separation<.05:issues.append({'model':slug,'kind':'coplanar visible roof cap','body':body,'roof':roof})
report={'model_count':len(models),'checked_rooftop_objects':checked,'roof_cap_checks':roof_cap_checks,'issues':issues,'models':models,'scope':'Bottom-centre and bottom-vertex samples of named rooftop details; not a certification of complete collision freedom or surveyed fidelity.'}
out=ROOT/'docs/final-qa.json';out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('MODELS',len(models),'PROPS',checked,'ISSUES',len(issues),'DEGENERATE',sum(m['degenerate_triangles'] for m in models))
for r in issues:print(r)
