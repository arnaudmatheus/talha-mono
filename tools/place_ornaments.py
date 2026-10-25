"""Step 1c: ornament, all opt-in (roadmap 0.8.0; see tools/ornament.py).

Florões and cartelas at Unicode's ornament code points, ribbon ends at ❰ ❱,
and the capitulares behind the titl and swsh features. Default text never
reaches any of it.
"""

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import cmap_format_12
from shapely import affinity
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

import caps
import ornament
import pen
from swash_caps import PILOT_CAPITALS, swash_shape
from build_state import BuildState
from gsub_features import add_single_subst_feature

# The Bold nib, as in the Bold style: heavy florões are drawn with it.
HEAVY_NIB = 1.42
# Ink kept this far inside the cell edge, so an ornament never paints over
# its neighbours in a terminal.
CELL_MARGIN = 15
BMP_END = 0xFFFF


def _fit_cell(shape: BaseGeometry, cell: int) -> BaseGeometry:
    """A rotated heart or a heavy leaf wider than the cell, scaled to fit."""
    x0, _, x1, _ = shape.bounds
    s = (cell - 2 * CELL_MARGIN) / (x1 - x0)
    shape = affinity.scale(shape, s, s, origin=((x0 + x1) / 2, ornament.CY))
    x0, _, x1, _ = shape.bounds
    return affinity.translate(shape, cell / 2 - (x0 + x1) / 2, 0)


def _ornament_shape(cp: int, w: float, t: float, cell: int) -> BaseGeometry:
    strokes, fills = ornament.ORNAMENTS[cp]()
    k = HEAVY_NIB if cp in ornament.HEAVY else 1.0
    shape = ornament.render(strokes, fills, w * k, t * k)
    x0, _, x1, _ = shape.bounds
    overflows = x0 < CELL_MARGIN or x1 > cell - CELL_MARGIN
    if cp not in ornament.FILACTERIOS and overflows:
        return _fit_cell(shape, cell)
    return shape


def _glyph_name(cp: int, cmap: dict[int, str]) -> str:
    return cmap.get(cp) or (f"uni{cp:04X}" if cp <= BMP_END else f"u{cp:05X}")


def _place_ornaments(state: BuildState) -> dict[int, str]:
    """Draws every ornament; returns the code points that are new glyphs."""
    w, t = state.nib
    cmap = state.font.getBestCmap()
    new_cmap = {}
    for cp in ornament.ORNAMENTS:
        shape = _ornament_shape(cp, w, t, state.opts.cell)
        name = _glyph_name(cp, cmap)
        if state.writer.has(name):
            state.writer.put(name, shape)
        else:
            state.writer.add(name, shape)
            new_cmap[cp] = name
        state.pen_glyphs.append(name)
    return new_cmap


def _capital_swash(state: BuildState, cap: str) -> BaseGeometry:
    fn, dx = state.glyphs[cap].strokes, state.placed[cap]
    if cap in PILOT_CAPITALS:
        return swash_shape(cap, state.nib, state.opts.slant_deg, dx)
    base, _ = pen.place(fn(), *state.nib, dx=dx)
    rasgo = ornament.render(ornament.flourish(base), [], *state.nib)
    return unary_union([base, rasgo])


def _add_capitulares(state: BuildState) -> tuple[dict[str, str], dict[str, str]]:
    """Carved (titl) and flourished (swsh) forms of each capital."""
    w, t = state.nib
    titl, swsh = {}, {}
    for cap in caps.CAPS:
        if cap not in state.placed or len(cap) != 1:
            continue
        fn, dx = state.glyphs[cap].strokes, state.placed[cap]
        strokes = [pen.slant(s) for s in fn()]
        carved = affinity.translate(ornament.carved(strokes, w, t), dx, 0)
        state.writer.add(f"{cap}.titl", carved)
        titl[cap] = f"{cap}.titl"
        state.writer.add(f"{cap}.swsh", _capital_swash(state, cap))
        swsh[cap] = f"{cap}.swsh"
    return titl, swsh


def _extend_cmap(font: TTFont, new_cmap: dict[int, str]) -> None:
    """Maps the new code points in every cmap subtable that can hold them,
    adding a Windows format 12 subtable for those past the BMP."""
    tables = font["cmap"].tables
    for table in tables:
        if table.format == 4:
            table.cmap.update({k: v for k, v in new_cmap.items() if k <= BMP_END})
        elif table.format == 12:
            table.cmap.update(new_cmap)
    has_windows_12 = any(
        t.format == 12 and (t.platformID, t.platEncID) == (3, 10) for t in tables
    )
    if any(k > BMP_END for k in new_cmap) and not has_windows_12:
        c12 = cmap_format_12(12)
        c12.platformID, c12.platEncID, c12.language = 3, 10, 0
        c12.cmap = {**font.getBestCmap(), **new_cmap}
        tables.append(c12)


def place_ornaments(state: BuildState) -> None:
    ornament.CELL = state.opts.cell
    new_cmap = _place_ornaments(state)
    titl, swsh = _add_capitulares(state)
    state.writer.commit_glyph_order()
    _extend_cmap(state.font, new_cmap)
    add_single_subst_feature(state.font, "titl", titl)
    add_single_subst_feature(state.font, "swsh", swsh)
