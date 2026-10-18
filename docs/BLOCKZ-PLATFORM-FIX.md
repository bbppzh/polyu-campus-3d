# Block Z platform fix (2026-10-18)

The platform/roof objects were regenerated so every roof bed, tree, AC unit and
terrace planter is tested against the actual footprint polygon before it is
created. Objects that could not fit were dropped rather than left floating.

## Changes

- **Roof beds**: only 2 of the previous 4 survive the inside test; all vertices
  are inside the 0.86-scaled upper footprint. The two overhanging beds are gone.
- **Roof trees**: 3 of 5 survive; all trunk vertices are inside the upper
  footprint and trees are kept clear of the pavilion.
- **Roof AC**: 1 unit survives the inside test; 0 vertices outside.
- **Terrace planters**: 1 survives; it is on the 18 m lower roof ring, outside
  the upper volume, and all vertices are inside the lower footprint.
- **Intermediate platforms**:
  - 11.5 m platform uses the **lower** footprint.
  - 24 m platform uses the **upper** footprint (previously the full building
    outline, which overhung by up to 12.9 m).
  - Both are now coincident with their supporting footprint; any "outside"
    vertices are exactly on the boundary (max distance 0.000 m).
- **Pavilion / pavilion roof**: already fully inside the upper footprint.

## Verification

Blender vertex check against the local footprint polygons:

```
BLKZ_bed_0 / bed_1                        0 vertices outside upper
BLKZ_tree_trunk_0 / _1 / _2               0 vertices outside upper
BLKZ_roof_ac_0                            0 vertices outside upper
BLKZ_terrace_planter_0                    0 vertices outside lower
BLKZ_platform_0 / platform_1              boundary-only, max outside 0.000 m
BLKZ_pavilion / pavilion_roof             0 vertices outside upper
```

## Limitation

The official single-angle photo shows layered terraces and planters, but it
does not supply exact terrace outlines or elevations. The reduced, contained
layout is a valid geometry fix, not a surveyed reconstruction of every terrace.
