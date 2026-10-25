"""Measure drawing and SS11 changes as four separate native-size conditions."""

import argparse
import json
import statistics
from pathlib import Path
from typing import TypedDict

from run_raster import RunRasterizer
from spacing_review import REVIEW_CORPUS, SpacingScore, spacing_score
from word_measure import READING_CORPUS, measure_word

CANDIDATE_CORPUS = READING_CORPUS + REVIEW_CORPUS + ("mĺm mľm młm", "it̃́p", "łódź 1lI")


class CandidateCase(TypedDict):
    face: str
    text: str
    size_px: int
    baseline_off: SpacingScore
    baseline_on: SpacingScore
    candidate_off: SpacingScore
    candidate_on: SpacingScore


def candidate_case(
    old: RunRasterizer, new: RunRasterizer, face: str, text: str, px: int
) -> CandidateCase:
    off, on = {"calt": 1, "liga": 1, "ss11": 0}, {"calt": 1, "liga": 1, "ss11": 1}
    return CandidateCase(
        face=face,
        text=text,
        size_px=px,
        baseline_off=spacing_score(measure_word(old, text, px, off)),
        baseline_on=spacing_score(measure_word(old, text, px, on)),
        candidate_off=spacing_score(measure_word(new, text, px, off)),
        candidate_on=spacing_score(measure_word(new, text, px, on)),
    )


def candidate_safety_errors(cases: list[CandidateCase]) -> list[str]:
    """Allow intended outline changes while guarding columns and collisions; e.g. ``candidate_safety_errors(cases)``."""
    errors = []
    for case in cases:
        label = f"{case['face']} / {case['text']!r} / {case['size_px']} px"
        scores = [
            case[key]
            for key in ("baseline_off", "baseline_on", "candidate_off", "candidate_on")
        ]
        if len({score["advance_px"] for score in scores}) != 1:
            errors.append(label + ": fixed advance changed")
        for baseline, candidate in (
            (case["baseline_off"], case["candidate_off"]),
            (case["baseline_on"], case["candidate_on"]),
        ):
            if candidate["overlap_pixels"] > baseline["overlap_pixels"]:
                errors.append(label + ": cross-cluster overlap increased")
    return errors


def measure_candidate_fonts(base: Path, candidate: Path) -> list[CandidateCase]:
    """Compare ten physical styles under the same rendering conditions; e.g. ``measure_candidate_fonts(old, new)``."""
    cases: list[CandidateCase] = []
    for path in sorted(candidate.glob("TalhaMono*.otf")):
        if "NF-" in path.name:
            continue
        old, new = RunRasterizer(base / path.name), RunRasterizer(path)
        cases += [
            candidate_case(old, new, path.stem, text, px)
            for text in CANDIDATE_CORPUS
            for px in (12, 15, 20)
        ]
    if not cases:
        raise ValueError(f"{candidate}: expected ordinary Talha Mono candidate fonts")
    return cases


def _candidate_mean(cases: list[CandidateCase], key: str) -> str:
    choices = {
        name: [case[name]["cv"] for case in cases]
        for name in ("baseline_off", "baseline_on", "candidate_off", "candidate_on")
    }
    values = [value for value in choices[key] if value is not None]
    return f"{statistics.mean(values):.4f}" if values else "n/a"


def candidate_markdown(cases: list[CandidateCase]) -> str:
    """Separate letterform and spacing diagnostics; e.g. ``candidate_markdown(cases)``."""
    lines = [
        "# Complete candidate: four-condition native measurements",
        "",
        "HarfBuzz/FreeType at 12/15/20 px; calt and liga on. Mean gap CV is diagnostic, not a reading-speed score.",
        "",
        "| Face | Cases | Beta.6 off | Beta.6 SS11 | Refined off | Refined SS11 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for face in sorted({case["face"] for case in cases}):
        lines.append(_candidate_face_row(cases, face))
    errors = candidate_safety_errors(cases)
    lines += [
        "",
        f"Column/overlap checks: {'FAIL' if errors else 'PASS'} ({len(errors)} errors).",
        *errors,
    ]
    return "\n".join(lines) + "\n"


def _candidate_face_row(cases: list[CandidateCase], face: str) -> str:
    subset = [case for case in cases if case["face"] == face]
    means = [
        _candidate_mean(subset, key)
        for key in ("baseline_off", "baseline_on", "candidate_off", "candidate_on")
    ]
    return f"| {face} | {len(subset)} | " + " | ".join(means) + " |"


def main(argv: list[str] | None = None) -> None:
    """Write a review without treating changed glyph pixels as regressions; e.g. ``main(['--base', 'old', '--new', 'new'])``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument(
        "--out", type=Path, default=Path("build/candidate-measurements")
    )
    args = parser.parse_args(argv)
    cases = measure_candidate_fonts(args.base, args.new)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix(".json").write_text(
        json.dumps(cases, indent=2, ensure_ascii=False) + "\n"
    )
    args.out.with_suffix(".md").write_text(candidate_markdown(cases))
    if errors := candidate_safety_errors(cases):
        raise SystemExit(f"Candidate measurement failed: {len(errors)} safety errors")
    print(f"Measured {len(cases)} cases / {4 * len(cases)} conditions")


if __name__ == "__main__":
    main()
