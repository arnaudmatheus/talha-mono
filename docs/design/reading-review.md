# Talha Mono: reading review and cross-style stem study

The [next-step research](next-steps-after-beta6.md) specifies full-family
propagation, independent feature combinations, renderer checks and font-pair
comparison work following this study.

23 October 2026. The next steps after beta.6 now have a portable reviewer,
cross-style letterform results, and a native terminal font-resolution check.
The 20 beta.6 candidate OTF files and the checked-in release fonts are unchanged.

## Review the current spacing

[Download the local reading reviewer](../../dist/TalhaMono-1.0.0-beta.6-reading-review.zip)
and extract it, or use the generated `build/reading-review/` directory.
It contains all 20 beta.6 faces, a face selector, 12/15/20/24 px sizes,
light/dark grounds, synchronized editable samples, anonymous A/B spacing,
and an observation journal with JSON export.

From the project root, run:

```sh
python -m http.server 8765 --bind 127.0.0.1 --directory build/reading-review
```

Open **http://127.0.0.1:8765/**. For the extracted ZIP, run the same command
without `--directory` from inside its `TalhaMono-reading-review` folder.
Serve it over localhost; opening `index.html` directly does not provide
the HTTP origin needed to load the manifest and font files.

Choose a face, size and ground at 100% browser zoom. Read or edit the samples
and record clarity/preference before revealing the spacing. Save several
observations, start a new A/B order as needed, then export the JSON before
closing the page. The two panes use the same physical font file with
`calt`/`liga` enabled; only SS11 differs.

The viewer verifies loaded font bytes against the manifest's SHA-256 digest.
Observations retain the font identity, actual edited text, face/size/ground,
A/B assignment, preference, notes, timestamp, and whether the UI reveal was
used before the rating. This is an anonymous preference comparison, not a
reading-speed experiment or a guarantee of scientific blinding. A timed
trial needs fresh equivalent passages and counterbalanced order.

Observations stay in page memory until exported. No server receives them;
reloading clears them. The downloadable bundle excludes user exports and
unlisted font files. It contains current beta.6 fonts; the letterform studies
below are reviewed separately.

## Extend the t/l/1 study

[Native Pango comparison](beta6-stem-study.png) ·
[Original 20-unit trial](measurements/beta6-stem-study.md) ·
[Refined trial](measurements/beta6-stem-refinement.md) ·
[Full refined scores](measurements/beta6-stem-refinement.json)

The original study lowers the `t` bar, widens the low `l` turn and extends
the `1` flag by 20 units. Each italic uses its own corsiva skeleton, with
its proper nib, slant, vertical mapping and hint exclusions. All ten
zero-strength controls reproduce the original CFF programs and pair scores.

At 12/15/20 px, the original trial passes the existing 0.01 pair guard in
**nine of ten styles**. Text Regular fails on `1/I` at 15 px, worsening by
**0.011**. No waiver is added.

A global refinement keeps `t/l` at 20 and reduces the `1` flag to **10 units**.
It passes in **all ten styles**, across 24 pairs and three sizes per face
(720 pair measurements). At 20 px, Regular `1/l` improves by 0.028 and Text
Regular `1/l` by 0.029. Improvements vary: Bold Italic `1/l` becomes 0.003
more similar at 20 px, and Regular `t/r` becomes 0.002 more similar.

These are isolated plain-glyph studies. Accented letters, inherited healing
forms and SS11 alternates are intentionally unchanged in the study copies;
their anchors are not redesigned. The audit protects every other outline,
shared hints, OpenType tables, glyph IDs and advances, and permits existing
corsiva overhangs without enlarging them. The study fonts are kept in
`build/stem-trials/` and excluded from installable/reviewer packages.

Passing this screen makes the refined recipe a candidate for propagation
through the complete glyph families. It does not establish a reading benefit
or make these partial study files ready to install.

## Native terminal check

[Ghostty/fontconfig report](measurements/beta6-terminal-resolution.md) ·
[Raw resolution evidence](measurements/beta6-terminal-resolution.json)

All **20 candidate faces** resolve correctly using a private fontconfig set.
Fontconfig selects the exact copied font/style; Ghostty resolves `t/l/1`,
an accented base and a combining mark to the requested family. NF faces also
resolve U+F120. Powerline U+E0B0 uses Ghostty's internal sprites.

The commands disable Ghostty's default config files and install no fonts.
`show-face` explicitly excludes grapheme-cluster behavior, so this check
does not verify terminal pixels, SS11 activation, caret/selection, scrolling,
or the rendering of an open editor.

## Validation status

- 230 Python tests and six JavaScript model tests pass; mypy passes on
  62 source files. JavaScript syntax, ZIP integrity, copied-font hashes and
  isolation from user exports are checked. The model checks invalid ratings,
  A/B assignments, immutable font snapshots, reveal state and Unicode export.
- Native Pango study proofs are generated and visually reviewed.
- Live browser interaction remains **unverified**: this session's browser
  runtime reports no available browser. The reviewer has no browser screenshot
  or claim of verified editing/caret/selection behavior.
- A personal rating session and native editor rendering review still need
  human evaluation. The candidate font bytes retain their beta.6 validation.

Reproduce the work with:

```sh
python tools/stem_trials.py --fonts build
python tools/stem_review.py --base build --variant 20
python tools/stem_review.py --base build --variant 20-flag10 \
  --out docs/design/measurements/beta6-stem-refinement
python tools/stem_proof.py
python tools/reading_review.py --fonts build \
  --zip dist/TalhaMono-1.0.0-beta.6-reading-review.zip
python tools/terminal_review.py
pytest
mypy
node --check tools/reading_ui/review.mjs
node tests/test_reading_review.mjs
```
