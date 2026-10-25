# Display pilot: swash capitals, scroll leaf, ribbon

21 October 2026. Fifteen studies: three each for `A`, `P`, `R`, a scroll leaf,
and a ribbon end. Study 02 is selected for all five motifs and integrated into
the build source. The title page, chapter opening, and source atlas now show
these selected drawings.

| Review | Preview | Vector |
|---|---|---|
| Previous capitals and three treatments | [PNG](swash-comparison.png) | [SVG](swash-comparison.svg) |
| Selected capitals at 48, 96, 192 px and in words | [PNG](swash-sizes.png) | [SVG](swash-sizes.svg) |
| Previous leaf/ribbon and three treatments | [PNG](motif-comparison.png) | [SVG](motif-comparison.svg) |
| Selected ornaments at 48, 96, 192 px | [PNG](motif-sizes.png) | [SVG](motif-sizes.svg) |
| Selected drawings in a title page | [PNG](display-folha.png) | [SVG](display-folha.svg) |
| Selected drawings in a chapter opening | [PNG](display-chapter.png) | [SVG](display-chapter.svg) |

## What changed

- **A:** its crossbar enters through an open loop on the left. Its diagonals
  and triangular counter retain the ordinary capital's construction.
- **P:** a curved entry joins the bowl, and the stem ends in a descending
  leftward rasgo. It has no detached ornament above its head.
- **R:** the entry shares P's motion, while the leg continues into a curl
  below the baseline and to the right.
- **Scroll leaf:** scalloped lobes replace the almond silhouette; two ribs
  articulate the interior. The supporting C-scroll remains. All four
  directions and their four turned forms use the same new skeleton.
- **Ribbon:** the front band stands in front of a lower swallowtail; a short
  crease separates the planes. Both ends retain a margin inside their cells,
  including at the Bold weight.

The first capital treatment uses short entries and exits. The second adds
room for the pen to turn. The third extends the motion further: A's additional
baseline sweep, P's longer descending stroke, and R's wider exit need more
margin in a composition. The second treatment provides a clearer gesture
without requiring the third's extra reach.

The first leaf omits the ribs; the second adds them; the third increases the
edge weight. The third ribbon adds a second inner rule, which crowds the
front band. The second leaf and ribbon retain enough internal detail at
96–192 px while keeping a recognizable silhouette at 48 px.

These are interpretations of the [documented sources](README.md#sources-and-image-credits).
The swash comparison uses a crop of Figueiredo's plate nº 7's capitals. The
leaf and ribbon use the portal and Habacuc references already credited in the
source atlas. They are contemporary drawings, not traced reproductions.

## Integration and validation

`swash_caps.py` supplies complete letter-specific skeletons for `A.swsh`,
`P.swsh`, and `R.swsh`. `place_ornaments.py` uses them when it creates `swsh`.
The remaining capitals retain their earlier flourish construction. `titl`
retains the existing carved capitals.

`display_motifs.py` supplies the leaf and ribbon; the existing ornament
orientation, cell fitting, and Unicode mapping code places them. A skeleton
is slanted or mirrored before the fixed-angle nib sweeps it.

The pilot exporter creates review copies in `build/swash-pilot/selected/`
from all 20 existing faces. Those copies retain the release's names, version
metadata, and hinting for the other glyphs. The checked-in release fonts in
`fonts/otf/` remain the baseline; the pilot has not been installed or released.

- [Outline audit](pilot-audit.md): precisely 13 glyphs changed in every face.
  Every other CFF program, including its hints, is byte-identical. All
  advances, OpenType feature tables, positioning, and other metadata tables
  remain unchanged. Every new glyph fits the ascent/descent, and Unicode
  ornaments fit their cells.
- [Legibility regression gate](pilot-regression.md): pass. Default-text
  confusability, spacing and sharpness measurements are unchanged.
- The capital geometry checks cover all three treatments in Regular,
  Bold, Italic, Bold Italic, and Text. Each letter remains connected and
  retains one counter. Ornament checks cover normal and Wide cells at
  Regular, Bold, and Text nib weights.
- Fresh Regular and Italic builds through `merge.py` reproduce all 13 pilot
  glyph programs byte for byte from the preview copies.
- Actual Pango shaping selects the new swashes at all three proof sizes
  in Regular and Italic. Rendering the same capitals with the feature off
  produces pixels identical to the baseline.

The new glyphs in review copies have fitted curves and are unhinted. The
normal build can autohint them through the existing build pipeline.

## Reproduce

From the repository root, with the normal dependencies and `rsvg-convert`:

```sh
python tools/swash_pilot.py
python tools/design_atlas.py --fonts build/swash-pilot/selected
python tools/pilot_validation.py --base fonts/otf --new build/swash-pilot/selected
python tools/check.py --base fonts/otf --new build/swash-pilot/selected --report docs/design/pilot-regression.md
pytest
```

The full build also uses the selected drawings. After building normally,
`python tools/design_atlas.py --fonts build` renders them from those files.
An application's `swsh` feature selects the capitals; leaf U+1F650–1F657 and
ribbon U+2770–U+2771 select the ornaments explicitly. Use a single swash initial
in a heading and reserve space for its horizontal overhang.
