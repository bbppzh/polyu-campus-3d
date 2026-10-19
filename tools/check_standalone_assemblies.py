#!/usr/bin/env python3
"""Check that unsupported rooftop props are absent and vault joints remain closed.
Requires numpy and shapely. Run after rebuilding the named GLBs.
"""
import ast,json,struct,pathlib,re,hashlib
import numpy as np
from shapely.geometry import MultiPoint
ROOT=pathlib.Path(__file__).resolve().parent.parent
code=ast.parse((ROOT/'tools/audit_models.py').read_text());ns={'np':np,'json':json,'struct':struct}
exec(compile(ast.Module(body=[n for n in code.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'glb_reader','exec'),ns)
read=ns['read_model'];heights=ns['heights'];errors=[];assemblies=[]
source=ast.parse((ROOT/'tools/roof_support.py').read_text())
pattern=next(n.value.args[0].value for n in source.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='UNVERIFIED_ROOF_PROPS' for t in n.targets))
forbidden=re.compile(pattern,re.I)
slugs=['lks','jcit','jca','gsh','shaw','blockx','blockz','chan','taio','anita','chow','mong','ng','yip','seal','cma','chung','lui','stanley','choi','shirley','gh','fong','tang','leeshaukee','hoi','industrial','communal','library','hotel_icon']
for slug in slugs:
 path=ROOT/'assets/models'/f'{slug}.glb';mm=read(path)
 remaining=[m['name'] for m in mm if forbidden.search(m['name'])]
 if remaining:errors.append({'slug':slug,'kind':'unverified roof props remain','names':remaining})
 assemblies.append({'slug':slug,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'unverified_roof_props':remaining})
vaults=[]
for slug,roof_name,hall_name in [('jca','JCA_roof','JCA_hall'),('shaw','SHAW_vault','SHAW_hall')]:
 path=ROOT/'assets/models'/f'{slug}.glb';mm=read(path);roof=next(m for m in mm if m['name']==roof_name);hall=next(m for m in mm if m['name']==hall_name)
 tri=roof['tri'];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);bottom=tri[norm[:,1]/np.maximum(np.linalg.norm(norm,axis=1),1e-12)<-.02];gap=[]
 for face in bottom:
  p=face.mean(0);hh=heights(hall['tri'],p[0],p[2]);gap.append(float(p[1]-hh.max()) if len(hh) else 999.)
 maxgap=max(abs(g) for g in gap)
 if maxgap>.005:errors.append({'slug':slug,'kind':'hall/roof gap or penetration','max_abs_gap_m':maxgap})
 vaults.append({'slug':slug,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'underside_triangles_checked':len(bottom),'max_abs_gap_m':maxgap})
report={'models':assemblies,'vaults':vaults,'errors':errors,'scope':'Actual exported GLBs. All 30 named models checked for removed unsupported roof-decoration categories; curved roof underside triangle centres against the matching hall top. Structural joints may touch; not a complete triangle-pair collision certification.'}
(ROOT/'docs/standalone-assemblies-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if errors:raise SystemExit(1)
