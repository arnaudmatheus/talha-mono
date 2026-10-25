"""The wider roman i keeps its dot, nib, centring and fixed cell."""

import math

import pytest

import letters
import pen
from build_options import STYLES, TEXT_NIB
from conftest import reloaded, tiny_font
from glyph_table import XH_NEW, taller
from glyph_writer import GlyphWriter


@pytest.mark.parametrize("cell", (1160, 1320))
@pytest.mark.parametrize("factor", (1.0, TEXT_NIB))
@pytest.mark.parametrize("style", ("Regular", "Bold"))
def test_i_family_fits_the_cell_without_changing_its_dot_or_advance(
    cell: int, factor: float, style: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pen, "ADV", cell)
    monkeypatch.setattr(pen, "SLANT", math.radians(STYLES[style].slant))
    monkeypatch.setattr(pen, "OPTICAL", 0)
    nib = tuple(value * factor for value in STYLES[style].nib)
    stem, dot = letters.strokes_idot()
    assert stem == letters.strokes_dotlessi()[0] and dot == letters.DOT()
    shape, dx = pen.place(taller(letters.strokes_idot)(), *nib, band_top=XH_NEW)
    assert shape.is_valid and len(shape.geoms) == 2
    assert 0 <= shape.bounds[0] < shape.bounds[2] <= cell
    font = reloaded(tiny_font({"i": [], "dotlessi": []}, cell))
    writer = GlyphWriter(font, cell)
    writer.put("i", shape)
    dotless, _ = pen.place(taller(letters.strokes_dotlessi)(), *nib, dx=dx)
    writer.put("dotlessi", dotless)
    assert all(font["hmtx"][name][0] == cell for name in ("i", "dotlessi"))
