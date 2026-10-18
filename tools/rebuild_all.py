"""Rebuild all named assets, including support checks, from any checkout."""
import pathlib,runpy,sys,json,traceback
ROOT=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'))
SCRIPTS=['build_lks','build_hicon','build_blockz','build_gsh','build_shaw','build_blockx','build_chan','build_taio','build_anita','build_chow','build_mong','build_ng','build_yip','build_seal','build_cma','build_chung','build_lui','build_stanley','build_choi','build_shirley','build_gh','build_fong','build_tang','build_leeshaukee','build_hoi','build_industrial','build_communal','build_library','build_jca','build_jcit']
if __name__=='__main__':
    selected=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else SCRIPTS
    failures=[]
    for name in selected:
        try:
            runpy.run_path(str(ROOT/'tools'/f'{name}.py'),run_name='__main__')
            if name=='build_jcit':
                import bpy
                bpy.ops.wm.read_factory_settings(use_empty=True)
                bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/models/jcit.glb'))
                bpy.context.preferences.filepaths.save_version=0
                bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/models/jcit.blend'))
            print('REBUILD_OK',name,flush=True)
        except Exception as e:traceback.print_exc();failures.append(name)
    if failures:raise RuntimeError('Failed builders: '+', '.join(failures))
    print('ALL_BUILDERS_OK',len(selected),flush=True)
