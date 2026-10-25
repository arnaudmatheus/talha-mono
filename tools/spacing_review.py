"""Compare optional spacing against beta.5 and feature-off pixels.

python tools/spacing_review.py --base build/beta5-baseline --new build
"""

import argparse
import json
import statistics
from pathlib import Path
from typing import TypedDict

import numpy as np

from run_raster import RunRasterizer
from word_measure import READING_CORPUS, WordMeasurement, measure_word

# Kept separate from the original diagnostic corpus before guard evaluation.
REVIEW_CORPUS = (
    "latitude",
    "limite",
    "trilho",
    "ritual",
    "literatura",
    "notifica",
    "interface",
    "iteration",
    "utility",
    "literal",
    "initialize",
    "trivial",
    "retirar",
    "futuro",
    "altura",
    "abrigo",
    "organizar",
    "pintura",
    "silêncio",
    "memória",
    "função",
    "vértice",
    "aceitação",
    "pão",
    "ação",
    "leitura",
    "installation",
    "title",
    "return",
    "terminal",
    "A leitura tem altura e ritmo.",
    "const title = items.filter(valid);",
)
SIZES = (12, 15, 20)
OFF, ON = {"calt": 1, "ss11": 0}, {"calt": 1, "ss11": 1}


class SpacingScore(TypedDict):
    cv: float | None
    advance_px: float
    overlap_pixels: int


class SpacingCase(TypedDict):
    face: str
    corpus: str
    text: str
    size_px: int
    baseline_off: SpacingScore
    baseline_on: SpacingScore
    candidate_on: SpacingScore
    default_pixels_equal: bool


def spacing_score(word: WordMeasurement) -> SpacingScore:
    """Keep the review compact while preserving safety metrics; e.g. ``spacing_score(word)``."""
    return SpacingScore(
        cv=word["cv"],
        advance_px=word["advance_px"],
        overlap_pixels=sum(gap["overlap_pixels"] for gap in word["gaps"]),
    )


def compare_spacing_case(
    before: RunRasterizer,
    after: RunRasterizer,
    face: str,
    corpus: str,
    text: str,
    px: int,
) -> SpacingCase:
    return SpacingCase(
        face=face,
        corpus=corpus,
        text=text,
        size_px=px,
        baseline_off=spacing_score(measure_word(before, text, px, OFF)),
        baseline_on=spacing_score(measure_word(before, text, px, ON)),
        candidate_on=spacing_score(measure_word(after, text, px, ON)),
        default_pixels_equal=_default_pixels_equal(before, after, text, px),
    )


def _default_pixels_equal(
    before: RunRasterizer, after: RunRasterizer, text: str, px: int
) -> bool:
    return bool(
        np.array_equal(
            before.render(text, px, OFF).image, after.render(text, px, OFF).image
        )
    )


def review_spacing_fonts(before: Path, after: Path) -> list[SpacingCase]:
    """Evaluate original and separate review strings in all plain faces; e.g. ``review_spacing_fonts(old, new)``."""
    cases: list[SpacingCase] = []
    corpora = (("original", READING_CORPUS), ("review", REVIEW_CORPUS))
    for source in sorted(after.glob("TalhaMono*.otf")):
        if "NF-" in source.name:
            continue
        old, new = RunRasterizer(before / source.name), RunRasterizer(source)
        cases.extend(
            compare_spacing_case(old, new, source.stem, corpus, text, px)
            for corpus, texts in corpora
            for text in texts
            for px in SIZES
        )
    if not cases:
        raise ValueError(f"{after}: expected built Talha Mono OTF faces")
    return cases


def spacing_safety_errors(cases: list[SpacingCase]) -> list[str]:
    """Gate advances, default pixels and added overlaps; e.g. ``spacing_safety_errors(cases)``."""
    errors = []
    for case in cases:
        label = f"{case['face']} / {case['text']!r} / {case['size_px']} px"
        old, new = case["baseline_off"], case["candidate_on"]
        if not case["default_pixels_equal"]:
            errors.append(label + ": feature-off pixels changed")
        if old["advance_px"] != new["advance_px"]:
            errors.append(label + ": fixed advance changed")
        if new["overlap_pixels"] > old["overlap_pixels"]:
            errors.append(label + ": cross-cluster overlap increased")
    return errors


def spacing_deltas(cases: list[SpacingCase], target: str) -> list[float]:
    """Compare only defined CV diagnostics; e.g. ``spacing_deltas(cases, 'baseline_on')``."""
    if target not in ("baseline_off", "baseline_on"):
        raise ValueError(f"{target!r}: expected baseline_off or baseline_on")
    deltas = []
    for case in cases:
        before = (
            case["baseline_off"] if target == "baseline_off" else case["baseline_on"]
        )
        old, new = before["cv"], case["candidate_on"]["cv"]
        if old is not None and new is not None:
            deltas.append(round(new - old, 4))
    return deltas


def _review_row(label: str, cases: list[SpacingCase]) -> str:
    delta = spacing_deltas(cases, "baseline_on")
    old_worse = sum(
        round(case["baseline_on"]["cv"] - case["baseline_off"]["cv"], 4) > 0.0001
        for case in cases
        if case["baseline_on"]["cv"] is not None
        and case["baseline_off"]["cv"] is not None
    )
    worse = sum(value > 0.0001 for value in spacing_deltas(cases, "baseline_off"))
    better, regressed = sum(d < -0.0001 for d in delta), sum(d > 0.0001 for d in delta)
    average = f"{statistics.mean(delta):+.5f}" if delta else "n/a"
    return f"| {label} | {len(cases)} | {old_worse} → {worse} | {better} / {regressed} | {average} |"


def spacing_review_markdown(cases: list[SpacingCase]) -> str:
    """Separate per-style original/review results; e.g. ``spacing_review_markdown(cases)``."""
    lines = [
        "# Contextual spacing review",
        "",
        "Native 12/15/20 px HarfBuzz + FreeType. CV is diagnostic, not a reading-speed score. Differences within 0.0001 count as unchanged.",
        "",
        "| Corpus / face | Cases | Worse than off: beta.5 → candidate | Better / worse than beta.5 on | Mean CV change vs beta.5 on |",
        "|---|---:|---:|---:|---:|",
    ]
    for corpus in ("original", "review"):
        lines.extend(_corpus_rows(cases, corpus))
    errors = spacing_safety_errors(cases)
    lines += [
        "",
        f"Safety checks: {'FAIL' if errors else 'PASS'} ({len(errors)} errors).",
        *errors,
    ]
    return "\n".join(lines) + "\n"


def _corpus_rows(cases: list[SpacingCase], corpus: str) -> list[str]:
    subset = [case for case in cases if case["corpus"] == corpus]
    lines = [
        _review_row(corpus + " / " + face, [c for c in subset if c["face"] == face])
        for face in sorted({case["face"] for case in subset})
    ]
    return lines + [_review_row(corpus + " / ALL", subset)]


def main(argv: list[str] | None = None) -> None:
    """Write measurements and fail unsafe changes; e.g. ``main(['--base', 'old', '--new', 'build'])``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("build/spacing-review"))
    args = parser.parse_args(argv)
    cases = review_spacing_fonts(args.base, args.new)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix(".json").write_text(
        json.dumps(cases, indent=2, ensure_ascii=False) + "\n"
    )
    args.out.with_suffix(".md").write_text(spacing_review_markdown(cases))
    if errors := spacing_safety_errors(cases):
        raise SystemExit(f"Spacing review failed: {len(errors)} safety errors")
    print(f"Compared {len(cases)} spacing cases: {args.out}")


if __name__ == "__main__":
    main()
