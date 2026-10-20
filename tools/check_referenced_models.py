#!/usr/bin/env python3
"""Check self-contained GLBs, model heights and the new supported roof surfaces.
These checks do not certify surveyed fidelity; see the separate photo comparison.
"""
import pathlib,json,struct,ast,hashlib,re
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
R=pathlib.Path(__file__).resolve().parent.parent
ns={'np':np,'json':json,'struct':struct};t=ast.parse((R/'tools/audit_models.py').read_text())
exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'reader','exec'),ns)
errors=[];records=[];models={}
def require(ok,message):
 if not ok:errors.append(message)
def projected(mesh):
 return unary_union([Polygon(t[:,[0,2]]) for t in mesh['tri'] if Polygon(t[:,[0,2]]).area>1e-8])
overrides=json.loads((R/'data/model-overrides.json').read_text())['models']
for o in overrides:
 slug=o['slug'];p=R/'assets/models'/f'{slug}.glb';raw=p.read_bytes();size=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+size]);mm=ns['read_model'](p);models[slug]=mm
 require(o['model_sha256']==hashlib.sha256(raw).hexdigest(),slug+' stale override')
 height=max(m['v'][:,1].max() for m in mm);require(abs(height-o['height'])<.011,slug+' UI/model height mismatch')
 require(len(g['meshes'])<=45,slug+' unbatched draw count')
 require(all('uri' not in i and 'bufferView' in i for i in g.get('images',[])),slug+' external texture dependency')
 mats=g['materials'];require(all(m['name'].startswith('REF_') for m in mats),slug+' generic shader material remains')
 textured={i for i,m in enumerate(mats) if 'baseColorTexture' in m.get('pbrMetallicRoughness',{})}
 require(bool(textured) or slug=='blockx',slug+' brick texture missing')
 for mesh in g['meshes']:
  for pr in mesh['primitives']:
   if pr.get('material') in textured:require('TEXCOORD_0' in pr['attributes'],slug+' missing exported texture UV')
 require(any(m['name'].startswith('DETAIL_baked_') for m in mm),slug+' missing baked facade geometry')
 records.append({'slug':slug,'sha256':o['model_sha256'],'height_m':float(height),'height_status':'visual estimate','mesh_draws':len(g['meshes']),'embedded_images':len(g.get('images',[]))})
# Count distinct horizontal glazing intervals in the actual LSK facade vertices.
blue=[m for m in models['leeshaukee'] if 'LSKB_blue' in m['name']]
ys=np.unique(np.round(np.concatenate([m['v'][:,1] for m in blue]),2));require(len(ys)==28,'LSK does not contain 14 distinct glazing rows')
require(40<next(r['height_m'] for r in records if r['slug']=='leeshaukee')<60,'LSK flattened')
require(next(r['height_m'] for r in records if r['slug']=='blockx')<12,'Block X is no longer low-rise')
mm=models['blockx'];deck=next(m for m in mm if m['name']=='BLKX_main_deck');deckpoly=projected(deck);landscape=[]
for m in mm:
 if 'verified_vegetated_surface' not in m['name']:continue
 outside=projected(m).difference(deckpoly.buffer(.0001)).area
 gap=abs(m['v'][:,1].min()-deck['v'][:,1].max())
 require(outside<.001,m['name']+' outside the deck');require(gap<.001,m['name']+' unsupported')
 landscape.append({'name':m['name'],'outside_deck_m2':float(outside),'base_gap_m':float(gap)})
require(len(landscape)==3,'missing supported roof landscape')
require(not any(re.search(r'BLKX_(court|fence|pole|lamp)',m['name']) for m in mm),'obsolete outdoor court returned')
# Every ramp post foot is checked against the sloping deck/wing triangles.
body=np.concatenate([m['tri'] for m in mm if m['name'] in ['BLKX_accessible_ramp','BLKX_wing_cap']]);posts=[]
for m in mm:
 if 'ramp_guard_post' not in m['name']:continue
 vv=m['v'];bottom=vv[:,1].min();pts=np.unique(np.round(vv[abs(vv[:,1]-bottom)<1e-5][:,[0,2]],5),axis=0)
 gaps=[]
 for x,z in pts:
  hh=ns['heights'](body,x,z);near=hh[abs(hh-bottom)<.03];gaps.append(float(min(abs(near-bottom))) if len(near) else 999)
 maxgap=max(gaps);require(maxgap<.01,m['name']+' unsupported ramp post');posts.append({'name':m['name'],'max_abs_foot_gap_m':maxgap})
report={'models':records,'lsk_glazing_rows':len(ys)//2,'roof_landscape':landscape,'ramp_posts':posts,'errors':errors,
        'scope':'Actual exported geometry/materials. Self-contained images and UVs, bounded draw counts, UI heights, LSK glazing-row count, Block X landscape/deck coverage and ramp-post foot support. Visual fidelity is separately compared against cited photographs; all dimensions remain estimates.'}
(R/'docs/referenced-models-qa.json').write_text(json.dumps(report,indent=2)+'\n')
print('Referenced models:',len(records),'errors:',len(errors));print(json.dumps(records))
for e in errors:print(e)
if errors:raise SystemExit(1)
