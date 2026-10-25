"""Study controls reproduce each face and reject changes outside the three glyphs."""

import math
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont
from shapely.geometry import box

import caps
import corsiva
import letters
import pen
from conftest import reloaded, square, tiny_font
from glyph_table import vmap
from glyph_writer import GlyphWriter
from stem_review import audit_stem_font, stem_regressions
from stem_study import STEM_NAMES, replace_stem_trial, stem_pen, stem_skeleton


@pytest.mark.parametrize("italic", [False, True])
@pytest.mark.parametrize("name", STEM_NAMES)
def test_zero_study_uses_the_exact_face_recipe(name: str, italic: bool) -> None:
    drawings = {"t": letters.strokes_t, "l": letters.strokes_l}
    if italic:
        drawings = {"t": corsiva.c_t_pulled_right, "l": corsiva.c_l}
    expected = caps.FIGURES["one"]() if name == "one" else drawings[name]()
    if name != "one":
        expected = [[(x, vmap(y)) for x, y in stroke] for stroke in expected]
    assert stem_skeleton(name, 0, italic) == expected
    assert stem_skeleton(name, 20, italic) != expected


def test_small_flag_strength_preserves_the_original_foot_and_stem() -> None:
    original, small, full = (stem_skeleton("one", amount) for amount in (0, 10, 20))
    assert original[1:] == small[1:] == full[1:]
    assert original[0][0][0] - small[0][0][0] == 10
    assert original[0][0][0] - full[0][0][0] == 20
    assert original[0][-1] == small[0][-1] == full[0][-1]
    with pytest.raises(ValueError, match="expected"):
        stem_skeleton("t", 10)


def stem_fixture_font(italic: bool = False) -> TTFont:
    glyphs = {name: [square(100, 0, 500)] for name in (*STEM_NAMES, "i", "x")}
    glyphs["A"] = [square(0, -1000, 3500)]
    font = tiny_font(glyphs)
    font["hhea"].ascent, font["hhea"].descent = 3000, -1000
    font["CFF "].cff.topDictIndex[0].Private.defaultWidthX = 1160
    if italic:
        font["name"].setName("Italic", 2, 3, 1, 0x409)
        font["post"].italicAngle = -13
    return reloaded(font)


def test_pen_context_restores_globals_after_a_failed_study() -> None:
    before = (pen.ADV, pen.SLANT, pen.OPTICAL, pen.PEN)
    with pytest.raises(RuntimeError, match="study stopped"):
        with stem_pen(stem_fixture_font(True)):
            assert pen.SLANT == math.radians(13)
            raise RuntimeError("study stopped")
    assert (pen.ADV, pen.SLANT, pen.OPTICAL, pen.PEN) == before


@pytest.mark.parametrize("italic", [False, True])
def test_audit_preserves_other_glyphs_features_and_fixed_advances(
    tmp_path: Path, italic: bool
) -> None:
    font = stem_fixture_font(italic)
    replace_stem_trial(font, 0)
    source, target = tmp_path / "source.otf", tmp_path / "trial.otf"
    font.save(source)
    with TTFont(source) as changed:
        replace_stem_trial(changed, 20, 10)
        changed.save(target)
    audit_stem_font(source, target)
    with TTFont(target) as changed:
        GlyphWriter(changed, 1160).put("x", box(100, 0, 300, 500))
        changed.save(target)
    with pytest.raises(ValueError, match="expected only t/l/one"):
        audit_stem_font(source, target)


def test_stem_guard_has_no_waiver_for_a_marginal_regression() -> None:
    baseline = {15: {"1/I": 0.8, "1/l": 0.8}}
    assert stem_regressions(baseline, {15: {"1/I": 0.810, "1/l": 0.75}}) == []
    rejected = stem_regressions(baseline, {15: {"1/I": 0.811, "1/l": 0.75}})
    assert rejected == [{"size": 15, "pair": "1/I", "increase": 0.011}]
