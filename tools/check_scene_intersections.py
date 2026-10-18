#!/usr/bin/env python3
"""Check actual procedural footprints exported by check_scene_layout.mjs.
node tools/check_scene_layout.mjs /tmp/campus-details.json
python3 tools/check_scene_intersections.py /tmp/campus-details.json
Requires Shapely. No browser or renderer state is mocked.
"""
import json,pathlib,sys
from shapely.geometry import Polygon,MultiPoint,Point
from shapely.ops import unary_union
r=pathlib.Path(__file__).resolve().parent.parent
l=json.loads((r/'data/scene-layout.json').read_text());d=json.loads(pathlib.Path(sys.argv[1]).read_text())
def poly(b):return Polygon(b['footprint'],b.get('holes',[]))
models=unary_union([poly(b) for b in l['landmarkEnvelopes']]);context=[poly(b) for b in l['context']];errors=[];maxarea=0
for i,p in enumerate(context):
 a=p.intersection(models).area;maxarea=max(maxarea,a)
 if a>.0001:errors.append(['context_model',l['context'][i]['id'],a])
 for q in context[i+1:]:
  a=p.intersection(q).area;maxarea=max(maxarea,a)
  if a>.0001:errors.append(['context_context',l['context'][i]['id'],a])
for a in d['details']:
 p=MultiPoint(a['points']).convex_hull
 area=p.intersection(models).area
 if area>.0001:errors.append(['detail_model',a['id'],a['bucket'],round(area,6)])
 for i,b in enumerate(l['context']):
  if b['id']==a['id'] or b['height']<=a['bottom']+.001:continue
  area=p.intersection(context[i]).area
  if area>.0001:errors.append(['detail_context',a['id'],b['id'],a['bucket'],round(area,6)])
source=json.loads((r/'data/campus.json').read_text());solids=unary_union([models]+[Polygon(b['footprint']) for b in source['context'] if b['id'] not in [236028367,236028374,236028379]])
for i,t in enumerate(d['trees']):
 if Point(t['x'],t['z']).buffer(t['r']).intersection(solids).area>.0001:errors.append(['tree',i])
report={'context_pieces':len(context),'procedural_details':len(d['details']),'trees':len(d['trees']),'max_context_overlap_m2':maxarea,'errors':errors,'scope':'Exact planar polygon intersections: rendered context pieces against exported landmark projections, context pairs, actual procedural detail footprints against landmark projections/taller neighbours, every full tree crown against buildings. Vertical projection is conservative; it is not an as-built survey.'}
(r/'docs/scene-intersections-qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if errors:raise SystemExit(1)
