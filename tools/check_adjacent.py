import runpy,contextlib,io,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parent.parent
with contextlib.redirect_stdout(io.StringIO()):s=runpy.run_path(str(R/'tools/audit_models.py'))
d=s['DATA'];read=s['read_model'];heights=s['heights'];inside=s['inside'];slugs=s['slugs'];out=[]
allm={l['name']:read(R/'assets/models'/f'{slug}.glb') for l,slug in zip(d['landmarks'],slugs)}
for l in d['landmarks']:
 if l['name'] not in ['Li Ka Shing Tower','Jockey Club Innovation Tower','Hotel ICON','Block Z']:continue
 mm=[m for m in allm[l['name']] if not any(t in m['name'].lower() for t in ['window','blade','transom','mullion','guard','spandrel','sill','column'])];v=np.concatenate([m['v'] for m in mm]);lo=v.min(0)[[0,2]]+l['center'];hi=v.max(0)[[0,2]]+l['center'];pts=np.array([(x,z) for x in np.arange(lo[0]+1,hi[0],2) for z in np.arange(lo[1]+1,hi[1],2)])
 # Only inspect the main occupied tower above its connected podium (or 1 m for Z).
 y=20 if l['name']!='Block Z' else 20
 occ=[]
 for x,z in pts:
  local=np.array([x,z])-l['center'];hit=False
  for m in mm:
   hh=heights(m['tri'],*local)
   if len(hh)>=2 and hh.min()+.02<y<hh.max()-.02:hit=True;break
  occ.append(hit)
 pts=pts[occ]
 for b in d['context']+d['landmarks']:
  if b is l or b.get('id') in {236028367,236028374,236028379}:continue
  if b['height']<=y:continue
  ps=pts[inside(pts,np.array(b['footprint']))]
  if len(ps):out.append({'building':l['name'],'other':b.get('name',b['id']),'height':y,'approx_overlap_m2':len(ps)*4,'samples':ps[:3].tolist()})
print(json.dumps(out,indent=2))
(R/'docs/final-adjacent-qa.json').write_text(json.dumps({'scope':'2 m grid check of four tower envelopes against neighbouring mapped solids at 20 m; shared lower podiums intentionally excluded. Not exhaustive CSG collision detection.','overlaps':out},indent=2))

# Independently verify that the clipped University House solid and the hotel
# teaching mass do not occupy the same 2 m grid samples at 20 m.
mm=allm['Hotel ICON'];uh=next(m for m in mm if m['name']=='ICON_UniversityHouse');hotel=next(m for m in mm if m['name']=='ICON_teaching_block')
vv=uh['v'];both=[]
for x in np.arange(vv[:,0].min()+1,vv[:,0].max(),2):
 for z in np.arange(vv[:,2].min()+1,vv[:,2].max(),2):
  a=heights(uh['tri'],x,z);b=heights(hotel['tri'],x,z)
  if len(a)>=2 and len(b)>=2 and a.min()+.02<20<a.max()-.02 and b.min()+.02<20<b.max()-.02:both.append([x,z])
report=json.loads((R/'docs/final-adjacent-qa.json').read_text());report['university_house_teaching_overlap_samples']=both
(R/'docs/final-adjacent-qa.json').write_text(json.dumps(report,indent=2)+'\n')
print('UH_TEACHING_OVERLAP_SAMPLES',len(both))
if both or out:raise SystemExit(1)
