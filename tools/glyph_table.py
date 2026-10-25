"""Every redrawn glyph: Radon's glyph name -> (upright strokes, kind).

The kind ('lower' or 'cap') decides the centring band and where the marks
sit. Capitals and figures stay as drawn; lowercase is stretched to the
taller x-height.
"""

from collections.abc import Callable
from typing import NamedTuple

import caps
import letters
from pen_types import StrokesFn
from drawing_catalog import drawing_catalog

# x-height +5% (roadmap B2: Legge & Bigelow's critical print size). Only the
# band from baseline to x-height stretches; ascenders keep their top, so the
# space above is compressed proportionally; descenders don't move.
XH_OLD, XH_NEW = 1027, 1080
K = XH_NEW / XH_OLD
T_NEW = letters.T * K
CAP_TOP = 1460
ASCENDERS = set("bdfhkl")
LOWERCASE = "abcdefghijklmnopqrstuvwxyz"
# Letters that take marks, by the character they are drawn for.
LETTER_OF = {**{c: c for c in LOWERCASE}, **{c: c for c in caps.CAPS}}


class Letter(NamedTuple):
    strokes: StrokesFn
    kind: str  # 'lower' or 'cap'


def vmap(y: float) -> float:
    """A skeleton height on the old x-height grid -> the taller one."""
    if y <= 0:
        return y
    if y <= letters.T:
        return y * K
    return T_NEW + (y - letters.T) * (letters.A - T_NEW) / (letters.A - letters.T)


def taller(fn: StrokesFn) -> StrokesFn:
    return lambda: [[(x, vmap(y)) for x, y in st] for st in fn()]


def band_top(kind: str) -> float:
    """Top of the band a glyph is centred on: x-height or cap height."""
    return XH_NEW if kind == "lower" else CAP_TOP


def _drawings(italic: bool, refined_stems: bool) -> dict[str, Letter]:
    catalog = drawing_catalog(italic, refined_stems)
    table = {c: Letter(catalog.lower[c], "lower") for c in LOWERCASE}
    table["dotlessi"] = Letter(catalog.lower["dotlessi"], "lower")
    table["uni0237"] = Letter(catalog.lower["dotlessj"], "lower")
    table.update({c: Letter(fn, "cap") for c, fn in caps.CAPS.items()})
    table.update({n: Letter(fn, "cap") for n, fn in catalog.figures.items()})
    table.update({n: Letter(fn, "lower") for n, fn in catalog.extra_lower.items()})
    table.update({n: Letter(fn, "cap") for n, fn in caps.EXTRAS_UPPER.items()})
    return table


def glyph_table(
    in_font: Callable[[str], bool], italic: bool = False, refined_stems: bool = True
) -> dict[str, Letter]:
    """The redrawn glyphs this font has, lowercase on the taller x-height.

    Each call resolves style/profile recipes without changing global catalogs.

    >>> glyph_table(writer.has)["a"].kind
    'lower'
    """
    table = {
        g: Letter(taller(fn), kind) if kind == "lower" else Letter(fn, kind)
        for g, (fn, kind) in _drawings(italic, refined_stems).items()
    }
    return {g: letter for g, letter in table.items() if in_font(g)}
