#!/usr/bin/env python3
"""Render the exported GLBs, never stale .blend scenes, for silhouette QA.
Blender -b --python tools/render_fourviews.py [-- lks jcit hotel_icon blockz]
"""
import bpy,math,pathlib,sys,json
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parent.parent;OUT=ROOT/'docs/fourview';OUT.mkdir(exist_ok=True)
slugs=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['lks','jcit','hotel_icon','blockz']
views={'front':(0,-1,.12),'back':(0,1,.12),'left':(-1,0,.12),'right':(1,0,.12),'iso':(1,-1,.60)}
metrics=[]
for slug in slugs:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/models'/f'{slug}.glb'));bpy.context.view_layer.update()
 if slug=='jcit':
  bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/models/jcit.blend'))
 sc=bpy.context.scene;pts=[o.matrix_world@Vector(c) for o in sc.objects if o.type=='MESH' for c in o.bound_box]
 lo=Vector(tuple(min(v[k] for v in pts) for k in range(3)));hi=Vector(tuple(max(v[k] for v in pts) for k in range(3)));center=(lo+hi)/2;dim=hi-lo
 sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=800;sc.render.resolution_y=700;sc.render.resolution_percentage=100
 sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(.17,.19,.21)
 metrics.append({'slug':slug,'bounds_min':list(lo),'bounds_max':list(hi),'dimensions':list(dim)})
 for view,d in views.items():
  cd=bpy.data.cameras.new('QC_CAMERA');cd.type='ORTHO';cd.ortho_scale=max(dim.x,dim.y,dim.z)*1.38
  cam=bpy.data.objects.new('QC_CAMERA',cd);sc.collection.objects.link(cam);cam.location=center+Vector(d).normalized()*max(dim.length*2,60);cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
  sc.render.image_settings.file_format='PNG';sc.render.filepath=str(OUT/f'{slug}-{view}.png');bpy.ops.render.render(write_still=True)
 print('RENDER_OK',slug,flush=True)
(OUT/'metrics.json').write_text(json.dumps(metrics,indent=2))
