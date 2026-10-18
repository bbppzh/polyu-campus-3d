#!/usr/bin/env python3
"""Download low-resolution cube faces for the 360° preview.

For every landmark in data/campus.json that has a `tourPanoId`, fetch the six
512x512 faces of its level-2 cube map from PolyU's virtual tour and store them
under assets/pano/<panoId>/{r,l,u,d,f,b}.jpg.

Usage:  python3 tools/fetch_panoramas.py
"""
import json
import os
import ssl
import subprocess
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://www.polyu.edu.hk/saso/vtour/media"
FACES = ["r", "l", "u", "d", "f", "b"]


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 2000:
        return True
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    # The polyu.edu.hk chain is rejected by some Python CA bundles; curl with
    # the system store is the reliable path. Fall back to urllib otherwise.
    if subprocess.call(
        ["curl", "-fsSL", "-m", "60", "--retry", "3", "--retry-delay", "2", url, "-o", dest]
    ) == 0:
        return os.path.exists(dest) and os.path.getsize(dest) > 2000
    try:
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(url, context=ctx, timeout=60) as r, open(dest, "wb") as f:
            f.write(r.read())
        return os.path.getsize(dest) > 2000
    except Exception as exc:  # noqa: BLE001
        print("failed:", url, exc)
        return False


def main():
    with open(os.path.join(ROOT, "data", "campus.json"), encoding="utf-8") as f:
        data = json.load(f)
    todo = [
        (landmark["tourPanoId"], face)
        for landmark in data.get("landmarks", [])
        if landmark.get("tourPanoId")
        for face in FACES
    ]
    print(f"{len(todo)} faces to check")
    failed = 0
    for pano_id, face in todo:
        dest = os.path.join(ROOT, "assets", "pano", pano_id, face + ".jpg")
        url = f"{BASE}/{pano_id}_0/{face}/2/0_0.jpg"
        if not fetch(url, dest):
            failed += 1
    print("done,", failed, "failures")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
