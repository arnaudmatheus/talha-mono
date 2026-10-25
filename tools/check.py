#!/usr/bin/env python3
"""Regression gate: the rule every release has followed, run by CI.

python check.py --base DIR --new DIR [--report PATH] [--tolerance 0.01]
               [--waivers tools/gate_waivers.json]

Measures each family in --new against the font of the same name in --base
(tools/measure.py: Pango/FreeType, 12/15/20 px) and fails if any confusable
pair got more than --tolerance worse. Spacing evenness and sharpness are
reported, not gated: a design change may move them on purpose, and the
roadmap records why. A family with no baseline yet (a new family) is
reported and skipped. A regression the user accepted on purpose for this
version (tools/gate_waivers.py) is reported and does not fail the gate.

The report is Markdown: written to --report, and to GitHub's job summary
when $GITHUB_STEP_SUMMARY is set."""

import argparse, json, os, subprocess, sys, tempfile
from pathlib import Path
from metric_types import FontMetrics
from typing import Sequence, cast
from gate_waivers import WAIVERS_PATH, Waiver, build_version, find_waiver, load_waivers

HERE = Path(__file__).resolve().parent
# (label, roman file, italic file or None): the roman/italic pair is measured
# together so roman/italic similarity is checked too.
FAMILIES = [
    ("Talha Mono", "TalhaMono-Regular.otf", "TalhaMono-Italic.otf"),
    ("Talha Mono Italic", "TalhaMono-Italic.otf", None),
    ("Talha Mono Bold", "TalhaMono-Bold.otf", "TalhaMono-BoldItalic.otf"),
    ("Talha Mono Wide", "TalhaMonoWide-Regular.otf", "TalhaMonoWide-Italic.otf"),
    ("Talha Mono Text", "TalhaMonoText-Regular.otf", "TalhaMonoText-Italic.otf"),
    ("Talha Mono Bold Italic", "TalhaMono-BoldItalic.otf", None),
    ("Talha Mono Wide Italic", "TalhaMonoWide-Italic.otf", None),
    ("Talha Mono Wide Bold", "TalhaMonoWide-Bold.otf", None),
    ("Talha Mono Wide Bold Italic", "TalhaMonoWide-BoldItalic.otf", None),
    ("Talha Mono Text Italic", "TalhaMonoText-Italic.otf", None),
]


FamilyPair = tuple[str, str | None, str | None]
Regression = tuple[int | str, str, float]
Accepted = tuple[str, int | str, str, float, Waiver]


def mean(d: dict[str, float]) -> float:
    return sum(d.values()) / len(d)


def _check_args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--new", required=True, type=Path)
    ap.add_argument("--report", type=Path, default=Path("check-report.md"))
    ap.add_argument("--tolerance", type=float, default=0.01)
    ap.add_argument("--waivers", type=Path, default=WAIVERS_PATH)
    return ap.parse_args(argv)


def _font_spec(directory: Path, roman: str, italic: str | None) -> str:
    spec = str(directory / roman)
    if italic and (directory / italic).exists():
        spec += ":" + str(directory / italic)
    return spec


def _comparison_specs(base: Path, new: Path) -> tuple[list[str], list[FamilyPair]]:
    specs: list[str] = []
    pairs: list[FamilyPair] = []
    for label, roman, italic in FAMILIES:
        if not (new / roman).exists():
            continue
        if not (base / roman).exists():
            pairs.append((label, None, None))
            continue
        i = len(pairs)
        specs += [
            "--font",
            f"base{i}={_font_spec(base, roman, italic)}",
            "--font",
            f"new{i}={_font_spec(new, roman, italic)}",
        ]
        pairs.append((label, f"base{i}", f"new{i}"))
    return specs, pairs


def _run_measurements(specs: list[str]) -> dict[str, FontMetrics]:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "m"
        subprocess.run(
            [sys.executable, str(HERE / "measure.py"), *specs, "--out", str(out)],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        return cast(
            dict[str, FontMetrics], json.loads(out.with_suffix(".json").read_text())
        )


def _worse_pairs(
    before: FontMetrics, after: FontMetrics, tolerance: float
) -> list[Regression]:
    return [
        (px, pair, after["confusability"][px][pair] - scores[pair])
        for px, scores in before["confusability"].items()
        for pair in scores
        if after["confusability"][px][pair] - scores[pair] > tolerance + 1e-9
    ]


def _regression_cell(worse: list[Regression]) -> str:
    top = sorted(worse, key=lambda w: -w[2])
    cell = ", ".join(f"`{p}` {px} px +{d:.3f}" for px, p, d in top[:8]) or "none"
    if len(top) > 8:
        cell += f", and {len(top) - 8} more"
    return cell


def _comparison_row(
    label: str, rb: FontMetrics, rn: FontMetrics, worse: list[Regression]
) -> str:
    conf = " / ".join(
        f"{mean(rb['confusability'][px]):.3f} → {mean(rn['confusability'][px]):.3f}"
        for px in ("12", "15", "20")
    )
    cv = f"{rb['spacing']['cv']} → {rn['spacing']['cv']}"
    sh = f"{rb['sharpness']['hintslight']} → {rn['sharpness']['hintslight']}"
    return f"| {label} | {conf} | {cv} | {sh} | {_regression_cell(worse)} |"


def _report_heading(tolerance: float) -> list[str]:
    return [
        "# Talha Mono: regression check",
        "",
        f"Each family against its baseline. Fails if a confusable pair is more than "
        f"{tolerance} worse (similarity; lower is easier to tell apart).",
        "",
        "| Family | Confusability 12 / 15 / 20 px | Spacing CV | Sharpness 12 px | Pairs worse |",
        "|---|---|---|---|---|",
    ]


def _split_waived(
    label: str, worse: list[Regression], waivers: Sequence[Waiver]
) -> tuple[list[Regression], list[Accepted]]:
    """(regressions that still fail, regressions a waiver accepts)."""
    open_: list[Regression] = []
    accepted: list[Accepted] = []
    for px, pair, delta in worse:
        w = find_waiver(waivers, label, px, pair, delta)
        if w is None:
            open_.append((px, pair, delta))
        else:
            accepted.append((label, px, pair, delta, w))
    return open_, accepted


def _accepted_lines(accepted: list[Accepted]) -> list[str]:
    if not accepted:
        return []
    lines = ["", "Accepted on purpose (tools/gate_waivers.json):", ""]
    lines += [
        f"- {label}: `{pair}` {px} px +{delta:.3f} (allowed +{w.max_delta:.3f})"
        for label, px, pair, delta, w in accepted
    ]
    reasons = sorted({w.reason for *_, w in accepted})
    return lines + [""] + [f"Why: {r}" for r in reasons]


def regression_report(
    res: dict[str, FontMetrics],
    pairs: list[FamilyPair],
    tolerance: float,
    waivers: Sequence[Waiver] = (),
) -> tuple[str, bool]:
    """Summarize regressions; e.g. ``report, failed = regression_report(results, pairs, 0.01)``."""
    lines = _report_heading(tolerance)
    failed: list[tuple[str, int | str, str, float]] = []
    accepted: list[Accepted] = []
    for label, b, n in pairs:
        if b is None or n is None:
            lines.append(f"| {label} | no baseline (new family) | | | skipped |")
            continue
        worse, ok = _split_waived(
            label, _worse_pairs(res[b], res[n], tolerance), waivers
        )
        lines.append(_comparison_row(label, res[b], res[n], worse))
        failed += [(label, *w) for w in worse]
        accepted += ok
    lines += _accepted_lines(accepted) + [
        "",
        "**Result: "
        + ("FAIL**, " + f"{len(failed)} pair(s) worse." if failed else "pass.**"),
    ]
    return "\n".join(lines) + "\n", bool(failed)


def _publish_report(report: str, path: Path) -> None:
    path.write_text(report)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write(report)
    print(report)


def main(argv: list[str] | None = None) -> None:
    """Run the release gate; e.g. ``main(["--base", "fonts/otf", "--new", "build"])``."""
    args = _check_args(argv)
    specs, pairs = _comparison_specs(args.base, args.new)
    waivers = load_waivers(args.waivers, build_version())
    report, failed = regression_report(
        _run_measurements(specs), pairs, args.tolerance, waivers
    )
    _publish_report(report, args.report)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
