"""Evaluate the cross-style stem study without promoting any trial drawing.

python tools/stem_review.py --base build --trials build/stem-trials
"""

import argparse
import json
from pathlib import Path
from typing import TypedDict

from fontTools.ttLib import TTFont

from measure import Renderer, confusability
from pilot_validation import (
    assert_pilot_resources,
    changed_charstrings,
)
from glyph_writer import GlyphWriter
from stem_study import STEM_NAMES

PairScores = dict[int | str, dict[str, float]]


class StemRegression(TypedDict):
    size: int | str
    pair: str
    increase: float


class StemResult(TypedDict):
    face: str
    variant: str
    baseline: PairScores
    control: PairScores
    trial: PairScores
    control_matches: bool
    failed_pairs: list[StemRegression]
    result: str


def stem_regressions(before: PairScores, after: PairScores) -> list[StemRegression]:
    """Apply the existing 0.01 pair limit without new waivers; e.g. ``stem_regressions(old, new)``."""
    return [
        StemRegression(size=px, pair=pair, increase=round(score - before[px][pair], 3))
        for px, pairs in after.items()
        for pair, score in pairs.items()
        if score - before[px][pair] > 0.010000001
    ]


def audit_stem_font(before_path: Path, after_path: Path) -> None:
    """Protect advances, other drawings, features and shared hints; e.g. ``audit_stem_font(old, trial)``."""
    with TTFont(before_path) as before, TTFont(after_path) as after:
        changed = changed_charstrings(before, after)
        if not changed <= set(STEM_NAMES):
            raise ValueError(
                f"{after_path}: changed {sorted(changed)}, expected only t/l/one"
            )
        assert_pilot_resources(before, after)
        _stem_bounds(before, after)
        _stem_tables(before, after)
        _stem_metrics(before, after)


def _stem_bounds(before: TTFont, after: TTFont) -> None:
    cell = before["hmtx"]["A"][0]
    original, updated = GlyphWriter(before, cell), GlyphWriter(after, cell)
    for name in STEM_NAMES:
        old, new = original.bounds(name), updated.bounds(name)
        if new[1] < before["hhea"].descent or new[3] > before["hhea"].ascent:
            raise ValueError(f"{name}/{new}: expected ink within original line metrics")
        # Corsiva ascenders already overhang: preserve their existing allowance.
        if new[0] < min(0, old[0]) - 1 or new[2] > max(cell, old[2]) + 1:
            raise ValueError(
                f"{name}/{new}: expected no added cell overhang beyond {old}"
            )


def _stem_tables(before: TTFont, after: TTFont) -> None:
    if before.getGlyphOrder() != after.getGlyphOrder():
        raise ValueError("Stem glyph order changed: expected identical glyph IDs")
    for tag in before.reader.keys():
        if (
            tag not in ("CFF ", "head", "hmtx")
            and before.reader[tag] != after.reader[tag]
        ):
            raise ValueError(f"{tag}: expected untouched nonoutline tables")


def _stem_metrics(before: TTFont, after: TTFont) -> None:
    for name, (advance, lsb) in before["hmtx"].metrics.items():
        expected = (advance, after["hmtx"][name][1] if name in STEM_NAMES else lsb)
        if after["hmtx"][name] != expected:
            raise ValueError(
                f"{name}: expected original advance and nontrial sidebearing"
            )


def review_stem_face(source: Path, trials: Path, variant: str = "20") -> StemResult:
    control, trial = (trials / name / source.name for name in ("0", variant))
    audit_stem_font(source, control)
    audit_stem_font(source, trial)
    baseline = confusability(Renderer(str(source)))
    zero, changed = (confusability(Renderer(str(path))) for path in (control, trial))
    regressions = stem_regressions(baseline, changed)
    return StemResult(
        face=source.name,
        variant=variant,
        baseline=baseline,
        control=zero,
        trial=changed,
        control_matches=zero == baseline,
        failed_pairs=regressions,
        result="PASS" if not regressions and zero == baseline else "REJECT",
    )


def stem_review_markdown(results: list[StemResult]) -> str:
    """Expose every rejected pair and the control result; e.g. ``stem_review_markdown(results)``."""
    lines = [
        "# Cross-style t/l/1 study",
        "",
        "Isolated drawing study at 12/15/20 px. Contextual and accented families are unchanged; these are not installable candidates.",
        "Variant: "
        + (results[0]["variant"] if results else "none")
        + ". 20 means t/l/1 at 20 units; 20-flag10 keeps t/l at 20 and reduces the 1 flag to 10.",
        "",
        "| Face | Zero-strength control | Pair guard | Regressions > 0.01 |",
        "|---|---|---|---|",
    ]
    lines += [_stem_row(result) for result in results]
    return "\n".join(lines) + "\n"


def _stem_row(result: StemResult) -> str:
    regressions = (
        ", ".join(
            f"{r['pair']} {r['size']} px +{r['increase']:.3f}"
            for r in result["failed_pairs"]
        )
        or "none"
    )
    control = "identical scores" if result["control_matches"] else "FAIL"
    return f"| {result['face']} | {control} | {result['result']} | {regressions} |"


def main(argv: list[str] | None = None) -> None:
    """Keep rejected experiments reviewable; e.g. ``main(['--base', 'build', '--trials', 'build/stem-trials'])``."""
    args = _stem_review_args(argv)
    sources = sorted(
        path for path in args.base.glob("TalhaMono*.otf") if "NF-" not in path.name
    )
    if not sources:
        raise ValueError(f"{args.base}: expected built Talha Mono faces")
    results = [
        review_stem_face(source, args.trials, args.variant) for source in sources
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix(".json").write_text(json.dumps(results, indent=2) + "\n")
    args.out.with_suffix(".md").write_text(stem_review_markdown(results))
    if not all(result["control_matches"] for result in results):
        raise SystemExit(
            "Stem control mismatch: expected unchanged scores in every face"
        )
    accepted = sum(row["result"] == "PASS" for row in results)
    print(f"Reviewed {len(results)} faces; {accepted} pass the trial guard")


def _stem_review_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=Path("build"))
    parser.add_argument("--trials", type=Path, default=Path("build/stem-trials"))
    parser.add_argument("--variant", choices=("20", "20-flag10"), default="20")
    parser.add_argument(
        "--out", type=Path, default=Path("docs/design/measurements/beta6-stem-study")
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    main()
