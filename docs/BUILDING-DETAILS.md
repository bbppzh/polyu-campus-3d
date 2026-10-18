# Building exterior models

30 named landmark models are generated. This records implementation coverage,
not surveyed architectural accuracy. Four landmark forms and roof-support handling
were revised on 2026-10-18: [current revision and verification](FINAL-REVISION.md).
The former rounded LKS/Hotel, domed JCIT and full-height Z massing are superseded.

## Model inventory

Heights are model parameters; see each landmark's `heightBasis` for provenance.

| Building | H (m) | Area (m²) | Custom asset | Batch |
| --- | ---: | ---: | --- | --- |
| Hotel ICON | 114.0 | 4039 | Hotel ICON GLB | done |
| Block Z | 48.0 | 3314 | Block Z GLB | done |
| Jockey Club Innovation Tower | 71.2 | 3211 | JCIT GLB | done |
| Block X | 35.0 | 3042 | Block X GLB | done |
| Pao Yue-kong Library | 16.0 | 2345 | Library GLB | done |
| Shaw Sports Complex | 12.8 | 2321 | Shaw GLB | done |
| Lee Shau Kee Building | 20.0 | 2100 | Lee Shau Kee GLB | done |
| Li Ka Shing Tower | 60.8 | 1910 | LKS GLB | done |
| Communal Building | 19.2 | 1820 | Communal GLB | done |
| Lui Che Woo Building | 22.4 | 1109 | AUTO GLB | done |
| GH Block | 25.6 | 1099 | AUTO GLB | done |
| Chow Yei Ching Building | 28.8 | 1073 | Chow GLB (hand) | done |
| CMA Building | 22.4 | 1049 | AUTO GLB | done |
| Chan Sui Wai Building | 22.4 | 989 | AUTO GLB | done |
| Mong Man Wai Building | 28.8 | 971 | Mong GLB (hand) | done |
| Fong Shu Chuen Hall | 6.4 | 961 | AUTO GLB | done |
| Anita Chan Lai Ling Building | 16.0 | 898 | AUTO GLB | done |
| Global Student Hub | 12.8 | 865 | GSH GLB | done |
| House of Innovation | 20.0 | 812 | AUTO GLB | done |
| Chung Sze Yuen Building | 16.0 | 765 | AUTO GLB | done |
| Jockey Club Auditorium | 18.0 | 756 | JCA GLB | done |
| Ng Wing Hong Building | 28.8 | 739 | AUTO GLB | done |
| Choi Kai Yau Building | 32.0 | 721 | Choi GLB (hand) | done |
| Chan Tai Ho Building | 22.4 | 615 | AUTO GLB | done |
| Seal of Love Foundation Building | 22.4 | 599 | AUTO GLB | done |
| Stanley Ho Building | 22.4 | 574 | AUTO GLB | done |
| Shirley Chan Building | 41.6 | 550 | Shirley GLB (hand) | done |
| Yip Kit Chuen Building | 28.8 | 533 | AUTO GLB | done |
| Tang Ping Yuan Building | 22.4 | 248 | Tang GLB (hand) | done |
| Industrial Centre | 25.6 | 1419 | Industrial GLB | done |

## Reproducible workflow

`tools/rebuild_all.py` rebuilds all 30 named models. Roof-bearing builders invoke
`roof_support.finalize_scene`, using actual mesh triangles to place or omit whole
roof assemblies. `cleanup_roof_objects.py` is a compatibility rebuild entry point;
it no longer accepts bounding-box gaps up to 4 m.

`data/landmark-overrides.json` is merged by `tools/extract_data.py`, preserving the
four documented height parameters. Hotel's current 114 m envelope comes from the
building record rather than a storey-count multiplier.

See [reference sources](reference/README.md), [exported geometry QA](final-qa.json),
[context roof QA](final-context-qa.json), and [adjacency QA](final-adjacent-qa.json).
Earlier roof-cleanup and Block Z fix reports describe historical intermediate
models and are superseded by FINAL-REVISION.md.


## Follow-up navigation/card fixes (2026-10-18)

After the final model rebuild, the navigation layer was checked against the
follow-up review:

- mobile 390×844: search/finder visible, Orbit and Reset inside the viewport,
  Map button and minimap hidden together;
- labels use actual DOM rectangles and avoid the open panel (1006×928 QA:
  6 visible, 0 overlaps);
- aliases JCIT / JCA / LKS / W座 / X座 / Z座 / GSH / library / hotel are searchable;
- info card maps raw OSM `yes` to a readable built form and shows height
  provenance visibly;
- JCIT entrance sign now follows the actual footprint edge.

Details and measured values: [FOLLOWUP-REVISION.md](FOLLOWUP-REVISION.md).


## Reference follow-up (2026-10-19)

Additional public references were preserved in `docs/reference/` and recorded in
[DATA-GAPS-20261019.md](DATA-GAPS-20261019.md). The Hotel G/F plan was used to
add three draft entrances (hotel / school / staff); their centres were checked
outside other solids, but plan registration is still approximate; LKS final material
names are now mapped to the app facade shaders. Complete four-direction measured
elevations and all platform/link levels remain unverified.
