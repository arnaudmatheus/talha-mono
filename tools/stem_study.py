"""Isolated t/l/1 drawings for review; defaults and contextual families stay intact."""

import math
from collections.abc import Iterator
from contextlib import contextmanager

from fontTools.ttLib import TTFont

import caps
import corsiva
import letters
import pen
from glyph_table import CAP_TOP, XH_NEW, vmap
from glyph_writer import GlyphWriter
from pen_types import Stroke
from swash_pilot import font_pen
from stem_recipes import STEM_NAMES, adjust_stem_recipe


def stem_skeleton(name: str, strength: int, italic: bool = False) -> list[Stroke]:
    """Use each face's own skeleton, with a zero-strength control; e.g. ``stem_skeleton('t', 20, True)``."""
    drawings = {"t": letters.strokes_t, "l": letters.strokes_l}
    if italic:
        drawings = {"t": corsiva.c_t_pulled_right, "l": corsiva.c_l}
    drawings["one"] = caps.FIGURES["one"]
    if name not in drawings:
        raise ValueError(f"{name!r}: expected t/l/one")
    strokes = adjust_stem_recipe(name, drawings[name](), strength)
    return (
        strokes
        if name == "one"
        else [[(x, vmap(y)) for x, y in stroke] for stroke in strokes]
    )


@contextmanager
def stem_pen(font: TTFont) -> Iterator[tuple[float, float]]:
    """Restore drawing globals even on failed exports; e.g. ``with stem_pen(font) as nib: ...``."""
    previous = (pen.ADV, pen.SLANT, pen.OPTICAL, pen.PEN)
    nib, degrees, cell = font_pen(font)
    pen.ADV, pen.SLANT, pen.OPTICAL, pen.PEN = (
        cell,
        math.radians(degrees),
        0,
        math.radians(35),
    )
    try:
        yield nib
    finally:
        pen.ADV, pen.SLANT, pen.OPTICAL, pen.PEN = previous


def replace_stem_trial(
    font: TTFont, strength: int, flag_strength: int | None = None
) -> None:
    """Change only the three plain glyphs in a study copy; e.g. ``replace_stem_trial(font, 20)``."""
    writer = GlyphWriter(font, font["hmtx"]["A"][0])
    italic = bool(font["post"].italicAngle)
    with stem_pen(font) as nib:
        for name in STEM_NAMES:
            amount = (
                flag_strength
                if name == "one" and flag_strength is not None
                else strength
            )
            skeleton = stem_skeleton(name, amount, italic)
            shape, _ = pen.place(
                skeleton, *nib, band_top=CAP_TOP if name == "one" else XH_NEW
            )
            writer.put(name, shape)
