"""Source-atlas layouts, with skeletons taken from the font's drawing code."""

import math
from pathlib import Path

from shapely.geometry import box
from shapely.ops import unary_union

import corsiva
import letters
import ornament
import pen
from atlas_svg import BLUE, INK, RED, OutlineFont, Sheet
from glyph_table import taller
from pen_types import Stroke, StrokesFn
from swash_caps import capital_offset, lean_strokes, swash_strokes


def placed_skeleton(
    builder: StrokesFn, italic: bool = False, lower: bool = True
) -> list[Stroke]:
    """Reproduce centring without changing pen globals; e.g. ``placed_skeleton(corsiva.c_h, True)``."""
    strokes = taller(builder)() if lower else builder()
    shear = math.tan(math.radians(13 if italic else 7))
    slanted = [[(x + y * shear, y) for x, y in st] for st in strokes]
    ink = unary_union([pen.sweep_broad(st, 138, 106) for st in slanted])
    band = ink.intersection(box(-2000, 0, 4000, 1080 if lower else 1460))
    left, _, right, _ = band.bounds
    shift = 580 - (left + right) / 2
    return [[(x + shift, y) for x, y in st] for st in slanted]


def motif_skeleton(character: str) -> list[Stroke]:
    """Read an ornament's production paths; e.g. ``motif_skeleton('❨')``."""
    strokes, fills = ornament.ORNAMENTS[ord(character)]()
    return [st[0] if isinstance(st, tuple) else st for st in strokes] + fills


def capital_skeleton() -> list[Stroke]:
    """Include the production swash construction; e.g. ``capital_skeleton()``."""
    dx = capital_offset("A", (138, 106), 7, 1160)
    strokes = lean_strokes(swash_strokes("A"), 7, dx)
    return [st[0] if isinstance(st, tuple) else st for st in strokes]


def atlas_header(sheet: Sheet, regular: OutlineFont, number: str, title: str) -> None:
    sheet.label("TALHA MONO  /  VISUAL SOURCE ATLAS", 70, 65, 17, BLUE)
    sheet.label(number, 1330, 65, 17, BLUE, "end")
    sheet.text(regular, title, 65, 155, 75)
    sheet.label("Historical detail → production skeleton → finished font", 70, 210, 23)
    sheet.line(70, 246, 1330, 246)


def row_header(sheet: Sheet, y: int, index: str, title: str) -> None:
    sheet.label(index, 70, y, 19, RED)
    sheet.label(title, 120, y, 23, INK)
    for text, x in (
        ("SOURCE DETAIL", 70),
        ("DRAWING SKELETON", 590),
        ("FONT OUTLINE", 1030),
    ):
        sheet.label(text, x, y + 43, 13, BLUE)


def row_notes(
    sheet: Sheet, y: int, credit: str, explanation: str, adaptation: str
) -> None:
    sheet.label(credit, 70, y + 337, 16)
    sheet.label(explanation, 70, y + 370, 18, INK)
    sheet.label(adaptation, 70, y + 401, 17)
    if y < 1260:
        sheet.line(70, y + 435, 1330, y + 435)


def letter_guides(
    sheet: Sheet, x: int, baseline: int, count: int, scale: float = 0.14
) -> None:
    for index in range(count + 1):
        sheet.line(
            x + index * 1160 * scale,
            baseline - 240,
            x + index * 1160 * scale,
            baseline + 35,
        )
    for height in (0, 1080, 1550):
        sheet.line(
            x,
            baseline - height * scale,
            x + count * 1160 * scale,
            baseline - height * scale,
        )


def regular_row(sheet: Sheet, regular: OutlineFont, sources: Path) -> None:
    y = 300
    row_header(sheet, y, "01", "The hooked ascender")
    sheet.photo(
        sources / "figueiredo-plate9.jpg",
        (70, y + 75, 430, 225),
        (430, 815, 1130, 1015),
    )
    letter_guides(sheet, 680, y + 300, 1)
    sheet.strokes(placed_skeleton(letters.strokes_h), 680, y + 300, 0.14)
    sheet.text(regular, "h", 1085, y + 300, 280)
    row_notes(
        sheet,
        y,
        "Figueiredo · plate nº 9 · BNP image 95",
        "Right-turning entry, shortened for the cell.",
        "The original quill's contrast becomes a fixed 35° broad-nib stroke.",
    )


def corsiva_row(sheet: Sheet, italic: OutlineFont, sources: Path) -> None:
    y = 780
    row_header(sheet, y, "02", "The loop and the descending rasgo")
    sheet.photo(
        sources / "figueiredo-plate7.jpg", (70, y + 75, 430, 225), (505, 180, 805, 415)
    )
    letter_guides(sheet, 620, y + 300, 2, 0.12)
    for index, builder in enumerate((corsiva.c_h, corsiva.c_p)):
        sheet.strokes(
            placed_skeleton(builder, True), 620 + index * 139.2, y + 300, 0.12
        )
    sheet.text(italic, "hp", 1030, y + 300, 240)
    row_notes(
        sheet,
        y,
        "Figueiredo · plate nº 7 · BNP image 91",
        "Keep the rising loop; compress the sweeping descender.",
        "The pen lifts between letters, and the rasgo stays inside its cell.",
    )


def initial_row(sheet: Sheet, regular: OutlineFont, sources: Path) -> None:
    y = 1260
    row_header(sheet, y, "03", "A flourish becomes a display initial")
    sheet.photo(
        sources / "figueiredo-plate7.jpg", (70, y + 75, 430, 225), (125, 500, 425, 775)
    )
    sheet.strokes(capital_skeleton(), 660, y + 290, 0.14)
    sheet.glyph(regular, "A", (1040, y + 70, 270, 245), INK, "swsh")
    row_notes(
        sheet,
        y,
        "Figueiredo · plate nº 7 · second alphabet",
        "Interpretation: the crossbar grows into a connected loop.",
        "Use swsh on a single initial; leave clear space for its overhang.",
    )


def letters_atlas(regular: OutlineFont, italic: OutlineFont, sources: Path) -> Sheet:
    """Lay out three documented transformations; e.g. ``letters_atlas(r, i, sources)``."""
    sheet = Sheet("Talha Mono source atlas: the written hand")
    atlas_header(sheet, regular, "01 / 02", "The written hand")
    regular_row(sheet, regular, sources)
    corsiva_row(sheet, italic, sources)
    initial_row(sheet, regular, sources)
    sheet.label(
        "Sources: Nova Escola (1722), RES-3075-A · Biblioteca Nacional de Portugal · Public domain",
        70,
        1745,
        15,
    )
    sheet.label(
        "Crops retain the scan's colour. Red lines are Talha's actual skeletons, rather than tracings of the scan.",
        70,
        1773,
        14,
    )
    return sheet


def carving_row(sheet: Sheet, regular: OutlineFont, sources: Path) -> None:
    y = 300
    row_header(sheet, y, "04", "Carving becomes a scroll and leaf")
    sheet.photo(
        sources / "aleijadinho-portal.jpg", (70, y + 75, 430, 225), (350, 600, 790, 900)
    )
    sheet.strokes(motif_skeleton("🙒"), 665, y + 275, 0.16)
    sheet.glyph(regular, "🙒", (1070, y + 85, 210, 195), INK)
    row_notes(
        sheet,
        y,
        "São Francisco de Assis · portal · Ouro Preto",
        "Interpretation: scalloped edges and ribs held by an open C-scroll.",
        "A vocabulary from Aleijadinho's carving; this leaf is not a traced portal detail.",
    )


def ceiling_row(sheet: Sheet, regular: OutlineFont, sources: Path) -> None:
    y = 780
    row_header(sheet, y, "05", "A painted cartouche becomes a frame")
    sheet.photo(
        sources / "ataide-ceiling.jpg", (70, y + 75, 430, 225), (100, 25, 440, 225)
    )
    sheet.strokes(motif_skeleton("❨"), 665, y + 280, 0.115)
    sheet.text(regular, "❨", 1020, y + 280, 240)
    sheet.text(regular, "❩", 1180, y + 280, 240)
    row_notes(
        sheet,
        y,
        "Ataíde · São Francisco de Assis · nave ceiling",
        "Interpretation: paired bows, volutes, and a terminal drop.",
        "The frame borrows the painted border's rhythm; the figures remain in the painting.",
    )


def scroll_row(sheet: Sheet, regular: OutlineFont, sources: Path) -> None:
    y = 1260
    row_header(sheet, y, "06", "An inscription scroll becomes a ribbon end")
    sheet.photo(
        sources / "habacuc-scroll.jpg", (70, y + 75, 430, 225), (360, 760, 800, 1430)
    )
    sheet.strokes(motif_skeleton("❰"), 660, y + 255, 0.16)
    sheet.text(regular, "❰❱", 1030, y + 260, 230)
    row_notes(
        sheet,
        y,
        "Aleijadinho · Habacuc · Congonhas",
        "Interpretation: a front band, a rear swallowtail, and a crease.",
        "The cut tail is a modern abstraction; the photograph shows the folded stone scroll.",
    )


def ornament_atlas(regular: OutlineFont, sources: Path) -> Sheet:
    """Show ornamental references honestly; e.g. ``ornament_atlas(r, sources)``."""
    sheet = Sheet("Talha Mono source atlas: the carved frame")
    atlas_header(sheet, regular, "02 / 02", "The carved frame")
    carving_row(sheet, regular, sources)
    ceiling_row(sheet, regular, sources)
    scroll_row(sheet, regular, sources)
    sheet.label(
        "Portal: Museu Paulista (USP) · Ceiling: Tetraktys, 2005 · Habacuc: Luis Rizo, 2008 · Public domain",
        70,
        1745,
        14,
    )
    sheet.label(
        "Photographs are visual references. Full source links, image treatments, and credits accompany this atlas.",
        70,
        1773,
        14,
    )
    return sheet
