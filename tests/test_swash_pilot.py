"""Swashes stay attached, counters stay open, and only opt-in outlines change."""

import math

import pytest
from shapely import affinity
from fontTools.ttLib import TTFont

import caps
import ornament
import pen
from conftest import reloaded, square, tiny_font
from display_motifs import leaf_study, ribbon_study
from place_ornaments import _ornament_shape
from swash_caps import (
    PILOT_CAPITALS,
    capital_offset,
    lean_strokes,
    swash_shape,
    swash_strokes,
)
from swash_pilot import font_pen, replace_swashes
from pilot_validation import (
    assert_pilot_metrics,
    assert_pilot_resources,
    changed_charstrings,
    require_pilot,
)
from glyph_writer import GlyphWriter
from shapely.geometry import box


@pytest.mark.parametrize("capital", PILOT_CAPITALS)
@pytest.mark.parametrize("variant", (1, 2, 3))
@pytest.mark.parametrize(
    "nib,degrees",
    [
        ((138, 106), 7),
        ((196, 150), 7),
        ((138, 106), 13),
        ((196, 150), 13),
        ((149.04, 114.48), 7),
    ],
)
def test_swashes_are_connected_with_one_open_counter(
    capital: str, variant: int, nib: tuple[float, float], degrees: float
) -> None:
    shape = swash_shape(capital, nib, degrees, 0, variant)
    parts = list(shape.geoms) if shape.geom_type == "MultiPolygon" else [shape]
    assert shape.is_valid and len(parts) == 1
    assert len(parts[0].interiors) == 1
    assert shape.bounds[1] >= -500
    assert shape.bounds[3] <= 1890


def test_swash_translation_and_nib_angle_are_independent_of_slant() -> None:
    shape = swash_shape("P", (138, 106), 13, 0)
    shifted = swash_shape("P", (138, 106), 13, 47)
    assert shifted.equals_exact(affinity.translate(shape, 47), 1e-9)
    points, weight = lean_strokes([([(0, 0), (0, 100)], 0.55)], 13, 47)[0]
    assert points == [(47, 0), (47 + 100 * math.tan(math.radians(13)), 100)]
    assert weight == 0.55


@pytest.mark.parametrize("capital", PILOT_CAPITALS)
def test_display_offset_matches_ordinary_capital_placement(
    capital: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pen, "ADV", 1160)
    monkeypatch.setattr(pen, "SLANT", math.radians(7))
    monkeypatch.setattr(pen, "OPTICAL", 0)
    _, expected = pen.place(caps.CAPS[capital](), 138, 106, band_top=1460)
    assert capital_offset(capital, (138, 106), 7, 1160) == expected


@pytest.mark.parametrize("capital,variant", [("B", 2), ("A", 0), ("R", 4)])
def test_invalid_swash_request_is_explicit(capital: str, variant: int) -> None:
    with pytest.raises(ValueError, match="expected"):
        swash_strokes(capital, variant)


@pytest.mark.parametrize("variant", (1, 2, 3))
def test_ornament_studies_are_valid_and_ribbon_has_a_separate_fold(
    variant: int,
) -> None:
    for strokes, fills in (
        leaf_study(variant),
        leaf_study(variant, True),
        ribbon_study(variant),
    ):
        shape = ornament.render(strokes, fills, 138, 106)
        assert shape.is_valid and not shape.is_empty
    assert len(ribbon_study(variant)[0]) == variant + 1


@pytest.mark.parametrize("cell", (1160, 1320))
@pytest.mark.parametrize("nib", ((138, 106), (196, 150), (149.04, 114.48)))
def test_selected_ornaments_fit_every_cell_and_weight(
    cell: int, nib: tuple[float, float], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(ornament, "CELL", cell)
    for cp in list(range(0x1F650, 0x1F658)) + [0x2770, 0x2771]:
        shape = _ornament_shape(cp, *nib, cell)
        assert shape.bounds[0] >= 0
        assert shape.bounds[2] <= cell


def minimal_swash_font() -> TTFont:
    names = list(PILOT_CAPITALS) + [f"{cap}.swsh" for cap in PILOT_CAPITALS] + ["B"]
    return reloaded(tiny_font({name: [square(100, 0, 500)] for name in names}))


def test_preview_replaces_only_three_alternates_with_fixed_advances() -> None:
    font = minimal_swash_font()
    strings = font["CFF "].cff.topDictIndex[0].CharStrings
    before = {name: strings[name].bytecode for name in font.getGlyphOrder()}
    replace_swashes(font)
    for name in font.getGlyphOrder():
        if name.endswith(".swsh"):
            assert strings[name].bytecode is None
        else:
            assert strings[name].bytecode == before[name]
        assert font["hmtx"][name][0] == 1160


def test_font_settings_reject_unknown_style_and_preserve_text_weight() -> None:
    font = minimal_swash_font()
    font["name"].setName("Talha Mono Text NF", 1, 3, 1, 0x409)
    assert font_pen(font)[0] == pytest.approx((149.04, 114.48))
    font["name"].setName("Unknown", 2, 3, 1, 0x409)
    with pytest.raises(ValueError, match="Unknown.*expected"):
        font_pen(font)


def test_outline_audit_detects_an_unrelated_letter_change() -> None:
    before, after = minimal_swash_font(), minimal_swash_font()
    GlyphWriter(after, 1160).put("B", box(100, 0, 900, 1000))
    after = reloaded(after)
    assert changed_charstrings(before, after) == {"B"}


def test_outline_audit_rejects_clipping_and_cell_overflow() -> None:
    font = minimal_swash_font()
    writer = GlyphWriter(font, 1160)
    writer.put("A.swsh", box(100, 0, 900, 2400))
    with pytest.raises(ValueError, match="A.swsh.*line bounds"):
        assert_pilot_metrics(font, {"A.swsh"})
    writer.put("A", box(-100, 0, 900, 1000))
    with pytest.raises(ValueError, match="A.*exceeds its cell"):
        assert_pilot_metrics(font, {"A"})


def test_audit_failure_remains_an_exception_when_assertions_are_disabled() -> None:
    with pytest.raises(ValueError, match="advance changed.*expected"):
        require_pilot(False, "A: advance changed")
    require_pilot(True, "unused")


def test_audit_protects_header_metrics_and_shared_hint_parameters() -> None:
    before, after = minimal_swash_font(), minimal_swash_font()
    assert_pilot_resources(before, after)
    after["head"].unitsPerEm = 4096
    with pytest.raises(ValueError, match="head metrics changed"):
        assert_pilot_resources(before, after)
    after["head"].unitsPerEm = before["head"].unitsPerEm
    after["CFF "].cff.topDictIndex[0].Private.rawDict["StdVW"] = 999
    with pytest.raises(ValueError, match="CFF Private parameters changed"):
        assert_pilot_resources(before, after)
