# Talha Mono beta.5: contextual forms and spacing

Historical review: the current candidate is [beta.6](beta6.md). The reviewed
beta.5 fonts are preserved in `build/beta5-baseline/`.

22 October 2026. The new features are implemented in all 20 locally built OTF
faces in `build/`. Contextual accent corrections apply in normal text. The
new **Contextual spacing** treatment is selected with OpenType **`ss11`**.
The beta.4 build is retained in `build/beta4-baseline/`; checked-in release
fonts in `fonts/otf/` remain beta.3.

The local package is `dist/TalhaMono-1.0.0-beta.5-local.zip`, accompanied by
a SHA-256 checksum. It contains the 20 candidate faces and the review material;
experimental strength and letterform trial fonts are excluded. The font
[checksums](measurements/beta5-sha256.json) identify the reviewed build.

| Review | Artifact |
|---|---|
| Before/after: stacked marks, below marks and accented healing forms | [Accent proof](beta5-context-accents.png) |
| SS11 off/on at native 12, 15, 20 px in five faces | [Spacing proof](beta5-context-spacing.png) |
| Anonymous personal comparison | [Samples A/B](beta5-reading-comparison.png) |
| Separate letterform experiments | [Trial proof](beta5-letter-trials.png) |
| Default-text legibility, all ten styles | [Regression gate](beta5-regression.md) |
| Contextual shaping, coverage and advances, all 20 faces | [Audit](measurements/beta5-context-check.json) |
| Whole-word measurements, all ten styles, feature off/on | [Table](measurements/beta5-whole-words.md) · [JSON](measurements/beta5-whole-words.json) |

## Contextual accent correction

Accented healing forms are now generated from the same Talha pen recipes as
their defaults. Their bodies and marks receive the underlying letter's
context transform before the fixed-angle nib sweeps them. This replaces the
inherited Radon outlines previously selected in words containing forms such
as `itilde.left` and `iacute.left`.

The build records each precomposition and each alternate's horizontal
transform. GPOS anchors follow that transform. Above-mark precompositions
retain their stacking anchors; below-mark precompositions also receive base
coverage. GDEF correctly classifies these variants as bases. Turkish `i.loclTRK`
and the redrawn extended Latin letters receive attachment coverage as well.

Accented `j` deserves a special case: upstream has `j.left/right/both`, but
no equivalent dotless-j variants. Its accented forms use the `j` placement
transform with Talha's genuinely dotless `uni0237` recipe.

The real-font audit requires attachment anchors and GDEF base classes on
**1,314 supported letter forms per face**, verifies stacked and below marks
with contextual features off/on, and compares NFC/NFD placement signatures.
Input cluster indices are excluded from that comparison because Unicode
normalization legitimately changes codepoint offsets. The previously failing
`mi\u0303\u0301`, `mi\u0302\u0301` and `ml\u0323` cases now pass in all 20 faces.

## Contextual spacing: SS11

Enable **ss11 — Contextual spacing** in an application that exposes stylistic
sets. Keep the existing `calt` feature enabled for texture healing. In CSS:

```css
font-feature-settings: "calt" 1, "ss11" 1;
```

The feature shifts the middle letter toward its narrower neighbor when the
two neighbors belong to different width classes. It adds **702 same-advance
alternates** per face. Neighbors that have already been shifted remain
recognizable to later substitutions. Existing healed forms can act as
neighbors, but are not shifted again as the middle letter.

Width classes come from mean horizontal ink spans across fifteen slices of
the lowercase body, rather than the outer bounding box. This avoids treating
`r` as a wide letter merely because its shoulder reaches right. Classes are
derived separately from each face. The fixed shift is 40 font units; no
advance width changes, so columns and total string widths stay fixed.

The new lookup is appended after upstream healing and preserves existing
GSUB features, language registrations, and required-feature indices. It is
not merged into `liga`. Turning SS11 off restores the ordinary spacing.

### Native-size diagnostics

The new harness shapes each complete string with HarfBuzz, then renders its
glyphs at the resulting positions with FreeType light hinting and native
CFF hints. Combining marks and ligatures stay in their original shaped
clusters. It measures gaps between those cluster masks, including gaps across
word spaces; no substring is reshaped to infer a word's spacing.

Examples at **15 px**, gap CV off → on, lower meaning more even in this
particular diagnostic:

| Face | tipiti | antigo | Estrada |
|---|---:|---:|---:|
| Regular | 0.1896 → 0.1378 | 0.2869 → 0.2274 | 0.3057 → 0.2868 |
| Italic | 0.2359 → 0.2013 | 0.3568 → 0.2913 | 0.3386 → 0.3277 |
| Wide Regular | 0.1455 → 0.1064 | 0.2496 → 0.1824 | 0.2639 → 0.2540 |
| Text Regular | 0.1891 → 0.1380 | 0.2854 → 0.2334 | 0.2972 → 0.2759 |

These results are not reading-speed scores. They are not directly comparable
to the previous 40 px Pango bigram statistic. The Pango proof provides a
second rendering check at the actual reading sizes.

The corpus includes sixteen words, prose/code runs and accent probes at
12/15/20 px, measured with SS11 off/on in all ten styles. It produces **960
measurements**. No new cross-cluster ink overlaps occur in this corpus.
There are tradeoffs: Regular *little* at 15 px rises from 0.0726 to 0.0764;
Italic *filter* rises from 0.1430 to 0.1472. SS11 therefore remains an opt-in
treatment for personal reading evaluation.

### Strength trials

`context_trials.py` exports 20/40/60-unit alternatives from an official
40-unit build. It moves glyph curves and their attachment anchors together,
keeps glyph IDs and advances, and autohints the changed eligible glyphs.
Other outlines remain intact. The copies are for isolated measurements.

[Strength comparison](measurements/beta5-spacing-strengths.md) ·
[Machine-readable results](measurements/beta5-spacing-strengths.json).
The 60-unit trial further reduces several target gaps but worsens Regular
*little* at 15 px. Forty is the middle trial, not a claimed universal optimum.

## Letterform experiments

Six Regular-only studies compared smaller/larger changes in three groups:
terminal openings (`r/f`), stem distinctions (`t/l/1`), and both together.
The trials lower the `t` bar, open the `r/f` endings, broaden the `l` turn,
and extend the `1` flag, at 20- or 40-unit strengths. Their advances stay fixed.
They are isolated-letter studies; their inherited contextual variants are
not regenerated and these drawings are not in the ordinary build.

Five of six fail the existing 0.01 pair guard. The 20-unit stem study passes
Regular's screen and improves `1/l`, but does not improve `t/r` at every size
and is not validated across the other styles. It remains a review candidate.
The default `t/r/f/l/1` drawings are retained.
[Scores and rejected pairs](measurements/beta5-letter-trials.json).

## Validation

- **201 Python tests pass; mypy passes on 51 source files.** Tests cover nested
  lookup relocation, inherited-feature preservation, actual mark attachment,
  dotless-j fallback, normalization, optical width classification, fixed-cell
  curve copying, missing coverage, ligatures and whole-run gap measurements.
- The default-text gate passes in all ten styles against beta.4, with no new
  waivers and unchanged isolated-letter confusability results.
- Real-font contextual checks pass in all 20 faces and are now part of CI.
  Unicode mappings and every pre-existing advance are preserved; all new
  spacing alternates occupy one cell.
- All 20 faces are rebuilt and hinted with the existing deliberate exclusions.
  Windows clipping checks pass during the build. NF copies retain their
  corresponding ordinary face's text programs, hint resources, GSUB and GPOS.
- FontBakery 1.1.0's universal profile reports **zero failures, errors or fatal
  results** across all six families. Network checks are skipped; the existing
  `case_mapping` and CFF-incompatible `opentype/monospace` exclusions remain.
  Existing warnings include inherited mark classifications, line gaps, soft
  hyphen/unreachable variants, NF size and legacy icon-name lengths.
  Reports: [Normal](qa/beta5-qa-normal.md), [Wide](qa/beta5-qa-wide.md),
  [Text](qa/beta5-qa-text.md), [Normal NF](qa/beta5-qa-normal-nf.md),
  [Wide NF](qa/beta5-qa-wide-nf.md), [Text NF](qa/beta5-qa-text-nf.md).

The shared OpenType table walker also discovers the previously missed nested
`period.raised` substitution, so that glyph now receives the existing pen
restroking treatment.

## Reproduce and review

Install the normal requirements, including the new HarfBuzz/FreeType Python
bindings used by the measurement and shaping checks:

```sh
JOBS=2 HINT_JOBS=1 ./build.sh /path/to/python
python tools/context_check.py --fonts build --base build/beta4-baseline
python tools/check.py --base build/beta4-baseline --new build
python tools/word_measure.py --font Candidate=build/TalhaMono-Regular.otf --compare-spacing
python tools/context_trials.py --font build/TalhaMono-Regular.otf
python tools/feature_proof.py --base build/beta4-baseline --new build
pytest
mypy
```

Use the anonymous PNG at 100% zoom to judge clarity and preference before
opening the [assignment key](measurements/beta5-reading-key.json). It repeats
the same passage, so second-read speed is not evidence of a font benefit.
For a timed personal trial, use fresh equivalent passages, counterbalance
A/B order, and log reading errors/corrections, time and preference separately.
The reading session itself remains a human evaluation; the artifacts do not
claim a population-level readability result.
