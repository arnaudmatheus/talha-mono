#!/usr/bin/env python3
"""Render the visual source atlas and display studies without rebuilding fonts.

python tools/design_atlas.py [--fonts build] [--out docs/design]
Requires the normal font drawing dependencies and rsvg-convert for PNGs.
The checked-in reference images are sufficient; rendering uses no network.
"""

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image

from atlas_sources import letters_atlas, ornament_atlas
from atlas_svg import OutlineFont, Sheet
from display_studies import chapter_study, cover_study

ROOT = Path(__file__).resolve().parent.parent


def atlas_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts", type=Path, default=ROOT / "build")
    parser.add_argument("--out", type=Path, default=ROOT / "docs/design")
    parser.add_argument("--svg-only", action="store_true")
    return parser.parse_args(argv)


def render_sheet(sheet: Sheet, path: Path, svg_only: bool) -> None:
    sheet.save(path)
    if not svg_only:
        subprocess.run(
            ["rsvg-convert", str(path), "-o", str(path.with_suffix(".png"))], check=True
        )
    print(f"Rendered {path.name}")


def font_provenance(fonts: Path) -> dict[str, dict[str, str]]:
    report = {}
    for style in ("Regular", "Italic"):
        path = fonts / f"TalhaMono-{style}.otf"
        outline = OutlineFont(path)
        report[path.name] = {
            "version": outline.font["name"].getDebugName(5),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    return report


def make_overview(directory: Path, names: list[str]) -> None:
    """Tile the PNG sheets for the documentation; e.g. ``make_overview(out, names)``."""
    overview = Image.new("RGB", (1400, 1800), "#F3EEE2")
    for index, name in enumerate(names):
        with Image.open(directory / f"{name}.png") as preview:
            preview.thumbnail((700, 900))
            overview.paste(preview, ((index % 2) * 700, (index // 2) * 900))
    overview.save(directory / "overview.png")


def review_sheets(regular: OutlineFont, italic: OutlineFont) -> dict[str, Sheet]:
    sources = ROOT / "docs/design/sources"
    return {
        "atlas-letters": letters_atlas(regular, italic, sources),
        "atlas-ornament": ornament_atlas(regular, sources),
        "display-folha": cover_study(regular, italic),
        "display-chapter": chapter_study(regular, italic),
    }


def main(argv: list[str] | None = None) -> None:
    """Build all four review sheets; e.g. ``main(['--svg-only'])``."""
    args = atlas_args(argv)
    regular = OutlineFont(args.fonts / "TalhaMono-Regular.otf")
    italic = OutlineFont(args.fonts / "TalhaMono-Italic.otf")
    sheets = review_sheets(regular, italic)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, sheet in sheets.items():
        render_sheet(sheet, args.out / f"{name}.svg", args.svg_only)
    provenance = json.dumps(font_provenance(args.fonts), indent=2) + "\n"
    (args.out / "font-provenance.json").write_text(provenance)
    if not args.svg_only:
        make_overview(args.out, list(sheets))


if __name__ == "__main__":
    main()
