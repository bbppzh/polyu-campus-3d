#!/usr/bin/env python3
"""Derive non-overlapping render context and tree exclusions from exported GLBs.
Requires numpy and shapely. Does not modify the OSM source records.
Run after rebuilding any landmark: python3 tools/build_scene_layout.py.
"""
from pathlib import Path
import ast, hashlib, json, struct
import numpy as np
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from shapely import make_valid, set_precision
ROOT=Path(__file__).resolve().parent.parent
# Reuse the GLB decoder only; importing the audit would rewrite its reports.
code=ast.parse((ROOT/'tools/audit_models.py').read_text())
ns={'np':np,'json':json,'struct':struct}
exec(compile(ast.Module(body=[n for n in code.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'glb_decoder','exec'),ns)
SLUGS=['lks','jcit','jca','gsh','shaw','blockx','blockz','chan','taio','anita','chow','mong','ng','yip','seal','cma','chung','lui','stanley','choi','shirley','gh','fong','tang','leeshaukee','hoi','industrial','communal','library','hotel_icon']
EXCLUDED={236028367,236028374,236028379} # represented inside the Hotel GLB
CLEARANCE=.35

def pieces(g):
    # Snap before serialization, removing sliver rings that would otherwise
    # become invalid when written as four-decimal JSON coordinates.
    g=set_precision(make_valid(g),.0001)
    if g.is_empty:return []
    if g.geom_type=='Polygon':return [g]
    return [p for part in getattr(g,'geoms',[]) for p in pieces(part)]

def encode(p):
    return {'footprint':[[round(x,4),round(z,4)] for x,z in list(p.exterior.coords)[:-1]],
            'holes':[[[round(x,4),round(z,4)] for x,z in list(r.coords)[:-1]] for r in p.interiors]}

def main():
    data=json.loads((ROOT/'data/campus.json').read_text());masks=[];hashes={}
    for lm,slug in zip(data['landmarks'],SLUGS):
        path=ROOT/'assets/models'/f'{slug}.glb';hashes[slug]=hashlib.sha256(path.read_bytes()).hexdigest()
        triangles=[]
        for mesh in ns['read_model'](path):
            for t in mesh['tri'][:,:,[0,2]]+np.array(lm['center']):
                p=Polygon(np.round(t,5))
                if p.area>1e-7:triangles.append(p)
        masks.append(unary_union(triangles).simplify(.002,preserve_topology=True))
    envelope=unary_union(masks).buffer(CLEARANCE,join_style=2)
    contexts=[];trimmed=[];loss=0
    claimed=Polygon()
    # OSM building/part records can overlap each other. Taller volumes own
    # their footprint; retain each lower building's exposed portion.
    ordered=sorted(data['context'],key=lambda b:(-b['height'],b['id']))
    for b in ordered:
        if b['id'] in EXCLUDED:continue
        original=make_valid(Polygon(b['footprint']))
        clean=original.difference(envelope).difference(claimed.buffer(.42,join_style=2))
        claimed=unary_union([claimed,clean])
        lost=original.area-clean.area
        if lost>.01:trimmed.append({'id':b['id'],'removed_overlap_m2':round(lost,3)})
        loss+=max(0,lost)
        for part in pieces(clean):
            if part.area<.05:continue
            pos=part.representative_point()
            contexts.append({**b,**encode(part),'clipped':lost>.01,'center':[round(pos.x,4),round(pos.y,4)]})
    # Full crown radius <=2.71 m. A 3 m setback keeps trunk AND crown clear.
    road_widths={'motorway':18,'trunk':16,'primary':13,'secondary':10,'tertiary':8,
                 'residential':7,'service':4.5,'pedestrian':6,'footway':2.6,
                 'path':2.4,'steps':2.4,'cycleway':2.4}
    road_masks=[]
    for road in data['roads']:
        pts=road.get('points') or road.get('path') or []
        if len(pts)>1:road_masks.append(LineString(pts).buffer(road_widths.get(road.get('class','').removesuffix('_link'),3)/2))
    city=[make_valid(Polygon(b['footprint'])) for b in data['context'] if b['id'] not in EXCLUDED]
    blocked=unary_union(masks+city+road_masks).buffer(3,join_style=2).simplify(.01,preserve_topology=True)
    result={'schema':1,'scope':'Rendering-only footprints clipped against actual landmark mesh projections; source OSM data unchanged. All heights use the existing estimates.',
            'model_sha256':hashes,'campus_sha256':hashlib.sha256((ROOT/'data/campus.json').read_bytes()).hexdigest(),
            'clearance_m':CLEARANCE,'context_seam_m':.42,'tree_clearance_m':3,'context':contexts,
            'landmarkEnvelopes':[{'name':lm['name'],**encode(part)} for lm,mask in zip(data['landmarks'],masks) for part in pieces(mask)],
            'treeObstacles':[encode(p) for p in pieces(blocked)],
            'trimmed_context':trimmed,'removed_overlap_m2':round(loss,3)}
    (ROOT/'data/scene-layout.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    print('Scene layout:',len(contexts),'context pieces;',len(trimmed),'trimmed source records;',round(loss,2),'m² projected duplication removed;',len(road_masks),'road exclusions')
if __name__=='__main__':main()
