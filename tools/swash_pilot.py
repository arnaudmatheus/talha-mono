#!/usr/bin/env python3
"""Export the three capital studies and selected preview fonts for review.

python tools/swash_pilot.py

Only three swash capitals, eight leaf forms and two ribbon ends are replaced
in copies of the existing fonts.
The regular outlines, hinting and OpenType feature tables remain intact.
"""

import argparse
from pathlib import Path

from fontTools.ttLib import TTFont

from atlas_svg import BLUE, INK, MUTED, RED, OutlineFont, Sheet
from build_options import STYLES, TEXT_NIB
from design_atlas import ROOT, render_sheet
from display_motifs import leaf_study, ribbon_study
from glyph_writer import GlyphWriter
import ornament
from place_ornaments import CELL_MARGIN, _fit_cell, _ornament_shape
from swash_caps import PILOT_CAPITALS, SWASH_VARIANTS, capital_offset, swash_shape


def font_pen(font: TTFont) -> tuple[tuple[float, float], float, int]:
    """Drawing parameters of a shipped face; e.g. ``font_pen(TTFont(path))``."""
    style = font["name"].getDebugName(17) or font["name"].getDebugName(2)
    if style not in STYLES:
        raise ValueError(f"{style!r}: expected one of {tuple(STYLES)}")
    width, thickness = STYLES[style].nib
    factor = TEXT_NIB if "Text" in font["name"].getDebugName(1) else 1.0
    return (
        (width * factor, thickness * factor),
        STYLES[style].slant,
        font["hmtx"]["A"][0],
    )


def replace_swashes(font: TTFont, variant: int | None = None) -> None:
    """Update three opt-in outlines in memory; e.g. ``replace_swashes(font, 2)``."""
    nib, degrees, cell = font_pen(font)
    writer = GlyphWriter(font, cell)
    for capital in PILOT_CAPITALS:
        name = f"{capital}.swsh"
        if not writer.has(name):
            raise ValueError(f"{name!r}: expected an existing swsh alternate")
        dx = capital_offset(capital, nib, degrees, cell)
        writer.put(name, swash_shape(capital, nib, degrees, dx, variant))


def preview_font(source: Path, target: Path, variant: int | None = None) -> None:
    """Write a review copy, retaining existing hints; e.g. ``preview_font(src, out, 2)``."""
    target.parent.mkdir(parents=True, exist_ok=True)
    with TTFont(source) as font:
        replace_swashes(font, variant)
        replace_motifs(font, variant)
        font.save(target)


def replace_motifs(font: TTFont, variant: int | None = None) -> None:
    """Update only the pilot's leaf and ribbon glyphs; e.g. ``replace_motifs(font, 2)``."""
    nib, _, cell = font_pen(font)
    writer = GlyphWriter(font, cell)
    ornament.CELL = cell
    if variant is not None:
        replace_motif_study(font, writer, nib, cell, variant)
        return
    cmap = font.getBestCmap()
    for cp in list(range(0x1F650, 0x1F658)) + [0x2770, 0x2771]:
        writer.put(cmap[cp], _ornament_shape(cp, *nib, cell))


def replace_motif_study(
    font: TTFont, writer: GlyphWriter, nib: tuple[float, float], cell: int, variant: int
) -> None:
    # Only the north-east leaf and left ribbon are needed in the comparison.
    leaf, fills = leaf_study(variant)
    leaf = [ornament._map(stroke, ornament._xf) for stroke in leaf]
    shape = ornament.render(leaf, [ornament._xf(stroke) for stroke in fills], *nib)
    if shape.bounds[0] < CELL_MARGIN or shape.bounds[2] > cell - CELL_MARGIN:
        shape = _fit_cell(shape, cell)
    writer.put(font.getBestCmap()[0x1F652], shape)
    strokes, fills = ribbon_study(variant, cell)
    writer.put(font.getBestCmap()[0x2770], ornament.render(strokes, fills, *nib))


def pilot_fonts(source: Path, output: Path) -> dict[int, OutlineFont]:
    choices = {}
    for variant in SWASH_VARIANTS:
        target = output / f"variant-{variant}" / "TalhaMono-Regular.otf"
        preview_font(source / target.name, target, variant)
        choices[variant] = OutlineFont(target)
    for path in sorted(source.glob("TalhaMono*.otf")):
        preview_font(path, output / "selected" / path.name)
    return choices


def swash_reference(sheet: Sheet, regular: OutlineFont, sources: Path) -> None:
    sheet.label("TALHA MONO  /  SWASH PILOT", 80, 65, 18, BLUE)
    sheet.text(regular, "A flourish from the stroke", 75, 157, 68)
    sheet.photo(
        sources / "figueiredo-plate7.jpg", (80, 205, 570, 200), (130, 1050, 900, 1400)
    )
    sheet.label("Figueiredo · Nova Escola, plate nº 7", 720, 270, 21, INK)
    sheet.label("A: crossbar loop   P: descending stem   R: running leg", 720, 315, 19)
    sheet.label("Three modern interpretations of the written gesture.", 720, 354, 18)
    sheet.line(80, 440, 1720, 440)


def swash_comparison(
    regular: OutlineFont, choices: dict[int, OutlineFont], sources: Path
) -> Sheet:
    """Three studies beside the previous form; e.g. ``swash_comparison(old, choices, sources)``."""
    sheet = Sheet("Talha Mono: A, P and R swash studies", 1800, 1800)
    swash_reference(sheet, regular, sources)
    for index, (title, font) in enumerate(
        [("PREVIOUS", regular)]
        + [
            (f"{v:02d} / {n}", choices[v])
            for v, n in zip(SWASH_VARIANTS, ("RESTRAINED", "WRITTEN", "CEREMONIAL"))
        ]
    ):
        comparison_row(sheet, font, title, 485 + index * 303)
    sheet.label(
        "All studies use the same broad nib and monospace advance. Display swashes may overhang their cell.",
        80,
        1760,
        18,
    )
    return sheet


def comparison_row(sheet: Sheet, font: OutlineFont, title: str, y: int) -> None:
    sheet.label(title, 80, y, 17, BLUE)
    for capital, x in zip(PILOT_CAPITALS, (250, 800, 1350)):
        sheet.text(font, capital, x, y + 218, 245, INK, "swsh")
    sheet.line(80, y + 280, 1720, y + 280)


def size_check(selected: OutlineFont, italic: OutlineFont) -> Sheet:
    """Compare native display sizes and word contexts; e.g. ``size_check(regular, italic)``."""
    sheet = Sheet("Talha Mono: selected swashes at display sizes", 1800, 1800)
    sheet.label("TALHA MONO  /  SELECTED SWASHES", 80, 65, 18, BLUE)
    sheet.text(selected, "The gesture at reading distance", 75, 157, 66)
    for index, size in enumerate((48, 96, 192)):
        y = 280 + index * 310
        sheet.label(f"{size} px · Regular", 80, y, 18, BLUE)
        for capital, x in zip(PILOT_CAPITALS, (280, 800, 1320)):
            sheet.text(selected, capital, x, y + 185, size, INK, "swsh")
        sheet.line(80, y + 230, 1720, y + 230)
    word_context(sheet, selected, "Arte", 1250, INK)
    word_context(sheet, selected, "Preto", 1430, RED)
    word_context(sheet, italic, "Rasgo", 1610, BLUE)
    sheet.label(
        "Feature: swsh on the initial only. The remaining letters use the ordinary face; allow space below the baseline.",
        80,
        1750,
        18,
    )
    return sheet


def word_context(
    sheet: Sheet, font: OutlineFont, word: str, baseline: int, color: str
) -> None:
    size = 140
    sheet.text(font, word[0], 320, baseline, size, color, "swsh")
    sheet.text(font, word[1:], 320 + font.width(word[0], size), baseline, size, color)
    sheet.label(word + " · initial only", 1050, baseline - 45, 20, MUTED)


def pilot_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fonts", type=Path, default=ROOT / "fonts/otf")
    parser.add_argument("--out", type=Path, default=ROOT / "build/swash-pilot")
    parser.add_argument("--proofs", type=Path, default=ROOT / "docs/design")
    return parser.parse_args(argv)


def motif_reference(sheet: Sheet, previous: OutlineFont, sources: Path) -> None:
    sheet.label("TALHA MONO  /  ORNAMENT PILOT", 80, 65, 18, BLUE)
    sheet.text(previous, "The leaf and the fold", 75, 157, 68)
    sheet.photo(
        sources / "aleijadinho-portal.jpg", (80, 205, 500, 200), (350, 600, 790, 900)
    )
    sheet.photo(
        sources / "habacuc-scroll.jpg", (950, 205, 500, 200), (360, 760, 800, 1430)
    )
    sheet.label("Portal · Ouro Preto · Museu Paulista (USP)", 80, 435, 17)
    sheet.label("Habacuc · Congonhas · Luis Rizo, 2008", 950, 435, 17)


def motif_comparison(
    previous: OutlineFont, choices: dict[int, OutlineFont], sources: Path
) -> Sheet:
    """Show the leaf and ribbon alternatives; e.g. ``motif_comparison(old, choices, sources)``."""
    sheet = Sheet("Talha Mono: scroll leaf and folded ribbon studies", 1800, 1800)
    motif_reference(sheet, previous, sources)
    studies = [("PREVIOUS", previous)] + [
        (f"0{v} / STUDY", font) for v, font in choices.items()
    ]
    for index, (title, font) in enumerate(studies):
        motif_row(sheet, font, title, 490 + index * 285)
    sheet.label(
        "Selected: study 02. Lobed edges and ribs articulate the leaf; front, rear and crease articulate the ribbon.",
        80,
        1745,
        18,
    )
    return sheet


def motif_row(sheet: Sheet, font: OutlineFont, title: str, y: int) -> None:
    sheet.label(title, 80, y, 17, BLUE)
    sheet.text(font, "🙒", 350, y + 225, 340, INK)
    sheet.text(font, "❰", 1120, y + 225, 340, INK)
    sheet.line(80, y + 260, 1720, y + 260)


def motif_sizes(font: OutlineFont) -> Sheet:
    """Check the selected ornaments at native sizes; e.g. ``motif_sizes(font)``."""
    sheet = Sheet("Talha Mono: selected ornament sizes", 1800, 1300)
    sheet.label("TALHA MONO  /  SELECTED ORNAMENTS", 80, 65, 18, BLUE)
    sheet.text(font, "Scallops, ribs, and a fold", 75, 157, 68)
    for index, size in enumerate((48, 96, 192)):
        y = 280 + index * 280
        sheet.label(f"{size} px · Regular", 80, y, 18, BLUE)
        sheet.text(font, "🙐🙒", 400, y + 180, size, INK)
        sheet.text(font, "❰", 1050, y + 180, size, INK)
        sheet.text(font, "❱", 1350, y + 180, size, INK)
        sheet.line(80, y + 220, 1720, y + 220)
    sheet.label(
        "The four directional leaves and their turned forms share one skeleton. The ribbon ends leave room for an inscription.",
        80,
        1200,
        18,
    )
    return sheet


def main(argv: list[str] | None = None) -> None:
    """Build the pilot fonts and proofs; e.g. ``main([])``."""
    args = pilot_args(argv)
    choices = pilot_fonts(args.fonts, args.out)
    old = OutlineFont(args.fonts / "TalhaMono-Regular.otf")
    selected = OutlineFont(args.out / "selected/TalhaMono-Regular.otf")
    italic = OutlineFont(args.out / "selected/TalhaMono-Italic.otf")
    comparison = swash_comparison(old, choices, ROOT / "docs/design/sources")
    args.proofs.mkdir(parents=True, exist_ok=True)
    render_sheet(comparison, args.proofs / "swash-comparison.svg", False)
    render_sheet(size_check(selected, italic), args.proofs / "swash-sizes.svg", False)
    sources = ROOT / "docs/design/sources"
    render_sheet(
        motif_comparison(old, choices, sources),
        args.proofs / "motif-comparison.svg",
        False,
    )
    render_sheet(motif_sizes(selected), args.proofs / "motif-sizes.svg", False)


if __name__ == "__main__":
    main()
