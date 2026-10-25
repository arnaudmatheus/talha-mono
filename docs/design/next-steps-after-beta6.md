# Research: next steps after the beta.6 studies

23 October 2026. Primary specifications and implementation documentation were
checked against the current source, study results, and three local shaping
probes. The recommended next implementation is a **complete experimental build
of the refined stem recipe**, followed by renderer checks and a comparison
that separates letterform and spacing effects. These are proposed steps;
candidate font files have not changed during this research.

## 1. Propagate the refined recipe through the full build

The [refined study](measurements/beta6-stem-refinement.md) passes the isolated
pair guard in all ten styles: `t/l` at 20 units, `1` flag at 10. Its file copies
replace only three plain glyphs. Accents, extended letters and contextual
alternates still use the current drawings.

Start by extracting a shared raw skeleton recipe and integrating it before
the normal drawing pipeline. Two local dependency details matter:

- `stem_study.stem_skeleton()` already applies `vmap()` to lowercase strokes.
  `glyph_table.glyph_table()` applies the same mapping through `taller()`.
  Installing the already-mapped study function in `letters.LETTERS` would
  map the heights twice. Share the raw recipe and map it once.
- `caps.EXTRAS_LOWER['lslash']` calls the aliased letter dictionary `caps.L`.
  Propagate the new `l` to `ł` too, and preserve that dependency if drawing
  dictionaries are refactored. Test Roman → Italic → Roman in one process
  to catch leaked global recipe changes.

Then rebuild supported precompositions, healing forms, SS11 alternates,
anchors, width classes, contour guards and eligible hints. The pipeline's
placement transforms must follow the new body, rather than keeping old anchor
coordinates. Monaspace's documentation explains that subsequent healing
lookups consume earlier substitutions; OpenType defines attachment anchors
on the actual covered bases. [Monaspace implementation](https://github.com/githubnext/monaspace/blob/main/docs/Texture%20Healing.md),
[GPOS specification](https://learn.microsoft.com/en-us/typography/opentype/spec/gpos#lookup-type-4-mark-to-base-attachment-positioning-subtable).

**Completion evidence:** a zero-strength/default build reproduces beta.6;
the experimental build covers all 20 ordinary/NF faces; unaffected outlines
and hints are preserved outside the declared glyph-family changes; Unicode
mappings and advances remain fixed. Rerun the ten-style pair gate, whole-run
measurements, contextual checks and six-family QA. Record word-level spacing
tradeoffs separately from pair-guard failures.

## 2. Expand the feature and normalization matrix

The current `context_check._check_mark_sample()` sets `calt` and `ss11` to
the same value. It therefore tests `(0,0)` and `(1,1)`, leaving `(1,0)` and
`(0,1)` untested by that check. Exercise all four combinations independently;
add `liga` off/on for code samples.

Add `mĺm`, `mḷm`, `ł`, caron forms and decomposed `t` with stacked/below
marks. Compare NFC/NFD placement signatures while respecting their different
input offsets. Include combinations with no ready-made precomposition, so
mark-to-mark behavior is exercised directly. Unicode distinguishes canonical
equivalence from byte identity and explicitly accounts for corresponding
offsets in differently normalized strings.
[Unicode normalization specification](https://www.unicode.org/reports/tr15/#Canonical_Equivalence).

**Completion evidence:** both new feature combinations pass on every face;
stacked marks remain attached after substitutions; normalization preserves
appearance/placement; glyph order and cell advances remain stable.

## 3. Verify editing behavior in the actual renderers

Ghostty documents cursor-dependent shaping-run breaks. Our current native
helper checks face resolution, not rendered editing behavior.
[Ghostty shaping configuration](https://ghostty.org/docs/config/reference#font-shaping-break).

A local HarfBuzz probe split strings into independent chunks:

| Text and split | Whole-run choice | Independently shaped chunks |
|---|---|---|
| `ti` / `piti` | first `i.ctxL` | first `i` |
| `an` / `tigo` | `n.ctxR`, `t.ctxR` | `n`, `t` |
| `fil` / `ter` | `t.ctxL` | `t` |

All preserve the 6,960-unit total advance. These probes demonstrate context
dependence; they do not reproduce Ghostty's complete shaping algorithm or
establish an editor defect. HarfBuzz documents unsafe-to-break cluster flags
for cases where independent shaping can differ.
[HarfBuzz buffer semantics](https://harfbuzz.github.io/harfbuzz-hb-buffer.html#hb-glyph-flags-t).

Test cursor movement through these words, selection, deletion/reinsertion,
tabs, syntax-color boundaries, ligatures and decomposed marks in a temporary
editor session. Record expected contextual changes; require stable columns,
correct caret/selection behavior, attached marks and no stale ink. Match
effective pixel sizes: Ghostty's size setting is in points and is scaled by
the display, while the reviewer uses CSS pixels.
[Ghostty size units](https://ghostty.org/docs/config/reference#font-size).

In the browser, verify face-switch races, failed-font/hash handling,
synchronized editing, A/B reveal state, exported text/assignments and light/dark
layout. Wait for font loading and layout readiness before screenshots or
geometry checks; the CSS Font Loading draft specifies `FontFaceSet.ready`
for that synchronization.
[W3C Font Loading, ready attribute](https://www.w3.org/TR/css-font-loading-3/#font-face-set-ready).

**Completion evidence:** live screenshots and recorded interactions from the
target browser/editor, with actual face, size, feature settings and display
scale. Static images and font-resolution output remain separate evidence.

## 4. Profile the SS11 lookup design

The current Regular file is 1,801,064 bytes: GSUB is 881,724 bytes and CFF
is 861,758 bytes. The existing local 1,760-character benchmark reports about
2.225 ms with beta.6 SS11 versus 0.383 ms with beta.5 SS11. This makes the
lookup graph a concrete optimization target; those timings are not editor
latency measurements.

FontTools documents automatic HarfBuzz repacking when its binding is available.
Its PairPos compaction option targets GPOS lookup type 2, not our GSUB chaining
tables. [FontTools configuration](https://fonttools.readthedocs.io/en/latest/_modules/fontTools/config.html).

A local serialization probe confirmed:

| Serializer | GSUB bytes | Whole font bytes |
|---|---:|---:|
| Current / forced HarfBuzz repacker | 881,724 | 1,801,064 |
| Forced Python serializer | 984,860 | 1,904,200 |

Both preserve the source CFF bytes. Enabling the repacker explicitly gives
the current size, so that toggle is not a new optimization. Profile lookup
and class-rule counts, experiment with equivalent grouping/indexing, and
compare cold/warm shaping on short lines as well as long runs. Accept an
optimization only with unchanged glyph selections, positions, advances,
normalization behavior and non-SS11 features across the corpus.

[Local probe data](measurements/beta6-next-step-probes.json).

## 5. Compare letterforms and spacing as separate factors

The current reviewer changes SS11 on one physical font file. It cannot
compare the refined stem drawings with the original drawings. After the full
candidate exists, add old/refined font-pair comparisons at a fixed SS11 state,
then compare spacing within each drawing choice. Log the file hash and full
feature settings for each pane; the current single-font observation schema
needs an extension for this.

This is our proposed evaluation design. Beier and Larson's within-typeface
letter-variant experiments support controlling unrelated design differences;
their results do not establish a reading-speed benefit for Talha.
[Primary study](https://www.microsoft.com/en-us/research/wp-content/uploads/2021/06/Beier-Larson-2010-Design-Improvements-for-Frequently-Misrecognized-Letters.pdf).

Keep clarity/preference distinct from errors or time. Use fresh equivalent
passages and balanced A/B order for any timed personal exercise. Complete
the renderer checks before drawing conclusions from the reviewer. Further
display ornament follows these text and validation priorities.
