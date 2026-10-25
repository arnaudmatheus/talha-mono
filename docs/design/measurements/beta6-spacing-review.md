# Contextual spacing review

Native 12/15/20 px HarfBuzz + FreeType. CV is diagnostic, not a reading-speed score. Differences within 0.0001 count as unchanged.

| Corpus / face | Cases | Worse than off: beta.5 → candidate | Better / worse than beta.5 on | Mean CV change vs beta.5 on |
|---|---:|---:|---:|---:|
| original / TalhaMono-Bold | 48 | 2 → 2 | 3 / 12 | +0.00062 |
| original / TalhaMono-BoldItalic | 48 | 9 → 1 | 15 / 9 | -0.00184 |
| original / TalhaMono-Italic | 48 | 8 → 1 | 16 / 8 | -0.00119 |
| original / TalhaMono-Regular | 48 | 1 → 0 | 4 / 5 | -0.00010 |
| original / TalhaMonoText-Italic | 48 | 8 → 1 | 16 / 8 | -0.00140 |
| original / TalhaMonoText-Regular | 48 | 0 → 0 | 3 / 18 | +0.00129 |
| original / TalhaMonoWide-Bold | 48 | 3 → 2 | 6 / 7 | -0.00004 |
| original / TalhaMonoWide-BoldItalic | 48 | 8 → 0 | 17 / 7 | -0.00139 |
| original / TalhaMonoWide-Italic | 48 | 8 → 0 | 12 / 12 | -0.00047 |
| original / TalhaMonoWide-Regular | 48 | 1 → 1 | 3 / 6 | +0.00015 |
| original / ALL | 480 | 48 → 8 | 95 / 92 | -0.00044 |
| review / TalhaMono-Bold | 96 | 4 → 3 | 24 / 45 | +0.00231 |
| review / TalhaMono-BoldItalic | 96 | 15 → 0 | 50 / 19 | -0.00466 |
| review / TalhaMono-Italic | 96 | 17 → 0 | 54 / 20 | -0.00339 |
| review / TalhaMono-Regular | 96 | 2 → 1 | 28 / 31 | +0.00093 |
| review / TalhaMonoText-Italic | 96 | 16 → 2 | 48 / 26 | -0.00284 |
| review / TalhaMonoText-Regular | 96 | 7 → 1 | 32 / 36 | +0.00076 |
| review / TalhaMonoWide-Bold | 96 | 5 → 0 | 26 / 41 | +0.00070 |
| review / TalhaMonoWide-BoldItalic | 96 | 17 → 0 | 52 / 16 | -0.00317 |
| review / TalhaMonoWide-Italic | 96 | 18 → 0 | 52 / 18 | -0.00227 |
| review / TalhaMonoWide-Regular | 96 | 2 → 3 | 23 / 35 | +0.00162 |
| review / ALL | 960 | 103 → 10 | 389 / 287 | -0.00100 |

Safety checks: PASS (0 errors).
