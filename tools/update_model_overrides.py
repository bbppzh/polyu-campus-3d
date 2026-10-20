#!/usr/bin/env python3
"""Derive UI/camera height overrides from the actual revised exported GLBs.
Original OSM footprints/heights remain available unchanged in campus.json.
"""
import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parent.parent
rows=json.loads((ROOT/'docs/models/manifest.json').read_text())['models']
selected={'library','leeshaukee','communal','blockx'}
models=[]
for row in rows:
 if row['slug'] not in selected:continue
 assert row['model_sha256']==hashlib.sha256((ROOT/row['model']).read_bytes()).hexdigest()
 models.append({'name':row['name'],'slug':row['slug'],'height':round(row['bounds_max'][2],2),
                'heightSource':'Visual estimate from a photo-referenced model; not surveyed',
                'model_sha256':row['model_sha256'],'bakedFacade':True})
(ROOT/'data/model-overrides.json').write_text(json.dumps({'scope':'UI and camera bounds from revised GLBs; source OSM data is not modified. All four heights remain estimates.','models':models},ensure_ascii=False,indent=2)+'\n')
print('Updated four rendered model height overrides')
