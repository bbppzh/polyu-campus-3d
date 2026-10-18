#!/usr/bin/env python3
"""Register architect G/F image pixels to OSM-derived campus metre coordinates.
Digitized controls are not surveyed points; fit residual is not absolute accuracy.
"""
import pathlib,json,math,hashlib
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/hotel-entrances';OUT.mkdir(exist_ok=True)
d=json.loads((ROOT/'data/campus.json').read_text());lm=next(l for l in d['landmarks'] if l['name']=='Hotel ICON')
ctx={b['id']:b for b in d['context']};uh=ctx[236028367]['footprint'];pod=ctx[236028379]['footprint']
controls=[('staff_nw',[94,97],uh[0]),('staff_ne',[150,97],uh[1]),('staff_sw',[94,580],uh[5]),('staff_se',[150,580],uh[4]),('podium_C',[495,221],pod[5]),('podium_X',[495,624],pod[0])]
P=np.array([r[1] for r in controls]);W=np.array([r[2] for r in controls]);A=np.linalg.lstsq(np.c_[P,np.ones(len(P))],W,rcond=None)[0]
def world(p):return np.r_[p,1]@A
def pixel(w):return (np.array(w)-A[2])@np.linalg.inv(A[:2])
def metrics(rows):
 out=[]
 for name,p,w in rows:
  predicted=world(p);out.append({'id':name,'pixel':p,'reference_world_xz':w,'predicted_world_xz':predicted.tolist(),'residual_m':float(np.linalg.norm(predicted-w))})
 return out
fits=metrics(controls);checks=metrics([('inner_north',[173,226],pod[4]),('courtyard_corner',[173,496],pod[3]),('setback_corner',[307,496],pod[2])])
def inside(poly,x,z):
 ok=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:ok=not ok
 return ok
entries=[]
for key,px,host,width in [('hotel',[234,502],236028379,5.0),('school',[390,226],236028379,3.8),('staff',[94,391],236028367,2.4)]:
 target=world(px);poly=ctx[host]['footprint'];candidates=[]
 for i,(a,b) in enumerate(zip(poly,poly[1:]+poly[:1])):
  a=np.array(a);b=np.array(b);edge=b-a;L=np.linalg.norm(edge)
  if L<width+2.5:continue
  t=float(np.dot(target-a,edge)/L**2);t=np.clip(t,(width+2.4)/2/L,1-(width+2.4)/2/L);point=a+t*edge;u=edge/L;n=np.array([u[1],-u[0]])
  if inside(poly,*(point+n*.2)):n=-n
  candidates.append((np.linalg.norm(point-target),i,point,u,n))
 distance,index,point,u,n=min(candidates,key=lambda r:r[0]);lat=d['origin']['lat']-point[1]/110540;lon=d['origin']['lon']+point[0]/(111320*math.cos(math.radians(d['origin']['lat'])))
 entries.append({'id':key,'image_pixel':px,'registered_world_xz':target.tolist(),'host_context_id':host,'wall_edge_index':index,'wall_world_xz':point.tolist(),'tangent_world_xz':u.tolist(),'outward_world_xz':n.tolist(),'snap_distance_m':float(distance),'wgs84_lon_lat':[lon,lat],'door_width_m':width,'door_height_m':3.2,'canopy_width_m':width+2.2,'canopy_depth_m':2.2,'threshold_model_y_m':0.02,'dimensions_basis':'visual simplification, not measured; GF datum is model zero'})
report={'image':'docs/reference/hotel-ground-plan.jpg','image_sha256':hashlib.sha256((ROOT/'docs/reference/hotel-ground-plan.jpg').read_bytes()).hexdigest(),'image_size_px':[600,675],'source':'https://www.rocco.hk/cms/media/1684_dia_0238.jpg','reference_system':'OSM-derived campus x/east,z/south in metres, using campus.json origin; WGS84 conversion matches extract_data.py','pixel_to_world_affine_3x2':A.tolist(),'control_points':fits,'independent_check_points':checks,'fit_rmse_m':float(np.sqrt(np.mean([r['residual_m']**2 for r in fits]))),'check_rmse_m':float(np.sqrt(np.mean([r['residual_m']**2 for r in checks]))),'entries':entries,'limitations':['Controls manually digitized from 600x675 architect image and matched to existing OSM footprints, not site measurements.','Low control residual does not establish geographic or as-built accuracy.','Door sizes, canopy details and GF vertical datum remain model estimates; 2026 site changes not confirmed.']}
(ROOT/'data/hotel-entrances.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1080" viewBox="0 0 600 720"><rect width="600" height="720" fill="#fff"/><image href="../reference/hotel-ground-plan.jpg" width="600" height="675"/>']
colors={236028367:'#2854a3',236028379:'#af7340'}
for cid,color in colors.items():
 pts=' '.join(','.join(f'{v:.2f}' for v in pixel(w)) for w in ctx[cid]['footprint']);svg.append(f'<polygon points="{pts}" fill="none" stroke="{color}" stroke-width="1.4" stroke-dasharray="5 3"/>')
for r in fits+checks:
 x,y=r['pixel'];col='#22754a' if r in fits else '#be7429';svg.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{col}"/><text x="{x+5}" y="{y-5}" font-family="Arial" font-size="9" fill="{col}">{r["id"]}</text>')
for e in entries:
 x,y=e['image_pixel'];sx,sy=pixel(e['wall_world_xz']);svg.append(f'<line x1="{x}" y1="{y}" x2="{sx}" y2="{sy}" stroke="#b1203c" stroke-width="2"/><circle cx="{sx}" cy="{sy}" r="5" fill="none" stroke="#b1203c" stroke-width="2"/><text x="{sx+8}" y="{sy+4}" fill="#b1203c" font-family="Arial" font-weight="bold" font-size="12">{e["id"]}</text>')
svg.append(f'<text x="16" y="690" font-family="Arial" font-size="11">Green: 6 fitted controls | Orange: 3 holdout checks | Red: mapped doors</text><text x="16" y="708" font-family="Arial" font-size="11">Fit RMSE {report["fit_rmse_m"]:.2f} m; holdout RMSE {report["check_rmse_m"]:.2f} m. Not a survey.</text></svg>')
(OUT/'registration.svg').write_text(''.join(svg))
print('REGISTRATION',report['fit_rmse_m'],report['check_rmse_m']);print('ENTRY_SNAPS',[(e['id'],round(e['snap_distance_m'],3),e['wall_edge_index']) for e in entries])
