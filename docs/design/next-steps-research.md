# Research: next steps after beta.4

Implementation update, 22 October: [beta.5](beta5.md) implements the
contextual accent correction, native whole-run measurements and opt-in
three-letter spacing. It also records letterform trials and prepares the
personal reading comparison. The findings below document the starting point.

21 October 2026. Primary font documentation, feature source code, OpenType
specifications and published reading studies were checked against Talha's local
measurements and actual shaping. The recommended order is: contextual accent
correctness, stronger context measurements, spacing prototypes, letterform
experiments, then a reading session. This research does not promote a release.

## 1. Correct the existing contextual accent pipeline

A read-only audit found two related problems:

- In Regular, `iacute.left` and `itilde.left` are exact outline matches for the
  horizontally rescaled upstream Radon glyphs. The default accented forms and
  unaccented `i.left` are redrawn. Enabling `calt` can therefore switch the
  writing style as well as the spacing.
- Contextual bases such as `itilde.right` lack GPOS mark-to-base coverage.
  With the diagnostic string `m + i + U+0303 + U+0301`, `calt` off places the
  acute at `(-1123, 371)` relative to its glyph origin in Regular. With `calt`
  on, HarfBuzz selects `itilde.right` and leaves the acute at `(0, 0)`.

The mark-placement result reproduces in all ten ordinary styles in **both**
the beta.3 baseline and beta.4 candidate. This predates the latest changes.
[Visual proof](context-accents.png) · [20 baseline/candidate probes and outline comparisons](measurements/context-research.json).

The existing gate checks isolated letters and selected shaping samples, so its
pass does not establish correctness for marks after contextual substitutions.
The OpenType specification describes mark placement through anchors on the
actual substituted base glyph. [GPOS specification](https://learn.microsoft.com/en-us/typography/opentype/spec/gpos#lookup-type-4-mark-to-base-attachment-positioning-subtable).

**Next implementation:** enumerate reachable `calt` outputs for supported Latin
bases and accents; regenerate these from Talha skeletons, with their marks;
create GDEF base membership and transformed attachment anchors for those
variants. Audit below-mark precomposed bases as well: `uni1ECB` also lacks
base coverage in the current Regular build. Check both precomposed and
decomposed inputs, stacked marks, and `calt` on/off before adding new alternates.

**Completion evidence:** targeted shaping tests catch these exact failures;
marks remain attached in native-size proofs; relevant contextual glyphs no
longer retain upstream letterforms; all advances remain fixed. Then rerun the
ten-style gate and full-family QA.

## 2. Measure complete contexts at reading sizes

The current bigram spacing score is calculated at 40 px. Beta.4's whole-word
results already disagree with its overall improvement: Regular *tipiti* gap
variation rises from 0.1404 to 0.1436, while *antigo* improves. Consequently,
further experiments need measurements of complete shaped strings at
12/15/20 px, alongside the existing 40 px diagnostic.

Use *tipiti, antigo, Estrada, filter, list, minimum, little*, Portuguese prose,
and code such as `if item != nil { filter(list, 1); }`. Add held-out words,
word boundaries, punctuation, marks, repeated runs and spaces. Measure the
entire sequence with contextual features enabled; do not infer a word's
spacing by assembling separately shaped bigrams.

Report individual gaps, their spread, collisions, word-boundary gaps and
feature-selected glyphs. A smaller CV is a useful diagnostic, not proof of
faster reading. Slattery and Rayner's experiments show that within-word and
between-word spacing interact; the result does not prescribe an ideal gap
for Talha. [2013 study](https://pubmed.ncbi.nlm.nih.gov/23709061/).

## 3. Prototype three-letter positioning, with fixed advances

Monaspace's healing swaps narrow/wide neighbors for alternates that donate
and use space. Its documentation also explains lookup ordering: later passes
see substitutions made by earlier passes. This supports extending the current
machinery, but does not establish a solution for narrow–narrow runs.
[Monaspace design and implementation](https://github.com/githubnext/monaspace/blob/main/docs/Texture%20Healing.md).

Commit Mono supplies a more relevant experiment: the middle character's
position depends on the width classes of both neighbors. Its public source
has substitution-based `ss05` and a positioning-based `kern` implementation.
The latter changes x placement with zero advance adjustment.
[Feature source: substitutions](https://github.com/eigilnikolajsen/commit-mono/blob/main/src/features/ss05_smartkerning.fea) ·
[Feature source: positioning](https://github.com/eigilnikolajsen/commit-mono/blob/main/src/features/kern_smartkerning.fea).

**Proposed Talha experiment, not a proven improvement:** compare beta.4 with
same-shape alternate positions at ±20/40/60 font units, chosen using both
neighbors. Derive width classes from Talha's own ink, not Commit Mono's letter
lists. Start in separate Regular preview files, then evaluate Italic and Text.
Merge only after accounting for upstream healing passes and the accent fix.

Use same-advance GSUB alternates under `calt` as the first compatibility trial;
compare placement-only GPOS as a second implementation where supported.
Check the exact glyph origin and advance in the target renderer. Neither
method automatically repairs every narrow run: moving an internal letter
closes one neighboring gap while opening the other. Some contexts will still
need different outlines or acceptance of monospace's spacing compromises.

Commit Mono's site describes its system as improving reading, but that claim
is not treated here as an independent reading-speed result for Talha.
[Designer explanation](https://commitmono.com/).

## 4. Test the letter group through distinguishing features

The previous shortened-`r` grid fails `t/r`, so repeating that direction has
little value. Instead, vary one discriminating feature at a time within
Talha: `t` crossbar/neck, `r` shoulder and terminal opening, `f` hook opening,
`l` lower turn, and `1` flag/foot. Keep the nib, weight and cell fixed. Screen
individual changes, then compare coordinated finalists against every pair
in the group, including `i/j` and `l/I`.

Beier and Larson compared variants within the same typeface to reduce design
confounds; their recognition experiments support investigating narrow-letter
width and distinguishing features, not a universal parameter setting.
[2010 paper](https://www.microsoft.com/en-us/research/wp-content/uploads/2021/06/Beier-Larson-2010-Design-Improvements-for-Frequently-Misrecognized-Letters.pdf).

A newer experiment included `r/t/f` among seven letters and found poorer
recognition with closed apertures, both with and without flankers. This makes
terminal opening worth testing. It does not prove that shortening Talha's `r`
will help, or that enlarging every aperture will improve code reading.
[Beier and Oderkerk, 2022](https://doi.org/10.1016/j.apergo.2022.103709).

## 5. Finish with a small blinded reading comparison

Use unnamed baseline and finalist samples, counterbalance their order and use
equivalent passages to reduce repetition effects. Log reading errors and
corrections, time, and preference separately. Include short character-in-string
tasks and several minutes of prose/code on the actual monitor and laptop at
12–20 px. This is a personal design decision aid, not a population-level
legibility study. Retain the 0.01 pair gate as a regression screen; do not
interpret image correlation as a calibrated probability of human error.

The first implementation to start is **contextual accented forms and their
mark attachment**, with regression cases for `mi\u0303\u0301`,
`mi\u0302\u0301` and `ml\u0323`. The next design experiment is three-letter
positioning evaluated in whole words. Further display ornament can follow
these text priorities.
