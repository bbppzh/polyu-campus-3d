"""Three pedestrian-height views of the actual exported Hotel GLB.
Optional -- /absolute/baseline.glb adds before/after images with identical cameras.
"""
import bpy,pathlib,sys,json,math,hashlib
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parent.parent;OUT=ROOT/'docs/hotel-entrances';OUT.mkdir(exist_ok=True)
d=json.loads((ROOT/'data/campus.json').read_text());lm=next(l for l in d['landmarks'] if l['name']=='Hotel ICON');reg=json.loads((ROOT/'data/hotel-entrances.json').read_text());baseline=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else None
cameras=[]
for e in reg['entries']:
 p=Vector((e['wall_world_xz'][0]-lm['center'][0],-(e['wall_world_xz'][1]-lm['center'][1]),0));n=Vector((e['outward_world_xz'][0],-e['outward_world_xz'][1],0));u=Vector((e['tangent_world_xz'][0],-e['tangent_world_xz'][1],0))
 eye=p+n*18+u*5;eye.z=1.7;target=p+n*.5;target.z=2.0
 cameras.append({'id':e['id'],'eye_blender_xyz':list(eye),'target_blender_xyz':list(target),'eye_height_m':1.7,'ground_datum':'model GF zero'})
for kind,file in [('after',ROOT/'assets/models/hotel_icon.glb')]+([('before',pathlib.Path(baseline))] if baseline else []):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(file));sc=bpy.context.scene
 for o in list(sc.objects):
  if o.type=='MESH':
   # Scene assets remain identical to the export. A ground plane is added only
   # for a pedestrian-height inspection, not to mask floating source geometry.
   pass
 mat=bpy.data.materials.new('Review pavement');mat.diffuse_color=(.57,.59,.58,1)
 bpy.ops.mesh.primitive_plane_add(size=500,location=(0,0,-.015));bpy.context.object.name='Review_ground_only';bpy.context.object.data.materials.append(mat)
 sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.render.engine='BLENDER_WORKBENCH';sc.render.resolution_x=1000;sc.render.resolution_y=700;sc.render.resolution_percentage=100
 sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('Review sky');sc.world.color=(.66,.71,.74)
 for c in cameras:
  cd=bpy.data.cameras.new('Camera_'+c['id']);cd.type='PERSP';cd.lens=34;cd.clip_start=.05;cd.clip_end=800;cam=bpy.data.objects.new('Camera_'+c['id'],cd);sc.collection.objects.link(cam);cam.location=Vector(c['eye_blender_xyz']);cam.rotation_euler=(Vector(c['target_blender_xyz'])-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam
  sc.render.image_settings.file_format='PNG';sc.render.filepath=str(OUT/f'{c["id"]}-{kind}.png');bpy.ops.render.render(write_still=True);print('LOW_VIEW',c['id'],kind,flush=True)
(OUT/'cameras.json').write_text(json.dumps(cameras,indent=2)+'\n')

manifest={'after_glb_sha256':hashlib.sha256((ROOT/'assets/models/hotel_icon.glb').read_bytes()).hexdigest(),'registration_sha256':hashlib.sha256((ROOT/'data/hotel-entrances.json').read_bytes()).hexdigest(),'cameras':cameras,'images':[f'{e["id"]}-{kind}.png' for e in reg['entries'] for kind in (['after','before'] if baseline else ['after'])],'render_engine':'BLENDER_WORKBENCH','reference_scope':'Three entrance positions compared with registered G/F plan; before/after use identical cameras. Staff/school matching real-world low-angle photos are not available.'}
(OUT/'render-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
