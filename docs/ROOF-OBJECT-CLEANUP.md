# Roof-object containment pass (2026-10-18)

Triggered by the all-buildings review. The goal was not to force every object
into a bounding box, but to remove decoration that has no supporting slab or is
buried inside a solid mass/parapet.

## Structural repairs

- **Seal of Love / Chung Sze Yuen**: the previous parapet was a solid extrusion
  filling the whole roof plan, which buried the planters. It is now a perimeter
  wall built edge-by-edge; the roof remains open and planters can sit on it.
- **Global Student Hub**: planter boxes reduced/repositioned inside the roof;
  railing posts moved to the actual roof inset instead of a fixed ±10 m.
- **Block X**: basketball court reduced from 30×18 m to 24×12 m and re-centred;
  line markings, fences and floodlights use the new court dimensions. Court
  vertices outside the footprint: **0** (previously 2 corners).
- **Block Z**: see [BLOCKZ-PLATFORM-FIX.md](BLOCKZ-PLATFORM-FIX.md).

## Post-process cleanup

`tools/cleanup_roof_objects.py` was run on the 15 flagged `.blend` files. It
tests each planter/bed/lawn/roof-plant/AC/vent/tree/trunk/pole/pergola-column:

1. all four bbox corners must be inside the building footprint;
2. the object must not be inside a solid `parapet` / `tower` / `upper` / `mass`;
3. some other mesh top must be within 0.8 m below the object bottom.

Failing objects are removed. Court surfaces and balcony rails are excluded from
this automatic pass.

Removed counts for the final pass:

| Building | Removed |
| --- | ---: |
| Communal | 4 |
| Lee Shau Kee | 4 |
| Block X | 3 (poles + roof plant) |
| Ng Wing Hong | 3 |
| Chung Sze Yuen | 2 |
| Stanley Ho | 2 |
| Choi Kai Yau | 3 |
| Yip Kit Chuen | 2 |
| Tang Ping Yuan | 1 |
| Chan Sui Wai | 3 |
| Industrial Centre | 1 |
| Shirley Chan | 4 |
| Shaw Sports | 4 |
| Global Student Hub | 0 after source fix |
| Seal of Love | 0 after parapet fix |

Some planters/equipment are now absent rather than floating; this is an
intentional conservative fix, not a surveyed replacement.

## Context roof details

`buildContextDetails()` now tests roof plant, vents, water tanks and green
roofs against the context footprint before adding them. Green roof boards were
lowered from `h + 0.9` to `h + 0.3` so they sit on the roof rather than float
0.625 m above it. Shopfronts already follow actual footprint edges.

This reduces the previously reported 77 outside-centre / 134 outside-corner
candidates; it has not been re-audited object-by-object across all 486 context
props.
