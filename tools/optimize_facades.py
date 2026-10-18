"""Batch existing photo-referenced Blender assets without rebuilding geometry."""
import bpy,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'tools'))
from architecture import export
for slug in ['lks','hotel_icon','blockz']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/models'/f'{slug}.blend'))
    bpy.context.preferences.filepaths.save_version=0
    export(slug)
