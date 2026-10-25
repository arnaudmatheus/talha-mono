"""Pango proofs and anonymous A/B samples for contextual features.

python tools/feature_proof.py --base build/beta4-baseline --new build
"""

import argparse
import json
import random
from pathlib import Path

from PIL import Image

from measure import Renderer
from reading_proof import (
    PAPER,
    READING_FACES,
    proof_label,
    proof_footer,
    reading_panel,
    reading_raster,
)

READING_PASSAGE = (
    "A letra tem ritmo, altura e proporção.\n"
    "O antigo tipiti fica perto da estrada.\n"
    "Read the little list from the runtime.\n"
    "if item != nil { filter(list, 1); }"
)


ACCENT_NOTE = "Default contextual shaping; fixed advances. Stacked and below marks now follow substituted bases."
SPACING_NOTES = (
    "Native 12 / 15 / 20 px. Compare at 100% zoom. SS11 changes ink placement; cell advances stay fixed.",
    "Opt-in treatment: compare whole words and prose before choosing it for sustained reading.",
)
READING_NOTE = "Compare at 100% zoom; note clarity and preference. Timing needs fresh passages and counterbalanced order."


def feature_sheet(title: str, height: int, left: str, right: str) -> Image.Image:
    canvas = Image.new("RGB", (1260, height), PAPER)
    proof_label(canvas, "TALHA MONO / " + title, 40, 35, 25)
    proof_label(canvas, left, 40, 95)
    proof_label(canvas, right, 670, 95)
    return canvas


def accent_feature_proof(before: Path, after: Path) -> Image.Image:
    """Actual Pango marks and accented styles with healing on; e.g. ``accent_feature_proof(old, new)``."""
    canvas = feature_sheet(
        "CONTEXTUAL ACCENT CORRECTION", 730, "Beta.4 / calt on", "Beta.5 / calt on"
    )
    samples = ("mĩ́", "mî́", "mḷ", "mĩm mĵm")
    for directory, x in ((before, 40), (after, 670)):
        raster = Renderer(str(directory / "TalhaMono-Regular.otf"))
        for index, text in enumerate(samples):
            canvas.paste(
                reading_raster(raster, text, 80, features="calt=1,ss11=0"),
                (x, 145 + index * 125),
            )
    proof_label(canvas, ACCENT_NOTE, 40, 680, 16)
    return canvas


def spacing_feature_proof(fonts: Path) -> Image.Image:
    """Same font and native sizes, changing only SS11; e.g. ``spacing_feature_proof(fonts)``."""
    canvas = feature_sheet(
        "CONTEXTUAL SPACING / BETA.5", 1460, "SS11 off", "SS11 on / 40-unit shifts"
    )
    for index, face in enumerate(READING_FACES):
        y = 155 + index * 240
        proof_label(canvas, face.removesuffix(".otf"), 40, y)
        raster = Renderer(str(fonts / face))
        for enabled, x in ((0, 40), (1, 670)):
            reading_panel(canvas, raster, x, y + 35, f"calt=1,ss11={enabled}")
    proof_footer(canvas, SPACING_NOTES, 1380)
    return canvas


def blind_reading_proof(fonts: Path, modes: list[int]) -> Image.Image:
    """Anonymous personal comparison, with the assignment stored separately; e.g. ``blind_reading_proof(fonts, [1, 0])``."""
    canvas = feature_sheet("PERSONAL READING COMPARISON", 650, "Sample A", "Sample B")
    for mode, x in zip(modes, (40, 670)):
        for index, face in enumerate((READING_FACES[0], READING_FACES[-1])):
            raster = Renderer(str(fonts / face))
            proof_label(
                canvas, "Regular" if index == 0 else "Text", x, 155 + index * 200
            )
            image = reading_raster(
                raster, READING_PASSAGE, 15, features=f"calt=1,ss11={mode}"
            )
            canvas.paste(image, (x, 190 + index * 200))
    proof_label(canvas, READING_NOTE, 40, 590, 16)
    return canvas


def feature_proof_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("docs/design"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Write review artifacts and an A/B key; e.g. ``main(['--base', 'baseline', '--new', 'build'])``."""
    args = feature_proof_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    accent_feature_proof(args.base, args.new).save(
        args.out / "beta5-context-accents.png"
    )
    spacing_feature_proof(args.new).save(args.out / "beta5-context-spacing.png")
    modes = [0, 1]
    random.Random(20261022).shuffle(modes)
    blind_reading_proof(args.new, modes).save(args.out / "beta5-reading-comparison.png")
    (args.out / "measurements").mkdir(exist_ok=True)
    key = {label: {"ss11": mode} for label, mode in zip(("A", "B"), modes)}
    (args.out / "measurements/beta5-reading-key.json").write_text(
        json.dumps(key, indent=2) + "\n"
    )
    print(f"Contextual feature proofs: {args.out}")


if __name__ == "__main__":
    main()
