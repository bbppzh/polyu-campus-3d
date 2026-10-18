import ast,json,sys,pathlib,struct,numpy as np,re,time
R=pathlib.Path(__file__).resolve().parent.parent;out=R/'docs/model-intersections-qa.json';s=ast.parse((R/'tools/audit_models.py').read_text());ns={'np':np,'struct':struct,'json':json};exec(compile(ast.Module(body=[n for n in s.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'qa','exec'),ns)
read=ns['read_model'];inside=ns['inside'];heights=ns['heights']
d=json.loads((R/'data/campus.json').read_text());slugs=['lks','jcit','jca','gsh','shaw','blockx','blockz','chan','taio','anita','chow','mong','ng','yip','seal','cma','chung','lui','stanley','choi','shirley','gh','fong','tang','leeshaukee','hoi','industrial','communal','library','hotel_icon'];models=[]
for l,slug in zip(d['landmarks'],slugs):
 mm=[m for m in read(R/'assets/models'/f'{slug}.glb') if not re.search(r'DETAIL|window|mullion|blade|transom|guard|spandrel|sill|column|pier|planter|lawn|rail|trunk|canopy|door|bracket|jamb|header|divider|roof_ac|vent|pole|fin_',m['name'],re.I)]
 for m in mm:
  m['tri']=m['tri']+np.array([l['center'][0],0,l['center'][1]]);m['lo']=m['tri'].min((0,1));m['hi']=m['tri'].max((0,1))
 lo=np.min([m['lo'] for m in mm],0);hi=np.max([m['hi'] for m in mm],0);models.append({'name':l['name'],'mm':mm,'lo':lo,'hi':hi})
def occupied(m,x,z,y):
 if not (m['lo'][0]+.05<x<m['hi'][0]-.05 and m['lo'][2]+.05<z<m['hi'][2]-.05 and m['lo'][1]+.02<y<m['hi'][1]-.02):return False
 hh=np.unique(np.round(heights(m['tri'],x,z),4));return np.count_nonzero(hh<y)%2==1
others=[]
layout=json.loads((R/'data/scene-layout.json').read_text()) if (R/'data/scene-layout.json').exists() else None
for b in (layout['context'] if layout else d['context']):
 if b['id'] in [236028367,236028374,236028379]:continue
 p=np.array(b['footprint']);others.append({'name':b.get('name') or str(b['id']),'id':b['id'],'poly':p,'holes':b.get('holes',[]),'lo':np.array([p[:,0].min(),0,p[:,1].min()]),'hi':np.array([p[:,0].max(),max(4,b['height']),p[:,1].max()])})
issues=[]
for i,a in enumerate(models):
 for b in models[i+1:]+others:
  lo=np.maximum(a['lo'],b['lo']);hi=np.minimum(a['hi'],b['hi'])
  if np.any(hi-lo<.15):continue
  pts=np.array([(x,z) for x in np.arange(lo[0]+.37,hi[0],1.5) for z in np.arange(lo[2]+.41,hi[2],1.5)])
  if not len(pts):continue
  if 'poly'in b:
   keep=inside(pts,b['poly'])
   for hole in b['holes']:keep &= ~inside(pts,np.array(hole))
   pts=pts[keep]
  if not len(pts):continue
  found=[]
  for y in [1.,3.,6.,10.,15.,20.,30.,40.,50.,60.]:
   if y>=hi[1]:continue
   hits=[]
   for x,z in pts:
    if any(occupied(m,x,z,y) for m in a['mm']) and ('poly'in b or any(occupied(m,x,z,y) for m in b['mm'])):hits.append([round(x,2),round(z,2)])
   if hits:found.append({'y':y,'area_estimate_m2':round(len(hits)*2.25,2),'points':hits[:3]})
  if found:issues.append({'a':a['name'],'b':b['name'],'context_id':b.get('id'),'levels':found})
 print('scanned',a['name'],flush=True)
out.write_text(json.dumps({'grid_spacing_m':1.5,'sample_heights_m':[1,3,6,10,15,20,30,40,50,60],'landmark_count':len(models),'overlaps':issues,'scope':'Actual exported structural triangles sampled against other landmarks and the rendered context. Facade details excluded. Sampling is not a proof of complete collision freedom.'},indent=2)+'\n');print('Sampled overlap pairs:',len(issues));
if issues:raise SystemExit(1)
