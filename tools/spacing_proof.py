"""Native Pango review: ordinary spacing, beta.5 SS11 and refined SS11.

python tools/spacing_proof.py --base build/beta5-baseline --new build
"""

import argparse
import json
import random
from pathlib import Path

from PIL import Image

from measure import Renderer
from feature_proof import blind_reading_proof
from reading_proof import PAPER, proof_label, reading_raster

REVIEW_LINE = "tipiti antigo Estrada  filter little"
REVIEW_CODE = "if item != nil { filter(list, 1); }"


def _review_panel(
    canvas: Image.Image, font: Path, x: int, y: int, enabled: int
) -> None:
    raster = Renderer(str(font))
    features = f"calt=1,ss11={enabled}"
    for index, size in enumerate((12, 15, 20)):
        proof_label(canvas, f"{size} px", x, y + index * 33, 13)
        canvas.paste(
            reading_raster(raster, REVIEW_LINE, size, features=features),
            (x + 48, y + index * 33),
        )
    canvas.paste(
        reading_raster(raster, REVIEW_CODE, 15, True, features), (x + 48, y + 103)
    )


def _spacing_headers(canvas: Image.Image) -> None:
    proof_label(canvas, "TALHA MONO / SPACING REFINEMENT / BETA.6", 40, 35, 25)
    headings = (
        "Ordinary spacing / SS11 off",
        "Beta.5 / SS11 on",
        "Beta.6 / guarded SS11 on",
    )
    for heading, x in zip(headings, (40, 660, 1280)):
        proof_label(canvas, heading, x, 95)
    proof_label(
        canvas,
        "Native pixels: compare at 100% zoom. Same cell advances; diagnostic tradeoffs remain.",
        40,
        canvas.height - 60,
        16,
    )


def spacing_review_proof(before: Path, after: Path) -> Image.Image:
    """Render all ten faces without scaling text pixels; e.g. ``spacing_review_proof(old, new)``."""
    faces = sorted(
        path.name for path in after.glob("TalhaMono*.otf") if "NF-" not in path.name
    )
    canvas = Image.new("RGB", (1900, 240 + 190 * len(faces)), PAPER)
    _spacing_headers(canvas)
    for index, face in enumerate(faces):
        y = 155 + index * 190
        proof_label(canvas, face.removesuffix(".otf"), 40, y)
        for directory, x, enabled in (
            (after, 40, 0),
            (before, 660, 1),
            (after, 1280, 1),
        ):
            _review_panel(canvas, directory / face, x, y + 30, enabled)
    return canvas


def main(argv: list[str] | None = None) -> None:
    """Write the three-column reading proof; e.g. ``main(['--base', 'old', '--new', 'build'])``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument(
        "--out", type=Path, default=Path("docs/design/beta6-spacing-review.png")
    )
    args = parser.parse_args(argv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    spacing_review_proof(args.base, args.new).save(args.out)
    _reading_review_files(args.new, args.out.parent)
    print(f"Spacing review proof: {args.out}")


def _reading_review_files(fonts: Path, output: Path) -> None:
    modes = [0, 1]
    random.Random(20261023).shuffle(modes)
    blind_reading_proof(fonts, modes).save(output / "beta6-reading-comparison.png")
    key = {label: {"ss11": mode} for label, mode in zip(("A", "B"), modes)}
    (output / "measurements").mkdir(exist_ok=True)
    (output / "measurements/beta6-reading-key.json").write_text(
        json.dumps(key, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
