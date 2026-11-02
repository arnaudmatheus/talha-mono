# Status — 2026-11-01

## Working
- Talha Mono 1.0.0-beta.7, published as a GitHub pre-release on 2026-10-24.
- CI "Build and check" is green on `main` for the latest commit 37be012 (run 41366851345, 2026-11-01): pytest, five build jobs, the regression check and fontbakery QA. It is also green on the `v1.0.0-beta.7` tag.

## Unverified
- `pytest` was not run locally today: no environment on this machine has pytest installed. CI runs it.
- How beta.7 renders in real editors and terminals: caret, selection, tabs, fallback, SS11 run boundaries.
- SS11 contextual spacing as the default: there are only two blind ratings (both preferred it on). No blind letterform ratings were recorded for the refined `t/l/1`.

## Next
- Check beta.7 in a real editor and terminal: caret, selection, tabs, fallback and SS11 run boundaries.

## Evidence
- [ROADMAP.md](ROADMAP.md) "Next"; [docs/design/beta7.md](docs/design/beta7.md); [SPEC.md](SPEC.md); [FONTLOG.txt](FONTLOG.txt).
- The GitHub repo is `talha-mono`. The directory keeps the old name (renamed from Jandí Mono at beta.3).
