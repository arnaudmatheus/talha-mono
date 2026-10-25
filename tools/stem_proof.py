"""Three-column native proof of the original and refined cross-style stem studies."""

import argparse
from pathlib import Path

from PIL import Image

from measure import Renderer
from reading_proof import PAPER, proof_label, reading_raster

STEM_FEATURES = "calt=0,ss11=0,liga=0"


def _stem_panel(canvas: Image.Image, path: Path, x: int, y: int) -> None:
    raster = Renderer(str(path))
    canvas.paste(reading_raster(raster, "t l 1 I", 60, features=STEM_FEATURES), (x, y))
    for index, px in enumerate((12, 15, 20)):
        proof_label(canvas, f"{px} px", x, y + 80 + index * 32, 13)
        canvas.paste(
            reading_raster(
                raster, "little  1 l I  filter tipiti", px, features=STEM_FEATURES
            ),
            (x + 48, y + 80 + index * 32),
        )


def cross_style_stem_proof(base: Path, trials: Path) -> Image.Image:
    """Show all ten physical styles, retaining native small pixels; e.g. ``cross_style_stem_proof(base, trials)``."""
    faces = sorted(
        path.name for path in base.glob("TalhaMono*.otf") if "NF-" not in path.name
    )
    canvas = Image.new("RGB", (1900, 260 + 225 * len(faces)), PAPER)
    _stem_proof_headings(canvas)
    for index, face in enumerate(faces):
        y = 155 + index * 225
        proof_label(canvas, face.removesuffix(".otf"), 40, y)
        for directory, x in (
            (base, 40),
            (trials / "20", 660),
            (trials / "20-flag10", 1280),
        ):
            _stem_panel(canvas, directory / face, x, y + 25)
    return canvas


def _stem_proof_headings(canvas: Image.Image) -> None:
    proof_label(canvas, "TALHA MONO / CROSS-STYLE T L 1 STUDY", 40, 35, 25)
    titles = (
        "Beta.6 defaults",
        "t/l/1 at 20 units",
        "t/l 20 + 1 flag 10",
    )
    for title, x in zip(titles, (40, 660, 1280)):
        proof_label(canvas, title, x, 95)
    proof_label(
        canvas,
        "Isolated defaults: calt, liga and SS11 off. Accents and contextual families are unchanged; these are study fonts.",
        40,
        canvas.height - 60,
        16,
    )


def main(argv: list[str] | None = None) -> None:
    """Write the reviewed study sheet; e.g. ``main(['--base', 'build'])``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=Path("build"))
    parser.add_argument("--trials", type=Path, default=Path("build/stem-trials"))
    parser.add_argument(
        "--out", type=Path, default=Path("docs/design/beta6-stem-study.png")
    )
    args = parser.parse_args(argv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    cross_style_stem_proof(args.base, args.trials).save(args.out)
    print(f"Stem study proof: {args.out}")


if __name__ == "__main__":
    main()
