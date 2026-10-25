# Talha Mono beta.6: guarded contextual spacing

23 October 2026. The next implementation step refines optional **SS11 —
Contextual spacing**. The 40-unit ink shifts and fixed cell widths remain;
the build now checks whether a proposed shift has enough room to improve
its two neighboring contour gaps.

[Native-size comparison](beta6-spacing-review.png) ·
[Anonymous A/B sample](beta6-reading-comparison.png) ·
[All-style results](measurements/beta6-spacing-review.md) ·
[Measurement JSON](measurements/beta6-spacing-review.json)

## What changed

Beta.5 chose a direction using the neighbors' optical width classes. That
misses asymmetric bodies and can disturb already balanced gaps. Beta.6 keeps
that proposal, then samples the contours at shared heights. A shift activates
only when the predicted gap difference exceeds **twice the shift**, in the
proposed direction. Otherwise the default drawing is retained.

Profiles sample every 16 font units from −400 through 2,000. A pair's gap
uses only rows containing both bodies. Neighbor gaps are grouped in 80-unit
bins; the guard uses the strictest actual gap in each bin, so rounding cannot
activate a marginal context. Accents share their base letter's body profile;
attached marks still move with their anchors. Shifted letters remain eligible
neighbors; healed forms are not shifted again as middle letters.

The compiler partitions overlapping right-neighbor sets into disjoint classes.
It emits class-based chaining subtables grouped by central body, wrapped in
extension lookups. Nested indices are relocated into the existing GSUB table.
Language registrations, required features, ligatures and the SS11 UI label
are preserved. There are no word-specific exceptions.

## Results and limits

The comparison covers all ten ordinary styles at **12, 15 and 20 px**:
16 original diagnostic strings and 32 separate review strings, giving
**1,440 cases**, each with ordinary spacing, beta.5 SS11 and beta.6 SS11.
The separate set includes Portuguese accents, English words and code.

Using gap CV as a diagnostic, differences within 0.0001 count as unchanged.
Cases scoring worse than ordinary spacing fall from **151 to 18**:

| Corpus | Beta.5 SS11 worse than off | Beta.6 SS11 worse than off |
|---|---:|---:|
| Original, 480 cases | 48 | 8 |
| Separate review, 960 cases | 103 | 10 |

At 15 px, Regular *little* returns from 0.0764 to its ordinary 0.0726;
Italic *filter* returns from 0.1472 to 0.1430. Regular *tipiti* retains
0.1378, compared with 0.1896 off.

This is a conservative tradeoff, not a uniform improvement over beta.5 on.
The guard suppresses some helpful shifts too. Wide Regular *trilho* at
12 px changes from 0.1657 off / 0.1616 beta.5 on to 0.1716 beta.6 on.
Per-style counts and every word are in the linked reports. CV does not
measure reading speed, comprehension or preference. SS11 remains opt-in.

### Size and shaping cost

The extra conditions enlarge GSUB and cost more to shape than the width-only
feature. The 80-unit bins reduce that cost relative to the finer 40-unit
prototype. The coarser 160-unit prototype suppresses more helpful spacing
and was not selected.

Local diagnostic timings for 1,760 characters were approximately 0.4 ms with
beta.5 SS11, 5.4 ms with 40-unit bins, 2.2 ms with 80-unit bins, and 1.1 ms
with 160-unit bins. These are local HarfBuzz timings, not editor latency or
a portable benchmark. Default spacing does not enable the new lookup.
[Final-build timing details](measurements/beta6-shaping-cost.json): SS11 off
measures about 0.22 ms in both builds; beta.6 on measures about 2.23 ms.
Ordinary Regular grows from about 928 KiB to 1.7 MiB, introducing the
FontBakery file-size warning in the ordinary families as well as NF.

## Validation and reproduction

- **214 Python tests pass; mypy passes on 56 source files.**
- All 20 ordinary/NF faces are rebuilt and autohinted. The
  [contextual audit](measurements/beta6-context-check.json) passes in every face.
- The [legibility gate](beta6-regression.md) passes in all ten ordinary styles
  against beta.5, with unchanged confusability and no new waivers.
- All glyph orderings, CFF outline programs, private/global hint resources,
  GPOS, GDEF and non-SS11 substitution graphs match beta.5 across all 20 faces.
- All 1,440 review cases preserve feature-off pixels and string advances.
  There are no cross-cluster ink overlaps in either baseline or candidate.

FontBakery 1.1.0's universal profile reports **zero failures, errors or fatal
results across all six families**. Network checks are skipped, with the same
`case_mapping` and CFF-incompatible `opentype/monospace` exclusions as beta.5.
Existing warnings remain, plus file-size warnings for the ordinary faces.
Reports: [Normal](qa/beta6-qa-normal.md), [Wide](qa/beta6-qa-wide.md),
[Text](qa/beta6-qa-text.md), [Normal NF](qa/beta6-qa-normal-nf.md),
[Wide NF](qa/beta6-qa-wide-nf.md), [Text NF](qa/beta6-qa-text-nf.md).

The local package is `dist/TalhaMono-1.0.0-beta.6-local.zip`, with a SHA-256
checksum beside it. The [font checksums](measurements/beta6-sha256.json)
identify the reviewed files.

```sh
JOBS=2 HINT_JOBS=1 ./build.sh /path/to/python
python tools/spacing_review.py --base build/beta5-baseline --new build \
  --out docs/design/measurements/beta6-spacing-review
python tools/context_check.py --fonts build --base build/beta5-baseline
python tools/check.py --base build/beta5-baseline --new build
python tools/spacing_proof.py --base build/beta5-baseline --new build
pytest
mypy
```

The reviewed beta.5 files are retained in `build/beta5-baseline/`; checked-in
release fonts remain beta.3. A new workspace can recover the baseline from
the previous local candidate ZIP. The beta.6 package contains ordinary and
NF candidates, review documents and proofs; strength and letterform trial
fonts are excluded.

Enable the feature in CSS with:

```css
font-feature-settings: "calt" 1, "ss11" 1;
```

## What remains

The [reading-review follow-up](reading-review.md) now provides a portable
reviewer and cross-style `t/l/1` results. A refined 20-unit `t/l` + 10-unit
`1` flag study passes the isolated pair guard in all ten styles; the default
glyph families remain unchanged pending propagation and evaluation.

Compare the proof at 100% zoom and try SS11 in the actual editor before
choosing it for sustained reading. A personal timed trial needs fresh,
equivalent passages and counterbalanced order. The previous `t/l/1` drawing
study remains separate; default letterforms have not been promoted from it.
Record clarity and preference in the anonymous sample before opening the
[A/B assignment key](measurements/beta6-reading-key.json).
