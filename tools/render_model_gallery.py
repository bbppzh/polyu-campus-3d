#!/usr/bin/env python3
"""Render every README model preview from the current exported GLB, never .blend.
Blender --background --python tools/render_model_gallery.py
"""
import bpy, pathlib, json, hashlib,sys
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parent.parent
OUT=ROOT/'docs/models';OUT.mkdir(exist_ok=True)
DATA=json.loads((ROOT/'data/campus.json').read_text())
SLUGS=['lks','jcit','jca','gsh','shaw','blockx','blockz','chan','taio','anita','chow','mong','ng','yip','seal','cma','chung','lui','stanley','choi','shirley','gh','fong','tang','leeshaukee','hoi','industrial','communal','library','hotel_icon']
selected=set(sys.argv[sys.argv.index('--')+1:]) if '--' in sys.argv else set(SLUGS)
pbr='--pbr' in sys.argv
review_views=json.loads((ROOT/'data/review-views.json').read_text()) if (ROOT/'data/review-views.json').exists() else {}
manifest=[]
for lm,slug in zip(DATA['landmarks'],SLUGS):
    if slug not in selected:continue
    path=ROOT/'assets/models'/f'{slug}.glb'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path));bpy.context.view_layer.update()
    sc=bpy.context.scene
    pts=[o.matrix_world@v.co for o in sc.objects if o.type=='MESH' for v in o.data.vertices]
    lo=Vector(tuple(min(v[k] for v in pts) for k in range(3)));hi=Vector(tuple(max(v[k] for v in pts) for k in range(3)))
    target=(lo+hi)/2;dim=hi-lo
    sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=900;sc.render.resolution_y=800;sc.render.resolution_percentage=100
    sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True
    sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.background_type='WORLD'
    sc.world=bpy.data.worlds.new('ModelPreviewWorld');sc.world.color=(.17,.19,.21)
    if pbr:
        sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=24;sc.cycles.use_denoising=True
        sc.render.threads_mode='FIXED';sc.render.threads=8
        sc.world.use_nodes=True;bg=sc.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.66,.69,.72,1);bg.inputs['Strength'].default_value=.65
        for name,pos,power,size in [('KEY',(-65,-80,120),35000,70),('FILL',(70,40,80),22000,65)]:
            ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.shape='DISK';ld.size=size
            light=bpy.data.objects.new(name,ld);sc.collection.objects.link(light);light.location=target+Vector(pos);light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('PREVIEW_CAMERA');cd.type='ORTHO'
    cam=bpy.data.objects.new('PREVIEW_CAMERA',cd);sc.collection.objects.link(cam)
    front=Vector((1,-1,0))
    entrances=[o for o in sc.objects if o.type=='MESH' and 'canopy' in o.name.lower() and 'terrace' not in o.name.lower()]
    identity=[o for o in sc.objects if o.type=='MESH' and o.name.endswith('_identity')]
    if identity:entrances=identity
    if entrances:
        ob=next((o for o in entrances if 'entrance_hotel' in o.name),entrances[0])
        corners=[ob.matrix_world@Vector(c) for c in ob.bound_box]
        front=sum(corners,Vector())/len(corners)-target;front.z=0
        if front.length<.01:front=Vector((1,-1,0))
    if slug in review_views:front=Vector((*review_views[slug]['front'],0))
    front.normalize();side=Vector((-front.y,front.x,0))
    direction=front+side*.6+Vector((0,0,review_views.get(slug,{}).get('elevation',.72)))
    cam.location=target+direction.normalized()*max(dim.length*2,60)
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
    # Fit the real geometry in camera coordinates, avoiding tiny models or clipping.
    inv=cam.rotation_euler.to_matrix().transposed();q=[inv@(p-target) for p in pts]
    width=max(p.x for p in q)-min(p.x for p in q);height=max(p.y for p in q)-min(p.y for p in q)
    shift=cam.rotation_euler.to_matrix()@Vector(((min(p.x for p in q)+max(p.x for p in q))/2,(min(p.y for p in q)+max(p.y for p in q))/2,0))
    cam.location+=shift
    cd.ortho_scale=max(width,height*(900/800))*1.17
    if pbr:
        bpy.ops.mesh.primitive_plane_add(size=max(dim)*20,location=(target.x,target.y,lo.z-.04))
        ground=bpy.context.object;ground.name='STUDIO_GROUND_NOT_IN_MODEL'
        gm=bpy.data.materials.new('STUDIO_GROUND');gm.diffuse_color=(.69,.69,.66,1);gm.use_nodes=True
        gm.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.69,.69,.66,1);gm.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.9;ground.data.materials.append(gm)
    sc.render.image_settings.file_format='PNG';sc.render.filepath=str(OUT/f'{slug}.png')
    bpy.ops.render.render(write_still=True)
    manifest.append({'name':lm['name'],'nameZh':lm.get('nameZh',''),'slug':slug,'model':f'assets/models/{slug}.glb','preview':f'docs/models/{slug}.png','model_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'preview_sha256':hashlib.sha256((OUT/f'{slug}.png').read_bytes()).hexdigest(),'bounds_min':list(lo),'bounds_max':list(hi),'render_engine':sc.render.engine})
    print('GALLERY_OK',slug,flush=True)
prior=json.loads((OUT/'manifest.json').read_text())['models'] if (OUT/'manifest.json').exists() else []
by_slug={m['slug']:m for m in prior};by_slug.update({m['slug']:m for m in manifest})
manifest=[by_slug[slug] for slug in SLUGS if slug in by_slug]
(OUT/'manifest.json').write_text(json.dumps({'source':'Rendered from the current exported GLBs; no historical Blender scene or image reused.','models':manifest},ensure_ascii=False,indent=2)+'\n')
