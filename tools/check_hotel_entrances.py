#!/usr/bin/env python3
"""Independent GLB checks: every entrance bottom corner, top corner, centre.
Uses exported world-space triangles; does not import/run a Blender builder.
"""
import ast,json,pathlib,hashlib,struct
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent.parent
# Reuse only pure GLB parsing/math functions; do not execute the audit's job.
source=ast.parse((ROOT/'tools/audit_models.py').read_text());names={'matrix','read_model','inside','heights'}
exec(compile(ast.Module(body=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'<pure-glb-reader>','exec'))
d=json.loads((ROOT/'data/campus.json').read_text());lm=next(l for l in d['landmarks'] if l['name']=='Hotel ICON');registration=json.loads((ROOT/'data/hotel-entrances.json').read_text());glb=ROOT/'assets/models/hotel_icon.glb';mm=read_model(glb)
solids=[m for m in mm if m['name'].startswith('ICON_') and not m['name'].startswith('ICON_entrance_')];details=[m for m in mm if m['name'].startswith('ICON_entrance_')]
issues=[];rows=[];totalbottom=0;primarybottom=0
excluded={236028367,236028374,236028379}
def enclosing(p):
 found=[]
 for b in solids:
  vv=b['v']
  if np.any(p<vv.min(0)-.0005) or np.any(p>vv.max(0)+.0005):continue
  hs=np.unique(np.round(heights(b['tri'],p[0],p[2]),5))
  # Exact wall/roof contact is allowed, volumetric burial is not.
  if len(hs) and np.min(abs(hs-p[1]))<.002:continue
  if sum(hs<p[1])%2:found.append(b['name'])
 w=np.array([p[0]+lm['center'][0],p[2]+lm['center'][1]])
 for b in d['context']:
  if b['id'] in excluded or b.get('height',0)<=p[1]+.002:continue
  poly=np.array(b['footprint'])
  if np.any(w<poly.min(0)) or np.any(w>poly.max(0)):continue
  if inside(np.array([w]),poly)[0]:found.append('context_'+str(b['id']))
 return found
for m in details:
 v=m['v'];lo=v[:,1].min();hi=v[:,1].max();bottom=np.unique(np.round(v[abs(v[:,1]-lo)<.0001],5),axis=0);top=np.unique(np.round(v[abs(v[:,1]-hi)<.0001],5),axis=0);center=(v.min(0)+v.max(0))/2
 primary=m['name'].endswith('_door') or m['name'].endswith('_canopy');totalbottom+=len(bottom);primarybottom+=len(bottom) if primary else 0;checked=[]
 for kind,pts in [('bottom_corner',bottom),('top_corner',top),('centre',[center])]:
  for i,p in enumerate(pts):
   hit=enclosing(np.array(p));checked.append({'kind':kind,'index':i,'xyz':np.array(p).tolist(),'inside_solids':hit})
   if hit:issues.append({'mesh':m['name'],'point_kind':kind,'point':np.array(p).tolist(),'inside_solids':hit})
 if m['name'].endswith('_door') and abs(lo-.02)>.005:issues.append({'mesh':m['name'],'kind':'threshold not on model GF datum'})
 rows.append({'mesh':m['name'],'is_primary_door_or_canopy':primary,'bottom_corner_count':len(bottom),'points':checked})
registered=[]
for e in registration['entries']:
 mesh=next(m for m in details if m['name']==f'ICON_entrance_{e["id"]}_door');c=(mesh['v'].min(0)+mesh['v'].max(0))/2;p=np.array(e['wall_world_xz']);n=np.array(e['outward_world_xz']);u=np.array(e['tangent_world_xz']);actual=c[[0,2]]+lm['center'];err=float(np.linalg.norm(actual-(p+n*.15)));approach=[]
 if err>.002:issues.append({'entry':e['id'],'kind':'export differs from registered position','distance_m':err})
 # Check the full door-width approach at ground/eye heights, at 0.25m steps.
 for dist in np.arange(.3,8.01,.25):
  for lateral in [-e['door_width_m']/2,0,e['door_width_m']/2]:
   w=p+n*dist+u*lateral
   for y in [.08,1.7]:
    local=np.array([w[0]-lm['center'][0],y,w[1]-lm['center'][1]]);hit=enclosing(local)
    if hit:approach.append({'distance_m':float(dist),'lateral_m':lateral,'height_m':y,'inside_solids':hit})
 if approach:issues.append({'entry':e['id'],'kind':'blocked approach samples','samples':approach})
 registered.append({'id':e['id'],'export_position_error_m':err,'plan_to_wall_snap_m':e['snap_distance_m'],'approach_samples':len(np.arange(.3,8.01,.25))*3*2,'blocked_approach_samples':len(approach)})
if len(details)!=24 or primarybottom!=24 or totalbottom!=96:issues.append({'kind':'missing entrance objects/corners','objects':len(details),'primary_bottom_corners':primarybottom,'all_bottom_corners':totalbottom})
report={'status':'PASS' if not issues else 'FAIL','model_sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),'registration_fit_rmse_m':registration['fit_rmse_m'],'registration_holdout_rmse_m':registration['check_rmse_m'],'primary_door_canopy_bottom_corners_checked':primarybottom,'all_entrance_bottom_corners_checked':totalbottom,'objects_checked':len(rows),'entries':registered,'objects':rows,'issues':issues,'scope':'All exported entrance-object bottom/top corners and centres, owner/foreign Hotel solids and neighbouring context; approach sampled at two heights. Not a surveyed/as-built position or vertical-level certification.'}
(ROOT/'docs/hotel-entrances/geometry-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(report['status'],'objects',len(rows),'primary bottom corners',primarybottom,'all bottom corners',totalbottom,'issues',len(issues))
for i in issues:print(i)
if issues:raise SystemExit(1)
