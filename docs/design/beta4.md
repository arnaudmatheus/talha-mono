# Talha Mono beta.4: local reading candidate

21 October 2026. All 20 OTF faces are built locally in `build/`, combining the
[selected display treatment](pilot.md) with a small roman `i` adjustment.
`fonts/otf/` still contains the beta.3 release baseline. Nothing is installed
or published.

Subsequent [research and contextual checks](next-steps-research.md) found
inherited accented-alternate and mark-attachment problems in both beta.3 and
this candidate. Those cases were outside the checks reported below and are
the first correction to make before promoting the candidate.
They are corrected in the [local beta.5 build](beta5.md).

| Review | Artifact |
|---|---|
| Native 12, 15, 20 px; Regular, Italic, Bold, Wide, Text | [Reading sizes](reading-sizes.png) |
| Whole words, the narrow-letter group, and enlarged native pixels | [Reading contexts](reading-context.png) |
| Historical sources and composed display use | [Source atlas](README.md) |
| Confusable pairs, spacing and sharpness, all ten styles | [Regression gate](beta4-regression.md) |
| Outline, mapping, advance and shaping audit | [Audit](beta4-audit.md) · [JSON](measurements/candidate-audit.json) |

## Selected change

The roman `i` keeps its stem, dot and fixed advance. Its entry begins at
`(320, 865)` instead of `(400, 865)`; its exit ends at `(840, 100)` instead
of `(760, 100)`. Coordinates are on the original skeleton grid, before the
existing x-height mapping, slant, broad-nib sweep and centring.

Both ends expand together. Extending only the exit made `i/l` substantially
more alike at 12 px. The balanced form gives `i/j` a clearer silhouette while
keeping the largest measured `i/l` increase below the 0.01 gate. Dotless i,
precomposed accents, the Turkish local form and texture-healing alternates
inherit the same construction. The corsiva retains its existing `i`.

The source audit finds 32 changed outlines in each roman face: 19 members of
the `i` family and the 13 display glyphs. Each italic face changes only those
13 display glyphs. The display features and Unicode ornament mappings remain
the same. Every character advance is preserved.

## Measurements and limits

Pango/FreeType, isolated fontconfig, grayscale antialiasing, `hintslight`;
24 confusable pairs at 12, 15 and 20 px. The full ten-style gate passes
without a new waiver. The standard gate now includes individual Bold Italic,
Wide Bold, Wide Italic, Wide Bold Italic and Text Italic checks.

| Roman face | Overall gap variation, before → after |
|---|---:|
| Regular | 0.234 → 0.232 |
| Bold | 0.254 → 0.251 |
| Wide Regular | 0.192 → 0.190 |
| Text Regular | 0.236 → 0.234 |

Lower variation means more even gaps in the harness's bigram sample, measured
at 40 px. This is a modest improvement, not evidence that the spacing problem
is solved. [Whole-word measurements](measurements/word-gaps.json) show why:
Regular *antigo* improves from 0.2758 to 0.2688 and *list* from 0.1183 to
0.1133, but *tipiti* becomes slightly less even, 0.1404 to 0.1436, despite
its largest gaps becoming smaller. *Estrada* is unchanged. Italic spacing is
unchanged. These words remain priorities for the next reading session.

Seven whole-skeleton `i` widths, twenty entry/exit combinations and five `r`
arm widths were compared in review copies. Stronger whole-`i` expansion and
exit-only expansion fail the `i/l` guard. Shortening the roman `r` arm improves
`r/n` but worsens `t/r`: even a 4% reduction costs approximately +0.012 at
20 px; 16% costs approximately +0.054. Those `r` trials are rejected. The
`t/r/f/l/1` group retains its existing silhouettes.

[Raw measurements](measurements/) retain the tested coordinates, width scales,
focused pair scores, gap values and all five roman finalists. Prototype fonts
remain under `build/readability-study/`; only the selected balanced `i` is
integrated into `letters.py`.

## Full-build QA

All ten source faces were rebuilt and autohinted with the existing exclusions
for letters whose hinting harms distinction. All ten NF faces were then made
from those hinted fonts. The installed MonaspiceRn Nerd Font Mono sources
supply 10,828 icons per NF face.

FontBakery 1.1.0, universal profile, one worker, network checks skipped, using
the two exclusions already documented in CI: `case_mapping` (inherited missing
capitals) and `opentype/monospace` (the CFF-incompatible check). Fixed advances
are checked independently in the audit.

| Family | Faces | Errors / fatal / failures | Warnings | Detailed report |
|---|---:|---:|---:|---|
| Normal | 4 | 0 / 0 / 0 | 20 | [QA](qa/beta4-qa-normal.md) |
| Wide | 4 | 0 / 0 / 0 | 20 | [QA](qa/beta4-qa-wide.md) |
| Text | 2 | 0 / 0 / 0 | 10 | [QA](qa/beta4-qa-text.md) |
| Normal NF | 4 | 0 / 0 / 0 | 28 | [QA](qa/beta4-qa-normal-nf.md) |
| Wide NF | 4 | 0 / 0 / 0 | 28 | [QA](qa/beta4-qa-wide-nf.md) |
| Text NF | 2 | 0 / 0 / 0 | 14 | [QA](qa/beta4-qa-text-nf.md) |

The ordinary families' warning types are line gap, inherited GDEF mark
classification, spacing marks, soft hyphen and unreachable inherited variants.
Normal-family warnings match beta.3 exactly. NF adds font-size warnings and
legacy warnings for icon names longer than 31 characters.

NF testing exposed inherited hyphenated icon names that failed the mandatory
name check. The NF builder now makes valid, unique names of at most 63
characters and preserves source aliases. Tests cover normalization collisions,
length, invalid prefixes and multiple codepoints referring to one source icon.
The rebuilt fonts retain icon coverage, glyph IDs, advances and byte-identical
CFF outline programs relative to the copies made before renaming.

The candidate audit checks every face's version, Unicode coverage, glyph
indices, advances, missing glyphs in reading/code/diacritic samples, and real
HarfBuzz activation of `swsh`, `titl` and `liga`. The new display glyphs and
`i` fit the existing line metrics; Unicode ornaments fit their cells. The
normal build's Windows clipping check covers every glyph, including icons.
NF copies retain the ordinary font's text CFF programs, hint parameters,
GSUB and GPOS. This also carries the ten-style legibility result to NF.

Python validation: **184 tests pass**, mypy passes on 43 source files, and
Black formatting and shell syntax pass. The source atlas, title/chapter
compositions, hero and specimen are regenerated from the candidate.

## Reproduce and review

```sh
JOBS=2 HINT_JOBS=1 ./build.sh /path/to/python
python tools/check.py --base fonts/otf --new build --report docs/design/beta4-regression.md
python tools/reading_proof.py --base fonts/otf --new build
python tools/design_atlas.py --fonts build
./tools/specimen.sh
./tools/hero.sh
pytest
mypy
```

For each ordinary/NF family, run `fontbakery check-universal -J 1
--skip-network -x case_mapping -x opentype/monospace` on its faces. JSON
reports are retained beside the Markdown reports under `qa/`.

Review the reading PNG at 100% zoom on the actual low-density monitor and
laptop. Concentrate on *tipiti*, *antigo*, *Estrada*, `filter(list, 1)`, and
`t/r/f/l/1` at 12–20 px. The next design decision is whether the small roman
`i` gain feels useful in sustained reading, and which remaining word rhythm
needs a contextual solution. Publishing and installation are separate steps.
