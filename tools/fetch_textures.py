#!/usr/bin/env python3
"""Download the CC0 PBR texture sets used by the facade shader.

Textures from Poly Haven (CC0): brick_wall_001 and large_sandstone_blocks.
Each set provides diffuse, OpenGL normal and roughness maps at 1k.

Usage:  python3 tools/fetch_textures.py
"""
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETS = {
    "brick": "brick_wall_001",
    "stone": "large_sandstone_blocks",
}
BASE = "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k"


def main():
    for folder, asset in SETS.items():
        out = os.path.join(ROOT, "assets", "textures", folder)
        os.makedirs(out, exist_ok=True)
        maps = {
            "diffuse": asset + "_diff_1k.jpg" if asset.startswith("large_sandstone") else asset + "_diffuse_1k.jpg",
            "normal": asset + "_nor_gl_1k.jpg",
            "rough": asset + "_rough_1k.jpg",
        }
        for name, filename in maps.items():
            dest = os.path.join(out, name + ".jpg")
            if os.path.exists(dest) and os.path.getsize(dest) > 1000:
                continue
            url = f"{BASE}/{asset}/{filename}"
            print("fetching", url)
            subprocess.run(["curl", "-fsSL", "-m", "120", url, "-o", dest], check=True)
            print("  ->", dest)
    print("done")


if __name__ == "__main__":
    main()
