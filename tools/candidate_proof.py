"""Show the full stem build and SS11 as four independent native-pixel conditions."""

import argparse
from pathlib import Path

from PIL import Image, ImageOps

from reading_proof import INK, PAPER, proof_label
from run_raster import RunRasterizer

PROOF_LINES = (
    (12, "little filter tipiti  1 l I"),
    (15, "A leitura tem altura e ritmo."),
    (20, "mĺm mľm młm  it̃́p  łódź"),
    (15, "if (item != nil) { return 1; }"),
)
PROOF_TITLES = (
    "Beta.6 / SS11 off",
    "Beta.6 / SS11 on",
    "Stem trial / SS11 off",
    "Stem trial / SS11 on",
)


def candidate_panel(canvas: Image.Image, path: Path, x: int, y: int, ss11: int) -> None:
    """Keep native hinted pixels in each condition; e.g. ``candidate_panel(sheet, font, 40, 180, 1)``."""
    raster = RunRasterizer(path)
    for index, (px, text) in enumerate(PROOF_LINES):
        proof_label(canvas, f"{px}px", x, y + index * 40, 13)
        run = raster.render(text, px, {"calt": 1, "liga": 1, "ss11": ss11})
        image = ImageOps.colorize(Image.fromarray(run.image), PAPER, INK)
        canvas.paste(image, (x + 42, y + index * 40))


def candidate_sheet(base: Path, candidate: Path) -> Image.Image:
    """Compare all ten physical styles without changing two factors at once; e.g. ``candidate_sheet(old, new)``."""
    faces = sorted(
        path for path in base.glob("TalhaMono*.otf") if "NF-" not in path.name
    )
    if not faces:
        raise ValueError(f"{base}: expected ordinary Talha Mono faces")
    canvas = Image.new("RGB", (2520, 220 + 225 * len(faces)), PAPER)
    proof_label(canvas, "TALHA MONO / COMPLETE STEM TRIAL", 40, 30, 25)
    conditions = ((base, 0), (base, 1), (candidate, 0), (candidate, 1))
    for index, title in enumerate(PROOF_TITLES):
        proof_label(canvas, title, 40 + index * 620, 85)
    for row, face in enumerate(faces):
        proof_label(canvas, face.stem, 40, 130 + row * 225)
        for column, (directory, ss11) in enumerate(conditions):
            candidate_panel(
                canvas, directory / face.name, 40 + column * 620, 158 + row * 225, ss11
            )
    _candidate_proof_footer(canvas)
    return canvas


def _candidate_proof_footer(canvas: Image.Image) -> None:
    proof_label(
        canvas,
        "HarfBuzz / FreeType light hinting; calt and liga on. Inspect at 100% zoom; native 12 / 15 / 20 px.",
        40,
        canvas.height - 45,
        16,
    )


def main(argv: list[str] | None = None) -> None:
    """Write a complete candidate contact sheet; e.g. ``main(['--base', 'old', '--new', 'new'])``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument(
        "--out", type=Path, default=Path("docs/design/beta7-four-conditions.png")
    )
    args = parser.parse_args(argv)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    candidate_sheet(args.base, args.new).save(args.out)
    print(f"Four-condition proof: {args.out}")


if __name__ == "__main__":
    main()
