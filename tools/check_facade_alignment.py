#!/usr/bin/env python3
"""Independent alignment regression checks on the exported six GLBs.
No Blender-builder imports. Requires numpy and shapely.
"""
import ast, json, struct, hashlib, pathlib
import numpy as np
from shapely.geometry import Polygon, MultiPoint, LineString
from shapely.ops import unary_union
ROOT=pathlib.Path(__file__).resolve().parent.parent
code=ast.parse((ROOT/'tools/audit_models.py').read_text())
ns={'np':np,'json':json,'struct':struct}
exec(compile(ast.Module(body=[n for n in code.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'reader','exec'),ns)
MODELS={'seal':('SOL','Seal of Love Foundation Building'),'chung':('CSY','Chung Sze Yuen Building'),
        'stanley':('SHB','Stanley Ho Building'),'tang':('TPY','Tang Ping Yuan Building'),
        'hoi':('HOI','House of Innovation'),'gh':('GHB','GH Block')}
landmarks=json.loads((ROOT/'data/campus.json').read_text())['landmarks']
errors=[];checks=[];models={}
def check(slug,kind,value,tolerance):
    ok=value<=tolerance
    checks.append({'slug':slug,'check':kind,'value':float(value),'maximum':tolerance,'pass':bool(ok)})
    if not ok:errors.append(checks[-1])
def shape(m):
    parts=[Polygon(t[:,[0,2]]) for t in m['tri'] if Polygon(t[:,[0,2]]).area>1e-9]
    return unary_union(parts)
def named(slug,name):
    # GLTF can split a node into several material primitives.
    matches=[m for m in models[slug] if m['name']==name]
    if not matches:raise AssertionError(f'{slug}: missing {name}')
    return {'name':name,'v':np.concatenate([m['v'] for m in matches]),'tri':np.concatenate([m['tri'] for m in matches])}
def plane_fit(slug,m,host):
    """Match the thin component to a real host polygon edge using all vertices."""
    pts=m['v'][:,[0,2]];p=list(host.exterior.coords)[:-1];choices=[]
    for a,b in zip(p,p[1:]+p[:1]):
        a,b=np.array(a),np.array(b);t=(b-a)/np.linalg.norm(b-a);n=np.array([t[1],-t[0]])
        mid=(a+b)/2
        from shapely.geometry import Point
        if host.contains(Point(mid+n*.01)):n=-n
        along=(pts-a)@t;depth=(pts-a)@n
        if along.min()>=-.003 and along.max()<=np.linalg.norm(b-a)+.003:
            choices.append((max(abs(depth.min()+.015),abs(depth.max()-.085)),depth,t,n,a))
    if not choices:raise AssertionError('Component extends past every host edge')
    return min(choices,key=lambda x:x[0])
for slug,(prefix,name) in MODELS.items():
    path=ROOT/'assets/models'/f'{slug}.glb';models[slug]=ns['read_model'](path)
    lm=next(l for l in landmarks if l['name']==name)
    footprint=Polygon([(x-lm['center'][0],z-lm['center'][1]) for x,z in lm['footprint']])
    a=named(slug,prefix+'_atrium');c=named(slug,prefix+'_canopy')
    ap=shape(a);cp=shape(c)
    # Atrium's rear edge must run along one actual building edge, seated 4 cm.
    best=None
    p=list(footprint.exterior.coords)[:-1]
    for u,v in zip(p,p[1:]+p[:1]):
        u,v=np.array(u),np.array(v);t=(v-u)/np.linalg.norm(v-u);n=np.array([t[1],-t[0]])
        from shapely.geometry import Point
        if footprint.contains(Point((u+v)/2+n*.01)):n=-n
        pts=a['v'][:,[0,2]];d=(pts-u)@n;s=(pts-u)@t
        mismatch=max(abs(d.min()+.04),abs(d.max()-1.8))
        if s.min()<0 or s.max()>np.linalg.norm(v-u):mismatch+=10
        if best is None or mismatch<best[0]:best=(mismatch,t,n,u)
    check(slug,'entry wall-plane registration error (m)',best[0],.0001)
    check(slug,'canopy underside / atrium top gap (m)',abs(c['v'][:,1].min()-a['v'][:,1].max()),.0001)
    check(slug,'atrium footprint outside canopy (m2)',ap.difference(cp).area,.0001)
    for frame in [m for m in models[slug] if '_entry_frame_' in m['name']]:
        check(slug,frame['name']+' vertical mismatch (m)',max(abs(frame['v'][:,1].min()-a['v'][:,1].min()),abs(frame['v'][:,1].max()-a['v'][:,1].max())),.0001)
        depth=(frame['v'][:,[0,2]]-best[3])@best[2]
        check(slug,frame['name']+' front-plane mismatch (m)',max(abs(depth.min()-1.76),abs(depth.max()-1.90)),.0001)
    # Structural layers with coincident outside faces used to z-fight.
    structural=[m for m in models[slug] if any(s in m['name'] for s in ['_podium','_band','_tower','_upper','_storey','_roof_slab','_glass','_core']) and '_frame_' not in m['name']]
    for i,m in enumerate(structural):
        for n in structural[i+1:]:
            overlap=min(m['v'][:,1].max(),n['v'][:,1].max())-max(m['v'][:,1].min(),n['v'][:,1].min())
            if overlap>.001:
                check(slug,m['name']+' / '+n['name']+' solid overlap (m2)',shape(m).intersection(shape(n)).area,.001)
    if slug in ['seal','chung']:
        ring=shape(named(slug,prefix+'_parapet'))
        check(slug,'missing parapet footprint edge (m)',footprint.boundary.difference(ring.buffer(.001)).length,.001)
    if slug=='seal':
        glass=shape(named(slug,'SOL_glass_tower'))
        for support in ['SOL_podium','SOL_band_0','SOL_roof_slab']:
            check(slug,'circular stair coverage by '+support+' (m2)',glass.difference(shape(named(slug,support)).buffer(.0001)).area,.001)
    if slug=='hoi':
        core=shape(named(slug,'HOI_core'))
        check(slug,'core outside roof envelope (m2)',core.difference(shape(named(slug,'HOI_roof_slab'))).area,.001)
    if slug=='tang':
        host=shape(named(slug,'TPY_upper'))
        for k in range(5):
            check(slug,f'upper slit {k} wall-plane error (m)',plane_fit(slug,named(slug,f'TPY_slit_{k}'),host)[0],.0001)
    if slug=='stanley':
        green=named(slug,'SHB_green_wall');host=shape(named(slug,'SHB_tower'))
        fit=plane_fit(slug,green,host)
        # Backing has 2 cm insertion, 20 cm projection; all frames stay on it.
        check(slug,'green wall host-plane error (m)',max(abs(fit[1].min()+.02),abs(fit[1].max()-.20)),.0001)
        for k in range(3):
            slab=named(slug,f'SHB_balcony_{k}');rail=named(slug,f'SHB_rail_{k}')
            check(slug,f'balcony {k} rail support gap (m)',abs(rail['v'][:,1].min()-slab['v'][:,1].max()),.0001)
            check(slug,f'balcony {k} rail overhang (m2)',shape(rail).difference(shape(slab).buffer(.0001)).area,.0001)
report={'models':[{'slug':s,'sha256':hashlib.sha256((ROOT/'assets/models'/f'{s}.glb').read_bytes()).hexdigest()} for s in MODELS],
        'checks':checks,'errors':errors,'scope':'Actual exported GLB vertices/triangles: entry registration, canopy/frame joints, overlapping structural layers, core/corner partitions, parapet coverage, upper windows, green-wall and balcony joints. No surveyed-fidelity or full triangle-pair certification.'}
(ROOT/'docs/facade-alignment-qa.json').write_text(json.dumps(report,indent=2)+'\n')
print('FACADE ALIGNMENT:',len(MODELS),'models;',len(checks),'checks;',len(errors),'errors')
for e in errors:print(e)
if errors:raise SystemExit(1)
