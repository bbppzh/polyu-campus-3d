#!/usr/bin/env python3
"""Rebuild the PolyU campus-diorama datasets from the raw recon inputs.

Outputs
-------
data/campus.json   landmarks + context blocks + road centrelines + ground areas
data/tour.json     108 virtual-tour panorama labels -> {panoId, thumb, description}
assets/thumbs/*.jpg in-game thumbnails (only for landmarks that are also tour scenes)

Inputs (read-only)
------------------
../_recon/buildings.json   Overpass `way["building"]` dump (ways + geometry)
../_recon/roads.json       Overpass `way["highway"]/["railway"]` dump
../_recon/landuse.json     Overpass landuse/natural/leisure/amenity dump
/tmp/polyu/en.txt          PolyU virtual-tour locale (panorama labels + description)
tools/osm_extra.json       small OSM geometry snapshot for the two landmarks that are
                           missing from the building dump (Pao Yue-kong Library and
                           Hotel ICON are tagged amenity=library / tourism=hotel, not
                           building=*), see the "_note" field of that file
https://www.polyu.edu.hk/saso/vtour/media/<panoId>_t.jpg   thumbnails

Projection (metres, x=east, z=south, origin 22.3045 N 114.1795 E)
------------------------------------------------------------------
x = (lon - 114.1795) * 111320 * cos(22.3045 deg)
z = -(lat - 22.3045) * 110540

Height rule
-----------
tags.height (number, capped at 120 m)  else  building:levels * 3.2
else type default: university 35, concourse 28, retail 15, hotel 60,
hospital 40, apartments 40, everything else 20.

Footprints are outer rings, Douglas-Peucker simplified (tolerance 1 m, <= 40
points) with a ring-safe split so closed OSM rings never collapse; every
landmark footprint keeps >= 3 distinct points and > 20 m2.

Landmarks
---------
28 large named campus buildings plus Pao Yue-kong Library and Hotel ICON.  The
16 OSM `building=concourse` "Core A-U" ways are only ~13x13 m lift/stair cores
inside the podium, so they stay in the context layer instead of becoming
landmarks.  Landmarks carry the schema fields plus a small `tags` subset
(`tags.building` etc.) and a flat `building` value for display.

Usage
-----
python3 tools/extract_data.py               # full run (downloads thumbnails)
python3 tools/extract_data.py --no-download # rebuild JSON, reuse cached thumbs
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

# --------------------------------------------------------------------------- #
# paths / constants
# --------------------------------------------------------------------------- #

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RECON_DIR = Path(os.environ.get("POLYU_RECON_DIR", str(PROJECT_ROOT.parent / "_recon")))
TOUR_DIR = Path(os.environ.get("POLYU_TOUR_DIR", "/tmp/polyu"))

DATA_DIR = PROJECT_ROOT / "data"
THUMBS_DIR = PROJECT_ROOT / "assets" / "thumbs"
LANDMARK_OVERRIDES_PATH = DATA_DIR / "landmark-overrides.json"

ORIGIN_LAT = 22.3045
ORIGIN_LON = 114.1795
M_PER_DEG_LAT = 110540.0
M_PER_DEG_LON = 111320.0
COS_LAT = math.cos(math.radians(ORIGIN_LAT))

CONTEXT_RADIUS_M = 700.0
CONTEXT_MAX = 400
ROAD_RADIUS_M = 900.0
AREA_RADIUS_M = 700.0
AREA_MIN_M2 = 40.0
AREA_MAX_POINTS = 40
FOOTPRINT_TOL_M = 1.0
FOOTPRINT_MAX_POINTS = 40
HEIGHT_CAP_M = 120.0
THUMB_MAX_DOWNLOADS = 24
THUMB_MIN_BYTES = 2048
THUMB_BASE = "https://www.polyu.edu.hk/saso/vtour/media/"
USER_AGENT = "polyu-campus-3d/1.0 (campus visualisation prototype)"

TYPE_HEIGHT_DEFAULTS = {
    "university": 35.0,
    "concourse": 28.0,
    "retail": 15.0,
    "hotel": 60.0,
    "hospital": 40.0,
    "apartments": 40.0,
}
TYPE_HEIGHT_FALLBACK = 20.0

# Large named campus buildings used as diorama landmarks.  The 16 OSM
# building=concourse "Core A-U" ways are only ~13x13 m lift/stair cores inside
# the podium (verified against the footprints), so they are left to the context
# layer instead of being promoted to landmarks.
# (osm id, English name, Chinese name, diorama category)
NAMED_LANDMARKS = [
    (121554917, "Li Ka Shing Tower", "李嘉誠樓", "Landmark"),
    (232267287, "Jockey Club Innovation Tower", "賽馬會創新樓", "Landmark"),
    (184551728, "Jockey Club Auditorium", "賽馬會綜藝館", "Landmark"),
    (1492140378, "Global Student Hub", "黃民鄧潔華伉儷環球學生薈", "Landmark"),
    (232267283, "Shaw Sports Complex", "邵逸夫體育館", "Sports"),
    (569218714, "Block X", "X座", "Sports"),
    (193047642, "Block Z", "Z座", "Campus building"),
    (232267273, "Chan Sui Wai Building", "陳瑞槐樓", "Campus building"),
    (232267274, "Chan Tai Ho Building", "陳大河樓", "Campus building"),
    (223300947, "Anita Chan Lai Ling Building", "陳麗玲樓", "Campus building"),
    (223300949, "Chow Yei Ching Building", "周亦卿樓", "Campus building"),
    (223300950, "Mong Man Wai Building", "蒙民偉樓", "Campus building"),
    (223300951, "Ng Wing Hong Building", "伍永康樓", "Campus building"),
    (223300953, "Yip Kit Chuen Building", "葉傑全樓", "Campus building"),
    (232267271, "Seal of Love Foundation Building", "正愛慈善基金樓", "Campus building"),
    (232267272, "CMA Building", "香港中華廠商聯合會樓", "Campus building"),
    (232267275, "Chung Sze Yuen Building", "鍾士元樓", "Campus building"),
    (232267281, "Lui Che Woo Building", "呂志和樓", "Campus building"),
    (232267284, "Stanley Ho Building", "何鴻燊樓", "Campus building"),
    (223305768, "Choi Kai Yau Building", "蔡繼有樓", "Campus building"),
    (223305770, "Shirley Chan Building", "陳鮑雪瑩樓", "Campus building"),
    (232267279, "GH Block", "GH棟", "Campus building"),
    (232267277, "Fong Shu Chuen Hall", "方樹泉堂", "Campus building"),
    (232267285, "Tang Ping Yuan Building", "唐炳源樓", "Campus building"),
    (184551727, "Lee Shau Kee Building", "李兆基樓", "Campus building"),
    (575344542, "House of Innovation", "創新館", "Campus building"),
    (220428422, "Industrial Centre", "工業中心", "Campus building"),
    (223305769, "Communal Building", "文康大樓", "Campus building"),
]

# The tour locale only ships one tour-wide description; it is reused as the
# fallback blurb.  The two buildings that are absent from the OSM building dump
# carry a footprint-provenance note instead (requested by the 3D integrator).
LANDMARK_DESCRIPTIONS = {
    "Pao Yue-kong Library": (
        "Pao Yue-kong Library (Block L). Footprint from outer way 184551440 of OSM "
        "multipolygon relation 10345171 (about 77 x 80 m); the library is tagged "
        "amenity=library rather than building=*, so it is absent from the building dump."
    ),
    "Hotel ICON": (
        "Hotel ICON (唯港薈). Tower footprint from OSM way 186997755 (building:levels=34), "
        "inside the tourism=hotel site way 121554924; the site itself is not in the building dump."
    ),
}

# Pao Yue-kong Library (relation 10345171, alt_name "L座 Block L") and Hotel ICON
# are absent from buildings.json because the OSM ways have no building tag; their
# geometry is snapshotted in tools/osm_extra.json.
LIBRARY_RELATION_ID = 10345171
LIBRARY_WAY_ID = 184551440
HOTEL_SITE_ID = 121554924
HOTEL_TOWER_ID = 186997755

# Curated landmark -> tour panorama label mappings. Order = preference.  The tour
# uses "Block X" for the core buildings, "3/F Library"/"***Pao Yue-kong Library"
# variants for the library and several spellings of Hotel ICON, hence the list.
CURATED_TOUR_MATCHES = {
    "Li Ka Shing Tower": ["Li Ka Shing Tower"],
    "Pao Yue-kong Library": [
        "Pao Yue-kong Library",
        "***Pao Yue-kong Library",
        "***P/F, Pao Yue-kong Library",
    ],
    "Hotel ICON": ["Hotel Icon", "Hotel ICON", "XXHotel Icon"],
    "Jockey Club Innovation Tower": ["Innovation Gallery", "Inno Hub"],
    "Jockey Club Auditorium": ["Jockey Club Auditorium", "Jockey Club Auditorium 2"],
    "Block X": [
        "Block X Area",
        "Block X Sports Centre Entrance",
        "Block X Roof Garden",
    ],
    "Block Z": ["Block Z"],
    "Industrial Centre": ["Block W Industrial Centre", "Industrial Centre Air Lab"],
    "Communal Building": ["Communal Building"],
    "Shaw Sports Complex": ["Shaw Sports Complex"],
    "Global Student Hub": [
        "Wong Man and Tang Kit Wah Global Student Hub",
        "Global Student Hub",
    ],
    "Tang Ping Yuan Building": ["Tang Ping Yuan Square"],
    "Hung Hom Bay Campus": ["Hung Hom Bay Campus Faculty of Humanities"],
}

CJK_RE = re.compile(r"[\u3400-\u9fff]")

# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def norm_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


def norm_name(text: str) -> str:
    """Lowercase, ampersand -> and, strip punctuation, collapse whitespace."""
    text = text.replace("&", " and ")
    text = re.sub(r"[^0-9A-Za-z\u3400-\u9fff]+", " ", text)
    return norm_ws(text).lower()


def tokens(text: str):
    return norm_name(text).split()


def project(lat: float, lon: float):
    """WGS84 -> local diorama metres (x east, z south)."""
    return (
        (lon - ORIGIN_LON) * M_PER_DEG_LON * COS_LAT,
        -(lat - ORIGIN_LAT) * M_PER_DEG_LAT,
    )


def round_pt(pt):
    return [round(pt[0], 2), round(pt[1], 2)]


def ring_from_geometry(geometry):
    """Project [{lat,lon}, ...] to a closed-ring point list (no duplicate end)."""
    pts = [project(p["lat"], p["lon"]) for p in geometry]
    # drop consecutive duplicates, including the repeated closing vertex
    cleaned = []
    for pt in pts:
        if not cleaned or abs(pt[0] - cleaned[-1][0]) > 1e-9 or abs(pt[1] - cleaned[-1][1]) > 1e-9:
            cleaned.append(pt)
    if len(cleaned) > 1 and abs(cleaned[0][0] - cleaned[-1][0]) < 1e-9 and abs(cleaned[0][1] - cleaned[-1][1]) < 1e-9:
        cleaned.pop()
    return cleaned


def ring_area(pts) -> float:
    if len(pts) < 3:
        return 0.0
    s = 0.0
    for i in range(len(pts)):
        x1, z1 = pts[i]
        x2, z2 = pts[(i + 1) % len(pts)]
        s += x1 * z2 - x2 * z1
    return abs(s) * 0.5


def ring_centroid(pts):
    """Area-weighted centroid, falling back to the vertex mean for degenerate rings."""
    a = 0.0
    cx = 0.0
    cz = 0.0
    for i in range(len(pts)):
        x1, z1 = pts[i]
        x2, z2 = pts[(i + 1) % len(pts)]
        cross = x1 * z2 - x2 * z1
        a += cross
        cx += (x1 + x2) * cross
        cz += (z1 + z2) * cross
    if abs(a) < 1e-9:
        return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    a *= 0.5
    return (cx / (6.0 * a), cz / (6.0 * a))


def simplify_polyline(pts, tol):
    """Douglas-Peucker for an open polyline."""
    if len(pts) <= 2:
        return list(pts)
    # iterative DP to stay well under the recursion limit for long ways
    keep = [False] * len(pts)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        first, last = stack.pop()
        if last <= first + 1:
            continue
        x1, z1 = pts[first]
        x2, z2 = pts[last]
        dx, dz = x2 - x1, z2 - z1
        seg_len = math.hypot(dx, dz)
        best_i = -1
        best_d = -1.0
        for i in range(first + 1, last):
            px, pz = pts[i]
            if seg_len < 1e-9:
                d = math.hypot(px - x1, pz - z1)
            else:
                d = abs(dz * (px - x1) - dx * (pz - z1)) / seg_len
            if d > best_d:
                best_d = d
                best_i = i
        if best_d > tol and best_i > 0:
            keep[best_i] = True
            stack.append((first, best_i))
            stack.append((best_i, last))
    return [pt for pt, k in zip(pts, keep) if k]


def _farthest_index(pts, point):
    best_i = 0
    best_d = -1.0
    for i, (x, z) in enumerate(pts):
        d = (x - point[0]) ** 2 + (z - point[1]) ** 2
        if d > best_d:
            best_d = d
            best_i = i
    return best_i


def simplify_ring(pts, tol=FOOTPRINT_TOL_M, max_points=FOOTPRINT_MAX_POINTS):
    """Ring-safe Douglas-Peucker.

    A plain DP over a closed ring can collapse it to two coincident points, so the
    ring is split into two arcs at the vertex farthest from the centroid and the
    vertex farthest from that one; each arc is simplified as an open polyline.
    """
    ring = list(pts)
    if len(ring) <= 3:
        return ring
    if len(ring) <= max_points:
        # still apply the tolerance so tiny wiggles disappear, but never below 3
        simplified = _simplify_ring_once(ring, tol)
        return simplified if len(simplified) >= 3 else ring

    current_tol = tol
    simplified = _simplify_ring_once(ring, current_tol)
    while len(simplified) > max_points and current_tol < 32.0:
        current_tol *= 1.6
        simplified = _simplify_ring_once(ring, current_tol)
    if len(simplified) > max_points:
        # last resort: keep an even sample of the simplified ring
        step = len(simplified) / float(max_points)
        sampled = [simplified[int(i * step)] for i in range(max_points)]
        simplified = sampled
    if len(simplified) < 3:
        return ring
    return simplified


def _simplify_ring_once(ring, tol):
    if len(ring) <= 3:
        return list(ring)
    centroid = (
        sum(p[0] for p in ring) / len(ring),
        sum(p[1] for p in ring) / len(ring),
    )
    i0 = _farthest_index(ring, centroid)
    i1 = _farthest_index(ring, ring[i0])
    if i0 == i1:
        return list(ring)
    if i0 > i1:
        i0, i1 = i1, i0
    arc_a = ring[i0 : i1 + 1]
    arc_b = ring[i1:] + ring[: i0 + 1]
    out_a = simplify_polyline(arc_a, tol)
    out_b = simplify_polyline(arc_b, tol)
    merged = out_a[:-1] + out_b[:-1]
    # dedupe any accidental repeats
    deduped = []
    for pt in merged:
        if not deduped or abs(pt[0] - deduped[-1][0]) > 1e-9 or abs(pt[1] - deduped[-1][1]) > 1e-9:
            deduped.append(pt)
    if len(deduped) > 1 and abs(deduped[0][0] - deduped[-1][0]) < 1e-9 and abs(deduped[0][1] - deduped[-1][1]) < 1e-9:
        deduped.pop()
    return deduped


# --------------------------------------------------------------------------- #
# heights
# --------------------------------------------------------------------------- #


def _number(value):
    if value is None:
        return None
    m = re.search(r"[-+]?[0-9]+(?:[.,][0-9]+)?", str(value))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", "."))
    except ValueError:
        return None


def height_for(tags, height_type=None):
    """Spec height rule: tags.height, else levels*3.2, else type default; cap 120 m."""
    raw = _number(tags.get("height"))
    if raw is not None and raw > 0:
        return round(min(raw, HEIGHT_CAP_M), 2)
    levels = _number(tags.get("building:levels"))
    if levels is not None and levels > 0:
        return round(min(levels * 3.2, HEIGHT_CAP_M), 2)
    kind = height_type or tags.get("building") or ""
    return round(min(TYPE_HEIGHT_DEFAULTS.get(kind, TYPE_HEIGHT_FALLBACK), HEIGHT_CAP_M), 2)


def height_basis_for(tags):
    """Human-readable provenance for a landmark height."""
    raw = _number(tags.get("height"))
    if raw is not None and raw > 0:
        return "OSM tags.height; estimate, not a surveyed dimension."
    levels = _number(tags.get("building:levels"))
    if levels is not None and levels > 0:
        return "OSM building:levels × 3.2 m; estimate, not a surveyed dimension."
    return "Type-default model height; estimate, not a surveyed dimension."


def load_landmark_overrides():
    if not LANDMARK_OVERRIDES_PATH.exists():
        return {}
    with open(LANDMARK_OVERRIDES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- #
# tour locale parsing
# --------------------------------------------------------------------------- #


def parse_tour_locale(path: Path):
    """Return (labels, description).

    labels: ordered dict normalised-name -> [panoId, ...] (first pano is canonical)
    description: the '### Description' tour text, or ''
    """
    labels = {}
    description = ""
    section = None
    lines = path.read_text(encoding="utf-8").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^###\s+(.*)$", line)
        if m:
            section = m.group(1).strip()
            i += 1
            continue
        if re.match(r"^##\s+", line):
            section = None
            i += 1
            continue
        if section and "=" in line:
            key, value = line.split("=", 1)
            # locale files wrap long values with a trailing backslash
            while value.rstrip().endswith("\\") and i + 1 < len(lines):
                value = value.rstrip()[:-1]
                i += 1
                value += " " + lines[i]
            key = key.strip()
            value = norm_ws(value)
            if section == "Title" and key.startswith("panorama_") and key.endswith(".label"):
                pano_id = key[: -len(".label")]
                labels.setdefault(value, [])
                if pano_id not in labels[value]:
                    labels[value].append(pano_id)
            elif section == "Description" and key == "tour.description":
                description = value
        i += 1
    return labels, description


# --------------------------------------------------------------------------- #
# tour matching
# --------------------------------------------------------------------------- #


def fuzzy_score(name: str, label: str) -> float:
    n = norm_name(name)
    l = norm_name(label)
    if not n or not l:
        return 0.0
    if n == l:
        return 1.0
    if n in l or l in n:
        shorter = min(len(n), len(l))
        longer = max(len(n), len(l))
        return 0.6 + 0.2 * (shorter / longer)  # containment
    tn = [t for t in tokens(name)]
    tl = set(tokens(label))
    if not tn or not tl:
        return 0.0
    hits = [t for t in tn if t in tl]
    distinctive = [t for t in hits if len(t) >= 3]
    if not distinctive:
        return 0.0
    frac = len(hits) / float(len(tn))
    if frac >= 1.0:
        return 0.75
    if frac >= 0.6:
        return 0.6
    return 0.0


def find_label_key(labels, wanted):
    target = norm_name(wanted)
    for key in labels:
        if norm_name(key) == target:
            return key
    return None


def tour_candidates(landmark_name, labels):
    """Ordered [(label_key, score)] candidates for a landmark."""
    scores = {}
    for rank, wanted in enumerate(CURATED_TOUR_MATCHES.get(landmark_name, [])):
        key = find_label_key(labels, wanted)
        if key is not None:
            scores[key] = max(scores.get(key, 0.0), 1.0 - 0.01 * rank)
    for key in labels:
        s = fuzzy_score(landmark_name, key)
        if s >= 0.6:
            scores[key] = max(scores.get(key, 0.0), s)
    return sorted(scores.items(), key=lambda kv: (-kv[1], len(kv[0]), kv[0]))


# --------------------------------------------------------------------------- #
# thumbnails
# --------------------------------------------------------------------------- #


def is_jpeg(path: Path) -> bool:
    try:
        if path.stat().st_size < THUMB_MIN_BYTES:
            return False
        with path.open("rb") as fh:
            return fh.read(3) == b"\xff\xd8\xff"
    except OSError:
        return False


_ssl_note_shown = False


def _read_url(url, insecure=False):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    kwargs = {"timeout": 45}
    if insecure:
        # Some corporate/AV TLS proxies break Python's bundled CA bundle while the
        # system curl accepts the chain; fall back to an unverified context for the
        # public thumbnail images only (never for data files).
        kwargs["context"] = ssl._create_unverified_context()
    with urllib.request.urlopen(request, **kwargs) as response:
        return response.read()


def download_thumb(pano_id: str, dest: Path) -> bool:
    global _ssl_note_shown
    if is_jpeg(dest):
        return True
    url = THUMB_BASE + pano_id + "_t.jpg"
    last_error = None
    for insecure in (False, True):
        try:
            data = _read_url(url, insecure=insecure)
            if len(data) > THUMB_MIN_BYTES and data[:3] == b"\xff\xd8\xff":
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
                return True
            last_error = "response is not a JPEG of >2KB (%d bytes)" % len(data)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ssl.SSLError) as exc:
            last_error = str(exc)
            if not insecure and ("CERTIFICATE" in str(exc).upper() or isinstance(exc, ssl.SSLError)):
                if not _ssl_note_shown:
                    print("  note: TLS chain rejected by Python's CA bundle; retrying thumbnail "
                          "downloads without verification (public images only)", file=sys.stderr)
                    _ssl_note_shown = True
                continue
    print("    ! thumbnail failed %s (%s)" % (url, last_error), file=sys.stderr)
    return False


def slugify(name: str) -> str:
    slug = norm_name(name)
    slug = re.sub(r"\s+", "-", slug)
    return slug or "landmark"


# --------------------------------------------------------------------------- #
# builders
# --------------------------------------------------------------------------- #


def build_tour(labels, description):
    tour = {}
    for name in sorted(labels, key=lambda s: (norm_name(s), s)):
        pano_ids = labels[name]
        tour[name] = {
            "panoId": pano_ids[0],
            "thumb": None,
            "description": description,
        }
    return tour


def landmark_definitions(extra_elements):
    """Return the ordered landmark definitions (named buildings + the 2 extras)."""
    defs = []
    for osm_id, name, name_zh, category in NAMED_LANDMARKS:
        defs.append(
            {
                "id": osm_id,
                "name": name,
                "nameZh": name_zh,
                "category": category,
                "height_type": None,
            }
        )
    library_way = extra_elements.get(LIBRARY_WAY_ID, {})
    library_relation = extra_elements.get(LIBRARY_RELATION_ID, {})
    library_tags = dict(library_way.get("tags", {}))
    library_tags.update(library_relation.get("tags", {}))
    defs.append(
        {
            "id": LIBRARY_WAY_ID,
            "name": "Pao Yue-kong Library",
            "nameZh": "包玉剛圖書館",
            "category": "Library",
            "height_type": "university",
            "extra": "way",
            "tags_override": library_tags,
        }
    )
    hotel_site = extra_elements.get(HOTEL_SITE_ID, {})
    hotel_tags = dict(hotel_site.get("tags", {}))
    defs.append(
        {
            "id": HOTEL_TOWER_ID,
            "name": "Hotel ICON",
            "nameZh": "唯港薈",
            "category": "Hotel",
            "height_type": "hotel",
            "tags_override": hotel_tags,
        }
    )
    return defs


def element_tags(element):
    return element.get("tags", {}) if element else {}


LANDMARK_TAG_KEYS = (
    "name",
    "name:en",
    "name:zh",
    "building",
    "building:levels",
    "height",
    "tourism",
    "amenity",
    "library",
    "layer",
)


def landmark_tags(tags):
    """Small, display-oriented subset of OSM tags (the UI reads tags.building)."""
    return {key: tags[key] for key in LANDMARK_TAG_KEYS if key in tags}


def build_campus(buildings, extras, tour_labels, tour_description, landmarks_with_thumbs):
    """Assemble the campus.json dict."""
    extras_by_id = {}
    for element in extras.get("elements", []):
        extras_by_id[element["id"]] = element

    overrides = load_landmark_overrides()
    by_id = {}
    for element in buildings:
        by_id[element["id"]] = element

    definitions = landmark_definitions(extras_by_id)
    landmark_ids = {d["id"] for d in definitions}
    landmarks = []
    for definition in definitions:
        osm_id = definition["id"]
        element = by_id.get(osm_id) or extras_by_id.get(osm_id)
        if element is None:
            raise SystemExit("landmark OSM id %s not found in inputs" % osm_id)
        geometry = element.get("geometry")
        if not geometry:
            raise SystemExit("landmark OSM id %s has no geometry" % osm_id)
        tags = dict(element_tags(element))
        tags.update(definition.get("tags_override") or {})
        ring = simplify_ring(ring_from_geometry(geometry))
        area = ring_area(ring)
        if len(ring) < 3 or area < 20.0:
            raise SystemExit("landmark %s degenerate footprint (%d pts, %.1f m2)" % (osm_id, len(ring), area))
        center = ring_centroid(ring)
        thumb_info = landmarks_with_thumbs.get(definition["name"])
        description = LANDMARK_DESCRIPTIONS.get(definition["name"], tour_description)
        override = overrides.get(definition["name"], {})
        landmarks.append(
            {
                "id": osm_id,
                "name": definition["name"],
                "nameZh": definition["nameZh"],
                "building": tags.get("building", ""),
                "category": definition["category"],
                "height": override.get("height", height_for(tags, definition.get("height_type"))),
                "heightBasis": override.get("heightBasis") or height_basis_for(tags),
                "footprint": [round_pt(p) for p in ring],
                "center": round_pt(center),
                "tourPanoId": thumb_info["panoId"] if thumb_info else None,
                "thumb": thumb_info["thumb"] if thumb_info else None,
                "description": description,
                "tags": landmark_tags(tags),
            }
        )

    # ---- context: every other building within 700 m, nearest 400 -------------
    context = []
    for element in buildings:
        if element["id"] in landmark_ids:
            continue
        geometry = element.get("geometry")
        if not geometry:
            continue
        ring = simplify_ring(ring_from_geometry(geometry))
        if len(ring) < 3 or ring_area(ring) < 2.0:
            continue
        center = ring_centroid(ring)
        distance = math.hypot(center[0], center[1])
        if distance > CONTEXT_RADIUS_M:
            continue
        context.append(
            (
                distance,
                {
                    "id": element["id"],
                    "height": height_for(element_tags(element)),
                    "footprint": [round_pt(p) for p in ring],
                },
            )
        )
    context.sort(key=lambda item: item[0])
    context = [block for _, block in context[:CONTEXT_MAX]]

    # ---- roads --------------------------------------------------------------
    roads = []
    roads_path = RECON_DIR / "roads.json"
    if roads_path.exists():
        for element in load_json(roads_path).get("elements", []):
            tags = element_tags(element)
            road_class = tags.get("highway")
            if not road_class:
                continue  # railway-only ways are not roads
            geometry = element.get("geometry")
            if not geometry or len(geometry) < 2:
                continue
            points = [project(p["lat"], p["lon"]) for p in geometry]
            if math.hypot(points[0][0], points[0][1]) > ROAD_RADIUS_M and math.hypot(
                sum(p[0] for p in points) / len(points),
                sum(p[1] for p in points) / len(points),
            ) > ROAD_RADIUS_M:
                continue
            points = simplify_polyline(points, 0.4)
            roads.append(
                {
                    "class": road_class,
                    "points": [round_pt(p) for p in points],
                }
            )

    # ---- ground areas -------------------------------------------------------
    areas = []
    landuse_path = RECON_DIR / "landuse.json"
    if landuse_path.exists():
        for element in load_json(landuse_path).get("elements", []):
            tags = element_tags(element)
            kind = area_kind(tags)
            if kind is None:
                continue
            geometry = element.get("geometry")
            if not geometry or len(geometry) < 4:
                continue
            ring = ring_from_geometry(geometry)
            if len(ring) < 3:
                continue
            area = ring_area(ring)
            if area < AREA_MIN_M2:
                continue
            center = ring_centroid(ring)
            if math.hypot(center[0], center[1]) > AREA_RADIUS_M:
                continue
            simplified = simplify_ring(ring, FOOTPRINT_TOL_M, AREA_MAX_POINTS)
            areas.append({"kind": kind, "polygon": [round_pt(p) for p in simplified]})
        areas.sort(key=lambda item: item["kind"])

    return {
        "origin": {"lat": ORIGIN_LAT, "lon": ORIGIN_LON},
        "landmarks": landmarks,
        "context": context,
        "roads": roads,
        "areas": areas,
    }


def area_kind(tags):
    """Map landuse/natural/leisure tags to grass|water|wood|pavement|other."""
    landuse = tags.get("landuse")
    natural = tags.get("natural")
    leisure = tags.get("leisure")
    if not any([landuse, natural, leisure]):
        return None
    if natural == "water" or leisure == "swimming_pool" or landuse in ("reservoir", "basin"):
        return "water"
    if natural in ("wood", "scrub", "forest") or landuse == "forest":
        return "wood"
    if (
        landuse in ("grass", "meadow", "recreation_ground", "village_green", "greenery")
        or natural in ("grassland", "heath")
        or leisure in ("park", "garden", "pitch", "playground", "track", "stadium", "golf_course")
    ):
        return "grass"
    if landuse == "highway" or tags.get("highway") in ("pedestrian", "footway", "square", "service"):
        return "pavement"
    if natural in ("coastline", "cliff", "ridge", "tree_row", "bare_rock"):
        return None
    return "other"


# --------------------------------------------------------------------------- #
# validation / summary
# --------------------------------------------------------------------------- #


def validate(campus, tour, allow_missing_thumbs):
    problems = []
    landmark_footprints = 0
    for landmark in campus["landmarks"]:
        footprint = landmark["footprint"]
        distinct = {(p[0], p[1]) for p in footprint}
        if len(distinct) < 3:
            problems.append("landmark %s has <3 distinct footprint points" % landmark["id"])
        if ring_area(footprint) < 20.0:
            problems.append("landmark %s footprint area < 20 m2" % landmark["id"])
        landmark_footprints += 1
        if not allow_missing_thumbs and landmark["thumb"]:
            path = PROJECT_ROOT / landmark["thumb"]
            if not is_jpeg(path):
                problems.append("landmark %s thumb missing/invalid: %s" % (landmark["id"], landmark["thumb"]))
    if len(tour) != 108:
        problems.append("tour.json has %d entries, expected 108" % len(tour))
    size = (DATA_DIR / "campus.json").stat().st_size
    if size >= 3 * 1024 * 1024:
        problems.append("campus.json is %.2f MB (limit 3 MB)" % (size / 1048576.0))
    if problems:
        for problem in problems:
            print("  FAIL " + problem, file=sys.stderr)
        raise SystemExit(1)
    return size


def summary(campus, tour, campus_size, downloads):
    print("origin               %.4f N, %.4f E" % (campus["origin"]["lat"], campus["origin"]["lon"]))
    category_counts = {}
    for landmark in campus["landmarks"]:
        category_counts[landmark["category"]] = category_counts.get(landmark["category"], 0) + 1
    print("landmarks            %d (%s)" % (
        len(campus["landmarks"]),
        ", ".join("%s:%d" % (k, category_counts[k]) for k in sorted(category_counts)),
    ))
    print("context buildings    %d" % len(campus["context"]))
    print("roads                %d" % len(campus["roads"]))
    print("areas                %d (%s)" % (
        len(campus["areas"]),
        ", ".join(
            "%s:%d" % (kind, sum(1 for a in campus["areas"] if a["kind"] == kind))
            for kind in sorted({a["kind"] for a in campus["areas"]})
        )
        or "none",
    ))
    print("tour panoramas       %d" % len(tour))
    with_thumb = sum(1 for l in campus["landmarks"] if l["thumb"])
    print("landmark thumbs      %d (%d newly downloaded)" % (with_thumb, downloads))
    print("campus.json          %.1f KB" % (campus_size / 1024.0))
    print("tour.json            %.1f KB" % ((DATA_DIR / "tour.json").stat().st_size / 1024.0))


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-download", action="store_true", help="do not fetch thumbnails; reuse cached files")
    args = parser.parse_args(argv)

    buildings_path = RECON_DIR / "buildings.json"
    if not buildings_path.exists():
        raise SystemExit("missing input: %s" % buildings_path)
    tour_path = TOUR_DIR / "en.txt"
    if not tour_path.exists():
        raise SystemExit("missing input: %s" % tour_path)
    extra_path = PROJECT_ROOT / "tools" / "osm_extra.json"
    if not extra_path.exists():
        raise SystemExit("missing input: %s" % extra_path)

    print("reading %s" % buildings_path)
    buildings = [e for e in load_json(buildings_path).get("elements", []) if e.get("type") == "way"]
    extras = load_json(extra_path)
    print("reading %s" % tour_path)
    labels, tour_description = parse_tour_locale(tour_path)
    if len(labels) != 108:
        print("  note: parsed %d unique tour labels (expected 108)" % len(labels), file=sys.stderr)

    # ---- match landmarks to tour panoramas and download thumbnails ----------
    definitions = landmark_definitions({e["id"]: e for e in extras.get("elements", [])})
    landmark_names = [d["name"] for d in definitions]
    taken_labels = set()
    label_thumb = {}
    landmarks_with_thumbs = {}
    downloads = 0
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
    print("matching tour panoramas")
    for name in landmark_names:
        candidates = tour_candidates(name, labels)
        if downloads >= THUMB_MAX_DOWNLOADS:
            break
        slug = slugify(name)
        dest = THUMBS_DIR / (slug + ".jpg")
        cached = is_jpeg(dest)
        got = False
        for label_key, _score in candidates:
            if label_key in taken_labels:
                continue
            for pano_id in labels[label_key]:
                if args.no_download:
                    if is_jpeg(dest):
                        got = True
                    else:
                        continue
                elif download_thumb(pano_id, dest):
                    if not cached:
                        downloads += 1
                    got = True
                    break
            if got:
                taken_labels.add(label_key)
                label_thumb[label_key] = (pano_id, "assets/thumbs/" + slug + ".jpg")
                landmarks_with_thumbs[name] = {
                    "panoId": pano_id,
                    "thumb": "assets/thumbs/" + slug + ".jpg",
                }
                print("  %-34s -> %-52s %s" % (name, label_key, pano_id))
                break
        if not got:
            if candidates:
                print("  %-34s -> no thumbnail (candidates: %s)" % (
                    name,
                    ", ".join(c[0] for c in candidates[:2]),
                ))
            continue

    # ---- write tour.json ----------------------------------------------------
    tour = build_tour(labels, tour_description)
    for label_key, (pano_id, thumb_path) in label_thumb.items():
        if label_key in tour:
            tour[label_key]["panoId"] = pano_id
            tour[label_key]["thumb"] = thumb_path
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with (DATA_DIR / "tour.json").open("w", encoding="utf-8") as fh:
        json.dump(tour, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write("\n")

    # ---- write campus.json --------------------------------------------------
    print("building campus.json")
    campus = build_campus(buildings, extras, labels, tour_description, landmarks_with_thumbs)
    with (DATA_DIR / "campus.json").open("w", encoding="utf-8") as fh:
        json.dump(campus, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write("\n")

    # ---- validate -----------------------------------------------------------
    campus_size = validate(campus, tour, allow_missing_thumbs=args.no_download)
    if args.no_download:
        # thumbnails may be absent in a cold checkout; report them but do not fail
        for landmark in campus["landmarks"]:
            if landmark["thumb"] and not is_jpeg(PROJECT_ROOT / landmark["thumb"]):
                print("  note: cached thumb missing for %s" % landmark["name"], file=sys.stderr)
    summary(campus, tour, campus_size, downloads)
    return 0


if __name__ == "__main__":
    sys.exit(main())
