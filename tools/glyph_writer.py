"""Writes pen shapes into the font: CFF outlines (as curves), advance, ink."""

from fontTools.pens.boundsPen import BoundsPen
from fontTools.misc.psCharStrings import T2CharString
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from shapely.geometry.polygon import orient

import fitcurves
from pen_types import Bounds, Point

# Outline simplification before fitting, in font units.
SIMPLIFY = 0.5


def _rounded(q: Point) -> tuple[int, int]:
    return (round(q[0]), round(q[1]))


def _polygons(shape: BaseGeometry) -> list[Polygon]:
    parts = shape.geoms if hasattr(shape, "geoms") else [shape]
    return [g for g in parts if g.geom_type == "Polygon" and not g.is_empty]


def _draw_ring(pen: T2CharStringPen, ring: list[Point]) -> None:
    # Curves, not polylines (roadmap F1): tools/fitcurves.py.
    start, segs = fitcurves.fit_ring(ring)
    pen.moveTo(_rounded(start))
    for s in segs:
        if s[0] == "L":
            pen.lineTo(_rounded(s[1]))
        else:
            pen.curveTo(_rounded(s[1]), _rounded(s[2]), _rounded(s[3]))
    pen.closePath()


class GlyphWriter:
    """Puts shapes into one font's CFF table and remembers each one's ink.

    >>> writer = GlyphWriter(font, cell=1160)
    >>> writer.put("a", shape)
    >>> writer.ink["a"]
    (231.0, -12.0, 958.0, 1094.0)
    """

    def __init__(self, font: TTFont, cell: int) -> None:
        self.font = font
        self.cell = cell
        self.ink: dict[str, Bounds] = {}
        self._cff = font["CFF "].cff
        self._top = self._cff.topDictIndex[0]

    def charstring(self, shape: BaseGeometry, width: int | None = None) -> T2CharString:
        """The shape as a CFF charstring; width None means the cell."""
        pen = T2CharStringPen(width, None)
        for g in _polygons(shape.simplify(SIMPLIFY)):
            g = orient(g, sign=1.0)  # CFF: outer contours counter-clockwise
            for ring in [g.exterior] + list(g.interiors):
                _draw_ring(pen, list(ring.coords[:-1]))
        return pen.getCharString(
            private=self._top.Private, globalSubrs=self._cff.GlobalSubrs
        )

    def put(self, name: str, shape: BaseGeometry, advance: int | None = None) -> None:
        """Replaces glyph `name`. advance None = the cell; ligatures and
        spacers keep Radon's own."""
        charstrings = self._top.CharStrings
        adv = self.cell if advance is None else advance
        new = self.charstring(shape, None if adv == self.cell else adv)
        if charstrings.charStringsAreIndexed:
            charstrings.charStringsIndex[charstrings.charStrings[name]] = new
        else:
            charstrings.charStrings[name] = new
        self.font["hmtx"][name] = (adv, int(shape.bounds[0]))
        self.ink[name] = shape.bounds

    def add(self, name: str, shape: BaseGeometry) -> None:
        """A glyph Radon doesn't have: appended to the CFF, the glyph order
        and hmtx. Call commit_glyph_order() once all are added."""
        charstrings = self._top.CharStrings
        charstrings.charStringsIndex.append(self.charstring(shape))
        charstrings.charStrings[name] = len(charstrings.charStringsIndex) - 1
        self.font.getGlyphOrder().append(name)
        self.font["hmtx"][name] = (self.cell, int(shape.bounds[0]))
        self.ink[name] = shape.bounds

    def commit_glyph_order(self) -> None:
        order = self.font.getGlyphOrder()
        self._top.charset = order
        self.font.setGlyphOrder(order)

    def add_shifted(self, name: str, source: str, shift: float) -> None:
        """Copy curves into another position in the same cell; e.g. ``writer.add_shifted('i.ctxL', 'i', -40)``."""
        if self.has(name):
            raise ValueError(f"{name!r}: expected an unused glyph name")
        strings = self._top.CharStrings
        strings.charStringsIndex.append(self._shifted_charstring(source, shift))
        strings.charStrings[name] = len(strings.charStringsIndex) - 1
        self.font.getGlyphOrder().append(name)
        self._remember_shift(name, source, shift)

    def _shifted_charstring(self, source: str, shift: float) -> T2CharString:
        advance = self.font["hmtx"][source][0]
        private = self._top.Private
        width = (
            None
            if advance == private.defaultWidthX
            else advance - private.nominalWidthX
        )
        pen = T2CharStringPen(width, None)
        self.font.getGlyphSet()[source].draw(TransformPen(pen, (1, 0, 0, 1, shift, 0)))
        return pen.getCharString(
            private=self._top.Private, globalSubrs=self._cff.GlobalSubrs
        )

    def put_shifted(self, name: str, source: str, shift: float) -> None:
        """Replace an alternate without duplicating its glyph ID; e.g. ``writer.put_shifted('i.ctxL', 'i', -20)``."""
        if name == source or not self.has(name):
            raise ValueError(
                f"{name!r}: expected an existing alternate distinct from {source!r}"
            )
        strings = self._top.CharStrings
        strings.charStringsIndex[strings.charStrings[name]] = self._shifted_charstring(
            source, shift
        )
        self._remember_shift(name, source, shift)

    def _remember_shift(self, name: str, source: str, shift: float) -> None:
        advance, lsb = self.font["hmtx"][source]
        self.font["hmtx"][name] = (advance, round(lsb + shift))
        x0, y0, x1, y1 = self.bounds(source)
        self.ink[name] = (x0 + shift, y0, x1 + shift, y1)

    def has(self, name: str) -> bool:
        return name in self._top.CharStrings

    def bounds(self, name: str) -> Bounds:
        """The ink bounds of the glyph as it is in the font right now."""
        glyphs = self.font.getGlyphSet()
        bp = BoundsPen(glyphs)
        glyphs[name].draw(bp)
        if bp.bounds is None:
            raise ValueError(f"glyph {name!r} has no outline (expected ink to measure)")
        return bp.bounds
