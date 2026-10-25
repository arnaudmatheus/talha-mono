"""Native Pango comparisons for the next reading session.

python tools/reading_proof.py --base fonts/otf --new build
"""

import argparse
import html
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

from measure import Renderer

READING_FACES = (
    "TalhaMono-Regular.otf",
    "TalhaMono-Italic.otf",
    "TalhaMono-Bold.otf",
    "TalhaMonoWide-Regular.otf",
    "TalhaMonoText-Regular.otf",
)
READING_LINE = "tipiti antigo Estrada  ti tr li ri fi"
CODE_LINE = "if item != nil { filter(list, 1); }"
INK, PAPER, BLUE = "#17283D", "#F5F0E4", "#315B7C"


def reading_raster(
    renderer: Renderer,
    text: str,
    size: int,
    dark: bool = False,
    features: str | None = None,
) -> Image.Image:
    """Keep native text pixels, tinting the two grounds; e.g. ``reading_raster(r, 'ti', 15)``."""
    attribute = (
        f' font_features="{html.escape(features, quote=True)}"' if features else ""
    )
    markup = f'<span foreground="#FFFFFF"{attribute}>{html.escape(text)}</span>'
    pixels = np.round(renderer.render(markup, size)[:, :, 0] * 255).astype("uint8")
    mask = Image.fromarray(pixels)
    return ImageOps.colorize(mask, INK if dark else PAPER, PAPER if dark else INK)


def proof_label(canvas: Image.Image, text: str, x: int, y: int, size: int = 18) -> None:
    ImageDraw.Draw(canvas).text(
        (x, y), text, font=ImageFont.load_default(size=size), fill=BLUE
    )


def reading_panel(
    canvas: Image.Image, renderer: Renderer, x: int, y: int, features: str | None = None
) -> None:
    for index, size in enumerate((12, 15, 20)):
        proof_label(canvas, f"{size} px", x, y + index * 37, 13)
        canvas.paste(
            reading_raster(renderer, READING_LINE, size, features=features),
            (x + 48, y + index * 37),
        )
    canvas.paste(
        reading_raster(renderer, CODE_LINE, 15, True, features), (x + 48, y + 118)
    )


def proof_canvas(title: str, height: int) -> Image.Image:
    canvas = Image.new("RGB", (1260, height), PAPER)
    proof_label(canvas, "TALHA MONO / " + title, 40, 35, 25)
    proof_label(canvas, "Previous beta.3", 40, 95)
    proof_label(canvas, "Local beta.4 candidate", 670, 95)
    return canvas


def proof_footer(canvas: Image.Image, lines: tuple[str, str], y: int) -> None:
    for index, text in enumerate(lines):
        proof_label(canvas, text, 40, y + index * 30, 16)


SIZE_FOOTER = (
    "Actual 12 / 15 / 20 px Pango + FreeType; hintslight; fixed cell advances.",
    "Inspect at 100% zoom. Dark rows use the same coverage mask on a dark ground.",
)
CONTEXT_FOOTER = (
    "Large rows: 48 px. Enlargements: native 20 px pixels at 3x, nearest-neighbour.",
    "The roman i receives balanced entries and exits. The t / r / f / l / 1 forms are retained.",
)


def comparison_proof(before: Path, after: Path) -> Image.Image:
    """Before/after at native pixels with no rescaling; e.g. ``comparison_proof(old, new)``."""
    canvas = proof_canvas("READING PROOF / BETA.4", 1460)
    for index, face in enumerate(READING_FACES):
        y = 155 + index * 240
        proof_label(canvas, face.removesuffix(".otf"), 40, y, 18)
        for directory, x in ((before, 40), (after, 670)):
            reading_panel(canvas, Renderer(str(directory / face)), x, y + 35)
        ImageDraw.Draw(canvas).line((40, y + 215, 1220, y + 215), fill="#C9C7BE")
    proof_footer(canvas, SIZE_FOOTER, 1380)
    return canvas


def confusable_proof(before: Path, after: Path) -> Image.Image:
    """Show whole words and the coordinated group; e.g. ``confusable_proof(old, new)``."""
    canvas = proof_canvas("NARROW LETTERS IN CONTEXT", 1200)
    for index, face in enumerate(READING_FACES[:2]):
        y = 155 + index * 440
        proof_label(canvas, face.removesuffix(".otf"), 40, y)
        for directory, x in ((before, 40), (after, 670)):
            context_panel(canvas, Renderer(str(directory / face)), x, y + 45)
    proof_footer(canvas, CONTEXT_FOOTER, 1090)
    return canvas


def context_panel(canvas: Image.Image, renderer: Renderer, x: int, y: int) -> None:
    for index, text in enumerate(("tipiti antigo", "Estrada  fi li", "t r f l 1 i")):
        canvas.paste(reading_raster(renderer, text, 48), (x, y + index * 75))
    native = reading_raster(renderer, "ti tr li ri fi", 20)
    enlarged = native.resize(
        (native.width * 3, native.height * 3), Image.Resampling.NEAREST
    )
    canvas.paste(enlarged, (x, y + 235))


def main(argv: list[str] | None = None) -> None:
    """Save the two review images; e.g. ``main(['--base', 'fonts/otf', '--new', 'build'])``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("docs/design"))
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    comparison_proof(args.base, args.new).save(args.out / "reading-sizes.png")
    confusable_proof(args.base, args.new).save(args.out / "reading-context.png")
    print(f"Reading proofs: {args.out}")


if __name__ == "__main__":
    main()
