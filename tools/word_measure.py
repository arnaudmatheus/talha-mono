"""Native-size spacing measurements from complete shaped words and code.

python tools/word_measure.py --font Beta5=build/TalhaMono-Regular.otf --compare-spacing
"""

import argparse
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import TypedDict

import numpy as np

from run_raster import RasterRun, RunRasterizer

READING_CORPUS = (
    "tipiti",
    "antigo",
    "Estrada",
    "filter",
    "list",
    "minimum",
    "little",
    "initiator",
    "runtime",
    "filming",
    "milli",
    "illiterate",
    "tipiti antigo Estrada",
    "a letra tem ritmo",
    "mi\u0303\u0301 ml\u0323",
    "if item != nil { filter(list, 1); }",
)


class ContextGap(TypedDict):
    left: str
    right: str
    word_boundary: bool
    mean_gap_px: float | None
    overlap_pixels: int


class WordMeasurement(TypedDict):
    text: str
    size_px: int
    advance_px: float
    mean_gap_px: float | None
    cv: float | None
    features: dict[str, int]
    gaps: list[ContextGap]
    glyphs: list[dict[str, object]]


def mask_gap(left: np.ndarray, right: np.ndarray) -> tuple[float | None, int]:
    """Rowwise empty pixels between two run-cluster masks; e.g. ``mask_gap(left, right)``."""
    first, second = left > 76, right > 76
    distances = []
    for red, green in zip(first, second):
        a, b = np.flatnonzero(red), np.flatnonzero(green)
        if a.size and b.size:
            distances.append(int(b.min() - a.max() - 1))
    distance = round(float(np.mean(distances)), 4) if distances else None
    return distance, int(np.count_nonzero(first & second))


def run_gaps(text: str, run: RasterRun) -> list[ContextGap]:
    """Measure adjacent ink clusters, including gaps across spaces; e.g. ``run_gaps(text, run)``."""
    starts = list(run.masks)
    labels = {
        start: text[start:end] for start, end in zip(starts, starts[1:] + [len(text)])
    }
    visible = [start for start in starts if run.masks[start].any()]
    return [
        _context_gap(text, run, labels, left, right)
        for left, right in zip(visible, visible[1:])
    ]


def _context_gap(
    text: str, run: RasterRun, labels: dict[int, str], left: int, right: int
) -> ContextGap:
    distance, overlap = mask_gap(run.masks[left], run.masks[right])
    boundary = any(character.isspace() for character in text[left:right])
    return ContextGap(
        left=labels[left],
        right=labels[right],
        word_boundary=boundary,
        mean_gap_px=distance,
        overlap_pixels=overlap,
    )


def measure_word(
    raster: RunRasterizer, text: str, px: int, features: dict[str, int]
) -> WordMeasurement:
    """Keep full-run shaping while measuring each gap; e.g. ``measure_word(r, 'tipiti', 15, {'calt': 1})``."""
    run = raster.render(text, px, features)
    gaps = run_gaps(text, run)
    average, cv = _gap_statistics(gaps)
    return WordMeasurement(
        text=text,
        size_px=px,
        advance_px=round(run.advance_px, 4),
        mean_gap_px=average,
        cv=cv,
        features=dict(features),
        gaps=gaps,
        glyphs=[asdict(glyph) for glyph in run.glyphs],
    )


def _gap_statistics(gaps: list[ContextGap]) -> tuple[float | None, float | None]:
    values = [
        gap["mean_gap_px"]
        for gap in gaps
        if not gap["word_boundary"] and gap["mean_gap_px"] is not None
    ]
    average = float(np.mean(values)) if values else None
    cv = float(np.std(values) / average) if average and average > 0 else None
    return (
        round(average, 4) if average is not None else None,
        round(cv, 4) if cv is not None else None,
    )


def feature_settings(value: str) -> dict[str, int]:
    """Parse explicit OpenType settings; e.g. ``feature_settings('calt=1,ss11=0')``."""
    settings: dict[str, int] = {}
    for token in value.split(","):
        if not re.fullmatch(r"[A-Za-z0-9]{4}=[0-9]+", token):
            raise argparse.ArgumentTypeError(
                f"{token!r}: expected four-character tag=nonnegative integer"
            )
        tag, number = token.split("=")
        settings[tag] = int(number)
    return settings


def word_measure_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", action="append", required=True, help="LABEL=PATH")
    parser.add_argument(
        "--features", type=feature_settings, default=feature_settings("calt=1")
    )
    parser.add_argument(
        "--compare-spacing", action="store_true", help="Compare ss11 off/on"
    )
    parser.add_argument("--sizes", type=int, nargs="+", default=[12, 15, 20])
    parser.add_argument(
        "--text", action="append", help="A complete single-line text run"
    )
    parser.add_argument("--out", type=Path, default=Path("build/word-measurements"))
    return parser.parse_args(argv)


def word_measurements(args: argparse.Namespace) -> dict[str, list[WordMeasurement]]:
    results = {}
    for spec in args.font:
        label, separator, filename = spec.partition("=")
        if not separator or not label or not filename:
            raise ValueError(f"{spec!r}: expected LABEL=PATH")
        raster = RunRasterizer(Path(filename))
        modes = (0, 1) if args.compare_spacing else (args.features.get("ss11", 0),)
        for enabled in modes:
            features = dict(args.features, ss11=enabled)
            key = f"{label} / ss11={enabled}"
            results[key] = [
                measure_word(raster, text, px, features)
                for text in (args.text or READING_CORPUS)
                for px in args.sizes
            ]
    return results


def word_markdown(results: dict[str, list[WordMeasurement]]) -> str:
    """Summarize word diagnostics with full-run raster provenance; e.g. ``word_markdown(results)``."""
    lines = [
        "# Whole-run spacing measurements",
        "",
        "HarfBuzz shapes each entire string; FreeType renders native pixels with light hinting and no forced autohint. CV is diagnostic, not a reading-speed score.",
        "",
        "| Font / feature | Text | Size | Mean internal gap | CV | Overlap pixels |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for label, words in results.items():
        for word in words:
            overlaps = sum(gap["overlap_pixels"] for gap in word["gaps"])
            text = word["text"].replace("|", "\\|")
            lines.append(
                f"| {label} | {text} | {word['size_px']} | {word['mean_gap_px']} | {word['cv']} | {overlaps} |"
            )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    """Write reproducible full-context metrics; e.g. ``main(['--font', 'trial=font.otf'])``."""
    args = word_measure_args(argv)
    results = word_measurements(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix(".json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n"
    )
    args.out.with_suffix(".md").write_text(word_markdown(results))
    print(f"Measured {len(results)} font/feature combinations: {args.out}")


if __name__ == "__main__":
    main()
