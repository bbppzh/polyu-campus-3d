# Follow-up navigation/card fixes (2026-10-18)

Triggered by `campus-final/followup-review/不足與下一輪修改.md`.

## Mobile layout (390 × 844)

- Finder/search stays visible; previously both were `display:none`.
- Controls become a two-row grid; Labels / Orbit / Reset fit inside the viewport.
- Map button is hidden on mobile and the minimap remains hidden, so the button no longer claims a hidden feature.
- Measured after the fix:
  - finder/search: x=25, right=365 (390 px viewport)
  - Orbit: x=138, right=252
  - Reset: x=257, right=371
  - `#btnMap` computed display: `none`

## Label collision

- Uses each label's actual DOM rect (width + height) instead of a fixed 104×21
  centre-distance test.
- Avoids the open information panel; selected/hovered labels are still kept.
- Desktop QA at 1006×928: **6 visible labels, 0 overlapping pairs**.

## Search aliases

Added aliases including `JCIT`, `JCA`, `LKS`, `library`, `hotel`, `Z座`,
`X座`, `W座`, `GSH`, `Shaw`, `innovation tower`, `創新樓`, `李嘉誠`, `唯港薈`.
Verified in the browser: `JCIT` → Jockey Club Innovation Tower, `LKS` → Li Ka
Shing Tower.

## Info card

- Built form maps raw OSM `yes` / `university` / `college` / etc. to readable
  labels; Hotel ICON now shows **Hotel / teaching complex**, not `yes`.
- Height provenance is visible in the card body (`Model geometry ·
  record-height reference` or `Model estimate · not surveyed`), not only in a
  hover tooltip.
- Browser QA: Hotel ICON → form `Hotel / teaching complex`, basis `Model
  geometry · record-height reference`, height `114 m`.

## Entrance signage

- JCIT no longer uses the fixed 30.6 m radius placement; its sign now uses
  `nearestEdge()` against the actual footprint. This is a placement fix, not a
  full entrance/wall binding pass for every building.

## Mobile performance sample

- 390×844 iframe, DPR 2 → canvas 780×1688.
- 2-second requestAnimationFrame sample: **120.1 fps** (desktop browser, synthetic mobile viewport; not a real-phone GPU test).
- No JavaScript errors during load + sample.

## LKS material mapping

The final LKS GLB uses `LKS_terracotta` / `LKS_glazing` / `LKS_stone` /
`LKS_metal`; the app mapping was extended to these names so the brick shader,
glass, stone and metal are applied instead of raw Blender materials.

## Still open

- Cross-building bridges, entrance positions and platform levels are not
  individually surveyed.
- Facade depth on LKS/JCIT/Hotel/Z remains a low-poly approximation.
- No real-device mobile performance or long-run stability test.
