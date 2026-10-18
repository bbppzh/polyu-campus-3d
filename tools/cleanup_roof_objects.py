#!/usr/bin/env python3
"""Compatibility entry point: rebuild roof-bearing models with triangle support QA.

The old bounding-box post-process accepted gaps up to 4 m and could discard
valid assemblies. Rebuild from source instead so every roof assembly is checked
against actual roof triangles by roof_support.finalize_scene.
Run Blender --background --python tools/cleanup_roof_objects.py.
"""
import pathlib,runpy,sys
ROOT=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'))
from rebuild_all import SCRIPTS
icons={'build_lks','build_hicon','build_blockz','build_jcit'}
for name in SCRIPTS:
    if name not in icons:
        runpy.run_path(str(ROOT/'tools'/f'{name}.py'),run_name='__main__')
print('ROOF_REBUILD_DONE',flush=True)
