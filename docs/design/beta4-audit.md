# Beta.4 candidate audit

All 20 faces pass. The changed-outline count includes the text and display changes relative to beta.3. NF icon names are normalized; their outline programs are unchanged.

| Face | Glyphs | Cell | Changed text/display outlines | Structure / shaping / bounds |
|---|---:|---:|---:|---|
| TalhaMono-Bold.otf | 3639 | 1160 | 32 | PASS |
| TalhaMono-BoldItalic.otf | 3639 | 1160 | 13 | PASS |
| TalhaMono-Italic.otf | 3639 | 1160 | 13 | PASS |
| TalhaMono-Regular.otf | 3639 | 1160 | 32 | PASS |
| TalhaMonoNF-Bold.otf | 14467 | 1160 | 32 | PASS |
| TalhaMonoNF-BoldItalic.otf | 14467 | 1160 | 13 | PASS |
| TalhaMonoNF-Italic.otf | 14467 | 1160 | 13 | PASS |
| TalhaMonoNF-Regular.otf | 14467 | 1160 | 32 | PASS |
| TalhaMonoText-Italic.otf | 3639 | 1160 | 13 | PASS |
| TalhaMonoText-Regular.otf | 3639 | 1160 | 32 | PASS |
| TalhaMonoTextNF-Italic.otf | 14467 | 1160 | 13 | PASS |
| TalhaMonoTextNF-Regular.otf | 14467 | 1160 | 32 | PASS |
| TalhaMonoWide-Bold.otf | 3639 | 1320 | 32 | PASS |
| TalhaMonoWide-BoldItalic.otf | 3639 | 1320 | 13 | PASS |
| TalhaMonoWide-Italic.otf | 3639 | 1320 | 13 | PASS |
| TalhaMonoWide-Regular.otf | 3639 | 1320 | 32 | PASS |
| TalhaMonoWideNF-Bold.otf | 14467 | 1320 | 32 | PASS |
| TalhaMonoWideNF-BoldItalic.otf | 14467 | 1320 | 13 | PASS |
| TalhaMonoWideNF-Italic.otf | 14467 | 1320 | 13 | PASS |
| TalhaMonoWideNF-Regular.otf | 14467 | 1320 | 32 | PASS |

Checks: beta.4 version; unchanged Unicode coverage and glyph indices; every advance unchanged; GSUB preserved; no missing glyphs and fixed cells in reading/code/diacritic samples; HarfBuzz activation of swsh, titl and liga; new glyph line containment; ornament cell containment. NF copies retain text CFF programs, hint parameters, GSUB and GPOS. All icon CFF programs remain byte-identical across the naming correction.

The full build also checks every glyph against Windows clipping metrics. [Machine-readable results](measurements/candidate-audit.json).
