# Context intrusion candidates — manual classification

Source: `geometry-audit-v2.json` (2026-10-18). The audit found 16 context
footprints that intersect a custom GLB. Intersection is not automatically an
error: many campus buildings share podiums, cores and connected wings.

## Decision

| Landmark | Context ID / name | Height | Decision | Reason |
| --- | --- | ---: | --- | --- |
| JCIT | 1294954759 (unnamed) | 9.0 m | keep | Low podium beneath/around the tower; layer-1 footprint. |
| Global Student Hub | 121554933 Core T | 28.8 m | keep | Connected vertical circulation core. |
| Mong Man Wai | 232874902 Block N | 20.0 m | keep | OSM note says “buildings actually overlap”; physically connected. |
| Ng Wing Hong | 121554936 Core S | 28.8 m | keep | Connected core. |
| Seal of Love | 121554925 Core B | 25.6 m | keep | Connected core. |
| Chung Sze Yuen | 1447164688 (unnamed) | 20.0 m | keep | Small adjacency; only 4 fully-inside triangles. |
| Stanley Ho | 121554927 Core J | 25.6 m | keep | Connected core. |
| Shirley Chan | 232874902 Block N | 20.0 m | keep | Same physically overlapping Block N. |
| GH Block | 121554942 Core H | 28.8 m | keep | Connected core. |
| GH Block | 232267278 GH Podium Annexe | 20.0 m | keep | Named connected annexe. |
| Tang Ping Yuan | 121554947 Core F | 25.6 m | keep | Connected core. |
| Tang Ping Yuan | 121554938 Core C | 25.6 m | keep | Connected core. |
| Lee Shau Kee | 223300952 Realink Building | 22.4 m | keep | Separate adjacent building (Block U); not part of the LSKB massing. |
| Hotel ICON | 236028367 University House | 38.4 m | **remove** | Its footprint/volume is absorbed by the Hotel ICON composite massing; no separate mass is rendered until surveyed boundaries are available. |
| Hotel ICON | 236028379 (unnamed) | 12.8 m | **remove** | 4-storey footprint occupies the same hotel podium volume as the custom Hotel GLB. |
| Hotel ICON | 236028374 (unnamed) | 48.0 m | **remove** | 15-storey footprint is the OSM hotel tower volume duplicated by the custom GLB. |

The three removals are applied in `src/buildings.js` (`excludedContextIds`), not by
deleting the source OSM records. University House is retained; its intersection
with the custom hotel massing still needs a dedicated geometry pass.

## v3 follow-up (2026-10-18)

- Excluded **236028367 University House** as well: the custom Hotel ICON composite
  mass already occupies the overlapping volume, so rendering both produced 373
  fully-inside GLB triangles. A separate University House mass is deferred until
  surveyed boundaries are available.
- Context shopfronts/awnings now follow one **actual footprint edge** with the
  correct outward normal and rotation; they no longer use an axis-aligned bbox side.
- Height overrides are reproducible: `data/landmark-overrides.json` is merged by
  `tools/extract_data.py`, and every landmark gets a `heightBasis` field.
- Remaining kept candidates are connected podiums/cores/wings; see the table.

## Other follow-ups from the v2 review

- **Coastline**: moved from `z=420` to `z=620` in `src/environment.js`, so Hotel
  ICON (max z ≈429.5) and every context footprint (max z ≈595.8) stay on land.
- **Innovation Centre bars**: edge bars now use `atan2(dy, dx)` in Blender local
  coordinates; the `atan2(-dy, dx)` error was corrected in `build_hoi.py` and
  the same pattern fixed in `build_fong.py`, `build_tang.py`, `build_shirley.py`.
- **Height provenance**: every landmark now has a `heightBasis` string shown as
  the data-card tooltip; the card says “model” rather than presenting the value
  as surveyed.
